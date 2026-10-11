"""Đo lớp chữ hai backend, mẫu trang cố định; chỉ sách phát triển và D-01 train."""
import json
import sys
import time
from contextlib import closing
from pathlib import Path

import pypdfium2 as pdfium
from docling_parse.pdf_parser import DecodeConfig, DoclingPdfParser

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from doc2roadmap.application.use_cases.ingest_document import _text_quality


def audit_cached():
    from doc2roadmap.infrastructure.artifacts import JsonArtifactStore
    from doc2roadmap.application.use_cases.ingest_document import tree_text_quality
    store = JsonArtifactStore(ROOT / "artifacts")
    ids = ["doc-1", "doc-4", "doc-6", "xstk-ch3-1", "naive-bayes"] + [f"d01-{i:02}" for i in range(1, 17)]
    rows = []
    for doc_id in ids:
        chunks = store.load_latest_chunks(doc_id)
        quality = tree_text_quality(store.load_parse(doc_id, chunks.manifest["parse_version"]).tree)
        rows.append({"doc_id": doc_id, "chunks_version": chunks.version,
                     "parse_version": chunks.manifest["parse_version"], "quality": quality})
        print(doc_id, quality["warnings"], flush=True)
    out = ROOT / "tmp/thu-a1/v413-cached.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    books = [(name, ROOT / filename) for name, filename in (
        ("doc-1", "doc-1.pdf"), ("doc-4", "doc-4.pdf"), ("doc-6", "doc-6.pdf"),
        ("xstk-ch3-1", "xstk-ch3-1.pdf"), ("naive-bayes", "5_Naive Bayes Classifier.pdf"))]
    manifest = json.loads((ROOT / "document-data/manifest.json").read_text(encoding="utf-8"))
    books += [(b["id"], ROOT / "document-data" / b["file"]) for b in manifest["books"] if b["split"] == "train"]
    rows = []
    out = ROOT / "tmp/thu-a1/v413-chu.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    for doc_id, path in books:
        assert path.is_relative_to(ROOT) and "test" not in path.parts
        with pdfium.PdfDocument(path) as pdf:
            pages = sorted({1, min(5, len(pdf)), min(10, len(pdf)), max(1, len(pdf)//4),
                            max(1, len(pdf)//2), max(1, len(pdf)*3//4), len(pdf)})
            began = time.perf_counter()
            texts = []
            for number in pages:
                with closing(pdf[number-1]) as page, closing(page.get_textpage()) as textpage:
                    texts.append(textpage.get_text_range())
            rows.append({"doc_id": doc_id, "backend": "pypdfium2", "pages": pages,
                         "seconds": time.perf_counter()-began, **_text_quality(texts)})
        parser = DoclingPdfParser()
        parsed = parser.load(path, lazy=True, decode_config=DecodeConfig(enforce_same_font=True))
        try:
            began = time.perf_counter()
            texts = ["\n".join(c.text for c in parsed.get_page(number).textline_cells) for number in pages]
            rows.append({"doc_id": doc_id, "backend": "docling-parse", "pages": pages,
                         "seconds": time.perf_counter()-began, **_text_quality(texts)})
        finally:
            parsed.unload()
        out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        print(doc_id, flush=True)


if __name__ == "__main__":
    if "--cached-only" in sys.argv:
        audit_cached()
    else:
        main()
