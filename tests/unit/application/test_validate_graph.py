import json
from types import SimpleNamespace
from unittest.mock import patch

from doc2roadmap.application.use_cases.validate_graph import ValidateGraph
from doc2roadmap.domain.global_validation import validate_graph_rules


class Store:
    def __init__(self):
        nodes = [
            {"node_id": "a", "name": "A", "learnable": True, "cluster_id": "g1"},
            {"node_id": "b", "name": "B", "learnable": True, "cluster_id": "g1"},
        ]
        self.edges = SimpleNamespace(
            payload={
                "stage": "edges",
                "main_complete": True,
                "secondary_complete": True,
                "nodes": nodes,
                "main_edges": [{"source": "a", "target": "b", "edge_type": "requires", "evidence_kind": "noi_ro", "order_relation": "thuận", "confidence": 0.9, "chunk_ids": ["body"]}],
                "secondary_edges": [],
                "main_flags": [],
                "secondary_flags": [],
                "flags": [],
                "node_vectors_version": 2,
                "decision_log": [{"input": "large"}],
            },
            version=4,
            manifest={"source_hash": "edge-source", "config_hash": "edge-config", "config": {"chunks_version": 3}},
        )
        self.latest = self.edges
        self.clusters = SimpleNamespace(
            payload={"stage": "clusters", "node_vectors": {"a": [1.0, 0.0], "b": [0.0, 1.0]}},
            version=2,
            manifest={"upstream_version": None},
        )
        self.canonical = SimpleNamespace(payload={"edges": []}, version=1, manifest={})
        self.role_chunks = SimpleNamespace(version=6, manifest={"config_hash": "role-config"}, result=SimpleNamespace(
            chunks=[SimpleNamespace(chunk_id="body", role="noi_dung"),
                    SimpleNamespace(chunk_id="front", role="mo_dau"),
                    SimpleNamespace(chunk_id="exercise", role="bai_tap")]
        ))
        self.saved = None

    def load_latest_graph(self, doc_id):
        return self.latest

    def load_graph(self, doc_id, version):
        if version == 2:
            return self.clusters
        assert version == 4
        return self.edges

    def load_latest_canonical(self, doc_id):
        return self.canonical

    def load_type_aliases(self):
        return {}

    def load_role_chunks(self, doc_id, version):
        assert version == 3
        return self.role_chunks

    def find_graph(self, doc_id, source_hash, config_hash):
        if self.saved and self.saved.manifest["source_hash"] == source_hash and self.saved.manifest["config_hash"] == config_hash:
            return self.saved
        return None

    def save_graph(self, doc_id, source_hash, config_hash, config, payload, **kwargs):
        self.manifest_fields = kwargs["manifest_fields"]
        self.saved = SimpleNamespace(
            payload=json.loads(json.dumps(payload)), version=5, path=None,
            manifest={"source_hash": source_hash, "config_hash": config_hash, "config": config, "upstream_version": kwargs["upstream_version"]},
        )
        self.latest = self.saved
        return self.saved


def test_validate_stage_is_pure_cached_and_preserves_requires():
    store = Store()
    first, reused = ValidateGraph(store).execute("doc")
    assert not reused and first.payload["stage"] == "validated"
    assert first.payload["requires_edges"][0]["source"] == "a"
    assert "decision_log" not in first.payload and "node_vectors" not in first.payload
    assert first.payload["decision_log_version"] == store.edges.version
    assert first.payload["node_vectors_version"] == store.clusters.version
    assert first.payload["incremental_node_vectors"] == {}
    assert first.payload["quality_gate"] == store.manifest_fields["quality_gate"]
    assert store.manifest_fields["quality_gate"]["nonredundant_requires_edge_count"] == 1
    assert store.manifest_fields["check_name"] == "structural_consistency_check"
    assert first.payload["stats"]["remaining_scc_size_distribution"] == {"1": 2}
    second, reused = ValidateGraph(store).execute("doc")
    assert reused and second is first


def test_validate_rejects_incomplete_edge_artifact():
    store = Store()
    store.edges.payload["secondary_complete"] = False
    try:
        ValidateGraph(store).execute("doc")
    except ValueError as error:
        assert "hoàn tất" in str(error)
    else:
        raise AssertionError("incomplete edges must be rejected")


def test_closed_quality_gate_is_a_visible_review_flag():
    store = Store()
    store.edges.payload["main_edges"] = []
    artifact, _ = ValidateGraph(store).execute("doc")
    assert not artifact.payload["quality_gate"]["passed"]
    assert any(
        flag["kind"] == "structural_consistency_gate_closed" and flag["reason"]
        for flag in artifact.payload["validation_flags"]
    )


def test_legacy_empty_secondary_flags_are_diagnosed_not_sent_to_review():
    store = Store()
    store.edges.payload["secondary_flags"] = [{}, {"kind": ""}]
    artifact, _ = ValidateGraph(store).execute("doc")
    assert artifact.payload["stats"]["invalid_upstream_flag_count"] == 2
    assert all(flag.get("kind") for flag in artifact.payload["validation_flags"])
    assert any(flag["kind"] == "invalid_upstream_flags" for flag in artifact.payload["validation_flags"])


def test_new_node_cluster_assignment_happens_after_structural_check():
    store = Store()
    store.edges.payload["flags"] = [
        {
            "kind": "resolved_new_node",
            "resolved_node": {"node_id": "c", "name": "C", "learnable": True},
            "semantic_vector": [1.0, 0.0],
        },
        {
            "kind": "resolved_new_node",
            "resolved_node": {"node_id": "d", "name": "D", "learnable": True},
            "semantic_vector": [0.0, 1.0],
        },
    ]
    with patch("doc2roadmap.application.use_cases.validate_graph.validate_graph_rules", wraps=validate_graph_rules) as check:
        artifact, _ = ValidateGraph(store).execute("doc")
    checked = next(node for node in check.call_args.args[0] if node["node_id"] == "c")
    assigned = next(node for node in artifact.payload["nodes"] if node["node_id"] == "c")
    assert "cluster_id" not in checked
    assert assigned["cluster_id"] == "g1"
    assert next(node for node in artifact.payload["nodes"] if node["node_id"] == "d")["cluster_id"] == "g1"


def test_validate_uses_pinned_role_overlay_and_records_excluded_edge():
    store = Store()
    store.edges.payload["main_edges"] = [
        {"source": "a", "target": "b", "edge_type": "requires", "chunk_ids": ["front"]},
    ]
    artifact, _ = ValidateGraph(store).execute("doc")
    assert artifact.payload["requires_edges"] == []
    assert any(flag["kind"] == "requires_non_teaching_evidence" for flag in artifact.payload["validation_flags"])
    assert artifact.manifest["config"]["role_chunks_version"] == 6
    assert artifact.payload["stats"]["excluded_region_edge_count"] == 1
