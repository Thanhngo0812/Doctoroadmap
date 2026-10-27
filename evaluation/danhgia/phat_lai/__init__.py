"""Bộ phát lại A9 -> A10 (vé DG-11), thuộc seam xuất: nhập mã pipeline, đọc kho chỉ đọc, không gọi mạng.

Bốn biến thể cho ablation và oracle (spec mục 11): tắt R17, bỏ cạnh pass chính, bỏ cạnh pass phụ, thay cạnh bằng cạnh vàng đã căn.
"""
from .chay import KetQua, LoiPhatLai, kiem_tai_tao, phat_lai
from .oracle import canh_oracle
from .xuat import hop_dong

__all__ = ["KetQua", "LoiPhatLai", "canh_oracle", "hop_dong", "kiem_tai_tao", "phat_lai"]
