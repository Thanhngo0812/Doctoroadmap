import json
from types import SimpleNamespace

import pytest

from doc2roadmap.application.phase_b.lectures import _assemble
from doc2roadmap.application.phase_b.retrieval import load_learning_graph
from doc2roadmap.application.use_cases.build_roadmap import BuildRoadmap
from doc2roadmap.domain.models import DocumentNode, DocumentTree
from doc2roadmap.domain.phase_b_limits import BSettings
from tests.legacy_v3 import legacy_store
from doc2roadmap.domain.canonical import digest
from tests.unit.application.test_canonical_gop import DOC
from tests.unit.application.test_gop_graph import real_fixture_gop_roadmap


def pinned_parse_for_chunk_fixture(store, artifact):
    """The A4 fixture has real chunks, but does not package its parse artifact."""
    version = artifact.manifest["config"]["chunks_version"]
    chunks = store.load_chunks(DOC, version)
    parse_version = chunks.manifest["parse_version"]
    tree = DocumentTree([DocumentNode("paragraph", c.text, i, page=c.page)
                         for i, c in enumerate(chunks.result.chunks)])
    path = store.root / "parse_tree" / DOC / f"v{parse_version}"
    store._write(path / "tree.json", tree.to_dict())
    store._write(path / "manifest.json", {"doc_id": DOC, "version": parse_version})


@pytest.fixture(params=["gop", "v3"])
def real_roadmap(tmp_path, request):
    if request.param == "gop":
        store, _, artifact = real_fixture_gop_roadmap(tmp_path, "ml")
        assert "identity_map" not in artifact.payload
    else:
        store, identity, frozen = legacy_store(tmp_path)
        artifact, _ = BuildRoadmap(store).execute(DOC, upstream=identity)
        assert digest(artifact.payload) == frozen['roadmap_payload_hash']
        assert artifact.payload['identity_map']
        assert 'upstream_chain' not in artifact.manifest['config']
    pinned_parse_for_chunk_fixture(store, artifact)
    return store, artifact


def test_phase_b_loader_and_lecture_context_accept_real_roadmap(real_roadmap):
    store, artifact = real_roadmap
    graph = load_learning_graph(store, DOC, artifact.version)
    assert graph.graph_version == artifact.version and graph.modules
    expected = {node["node_id"]: node for node in artifact.payload["nodes"]}
    taught = [node_id for node_id, node in expected.items() if node.get("teaching_status") == "taught" and node.get("anchor")]
    assert taught
    for node_id in taught:
        node = graph.nodes[node_id]
        assert node["anchor"] == expected[node_id]["anchor"]
        assert node["teaching_chunk_ids"] == expected[node_id]["teaching_chunk_ids"]
        context, skeleton, mapping = _assemble(graph, node_id, BSettings())
        assert skeleton["definition"]["quote"] == node["anchor"]["sentence"]
        assert skeleton["definition"]["chunk_id"] == node["anchor"]["chunk_id"]
        assert context["teaching"]
        assert {mapping[row["label"]] for row in context["teaching"]} == set(node["teaching_chunk_ids"])
        source = next(row for row in context["sources"].values() if row["chunk_id"] == node["anchor"]["chunk_id"])
        assert source["citation"] and source["citation"]["chunk_id"] == node["anchor"]["chunk_id"]


def test_composed_module_naming_records_time_outside_semantic_payload(tmp_path, monkeypatch):
    from doc2roadmap.composition import build_learning_graph
    from doc2roadmap.config import Settings

    store, _, artifact = real_fixture_gop_roadmap(tmp_path, "ml")
    settings = Settings(_env_file=None, artifact_dir=tmp_path, secondary_mode="llm")
    embedding = SimpleNamespace(limiter=None)
    monkeypatch.setattr("doc2roadmap.composition._a3_dependencies", lambda: (settings, store, embedding))
    monkeypatch.setattr("doc2roadmap.composition.GeminiEntityExtractor",
                        lambda *args, **kwargs: SimpleNamespace(model_id="fixture-model"))
    graph, _ = build_learning_graph()
    graph.module_titles.deterministic = True
    named, _ = graph.module_titles.execute(DOC, upstream=artifact)
    assert named.manifest["stats"]["runtime_seconds"] >= 0
    # Legacy cluster_stats already carries a duration; naming must add none to the payload.
    assert json.dumps(named.payload).count('"runtime_seconds"') == json.dumps(artifact.payload).count('"runtime_seconds"')
    assert "runtime_seconds" not in json.dumps(named.manifest["config"])
