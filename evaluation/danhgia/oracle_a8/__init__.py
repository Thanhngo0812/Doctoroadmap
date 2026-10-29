"""Oracle A8 (vé DG-14): thay khái niệm máy trích bằng khái niệm vàng của kho chốt G3, để A6-A10 chạy như thường.

Adapter dựng **canonical oracle** (đầu ra của A4/A5) từ kho chốt G3 và chunk của lượt chính. Số oracle báo trong cột riêng, không đặt ngang số hệ
thật: nó đo phần lỗi quan hệ còn lại khi khái niệm đã đúng. Không nhập mã pipeline (chỉ đọc và ghi JSON theo bố cục kho).
"""
from .canonical import GhiDeCanonical, dung_canonical, ghi_canonical, kiem_canonical, tim_chunk
from .anh_xa import MAY_TU_VANG

__all__ = ["GhiDeCanonical", "MAY_TU_VANG", "dung_canonical", "ghi_canonical", "kiem_canonical", "tim_chunk"]
