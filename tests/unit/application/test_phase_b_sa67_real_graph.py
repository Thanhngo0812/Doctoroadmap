"""SA-67: the material of `document-3` on the real xstk-ch3-1 v68 graph (read only, BM25 search, 0 USD).

Skipped when the artifacts are absent. The model is a fake; what is asserted is the message it received."""
import os
import re
from functools import partial
from pathlib import Path

import pytest

from doc2roadmap.application.phase_b.documents import DocumentUseCase
from doc2roadmap.composition_phase_b import PhaseBRuntime
from doc2roadmap.config import Settings
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore

from sa64_support import FakeClock, FakeModel, FakePages

ARTIFACTS = Path(os.environ.get("SA64_REAL_ARTIFACTS", Path(__file__).resolve().parents[3] / "artifacts"))
pytestmark = pytest.mark.skipif(not (ARTIFACTS / "graph" / "xstk-ch3-1").exists(), reason="no real artifacts here")
REQUEST = "Tóm tắt các công thức cần nhớ về tương quan và hồi quy mẫu, kèm giải thích ngắn khi nào dùng."


@pytest.fixture(scope="module")
def made():
    runtime = PhaseBRuntime(settings=Settings(artifact_dir=ARTIFACTS, _env_file=None), mode="offline",
                            store=InMemoryPhaseBStore())
    graph = runtime.graph("xstk-ch3-1", 68)
    module_ids = [list(graph.modules)[index] for index in (3, 4, 5)]
    model, pages = FakeModel(), FakePages({})
    result = DocumentUseCase(model, InMemoryPhaseBStore(), search=partial(runtime.search, graph, free=True),
                             page_images=pages, clock=FakeClock()).create(
        graph.doc_id, graph.graph_version, graph, REQUEST, {"module_ids": module_ids}, owner="alice", allow_spend=True)
    return graph, module_ids, result, model, pages


def passages(prompt):
    body = prompt.split("Tư liệu từ sách:\n", 1)[1]
    parts = re.split(r"^\[S\d+\] \(trang \d+[^\n]*\)\n", body, flags=re.M)
    return parts[1:]


def test_material_has_the_definitions_of_correlation_and_regression_and_the_raw_formula_text(made):
    _, _, result, model, _ = made
    prompt = model.calls[0].prompt
    assert result["status"] == "ready"
    folded = prompt.casefold()
    assert "hệ số tương quan mẫu" in folded and "đường hồi quy" in folded
    assert "0,8165" in prompt


def test_every_concept_of_the_three_modules_is_listed_and_the_material_fits_the_limit(made):
    graph, module_ids, result, model, _ = made
    head = model.calls[0].prompt.split("Tư liệu từ sách:", 1)[0]
    names = [graph.nodes[n].get("display_name") or graph.nodes[n]["name"]
             for module_id in module_ids for n in graph.modules[module_id]["node_ids"]]
    assert all(f"- {name} (module " in head for name in names)
    assert sum(len(text.strip()) for text in passages(model.calls[0].prompt)) <= 20_000
    ids = [row["chunk_id"] for row in result["sources"]]
    orders = [graph.chunks[cid].order_index for cid in ids]
    assert orders == sorted(orders)


def test_every_listed_concept_has_its_definition_passage_in_the_material(made):
    """The first passage of each concept is chosen before any searched or neighbouring passage."""
    from doc2roadmap.application.phase_b.lectures import _assemble
    graph, module_ids, result, _, _ = made
    sent = {row["chunk_id"] for row in result["sources"]}
    missing = []
    for module_id in module_ids:
        for node_id in graph.modules[module_id]["node_ids"]:
            definition = _assemble(graph, node_id, BSettings())[1]["definition"].get("chunk_id")
            if definition and definition not in sent:
                missing.append(node_id)
    assert missing == []


def test_formula_pages_are_asked_from_the_picture_port_at_most_eight_and_only_formula_pages(made):
    graph, _, result, model, pages = made
    asked = [call[2] for call in pages.calls]
    formula_pages = []
    for row in result["sources"]:
        chunk = graph.chunks[row["chunk_id"]]
        if "[formula]" in chunk.text and chunk.page not in formula_pages:
            formula_pages.append(chunk.page)
    assert 0 < len(asked) <= 8
    assert asked == formula_pages[:8]
