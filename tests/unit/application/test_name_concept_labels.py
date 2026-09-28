from types import SimpleNamespace as Obj

from doc2roadmap.application.use_cases.name_concept_labels import NameConceptLabels


class Store:
    def __init__(self):
        self.saved = None
        self.checkpoint = None

    def load_role_chunks(self, doc_id, version):
        assert version == 2
        return Obj(result=Obj(chunks=[Obj(section_path=["Tính chất 1", "Tính chất 2"])]))

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
