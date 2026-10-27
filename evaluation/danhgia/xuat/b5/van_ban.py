"""Văn bản sách cho B5: pypdfium2, mỗi trang mở đầu bằng `[Trang N]` (N là số trang PDF, tính từ 1)."""
from __future__ import annotations

from danhgia.phieu.trang import doc_trang as doc_trang_pdf  # noqa: F401 — đọc trực tiếp bằng pypdfium2, không qua pipeline


def _trang(doc_trang, n: int) -> str:
    return f"[Trang {n}]\n" + doc_trang(n).replace("\r\n", "\n").replace("\r", "\n").strip("\n")


def khoang(doc_trang, dau: int, cuoi: int) -> str:
    return "\n\n".join(_trang(doc_trang, n) for n in range(dau, cuoi + 1))


def cuon(manifest: dict, doc_trang) -> str:
    """B5a: cả cuốn, từ trang 1 đến `so_trang` của manifest."""
    return khoang(doc_trang, 1, manifest["so_trang"])


def chuong(manifest: dict, doc_trang) -> list[dict]:
    """B5b: từng chương của manifest theo thứ tự sách (mọi loại chương)."""
    return [{"ma": c["ma"], "dau": c["trang_dau"], "cuoi": c["trang_cuoi"],
             "text": khoang(doc_trang, c["trang_dau"], c["trang_cuoi"])} for c in manifest["chuong"]]
