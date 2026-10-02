import json
from types import SimpleNamespace

import pytest

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


class PairModel(Model):
    def ask_json(self, prompt, *, response_schema):
        data = json.loads(prompt.split("\nCorrect this validation error:")[0])
        self.calls.append(data)
        dossier = data["dossier"]
        prerequisite, target = sorted((dossier["left"], dossier["right"]))
        return SimpleNamespace(payload={
            "pair_id": dossier["pair_id"],
            "decision": "create",
            "prerequisite": prerequisite,
            "target": target,
            "evidence_kind": "noi_ro",
            "chunk_ids": ["c1"],
            "reason": "explicit",
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
                "decision_log": [{"stage": "main", "large": True}],
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
    assert first.payload["main_decision_log_version"] == store.main.version
    assert all(row.get("stage") == "secondary" for row in first.payload["decision_log"])
    assert first.payload["stats"]["evidence_hard_count"] == 0
    assert first.payload["stats"]["evidence_soft_count"] == 1
    second, reused = BuildSecondaryEdges(store, model, concurrency=100, window_pairs=50).execute("doc")
    assert reused and second is first and len(model.calls) == 2
    assert store.saved_versions == 1
    assert not store.checkpoints


def test_secondary_uses_both_verdicts_and_defers_when_decisions_differ():
    store, model = Store(), InconsistentModel()
    artifact, _ = BuildSecondaryEdges(store, model, concurrency=2).execute("doc")
    assert len(model.calls) == 2
    assert artifact.payload["secondary_edges"] == []
    assert artifact.payload["secondary_log"][-1]["reason"] == "inconsistent_orders"


def test_secondary_downgrades_hard_quote_outside_definition_after_one_retry():
    class OutsideWindowModel(Model):
        def ask_json(self, prompt, *, response_schema):
            data = json.loads(prompt.split("\nCorrect this validation error:")[0])
            self.calls.append(data)
            return SimpleNamespace(payload={
                "pair_id": data["dossier"]["pair_id"], "decision": "create",
                "prerequisite": "a", "target": "b", "evidence_kind": "noi_ro",
                "prerequisite_kind": "can_de_hieu", "chunk_ids": ["c1"],
                "quote": "A helps solve the exercise.", "reason": "Only an exercise uses A.", "flags": [],
            })

    store, model = Store(), OutsideWindowModel()
    store.main.payload["definition_contract"] = True
    store.main.payload["nodes"][1]["anchor"] = {
        "chunk_id": "c1", "char_start": 0, "sentence": "B is a concept."
    }
    store.chunks.result.chunks[0].text = (
        "B is a concept. It has properties. We study it. A helps solve the exercise."
    )
    artifact, _ = BuildSecondaryEdges(store, model, concurrency=2).execute("doc")
    assert len(model.calls) == 4  # Two orders, one repair each.
    edge = artifact.payload["secondary_edges"][0]
    assert edge["soft"] is True and edge["soft_reason"] == "cong_cu"
    assert all(row.get("downgraded_to_cong_cu_after_retry") for row in artifact.payload["decision_log"])


def test_secondary_rejects_an_incomplete_main_pass():
    store = Store()
    store.main.payload["main_complete"] = False
    with pytest.raises(ValueError, match="pass chính hoàn chỉnh"):
        BuildSecondaryEdges(store, Model()).execute("doc")


def test_secondary_stops_at_clusters_instead_of_following_a_cross_tier_version():
    store = Store()
    store.latest = SimpleNamespace(payload={"stage": "clusters"}, version=8, manifest={"upstream_version": None})
    with pytest.raises(ValueError, match="không trỏ về stage edges"):
        BuildSecondaryEdges(store, Model()).execute("doc")


def test_secondary_resume_and_uninterrupted_run_prune_the_same_pairs_with_logs():
    class ChainStore(Store):
        def __init__(self, *, interrupt=False):
            super().__init__()
            self.main.payload["nodes"].append({
                "node_id": "c", "name": "C", "description": "C", "cluster_id": "g1",
                "learnable": True, "defining_chunk_ids": ["c1"],
            })
            self.main.payload["mention_map"]["c1"]["c"] = {"channels": ["exact"]}
            self.main.payload["suspected_pairs"] = [
                {"pair_id": "ab", "left": "a", "right": "b", "sources": ["citation"], "details": {}},
                {"pair_id": "ac", "left": "a", "right": "c", "sources": ["citation"], "details": {}},
            ]
            self.main.payload["main_edges"] = [{
                "source": "b", "target": "c", "edge_type": "requires", "explicit_evidence": True,
            }]
            self.interrupt = interrupt

        def save_checkpoint(self, doc_id, checkpoint_id, payload):
            super().save_checkpoint(doc_id, checkpoint_id, payload)
            if self.interrupt:
                self.interrupt = False
                raise RuntimeError("interrupted after first pair")

    continuous_store, continuous_model = ChainStore(), PairModel()
    continuous, _ = BuildSecondaryEdges(continuous_store, continuous_model).execute("doc")

    resumed_store, resumed_model = ChainStore(interrupt=True), PairModel()
    with pytest.raises(RuntimeError, match="interrupted"):
        BuildSecondaryEdges(resumed_store, resumed_model).execute("doc")
    resumed, _ = BuildSecondaryEdges(resumed_store, resumed_model).execute("doc")

    assert resumed.payload["secondary_edges"] == continuous.payload["secondary_edges"]
    assert resumed.payload["secondary_log"] == continuous.payload["secondary_log"]
    assert resumed.payload["stats"]["pruned_secondary_pair_count"] == 1
    assert resumed.payload["stats"]["completed_secondary_pair_count"] == 2
    assert any(row["pair_id"] == "ac" and row["status"] == "pruned_explicit_path" for row in resumed.payload["secondary_log"])


@pytest.mark.parametrize("window", [1, 4, 50])
def test_secondary_windows_commit_exactly_like_sequential_and_reask_changed_dossier(window):
    class WindowStore(Store):
        def __init__(self):
            super().__init__()
            self.main.payload["nodes"].append({
                "node_id": "c", "name": "C", "description": "C", "cluster_id": "g1",
                "learnable": True, "defining_chunk_ids": ["c1"],
            })
            self.main.payload["mention_map"]["c1"]["c"] = {"channels": ["exact"]}
            self.main.payload["suspected_pairs"] = [
                {"pair_id": "ab", "left": "a", "right": "b", "sources": ["citation"], "details": {}},
                {"pair_id": "ac", "left": "a", "right": "c", "sources": ["citation"], "details": {}},
            ]
            self.main.payload["main_edges"] = [{
                "source": "b", "target": "c", "edge_type": "requires", "explicit_evidence": True,
            }]

    class WindowModel(PairModel):
        def ask_json(self, prompt, *, response_schema):
            reply = super().ask_json(prompt, response_schema=response_schema)
            reply.payload["evidence_kind"] = "mach_trinh_bay"
            return reply

    sequential_store, sequential_model = WindowStore(), WindowModel()
    sequential, _ = BuildSecondaryEdges(sequential_store, sequential_model, concurrency=2, window_pairs=1).execute("doc")
    batched_store, batched_model = WindowStore(), WindowModel()
    batched, _ = BuildSecondaryEdges(batched_store, batched_model, concurrency=100, window_pairs=window).execute("doc")

    assert batched.payload["secondary_edges"] == sequential.payload["secondary_edges"]
    assert batched.payload["secondary_log"] == sequential.payload["secondary_log"]
    if window > 1:
        ac_calls = [row for row in batched_model.calls if row["dossier"]["pair_id"] == "ac"]
        assert len(ac_calls) == 4
        assert ac_calls[-1]["dossier"]["indirect_path"] is not None
