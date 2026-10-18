from __future__ import annotations

from contextlib import closing
import io
import math
from collections import defaultdict

import pypdfium2 as pdfium


class PdfiumFormulaRenderer:
    """Crop parser `l,t,r,b` point boxes from one-based PDF pages."""

    def render_formula(self, pdf_path, page_number: int, bbox, *, scale: float = 2.0,
                       origin: str | None = None) -> bytes | None:
        return self.render_formula_batch(pdf_path, [(page_number, bbox, origin)], scale=scale)[0]

    def render_formula_batch(self, pdf_path, formulas, *, scale: float = 2.0) -> list[bytes | None]:
        """Render many crops while opening each source page only once."""
        result: list[bytes | None] = [None] * len(formulas)
        by_page = defaultdict(list)
        for index, (page_number, bbox, origin) in enumerate(formulas):
            if page_number >= 1 and bbox is not None and len(bbox) == 4:
                by_page[page_number].append((index, bbox, origin))
        if scale <= 0 or not by_page:
            return result
        with pdfium.PdfDocument(pdf_path) as pdf:
            for page_number, entries in by_page.items():
                if page_number > len(pdf):
                    continue
                with closing(pdf[page_number - 1]) as page:
                    width, height = page.get_size()
                    with closing(page.render(scale=scale).to_pil()) as image:
                        for index, bbox, origin in entries:
                            result[index] = self._crop(image, width, height, bbox, origin, scale)
        return result

    @staticmethod
    def _crop(image, width, height, bbox, origin, scale):
        if scale <= 0 or len(bbox) != 4:
            return None
        left, top, right, bottom = map(float, bbox)
        if not all(math.isfinite(value) for value in (left, top, right, bottom)):
            return None
        x0, x1 = sorted((left, right))
        if x1 <= x0 or top == bottom:
            return None
        # Docling preserves coord_origin; native parser uses lower-left PDF points.
        # Old trees lack the field, so infer from their conventional t/b ordering.
        origin = (origin or ("topleft" if top < bottom else "bottomleft")).casefold()
        if origin in {"topleft", "top_left", "coordorigin.topleft"}:
            y0, y1 = sorted((top, bottom))
        elif origin in {"bottomleft", "bottom_left", "coordorigin.bottomleft"}:
            y_top, y_bottom = sorted((top, bottom), reverse=True)
            y0, y1 = height - y_top, height - y_bottom
        else:
            return None
        px0 = max(0, min(round(x0 * scale), round(width * scale)))
        px1 = max(0, min(round(x1 * scale), round(width * scale)))
        py0 = max(0, min(round(y0 * scale), round(height * scale)))
        py1 = max(0, min(round(y1 * scale), round(height * scale)))
        if px1 <= px0 or py1 <= py0:
            return None
        crop = image.crop((px0, py0, px1, py1))
        buffer = io.BytesIO()
        crop.save(buffer, format="PNG")
        crop.close()
        return buffer.getvalue()
