"""Hợp đồng đánh giá `danh-gia-xuat-1`: lược đồ cộng kiểm tính nhất quán. Không nhập mã pipeline."""
from __future__ import annotations

from collections import Counter

from .luoc_do import LUOC_DO, TEN_LUOC_DO, kiem_theo_luoc_do

__all__ = ["LUOC_DO", "TEN_LUOC_DO", "LoiHopDong", "kiem", "kiem_hoac_loi"]


class LoiHopDong(ValueError):
    """`args[0]` là danh sách mọi lỗi tìm được."""

    def __init__(self, loi):
        super().__init__(loi)
        self.loi = loi

    def __str__(self):
        return "hợp đồng không hợp lệ:\n- " + "\n- ".join(self.loi)


def kiem(hop_dong) -> list[str]:
    """Trả danh sách lỗi (rỗng nếu hợp lệ). Lỗi lược đồ trước; nếu cấu trúc đã sai thì không kiểm nhất quán."""
    loi = kiem_theo_luoc_do(hop_dong, LUOC_DO)
    if loi:
        return loi
    return _nhat_quan(hop_dong)


def kiem_hoac_loi(hop_dong) -> None:
    loi = kiem(hop_dong)
    if loi:
        raise LoiHopDong(loi)


def _nhat_quan(hd) -> list[str]:
    loi = []
    ma = [k["ma"] for k in hd["khai_niem"]]
    lap = sorted(m for m, so in Counter(ma).items() if so > 1)
    if lap:
        loi.append(f"khai_niem: mã trùng {lap}")
    co = set(ma)
    for chi_so, canh in enumerate(hd["canh"]):
        for khoa in ("nguon", "dich"):
            if canh[khoa] not in co:
                loi.append(f"canh[{chi_so}].{khoa}: {canh[khoa]!r} không phải khái niệm trong hợp đồng")
        if canh["mem"] and canh["ly_do_mem"] is None:
            loi.append(f"canh[{chi_so}].ly_do_mem: cạnh mềm phải có lý do")
        if not canh["mem"] and canh["ly_do_mem"] is not None:
            loi.append(f"canh[{chi_so}].ly_do_mem: cạnh cứng không được có lý do làm mềm")
    for nguon, dich in hd["ban_do_danh_tinh"].items():
        for ma_ in (nguon, dich):
            if ma_ not in co:
                loi.append(f"ban_do_danh_tinh: {ma_!r} không phải khái niệm trong hợp đồng")
    lo_trinh = hd["lo_trinh"]
    if lo_trinh is not None:
        day = lo_trinh["day_hoc"]
        lap = sorted(m for m, so in Counter(day).items() if so > 1)
        if lap:
            loi.append(f"lo_trinh.day_hoc: khái niệm lặp {lap}; mỗi khái niệm một vị trí")
        la = sorted(set(day) - co)
        if la:
            loi.append(f"lo_trinh.day_hoc: {la} không phải khái niệm trong hợp đồng")
        for chi_so, module in enumerate(lo_trinh["module"]):
            la = sorted(set(module["thanh_vien"]) - co)
            if la:
                loi.append(f"lo_trinh.module[{chi_so}].thanh_vien: {la} không phải khái niệm trong hợp đồng")
    return loi
