"""Fixture dựng tay cho test `bang-hinh` (vé DG-17): 3 cuốn (A, B, C) × 2 chương (c1, c2), số tính tay ghi cạnh từng khối.

Hệ chính, B1, B5 có dòng số đếm; trần người đến từ tệp đồng thuận G4; chi phí đến từ khối `chi_phi` của hợp đồng.
"""
import json
from pathlib import Path

from danhgia.cham import dong

SACH = ("A", "B", "C")
CHU_DE = {"A": "Toán rời rạc", "B": "Xác suất thống kê", "C": "Máy học"}
SECRET = "BI-MAT-GIA-KHAI-NIEM-XYZ"
F1 = "a8.f1_truc_tiep.nghiem"
Q6 = "a10.q6.nghiem"
BC = "truy_nguyen.bang_chung_co_that.nghiem"
DP = "dau_cuoi.do_phu_day_hoc.nghiem"


def _f1(he, thuoc, theo_sach):
    return [dong.f1(he, s, f"c{i + 1}", thuoc, *d) for s, ds in theo_sach.items() for i, d in enumerate(ds)]


def _ti_le(he, thuoc, theo_sach, chuong=None):
    return [dong.ti_le(he, s, chuong or f"c{i + 1}", thuoc, *d) for s, ds in theo_sach.items() for i, d in enumerate(ds)]


# F1 hệ chính: A (14,6,6) -> 28/40 = 0,7; B (10,10,10) -> 0,5; C (18,2,2) -> 0,9; macro 0,7
F1_CHINH = {"A": [(8, 2, 2), (6, 4, 4)], "B": [(5, 5, 5), (5, 5, 5)], "C": [(9, 1, 1), (9, 1, 1)]}
# F1 B5: A 0,6; B 0,4; C 0,8; macro 0,6
F1_B5 = {"A": [(6, 4, 4), (6, 4, 4)], "B": [(4, 6, 6), (4, 6, 6)], "C": [(8, 2, 2), (8, 2, 2)]}
F1_B1 = {s: [(1, 9, 9), (1, 9, 9)] for s in SACH}        # 4/40 = 0,1 mỗi cuốn
# hai lượt nhiễu của hệ chính: macro 0,6 và 0,8, nên dải nhiễu [0,6; 0,8] rộng 0,2
F1_NHIEU_1 = {"A": [(7, 3, 3), (5, 5, 5)], "B": [(4, 6, 6), (4, 6, 6)], "C": [(8, 2, 2), (8, 2, 2)]}
F1_NHIEU_2 = {"A": [(9, 1, 1), (7, 3, 3)], "B": [(6, 4, 4), (6, 4, 4)], "C": [(10, 0, 0), (10, 0, 0)]}
# Q6 hệ chính: A 3/20 = 0,15; B 5/20 = 0,25; C 2/20 = 0,1; macro 1/6
Q6_CHINH = {"A": [(1, 10), (2, 10)], "B": [(2, 10), (3, 10)], "C": [(1, 10), (1, 10)]}
# Q6 B1: cuốn C mẫu số 0 (chưa đo được): macro (0,55 + 0,7) / 2 = 0,625 trên 2 cuốn
Q6_B1 = {"A": [(5, 10), (6, 10)], "B": [(7, 10), (7, 10)], "C": [(0, 0), (0, 0)]}
# tắt R17: mọi chương hơn hệ chính đúng 1/10, nên hiệu là +0,1 ở mọi lần lấy lại mẫu và CI suy biến
Q6_TAT_R17 = {"A": [(2, 10), (3, 10)], "B": [(3, 10), (4, 10)], "C": [(2, 10), (2, 10)]}
BC_CHINH = {"A": [(95, 100)], "B": [(90, 100)], "C": [(80, 100)]}      # macro (0,95 + 0,9 + 0,8) / 3
BC_B5 = {"A": [(90, 100)], "B": [(60, 100)], "C": [(50, 100)]}
DP_CHINH = {"A": [(8, 10), (9, 10)], "B": [(7, 10), (7, 10)], "C": [(10, 10), (10, 10)]}   # 0,85; 0,7; 1; macro 0,85


def dong_he_chinh():
    return (_f1("chinh", F1, F1_CHINH) + _ti_le("chinh", Q6, Q6_CHINH) + _ti_le("chinh", BC, BC_CHINH, "toan_sach")
            + _ti_le("chinh", DP, DP_CHINH))


def dong_b1():
    return _f1("b1", F1, F1_B1) + _ti_le("b1", Q6, Q6_B1)


def dong_b5():
    return _f1("b5", F1, F1_B5) + _ti_le("b5", BC, BC_B5, "toan_sach")


def dong_tat_r17():
    return _ti_le("tat_r17", Q6, Q6_TAT_R17)


def dong_nhieu(f1):
    return _f1("xao", F1, f1)


# Quy lỗi hệ chính (mỗi chương: số đúng và số cạnh vàng mất ở lý do 1..7); lý do 1 và 5 không áp. Tổng 60 cạnh = 27 đúng + 9 + 5 + 3 + 10 + 6
QUY_LOI = {"A": [(4, [0, 2, 1, 0, 0, 2, 1]), (5, [0, 1, 1, 1, 0, 1, 1])], "B": [(3, [0, 3, 0, 1, 0, 2, 1]), (6, [0, 0, 1, 0, 0, 2, 1])],
           "C": [(7, [0, 1, 0, 0, 0, 1, 1]), (2, [0, 2, 2, 1, 0, 2, 1])]}
TONG_QUY_LOI = {"tong": 60, "dung": 27, "ly_do": {1: None, 2: 9, 3: 5, 4: 3, 5: None, 6: 10, 7: 6}}


def quy_loi(sach, khong_ap=(1, 5), them=None):
    rows = []
    for i, (dung, ly_do) in enumerate(QUY_LOI[sach]):
        c = f"c{i + 1}"
        gia = {"quy_loi.vang_pham_vi.nghiem": dung + sum(ly_do), "quy_loi.dung.nghiem": dung,
               **{f"quy_loi.ly_do_{k + 1}.nghiem": v for k, v in enumerate(ly_do)}, **(them or {})}
        rows += [dong.dem("chinh", sach, c, t, v) for t, v in gia.items()]
    return {"theo_chuong": rows, "theo_cuon": [], "meta": {"khong_ap": list(khong_ap), "ly_do_5_khong_ap": 5 in khong_ap, "cua_so_thieu": False,
                                                          "so_canh_vang": 20}}


def dong_thuan(a, b, c):
    """Tệp đồng thuận G4 giống `vang.g4.dem_g4` ở phần dùng đến: mỗi chương một khối `tong` có a, b, c."""
    return {"khong_bac_cau": {"theo_chuong": {ch: {"tong": {"a": a, "b": b, "c": c, "f1": None}} for ch in ("c1", "c2")}}}


# trần người: A (16,2,2) -> 32/36; B (12,4,4) -> 24/32 = 0,75; C (8,6,6) -> 16/28; macro 0,7368
DONG_THUAN = {"A": dong_thuan(8, 1, 1), "B": dong_thuan(6, 2, 2), "C": dong_thuan(4, 3, 3)}


def hop_dong(he, giay, cho, usd):
    chi_phi = None if giay is False else {"theo_khau": {}, "ghi_chu": None,
                                          "tong": {"giay_chay": giay, "giay_cho_embedding": cho, "so_loi_goi_mo_hinh": 0, "token_vao": 0, "token_ra": 0,
                                                   "so_loi_goi_embedding": 0, "usd": usd}}
    return {"dinh_danh": {"he": he}, "chi_phi": chi_phi,
            "khai_niem": [{"ma": "k1", "ten": SECRET + "-TEN", "cau_neo": SECRET + "-CAU"}]}


# chinh: 10, 20, 30 phút (không chờ embedding: 9, 18, 27); USD 0,004; 0,004; 0,008 (trung bình 0,00533 làm tròn 0,01, còn làm tròn từng cuốn trước ra 0,003)
HOP_DONG = {
    "chinh": {"A": hop_dong("chinh", 600, 60, 0.004), "B": hop_dong("chinh", 1200, 120, 0.004), "C": hop_dong("chinh", 1800, 180, 0.008)},
    # B1: tính lại từ artifact, không đo thời gian (null), USD 0
    "b1": {s: hop_dong("b1", None, None, 0.0) for s in SACH},
    # B5 chưa có khối chi phí
    "b5": {s: hop_dong("b5", False, None, None) for s in SACH},
}


def ghi_json(duong, gia_tri):
    Path(duong).write_text(json.dumps(gia_tri, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return str(duong)


def manifest(ma_sach, tap="phat_trien", **them):
    return {"schema": "danh-gia-sach-1", "ma_sach": ma_sach, "chu_de": CHU_DE[ma_sach], "tap": tap, **them}


def dung_thu_muc(thu_muc, *, tap="phat_trien", them_manifest=None, co_b5=True):
    """Ghi mọi tệp đầu vào vào `thu_muc`; trả danh sách đối số CLI (không có `--ra`)."""
    thu_muc = Path(thu_muc)
    rows = dong_he_chinh() + dong_b1() + (dong_b5() if co_b5 else []) + dong_tat_r17()
    argv = ["bang-hinh", "--dong", ghi_json(thu_muc / "dong.json", rows)]
    argv += ["--manifest", *[ghi_json(thu_muc / f"m-{s}.json", manifest(s, tap, **(them_manifest or {}))) for s in SACH]]
    for he, theo in HOP_DONG.items():
        for sach, hd in theo.items():
            argv += ["--hop-dong", f"{sach}={ghi_json(thu_muc / f'hd-{he}-{sach}.json', hd)}"]
    for sach, kq in DONG_THUAN.items():
        argv += ["--dong-thuan", f"{sach}={ghi_json(thu_muc / f'dt-{sach}.json', kq)}"]
    argv += ["--quy-loi", *[ghi_json(thu_muc / f"ql-{sach}.json", quy_loi(sach)) for sach in SACH]]
    argv += ["--nhieu", ghi_json(thu_muc / "nhieu-1.json", dong_nhieu(F1_NHIEU_1)), ghi_json(thu_muc / "nhieu-2.json", dong_nhieu(F1_NHIEU_2))]
    return argv
