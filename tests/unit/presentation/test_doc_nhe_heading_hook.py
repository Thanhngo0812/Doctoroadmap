"""Approved v4-14 research hook: preserve the default parser output."""
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location("doc_nhe_hook", ROOT / "scripts/thu-a1/doc_nhe.py")
DOC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DOC)


@pytest.mark.parametrize("name,digest", [
    ("smoke.pdf", "e265de7214a184c252f78f2419c2d3104daa620ccb9d562d204875647a1e739d"),
    ("smoke-updated.pdf", "4ae64684e3919779b4c0336d34f4e9a29bacdafad89847107a924edd30097872"),
    ("two-column.pdf", "0cebae8d9527c89a42fc21341de2c22610acf6e532eb95f84f809982a84a3391"),
])
def test_baseline_serialized_tree_unchanged(name, digest):
    serialized = json.dumps(DOC.parse(ROOT / "tests/fixtures" / name), ensure_ascii=False, sort_keys=True)
    assert hashlib.sha256(serialized.encode()).hexdigest() == digest


def test_predictor_can_promote_and_demote_heading(monkeypatch):
    def row(text, top, weight):
        return DOC.describe([DOC.Char(ch, 20 + i * 6, top - 12, 26 + i * 6, top,
                                      "Times", weight) for i, ch in enumerate(text)], 1, 800, 600)
    rows = [row("1. Tổng quan", 600, 700), row("Nội dung thân bài thông thường", 540, 400)]
    monkeypatch.setattr(DOC, "extract_rows", lambda path: (rows, [], 1))
    baseline, _ = DOC.parse("unused.pdf")
    assert [n["node_type"] for n in baseline] == ["section_header", "text"]
    changed, _ = DOC.parse("unused.pdf", heading_predictor=lambda selected, body: [False, True])
    assert [n["node_type"] for n in changed] == ["text", "section_header"]
    assert [n["text"] for n in changed] == [n["text"] for n in baseline]
    with pytest.raises(ValueError, match="prediction"):
        DOC.parse("unused.pdf", heading_predictor=lambda selected, body: [True])


def test_describe_exposes_layout_without_changing_text():
    row = DOC.describe([DOC.Char("A", 10, 20, 15, 32, "Times-Italic", 400)], 1, 800, 600)
    assert (row["text"], row["width"], row["italic"], row["font"]) == ("A", 600, 1.0, "Times-Italic")
