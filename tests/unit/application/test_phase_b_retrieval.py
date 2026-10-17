from types import SimpleNamespace
import json

import pytest

from doc2roadmap.application.phase_b.retrieval import (
    assert_retrieval_compatible,
    build_module_assignments,
    load_learning_graph,
)
from doc2roadmap.domain.retrieval import RetrievalDocument, SearchHit, prefer_module_hits


def chunk(chunk_id, order, text=None, section_path=None, role="noi_dung"):
    return SimpleNamespace(chunk_id=chunk_id, order_index=order, text=text or chunk_id,
                           section_path=section_path or ["Chương 1"],
                           parent_section_id="s1", role=role)


def test_a12_assigns_nearest_preceding_teaching_module_without_changing_chunks():
    chunks = [chunk("c0", 0), chunk("c1", 1), chunk("c2", 2), chunk("c3", 3)]
    before = [(row.chunk_id, row.text) for row in chunks]
    graph = {
        "graph_version": 7,
        "modules": [{"module_id": "m1", "index": 0}, {"module_id": "m2", "index": 1}],
        "chunk_module_map": {
            "c1": {"module_id": "m1", "all_module_ids": ["m1"]},
            "c3": {"module_id": "m2", "all_module_ids": ["m2"]},
        },
    }

    overlay = build_module_assignments(graph, chunks)

    assert overlay["assignments"] == {
        "c0": {"module_id": None, "all_module_ids": [], "module_source": "none"},
        "c1": {"module_id": "m1", "all_module_ids": ["m1"], "module_source": "chunk_module_map"},
        "c2": {"module_id": "m1", "all_module_ids": ["m1"], "module_source": "hint"},
        "c3": {"module_id": "m2", "all_module_ids": ["m2"], "module_source": "chunk_module_map"},
    }
    assert overlay["counts"] == {"chunk_module_map": 2, "hint": 1, "none": 1}
    assert [(row.chunk_id, row.text) for row in chunks] == before


def test_index_compatibility_ignores_artifact_version_but_checks_actual_inputs():
    chunks = [chunk("c1", 0, "alpha", ["Chương 1"]), chunk("c2", 1, "beta", ["Chương 2"])]
    payload = {"documents": [
        {"chunk_id": "c1", "text": "alpha", "section_path": ["Chương 1"]},
        {"chunk_id": "c2", "text": "beta", "section_path": ["Chương 2"]},
    ]}

    fingerprint = assert_retrieval_compatible(payload, chunks)

    assert fingerprint
    with pytest.raises(ValueError, match="văn bản"):
        assert_retrieval_compatible({"documents": [{**payload["documents"][0], "text": "changed"},
                                                    payload["documents"][1]]}, chunks)
    with pytest.raises(ValueError, match="đường mục"):
        assert_retrieval_compatible({"documents": [payload["documents"][0],
                                                    {**payload["documents"][1], "section_path": ["Changed"]}]}, chunks)


def test_module_promotion_never_filters_later_or_unassigned_chunks():
    hits = [SearchHit(RetrievalDocument(f"c{i}", f"text{i}", (1.0,), order_index=i), 1.0)
            for i in range(20)]
    assignments = {
        f"c{i}": {"module_id": "before" if i == 12 else "after" if i == 1 else None,
                   "all_module_ids": ["before"] if i == 12 else ["after"] if i == 1 else [],
                   "module_source": "hint" if i == 12 else "none"}
        for i in range(20)
    }

    result = prefer_module_hits(hits, assignments, {"before": 1, "current": 2, "after": 3},
                                "current", top_k=6)

    ids = [hit.chunk_id for hit in result]
    assert "c12" in ids
    assert "c1" in ids
    assert len(ids) == 6


def test_graph_loader_skips_latest_intermediate_and_selects_complete_a10():
    class Artifact:
        def __init__(self, version, algorithm, modules, chunks_version=1):
            self.version = version
            self.manifest = {"stage": "stages" if modules else "edges",
                             "config": {"algorithm_id": algorithm, "chunks_version": chunks_version}}
            self.payload = {"modules": modules, "nodes": [], "main_complete": True}

    class Store:
        rows = {
            2: Artifact(2, "a10-module-titles-v9", [{"module_id": "m1", "index": 0}]),
            3: Artifact(3, "a8-main-pass-v5", []),
        }

        def load_latest_graph(self, _doc_id):
            return self.rows[3]

        def load_graph(self, _doc_id, version):
            if version not in self.rows:
                raise FileNotFoundError(version)
            return self.rows[version]

        def load_chunks(self, _doc_id, _version):
            return type("Chunks", (), {"result": type("Result", (), {"chunks": []})(),
                                      "manifest": {}})()

        def load_latest_chunks(self, _doc_id):
            raise AssertionError("pinned chunks version should be loaded")

    graph = load_learning_graph(Store(), "book")

    assert graph.graph_version == 2
    assert list(graph.modules) == ["m1"]


def test_graph_loader_rejects_explicit_non_a10_version():
    class Artifact:
        version = 7
        manifest = {"stage": "edges", "config": {"algorithm_id": "a8-main-pass-v5", "chunks_version": 1}}
        payload = {"modules": [], "main_complete": True}

    class Store:
        def load_graph(self, _doc_id, _version):
            return Artifact()

    with pytest.raises(ValueError, match="không phải lộ trình A10"):
        load_learning_graph(Store(), "book", graph_version=7)


def test_graph_loader_exposes_formula_images_by_occurrence(tmp_path):
    class Artifact:
        version = 2
        manifest = {"stage": "stages", "config": {"chunks_version": 1}}
        payload = {"modules": [{"module_id": "m1", "index": 0}], "nodes": []}

    class Store:
        root = tmp_path

        def load_graph(self, _doc_id, _version):
            return Artifact()

        def load_chunks(self, _doc_id, _version):
            return type("Chunks", (), {"result": type("Result", (), {"chunks": []})(),
                                      "manifest": {"parse_version": 4}})()

        def load_parse(self, _doc_id, _version):
            return type("Parse", (), {"tree": None})()

    index_path = tmp_path / "phase_b" / "formula_images" / "book" / "parse-v4" / "index.json"
    index_path.parent.mkdir(parents=True)
    index_path.write_text(json.dumps({
        "doc_id": "book", "parse_version": 4,
        "formula_refs": [{"occurrence_id": "f1@p2:r3", "formula_id": "f1",
                          "image_ref": "images/hash.png", "status": "cut"}],
    }), encoding="utf-8")

    graph = load_learning_graph(Store(), "book", graph_version=2)

    assert graph.formula_images["f1@p2:r3"]["image_ref"] == "images/hash.png"
