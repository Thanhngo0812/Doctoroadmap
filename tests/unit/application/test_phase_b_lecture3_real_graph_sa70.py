"""SA-70: raw formula text on the real graphs (read only, 0 USD). Skipped when the artifacts are absent."""
import os
import re
from pathlib import Path

import pytest

from doc2roadmap.application.phase_b.lecture3 import Lecture3UseCase
from doc2roadmap.application.phase_b.retrieval import load_learning_graph
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore

from sa64_support import FakeClock, FakeModel

ARTIFACTS = Path(os.environ.get("SA64_REAL_ARTIFACTS", Path(__file__).resolve().parents[3] / "artifacts"))
BOOKS = {"doc-1": 8, "xstk-ch3-1": 68, "naive-bayes": 49}
pytestmark = pytest.mark.skipif(not all((ARTIFACTS / "graph" / book).exists() for book in BOOKS),
                                reason="no real artifacts here")
_graphs = {}


def graph_of(book):
    if book not in _graphs:
        _graphs[book] = load_learning_graph(JsonArtifactStore(ARTIFACTS), book, BOOKS[book])
    return _graphs[book]


def lecture_prompt(graph, book, node_id):
    model = FakeModel()
    result = Lecture3UseCase(model, InMemoryPhaseBStore(), settings=BSettings(), clock=FakeClock()).make(
        book, BOOKS[book], graph, node_id, allow_spend=True)
    return result, model.calls[0].prompt if model.calls else ""


def passages(prompt, result):
    """chunk_id -> the text the model was shown for it."""
    blocks = re.split(r"^\[S\d+\] \(trang [^\n]*\n", prompt, flags=re.M)[1:]
    return {row["chunk_id"]: block for row, block in zip(result["sources"], blocks)}


@pytest.mark.parametrize("book", BOOKS)
def test_every_formula_passage_the_model_is_shown_has_all_its_marks_replaced(book):
    graph, seen = graph_of(book), 0
    for node_id in sorted(graph.learnable_nodes):
        result, prompt = lecture_prompt(graph, book, node_id)
        for chunk_id, shown in passages(prompt, result).items():
            chunk = graph.chunks[chunk_id]
            if "[formula]" not in chunk.text:
                continue
            seen += 1
            refs = getattr(chunk, "formula_refs", [])
            assert chunk.text.count("[formula]") == len(refs), chunk_id
            assert len(re.findall(r"\[formula: ", shown)) == len(refs), chunk_id
            assert "[formula]" not in shown, chunk_id
        if seen >= 12:
            break
    assert seen >= 12


def test_sample_correlation_coefficient_message_holds_the_book_number():
    graph = graph_of("xstk-ch3-1")
    node_id = next(key for key, node in graph.nodes.items()
                   if (node.get("display_name") or node.get("name")) == "Hệ số tương quan mẫu")
    _, prompt = lecture_prompt(graph, "xstk-ch3-1", node_id)
    assert "0,8165" in prompt


@pytest.mark.parametrize("book", BOOKS)
def test_every_formula_chunk_of_the_book_is_replaced_completely(book):
    from doc2roadmap.application.phase_b.lecture_context3 import formula_raw_texts, formula_text
    graph = graph_of(book)
    raw = formula_raw_texts(graph)
    total = 0
    for chunk in graph.chunks.values():
        if "[formula]" not in chunk.text:
            continue
        refs = getattr(chunk, "formula_refs", [])
        text = formula_text(chunk, raw)
        total += 1
        assert text.count("[formula: ") == len(refs), (chunk.chunk_id, len(refs))
    assert total > 0
