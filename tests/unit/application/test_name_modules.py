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
        manifest = {"role_transfer": {"reference_version": 7}} if hasattr(self, "reference") else {}
        return Obj(version=version, manifest=manifest, result=Obj(sections=self.sections, chunks=self.chunks))

    def load_chunks(self, doc_id, version):
        assert version == 7
        return self.reference

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


class RepairModel(Model):
    def ask_json(self, prompt, response_schema):
        return Obj(payload={"suffix": "Addition" if "module_001" in prompt else "Multiplication"})


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
        "Operations — Addition", "Operations — Multiplication"]
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


def test_single_concept_title_does_not_gain_one_of_one():
    store, model, base = Store(), Model(), upstream()
    store.chunks[0].parent_section_id = "missing"
    base.payload["modules"] = [base.payload["modules"][0]]
    artifact, _ = NameModules(store, model).execute("doc", upstream=base)
    assert artifact.payload["modules"][0]["title"] == "Addition"
    assert model.calls == 0


def test_valid_prior_decision_is_reused_but_invalid_old_suffix_is_reasked():
    old = Obj(payload={"module_title_decision_log": [
        {"valid": True, "input": {"module_id": "module_001", "section_title": "Operations",
                                  "concept_names": ["Addition"]}, "output": {"suffix": "Addition"}},
        {"valid": True, "input": {"module_id": "module_002", "section_title": "Operations",
                                  "concept_names": ["Multiplication"]}, "output": {"suffix": "Operations"}},
    ]})
    store, model = Store(), RepairModel()
    stage = NameModules(store, model, reuse_artifact=old)
    assert stage.plan("doc", upstream=upstream()).remaining_items == 1
    artifact, _ = stage.execute("doc", upstream=upstream())
    assert model.calls == 1
    assert [m["title"] for m in artifact.payload["modules"]] == [
        "Operations — Addition", "Operations — Multiplication"]


def test_reference_tree_replaces_broken_section_path_for_titles_only():
    store, model, base = Store(), Model(), upstream()
    store.chunks = [Obj(chunk_id="c1", text="uno dos tres cuatro cinco seis siete ocho",
                        parent_section_id="unit", role="noi_dung", order_index=0)]
    store.sections = [Obj(section_id="unit", title="Chapter 1", parent_section_id=None, role="noi_dung")]
    store.reference = Obj(version=7, result=Obj(
        sections=[Obj(section_id="real", title="Álgebra lineal", parent_section_id=None, role="noi_dung")],
        chunks=[Obj(chunk_id="new", text="uno dos tres cuatro cinco seis siete ocho",
                    parent_section_id="real", role="noi_dung", order_index=0)]))
    base.payload["modules"] = [base.payload["modules"][0]]
    artifact, _ = NameModules(store, model).execute("doc", upstream=base)
    assert artifact.payload["modules"][0]["title"] == "Álgebra lineal"
    assert base.payload["modules"][0]["node_ids"] == ["a"]


def test_a10_section_assignment_is_reused_for_names_without_second_transfer():
    store, model, base = Store(), Model(), upstream()
    store.reference = Obj(version=7, result=Obj(
        sections=[Obj(section_id="new", title="Álgebra lineal", parent_section_id=None,
                      level=2, role="noi_dung", order_index=1)], chunks=[]))
    base.manifest["config"]["title_sections_version"] = 7
    base.payload["modules"] = [{**base.payload["modules"][0], "title_section_ids": ["new"]}]
    artifact, _ = NameModules(store, model).execute("doc", upstream=base)
    assert artifact.payload["modules"][0]["title"] == "Álgebra lineal"
    assert model.calls == 0


def test_fallback_uses_first_and_highest_outdegree_full_concept_names():
    store, model, base = Store(), Model(), upstream()
    base.payload["nodes"].append({"node_id": "c", "name": "Division", "teaching_chunk_ids": ["c2"]})
    base.payload["modules"][0]["node_ids"] = ["a", "b", "c"]
    base.payload["modules"][1]["node_ids"] = ["c"]
    base.payload["requires_edges"] = [{"source": "b", "target": "a"},
                                      {"source": "b", "target": "c"}]
    artifact, _ = NameModules(store, model).execute("doc", upstream=base)
    assert artifact.payload["modules"][0]["title"] == "Operations — Addition · Multiplication"


def test_fallback_keeps_full_concepts_but_does_not_make_sentence_long_title():
    store, model, base = Store(), Model(), upstream()
    base.payload["nodes"][0]["name"] = "Upper bound on number of distinct eigenvalues"
    base.payload["nodes"][1]["name"] = "Product of polynomials"
    base.payload["modules"][0]["node_ids"] = ["a", "b"]
    artifact, _ = NameModules(store, model).execute("doc", upstream=base)
    assert all(len(module["title"].split()) <= 12 for module in artifact.payload["modules"])
    assert "Upper bound on number of distinct eigenvalues" in artifact.payload["modules"][0]["title"]


def test_long_base_does_not_force_numbered_title_when_no_full_concept_fits():
    store, model, base = Store(), Model(), upstream()
    store.sections[1].title = "1.1 Các khái niệm và bài toán học cơ bản"
    base.payload["nodes"][0]["name"] = "Lọc thư rác"
    base.payload["nodes"][1]["name"] = "Bài toán phân loại"
    artifact, _ = NameModules(store, model).execute("doc", upstream=base)
    assert all("(" not in module["title"] for module in artifact.payload["modules"])
