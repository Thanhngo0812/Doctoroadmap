from __future__ import annotations

import io
from contextlib import closing

import pypdfium2 as pdfium


class PdfiumPageRenderer:
    """Whole-page JPEG pictures and plain text for one-based PDF page numbers."""

    def page_count(self, pdf_path) -> int:
        with pdfium.PdfDocument(pdf_path) as pdf:
            return len(pdf)

    def page_text(self, pdf_path, page_number: int) -> str:
        with pdfium.PdfDocument(pdf_path) as pdf:
            if not 1 <= page_number <= len(pdf):
                return ""
            with closing(pdf[page_number - 1]) as page, closing(page.get_textpage()) as text:
                return text.get_text_range()

    def render_pages(self, pdf_path, pages, *, scale: float, quality: int) -> dict[int, bytes]:
        result: dict[int, bytes] = {}
        with pdfium.PdfDocument(pdf_path) as pdf:
            for number in pages:
                if not 1 <= number <= len(pdf):
                    continue
                with closing(pdf[number - 1]) as page, closing(page.render(scale=scale).to_pil()) as image:
                    buffer = io.BytesIO()
                    image.convert("RGB").save(buffer, format="JPEG", quality=quality)
                    result[number] = buffer.getvalue()
        return result
