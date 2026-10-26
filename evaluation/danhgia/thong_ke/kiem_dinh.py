"""Kiểm định so hai hệ: hoán vị ghép cặp phân tầng theo chương, sign test theo cuốn, hiệu chỉnh Holm (spec mục 9)."""
from math import comb

from danhgia.thong_ke.lcg import Lcg
from danhgia.thong_ke.so_dem import dem_theo_chuong, gia_tri_cuon, trung_binh_macro


def _hieu_macro(kieu, cap):
    """`cap`: `{sach: [(đếm A, đếm B) theo chương]}` → macro(A) − macro(B), thước mỗi cuốn tính từ tổng số đếm."""
    a = trung_binh_macro(gia_tri_cuon(kieu, [x for x, _ in chuong]) for chuong in cap.values())
    b = trung_binh_macro(gia_tri_cuon(kieu, [y for _, y in chuong]) for chuong in cap.values())
    if a is None or b is None:
        return None
    return a - b


def hoan_vi_ghep_cap(rows, he_a, he_b, *, thuoc, so_lan=10000, seed=20261114):
    """p hai phía. Mỗi lần hoán vị đổi nhãn hai hệ trong từng chương với xác suất ½; không bao giờ trộn chương giữa các cuốn.

    Chương nào chỉ có một hệ thì không ghép cặp được: báo lỗi thay vì lặng lẽ bỏ, vì bỏ chương làm đổi mẫu.
    """
    kieu_a, dem_a = dem_theo_chuong(rows, he_a, thuoc)
    kieu_b, dem_b = dem_theo_chuong(rows, he_b, thuoc)
    if kieu_a != kieu_b:
        raise ValueError("hai hệ phải cùng kiểu thước")
    khoa_a = {(s, c) for s, ch in dem_a.items() for c in ch}
    khoa_b = {(s, c) for s, ch in dem_b.items() for c in ch}
    if khoa_a != khoa_b:
        raise ValueError(f"chương lệch giữa hai hệ: {sorted(khoa_a ^ khoa_b)[:5]}")
    cap = {s: [(dem_a[s][c], dem_b[s][c]) for c in sorted(dem_a[s])] for s in sorted(dem_a)}
    quan_sat = _hieu_macro(kieu_a, cap)
    if quan_sat is None:
        return {"hieu": None, "p": None, "so_lan": so_lan}
    sinh = Lcg(seed)
    cuc_doan = 0
    for _ in range(so_lan):
        xao = {s: [(y, x) if sinh.dong_xu() else (x, y) for x, y in chuong] for s, chuong in cap.items()}
        hieu = _hieu_macro(kieu_a, xao)
        # Sai số dấu phẩy động: hiệu bằng đúng hiệu quan sát vẫn phải tính là cực đoan.
        if hieu is not None and abs(hieu) >= abs(quan_sat) - 1e-12:
            cuc_doan += 1
    return {"hieu": quan_sat, "p": (cuc_doan + 1) / (so_lan + 1), "so_lan": so_lan}


def sign_test(thang, thua):
    """p hai phía của kiểm định dấu nhị thức chính xác; hoà đã loại trước. Không có cặp nào thì `None`."""
    n = thang + thua
    if n == 0:
        return None
    k = min(thang, thua)
    duoi = sum(comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * duoi)


def holm(p_theo_ten):
    """p đã hiệu chỉnh Holm–Bonferroni: nhân (m − i + 1) theo thứ tự tăng, lấy cực đại tích luỹ, chặn ở 1."""
    thu_tu = sorted(p_theo_ten.items(), key=lambda kv: (kv[1], kv[0]))
    m = len(thu_tu)
    ket, cuc_dai = {}, 0.0
    for i, (ten, p) in enumerate(thu_tu):
        cuc_dai = max(cuc_dai, min(1.0, (m - i) * p))
        ket[ten] = cuc_dai
    return ket
