import json
from types import SimpleNamespace

import pytest

from doc2roadmap.application.use_cases.check_teaching import CheckTeachingSources

CHUNKS = {
    "de_cuong": ("Đề cương: Chương 5 học dạng toàn phương.", 10, ["ĐỀ CƯƠNG CHI TIẾT HỌC PHẦN"]),
    "c80": ("Định nghĩa. Dạng toàn phương là một đa thức thuần nhất bậc hai.", 80, ["Chương 5", "5.1 Dạng toàn phương"]),
    "danh_gia": ("Thang điểm chữ A, B, C, D được quy đổi từ điểm số.", 14, ["10. Hình thức đánh giá"]),
}

VERDICTS = {
    ("dtp", "de_cuong"): {"verdict": "mentions_only", "reason": "chỉ liệt kê trong đề cương"},
    ("dtp", "c80"): {"verdict": "teaches", "quote": "Dạng toàn phương là một đa thức", "reason": "định nghĩa"},
    ("thang", "danh_gia"): {"verdict": "not_subject_matter", "quote": "Thang điểm chữ A, B, C, D", "reason": "chấm điểm"},
}


class Model:
    model_id = "fixture-model"

    def __init__(self, verdicts=VERDICTS):
        self.verdicts = verdicts
        self.calls = []

    def start_session(self, system_prompt):
        return self

    def ask_json(self, prompt, *, response_schema):
        data = json.loads(prompt.split("\nCorrect this validation error:")[0])
        self.calls.append(data)
        key = (data["node_id"], data["chunk_id"])
        return SimpleNamespace(payload={"node_id": key[0], "chunk_id": key[1], **self.verdicts[key]}, usage=None)


def node(node_id, name, chunks):
    return {"node_id": node_id, "name": name, "description": name, "aliases": [], "learnable": True,
            "defining_chunk_ids": list(chunks), "first_order_index": min(CHUNKS[c][1] for c in chunks)}


class Store:
    def __init__(self, stage="validated"):
        self.validated = SimpleNamespace(
            payload={"stage": stage, "nodes": [node("dtp", "Dạng toàn phương", ["de_cuong", "c80"]),
                                               node("thang", "Thang điểm chữ", ["danh_gia"])],
                     "requires_edges": [], "cost_summary": {"usd": 1.0, "input_tokens": 10, "output_tokens": 5}},
            version=9, manifest={"config_hash": "validated-config", "config": {"edges_version": 8}},
        )
        self.edges = SimpleNamespace(payload={"stage": "edges"}, version=8, manifest={"config": {"chunks_version": 5}})
        chunks = [SimpleNamespace(chunk_id=key, text=text, order_index=order, section_path=path)
                  for key, (text, order, path) in CHUNKS.items()]
        self.chunks = SimpleNamespace(result=SimpleNamespace(chunks=chunks), version=5)
        self.latest = self.validated
        self.checkpoints = {}
        self.saved = []

    def load_latest_graph(self, doc_id):
        return self.latest

    def load_graph(self, doc_id, version):
        return {9: self.validated, 8: self.edges}[version]

    def load_chunks(self, doc_id, version):
        assert version == 5
        return self.chunks

    def find_graph(self, doc_id, source_hash, config_hash):
        return next((artifact for artifact in self.saved if artifact.manifest["source_hash"] == source_hash
                     and artifact.manifest["config_hash"] == config_hash), None)

    def load_checkpoint(self, doc_id, checkpoint_id):
        return self.checkpoints.get(checkpoint_id)

    def save_checkpoint(self, doc_id, checkpoint_id, payload):
        self.checkpoints[checkpoint_id] = json.loads(json.dumps(payload))

    def save_graph(self, doc_id, source_hash, config_hash, config, payload, **kwargs):
        artifact = SimpleNamespace(payload=json.loads(json.dumps(payload)), version=10 + len(self.saved), path=None,
                                   manifest={"source_hash": source_hash, "config_hash": config_hash, "config": config,
                                             "upstream_version": kwargs["upstream_version"]})
        self.saved.append(artifact)
        self.latest = artifact
        return artifact


def test_every_defining_passage_is_judged_and_provenance_is_left_untouched():
    store, model = Store(), Model()
    artifact, reused = CheckTeachingSources(store, model).execute("doc-1")
    assert not reused and artifact.payload["stage"] == "teaching"
    assert artifact.manifest["upstream_version"] == 9
    assert sorted((call["node_id"], call["chunk_id"]) for call in model.calls) == sorted(VERDICTS)
    sent = next(call for call in model.calls if call["chunk_id"] == "de_cuong")
    assert sent["passage"] == {"section_path": ["ĐỀ CƯƠNG CHI TIẾT HỌC PHẦN"], "text": CHUNKS["de_cuong"][0]}
    assert sent["concept"]["name"] == "Dạng toàn phương"

    nodes = {value["node_id"]: value for value in artifact.payload["nodes"]}
    # Vị trí dạy thoát khỏi đề cương; provenance gốc giữ nguyên để concept_hash của vàng đóng băng không đổi.
    assert nodes["dtp"]["teaching_status"] == "taught"
    assert nodes["dtp"]["teaching_chunk_ids"] == ["c80"] and nodes["dtp"]["teaching_order_index"] == 80
    assert nodes["dtp"]["defining_chunk_ids"] == ["de_cuong", "c80"] and nodes["dtp"]["first_order_index"] == 10
    assert nodes["thang"]["teaching_status"] == "not_subject_matter"
    assert {(row["node_id"], row["chunk_id"], row["verdict"]) for row in artifact.payload["teaching_log"]} == {
        (node_id, chunk_id, value["verdict"]) for (node_id, chunk_id), value in VERDICTS.items()}


def test_an_unchanged_input_is_reused_without_calling_the_model_again():
    store, model = Store(), Model()
    first, _ = CheckTeachingSources(store, model).execute("doc-1")
    store.latest = store.validated
    again, reused = CheckTeachingSources(store, Model()).execute("doc-1")
    assert reused and again is first


def test_a_reply_that_keeps_failing_validation_keeps_the_node_as_uncertain():
    # Câu trích bịa ra thì không được dùng để loại node: hết lượt sửa thì coi là chưa đủ căn cứ, và giữ node.
    bad = {**VERDICTS, ("thang", "danh_gia"): {"verdict": "not_subject_matter", "quote": "câu không có", "reason": "x"}}
    artifact, _ = CheckTeachingSources(Store(), Model(bad)).execute("doc-1")
    nodes = {value["node_id"]: value for value in artifact.payload["nodes"]}
    assert nodes["thang"]["teaching_status"] == "uncertain"
    row = next(value for value in artifact.payload["teaching_log"] if value["node_id"] == "thang")
    assert row["verdict"] == "uncertain" and row["reason"] == "invalid_response"


def test_a_run_resumes_from_its_checkpoint_without_asking_finished_nodes_again():
    store, model = Store(), Model()
    CheckTeachingSources(store, model).execute("doc-1")
    checkpoint = next(iter(store.checkpoints.values()))
    finished = {row["node_id"] for row in checkpoint["teaching_log"]}
    assert finished == {"dtp", "thang"}
    # Giả lập lượt chạy bị ngắt sau node đầu tiên: xoá artifact đã lưu, giữ checkpoint chỉ còn node `dtp`.
    store.saved.clear()
    store.latest = store.validated
    checkpoint["completed_nodes"] = ["dtp"]
    checkpoint["teaching_log"] = [row for row in checkpoint["teaching_log"] if row["node_id"] == "dtp"]
    checkpoint["decision_log"] = [row for row in checkpoint["decision_log"] if row["input"]["node_id"] == "dtp"]
    resumed = Model()
    artifact, _ = CheckTeachingSources(store, resumed).execute("doc-1")
    assert {call["node_id"] for call in resumed.calls} == {"thang"}
    assert {value["node_id"]: value["teaching_status"] for value in artifact.payload["nodes"]} == {
        "dtp": "taught", "thang": "not_subject_matter"}


def test_the_check_refuses_anything_but_a_validated_graph():
    with pytest.raises(ValueError, match="validated"):
        CheckTeachingSources(Store(stage="edges"), Model()).execute("doc-1")
