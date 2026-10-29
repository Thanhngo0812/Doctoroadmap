"""Chốt chặn giao thức đăng ký trước cho lượt trên tập thử (DG-18a; spec mục 15; `evaluation/giao-thuc/dang-ky-truoc.md`).

Mọi lệnh nhận manifest sách và có thể chi tiền hay sinh hợp đồng để chấm (`luot`, `b5`) gọi `kiem_giao_thuc` **trước bước đầu tiên**:
- `manifest.tap` phải là một trong `bo_sach.TAP`;
- tập thử: bắt buộc `--giao-thuc`, tệp phải đọc được và không còn chữ `CHỜ` hay `NHÁP` (bản chưa chốt); trả SHA-256 của tệp;
- tập phát triển: `--giao-thuc` tuỳ chọn; có thì trả SHA-256 (không đòi bản chốt), không có thì `None`.
Lỗi là `LoiGiaoThuc` (một `ValueError`); thông báo chỉ nêu lý do, không chép nội dung tệp hay manifest.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from danhgia.bo_sach import TAP

DAU_HIEU_CHUA_CHOT = ("CHỜ", "NHÁP")


class LoiGiaoThuc(ValueError):
    pass


def kiem_giao_thuc(manifest, duong):
    """Trả SHA-256 (hex) của tệp giao thức, hoặc `None` (tập phát triển không khai tệp)."""
    tap = manifest.get("tap") if isinstance(manifest, dict) else None
    if tap not in TAP:
        raise LoiGiaoThuc(f"manifest.tap phải thuộc {sorted(TAP)}")
    if duong is None:
        if tap == "thu":
            raise LoiGiaoThuc("tập thử cần --giao-thuc (tệp giao thức đăng ký trước đã chốt)")
        return None
    try:
        noi_dung = Path(duong).read_bytes()
    except OSError as loi:
        raise LoiGiaoThuc(f"không đọc được tệp giao thức ({type(loi).__name__})") from loi
    if tap == "thu":
        van_ban = noi_dung.decode("utf-8", errors="replace")
        con = [d for d in DAU_HIEU_CHUA_CHOT if d in van_ban]
        if con:
            raise LoiGiaoThuc(f"giao thức chưa chốt: còn chữ {', '.join(con)}")
    return hashlib.sha256(noi_dung).hexdigest()
