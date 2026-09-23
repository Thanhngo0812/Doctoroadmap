import json
from types import SimpleNamespace

from doc2roadmap.application.use_cases.build_roadmap import BuildRoadmap


class Store:
    def __init__(self, root):
        nodes = [
            {"node_id": "a", "name": "Alpha", "learnable": True, "cluster_id": "g1", "first_order_index": 0, "defining_chunk_ids": ["c1"]},
            {"node_id": "b", "name": "Beta", "learnable": True, "cluster_id": "g1", "first_order_index": 1, "defining_chunk_ids": ["c1"]},
        ]
        edge = {"source": "a", "target": "b", "edge_type": "requires", "chunk_ids": ["c1"], "redundant_via": ["a", "x", "b"]}
        self.validated = SimpleNamespace(
            payload={
                "stage": "validated",
                "nodes": nodes,
                "requires_edges": [edge],
                "quality_gate": {"passed": True},
                "main_sessions": [{"session_id": "main", "target_node_ids": ["a", "b"]}],
                "completed_secondary_pairs": [],
                "suspected_pairs": [],
                "validation_flags": [{"kind": "review_me"}],
                "suspected_pairs": [],
            },
            version=5,
            manifest={"source_hash": "validated-source", "config_hash": "validated-config"},
        )
        self.latest = self.validated
        self.root = root
        self.saved = None

    def load_latest_graph(self, doc_id):
        return self.latest

    def load_graph(self, doc_id, version):
        assert version == 5
        return self.validated

    def find_graph(self, doc_id, source_hash, config_hash):
        if self.saved and self.saved.manifest["source_hash"] == source_hash and self.saved.manifest["config_hash"] == config_hash:
            return self.saved
        return None

    def save_graph(self, doc_id, source_hash, config_hash, config, payload, **kwargs):
        path = self.root / "graph" / doc_id / "v6"
        path.mkdir(parents=True, exist_ok=True)
        self.saved = SimpleNamespace(
            payload=json.loads(json.dumps(payload)), version=6, path=path,
            manifest={"source_hash": source_hash, "config_hash": config_hash, "config": config, "upstream_version": kwargs["upstream_version"]},
        )
        self.latest = self.saved
        return self.saved


def test_roadmap_stage_writes_static_review_page_and_reuses(tmp_path):
    store = Store(tmp_path)
    first, reused = BuildRoadmap(store, stage_cap=5).execute("doc")
    assert not reused and first.payload["stage"] == "stages"
    html = (first.path / "roadmap.html").read_text(encoding="utf-8")
    assert "Alpha" in html and "review_me" in html and "redundant" in html and "c1" in html
    second, reused = BuildRoadmap(store, stage_cap=5).execute("doc")
    assert reused and second is first


def test_roadmap_rejects_unvalidated_edges(tmp_path):
    store = Store(tmp_path)
    store.validated.payload["stage"] = "edges"
    try:
        BuildRoadmap(store, stage_cap=5).execute("doc")
    except ValueError as error:
        assert "validated" in str(error)
    else:
        raise AssertionError("roadmap must not duplicate validation")


def test_invalid_main_session_does_not_mark_its_targets_as_reviewed(tmp_path):
    store = Store(tmp_path)
    store.validated.payload["main_flags"] = [{"kind": "invalid_main_session", "session_id": "main"}]
    artifact, _ = BuildRoadmap(store, stage_cap=5).execute("doc")
    assert {node["node_id"]: node["coverage_status"] for node in artifact.payload["nodes"]} == {
        "a": "unreviewed",
        "b": "unreviewed",
    }


def test_nodes_that_are_not_subject_matter_leave_the_stages_but_their_order_constraints_stay(tmp_path):
    store = Store(tmp_path)

    def taught(node_id, name, status, order):
        return {"node_id": node_id, "name": name, "learnable": True, "cluster_id": "g1", "first_order_index": order,
                "defining_chunk_ids": ["c1"], "teaching_status": status}

    store.validated.payload.update({
        "stage": "teaching",
        "nodes": [taught("a", "Alpha", "taught", 0), taught("x", "Thang điểm chữ", "not_subject_matter", 1),
                  taught("p", "Python", "prior_knowledge", 2), taught("b", "Beta", "mentioned_only", 3)],
        "requires_edges": [
            {"source": "a", "target": "x", "edge_type": "requires", "chunk_ids": ["c1"]},
            {"source": "x", "target": "b", "edge_type": "requires", "chunk_ids": ["c1"]},
        ],
        "main_sessions": [{"session_id": "main", "target_node_ids": ["a", "x", "p", "b"]}],
    })
    artifact, _ = BuildRoadmap(store, stage_cap=5, stage_floor=1).execute("doc")
    stage_of = {node_id: index for index, stage in enumerate(artifact.payload["stages"]) for node_id in stage["node_ids"]}
    # Node "chỉ được nhắc" vẫn giữ; hai trạng thái bị loại ra khỏi stage.
    assert set(stage_of) == {"a", "b"}
    assert stage_of["a"] < stage_of["b"]  # a → x → b: bỏ x không được làm mất ràng buộc a trước b
    assert {row["node_id"]: row["teaching_status"] for row in artifact.payload["excluded_nodes"]} == {
        "x": "not_subject_matter", "p": "prior_knowledge"}
    assert artifact.payload["bypassed_edges"] == [
        {"source": "a", "target": "b", "edge_type": "requires", "via_excluded": ["x"]}]
    html = (artifact.path / "roadmap.html").read_text(encoding="utf-8")
    assert "Kiến thức nền cần có" in html and "Python" in html
    assert "Không đưa vào lộ trình" in html and "Thang điểm chữ" in html
