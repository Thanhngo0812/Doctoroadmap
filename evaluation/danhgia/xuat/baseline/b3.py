"""B3 tiêu đề: mỗi tiêu đề A1 của hệ chính, bỏ số mục, là một khái niệm.

- Lấy mọi tiêu đề cấp từ 1 trở lên của `cau_truc.tieu_de`, theo thứ tự của hệ chính (thứ tự sách), không lọc theo vai trò vùng (A2 là một
  bước của luồng 10 bước mà B3 không có);
- bỏ số mục ở đầu: "Chương 2.", "2.1", "2.1.1.", "1)", "II.", "A." và chữ "Chương/Mục/Bài/Phần/Phụ lục" đứng ngay trước số;
  tiêu đề chỉ gồm số thì giữ nguyên;
- câu neo là chính dòng tiêu đề (nguyên văn, kèm số mục) tại trang của nó; không có cạnh.
"""
from __future__ import annotations

import re

from .chung import dung_hop_dong, khai_niem_mau

_SO_MUC = re.compile(
    r"^\s*(?:(?:chương|mục|bài|phần|phụ lục)\s+)?(?:\d+(?:\.\d+)*[.):]?|[IVXLC]+[.):]|[A-Za-z][.):])(?:\s*[-–—]\s*|\s+)",
    re.IGNORECASE)


def bo_so_muc(chu):
    con_lai = _SO_MUC.sub("", chu, count=1).strip()
    return con_lai if con_lai else chu.strip()


def hop_dong_b3(hop_dong_chinh):
    cau_truc = hop_dong_chinh["cau_truc"]
    if cau_truc is None:
        raise ValueError("B3 cần cau_truc của hệ chính (tiêu đề A1); hợp đồng đưa vào không có")
    khai_niem = []
    for tieu_de in cau_truc["tieu_de"]:
        if tieu_de["cap"] is not None and tieu_de["cap"] < 1:
            continue
        khai_niem.append(khai_niem_mau(
            f"b3-{tieu_de['ma']}", bo_so_muc(tieu_de["chu"]), kieu="tieu_de", vi_tri=len(khai_niem),
            cau_neo={"trang": tieu_de["trang"], "cau": tieu_de["chu"], "ma_chunk": ""}))
    return dung_hop_dong(hop_dong_chinh, "b3", khai_niem, tham_so={"loai": "tieu_de_cap_tu_1"})
