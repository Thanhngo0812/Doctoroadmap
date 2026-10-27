"""Vé DG-10: thước A3, A4, A5, truy nguyên, thước phụ so với B5 và trần người. Mỗi thước có ca dựng tay với số tính tay."""
import copy
import json
from pathlib import Path

import pytest

from danhgia.cham import bang, dong, khai_niem
from tests.evaluation import dung_tay as dt

MA = "S"
ANH_XA = {"nhap": True, "may_sang_vang": {
    "taught": ["day_o_day", "day_qua_vi_du"], "mentioned_only": ["chi_nhac"], "prior_knowledge": ["kien_thuc_nen"],
    "uncertain": None, "unchecked": None, "not_subject_matter": []}}


def nd(ma, *, day=True, neo=None, status="taught", ten=None, ten_khac=()):
    k = dt.khai_niem(ma, ten, trong_day_hoc=day, trang_thai=status)
    k["ten_khac"] = list(ten_khac)
    k["cau_neo"] = None if neo is None else {"trang": neo[0], "cau": neo[1], "ma_chunk": "c"}
    return k


def vang(ma, chuong, trang_thai="day_o_day", trang=1, cau="Câu định nghĩa vàng.", ten=None):
    return {"ma": ma, "chuong": chuong, "ten": ten or ma, "ten_khac": [], "trang_thai": trang_thai,
            "dinh_nghia": {"trang": trang, "cau": cau}, "khong_chac": False, "ghi_chu": ""}


def g3_(*khai_niem_):
    return {"schema": "danh-gia-g3-1", "ma_sach": MA, "nguoi_gan": "hoi-y", "phien_ban_huong_dan": "g3-2",
            "khai_niem": list(khai_niem_), "tranh_chap": []}


def hd_(nodes, canh=(), ban_do=None):
    return dt.hop_dong(nodes, list(canh), [k["ma"] for k in nodes if k["trong_day_hoc"]], ban_do_danh_tinh=ban_do)


def so(rows, thuoc, chuong):
    (r,) = [r for r in rows if r["thuoc"] == thuoc and r["chuong"] == chuong]
    return r


def tu_mau(rows, thuoc, chuong="c1"):
    r = so(rows, thuoc, chuong)
    return r["tu"], r["mau"]


def cham(hd, g3, can, van_ban=None, g4=None, **kw):
    return khai_niem.cham_khai_niem(hd, g3, g4 or dt.g4(MA, []), can, van_ban or {}, ANH_XA, **kw)


# ---------------------------------------------------------------- A3


def test_a3_do_phu_va_mau_so_khong():
    g3 = g3_(vang("G1", "c1"), vang("G2", "c1", "day_qua_vi_du"), vang("G3", "c1", "chi_nhac"), vang("G4", "c2", "kien_thuc_nen"))
    hd = hd_([nd("a", day=False), nd("b")])
    can = dt.can(MA, [("G1", "a", "khop"), ("G2", "b", "may_rong_hon"), ("G3", "b", "khop")])
    rows = cham(hd, g3, can)
    assert tu_mau(rows, "a3.do_phu.nghiem") == (1, 2)        # G1 có node; G2 chỉ căn mức nới; G3 chi_nhac không vào mẫu số
    assert tu_mau(rows, "a3.do_phu.noi") == (2, 2)
    assert tu_mau(rows, "dau_cuoi.do_phu_day_hoc.nghiem") == (0, 2)   # node a không trong dãy học
    assert tu_mau(rows, "dau_cuoi.do_phu_day_hoc.noi") == (1, 2)
    r = so(rows, "a3.do_phu.nghiem", "c2")
    assert r["mau"] == 0 and dong.gia_tri(r) is None          # chương không có khái niệm dạy: mẫu số 0 cho None, không bao giờ 0


def test_a3_khai_niem_vang_khong_can_duoc_va_node_chua_can_khong_lam_tang_do_phu():
    g3 = g3_(vang("G1", "c1"), vang("G2", "c1"))
    hd = hd_([nd("a"), nd("b")])
    rows = cham(hd, g3, dt.can(MA, [("G1", "a", "khop")]))
    assert tu_mau(rows, "a3.do_phu.nghiem") == (1, 2)


# ---------------------------------------------------------------- A4


def a4_fixture():
    g3 = g3_(*(vang(g, "c1") for g in ("G1", "G2", "G3", "G4")))
    hd = hd_([nd("a"), nd("b"), nd("c", day=False), nd("d")])
    can = dt.can(MA, [("G1", "a", "khop"), ("G1", "b", "khop"), ("G2", "b", "khop"), ("G3", "c", "khop"), ("G3", "d", "khop")])
    return hd, g3, can


def test_a4_tach_chi_tinh_node_trong_day_hoc():
    rows = cham(*a4_fixture()[:2], a4_fixture()[2])
    # G1 có a, b trong dãy: tách. G2 chỉ b. G3 có d trong dãy, c ngoài dãy: không tách. G4 không căn được: ngoài mẫu số.
    assert tu_mau(rows, "a4.ti_le_tach.nghiem") == (1, 3)


def test_a4_gop_nham_va_bcubed_tinh_tay():
    rows = cham(*a4_fixture()[:2], a4_fixture()[2])
    assert tu_mau(rows, "a4.ti_le_gop_nham.nghiem") == (1, 3)      # node a, b, d trong dãy; chỉ b căn hai vàng
    p, r = so(rows, "a4.bcubed_p.nghiem", "c1"), so(rows, "a4.bcubed_r.nghiem", "c1")
    # liên kết (vàng, node trong dãy): (G1,a) (G1,b) (G2,b) (G3,d). P: 1/1, 1/2, 1/2, 1/1; R: 1/2, 1/2, 1/1, 1/1
    assert (p["tong"], p["n"]) == (3.0, 4) and (r["tong"], r["n"]) == (3.0, 4)
    assert dong.gia_tri(p) == pytest.approx(0.75)


def test_a4_node_khong_trong_day_va_khong_co_vang_cho_mau_so_khong():
    g3 = g3_(vang("G1", "c1"))
    rows = cham(hd_([nd("a", day=False)]), g3, dt.can(MA, [("G1", "a", "khop")]))
    for thuoc in ("a4.ti_le_tach.nghiem", "a4.ti_le_gop_nham.nghiem"):
        r = so(rows, thuoc, "c1")
        assert r["mau"] == 0 and dong.gia_tri(r) is None
    assert dong.gia_tri(so(rows, "a4.bcubed_p.nghiem", "c1")) is None


# ---------------------------------------------------------------- A5


def test_a5_cau_neo_dung_chuan_hoa_khoang_trang_va_muc_cung_trang():
    cau = "Cao độ là độ cao thấp của âm thanh."
    g3 = g3_(vang("G1", "c1", trang=3, cau=cau), vang("G2", "c1", trang=3, cau=cau), vang("G3", "c1", trang=3, cau=cau),
             vang("G4", "c1", "chi_nhac", trang=3, cau=""))
    hd = hd_([nd("n1", neo=(3, "cao độ  là độ cao\nthấp của âm thanh")),        # đúng câu, khác khoảng trắng và hoa thường
              nd("n2", neo=(3, "Một câu khác hẳn về nhạc lý và nhịp.")),         # cùng trang, khác câu
              nd("n3", neo=(5, cau)),                                          # đúng câu nhưng khác trang
              nd("n4", neo=(3, "x"))])
    can = dt.can(MA, [("G1", "n1", "khop"), ("G2", "n2", "khop"), ("G3", "n3", "khop"), ("G4", "n4", "khop")])
    rows = cham(hd, g3, can)
    assert tu_mau(rows, "a5.cau_neo_dung.nghiem") == (1, 3)           # G4 không có câu định nghĩa: ngoài mẫu số
    assert tu_mau(rows, "a5.cau_neo_cung_trang.nghiem") == (2, 3)     # n2 cùng trang với câu định nghĩa: tính ở mức nới


def test_a5_trang_thai_day_uncertain_ngoai_mau_so_va_ma_tran_nham_lan():
    g3 = g3_(vang("G1", "c1", "day_o_day"), vang("G2", "c1", "chi_nhac"), vang("G3", "c1", "kien_thuc_nen"),
             vang("G4", "c1", "day_qua_vi_du"))
    hd = hd_([nd("n1", status="taught"), nd("n2", status="taught"), nd("n3", status="uncertain"),
              nd("n4", status="mentioned_only")])
    can = dt.can(MA, [("G1", "n1", "khop"), ("G2", "n2", "khop"), ("G3", "n3", "khop"), ("G4", "n4", "khop")])
    rows = cham(hd, g3, can)
    assert tu_mau(rows, "a5.trang_thai_chinh_xac.nghiem") == (1, 3)    # uncertain ra khỏi mẫu số, không bị tính sai
    assert tu_mau(rows, "a5.trang_thai_phu.nghiem") == (3, 4)          # độ phủ: 3/4 cặp có quyết định
    nham = {r["thuoc"]: r["gia_tri"] for r in rows if r["thuoc"].startswith("a5.nham.") and r["thuoc"].endswith(".nghiem") and r["chuong"] == "c1" and r["gia_tri"]}
    assert nham == {"a5.nham.day_o_day.taught.nghiem": 1, "a5.nham.chi_nhac.taught.nghiem": 1,
                    "a5.nham.kien_thuc_nen.uncertain.nghiem": 1, "a5.nham.day_qua_vi_du.mentioned_only.nghiem": 1}


def test_a5_trang_thai_may_la_chuoi_la_hoac_thieu_anh_xa_bi_tu_choi():
    g3 = g3_(vang("G1", "c1"))
    hd = hd_([nd("n1", status="taught")])
    hd["khai_niem"][0]["trang_thai_day"] = "la"
    with pytest.raises(ValueError, match="ánh xạ"):
        cham(hd, g3, dt.can(MA, [("G1", "n1", "khop")]))


# ---------------------------------------------------------------- truy nguyên

TRANG = {1: "Cao độ là độ cao thấp của âm thanh. Hai câu liền nhau, câu này bắt đầu ở cuối trang một và",
         2: "kết thúc ở đầu trang hai. Trang hai còn nói về trường độ."}


def truy_nguyen_fixture():
    nodes = [nd("t1", ten="Cao độ", neo=(1, "Cao độ  là độ cao\nthấp của âm thanh.")),
             nd("t2", ten="Trường độ", neo=(1, "Hai câu liền nhau, câu này bắt đầu ở cuối trang một và kết thúc ở đầu trang hai.")),
             nd("t3", ten="Hai câu", neo=(1, "Một câu hoàn toàn bịa đặt, không hề có trong trang này đâu.")),
             nd("t4", ten="Zxq vwy", ten_khac=["Qwv zzx"], neo=None)]
    canh = [dt.canh("t1", "t2"), dt.canh("t2", "t3"), dt.canh("t3", "t4")]
    canh[0]["bang_chung"] = {"trang": 2, "cau": "Trang hai còn nói về trường độ."}
    canh[1]["bang_chung"] = {"trang": 1, "cau": "Cao độ là độ cao thấp"}
    canh[2]["bang_chung"] = None
    return hd_(nodes, canh)


def test_truy_nguyen_bang_chung_co_that_ke_ca_cau_vat_hai_trang():
    hd = truy_nguyen_fixture()
    rows = khai_niem.truy_nguyen(hd, TRANG)
    # câu neo: t1 (khác khoảng trắng), t2 (vắt hai trang) thật; t3 bịa. t4 không có câu neo: ngoài mẫu số
    assert tu_mau(rows, "truy_nguyen.cau_neo_co_that.nghiem", "toan_sach") == (2, 3)
    assert tu_mau(rows, "truy_nguyen.cau_canh_co_that.nghiem", "toan_sach") == (2, 2)
    assert tu_mau(rows, "truy_nguyen.bang_chung_co_that.nghiem", "toan_sach") == (4, 5)
    ca = khai_niem.ca_truot(hd, TRANG)
    assert [(c["loai"], c["ma"]) for c in ca] == [("cau_neo", "t3")]


def test_truy_nguyen_khai_niem_bia_va_khai_niem_canh_co_bang_chung():
    hd = truy_nguyen_fixture()
    rows = khai_niem.truy_nguyen(hd, TRANG)
    assert tu_mau(rows, "truy_nguyen.khai_niem_bia", "toan_sach") == (1, 4)       # chỉ t4: tên và mọi tên khác không có trong sách
    assert tu_mau(rows, "truy_nguyen.khai_niem_co_bang_chung", "toan_sach") == (3, 4)
    assert tu_mau(rows, "truy_nguyen.canh_co_bang_chung", "toan_sach") == (2, 3)


def test_truy_nguyen_hai_muc_nghiem_va_noi_theo_nguong():
    hd = hd_([nd("t1", neo=(1, "Cao độ là độ cao thấp của âm thanh hay là cao độ lớn."))])
    rows = khai_niem.truy_nguyen(hd, TRANG, nguong={"nghiem": 0.99, "noi": 0.5})
    assert tu_mau(rows, "truy_nguyen.cau_neo_co_that.nghiem", "toan_sach") == (0, 1)
    assert tu_mau(rows, "truy_nguyen.cau_neo_co_that.noi", "toan_sach") == (1, 1)


def test_truy_nguyen_mau_so_khong():
    rows = khai_niem.truy_nguyen(hd_([nd("t1")]), TRANG)
    assert dong.gia_tri(so(rows, "truy_nguyen.cau_neo_co_that.nghiem", "toan_sach")) is None
    assert dong.gia_tri(so(rows, "truy_nguyen.cau_canh_co_that.nghiem", "toan_sach")) is None


def test_node_bi_loai_hoac_da_gop_khong_vao_truy_nguyen():
    hd = hd_([nd("t1", neo=(1, "Cao độ là độ cao thấp của âm thanh.")), nd("t2", neo=(1, "Câu bịa hoàn toàn khác biệt."))])
    hd["khai_niem"][1]["bi_loai"] = True
    assert tu_mau(khai_niem.truy_nguyen(hd, TRANG), "truy_nguyen.cau_neo_co_that.nghiem", "toan_sach") == (1, 1)


# ---------------------------------------------------------------- dòng số đếm gộp được; giao thức; thước phụ B5


def test_moi_dong_theo_dung_dinh_dang_dong_va_gop_duoc_len_cuon():
    hd, g3, can = a4_fixture()
    rows = cham(hd, g3, can) + khai_niem.truy_nguyen(truy_nguyen_fixture(), TRANG)
    assert rows and all(set(r) >= {"he", "ma_sach", "chuong", "thuoc", "kieu"} for r in rows)
    cuon = dong.gop_cuon(rows)
    assert all(dong.gia_tri(r) is None or isinstance(dong.gia_tri(r), (int, float)) for r in cuon)
    assert len({(r["thuoc"]) for r in cuon}) == len(cuon)


def test_anh_xa_giao_thuc_nhap_doc_duoc_va_du_sau_gia_tri():
    tep = Path(__file__).resolve().parents[2] / "evaluation" / "giao-thuc" / "anh-xa-trang-thai.json"
    ax = khai_niem.doc_anh_xa(tep)
    assert ax["nhap"] is True and set(ax["may_sang_vang"]) == {"taught", "uncertain", "mentioned_only", "unchecked", "prior_knowledge", "not_subject_matter"}


def test_doc_anh_xa_tu_choi_thieu_gia_tri_hoac_gia_tri_vang_la(tmp_path):
    xau = copy.deepcopy(ANH_XA)
    del xau["may_sang_vang"]["unchecked"]
    (tmp_path / "a.json").write_text(json.dumps(xau), encoding="utf-8")
    with pytest.raises(ValueError, match="unchecked"):
        khai_niem.doc_anh_xa(tmp_path / "a.json")
    xau = copy.deepcopy(ANH_XA)
    xau["may_sang_vang"]["taught"] = ["day_o_day", "la_hoa"]
    (tmp_path / "b.json").write_text(json.dumps(xau), encoding="utf-8")
    with pytest.raises(ValueError, match="la_hoa"):
        khai_niem.doc_anh_xa(tmp_path / "b.json")


def test_thuoc_phu_b5_do_phu_va_ti_le_tach_theo_vi_tri_chuong():
    g3 = g3_(vang("G1", "c1"), vang("G2", "c1"), vang("G3", "c2"), vang("G4", "c2"))
    hd = hd_([nd("a"), nd("b"), nd("c")])
    can = dt.can(MA, [("G1", "a", "khop"), ("G2", "a", "khop"), ("G3", "b", "khop"), ("G3", "c", "khop")])
    bang_ = khai_niem.bang_theo_vi_tri_chuong(cham(hd, g3, can), g3)
    assert [(b["chuong"], b["vi_tri"], b["do_phu"], b["ti_le_tach"]) for b in bang_] == [("c1", 0, 1.0, 0.0), ("c2", 1, 0.5, 1.0)]


# ---------------------------------------------------------------- trần người


def test_tran_nguoi_cham_rieng_voi_vang_tho_cua_tung_nguoi():
    g3 = g3_(vang("G1", "c1"), vang("G2", "c1"), vang("G3", "c1"))
    hd = hd_([nd("a"), nd("b"), nd("c")], [dt.canh("a", "b"), dt.canh("b", "c")])
    can = dt.can(MA, [("G1", "a", "khop"), ("G2", "b", "khop"), ("G3", "c", "khop")])
    g4_a = dt.g4(MA, [("G1", "G2"), ("G2", "G3")])           # người A: cả hai cạnh của máy
    g4_b = dt.g4(MA, [("G1", "G2")])                          # người B: thiếu cạnh G2 > G3
    g4_hoi_y = dt.g4(MA, [("G1", "G2"), ("G2", "G3")])        # hội ý lấy cả hai (khác bản thô của B)
    ket = khai_niem.tran_nguoi(hd, {"A": (g3, g4_a, can), "B": (g3, g4_b, can)})
    f1 = lambda nguoi: dong.chi_so_f1(  # noqa: E731
        so_cuon(ket, f"tran_nguoi.{nguoi}.a8.f1_truc_tiep.nghiem"))[2]
    assert f1("A") == pytest.approx(1.0)                      # tp 2, fp 0, fn 0
    assert f1("B") == pytest.approx(2 * 1 / (2 * 1 + 1 + 0))  # tp 1, fp 1 (G2>G3 máy có, người B không có), fn 0
    # độc lập: kết quả của B khác kết quả khi chấm bằng vàng hội ý
    hoi_y = bang.cham(hd, g3, g4_hoi_y, can)
    assert dong.chi_so_f1(so_cuon(hoi_y, "a8.f1_truc_tiep.nghiem"))[2] == pytest.approx(1.0) != f1("B")
    # hệ và dòng giữ nguyên định dạng, gộp được
    assert all(r["he"] == "chinh" for r in ket)


def so_cuon(rows, thuoc):
    (r,) = [r for r in dong.gop_cuon(rows) if r["thuoc"] == thuoc]
    return r


def test_tran_nguoi_tu_choi_sach_khac_nhau_va_danh_sach_rong():
    g3 = g3_(vang("G1", "c1"))
    hd = hd_([nd("a")])
    with pytest.raises(ValueError):
        khai_niem.tran_nguoi(hd, {})
    can = dt.can(MA, [("G1", "a", "khop")])
    xau = dt.g4("KHAC", [])
    with pytest.raises(ValueError):
        khai_niem.tran_nguoi(hd, {"A": (g3, xau, can)})


def test_cli_thuoc_khai_niem_in_bang_va_ghi_ca_truot(tmp_path, capsys):
    from danhgia.__main__ import main
    hd = truy_nguyen_fixture()
    g3 = g3_(vang("G1", "c1", trang=1, cau="Cao độ là độ cao thấp của âm thanh."))
    can = dt.can(MA, [("G1", "t1", "khop")])
    tep = {"hd": hd, "g3": g3, "g4": dt.g4(MA, []), "can": can, "ax": ANH_XA, "vb": TRANG}
    for ten, gt in tep.items():
        (tmp_path / f"{ten}.json").write_text(json.dumps(gt, ensure_ascii=False), encoding="utf-8")
    ra = ["thuoc-khai-niem", "--hop-dong", str(tmp_path / "hd.json"), "--g3", str(tmp_path / "g3.json"), "--g4", str(tmp_path / "g4.json"),
          "--can", str(tmp_path / "can.json"), "--anh-xa", str(tmp_path / "ax.json"), "--van-ban", str(tmp_path / "vb.json"),
          "--ra", str(tmp_path / "bang.json"), "--ca-truot", str(tmp_path / "ca.json")]
    assert main(ra) == 0
    out = capsys.readouterr().out
    assert "a3.do_phu.nghiem" in out and "truy_nguyen.cau_neo_co_that.nghiem" in out and "ca bằng chứng khớp dưới ngưỡng nghiêm: 1" in out
    assert [c["ma"] for c in json.loads((tmp_path / "ca.json").read_text(encoding="utf-8"))] == ["t3"]
    assert json.loads((tmp_path / "bang.json").read_text(encoding="utf-8"))["theo_cuon"]


def test_khai_niem_bia_chi_khi_ten_va_moi_ten_khac_deu_vang_mat():
    hd = hd_([nd("a", ten="Zxq vwy", ten_khac=["Cao độ"]),          # tên chính không có, tên khác có trong sách: không bịa
              nd("b", ten="Zxq vwy", ten_khac=["Qwv zzx"])])         # không tên nào có: bịa
    assert tu_mau(khai_niem.truy_nguyen(hd, TRANG), "truy_nguyen.khai_niem_bia", "toan_sach") == (1, 2)


def test_cho_giu_cho_cong_thuc_cua_pipeline_khong_lam_cau_neo_tuot():
    van_ban = {1: "Khi đó độ chính xác ε của ước lượng μ được tính theo công thức: ε = t S/√n. Khoảng ước lượng của μ có dạng: μ − ε < μ < μ + ε."}
    hd = hd_([nd("a", neo=(1, "Khi đó độ chính xác ε của ước lượng μ được tính theo công thức: [formula] Khoảng ước lượng của μ có dạng: [formula]")),
              nd("b", neo=(1, "Câu bịa hoàn toàn khác biệt: [formula] không có trong trang một chữ nào cả.")),
              nd("c", neo=(1, "[formula] [formula]"))])
    rows = khai_niem.truy_nguyen(hd, van_ban)
    # a: hai mảnh chữ đều có trong trang; b: bịa; c: chỉ còn chỗ giữ chỗ, không có chữ để khớp nên ngoài mẫu số
    assert tu_mau(rows, "truy_nguyen.cau_neo_co_that.nghiem", "toan_sach") == (1, 2)
    assert [c["ma"] for c in khai_niem.ca_truot(hd, van_ban)] == ["b"]


def test_khoang_trang_quanh_ky_hieu_toan_khong_lam_cau_neo_tuot():
    van_ban = {1: "Khoảng số thực (θ1,θ2) được gọi là khoảng ước lượng của θ với độ tin cậy 1−α."}
    hd = hd_([nd("a", neo=(1, "Khoảng số thực ( θ 1 , θ 2) được gọi là khoảng ước lượng của θ với độ tin cậy 1 -α ."))])
    assert tu_mau(khai_niem.truy_nguyen(hd, van_ban), "truy_nguyen.cau_neo_co_that.nghiem", "toan_sach") == (1, 1)


def test_khoang_trang_giua_ky_hieu_va_chi_so_khop_tron_o_ngưỡng_rat_cao():
    van_ban = {1: "Ước lượng θ1 và θ2 của mẫu cho trước."}
    hd = hd_([nd("a", neo=(1, "Ước lượng θ 1 và θ 2 của mẫu cho trước."))])
    rows = khai_niem.truy_nguyen(hd, van_ban, nguong={"nghiem": 0.999, "noi": 0.5})
    assert tu_mau(rows, "truy_nguyen.cau_neo_co_that.nghiem", "toan_sach") == (1, 1)


def test_a4_bcubed_p_va_r_bat_doi_xung():
    # G1 căn 2 node (a, b); node c căn 3 vàng (G2, G3, G4). Liên kết: (G1,a) (G1,b) (G2,c) (G3,c) (G4,c)
    g3 = g3_(*(vang(g, "c1") for g in ("G1", "G2", "G3", "G4")))
    hd = hd_([nd("a"), nd("b"), nd("c")])
    can = dt.can(MA, [("G1", "a", "khop"), ("G1", "b", "khop"), ("G2", "c", "khop"), ("G3", "c", "khop"), ("G4", "c", "khop")])
    rows = cham(hd, g3, can)
    p, r = so(rows, "a4.bcubed_p.nghiem", "c1"), so(rows, "a4.bcubed_r.nghiem", "c1")
    # P = (1 + 1 + 1/3 + 1/3 + 1/3) / 5 = 3/5 ; R = (1/2 + 1/2 + 1 + 1 + 1) / 5 = 4/5 (tính tay)
    assert (p["tong"], p["n"]) == (pytest.approx(3.0), 5) and (r["tong"], r["n"]) == (pytest.approx(4.0), 5)
    assert dong.gia_tri(p) == pytest.approx(0.6) and dong.gia_tri(r) == pytest.approx(0.8)


def test_anh_xa_nhap_unchecked_khong_quyet_dinh_not_subject_matter_luon_sai():
    tep = Path(__file__).resolve().parents[2] / "evaluation" / "giao-thuc" / "anh-xa-trang-thai.json"
    ax = khai_niem.doc_anh_xa(tep)["may_sang_vang"]
    assert ax["unchecked"] is None and ax["uncertain"] is None and ax["not_subject_matter"] == []
    g3 = g3_(vang("G1", "c1", "day_o_day"), vang("G2", "c1", "chi_nhac"), vang("G3", "c1", "day_o_day"))
    hd = hd_([nd("n1", status="not_subject_matter"), nd("n2", status="not_subject_matter"), nd("n3", status="unchecked")])
    rows = khai_niem.cham_khai_niem(hd, g3, dt.g4(MA, []), dt.can(MA, [("G1", "n1", "khop"), ("G2", "n2", "khop"), ("G3", "n3", "khop")]),
                                    {}, khai_niem.doc_anh_xa(tep))
    assert tu_mau(rows, "a5.trang_thai_chinh_xac.nghiem") == (0, 2)       # hai cặp not_subject_matter luôn sai; unchecked ra khỏi mẫu số
    assert tu_mau(rows, "a5.trang_thai_phu.nghiem") == (2, 3)
