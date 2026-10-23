from __future__ import annotations

import hashlib
import json
import unicodedata
from pathlib import Path

from doc2roadmap.application.use_cases.ingest_document import validate_doc_id

SAMPLE_PAGES = 5
SNIPPET_CHARS = 30
MIN_SAMPLE_CHARS = 40
MIN_MATCH_FRACTION = 0.6
TEXT_BLOCKS = {"text", "paragraph", "list_item"}


class PageImageMismatch(ValueError):
    """The PDF is not the file the book was parsed from."""


def formula_pages(tree, chunks) -> list[int]:
    pages = {node.page for node in tree.nodes if node.node_type == "formula" and node.page}
    pages |= {chunk.page for chunk in chunks if chunk.page and "[formula]" in (chunk.text or "")}
    return sorted(pages)


def _letters(text: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFC", text).casefold() if ch.isalnum())


def _expected_pages(tree, chunks) -> int:
    declared = (tree.parse_stats or {}).get("page_count")
    if declared:
        return int(declared)
    return max([node.page for node in tree.nodes if node.page] + [chunk.page for chunk in chunks if chunk.page] + [0])


class CapturePageImages:
    """Write JPEG pictures of the pages that hold formulas, in the layout `ArtifactPageImages` reads."""

    def __init__(self, renderer, *, scale: float = 1.5, quality: int = 80) -> None:
        self.renderer, self.scale, self.quality = renderer, scale, quality

    def verify(self, pdf_path, tree, chunks) -> None:
        expected, actual = _expected_pages(tree, chunks), self.renderer.page_count(pdf_path)
        if expected != actual:
            raise PageImageMismatch(f"PDF có {actual} trang nhưng bản parse có {expected} trang")
        candidates = [c for c in chunks if c.page and set(c.block_types or ()) <= TEXT_BLOCKS
                      and len(_letters(c.text or "")) >= MIN_SAMPLE_CHARS]
        if not candidates:
            raise PageImageMismatch("không có chunk văn bản nào đủ dài để đối chiếu với PDF")
        step = max(1, len(candidates) // SAMPLE_PAGES)
        samples = candidates[::step][:SAMPLE_PAGES]
        hits = sum(_letters(c.text)[:SNIPPET_CHARS] in _letters(self.renderer.page_text(pdf_path, c.page))
                   for c in samples)
        if hits / len(samples) < MIN_MATCH_FRACTION:
            raise PageImageMismatch(f"văn bản PDF chỉ khớp {hits}/{len(samples)} chunk mẫu")

    def execute(self, pdf_path, tree, chunks, *, root, doc_id: str, parse_version: int, verify: bool = False) -> dict:
        validate_doc_id(doc_id)
        if parse_version < 1:
            raise ValueError("parse_version phải lớn hơn 0")
        if verify:
            self.verify(pdf_path, tree, chunks)
        pages = formula_pages(tree, chunks)
        if not pages:
            return {"page_count": 0, "written_count": 0}
        images = self.renderer.render_pages(pdf_path, pages, scale=self.scale, quality=self.quality)
        folder = Path(root) / "phase_b" / "page_images" / doc_id / f"parse-v{parse_version}"
        (folder / "pages").mkdir(parents=True, exist_ok=True)
        rows, written = {}, 0
        for page, data in sorted(images.items()):
            name = f"pages/p{page:03d}.jpg"
            target = folder / name
            digest = hashlib.sha256(data).hexdigest()
            if not (target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == digest):
                target.write_bytes(data)
                written += 1
            rows[str(page)] = {"file": name, "sha256": digest}
        index = {"schema_version": 1, "doc_id": doc_id, "parse_version": parse_version, "scale": self.scale,
                 "format": "jpeg", "pages": rows}
        text = json.dumps(index, ensure_ascii=False, indent=2) + "\n"
        index_path = folder / "index.json"
        if not index_path.exists() or index_path.read_text(encoding="utf-8") != text:
            index_path.write_text(text, encoding="utf-8")
            written += 1
        return {"page_count": len(rows), "written_count": written, "index_path": str(index_path),
                "parse_version": parse_version}
