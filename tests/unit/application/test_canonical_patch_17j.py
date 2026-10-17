import json
from collections import Counter
from types import SimpleNamespace

import pytest

from doc2roadmap.application.use_cases.canonical_reasoning import CanonicalReasoning
from doc2roadmap.application.use_cases.canonicalize import Canonicalize
from doc2roadmap.config import Settings
from tests.unit.application.test_a4_pipeline import embedding, fixture_store, graph_with
from tests.unit.application.test_canonical_a5_anchors import IntegratedModel
from tests.unit.application.test_canonical_gop import DOC
from tests.unit.application.test_canonical_repairs import CUTS, RepairModel, run as run_repairs


@pytest.mark.parametrize("stage", ["describe", "check"])
@pytest.mark.parametrize("bad_fallback", [False, True])
def test_failed_combined_a5_call_falls_back_without_reused_key_error(tmp_path, stage, bad_fallback):
    class FailingCombined(IntegratedModel):
        def __init__(self):
            super().__init__()
            self.failed_ids, self.failed_attempts = set(), 0

        def ask_json(self, prompt, *, response_schema):
            data = json.loads(prompt.split("\nCorrect this validation error:")[0])
            items = data.get("nodes", [data])
            combined = [item for item in items if item.get("anchor_candidates")]
            current_stage = "check" if "nodes" in data else "describe"
            if combined and current_stage == stage:
                ids = {item["node_id"] for item in combined}
                if not self.failed_ids:
                    self.failed_ids = ids
                if ids == self.failed_ids:
                    self.failed_attempts += 1
                    value = {"nodes": [{"node_id": item["node_id"]} for item in items]} if stage == "check" else {}
                    return SimpleNamespace(payload=value, usage=self.usage)
            reply = super().ask_json(prompt, response_schema=response_schema)
            if bad_fallback and "candidates" in data and data["node_id"] in self.failed_ids:
                reply.payload["anchor"] = "invented"
            return reply

    store, model = fixture_store(tmp_path), FailingCombined()
    artifact, reused = Canonicalize(store, embedding(), reasoning=CanonicalReasoning(model, model),
                                    upstream_chain="gop", anchor_batch_mode="a5").execute(DOC)
    assert not reused and model.failed_ids and model.failed_attempts == 2
    nodes = {node["node_id"]: node for node in artifact.payload["nodes"]}
    fallback_counts = Counter(call["node_id"] for call in model.anchor_calls)
    assert set(fallback_counts) == model.failed_ids
    for node_id in model.failed_ids:
        assert nodes[node_id]["description_status"] == "draft_fallback_invalid"
        assert nodes[node_id]["learnable"]
        assert fallback_counts[node_id] == (2 if bad_fallback else 1)
        assert nodes[node_id]["teaching_status"] == ("uncertain" if bad_fallback else "taught")
        assert (nodes[node_id]["anchor"] is None) == bad_fallback
    failed = [row for row in artifact.payload["decision_log"]
              if row.get("origin_stage") == stage and not row["valid"]]
    assert len(failed) == 1 and "reused" not in failed[0]
    anchor_log = [row for row in artifact.payload["anchor_decision_log"]
                  if row.get("origin_stage") == stage and row["input"]["node_id"] in model.failed_ids]
    assert anchor_log and all(row["reused"] is False for row in anchor_log)


def test_default_gop_repairs_are_single_and_explicit_batching_still_changes_cache(tmp_path, monkeypatch):
    def graph(*args, **kwargs):
        value = graph_with([], CUTS)(*args, **kwargs)
        value["metrics"]["nomination_channels"] = {}
        return value
    monkeypatch.setattr("doc2roadmap.application.use_cases.canonicalize.nomination_graph", graph)
    monkeypatch.delenv("DOC2ROADMAP_CANONICAL_REPAIR_BATCH_SIZE", raising=False)
    assert Settings(_env_file=None).canonical_repair_batch_size == 1
    store, model = fixture_store(tmp_path), RepairModel()
    single, _ = Canonicalize(store, embedding(), reasoning=CanonicalReasoning(model, model),
                             upstream_chain="gop", anchor_batch_mode="single").execute(DOC)
    assert len(model.repairs) == 3 and not model.batches
    assert single.manifest["config"]["reasoning"]["repairs"]["batch_size"] == 1
    batched, model, _, _ = run_repairs(tmp_path, monkeypatch, size=3, store=store)
    assert len(model.batches) == 1 and not model.repairs
    assert single.manifest["config_hash"] != batched.manifest["config_hash"]


@pytest.mark.parametrize("route", ["merge", "repair", "repair_batch"])
@pytest.mark.parametrize("label,retries", [("synonym", 1), ("same_category", 0),
                                           ("coextensive_with", 1), ("coextensive_with_candidate", 0)])
def test_gop_identity_relation_retries_only_exact_identity_labels(tmp_path, monkeypatch, route, label, retries):
    from tests.unit.application.test_canonical_gop import AnchorModel

    class RelationModel(AnchorModel):
        def __init__(self):
            super().__init__()
            self.judgments = []

        def partition(self, groups):
            value = {"nodes": [{"groups": [group["group_id"]], "reason": "different"} for group in groups],
                     "deferred": [], "relations": []}
            if not self.judgments:
                value["relations"] = [{"source": groups[0]["group_id"], "target": groups[1]["group_id"],
                    "edge_type": label, "chunk_ids": [groups[0]["evidence"][0]["chunk_id"]], "reason": "fixture"}]
            return value

        def ask_json(self, prompt, *, response_schema):
            data = json.loads(prompt.split("\nCorrect this validation error:")[0])
            if "items" in data:
                value = {"items": [{"item_id": item["item_id"], "partition": self.partition(item["groups"])}
                                    for item in data["items"]]}
            elif "groups" in data:
                value = self.partition(data["groups"])
            else:
                return super().ask_json(prompt, response_schema=response_schema)
            self.judgments.append(data)
            return SimpleNamespace(payload=value, usage=self.usage)

    def graph(*args, **kwargs):
        pair = [CUTS[0]]
        value = graph_with(pair if route == "merge" else [], [] if route == "merge" else pair)(*args, **kwargs)
        value["metrics"]["nomination_channels"] = {}
        return value
    monkeypatch.setattr("doc2roadmap.application.use_cases.canonicalize.nomination_graph", graph)
    model = RelationModel()
    artifact, _ = Canonicalize(fixture_store(tmp_path), embedding(),
        reasoning=CanonicalReasoning(model, model, repair_batch_size=10 if route == "repair_batch" else 1),
        upstream_chain="gop", anchor_batch_mode="single").execute(DOC)
    assert len(model.judgments) == 1 + retries
    assert artifact.payload["stats"]["partition_contradictions"] == retries
    proposed = [edge for edge in artifact.payload["edges"] if "2a" in edge["origins"]]
    assert any(edge["edge_type"] == label for edge in proposed) == (not retries)
    assert artifact.manifest["config"]["reasoning"]["partition_validation"] == "consistency-gop-identity-labels-v3"
