import json
from types import SimpleNamespace

from doc2roadmap.application.use_cases.find_implicit import FindImplicitPrerequisites

TEXT = {"c1": "Một ma trận cột là ma trận có một cột.",
        "c2": "Tích Ab là tổ hợp tuyến tính các cột của A với hệ số lấy từ b.",
        "c3": "Thang điểm của môn học."}


class Model:
    model_id = "fixture-model"

    def __init__(self, bad=False):
        self.calls, self.bad = [], bad

    def start_session(self, system_prompt):
        return self

    def ask_json(self, prompt, *, response_schema):
        data = json.loads(prompt.split("\nCorrect this validation error:")[0])
        self.calls.append(data)
        rows = []
        if data["node_id"] == "tich":
            rows = [{"node_id": "cot", "quote": "câu bịa" if self.bad else "các cột của A", "reason": "dùng cột"}]
        return SimpleNamespace(payload={"node_id": data["node_id"], "prerequisites": rows}, usage=None)


def node(node_id, order, chunk, status="taught"):
    return {"node_id": node_id, "name": node_id, "description": node_id, "learnable": True, "teaching_status": status,
            "teaching_order_index": order, "teaching_chunk_ids": [chunk], "defining_chunk_ids": [chunk]}


class Store:
    def __init__(self):
        nodes = [node("cot", 1, "c1"), node("rac", 2, "c3", status="not_subject_matter"), node("tich", 3, "c2")]
        self.upstream = SimpleNamespace(payload={"stage": "teaching", "nodes": nodes, "requires_edges": [],
                                                 "cost_summary": {"usd": 0.0}},
                                        version=21, manifest={"config_hash": "th", "config": {"chunks_version": 5}})
        chunks = [SimpleNamespace(chunk_id=k, text=v, section_path=["S"]) for k, v in TEXT.items()]
        self.chunks = SimpleNamespace(result=SimpleNamespace(chunks=chunks))
        self.checkpoints = {}

    def load_chunks(self, doc_id, version):
        assert version == 5
        return self.chunks

    def find_graph(self, doc_id, source_hash, config_hash):
        return None

    def load_checkpoint(self, doc_id, checkpoint_id):
        return self.checkpoints.get(checkpoint_id)

    def save_checkpoint(self, doc_id, checkpoint_id, payload):
        self.checkpoints[checkpoint_id] = json.loads(json.dumps(payload))

    def save_graph(self, doc_id, source_hash, config_hash, config, payload, **kwargs):
        return SimpleNamespace(payload=json.loads(json.dumps(payload)), version=22, manifest={"config": config})


def test_an_implicit_edge_is_added_from_the_target_passage_and_excluded_concepts_are_never_offered():
    store, model = Store(), Model()
    artifact, _ = FindImplicitPrerequisites(store, model).execute("doc-2", upstream=store.upstream)
    assert [call["node_id"] for call in model.calls] == ["tich"]  # `cot` không có ai dạy trước
    assert [c["node_id"] for c in model.calls[0]["candidates"]] == ["cot"]  # node bị loại không được đưa ra
    assert model.calls[0]["passage"]["text"] == TEXT["c2"]
    [edge] = artifact.payload["requires_edges"]
    assert (edge["source"], edge["target"], edge["evidence_kind"]) == ("cot", "tich", "ngam")
    assert edge["chunk_ids"] == ["c2"] and edge["confidence"] < 0.7
    assert artifact.payload["stage"] == "implicit" and artifact.manifest["config"]["chunks_version"] == 5


def test_a_reply_that_keeps_quoting_outside_the_passage_adds_nothing():
    store = Store()
    artifact, _ = FindImplicitPrerequisites(store, Model(bad=True)).execute("doc-2", upstream=store.upstream)
    assert artifact.payload["requires_edges"] == []
    assert artifact.payload["stats"]["implicit_invalid_targets"] == 1
