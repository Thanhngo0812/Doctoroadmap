import json
from types import SimpleNamespace as Obj

import pytest

from doc2roadmap.application.use_cases.name_concept_labels import NameConceptLabels


class Store:
    def __init__(self):
        self.saved = None
        self.checkpoint = None

    def load_role_chunks(self, doc_id, version):
        assert version == 2
        return Obj(result=Obj(chunks=[Obj(chunk_id="c1", text="", section_path=["Tính chất 1", "Tính chất 2"])]))

    def find_graph(self, *args):
        return None

    def load_checkpoint(self, *args):
        return self.checkpoint

    def save_checkpoint(self, *args):
        self.checkpoint = args[-1]

    def save_graph(self, doc_id, source_hash, config_hash, config, payload, **kwargs):
        self.saved = Obj(payload=payload, manifest={"config": config, "stage": kwargs["manifest_fields"]["stage"]})
        return self.saved


class Model:
    model_id = "fake"

    def __init__(self):
        self.calls = 0

    def start_session(self, prompt):
        self.calls += 1
        return self

    def ask_json(self, prompt, response_schema):
        return Obj(payload={"node_id": "n1", "display_name": "Phép cộng"})


def test_post_identity_labeling_does_not_rejudge_anchor_or_identity():
    store, model = Store(), Model()
    upstream = Obj(version=3, manifest={"config_hash": "identity", "config": {"chunks_version": 2}},
                   payload={"stage": "identity", "nodes": [
                       {"node_id": "n1", "name": "Tính chất 1", "learnable": True, "teaching_status": "taught",
                        "anchor": {"sentence": "Phép cộng có tính giao hoán"}},
                       {"node_id": "n2", "name": "Tính chất 2", "learnable": True, "teaching_status": "taught",
                        "anchor": {"sentence": "Phép nhân có tính kết hợp"}},
                       {"node_id": "generic", "name": "Tính chất", "learnable": True,
                        "teaching_status": "mentioned_only"}]})
    stage = NameConceptLabels(store, model)
    assert stage.plan("doc", upstream=upstream).remaining_items == 2
    assert model.calls == 0
    artifact, reused = stage.execute("doc", upstream=upstream)
    assert not reused and artifact.payload["stage"] == "identity"
    nodes = {node["node_id"]: node for node in artifact.payload["nodes"]}
    assert nodes["n1"]["name"] == "Tính chất 1" and nodes["n1"]["display_name"] == "Phép cộng"
    assert nodes["generic"]["teaching_status"] == "not_subject_matter"
    assert upstream.payload["nodes"][2]["teaching_status"] == "mentioned_only"


@pytest.mark.parametrize("label,source,new_name", [
    ("定理2", "定理2。行列の階数は独立な列の数である。", "行列の階数"),
    ("Théorème 2", "Théorème 2. Le rang d'une matrice mesure les colonnes indépendantes.", "rang d'une matrice"),
])
def test_label_only_anchor_uses_following_sentence_in_same_chunk(label, source, new_name):
    store = Store()
    store.load_role_chunks = lambda doc_id, version: Obj(result=Obj(chunks=[Obj(
        chunk_id="c1", text=source, section_path=[label, label.replace("2", "3")])]))

    class Answer(Model):
        def ask_json(self, prompt, response_schema):
            assert source in prompt
            return Obj(payload={"node_id": "n1", "display_name": new_name})

    upstream = Obj(version=3, manifest={"config_hash": "identity", "config": {"chunks_version": 2}},
                   payload={"stage": "identity", "nodes": [{"node_id": "n1", "name": label,
                       "learnable": True, "teaching_status": "taught",
                       "anchor": {"chunk_id": "c1", "char_start": 0, "sentence": source.split("。")[0] + "。" if "。" in source else "Théorème 2."}}]})
    artifact, _ = NameConceptLabels(store, Answer()).execute("doc", upstream=upstream)
    assert artifact.payload["nodes"][0]["display_name"] == new_name


def test_label_at_end_of_anchor_uses_its_own_following_text_not_previous_or_next_label():
    store = Store()
    source = "Phép cộng đã xong. Tính chất 3. Công thức khai triển theo hàng. Tính chất 4. Công thức theo cột."
    store.load_role_chunks = lambda doc_id, version: Obj(result=Obj(chunks=[Obj(
        chunk_id="c1", text=source, section_path=["Tính chất 3", "Tính chất 4"])]))

    class Answer(Model):
        def ask_json(self, prompt, response_schema):
            evidence = json.loads(prompt)["anchor_sentence"]
            assert evidence.startswith("Tính chất 3.")
            assert "khai triển theo hàng" in evidence
            assert "Tính chất 4" not in evidence
            return Obj(payload={"node_id": "n1", "display_name": "Khai triển theo hàng"})

    upstream = Obj(version=3, manifest={"config_hash": "identity", "config": {"chunks_version": 2}},
                   payload={"stage": "identity", "nodes": [
                       {"node_id": "n1", "name": "Tính chất 3", "learnable": True, "teaching_status": "taught",
                        "anchor": {"chunk_id": "c1", "char_start": 0, "sentence": "Phép cộng đã xong. Tính chất 3."}},
                       {"node_id": "n2", "name": "Tính chất 4"}]})
    artifact, _ = NameConceptLabels(store, Answer()).execute("doc", upstream=upstream)
    assert artifact.payload["nodes"][0]["display_name"] == "Khai triển theo hàng"


def test_duplicate_display_name_retries_then_keeps_distinct_name():
    store = Store()
    attempts = []

    class Answer(Model):
        def ask_json(self, prompt, response_schema):
            attempts.append(prompt)
            return Obj(payload={"node_id": "n1", "display_name":
                               "Ma trận chuyển cơ sở" if len(attempts) == 1 else "Phép đổi cơ sở"})

    upstream = Obj(version=3, manifest={"config_hash": "identity", "config": {"chunks_version": 2}},
                   payload={"stage": "identity", "nodes": [
                       {"node_id": "n1", "name": "Tính chất 1", "learnable": True, "teaching_status": "taught",
                        "anchor": {"sentence": "Ma trận chuyển cơ sở xác định phép đổi cơ sở."}},
                       {"node_id": "n2", "name": "Phép biến đổi", "aliases": ["Ma trận chuyển cơ sở"]}]})
    artifact, _ = NameConceptLabels(store, Answer()).execute("doc", upstream=upstream)
    assert artifact.payload["nodes"][0]["display_name"] == "Phép đổi cơ sở"
    assert len(attempts) == 2 and "Ma trận chuyển cơ sở" in attempts[1]


def test_new_display_names_cannot_collide_with_each_other():
    store = Store()
    calls = []

    class Answer(Model):
        def ask_json(self, prompt, response_schema):
            node_id = json.loads(prompt.splitlines()[0])["node_id"]
            calls.append(node_id)
            name = "Phép cộng" if node_id == "n1" or calls.count("n2") == 1 else "Phép nhân"
            return Obj(payload={"node_id": node_id, "display_name": name})

    upstream = Obj(version=3, manifest={"config_hash": "identity", "config": {"chunks_version": 2}},
                   payload={"stage": "identity", "nodes": [
                       {"node_id": "n1", "name": "Tính chất 1", "learnable": True, "teaching_status": "taught",
                        "anchor": {"sentence": "Phép cộng và phép nhân có cấu trúc."}},
                       {"node_id": "n2", "name": "Tính chất 2", "learnable": True, "teaching_status": "taught",
                        "anchor": {"sentence": "Phép cộng và phép nhân có cấu trúc."}}]})
    artifact, _ = NameConceptLabels(store, Answer(), concurrency=4).execute("doc", upstream=upstream)
    assert [n["display_name"] for n in artifact.payload["nodes"]] == ["Phép cộng", "Phép nhân"]
    assert calls == ["n1", "n2", "n2"]


def test_duplicate_after_retry_keeps_original_label_and_warns():
    store = Store()

    class Answer(Model):
        def ask_json(self, prompt, response_schema):
            return Obj(payload={"node_id": "n1", "display_name": "Ma trận chuyển cơ sở"})

    upstream = Obj(version=3, manifest={"config_hash": "identity", "config": {"chunks_version": 2}},
                   payload={"stage": "identity", "nodes": [
                       {"node_id": "n1", "name": "Tính chất 1", "learnable": True, "teaching_status": "taught",
                        "anchor": {"sentence": "Ma trận chuyển cơ sở được xác định."}},
                       {"node_id": "n2", "name": "Ma trận chuyển cơ sở"}]})
    artifact, _ = NameConceptLabels(store, Answer()).execute("doc", upstream=upstream)
    assert "display_name" not in artifact.payload["nodes"][0]
    assert artifact.payload["concept_display_name_warnings"][0]["node_id"] == "n1"
