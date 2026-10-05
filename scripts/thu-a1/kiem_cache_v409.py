"""Offline v4-09 acceptance: cache metadata audit and optional OCR equivalence."""
import argparse
import json
from pathlib import Path

from doc2roadmap.application.use_cases.ingest_document import _hash
from doc2roadmap.infrastructure.parsing.docling_parser import DoclingParser, PipelineConfig


def audit(root):
    rows = []
    for path in sorted(root.glob("parse_tree/*/v*/manifest.json")):
        manifest = json.loads(path.read_text(encoding="utf-8"))
        previous = manifest["config"]["parser"]
        # Preserve historic adapter versions, backends and stripping rules, not
        # migrate them to today's adapter or today's PDF source hash.
        current = dict(previous)
        delta = PipelineConfig().cache_options()
        if delta:
            current["pipeline"] = delta
        rows.append({"path": str(path), "preserved": _hash(current) == manifest["parser_config_hash"]})
    assert rows and all(row["preserved"] for row in rows), rows
    return {"old_parse_artifacts": len(rows), "preserved": sum(row["preserved"] for row in rows),
            "scope": "root parse_tree; historic configs preserved, not all versions selectable with today's adapter/source",
            "artifacts": rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ocr", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("tmp/thu-a1/v409-cache.json"))
    args = parser.parse_args()
    result = audit(Path("artifacts"))
    if args.ocr:
        import importlib.util
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        from docling.document_converter import DocumentConverter, PdfFormatOption

        spec = importlib.util.spec_from_file_location("a1_bench", Path(__file__).with_name("do_a1.py"))
        bench = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bench)
        comparisons = []
        for name, filename, start, backend in bench.DOCS:
            extra = {}
            if backend == "pypdfium2":
                from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
                extra["backend"] = PyPdfiumDocumentBackend
            old = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(
                pipeline_options=PdfPipelineOptions(images_scale=2.0, generate_picture_images=True), **extra)})
            new = DoclingParser._new_converter(backend)
            left = old.convert(filename, page_range=(start, start + 1)).document
            right = new.convert(filename, page_range=(start, start + 1)).document
            automatic = next(iter(old.initialized_pipelines.values())).ocr_model._engine
            pinned = next(iter(new.initialized_pipelines.values())).ocr_model
            row = {"doc_id": name, "pages": [start, start + 1],
                   "strict_equal": bench.fingerprint(left, None) == bench.fingerprint(right, None),
                   "items_equal": bench.items(left) == bench.items(right),
                   "adapter_equal": bench.adapter_hash(left, backend, filename) == bench.adapter_hash(right, backend, filename)}
            row["engine_options_equal"] = automatic.options == pinned.options
            comparisons.append(row)
            print(json.dumps(row), flush=True)
        result["ocr_comparison"] = comparisons
        assert all(r["strict_equal"] and r["items_equal"] and r["adapter_equal"]
                   and r["engine_options_equal"] for r in comparisons)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "artifacts"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
