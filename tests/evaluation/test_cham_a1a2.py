"""Vé DG-13: chấm A1 (M1, M2, M3, complete entry) và A2 (recall noi_dung, F1 sáu vai trò, ma trận nhầm, lỗi có hại).

Fixture tự soạn (nhạc lý, bảng dòng ASCII), số tính tay. Đối chiếu số với `scripts/a1-d02/cham_d02.py` bằng tiến trình con.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from danhgia.cham import a1a2, dong

GOC = Path(__file__).resolve().parents[2]
CHAM_D02 = GOC / "scripts" / "a1-d02" / "cham_d02.py"
MA = "dev-nhac"

DONG = [
    ("p0001-l001", 1, "LOI NOI DAU"), ("p0001-l002", 1, "Day la loi noi dau cua sach."),
    ("p0002-l001", 2, "CHUONG 1"), ("p0002-l002", 2, "Giai thich ve cao do va truong do."),
    ("p0002-l003", 2, "1.1 Cao do"), ("p0002-l004", 2, "Cao do la do cao thap."),
    ("p0003-l001", 3, "1.2 Truong do"), ("p0003-l002", 3, "Truong do la do dai."),
    ("p0003-l003", 3, "BAI TAP"), ("p0003-l004", 3, "Bai 1 hay lam bai."),
    ("p0004-l001", 4, "Giao trinh nhac ly 4"), ("p0004-l002", 4, "CHUONG 1"), ("p0004-l003", 4, "Noi dung cuoi sach nhac ly."),
]
BANG = [{"id": i, "trang": t, "text": x} for i, t, x in DONG]


def kt(chuoi):
    return sum(not c.isspace() for c in chuoi)


CHARS = {i: kt(x) for i, _, x in DONG}


def h(i, dong_, text, cap, cha, vai_tro, vung=None):
    return {"sach": MA, "id": i, "dong": dong_, "text": text, "cap": cap, "cha": cha, "vung": vai_tro if cap == 1 else None,
            "vai_tro": vai_tro, "ghi_chu": ""}


VANG = [h("h1", ["p0001-l001"], "LOI NOI DAU", 1, None, "mo_dau"),
        h("h2", ["p0002-l001"], "CHUONG 1", 1, None, "noi_dung"),
        h("h3", ["p0002-l003"], "1.1 Cao do", 2, "h2", "noi_dung"),
        h("h4", ["p0003-l001"], "1.2 Truong do", 2, "h2", "noi_dung"),
        h("h5", ["p0003-l003"], "BAI TAP", 1, None, "bai_tap")]
# hệ: 1.2 sai cấp (3) và sai vai trò, thiếu BAI TAP, thừa tiêu đề "Bai 1 ..." ở p0003-l004
DU_DOAN = {"headings": [h("a1", ["p0001-l001"], "LOI NOI DAU", 1, None, "mo_dau"),
                        h("a2", ["p0002-l001"], "CHUONG 1", 1, None, "noi_dung"),
                        h("a3", ["p0002-l003"], "1.1 Cao do", 2, "a2", "noi_dung"),
                        h("a4", ["p0003-l001"], "1.2 Truong do", 3, "a3", "bai_tap"),
                        h("a5", ["p0003-l004"], "Bai 1 hay lam bai.", 2, "a2", "bai_tap")],
           "evaluation_excluded": ["p0004-l001"]}


def cham(**kw):
    return a1a2.cham(VANG, DU_DOAN, BANG, he="chinh", ma_sach=MA, **kw)


def tm(rows, thuoc, chuong="toan_sach"):
    (r,) = [r for r in rows if r["thuoc"] == thuoc and r["chuong"] == chuong]
    return r


def tu_mau(rows, thuoc, chuong="toan_sach"):
    r = tm(rows, thuoc, chuong)
    return r["tu"], r["mau"]


# ---------------------------------------------------------------- A1


def test_m1_m2_complete_entry_tinh_tay():
    rows = cham()
    m1 = tm(rows, "a1.m1")
    assert (m1["tp"], m1["fp"], m1["fn"]) == (4, 1, 1)                  # 4 khớp, thừa "Bai 1", thiếu BAI TAP
    ce = tm(rows, "a1.complete_entry")
    assert (ce["tp"], ce["fp"], ce["fn"]) == (3, 2, 2)                  # 1.2 khớp tiêu đề nhưng sai cấp
    assert tu_mau(rows, "a1.m2") == (3, 4)                              # cha của 1.2 sai vì cấp sai; mẫu số là 4 tiêu đề khớp


def test_m3_chi_tinh_than_bai_va_loai_dau_chan_trang():
    rows = cham()
    # lá vàng: p1 -> h1; p2 l1,l2 -> h2; p2 l3,l4 -> h3; p3 l1,l2 -> h4; p3 l3,l4 -> h5 và hết sách -> h5.
    # lá hệ (theo vị trí): p3 l3 -> a4 (1.2) nên sai, p3 l4 và p4 -> a5 (tiêu đề thừa, không khớp) nên sai.
    dung = ["p0001-l001", "p0001-l002", "p0002-l001", "p0002-l002", "p0002-l003", "p0002-l004", "p0003-l001", "p0003-l002"]
    than = dung + ["p0003-l003", "p0003-l004", "p0004-l002", "p0004-l003"]       # p0004-l001 là dòng đầu trang bị loại
    assert tu_mau(rows, "a1.m3") == (sum(CHARS[i] for i in dung), sum(CHARS[i] for i in than))


def test_m3_theo_chuong_cong_lai_thanh_ca_cuon():
    chuong = [{"ma": "c1", "trang_dau": 2, "trang_cuoi": 3}]
    rows = cham(chuong=chuong)
    assert {r["chuong"] for r in rows} == {"c1", "ngoai_chuong"}
    cuon = {r["thuoc"]: r for r in dong.gop_cuon(rows)}
    tong = {r["thuoc"]: r for r in cham() if r["chuong"] == "toan_sach"}
    for thuoc in ("a1.m1", "a1.complete_entry", "a1.m2", "a1.m3"):
        assert dong.gia_tri(cuon[thuoc]) == dong.gia_tri(tong[thuoc])
    trip = lambda c: (tm(rows, "a1.m1", c)["tp"], tm(rows, "a1.m1", c)["fp"], tm(rows, "a1.m1", c)["fn"])  # noqa: E731
    assert trip("c1") == (3, 1, 1) and trip("ngoai_chuong") == (1, 0, 0)


def test_khop_tieu_de_khac_trang_khong_phai_khop_va_mau_so_khong():
    du_doan = {"headings": [h("a1", ["p0004-l002"], "CHUONG 1", 1, None, "noi_dung")], "evaluation_excluded": []}   # cùng chữ, trang 4
    rows = a1a2.cham(VANG[1:2], du_doan, BANG, he="chinh", ma_sach=MA)
    m1 = tm(rows, "a1.m1")
    assert (m1["tp"], m1["fp"], m1["fn"]) == (0, 1, 1)
    assert tm(rows, "a1.m2")["mau"] == 0 and dong.gia_tri(tm(rows, "a1.m2")) is None   # mẫu số 0 cho None, không bao giờ 0


def test_dinh_vi_tieu_de_hop_dong_theo_chu_va_trang():
    hd_td = [{"ma": "s1", "chu": "CHUONG 1", "cap": 1, "cha": None, "trang": 2, "ma_dong": None},
             {"ma": "s2", "chu": "CHUONG 1", "cap": 1, "cha": None, "trang": 4, "ma_dong": None},
             {"ma": "s3", "chu": "Khong co tren trang", "cap": 2, "cha": "s1", "trang": 2, "ma_dong": None}]
    hd = {"cau_truc": {"tieu_de": hd_td, "muc": [{"ma": "s1", "vai_tro": "noi_dung"}, {"ma": "s2", "vai_tro": "noi_dung"},
                                                 {"ma": "s3", "vai_tro": "noi_dung"}], "doan_van": []}}
    du_doan = a1a2.du_doan_tu_hop_dong(hd, BANG)
    theo = {x["id"]: x for x in du_doan["headings"]}
    assert theo["s1"]["dong"] == ["p0002-l001"] and theo["s2"]["dong"] == ["p0004-l002"]   # đúng trang, không lấy nhầm cùng chữ ở trang khác
    assert theo["s3"]["dong"] == [] and du_doan["khong_dinh_vi"] == ["s3"]


# ---------------------------------------------------------------- A2


def test_recall_noi_dung_theo_muc_va_theo_ky_tu_khac_nhau():
    rows = cham()
    assert tu_mau(rows, "a2.recall_noi_dung_muc") == (2, 3)             # h2, h3 đúng; h4 bị gán bai_tap
    # theo ký tự: dòng thuộc mục vàng noi_dung = p2 (l1..l4) và p3 (l1, l2); hệ đúng ở p2, sai ở p3
    dung = ["p0002-l001", "p0002-l002", "p0002-l003", "p0002-l004"]
    sai = ["p0003-l001", "p0003-l002"]
    tu, mau = tu_mau(rows, "a2.recall_noi_dung_ky_tu")
    assert (tu, mau) == (sum(CHARS[i] for i in dung), sum(CHARS[i] for i in dung + sai))
    assert tu / mau != 2 / 3                                            # ký tự và mục cho số khác nhau


def test_ma_tran_nham_lan_va_f1_sau_vai_tro():
    rows = cham()
    mt = {r["thuoc"]: r["gia_tri"] for r in rows if r["thuoc"].startswith("a2.nham.") and r["gia_tri"]}
    assert mt == {"a2.nham.mo_dau.mo_dau": 1, "a2.nham.noi_dung.noi_dung": 2, "a2.nham.noi_dung.bai_tap": 1,
                  "a2.nham.bai_tap.khong_khop": 1}
    f = {v: (tm(rows, f"a2.f1_vai_tro.{v}")["tp"], tm(rows, f"a2.f1_vai_tro.{v}")["fp"], tm(rows, f"a2.f1_vai_tro.{v}")["fn"])
         for v in a1a2.VAI_TRO}
    assert f["noi_dung"] == (2, 0, 1) and f["bai_tap"] == (0, 1, 1) and f["mo_dau"] == (1, 0, 0) and f["cuoi_sach"] == (0, 0, 0)
    macro = a1a2.macro_f1_vai_tro(dong.gop_cuon(rows))
    # mo_dau 1,0; noi_dung 2*2/(2*2+0+1)=0,8; bai_tap 0; ba vai trò còn lại có mẫu số 0 nên ra khỏi trung bình: (1 + 0,8 + 0) / 3
    assert macro["gia_tri"] == pytest.approx((1 + 0.8 + 0) / 3) and macro["so_vai_tro_co_so"] == 3


G3_KN = [
    {"ma": "G-1", "chuong": "c1", "ten": "Cao do", "dinh_nghia": {"trang": 2, "cau": "Cao do la do cao thap."}},
    {"ma": "G-2", "chuong": "c1", "ten": "Truong do", "dinh_nghia": {"trang": 3, "cau": "Truong do la do dai."}},
    {"ma": "G-3", "chuong": "c1", "ten": "Cuong do", "dinh_nghia": {"trang": None, "cau": ""}},          # không có câu: không đếm
    {"ma": "G-4", "chuong": "c1", "ten": "Bai", "dinh_nghia": {"trang": 3, "cau": "Bai 1 hay lam bai."}},
]


def test_loi_co_hai_chi_dem_khai_niem_co_cau_dinh_nghia():
    rows = cham(g3_khai_niem=G3_KN)
    # G-1 nằm trong 1.1 (hệ noi_dung): không hại. G-2 trong 1.2 (hệ bai_tap): hại. G-4 trong mục thừa (hệ bai_tap): hại. G-3 ngoài mẫu số.
    assert tu_mau(rows, "a2.loi_co_hai") == (2, 3)
    assert tm(rows, "a2.khong_dinh_vi_cau")["gia_tri"] == 0


def test_loi_co_hai_cau_khong_tim_thay_tren_trang_dem_rieng():
    kn = G3_KN[:1] + [{"ma": "G-9", "chuong": "c1", "ten": "X", "dinh_nghia": {"trang": 2, "cau": "Mot cau hoan toan khac khong co tren trang nay dau."}}]
    rows = cham(g3_khai_niem=kn)
    assert tu_mau(rows, "a2.loi_co_hai") == (0, 1)
    assert tm(rows, "a2.khong_dinh_vi_cau")["gia_tri"] == 1


def test_khong_co_vai_tro_cua_he_la_khong_noi_dung():
    du_doan = {"headings": [dict(x, vai_tro=None) for x in DU_DOAN["headings"]], "evaluation_excluded": []}
    rows = a1a2.cham(VANG, du_doan, BANG, he="chinh", ma_sach=MA)
    assert tu_mau(rows, "a2.recall_noi_dung_muc") == (0, 3)


# ---------------------------------------------------------------- đối chiếu bộ chấm D-02


def test_m1_m2_m3_bang_dung_so_cua_cham_d02(tmp_path):
    thu_muc = tmp_path / "d02"
    for ten in ("dong", "cay-muc", "chon-trang-mau"):
        (thu_muc / ten).mkdir(parents=True)
    (thu_muc / "dong" / f"{MA}.jsonl").write_text("".join(json.dumps(x) + "\n" for x in BANG), encoding="utf-8")
    (thu_muc / "cay-muc" / f"{MA}.jsonl").write_text("".join(json.dumps(x) + "\n" for x in VANG), encoding="utf-8")
    (thu_muc / "chon-trang-mau" / f"{MA}.json").write_text('{"trang": []}', encoding="utf-8")
    leaf = {}
    cur = None
    starts = {a["dong"][0]: a["id"] for a in DU_DOAN["headings"]}
    for x in BANG:
        cur = starts.get(x["id"], cur)
        leaf[x["id"]] = {"role": "than_bai", "leaf": cur}
    pred = {"headings": DU_DOAN["headings"], "lines": leaf, "evaluation_excluded": DU_DOAN["evaluation_excluded"], "reading_order": {}, "chunks": []}
    (tmp_path / "pred.json").write_text(json.dumps(pred), encoding="utf-8")
    kq = subprocess.run([sys.executable, "-X", "utf8", str(CHAM_D02), "--sach", MA, "--thu-muc", str(thu_muc), "--prediction",
                         str(tmp_path / "pred.json"), "--out", str(tmp_path / "ra.json")], capture_output=True, text=True,
                        encoding="utf-8", cwd=CHAM_D02.parent)
    assert kq.returncode == 0, kq.stdout + kq.stderr
    cu = json.loads((tmp_path / "ra.json").read_text(encoding="utf-8"))
    moi = a1a2.cham(VANG, dict(DU_DOAN, lines=leaf), BANG, he="chinh", ma_sach=MA)
    m1, m2, m3 = tm(moi, "a1.m1"), tm(moi, "a1.m2"), tm(moi, "a1.m3")
    assert (m1["tp"], m1["fp"], m1["fn"]) == (cu["M1"]["tp"], cu["M1"]["fp"], cu["M1"]["fn"])
    assert (m2["tu"], m2["mau"]) == (cu["M2"]["correct"], cu["M2"]["matched"])
    assert (m3["tu"], m3["mau"]) == (cu["M3"]["correct_chars"], cu["M3"]["total_chars"])


def test_cli_cham_a1a2(tmp_path, capsys):
    from danhgia.__main__ import main
    tep = {"vang": VANG, "du_doan": DU_DOAN, "dong": BANG}
    for ten, gt in tep.items():
        (tmp_path / f"{ten}.json").write_text(json.dumps(gt), encoding="utf-8")
    ra = ["cham-a1a2", "--vang", str(tmp_path / "vang.json"), "--du-doan", str(tmp_path / "du_doan.json"), "--dong",
          str(tmp_path / "dong.json"), "--he", "chinh", "--ma-sach", MA, "--ra", str(tmp_path / "bang.json")]
    assert main(ra) == 0
    out = capsys.readouterr().out
    assert "a1.m1" in out and "a2.recall_noi_dung_muc" in out
    assert json.loads((tmp_path / "bang.json").read_text(encoding="utf-8"))["theo_cuon"]


def test_khop_tieu_de_can_phu_tu_nua_so_dong_vang_tro_len():
    bang = [{"id": f"p0005-l{i:03d}", "trang": 5, "text": f"dong {i} cua tieu de dai"} for i in range(1, 5)]
    vang = [h("g", [b["id"] for b in bang], "tieu de dai", 1, None, "noi_dung")]
    ma = lambda *ids: {"headings": [h("a", [bang[i]["id"] for i in ids], "x", 1, None, "noi_dung")], "evaluation_excluded": []}  # noqa: E731
    dem = lambda dd: tm(a1a2.cham(vang, dd, bang, he="chinh", ma_sach=MA), "a1.m1")["tp"]  # noqa: E731
    assert dem(ma(0)) == 0                    # 1/4 dòng: chưa đủ nửa
    assert dem(ma(0, 1)) == 1                 # 2/4 dòng: đủ nửa


def test_macro_f1_bo_vai_tro_khong_co_muc_vang_khoi_trung_binh_khong_tinh_thanh_0():
    rows = [dong.f1("chinh", MA, "cuon", "a2.f1_vai_tro.noi_dung", 1, 0, 0), dong.f1("chinh", MA, "cuon", "a2.f1_vai_tro.mo_dau", 0, 0, 0)]
    kq = a1a2.macro_f1_vai_tro(rows)
    assert kq["gia_tri"] == 1.0 and (kq["so_vai_tro_co_so"], kq["so_vai_tro"]) == (1, 2)
