"""Bảng dòng của PDF dựng bằng đúng bộ đọc nhẹ của pipeline (`doc_nhe.page_lines` rồi `describe`), định dạng hàng như D-02.

Hệ chính đọc PDF bằng chính bộ đọc này, nên mã dòng của vàng G1 khớp thẳng với đầu ra A1. Lưu ý: `scripts/thu-a1/doc_nhe.py` mà D-02 cũ dùng
khác bản trong `src` (`page_lines`, `describe` đã đổi); bảng dòng ở đây theo bản `src`.

Hàng: `id` (`pNNNN-lNNN`), `trang`, `text`, `bbox` = [x0, top, x1, bottom] (toạ độ PDF, gốc dưới-trái), `co_chu`, `dam`.
Seam xuất: được nhập `doc2roadmap`. Gói `g1g2` chỉ nhận bảng dòng đã dựng.
"""
from collections import Counter
from contextlib import closing
from pathlib import Path

from doc2roadmap.infrastructure.parsing.nhe import doc_nhe as nhe


def _chu_cai_trang(trang):
    with closing(trang.get_textpage()) as tp:
        ma = (nhe.raw.FPDFText_GetUnicode(tp.raw, i) for i in range(tp.count_chars()))
        return Counter(c for c in map(chr, ma) if c.isalpha())


def hang_trang(trang, so_trang):
    rong, cao = trang.get_size()
    ket = []
    for chars in nhe.page_lines(trang):
        r = nhe.describe(chars, so_trang, cao, rong)
        if r:
            ket.append({"id": f"p{so_trang:04d}-l{len(ket) + 1:03d}", "trang": so_trang, "text": r["text"],
                        "bbox": [r["x0"], r["top"], r["x1"], r["bottom"]], "co_chu": r["size"], "dam": r["bold"]})
    return ket


def kiem_chu_cai(chu_cai_pdf, dong):
    """Mọi chữ cái Unicode của trang phải xuất hiện đúng một lần trong các hàng của trang đó."""
    theo_trang = {}
    for d in dong:
        theo_trang.setdefault(d["trang"], Counter()).update(c for c in d["text"] if c.isalpha())
    for trang in sorted(set(chu_cai_pdf) | set(theo_trang)):
        if chu_cai_pdf.get(trang, Counter()) != theo_trang.get(trang, Counter()):
            raise ValueError(f"chữ cái trang {trang} bị mất hoặc lặp trong bảng dòng")


def chu_cai_pdf(pdf):
    import pypdfium2

    doc = pypdfium2.PdfDocument(Path(pdf).read_bytes())
    try:
        return {i + 1: _chu_cai_trang(doc[i]) for i in range(len(doc))}
    finally:
        doc.close()


def dong_tu_pdf(pdf):
    import pypdfium2

    doc = pypdfium2.PdfDocument(Path(pdf).read_bytes())
    try:
        dong, chu_cai = [], {}
        for i in range(len(doc)):
            trang = doc[i]
            try:
                dong.extend(hang_trang(trang, i + 1))
                chu_cai[i + 1] = _chu_cai_trang(trang)
            finally:
                trang.close()
    finally:
        doc.close()
    kiem_chu_cai(chu_cai, dong)
    return dong
