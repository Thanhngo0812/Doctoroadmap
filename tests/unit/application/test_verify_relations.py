import json
from types import SimpleNamespace

import pytest

from doc2roadmap.application.use_cases.verify_relations import VerifyRelations

CHUNKS = {
    "c_kgvt": ("Cho K là một trường. V cùng phép cộng và phép nhân với vô hướng là không gian véc tơ.", 50, ["4.1"]),
    "c_vd": ("Ví dụ 4. Tập C[a, b] các hàm thực liên tục là một không gian véc tơ.", 55, ["4.1", "Ví dụ"]),
    "c_vh": ("Phần tử của trường K gọi là vô hướng.", 30, ["1.3"]),
    "c_mt": ("Ma trận là bảng số. Cộng hai ma trận cùng cỡ theo từng phần tử.", 20, ["2.1"]),
}

ANSWERS = {
    "vh->kgvt": {"verdict": "requires", "quote": "phép nhân với vô hướng", "reason": "định nghĩa dùng vô hướng"},
    "cong->kgvt": {"verdict": "supports", "quote": "Tập C[a, b] các hàm thực liên tục là một không gian véc tơ.",
                   "reason": "một ví dụ, không phải thành phần của định nghĩa"},
}


class Model:
    model_id = "fixture-model"

    def __init__(self, answers=ANSWERS):
        self.answers = answers
        self.calls = []

    def start_session(self, system_prompt):
        return self

    def ask_json(self, prompt, *, response_schema):
        data = json.loads(prompt.split("\nCorrect this validation error:")[0])
        self.calls.append(data)
        return SimpleNamespace(payload={"edge_id": data["edge_id"], **self.answers[data["edge_id"]]}, usage=None)


def node(node_id, name, defining, teaching=None):
    value = {"node_id": node_id, "name": name, "description": name, "aliases": [], "learnable": True,
             "defining_chunk_ids": list(defining)}
    if teaching is not None:
        value.update({"teaching_status": "taught", "teaching_chunk_ids": list(teaching)})
    return value


def requires(source, target, chunks):
    return {"source": source, "target": target, "edge_type": "requires", "chunk_ids": list(chunks)}


class Store:
    def __init__(self, stage="teaching"):
        self.upstream = SimpleNamespace(
            payload={"stage": stage,
                     "nodes": [node("vh", "Vô hướng", ["c_vh"], teaching=["c_vh"]),
                               # Đoạn định nghĩa gồm cả ví dụ; đoạn dạy chỉ còn định nghĩa thật.
                               node("kgvt", "Không gian véc tơ", ["c_kgvt", "c_vd"], teaching=["c_kgvt"]),
                               node("cong", "Cộng ma trận", ["c_mt"])],
                     "requires_edges": [requires("vh", "kgvt", ["c_kgvt"]), requires("cong", "kgvt", ["c_vd"])],
                     "cost_summary": {"usd": 1.0, "input_tokens": 10, "output_tokens": 5}},
            version=11, manifest={"config_hash": "teaching-config", "config": {"chunks_version": 5},
                                  "upstream_version": 9},
        )
        chunks = [SimpleNamespace(chunk_id=key, text=text, order_index=order, section_path=path)
                  for key, (text, order, path) in CHUNKS.items()]
        self.chunks = SimpleNamespace(result=SimpleNamespace(chunks=chunks), version=5)
        self.latest = self.upstream
        self.checkpoints = {}
        self.saved = []

    def load_latest_graph(self, doc_id):
        return self.latest

    def load_graph(self, doc_id, version):
        assert version == 11
        return self.upstream

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
        artifact = SimpleNamespace(payload=json.loads(json.dumps(payload)), version=12 + len(self.saved), path=None,
                                   manifest={"source_hash": source_hash, "config_hash": config_hash, "config": config,
                                             "upstream_version": kwargs["upstream_version"]})
        self.saved.append(artifact)
        self.latest = artifact
        return artifact


def test_an_example_stops_being_a_hard_prerequisite_while_a_definitional_use_stays():
    store, model = Store(), Model()
    artifact, reused = VerifyRelations(store, model).execute("doc-1")
    assert not reused and artifact.payload["stage"] == "verified" and artifact.manifest["upstream_version"] == 11
    assert [(edge["source"], edge["target"]) for edge in artifact.payload["requires_edges"]] == [("vh", "kgvt")]
    assert [(edge["source"], edge["relation_check"]) for edge in artifact.payload["recommended_edges"]] == [
        ("cong", "supports")]
    assert artifact.payload["rejected_edges"] == []


def test_the_dossier_carries_the_teaching_passages_of_both_ends_and_the_edge_evidence():
    store, model = Store(), Model()
    VerifyRelations(store, model).execute("doc-1")
    sent = next(call for call in model.calls if call["edge_id"] == "cong->kgvt")
    # Đoạn dạy của đích bỏ ví dụ; bằng chứng của cạnh vẫn được đưa riêng để mô hình thấy vì sao cạnh được đề xuất.
    assert [passage["chunk_id"] for passage in sent["target"]["passages"]] == ["c_kgvt"]
    assert [passage["chunk_id"] for passage in sent["prerequisite"]["passages"]] == ["c_mt"]  # chưa có đoạn dạy: dùng định nghĩa
    assert [passage["chunk_id"] for passage in sent["evidence"]] == ["c_vd"]
    assert sent["prerequisite"]["name"] == "Cộng ma trận" and sent["target"]["name"] == "Không gian véc tơ"


def test_an_answer_that_keeps_failing_validation_leaves_the_edge_as_a_hard_constraint():
    bad = {**ANSWERS, "cong->kgvt": {"verdict": "supports", "quote": "câu bịa", "reason": "x"}}
    artifact, _ = VerifyRelations(Store(), Model(bad)).execute("doc-1")
    kept = {(edge["source"], edge["relation_check"]) for edge in artifact.payload["requires_edges"]}
    assert kept == {("vh", "requires"), ("cong", "unresolved")}


def test_an_unchanged_input_is_reused_and_anything_but_a_teaching_or_validated_graph_is_refused():
    store = Store()
    first, _ = VerifyRelations(store, Model()).execute("doc-1")
    store.latest = store.upstream
    again, reused = VerifyRelations(store, Model()).execute("doc-1")
    assert reused and again is first
    with pytest.raises(ValueError, match="teaching"):
        VerifyRelations(Store(stage="edges"), Model()).execute("doc-1")
