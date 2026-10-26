"""A9/A10: Q6 theo dãy học, Q7, Q7b, số chu trình, số thành phần liên thông, tính trong không gian vàng.

Dãy học cho mỗi node đúng một vị trí, nên không còn rổ "cùng stage". Vị trí của một **khái niệm vàng** là vị trí **sớm nhất**
trong các node căn với nó; khái niệm vàng không có node nào trong dãy thì không có vị trí. Q6 chia cho **toàn bộ** cạnh vàng
trong phạm vi.
"""
from __future__ import annotations

from .do_thi import so_chu_trinh, so_thanh_phan, to_tien


def hang_nut(day_hoc):
    if len(set(day_hoc)) != len(day_hoc):
        lap = sorted({x for x in day_hoc if day_hoc.count(x) > 1})
        raise ValueError(f"dãy học có khái niệm lặp {lap}; mỗi khái niệm một vị trí")
    return {nut: chi_so for chi_so, nut in enumerate(day_hoc)}


def vi_tri_vang(hang, nut_cua_vang):
    """khái niệm vàng -> vị trí sớm nhất trong dãy học (bỏ khái niệm không có node nào trong dãy)."""
    ket_qua = {}
    for khoa, nuts in nut_cua_vang.items():
        co = [hang[n] for n in nuts if n in hang]
        if co:
            ket_qua[khoa] = min(co)
    return ket_qua


def q6(cap_vang, vi_tri):
    """(số cạnh vàng đặt ngược hoặc có đầu không có trong dãy học, tổng cạnh vàng trong phạm vi)."""
    loi = 0
    for nguon, dich in cap_vang:
        if nguon not in vi_tri or dich not in vi_tri or vi_tri[nguon] >= vi_tri[dich]:
            loi += 1
    return loi, len(cap_vang)


def q7(cap_vang_toan_cuon, canh_may_vang, dich):
    """Với mỗi đích có tổ tiên vàng: phần tổ tiên vàng nằm trong tổ tiên máy. Trả (tổng tỉ lệ, số đích, số đích trọn).

    `canh_may_vang`: cạnh máy trong dãy học, đã ánh xạ sang không gian vàng."""
    vang, may = to_tien(cap_vang_toan_cuon), to_tien(canh_may_vang)
    ti_le, tron = [], 0
    for nut in sorted(dich):
        can = vang.get(nut, set())
        if not can:
            continue
        co = may.get(nut, set())
        ti_le.append(len(can & co) / len(can))
        tron += can <= co
    # sum() của Python 3.12 cộng bù sai số; dùng nó để tổng khớp từng bit với bộ chấm cũ (cùng thứ tự, cùng hàm cộng)
    return sum(ti_le), len(ti_le), tron


def q7b(cap_vang_toan_cuon, canh_may_vang, dich):
    """Tổ tiên máy thuộc chương vàng có thật sự cần không. Trả (tổng độ chính xác, số đích có tổ tiên máy)."""
    vang, may = to_tien(cap_vang_toan_cuon), to_tien(canh_may_vang)
    pham_vi, ti_le = set(dich), []
    for nut in sorted(dich):
        co = may.get(nut, set()) & pham_vi
        if co:
            ti_le.append(len(co & vang.get(nut, set())) / len(co))
    return sum(ti_le), len(ti_le)


def cau_truc_do_thi(canh_cung, day_hoc):
    nut = set(day_hoc)
    trong = {(a, b) for a, b in canh_cung if a in nut and b in nut}
    return so_chu_trinh(nut, trong), so_thanh_phan(nut, trong)
