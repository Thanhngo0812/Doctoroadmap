"""Chuẩn hoá tên và câu, khớp theo ranh giới âm tiết tiếng Việt.

Cùng một phép biến đổi cho tên và câu: NFKC, chữ thường, gộp khoảng trắng, bỏ dấu câu ở hai đầu, giữ dấu tiếng Việt. NFKC (không phải NFC)
đưa chỉ số trên/dưới, chữ ghép và ký tự tương thích về dạng thường, nên "χ²" trùng "χ2" (gán thử xstk 27/10).
Âm tiết là chuỗi chữ-số liền nhau; khoảng trắng, dấu câu và dấu gạch dưới (chỗ nối từ ghép) là ranh giới. Mỗi âm tiết
được so nguyên vẹn, nên "quy" không bị đổi thành "qui" và không phụ thuộc vị trí trong câu (bài học chữ "y", vòng 2).
"""

import difflib
import re
import unicodedata

_DAU_HAI_DAU = " \t\r\n.,;:!?…\"'«»“”‘’-–—"
_AM_TIET = re.compile(r"[^\W_]+")


def chuan_hoa(s: str | None) -> str:
    s = unicodedata.normalize("NFKC", s or "").lower()
    return re.sub(r"\s+", " ", s).strip(_DAU_HAI_DAU)


def am_tiet(s: str | None) -> tuple[str, ...]:
    return tuple(_AM_TIET.findall(chuan_hoa(s)))


def xuat_hien(ten: str, cau: str) -> bool:
    """Tên xuất hiện liền kề, đúng ranh giới âm tiết, trong câu."""
    t, c = am_tiet(ten), am_tiet(cau)
    n = len(t)
    return n > 0 and any(c[i : i + n] == t for i in range(len(c) - n + 1))


def do_giong(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, " ".join(am_tiet(a)), " ".join(am_tiet(b)), autojunk=False).ratio()
