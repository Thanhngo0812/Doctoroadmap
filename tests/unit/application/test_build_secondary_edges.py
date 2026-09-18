import json
from types import SimpleNamespace

from doc2roadmap.application.use_cases.build_secondary_edges import BuildSecondaryEdges


class Model:
    model_id = "fixture-model"

    def __init__(self):
        self.calls = []

    def start_session(self, system_prompt):
        return self

    def ask_json(self, prompt, *, response_schema):
        data = json.loads(prompt.split("\nCorrect this validation error:")[0])
        self.calls.append(data)
        dossier = data["dossier"]
        return SimpleNamespace(payload={
            "pair_id": dossier["pair_id"],
            "decision": "create",
            "prerequisite": "a",
            "target": "b",
            "evidence_kind": "noi_ro",
            "chunk_ids": ["c1"],
            "reason": "explicit",
            "flags": [],
        })


class InconsistentModel(Model):
    def ask_json(self, prompt, *, response_schema):
        data = json.loads(prompt.split("\nCorrect this validation error:")[0])
        self.calls.append(data)
        dossier = data["dossier"]
        if dossier["left"] == "a":
            return SimpleNamespace(payload={
                "pair_id": dossier["pair_id"],
                "decision": "create",
                "prerequisite": "a",
                "target": "b",
                "evidence_kind": "noi_ro",
                "chunk_ids": ["c1"],
                "reason": "first order",
                "flags": [],
            })
        return SimpleNamespace(payload={
            "pair_id": dossier["pair_id"],
            "decision": "no_direct_relation",
            "flags": [],
        })


class Store:
    def __init__(self):
        nodes = [
            {"node_id": "a", "name": "A", "description": "A", "cluster_id": "g1", "learnable": True, "defining_chunk_ids": ["c1"]},
            {"node_id": "b", "name": "B", "description": "B", "cluster_id": "g1", "learnable": True, "defining_chunk_ids": ["c1"]},
        ]
        self.main = SimpleNamespace(
            payload={
                "stage": "edges",
                "nodes": nodes,
                "mention_map": {"c1": {"a": {}, "b": {}}},
                "suspected_pairs": [{"pair_id": "ab", "left": "a", "right": "b", "sources": ["citation"], "details": {"citation": ["c1"]}}],
                "pair_cluster_ledger": [],
                "routing": {"route": "chapter"},
                "main_complete": True,
                "main_edges": [],
                "main_flags": [],
                "decision_log": [],
                "executor_log": [],
            },
            version=3,
            manifest={"source_hash": "main-source", "config_hash": "main-config"},
        )
        self.latest = self.main
        chunk = SimpleNamespace(chunk_id="c1", text="A needs B", order_index=0)
        self.chunks = SimpleNamespace(result=SimpleNamespace(chunks=[chunk]), version=1, manifest={})
        self.version = 3
        self.checkpoints = {}
        self.saved_versions = 0

    def load_latest_graph(self, doc_id):
        return self.latest

    def load_graph(self, doc_id, version):
        assert version == 3
        return self.main

    def load_latest_chunks(self, doc_id):
        return self.chunks

    def find_graph(self, doc_id, source_hash, config_hash):
        if (
            self.latest is not self.main
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
        self.version += 1
        self.saved_versions += 1
        self.latest = SimpleNamespace(
            payload=json.loads(json.dumps(payload)), version=self.version, path=None,
            manifest={"source_hash": source_hash, "config_hash": config_hash, "config": config, "upstream_version": kwargs["upstream_version"]},
        )
        return self.latest


def test_secondary_asks_both_orders_uses_executor_and_reuses_final_artifact():
    store, model = Store(), Model()
    use_case = BuildSecondaryEdges(store, model, concurrency=2)
    first, reused = use_case.execute("doc")
    assert not reused and len(model.calls) == 2
    assert first.payload["secondary_edges"][0]["source"] == "a"
    assert first.payload["secondary_edges"][0]["target"] == "b"
    assert first.payload["secondary_edges"][0]["confidence"] == 0.9
    assert model.calls[0]["dossier"]["left"] == "a"
    assert model.calls[0]["dossier"]["nodes"][0]["node_id"] == "a"
    assert model.calls[1]["dossier"]["left"] == "b"
    assert model.calls[1]["dossier"]["nodes"][0]["node_id"] == "b"
    second, reused = use_case.execute("doc")
    assert reused and second is first and len(model.calls) == 2
    assert store.saved_versions == 1


def test_secondary_uses_both_verdicts_and_defers_when_decisions_differ():
    store, model = Store(), InconsistentModel()
    artifact, _ = BuildSecondaryEdges(store, model, concurrency=2).execute("doc")
    assert len(model.calls) == 2
    assert artifact.payload["secondary_edges"] == []
    assert artifact.payload["secondary_log"][-1]["reason"] == "inconsistent_orders"
