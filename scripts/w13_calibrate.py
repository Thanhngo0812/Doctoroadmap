"""Measure W-13 input gates on the six development books only (no model calls)."""
import json
import unicodedata
from pathlib import Path

from doc2roadmap.application.use_cases.ingest_document import tree_text_quality
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore
from doc2roadmap.infrastructure.parsing.nhe_parser import NheParser


SOURCES = {
    "doc-1": "doc-1.pdf",
    "xstk-ch3-1": "xstk-ch3-1.pdf",
    "doc-4": "doc-4.pdf",
    "nhap-mon-ml": None,  # Use cached parse only if nhap-mon-ml.pdf has not been restored.
    "naive-bayes": "5_Naive Bayes Classifier.pdf",
    "doc-6": "doc-6.pdf",
}


def measure(tree):
    pages = [""] * int(tree.parse_stats.get("page_count") or 1)
    for node in tree.nodes:
        index = (node.page or 1) - 1
        if 0 <= index < len(pages):
            pages[index] += unicodedata.normalize("NFC", node.text) + "\n"
    letters = [sum(char.isalpha() for char in page) for page in pages]
    text = "".join(pages)
    accents = sum(char.isalpha() and (char in "đĐ" or len(unicodedata.normalize("NFD", char)) > 1)
                  for char in text)
    quality = tree_text_quality(tree)
    return {
        "page_count": len(pages),
        "alphabetic_chars": sum(letters),
        "average_alphabetic_chars_per_page": round(sum(letters) / len(pages), 3),
        "empty_page_ratio": round(sum(count == 0 for count in letters) / len(pages), 6),
        "vi_diacritic_ratio": round(accents / max(sum(letters), 1), 6),
        "text_quality_warning_count": len(quality["warnings"]),
    }


def main():
    parser = NheParser()
    store = JsonArtifactStore(Path("artifacts"))
    cache = Path("tmp/w13-calibration")
    cache.mkdir(parents=True, exist_ok=True)
    rows = []
    sources = dict(SOURCES)
    if Path("nhap-mon-ml.pdf").is_file():
        sources["nhap-mon-ml"] = "nhap-mon-ml.pdf"
    for doc_id, filename in sources.items():
        if filename is None:
            chunks = store.load_latest_chunks(doc_id)
            tree = store.load_parse(doc_id, chunks.manifest["parse_version"]).tree
            basis = "cached_parse_original_pdf_missing"
        else:
            from doc2roadmap.domain.models import DocumentTree
            cached_tree = cache / (doc_id + ".json")
            if cached_tree.exists():
                tree = DocumentTree.from_dict(json.loads(cached_tree.read_text(encoding="utf-8")))
            else:
                tree = parser.parse(Path(filename).read_bytes(), filename).tree
                cached_tree.write_text(json.dumps(tree.to_dict(), ensure_ascii=False), encoding="utf-8")
            basis = "original_pdf_nhe"
        row = {"doc_id": doc_id, "basis": basis, **measure(tree)}
        rows.append(row)
        print(json.dumps(row, ensure_ascii=True), flush=True)
    (cache / "measurements.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
