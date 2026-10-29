"""Cổng allowlist: hàm trung tâm duy nhất in số ra màn hình cho lệnh chạy với manifest `tap = "thu"` (spec mục 14).

Chỉ in khoá nằm trong danh sách cho phép, với giá trị số, bool hoặc null. Khoá lạ, hay giá trị là chuỗi, dict, danh sách: ném `ValueError`
và không in gì. Thông báo lỗi không bao giờ chứa giá trị hay khoá lạ, vì chính chúng có thể là tên khái niệm hay câu của sách.
"""
from __future__ import annotations

import math


def dong_allowlist(du_lieu, cho_phep):
    """Danh sách dòng `khoá giá_trị`, theo thứ tự của `du_lieu`. Ném `ValueError` trước khi trả bất cứ dòng nào."""
    cho_phep = set(cho_phep)
    dong = []
    for khoa, gia_tri in du_lieu.items():
        if khoa not in cho_phep:
            raise ValueError("có khoá ngoài allowlist: không in")
        if gia_tri is None or isinstance(gia_tri, bool):
            pass
        elif isinstance(gia_tri, int):
            pass
        elif isinstance(gia_tri, float):
            if math.isnan(gia_tri) or math.isinf(gia_tri):
                raise ValueError(f"giá trị của {khoa} không phải số hữu hạn")
        else:
            raise ValueError(f"giá trị của {khoa} thuộc kiểu {type(gia_tri).__name__}: chỉ in số, bool hay null")
        dong.append(f"{khoa} {'null' if gia_tri is None else str(gia_tri).lower() if isinstance(gia_tri, bool) else gia_tri}")
    return dong


def in_allowlist(du_lieu, cho_phep, *, ghi=print):
    """In từng dòng qua `ghi` (mặc định `print`) sau khi mọi khoá và giá trị đã qua cổng."""
    for dong in dong_allowlist(du_lieu, cho_phep):
        ghi(dong)
