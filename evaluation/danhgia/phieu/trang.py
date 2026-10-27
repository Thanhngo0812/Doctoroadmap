"""Văn bản từng trang của PDF, đọc trực tiếp bằng pypdfium2 (không dùng đầu ra pipeline)."""

from collections.abc import Callable
from pathlib import Path


def doc_trang(pdf: str | Path) -> Callable[[int], str]:
    import pypdfium2 as pdfium

    tai_lieu = pdfium.PdfDocument(Path(pdf).read_bytes())  # đọc từ bytes để không giữ khoá tệp trên Windows
    cache: dict[int, str] = {}

    def van_ban(so_trang: int) -> str:
        if so_trang < 1 or so_trang > len(tai_lieu):
            return ""
        if so_trang not in cache:
            trang = tai_lieu[so_trang - 1]
            text = trang.get_textpage()
            cache[so_trang] = text.get_text_range()
            text.close()
            trang.close()
        return cache[so_trang]

    return van_ban
