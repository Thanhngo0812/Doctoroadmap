"""Lời nhắc B5: đọc từ tệp đã commit, tạo 5 biến thể định dạng giữ nguyên tập câu chỉ dẫn.

Mã chỉ biết cấu trúc khối của tệp (tiêu đề `##`, khối rào ```), không chứa câu nào của lời nhắc.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

DUONG_MAC_DINH = Path(__file__).resolve().parents[3] / "giao-thuc" / "b5" / "loi-nhac-b5.md"
SO_BIEN_THE = 5
_TIEU_DE_HE_THONG, _TIEU_DE_NGUOI_DUNG, _TIEU_DE_LUOC_DO = "## Lời nhắc hệ thống", "## Lời nhắc người dùng", "## Lược đồ đầu ra"
_DANG_KHAI_NIEM_TRUOC = re.compile(r"`(Các khái niệm đã có[^`]*?:\s)<")
_DAU_DONG = re.compile(r"^- ", re.M)


def _khoi(noi_dung: str, tieu_de: str) -> str:
    sau = noi_dung.split(tieu_de, 1)
    if len(sau) != 2:
        raise ValueError(f"tệp lời nhắc thiếu mục {tieu_de!r}")
    khop = re.search(r"```[a-z]*\n(.*?)\n```", sau[1], re.S)
    if not khop:
        raise ValueError(f"mục {tieu_de!r} không có khối mã")
    return khop.group(1)


def doc_tep(duong=None) -> dict:
    noi_dung = Path(duong or DUONG_MAC_DINH).read_text(encoding="utf-8")
    mo_dau = _DANG_KHAI_NIEM_TRUOC.search(noi_dung)
    if not mo_dau:
        raise ValueError("tệp lời nhắc thiếu dạng `{KHAI_NIEM_TRUOC}` ở chương sau")
    return {"mo_dau_khai_niem_truoc": mo_dau.group(1), "he_thong": _khoi(noi_dung, _TIEU_DE_HE_THONG), "nguoi_dung": _khoi(noi_dung, _TIEU_DE_NGUOI_DUNG),
            "luoc_do": json.loads(_khoi(noi_dung, _TIEU_DE_LUOC_DO))}


def luoc_do(duong=None) -> dict:
    return doc_tep(duong)["luoc_do"]


def chon_bien_the(seed: int) -> int:
    """Biến thể 1..5 theo seed, tất định."""
    return seed % SO_BIEN_THE + 1


def _tieu_de_khoi(khoi: str) -> str:
    return khoi.split(":", 1)[0] if ":" in khoi.split("\n", 1)[0] else ""


def _danh_so(khoi: str) -> str:
    dem = iter(range(1, 1000))
    return _DAU_DONG.sub(lambda _: f"{next(dem)}. ", khoi)


def _viet_hoa_tieu_de(khoi: str) -> str:
    tieu_de = _tieu_de_khoi(khoi)
    return tieu_de.upper() + khoi[len(tieu_de):] if tieu_de else khoi


def he_thong(k: int = 1, duong=None) -> str:
    """Lời nhắc hệ thống, biến thể k (1 = bản gốc của tệp). Các khối cách nhau bằng một dòng trống:
    giới thiệu, `Định nghĩa`, `Đầu ra` (kèm câu cuối)."""
    if not 1 <= k <= SO_BIEN_THE:
        raise ValueError(f"biến thể phải trong 1..{SO_BIEN_THE}")
    goc = doc_tep(duong)["he_thong"]
    khoi = goc.split("\n\n")
    if len(khoi) != 3:
        raise ValueError("lời nhắc hệ thống phải có 3 khối cách nhau bằng dòng trống")
    if k == 2:
        khoi[1], khoi[2] = khoi[2], khoi[1]
    if k == 3:
        khoi = [_danh_so(x) for x in khoi]
    if k == 4:
        khoi = [_viet_hoa_tieu_de(x) for x in khoi]
    return ("\n" if k == 5 else "\n\n").join(khoi)


def nguoi_dung(van_ban: str, khai_niem_truoc=(), duong=None) -> str:
    tep = doc_tep(duong)
    mau = tep["nguoi_dung"]
    truoc = tep["mo_dau_khai_niem_truoc"] + "; ".join(khai_niem_truoc) if khai_niem_truoc else ""
    return mau.replace("{KHAI_NIEM_TRUOC}", truoc).replace("{VAN_BAN}", van_ban)
