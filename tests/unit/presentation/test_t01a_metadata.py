"""The blinded checker must not serialize book text hidden inside metadata."""
import importlib.util
import json
from pathlib import Path


def test_checker_does_not_print_nested_book_text(monkeypatch):
    path = Path(__file__).resolve().parents[3] / "scripts/t01/kiem_t01a.py"
    spec = importlib.util.spec_from_file_location("t01a_checker", path)
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    secret = "SYNTHETIC_BOOK_TEXT_MUST_NOT_ESCAPE"
    cost = {"input_tokens": 10, "output_tokens": 2, "usd": 0.01,
            "extra": {"description": secret}}
    manifests = {
        "canonical": {"upstream_version": 1, "gold_sheet_id": checker.A4_GOLD_SHEET,
                      "a4_gold_coverage": "none", "config": {"declared_language": "vi"},
                      "cost_summary": cost},
        "candidates": {"upstream_version": 2, "model_id": checker.MODEL,
                       "llm_transport": "vertex", "cost_summary": cost,
                       "stats": {"section_count": 3, "model_calls": 5,
                                 "input_tokens": {"text": secret},
                                 "candidate_quality": {"names": [secret]},
                                 "rejected_symbol_only_names": [secret]}},
        "chunks": {"config": {"parser": {"adapter": checker.ADAPTER,
                                          "adapter_version": 11, "image_scale": 2.0}},
                   "stats": {"runtime_seconds": 4.5, "warnings": [secret]},
                   "role_counts": {"noi_dung": 3, "unknown_role": secret}},
    }

    def load(file):
        if file.name == "canonical.json":
            return {"stage": "complete", "nodes": [{"name": secret}]}
        return manifests[file.parents[2].name]

    monkeypatch.setattr(checker, "load", load)
    monkeypatch.setattr(checker, "latest", lambda folder: 1)
    info, errors = checker.check(Path("nonexistent-synthetic-artifacts"), "synthetic")
    serialized = json.dumps(info)
    assert not errors
    assert secret not in serialized
    assert info["canonical"]["so_nut"] == 1
    assert info["candidates"]["stats"]["section_count"] == 3
    assert info["chunks"]["stats"]["runtime_seconds"] == 4.5
    assert info["canonical"]["chi"]["usd"] == 0.01
