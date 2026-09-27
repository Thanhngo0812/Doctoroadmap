import json
from types import SimpleNamespace

from doc2roadmap.application.use_cases.anchor_concepts import AnchorConcepts

TEXTS = {
    "c5": "Đề cương: chương 3 học cơ sở và số chiều.",
    "c40": "Một hệ véc tơ được gọi là một cơ sở của V nếu nó độc lập tuyến tính và sinh ra V.",
    "c14": "Thang điểm chữ A, B, C, D được quy đổi từ điểm số.",
}
ORDER = {"c5": 5, "c14": 14, "c40": 40}


class Model:
    model_id = "fixture-model"

    def __init__(self, bad=False):
        self.calls, self.bad = [], bad

    def start_session(self, system_prompt):
        return self

    def ask_json(self, prompt, *, response_schema):
        data = json.loads(prompt.split("\nCorrect this validation error:")[0])
        self.calls.append(data)
        node_id = data["node_id"]
        if node_id == "cs":
            anchor = next(c for c in data["candidates"] if c["chunk_id"] == "c40")
            value = {"status": "defined_here", "anchor": anchor["cand_id"], "quote": "được gọi là một cơ sở của V",
                     "reason": "định nghĩa"}
        else:
            value = {"status": "not_subject_matter", "quote": "câu bịa" if self.bad else "Thang điểm chữ A, B, C, D",
                     "reason": "chấm điểm"}
        return SimpleNamespace(payload={"node_id": node_id, **value}, usage=None)


def node(node_id, name, chunks):
    return {"node_id": node_id, "name": name, "aliases": [], "description": name, "learnable": True,
            "defining_chunk_ids": list(chunks), "first_order_index": min((ORDER[c] for c in chunks), default=0)}


class Store:
    def __init__(self):
        self.validated = SimpleNamespace(
            payload={"stage": "validated",
                     "nodes": [node("cs", "Cơ sở", ["c5"]), node("tdc", "Thang điểm chữ", ["c14"]),
                               node("rong", "Khái niệm vắng", [])],
                     "mention_map": {"c40": {"cs": {"channels": ["exact"]}}},
                     "requires_edges": [], "cost_summary": {"usd": 0.0}},
            version=9, manifest={"config_hash": "vh", "config": {"edges_version": 8}})
        self.edges = SimpleNamespace(payload={}, version=8, manifest={"config": {"chunks_version": 5}})
        chunks = [SimpleNamespace(chunk_id=k, text=v, order_index=ORDER[k], section_path=["S"]) for k, v in TEXTS.items()]
        self.chunks = SimpleNamespace(result=SimpleNamespace(chunks=chunks), version=5)
        self.checkpoints, self.saved = {}, []

    def load_graph(self, doc_id, version):
        return {9: self.validated, 8: self.edges}[version]

    def load_chunks(self, doc_id, version):
        return self.chunks

    load_role_chunks = load_chunks

    def find_graph(self, doc_id, source_hash, config_hash):
        return next((a for a in self.saved if a.manifest["source_hash"] == source_hash
                     and a.manifest["config_hash"] == config_hash), None)

    def load_checkpoint(self, doc_id, checkpoint_id):
        return self.checkpoints.get(checkpoint_id)

    def save_checkpoint(self, doc_id, checkpoint_id, payload):
        self.checkpoints[checkpoint_id] = json.loads(json.dumps(payload))

    def save_graph(self, doc_id, source_hash, config_hash, config, payload, **kwargs):
        artifact = SimpleNamespace(payload=json.loads(json.dumps(payload)), version=10 + len(self.saved), path=None,
                                   manifest={"source_hash": source_hash, "config_hash": config_hash, "config": config,
                                             "upstream_version": kwargs["upstream_version"]})
        self.saved.append(artifact)
        return artifact


def test_each_concept_is_judged_once_on_sentences_found_beyond_its_defining_chunks():
    store, model = Store(), Model()
    artifact, _ = AnchorConcepts(store, model).execute("doc-1", upstream=store.validated)
    assert artifact.payload["stage"] == "teaching"
    assert sorted(call["node_id"] for call in model.calls) == ["cs", "tdc"]  # khái niệm không có câu nào thì không hỏi
    nodes = {n["node_id"]: n for n in artifact.payload["nodes"]}
    # Đoạn định nghĩa cũ chỉ là đề cương; câu dạy thật được tìm qua mention map, và vị trí dạy chuyển tới đó.
    assert nodes["cs"]["teaching_status"] == "taught" and nodes["cs"]["teaching_order_index"] == 40
    assert nodes["cs"]["defining_chunk_ids"] == ["c5"]  # provenance gốc không bị sửa
    assert nodes["tdc"]["teaching_status"] == "not_subject_matter"
    assert nodes["rong"]["teaching_status"] == "unchecked"


def test_an_answer_that_keeps_failing_validation_keeps_the_concept():
    store = Store()
    artifact, _ = AnchorConcepts(store, Model(bad=True)).execute("doc-1", upstream=store.validated)
    nodes = {n["node_id"]: n for n in artifact.payload["nodes"]}
    assert nodes["tdc"]["teaching_status"] == "uncertain"
