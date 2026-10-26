"""A9/A10: Q6 theo dãy học, Q7, Q7b, số chu trình, số thành phần liên thông.

Dãy học cho mỗi khái niệm đúng một vị trí, nên không còn rổ "cùng stage". Q6 chia cho **toàn bộ** cạnh vàng trong phạm vi.
"""
from __future__ import annotations

from .do_thi import so_chu_trinh, so_thanh_phan, to_tien


def hang_vi_tri(day_hoc):
    if len(set(day_hoc)) != len(day_hoc):
        lap = sorted({x for x in day_hoc if day_hoc.count(x) > 1})
        raise ValueError(f"dãy học có khái niệm lặp {lap}; mỗi khái niệm một vị trí")
    return {nut: chi_so for chi_so, nut in enumerate(day_hoc)}


def q6(cap_vang, hang):
    """(số cạnh vàng đặt ngược hoặc có đầu ngoài dãy học, tổng cạnh vàng trong phạm vi)."""
    loi = 0
    for nguon, dich in cap_vang:
        if nguon not in hang or dich not in hang or hang[nguon] >= hang[dich]:
            loi += 1
    return loi, len(cap_vang)


def _canh_trong_day(canh_may, hang):
    return {(a, b) for a, b in canh_may if a in hang and b in hang}


def q7(cap_vang_toan_cuon, canh_may, dich, hang):
    """Với mỗi đích có tổ tiên vàng: phần tổ tiên vàng nằm trong tổ tiên máy. Trả (tổng tỉ lệ, số đích, số đích trọn)."""
    vang, may = to_tien(cap_vang_toan_cuon), to_tien(_canh_trong_day(canh_may, hang))
    tong, n, tron = 0.0, 0, 0
    for nut in sorted(dich):
        can = vang.get(nut, set())
        if not can:
            continue
        co = may.get(nut, set())
        tong += len(can & co) / len(can)
        n += 1
        tron += can <= co
    return tong, n, tron


def q7b(cap_vang_toan_cuon, canh_may, dich, hang):
    """Tổ tiên máy thuộc chương vàng có thật sự cần không. Trả (tổng độ chính xác, số đích có tổ tiên máy)."""
    vang, may = to_tien(cap_vang_toan_cuon), to_tien(_canh_trong_day(canh_may, hang))
    pham_vi, tong, n = set(dich), 0.0, 0
    for nut in sorted(dich):
        co = may.get(nut, set()) & pham_vi
        if co:
            tong += len(co & vang.get(nut, set())) / len(co)
            n += 1
    return tong, n


def cau_truc_do_thi(canh_cung, day_hoc):
    nut = set(day_hoc)
    trong = {(a, b) for a, b in canh_cung if a in nut and b in nut}
    return so_chu_trinh(nut, trong), so_thanh_phan(nut, trong)
