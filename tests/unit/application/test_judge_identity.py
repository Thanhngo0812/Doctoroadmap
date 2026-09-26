import json
from types import SimpleNamespace

from doc2roadmap.application.use_cases.judge_identity import JudgeIdentity


class Model:
    model_id = "fixture-model"

    def __init__(self, verdicts):
        self.verdicts, self.calls = verdicts, []

    def start_session(self, system_prompt):
        return self

    def ask_json(self, prompt, *, response_schema):
        data = json.loads(prompt.split("\nCorrect this validation error:")[0])
        self.calls.append(data)
        names = frozenset((data["first"]["name"], data["second"]["name"]))
        return SimpleNamespace(payload={"pair_id": data["pair_id"], "verdict": self.verdicts.get(names, "different"),
                                        "reason": "vì hai câu neo"}, usage=None)


def node(node_id, name, order, anchor=None, status="taught"):
    return {"node_id": node_id, "name": name, "aliases": [], "description": name, "learnable": True,
            "teaching_status": status, "teaching_order_index": order, "anchor": anchor}


SAME = {"chunk_id": "c1", "char_start": 0, "sentence": "Tiên nghiệm, hợp lý và hậu nghiệm được định nghĩa như sau."}


class Store:
    def __init__(self):
        nodes = [node("dltt", "Độc lập tuyến tính", 3), node("hv", "Hệ véc tơ độc lập tuyến tính", 5),
                 node("tn", "Tiên nghiệm", 7, SAME), node("hn", "Hậu nghiệm", 7, SAME),
                 node("rac", "Độc lập tuyến tính", 1, status="not_subject_matter"),  # bị loại: không đưa ra xét
                 node("x", "Phụ thuộc tuyến tính", 9)]
        edges = [{"source": "x", "target": "hv", "edge_type": "requires"},
                 {"source": "dltt", "target": "x", "edge_type": "requires"},
                 {"source": "tn", "target": "hn", "edge_type": "requires"}]
        self.teaching = SimpleNamespace(payload={"stage": "teaching", "nodes": nodes, "requires_edges": edges,
                                                 "cost_summary": {"usd": 0.0}},
                                        version=21, manifest={"config_hash": "th", "config": {"chunks_version": 5}})
        self.checkpoints, self.saved = {}, []

    def find_graph(self, doc_id, source_hash, config_hash):
        return None

    def load_checkpoint(self, doc_id, checkpoint_id):
        return self.checkpoints.get(checkpoint_id)

    def save_checkpoint(self, doc_id, checkpoint_id, payload):
        self.checkpoints[checkpoint_id] = json.loads(json.dumps(payload))

    def save_graph(self, doc_id, source_hash, config_hash, config, payload, **kwargs):
        artifact = SimpleNamespace(payload=json.loads(json.dumps(payload)), version=22, manifest={"config": config})
        self.saved.append(artifact)
        return artifact


def test_only_judged_same_pairs_merge_into_the_earlier_taught_concept_and_the_result_is_a_dag():
    store = Store()
    model = Model({frozenset(("Độc lập tuyến tính", "Hệ véc tơ độc lập tuyến tính")): "same"})
    artifact, _ = JudgeIdentity(store, model).execute("doc-1", upstream=store.teaching)
    payload = artifact.payload
    assert payload["stage"] == "identity"
    assert artifact.manifest["config"]["chunks_version"] == 5  # A10 cần để tìm chunk
    # hai cặp ứng viên: tiền tố chung chung, và cùng câu neo; node bị loại không vào cặp nào
    assert sorted(frozenset((c["first"]["name"], c["second"]["name"])) for c in model.calls) == sorted([
        frozenset(("Độc lập tuyến tính", "Hệ véc tơ độc lập tuyến tính")), frozenset(("Tiên nghiệm", "Hậu nghiệm"))])
    assert payload["identity_map"] == {"hv": "dltt"}
    assert [n["node_id"] for n in payload["merged_nodes"]] == ["hv"] and payload["merged_nodes"][0]["merged_into"] == "dltt"
    assert "hv" not in {n["node_id"] for n in payload["nodes"]}
    # x → hv thành x → dltt, cùng dltt → x là chu trình; gỡ đúng một cạnh
    pairs = {(e["source"], e["target"]) for e in payload["requires_edges"]}
    assert len(payload["identity_removed_edges"]) == 1 and not {("x", "dltt"), ("dltt", "x")} <= pairs
    assert ("tn", "hn") in pairs  # cùng câu neo nhưng phán "different" thì không gộp
    assert payload["stats"]["identity_open_count"] == 0


def test_a_human_review_overrides_the_model_and_only_an_approved_merge_is_applied():
    # Mô hình phán `same` cho cả hai cặp; người duyệt để "Không chắc" ở cặp dltt/hv → không gộp cặp đó.
    store = Store()
    model = Model({frozenset(("Độc lập tuyến tính", "Hệ véc tơ độc lập tuyến tính")): "same",
                   frozenset(("Tiên nghiệm", "Hậu nghiệm")): "same"})
    review = {frozenset(("dltt", "hv")): "Không chắc", frozenset(("tn", "hn")): "Đồng ý gộp"}
    artifact, _ = JudgeIdentity(store, model, review=review).execute("doc-1", upstream=store.teaching)
    payload = artifact.payload
    assert payload["identity_map"] == {"tn": "hn"}  # cùng vị trí dạy → hoà phá theo node_id
    rows = {frozenset((r["left"], r["right"])): r for r in payload["identity_log"]}
    assert rows[frozenset(("dltt", "hv"))]["model_verdict"] == "same"
    assert rows[frozenset(("dltt", "hv"))]["verdict"] == "different"
    assert rows[frozenset(("dltt", "hv"))]["human_decision"] == "Không chắc"
    assert "review_hash" in artifact.manifest["config"]


def test_a_review_file_is_loaded_for_one_document_and_unknown_decisions_are_refused(tmp_path):
    import pytest

    from doc2roadmap.application.use_cases.judge_identity import load_identity_review

    path = tmp_path / "duyet.json"
    path.write_text(json.dumps({"doc_id": "doc-4", "decisions": [
        {"left": "a", "right": "b", "decision": "Đồng ý gộp"},
        {"left": "c", "right": "d", "decision": "Không chắc"}]}, ensure_ascii=False), encoding="utf-8")
    review = load_identity_review(path, doc_id="doc-4")
    assert review == {frozenset(("a", "b")): "Đồng ý gộp", frozenset(("c", "d")): "Không chắc"}
    with pytest.raises(ValueError, match="doc_id"):
        load_identity_review(path, doc_id="doc-1")  # quyết định của tài liệu khác không được áp nhầm
    path.write_text(json.dumps({"doc_id": "doc-4", "decisions": [{"left": "a", "right": "b", "decision": "Gộp đi"}]},
                               ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="quyết định"):
        load_identity_review(path, doc_id="doc-4")


def test_description_only_candidate_needs_same_verdict_and_reuses_a6_vectors_with_anchor_context():
    for verdict, expected in (("different", {}), ("same", {"b": "a"})):
        store = Store()
        store.teaching.payload["nodes"] = [node("a", "Im f", 1, SAME), node("b", "Ảnh", 2,
            {**SAME, "char_start": 99})]
        store.teaching.payload["requires_edges"] = []
        store.teaching.payload["node_vectors_version"] = 7
        store.load_graph = lambda doc, version: SimpleNamespace(payload={"node_vectors": {"a": [1, 0], "b": [1, .01]}})
        model = Model({frozenset(("Im f", "Ảnh")): verdict})
        artifact, _ = JudgeIdentity(store, model).execute("doc", upstream=store.teaching)
        assert artifact.payload["identity_map"] == expected
        assert len(model.calls) == 1 and model.calls[0]["paired_because"] == ["description_similarity"]
        assert model.calls[0]["first"]["anchor_sentence"] == SAME["sentence"]
        config = artifact.manifest["config"]
        assert config["semantic_top_k"] == 3 and config["semantic_min_similarity"] == 0.85
