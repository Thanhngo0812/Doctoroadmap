"""SA-64: material gathering on the real doc-1 graph (read only, 0 USD). Skipped when the artifacts are absent."""
import os
from pathlib import Path

import pytest

from doc2roadmap.application.phase_b.lecture3 import Lecture3UseCase
from doc2roadmap.application.phase_b.lecture_context3 import formula_pages, gather_chunks
from doc2roadmap.application.phase_b.lectures import _assemble
from doc2roadmap.application.phase_b.retrieval import load_learning_graph
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore

from sa64_support import FakeClock, FakePages

ARTIFACTS = Path(os.environ.get("SA64_REAL_ARTIFACTS", Path(__file__).resolve().parents[3] / "artifacts"))
pytestmark = pytest.mark.skipif(not (ARTIFACTS / "graph" / "doc-1").exists(), reason="no doc-1 artifacts here")


@pytest.fixture(scope="module")
def graph():
    return load_learning_graph(JsonArtifactStore(ARTIFACTS), "doc-1", 8)


def test_loaded_graph_carries_the_parse_version_its_chunks_came_from(graph):
    store = JsonArtifactStore(ARTIFACTS)
    chunks_version = store.load_graph("doc-1", 8).manifest["config"]["chunks_version"]
    expected = store.load_chunks("doc-1", int(chunks_version)).manifest["parse_version"]
    assert graph.parse_version == int(expected)


def concept(graph, name):
    return next(key for key, node in graph.nodes.items() if (node.get("display_name") or node.get("name")) == name)


def material(graph, name):
    node_id = concept(graph, name)
    skeleton = _assemble(graph, node_id, BSettings())[1]
    return node_id, gather_chunks(graph, graph.nodes[node_id], skeleton["definition"].get("chunk_id"), BSettings())


def test_unique_solution_system_material_holds_example_30(graph):
    _, chunks = material(graph, "Hệ phương trình có nghiệm duy nhất")
    assert any("Ví dụ 30" in chunk.text for chunk in chunks)
    assert sum(len(chunk.text.strip()) for chunk in chunks) <= 9000


def test_cauchy_schwarz_material_holds_page_62_and_needs_its_picture(graph):
    node_id, chunks = material(graph, "Bất đẳng thức Cauchy-Schwarz")
    assert any(chunk.page == 62 for chunk in chunks)
    assert 62 in formula_pages(chunks, 4)
    pages = FakePages({page: b"jpeg" for page in range(1, 400)})
    result = Lecture3UseCase(None, InMemoryPhaseBStore(), page_images=pages, settings=BSettings(),
                             clock=FakeClock()).make("doc-1", 8, graph, node_id, dry_run=True)
    assert 62 in result["images"] and len(result["images"]) <= 4
