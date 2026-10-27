"""DG-07 B5 "LLM đọc thẳng": lời nhắc từ tệp, parser, cờ cắt, bộ chuyển hợp đồng, CLI và chặn chi tiền.

Không test nào gọi mô hình thật: transport là `urlopen` bị thay, khách là khách giả.
"""
import json
import re
import socket
from pathlib import Path

import pytest

import b5_ho_tro as ht
from tests.evaluation.ho_tro import tao_pdf

from danhgia.__main__ import main
from danhgia.hop_dong import kiem
from danhgia.ten import chuan_hoa
from danhgia.xuat.b5 import chuyen, goi, lenh, loi_nhac, van_ban

TEP_LOI_NHAC = Path(__file__).resolve().parents[2] / "evaluation" / "giao-thuc" / "b5" / "loi-nhac-b5.md"
THU_MUC_B5 = Path(__file__).resolve().parents[2] / "evaluation" / "danhgia" / "xuat" / "b5"


def _khoi(tieu_de):
    """Độc lập với mã: lấy khối ```...``` đầu tiên sau tiêu đề trong tệp lời nhắc."""
    noi_dung = TEP_LOI_NHAC.read_text(encoding="utf-8")
    sau = noi_dung.split(tieu_de, 1)[1]
    return re.search(r"```[a-z]*\n(.*?)\n```", sau, re.S).group(1)


# ---------- lời nhắc ----------

def test_lap_he_thong_ban_1_dung_khoi_text_cua_tep():
    assert loi_nhac.he_thong(1) == _khoi("## Lời nhắc hệ thống")


def test_nguoi_dung_chuong_dau_la_mau_cua_tep():
    mau = _khoi("## Lời nhắc người dùng")
    assert loi_nhac.nguoi_dung("VB") == mau.replace("{KHAI_NIEM_TRUOC}", "").replace("{VAN_BAN}", "VB")


def test_nguoi_dung_chuong_sau_co_danh_sach_ten():
    nd = loi_nhac.nguoi_dung("VB", ["Mat Troi", "Quang pho"])
    assert "Các khái niệm đã có ở chương trước (dùng đúng tên này nếu nhắc lại): Mat Troi; Quang pho" in nd
    assert nd.endswith("VB")


def test_loi_nhac_doc_tu_tep_khong_phai_tu_ma(tmp_path):
    sua = tmp_path / "loi-nhac.md"
    sua.write_text(TEP_LOI_NHAC.read_text(encoding="utf-8").replace("Bạn đọc một giáo trình", "Bạn soát một giáo trình"),
                   encoding="utf-8")
    assert loi_nhac.he_thong(1, duong=sua).startswith("Bạn soát một giáo trình")
    assert loi_nhac.he_thong(1).startswith("Bạn đọc một giáo trình")


def test_khong_nhung_cau_loi_nhac_vao_ma():
    cau = [d.strip() for d in _khoi("## Lời nhắc hệ thống").splitlines() if len(d.strip()) >= 40]
    assert len(cau) >= 6
    ma = {p.name: p.read_text(encoding="utf-8") for p in THU_MUC_B5.glob("*.py")}
    assert ma
    for dong in cau:
        manh = dong[:35]
        for ten, noi in ma.items():
            assert manh not in noi, f"{ten} chép lời nhắc: {manh!r}"


def _chuan_cau(van_ban_he_thong):
    """Tập dòng chỉ dẫn sau khi bỏ dấu đầu dòng, số thứ tự, hoa/thường và dòng trống."""
    ra = []
    for dong in van_ban_he_thong.splitlines():
        dong = re.sub(r"^\s*(-|\d+\.)\s+", "", dong).strip().casefold()
        if dong:
            ra.append(dong)
    return sorted(ra)


@pytest.mark.parametrize("k", [1, 2, 3, 4, 5])
def test_moi_bien_the_giu_nguyen_tap_cau_chi_dan(k):
    assert _chuan_cau(loi_nhac.he_thong(k)) == _chuan_cau(loi_nhac.he_thong(1))


def test_cac_bien_the_that_su_khac_dinh_dang():
    goc = loi_nhac.he_thong(1)
    bien = [loi_nhac.he_thong(k) for k in range(1, 6)]
    assert len(set(bien)) == 5
    khoi = goc.split("\n\n")
    assert bien[1].split("\n\n")[1].startswith("Đầu ra:") and bien[1].split("\n\n")[2].startswith("Định nghĩa:")
    assert "1. Khái niệm là" in bien[2] and "- Khái niệm là" not in bien[2]
    assert "ĐỊNH NGHĨA:" in bien[3] and "ĐẦU RA:" in bien[3]
    assert "\n\n" not in bien[4] and len(khoi) == 3


def test_chon_bien_the_theo_seed_tat_dinh_va_phu_du_5():
    assert [loi_nhac.chon_bien_the(s) for s in range(5)] == [loi_nhac.chon_bien_the(s) for s in range(5)]
    assert {loi_nhac.chon_bien_the(s) for s in range(5)} == {1, 2, 3, 4, 5}


def test_luoc_do_doc_tu_tep():
    luoc_do = loi_nhac.luoc_do()
    assert luoc_do["required"] == ["khai_niem", "quan_he", "lo_trinh"]


# ---------- văn bản sách ----------

def test_van_ban_dau_trang_va_khoang_chuong(tmp_path):
    pdf = tao_pdf(tmp_path / "s.pdf", [ht.TRANG[n].replace("\n", " ") for n in (1, 2, 3, 4)])
    doc_trang = van_ban.doc_trang_pdf(pdf)
    cuon = van_ban.cuon(ht.manifest(), doc_trang)
    assert cuon.count("[Trang ") == 4 and cuon.startswith("[Trang 1]\n")
    chuong = van_ban.chuong(ht.manifest(), doc_trang)
    assert [(c["ma"], c["dau"], c["cuoi"]) for c in chuong] == [("c1", 1, 2), ("c2", 3, 4)]
    assert "[Trang 3]" not in chuong[0]["text"] and "[Trang 3]" in chuong[1]["text"]
    assert "\r" not in cuon


# ---------- parser và cờ cắt ----------

def _luot(text, **kw):
    kh = KhachGia([goi.PhanHoi(text=text, usage={"promptTokenCount": 10, "candidatesTokenCount": 5}, **kw)])
    return goi.chay_luot(kh, "he", "nd", loi_nhac.luoc_do()), kh


class KhachGia:
    def __init__(self, phan_hoi):
        self.phan_hoi, self.cuoc_goi = list(phan_hoi), []

    def goi(self, he_thong, nguoi_dung, luoc_do):
        self.cuoc_goi.append((he_thong, nguoi_dung))
        p = self.phan_hoi[min(len(self.cuoc_goi), len(self.phan_hoi)) - 1]
        return p(nguoi_dung) if callable(p) else p


def test_parser_chap_nhan_phan_hoi_hop_le():
    luot, _ = _luot(ht.van_ban_mo_hinh(ht.phan_hoi_a()))
    assert luot.ok and luot.loi == [] and not luot.cat_vi_tran
    assert len(luot.du_lieu["khai_niem"]) == 4


def test_parser_json_hong_thi_luot_that_bai_co_ly_do_khong_goi_lai():
    luot, kh = _luot('{"khai_niem": [')
    assert not luot.ok and luot.du_lieu is None
    assert any("JSON" in l for l in luot.loi)
    assert len(kh.cuoc_goi) == 1


def test_parser_thieu_truong_thi_that_bai_khong_va():
    hong = ht.phan_hoi_a()
    del hong["quan_he"][0]["cau_bang_chung"]
    luot, _ = _luot(ht.van_ban_mo_hinh(hong))
    assert not luot.ok and luot.du_lieu is None
    assert any("quan_he[0]" in l and "cau_bang_chung" in l for l in luot.loi)


def test_parser_thieu_khoa_cap_dinh_thi_that_bai():
    hong = ht.phan_hoi_a()
    del hong["lo_trinh"]
    luot, _ = _luot(ht.van_ban_mo_hinh(hong))
    assert not luot.ok and any("lo_trinh" in l for l in luot.loi)


def test_parser_goc_khong_phai_doi_tuong():
    luot, _ = _luot("[1, 2]")
    assert not luot.ok and luot.loi


def test_co_cat_vi_tran_khi_ly_do_dung_la_max_tokens():
    luot, kh = _luot('{"khai_niem": [{"ten": "Mat', ly_do_dung="MAX_TOKENS")
    assert luot.cat_vi_tran is True and not luot.ok
    assert len(kh.cuoc_goi) == 1  # không gọi lại


def test_khong_co_cat_khi_ly_do_stop():
    luot, _ = _luot(ht.van_ban_mo_hinh(ht.phan_hoi_a()), ly_do_dung="STOP")
    assert luot.cat_vi_tran is False


def test_luot_ghi_usage_va_usd_theo_bang_gia():
    kh = KhachGia([goi.PhanHoi(text=ht.van_ban_mo_hinh(ht.phan_hoi_a()), giay=2.5,
                               usage={"promptTokenCount": 1_000_000, "candidatesTokenCount": 100_000,
                                      "thoughtsTokenCount": 100_000})])
    luot = goi.chay_luot(kh, "he", "nd", loi_nhac.luoc_do())
    assert (luot.token_vao, luot.token_ra, luot.giay) == (1_000_000, 200_000, 2.5)
    assert luot.usd == pytest.approx(0.25 + 0.2 * 1.5)


def test_loi_duong_truyen_thanh_luot_that_bai():
    kh = KhachGia([goi.PhanHoi(text="", loi_truyen="HTTP 500")])
    luot = goi.chay_luot(kh, "he", "nd", loi_nhac.luoc_do())
    assert not luot.ok and any("HTTP 500" in l for l in luot.loi) and len(kh.cuoc_goi) == 1


# ---------- khách Gemini qua adapter (transport giả) ----------

class _Tra:
    def __init__(self, thanh):
        self.thanh = thanh

    def read(self):
        return self.thanh

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _khach_gemini(monkeypatch, thanh):
    import doc2roadmap.infrastructure.llm.gemini as gm
    cuoc_goi = []

    def urlopen(request, timeout=None):
        cuoc_goi.append(json.loads(request.data))
        return _Tra(thanh)

    monkeypatch.setattr(gm, "urlopen", urlopen)
    return goi.KhachGemini(goi.tao_extractor("khoa-gia", transport="developer_api", max_retries=0)), cuoc_goi


def test_khach_gemini_doc_ly_do_dung_usage_va_khong_gui_lai_khi_cat(monkeypatch):
    khach, cuoc_goi = _khach_gemini(monkeypatch, ht.phan_hoi_http('{"khai_niem": [{"ten"', ly_do="MAX_TOKENS"))
    luot = goi.chay_luot(khach, "HE", "ND", loi_nhac.luoc_do())
    assert luot.cat_vi_tran and not luot.ok
    assert (luot.token_vao, luot.token_ra) == (100, 50)
    assert len(cuoc_goi) == 1  # adapter ask_json sẽ gọi sửa lần hai; khách B5 không được
    cau_hinh = cuoc_goi[0]["generationConfig"]
    assert cau_hinh["temperature"] == 0 and cau_hinh["maxOutputTokens"] == goi.TRAN_TOKEN_RA
    assert cuoc_goi[0]["systemInstruction"]["parts"][0]["text"] == "HE"
    assert cuoc_goi[0]["contents"][0]["parts"][0]["text"] == "ND"


def test_khach_gemini_phan_hoi_hop_le(monkeypatch):
    khach, cuoc_goi = _khach_gemini(monkeypatch, ht.phan_hoi_http(ht.van_ban_mo_hinh(ht.phan_hoi_a())))
    luot = goi.chay_luot(khach, "HE", "ND", loi_nhac.luoc_do())
    assert luot.ok and not luot.cat_vi_tran and luot.ly_do_dung == "STOP"


# ---------- bộ chuyển sang hợp đồng ----------

def _tra_trang(n):
    return ht.TRANG.get(n, "")


def _luot_ok(du_lieu, **kw):
    return goi.chay_luot(KhachGia([goi.PhanHoi(text=ht.van_ban_mo_hinh(du_lieu), **kw)]), "he", "nd",
                         loi_nhac.luoc_do())


DANH_TINH = {"che_do": "a", "k": 1, "commit": "c" * 40, "ngay_chay": "2026-10-27", "transport": "vertex",
             "mo_hinh": "gemini-3.1-flash-lite", "hash_cau_hinh": "h"}


def _chuyen_a(du_lieu=None, **kw):
    luot = _luot_ok(du_lieu or ht.phan_hoi_a(), usage={"promptTokenCount": 800, "candidatesTokenCount": 200,
                                                         "thoughtsTokenCount": 50}, giay=3.0)
    return chuyen.chuyen([chuyen.LuotCuaChuong(nhan="cuon", dau=1, cuoi=4, luot=luot)], manifest=ht.manifest(),
                         doc_trang=_tra_trang, **DANH_TINH, **kw)


def test_hop_dong_b5a_qua_validator_va_dung_hinh():
    hd, bao_cao = _chuyen_a()
    assert kiem(hd) == []
    assert hd["cau_truc"] is None and hd["cap_ung_vien"] is None
    assert hd["dinh_danh"]["he"] == "b5a" and hd["dinh_danh"]["doc_id"] == "dev-thien-van"
    assert hd["dinh_danh"]["luot_nhieu"] == 0 and hd["dinh_danh"]["bien_the"].endswith("k1")
    k = {x["ten"]: x for x in hd["khai_niem"]}
    assert k["Quang pho"]["trang_thai_day"] == "taught"
    assert k["Quang pho"]["cau_neo"] == {"trang": 2, "cau": ht.C_QUANG_PHO, "ma_chunk": ""}
    assert k["Quang pho"]["ten_khac"] == ["pho anh sang"]
    assert k["Quang pho"]["trong_day_hoc"] and k["Quang pho"]["vi_tri"] == 1
    assert k["Hang so Hubble"]["module"] is not None and k["Mat Troi"]["module"] == k["Quang pho"]["module"]
    ma = {x["ten"]: x["ma"] for x in hd["khai_niem"]}
    canh = hd["canh"][0]
    assert (canh["nguon"], canh["dich"]) == (ma["Mat Troi"], ma["Quang pho"])
    assert canh["nguon_goc"] == "baseline" and canh["mem"] is False and canh["bo_qua"] is False
    assert canh["bang_chung"] == {"trang": 2, "cau": ht.C_PHU_THUOC}
    assert [hd["khai_niem"][i]["ten"] for i in range(4)] == ["Mat Troi", "Quang pho", "Sao", "Hang so Hubble"]
    assert hd["lo_trinh"]["day_hoc"] == [ma[t] for t in ("Mat Troi", "Quang pho", "Sao", "Hang so Hubble")]
    assert [m["ten"] for m in hd["lo_trinh"]["module"]] == ["Anh sang", "Vu tru"]
    assert bao_cao["cat_vi_tran"] is False


def test_chi_phi_lay_tu_usage():
    hd, _ = _chuyen_a()
    tong = hd["chi_phi"]["tong"]
    assert (tong["token_vao"], tong["token_ra"], tong["so_loi_goi_mo_hinh"], tong["giay_chay"]) == (800, 250, 1, 3.0)
    assert tong["usd"] == pytest.approx((800 * 0.25 + 250 * 1.5) / 1e6)
    assert tong["giay_cho_embedding"] is None and hd["chi_phi"]["theo_khau"]["b5"] == tong


def test_quan_he_tro_khai_niem_la_duoc_dem_giu_nguyen_khong_va():
    du_lieu = ht.phan_hoi_a()
    du_lieu["quan_he"].append({"nguon": "Thien ha", "dich": "Sao", "trang": 3, "cau_bang_chung": ht.C_SAO})
    du_lieu["quan_he"].append({"nguon": "Sao", "dich": "Lo den", "trang": 3, "cau_bang_chung": ht.C_SAO})
    hd, bao_cao = _chuyen_a(du_lieu)
    assert kiem(hd) == []
    assert bao_cao["quan_he_tro_khai_niem_la"] == 2
    assert [q["nguon"] + ">" + q["dich"] for q in bao_cao["quan_he_la"]] == ["Thien ha>Sao", "Sao>Lo den"]
    assert len(hd["canh"]) == 2 and len(hd["khai_niem"]) == 4  # không thêm khái niệm để vá


def test_cau_trich_duoc_kiem_trong_sach_va_cau_bia_bi_dem():
    du_lieu = ht.phan_hoi_a()
    du_lieu["khai_niem"][2]["cau_dinh_nghia"] = "Sao la mot qua cau lua khong lo duoc to boi vu tru."  # bịa
    du_lieu["khai_niem"][3]["trang"] = 2  # câu thật nhưng sai trang (nằm ở trang 4)
    du_lieu["quan_he"][0]["cau_bang_chung"] = "Mat  TROI phat ra anh sang, muon hieu quang pho phai biet."  # bịa
    hd, bao_cao = _chuyen_a(du_lieu)
    kn = bao_cao["cau_trich"]["khai_niem"]
    assert kn == {"tong": 4, "dung_trang": 2, "trang_khac": 1, "khong_co": 1}
    assert bao_cao["cau_trich"]["quan_he"] == {"tong": 2, "dung_trang": 1, "trang_khac": 0, "khong_co": 1}
    assert bao_cao["khong_co_trong_sach"] == [{"loai": "khai_niem", "ten": "Sao"},
                                              {"loai": "quan_he", "nguon": "Mat Troi", "dich": "Quang pho"}]
    assert len(hd["khai_niem"]) == 4 and len(hd["canh"]) == 2  # giữ nguyên để thước truy nguyên đếm


def test_cau_dung_khac_hoa_thuong_khoang_trang_van_la_cau_that():
    du_lieu = ht.phan_hoi_a()
    du_lieu["khai_niem"][0]["cau_dinh_nghia"] = "mat   troi la ngoi sao gan trai dat nhat"
    _, bao_cao = _chuyen_a(du_lieu)
    assert bao_cao["cau_trich"]["khai_niem"]["khong_co"] == 0


def test_day_hoc_lap_va_ten_la_bi_dem_khong_vao_hop_dong():
    du_lieu = ht.phan_hoi_a()
    du_lieu["lo_trinh"]["day_hoc"] = ["Mat Troi", "Quang pho", "Mat Troi", "Ten la", "Sao"]
    du_lieu["lo_trinh"]["module"][0]["khai_niem"].append("Ten la")
    hd, bao_cao = _chuyen_a(du_lieu)
    assert kiem(hd) == []
    assert len(hd["lo_trinh"]["day_hoc"]) == 3
    assert bao_cao["day_hoc_lap"] == 1 and bao_cao["lo_trinh_ten_la"] == 2


# ---------- B5b ----------

def _chuyen_b(du_lieu_1, du_lieu_2, **kw):
    l1 = _luot_ok(du_lieu_1, usage={"promptTokenCount": 100, "candidatesTokenCount": 10}, giay=1.0)
    l2 = _luot_ok(du_lieu_2, usage={"promptTokenCount": 120, "candidatesTokenCount": 20}, giay=2.0)
    return chuyen.chuyen([chuyen.LuotCuaChuong("c1", 1, 2, l1), chuyen.LuotCuaChuong("c2", 3, 4, l2)],
                         manifest=ht.manifest(), doc_trang=_tra_trang, **{**DANH_TINH, "che_do": "b"}, **kw)


def _mot_chuong(khai_niem, quan_he=(), day=None):
    return {"khai_niem": khai_niem, "quan_he": list(quan_he),
            "lo_trinh": {"day_hoc": day or [k["ten"] for k in khai_niem], "module": []}}


def _kn(ten, trang, cau, khac=()):
    return {"ten": ten, "ten_khac": list(khac), "trang": trang, "cau_dinh_nghia": cau}


def test_b5b_gop_khi_ten_trung_sau_chuan_hoa():
    c1 = _mot_chuong([_kn("Mat Troi", 1, ht.C_MAT_TROI, ["Thai duong"]), _kn("Quang pho", 2, ht.C_QUANG_PHO)])
    c2 = _mot_chuong([_kn("  mat   troi. ", 1, ht.C_MAT_TROI, ["Nhat"]), _kn("Sao", 3, ht.C_SAO)],
                     [{"nguon": "mat troi", "dich": "Sao", "trang": 3, "cau_bang_chung": ht.C_SAO}])
    hd, bao_cao = _chuyen_b(c1, c2)
    assert kiem(hd) == []
    ten = [k["ten"] for k in hd["khai_niem"]]
    assert ten == ["Mat Troi", "Quang pho", "Sao"]
    mat_troi = hd["khai_niem"][0]
    assert mat_troi["ten_khac"] == ["Thai duong", "Nhat"]
    assert bao_cao["khai_niem_gop_theo_ten"] == 1
    assert (hd["canh"][0]["nguon"], hd["canh"][0]["dich"]) == (mat_troi["ma"], hd["khai_niem"][2]["ma"])
    assert hd["dinh_danh"]["he"] == "b5b"
    assert hd["chi_phi"]["tong"]["so_loi_goi_mo_hinh"] == 2 and hd["chi_phi"]["tong"]["token_vao"] == 220


def test_b5b_khong_gop_ten_khac_nhau_du_gan_giong():
    c1 = _mot_chuong([_kn("Mat Troi", 1, ht.C_MAT_TROI), _kn("Sao", 3, ht.C_SAO)])
    c2 = _mot_chuong([_kn("Mat Trang", 1, ht.C_MAT_TROI), _kn("Sao choi", 3, ht.C_SAO),
                      _kn("Mặt Trời", 1, ht.C_MAT_TROI)])
    hd, bao_cao = _chuyen_b(c1, c2)
    assert [k["ten"] for k in hd["khai_niem"]] == ["Mat Troi", "Sao", "Mat Trang", "Sao choi", "Mặt Trời"]
    assert bao_cao["khai_niem_gop_theo_ten"] == 0


def test_b5b_ten_trung_theo_ten_khac_khong_gop():
    c1 = _mot_chuong([_kn("Mat Troi", 1, ht.C_MAT_TROI, ["Thai duong"])])
    c2 = _mot_chuong([_kn("Thai duong", 1, ht.C_MAT_TROI)])
    hd, _ = _chuyen_b(c1, c2)
    assert [k["ten"] for k in hd["khai_niem"]] == ["Mat Troi", "Thai duong"]


def test_b5b_ma_khai_niem_khong_trung():
    c1 = _mot_chuong([_kn("Mat Troi", 1, ht.C_MAT_TROI)])
    c2 = _mot_chuong([_kn("Sao", 3, ht.C_SAO)])
    hd, _ = _chuyen_b(c1, c2)
    assert len({k["ma"] for k in hd["khai_niem"]}) == 2


def test_chuong_that_bai_ghi_vao_bao_cao_va_ghi_chu_chi_phi():
    ok = _luot_ok(_mot_chuong([_kn("Mat Troi", 1, ht.C_MAT_TROI)]), usage={"promptTokenCount": 10})
    hong = goi.chay_luot(KhachGia([goi.PhanHoi(text="{", ly_do_dung="MAX_TOKENS", usage={"promptTokenCount": 7})]),
                         "he", "nd", loi_nhac.luoc_do())
    hd, bao_cao = chuyen.chuyen([chuyen.LuotCuaChuong("c1", 1, 2, ok), chuyen.LuotCuaChuong("c2", 3, 4, hong)],
                                manifest=ht.manifest(), doc_trang=_tra_trang, **{**DANH_TINH, "che_do": "b"})
    assert kiem(hd) == []
    assert bao_cao["cat_vi_tran"] is True and bao_cao["luot_that_bai"] == [
        {"nhan": "c2", "cat_vi_tran": True, "loi": hong.loi}]
    assert "c2" in hd["chi_phi"]["ghi_chu"] and hd["chi_phi"]["tong"]["so_loi_goi_mo_hinh"] == 2
    assert hd["chi_phi"]["tong"]["token_vao"] == 17  # lượt hỏng vẫn tốn tiền


def test_khong_co_luot_nao_thanh_cong_thi_khong_ra_hop_dong():
    hong = goi.chay_luot(KhachGia([goi.PhanHoi(text="{")]), "he", "nd", loi_nhac.luoc_do())
    with pytest.raises(chuyen.KhongCoLuotNaoThanhCong):
        chuyen.chuyen([chuyen.LuotCuaChuong("cuon", 1, 4, hong)], manifest=ht.manifest(), doc_trang=_tra_trang,
                      **DANH_TINH)


# ---------- CLI, dry-run và chặn chi tiền ----------

@pytest.fixture
def sach(tmp_path):
    pdf = tao_pdf(tmp_path / "s.pdf", [ht.TRANG[n].replace("\n", " ") for n in (1, 2, 3, 4)])
    mf = tmp_path / "m.json"
    mf.write_text(json.dumps(ht.manifest(ht.sha256(pdf))), encoding="utf-8")
    return pdf, mf


@pytest.fixture
def chan_mang(monkeypatch):
    """Mọi đường ra mạng đều là lỗi: urlopen của adapter, socket, và việc dựng khách thật."""
    import doc2roadmap.infrastructure.llm.gemini as gm

    def cam(*a, **k):
        raise AssertionError("đã gọi mạng")

    monkeypatch.setattr(gm, "urlopen", cam)
    monkeypatch.setattr(socket, "socket", cam)
    monkeypatch.setattr(socket, "create_connection", cam)
    monkeypatch.setattr(lenh, "tao_khach", cam)


def _lenh(sach, ra, *them):
    pdf, mf = sach
    return ["b5", "--manifest", str(mf), "--pdf", str(pdf), "--ra", str(ra), *them]


def test_khong_allow_spend_thi_khong_goi_mo_hinh(sach, tmp_path, chan_mang, capsys):
    ma = main(_lenh(sach, tmp_path / "ra", "--che-do", "a", "--bien-the", "1"))
    assert ma != 0
    assert "allow-spend" in capsys.readouterr().err
    assert not (tmp_path / "ra").exists() or not list((tmp_path / "ra").glob("*.json"))


def test_dry_run_khong_goi_mang_va_bao_du_toan(sach, tmp_path, chan_mang, capsys):
    ra = tmp_path / "ra"
    assert main(_lenh(sach, ra, "--che-do", "a", "--bien-the", "1", "--dry-run")) == 0
    bao = json.loads((ra / "dry-run.json").read_text(encoding="utf-8"))
    he_thong, luoc_do = loi_nhac.he_thong(1), loi_nhac.luoc_do()
    nd = loi_nhac.nguoi_dung(van_ban.cuon(ht.manifest(), van_ban.doc_trang_pdf(sach[0])))
    mong = (len(he_thong) + len(nd) + len(json.dumps(luoc_do, ensure_ascii=False))) // 3
    a = bao["b5a"]
    assert a["token_vao_uoc"] == mong and a["so_loi_goi"] == 1
    assert a["cach_uoc"] == "ky_tu_chia_3" and a["tran_token_ra"] == 65536
    assert a["usd_vao"] == pytest.approx(mong * 0.25 / 1e6)
    assert a["usd_toi_da"] == pytest.approx(a["usd_vao"] + 65536 * 1.5 / 1e6)
    b = bao["b5b"]
    assert b["so_loi_goi"] == 2 and b["usd_toi_da"] > b["usd_vao"] > 0
    assert "token_vao_uoc" in capsys.readouterr().out


def test_dry_run_khong_can_allow_spend_va_khong_ghi_hop_dong(sach, tmp_path, chan_mang):
    ra = tmp_path / "ra"
    main(_lenh(sach, ra, "--che-do", "b", "--seed", "3", "--dry-run"))
    assert [p.name for p in ra.glob("*")] == ["dry-run.json"]


class _KhachCli:
    def __init__(self, phan_hoi):
        self.k = KhachGia(phan_hoi)

    def goi(self, he_thong, nguoi_dung, luoc_do):
        return self.k.goi(he_thong, nguoi_dung, luoc_do)


def _giu_khach(monkeypatch, phan_hoi):
    khach = _KhachCli(phan_hoi)
    monkeypatch.setattr(lenh, "tao_khach", lambda *a, **k: (khach, "vertex-gia"))
    return khach.k


def test_chay_b5a_ghi_hop_dong_va_bao_cao(sach, tmp_path, monkeypatch):
    kh = _giu_khach(monkeypatch, [goi.PhanHoi(text=ht.van_ban_mo_hinh(ht.phan_hoi_a()),
                                              usage={"promptTokenCount": 500, "candidatesTokenCount": 90})])
    ra = tmp_path / "ra"
    assert main(_lenh(sach, ra, "--che-do", "a", "--bien-the", "3", "--allow-spend")) == 0
    assert len(kh.cuoc_goi) == 1
    he_thong, nguoi_dung = kh.cuoc_goi[0]
    assert he_thong == loi_nhac.he_thong(3)
    assert nguoi_dung.startswith("\nVăn bản giáo trình:\n[Trang 1]")
    hd = json.loads((ra / "b5a-k3.json").read_text(encoding="utf-8"))
    assert kiem(hd) == [] and hd["dinh_danh"]["luot_nhieu"] == 2
    luot = json.loads((ra / "b5a-k3-luot.json").read_text(encoding="utf-8"))
    assert luot["luot"][0]["phan_hoi_tho"] == ht.van_ban_mo_hinh(ht.phan_hoi_a())  # lưu để phát lại parser
    assert luot["bao_cao"]["cau_trich"]["khai_niem"]["khong_co"] == 0


def test_chay_b5b_tung_chuong_kem_danh_sach_chuong_truoc(sach, tmp_path, monkeypatch):
    c1 = _mot_chuong([_kn("Mat Troi", 1, ht.C_MAT_TROI), _kn("Quang pho", 2, ht.C_QUANG_PHO)])
    c2 = _mot_chuong([_kn("Sao", 3, ht.C_SAO)])
    kh = _giu_khach(monkeypatch, [goi.PhanHoi(text=ht.van_ban_mo_hinh(c1)), goi.PhanHoi(text=ht.van_ban_mo_hinh(c2))])
    ra = tmp_path / "ra"
    assert main(_lenh(sach, ra, "--che-do", "b", "--bien-the", "1", "--allow-spend")) == 0
    assert len(kh.cuoc_goi) == 2
    assert "Các khái niệm đã có" not in kh.cuoc_goi[0][1]
    assert "(dùng đúng tên này nếu nhắc lại): Mat Troi; Quang pho" in kh.cuoc_goi[1][1]
    assert "[Trang 3]" not in kh.cuoc_goi[0][1] and "[Trang 1]" not in kh.cuoc_goi[1][1]
    assert kiem(json.loads((ra / "b5b-k1.json").read_text(encoding="utf-8"))) == []


def test_luot_hong_thi_ma_thoat_1_van_ghi_bao_cao(sach, tmp_path, monkeypatch, capsys):
    _giu_khach(monkeypatch, [goi.PhanHoi(text='{"khai_niem": [', ly_do_dung="MAX_TOKENS")])
    ra = tmp_path / "ra"
    assert main(_lenh(sach, ra, "--che-do", "a", "--bien-the", "1", "--allow-spend")) == 1
    assert not (ra / "b5a-k1.json").exists()
    luot = json.loads((ra / "b5a-k1-luot.json").read_text(encoding="utf-8"))
    assert luot["bao_cao"]["cat_vi_tran"] is True


def test_sha_pdf_khac_manifest_thi_tu_choi_truoc_khi_goi(sach, tmp_path, chan_mang, capsys):
    pdf, mf = sach
    m = json.loads(mf.read_text(encoding="utf-8"))
    m["pdf_sha256"] = "1" * 64
    mf.write_text(json.dumps(m), encoding="utf-8")
    assert main(_lenh(sach, tmp_path / "ra", "--che-do", "a", "--bien-the", "1", "--allow-spend")) != 0
    assert "sha256" in capsys.readouterr().err


def test_bien_the_va_seed_loai_tru_nhau(sach, tmp_path, chan_mang, capsys):
    with pytest.raises(SystemExit):
        main(_lenh(sach, tmp_path / "ra", "--che-do", "a", "--bien-the", "1", "--seed", "2", "--dry-run"))


# ---------- kiến trúc ----------

def test_chi_goi_py_nhap_doc2roadmap_trong_b5():
    import ast
    nhap = {}
    for p in THU_MUC_B5.glob("*.py"):
        ten = []
        for nut in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            if isinstance(nut, ast.Import):
                ten += [x.name for x in nut.names]
            elif isinstance(nut, ast.ImportFrom) and nut.level == 0:
                ten.append(nut.module or "")
        nhap[p.name] = any(t.split(".")[0] == "doc2roadmap" for t in ten)
    assert nhap["goi.py"] is True
    assert {k for k, v in nhap.items() if v} == {"goi.py"}


def test_lenh_b5_trong_bang_lenh():
    from danhgia.__main__ import _LENH
    assert _LENH["b5"] == "danhgia.xuat.b5.lenh"


# ---------- bổ sung sau nghiệm thu vòng 1 (C4, C9, C11, C12, C13) ----------

def test_json_hop_le_nhung_max_tokens_van_la_luot_that_bai_co_co_cat():  # C4
    luot, kh = _luot(ht.van_ban_mo_hinh(ht.phan_hoi_a()), ly_do_dung="MAX_TOKENS")
    assert luot.cat_vi_tran is True and luot.ok is False
    assert any("cat_vi_tran" in l for l in luot.loi)
    assert len(kh.cuoc_goi) == 1


def test_b5b_day_hoc_va_module_noi_dung_thu_tu_sach():  # C9
    c1 = _mot_chuong([_kn("Mat Troi", 1, ht.C_MAT_TROI), _kn("Quang pho", 2, ht.C_QUANG_PHO)])
    c1["lo_trinh"]["module"] = [{"ten": "M1", "khai_niem": ["Mat Troi", "Quang pho"]}]
    c2 = _mot_chuong([_kn("Sao", 3, ht.C_SAO), _kn("Hang so Hubble", 4, ht.C_HUBBLE)])
    c2["lo_trinh"]["module"] = [{"ten": "M2", "khai_niem": ["Sao", "Hang so Hubble"]}]
    hd, _ = _chuyen_b(c1, c2)
    ten = {k["ma"]: k["ten"] for k in hd["khai_niem"]}
    assert [ten[m] for m in hd["lo_trinh"]["day_hoc"]] == ["Mat Troi", "Quang pho", "Sao", "Hang so Hubble"]
    assert [m["ten"] for m in hd["lo_trinh"]["module"]] == ["M1", "M2"]
    assert [k["vi_tri"] for k in hd["khai_niem"]] == [0, 1, 2, 3]


def _qh(nguon, dich, trang=2, cau=ht.C_PHU_THUOC):
    return {"nguon": nguon, "dich": dich, "trang": trang, "cau_bang_chung": cau}


def test_canh_lap_trong_mot_luot_giu_mot_canh():  # C11
    du_lieu = ht.phan_hoi_a()
    du_lieu["quan_he"] = [_qh("Mat Troi", "Quang pho"), _qh("mat troi", "Quang pho.")]
    hd, bao_cao = _chuyen_a(du_lieu)
    assert len(hd["canh"]) == 1 and bao_cao["canh_lap"] == 1


def test_canh_lap_giua_hai_chuong_b5b_giu_mot_canh():  # C11
    c1 = _mot_chuong([_kn("Mat Troi", 1, ht.C_MAT_TROI), _kn("Quang pho", 2, ht.C_QUANG_PHO)], [_qh("Mat Troi", "Quang pho")])
    c2 = _mot_chuong([_kn("Sao", 3, ht.C_SAO)], [_qh("Mat Troi", "Quang pho"), _qh("Quang pho", "Mat Troi")])
    hd, bao_cao = _chuyen_b(c1, c2)
    assert len(hd["canh"]) == 2 and bao_cao["canh_lap"] == 1  # (Quang pho, Mat Troi) là cạnh ngược, không phải lặp
    assert kiem(hd) == []


def _manifest_nhieu_loai():
    m = ht.manifest()
    m["chuong"] = [
        {"ma": "md", "so": "0", "ten": "Mo dau", "trang_dau": 1, "trang_cuoi": 1, "loai": "mo_dau"},
        {"ma": "c1", "so": "1", "ten": "Mat Troi", "trang_dau": 2, "trang_cuoi": 3, "loai": "noi_dung"},
        {"ma": "bt", "so": "bt", "ten": "Bai tap", "trang_dau": 4, "trang_cuoi": 4, "loai": "bai_tap"},
    ]
    return m


def test_b5b_doc_moi_loai_chuong_cung_pham_vi_voi_b5a(tmp_path):  # C13
    pdf = tao_pdf(tmp_path / "s.pdf", [ht.TRANG[n].replace("\n", " ") for n in (1, 2, 3, 4)])
    doc_trang = van_ban.doc_trang_pdf(pdf)
    m = _manifest_nhieu_loai()
    chuong = van_ban.chuong(m, doc_trang)
    assert [c["ma"] for c in chuong] == ["md", "c1", "bt"]
    cac_trang = [int(n) for c in chuong for n in re.findall(r"\[Trang (\d+)\]", c["text"])]
    assert cac_trang == [1, 2, 3, 4] == [int(n) for n in re.findall(r"\[Trang (\d+)\]", van_ban.cuon(m, doc_trang))]


def test_cli_b5b_goi_mot_lan_moi_chuong_ke_ca_mo_dau_va_bai_tap(tmp_path, monkeypatch):  # C13
    pdf = tao_pdf(tmp_path / "s.pdf", [ht.TRANG[n].replace("\n", " ") for n in (1, 2, 3, 4)])
    m = _manifest_nhieu_loai()
    m["pdf_sha256"] = ht.sha256(pdf)
    mf = tmp_path / "m.json"
    mf.write_text(json.dumps(m), encoding="utf-8")
    rong = _mot_chuong([])
    kh = _giu_khach(monkeypatch, [goi.PhanHoi(text=ht.van_ban_mo_hinh(rong))])
    main(["b5", "--manifest", str(mf), "--pdf", str(pdf), "--ra", str(tmp_path / "ra"), "--che-do", "b",
          "--bien-the", "1", "--allow-spend"])
    assert len(kh.cuoc_goi) == 3
    assert "[Trang 1]" in kh.cuoc_goi[0][1] and "[Trang 4]" in kh.cuoc_goi[2][1]


def test_chuong_bi_cat_du_json_hop_le_khong_dua_khai_niem_vao_danh_sach_chuong_sau(sach, tmp_path, monkeypatch):  # C12
    c1 = _mot_chuong([_kn("Mat Troi", 1, ht.C_MAT_TROI)])
    c2 = _mot_chuong([_kn("Sao", 3, ht.C_SAO)])
    kh = _giu_khach(monkeypatch, [goi.PhanHoi(text=ht.van_ban_mo_hinh(c1), ly_do_dung="MAX_TOKENS"),
                                  goi.PhanHoi(text=ht.van_ban_mo_hinh(c2))])
    assert main(_lenh(sach, tmp_path / "ra", "--che-do", "b", "--bien-the", "1", "--allow-spend")) == 1
    assert len(kh.cuoc_goi) == 2  # không gọi lại chương bị cắt
    assert "Các khái niệm đã có" not in kh.cuoc_goi[1][1] and "Mat Troi" not in kh.cuoc_goi[1][1]
