import json
from types import SimpleNamespace

from doc2roadmap.application.use_cases.build_main_edges import BuildMainEdges


class Model:
    model_id = "fixture-model"

    def __init__(self):
        self.calls = []

    def start_session(self, system_prompt):
        return self

    def ask_json(self, prompt, *, response_schema):
        data = json.loads(prompt.split("\nCorrect this validation error:")[0])
        self.calls.append(data)
        return SimpleNamespace(
            payload={
                "edges": [
                    {
                        "target": "b",
                        "prerequisite": "a",
                        "evidence_kind": "noi_ro",
                        "chunk_ids": ["c1"],
                        "reason": "Alpha is required before Beta",
                    }
                ],
                "flags": [],
            }
        )


class RepairModel(Model):
    def ask_json(self, prompt, *, response_schema):
        data = json.loads(prompt.split("\nCorrect this validation error:")[0])
        self.calls.append(data)
        invalid = not data.get("repair_only")
        return SimpleNamespace(payload={
            "edges": [{
                "target": "b",
                "prerequisite": "outside" if invalid else "a",
                "evidence_kind": "noi_ro",
                "chunk_ids": ["c1"],
                "reason": "repair me" if invalid else "repaired",
            }],
            "flags": [],
        })


class Store:
    def __init__(self):
        nodes = [
            {"node_id": "a", "name": "Alpha", "aliases": [], "description": "Alpha", "learnable": True, "cluster_id": "g1", "defining_chunk_ids": ["c1"]},
            {"node_id": "b", "name": "Beta", "aliases": [], "description": "Beta", "learnable": True, "cluster_id": "g1", "defining_chunk_ids": ["c1"]},
        ]
        self.mentions = SimpleNamespace(
            payload={
                "stage": "mentions",
                "nodes": nodes,
                "mention_map": {"c1": {"a": {"level": "definition"}, "b": {"level": "definition"}}},
                "suspected_pairs": [],
                "flags": [],
            },
            version=2,
            manifest={"source_hash": "mention-source", "config_hash": "mention-config"},
        )
        self.latest = self.mentions
        chunk = SimpleNamespace(chunk_id="c1", text="Alpha is required before Beta", parent_section_id="s1", order_index=0)
        section = SimpleNamespace(section_id="s1", parent_section_id=None, level=1, order_index=0)
        self.chunks = SimpleNamespace(result=SimpleNamespace(chunks=[chunk], sections=[section]), version=1, manifest={})
        self.canonical = SimpleNamespace(payload={"edges": []}, version=1, manifest={})
        self.version = 2
        self.checkpoints = {}
        self.saved_versions = 0
        self.fail_final_once = False

    def load_latest_graph(self, doc_id):
        return self.latest

    def load_graph(self, doc_id, version):
        assert version == 2
        return self.mentions

    def load_latest_chunks(self, doc_id):
        return self.chunks

    def load_latest_canonical(self, doc_id):
        return self.canonical

    def find_graph(self, doc_id, source_hash, config_hash):
        if (
            self.latest is not self.mentions
            and self.latest.manifest["source_hash"] == source_hash
            and self.latest.manifest["config_hash"] == config_hash
        ):
            return self.latest
        return None

    def load_checkpoint(self, doc_id, checkpoint_id):
        return self.checkpoints.get(checkpoint_id)

    def save_checkpoint(self, doc_id, checkpoint_id, payload):
        self.checkpoints[checkpoint_id] = json.loads(json.dumps(payload))

    def clear_checkpoint(self, doc_id, checkpoint_id):
        self.checkpoints.pop(checkpoint_id, None)

    def save_graph(self, doc_id, source_hash, config_hash, config, payload, **kwargs):
        if self.fail_final_once:
            self.fail_final_once = False
            raise RuntimeError("disk unavailable")
        self.version += 1
        self.saved_versions += 1
        self.latest = SimpleNamespace(
            payload=json.loads(json.dumps(payload)),
            version=self.version,
            path=None,
            manifest={
                "source_hash": source_hash,
                "config_hash": config_hash,
                "config": config,
                "upstream_version": kwargs["upstream_version"],
            },
        )
        return self.latest


def test_main_pass_checkpoints_and_reruns_without_model_calls():
    store, model = Store(), Model()
    use_case = BuildMainEdges(store, model, single_session_limit=20, concurrency=2)
    first, reused = use_case.execute("doc")
    assert not reused and first.payload["stage"] == "edges"
    assert len(model.calls) == 1
    assert first.payload["main_edges"] == [
        {
            "source": "a",
            "target": "b",
            "edge_type": "requires",
            "evidence_kind": "noi_ro",
            "chunk_ids": ["c1"],
            "reason": "Alpha is required before Beta",
            "confidence": 0.9,
            "explicit_evidence": True,
            "order_relation": "cùng chunk",
            "session_id": "main_single",
            "operation_index": 0,
        }
    ]
    second, reused = use_case.execute("doc")
    assert reused and second is first and len(model.calls) == 1
    assert store.saved_versions == 1


def test_main_pass_resumes_progress_file_without_creating_partial_version():
    store, model = Store(), Model()
    store.fail_final_once = True
    use_case = BuildMainEdges(store, model, single_session_limit=20, concurrency=2)
    try:
        use_case.execute("doc")
    except RuntimeError as error:
        assert str(error) == "disk unavailable"
    else:
        raise AssertionError("expected final artifact failure")
    assert len(model.calls) == 1 and store.saved_versions == 0 and store.checkpoints
    artifact, reused = use_case.execute("doc")
    assert not reused and artifact.payload["main_complete"] is True
    assert len(model.calls) == 1 and store.saved_versions == 1 and not store.checkpoints


def test_previous_edges_are_scoped_to_the_same_chapter():
    use_case = BuildMainEdges(Store(), Model())
    nodes = [
        {"node_id": "a", "name": "A"},
        {"node_id": "b", "name": "B"},
    ]
    chunks = [SimpleNamespace(chunk_id="c1", text="A", order_index=0)]
    session = {"session_id": "s1", "route": "chapter", "chapter_id": "ch1", "target_node_ids": ["a"], "allowed_node_ids": ["a", "b"], "chunk_ids": ["c1"]}
    value = use_case._input(
        session,
        nodes,
        chunks,
        {"c1": {}},
        [],
        [
            {"source": "a", "target": "b", "session_id": "s0"},
            {"source": "b", "target": "a", "session_id": "other"},
        ],
        {
            "s0": {"chapter_id": "ch1"},
            "other": {"chapter_id": "ch2"},
        },
    )
    assert [(edge["source"], edge["target"]) for edge in value["previous_edges_in_chapter"]] == [("a", "b")]


def test_executor_retries_only_rejected_operations_once():
    store, model = Store(), RepairModel()
    artifact, _ = BuildMainEdges(store, model).execute("doc")
    assert len(model.calls) == 2
    assert model.calls[1]["repair_only"] is True
    assert [(edge["source"], edge["target"]) for edge in artifact.payload["main_edges"]] == [("a", "b")]
