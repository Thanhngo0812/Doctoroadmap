import json
from types import SimpleNamespace

from doc2roadmap.application.use_cases.validate_graph import ValidateGraph


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
                "main_edges": [{"source": "a", "target": "b", "edge_type": "requires", "evidence_kind": "noi_ro", "order_relation": "thuận", "confidence": 0.9}],
                "secondary_edges": [],
                "main_flags": [],
                "secondary_flags": [],
                "flags": [],
                "node_vectors_version": 2,
                "decision_log": [{"input": "large"}],
            },
            version=4,
            manifest={"source_hash": "edge-source", "config_hash": "edge-config"},
        )
        self.latest = self.edges
        self.clusters = SimpleNamespace(
            payload={"stage": "clusters", "node_vectors": {"a": [1.0, 0.0], "b": [0.0, 1.0]}},
            version=2,
            manifest={"upstream_version": None},
        )
        self.canonical = SimpleNamespace(payload={"edges": []}, version=1, manifest={})
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

    def find_graph(self, doc_id, source_hash, config_hash):
        if self.saved and self.saved.manifest["source_hash"] == source_hash and self.saved.manifest["config_hash"] == config_hash:
            return self.saved
        return None

    def save_graph(self, doc_id, source_hash, config_hash, config, payload, **kwargs):
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
