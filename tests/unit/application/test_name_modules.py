from types import SimpleNamespace as Obj

from doc2roadmap.application.use_cases.name_modules import NameModules


class Store:
    def __init__(self):
        self.saved = None
        self.checkpoint = None
        self.sections = [Obj(section_id="chapter", title="Introduction", parent_section_id=None, role="noi_dung"),
                         Obj(section_id="unit", title="Operations", parent_section_id="chapter", role="noi_dung")]
        self.chunks = [Obj(chunk_id="c1", parent_section_id="unit", role="noi_dung", order_index=0),
                       Obj(chunk_id="c2", parent_section_id="unit", role="noi_dung", order_index=1)]

    def load_role_chunks(self, doc_id, version):
        assert version == 4
        return Obj(version=version, result=Obj(sections=self.sections, chunks=self.chunks))

    def find_graph(self, *args):
        return None

    def load_checkpoint(self, *args):
        return self.checkpoint

    def save_checkpoint(self, doc_id, checkpoint_id, payload):
        self.checkpoint = payload

    def save_graph(self, doc_id, source_hash, config_hash, config, payload, **kwargs):
        self.saved = Obj(payload=payload, version=2, manifest={"config": config})
        return self.saved


class Model:
    model_id = "fake"

    def __init__(self):
        self.calls = 0

    def start_session(self, prompt):
        self.calls += 1
        return self

    def ask_json(self, prompt, response_schema):
        # An invented word must be rejected even if the model insists twice.
        return Obj(payload={"suffix": "unrelated"})


def upstream():
    return Obj(version=1, manifest={"config": {"chunks_version": 4}, "config_hash": "base"},
               payload={"stage": "stages", "nodes": [
                   {"node_id": "a", "name": "Addition", "teaching_chunk_ids": ["c1"]},
                   {"node_id": "b", "name": "Multiplication", "teaching_chunk_ids": ["c2"]}],
                   "modules": [{"module_id": "module_001", "node_ids": ["a"], "section_ids": ["unit"],
                                "title": "Old"},
                               {"module_id": "module_002", "node_ids": ["b"], "section_ids": ["unit"],
                                "title": "Old"}]})


def test_name_modules_dry_run_then_invalid_suffix_falls_back_to_unique_titles():
    store, model = Store(), Model()
    stage = NameModules(store, model)
    plan = stage.plan("doc", upstream=upstream())
    assert plan.remaining_items == 2
    assert model.calls == 0 and store.saved is None
    artifact, reused = stage.execute("doc", upstream=upstream())
    assert not reused and model.calls == 4
    assert [row["title"] for row in artifact.payload["modules"]] == [
        "Operations (1/2)", "Operations (2/2)"]
    assert all(row["title_source"] == "section" for row in artifact.payload["modules"])


def test_unique_content_titles_do_not_open_model_session():
    store, model, base = Store(), Model(), upstream()
    store.chunks[1].parent_section_id = "chapter"
    stage = NameModules(store, model)
    assert stage.plan("doc", upstream=base).remaining_items == 0
    artifact, _ = stage.execute("doc", upstream=base)
    assert model.calls == 0
    assert [row["title"] for row in artifact.payload["modules"]] == ["Operations", "Introduction"]


def test_title_uses_all_members_not_only_top_two_ranked_sections():
    store, model, base = Store(), Model(), upstream()
    store.chunks[1].parent_section_id = "chapter"
    base.payload["modules"] = [{"module_id": "module_001", "node_ids": ["a", "b"],
                                "section_ids": ["unit"], "title": "Old"}]
    artifact, _ = NameModules(store, model).execute("doc", upstream=base)
    assert artifact.payload["modules"][0]["title"] == "Introduction"
    assert model.calls == 0
