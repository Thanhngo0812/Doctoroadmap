import json
from types import SimpleNamespace

import pytest

from doc2roadmap.application.use_cases.canonical_reasoning import CanonicalReasoning
from doc2roadmap.application.use_cases.canonicalize import Canonicalize
from tests.unit.application.test_a4_pipeline import embedding, fixture_store, graph_with
from tests.unit.application.test_canonical_gop import AnchorModel, DOC


CUTS = [("WebSocket", "WebSockets"), ("Mutex", "Race Condition"),
        ("Golang", "Giao thức WebSockets")]


class RepairModel(AnchorModel):
    def __init__(self, *, invalid=None, relation=False):
        super().__init__()
        self.invalid, self.batches, self.repairs = invalid, [], []
        self.relation = relation

    @staticmethod
    def partition(groups):
        return {"nodes": [{"groups": [group["group_id"]], "reason": "giữ tách"} for group in groups],
                "relations": [], "deferred": []}

    def ask_json(self, prompt, *, response_schema):
        data = json.loads(prompt.split("\nCorrect this validation error:")[0])
        if "items" in data:
            self.batches.append(data)
            rows = [{"item_id": item["item_id"], "partition": self.partition(item["groups"])}
                    for item in data["items"]]
            if self.relation:
                left, right = data["items"][0]["groups"][:2]
                rows[0]["partition"]["relations"] = [{"source": left["group_id"], "target": right["group_id"],
                    "edge_type": "subtype_of", "chunk_ids": [left["evidence"][0]["chunk_id"]], "reason": "trường hợp riêng"}]
            if self.invalid and len(self.batches) == 1:
                if self.invalid == "contradiction":
                    ids = [group["group_id"] for group in data["items"][0]["groups"]]
                    rows[0]["partition"]["nodes"] = [{"groups": ids, "reason": "mâu thuẫn"}]
                elif self.invalid == "missing":
                    rows.pop(0)
                elif self.invalid == "duplicate":
                    rows.append(rows[0])
                elif self.invalid == "envelope":
                    return SimpleNamespace(payload={}, usage=self.usage)
                else:
                    rows[0]["partition"] = {}
            return SimpleNamespace(payload={"items": rows}, usage=self.usage)
        if data.get("repair_of_cut_edge"):
            self.repairs.append(data)
            value = {} if self.invalid == "always" else self.partition(data["groups"])
            return SimpleNamespace(payload=value, usage=self.usage)
        return super().ask_json(prompt, response_schema=response_schema)


def run(tmp_path, monkeypatch, *, size=10, invalid=None, store=None, relation=False):
    def graph(*args, **kwargs):
        value = graph_with([], CUTS)(*args, **kwargs)
        value["metrics"]["nomination_channels"] = {}
        return value
    monkeypatch.setattr("doc2roadmap.application.use_cases.canonicalize.nomination_graph", graph)
    store, model = store or fixture_store(tmp_path), RepairModel(invalid=invalid, relation=relation)
    artifact, reused = Canonicalize(store, embedding(),
        reasoning=CanonicalReasoning(model, model, repair_batch_size=size),
        upstream_chain="gop", anchor_batch_mode="single").execute(DOC)
    return artifact, model, store, reused


def test_cut_repairs_use_one_batch_and_count_actual_cost_once(tmp_path, monkeypatch):
    artifact, model, _, _ = run(tmp_path, monkeypatch)
    assert len(model.batches) == 1 and len(model.batches[0]["items"]) == 3
    assert model.repairs == []
    stats, cost = artifact.payload["stats"], artifact.payload["cost_summary"]["phases"]["repair"]
    assert stats["repair_batch_count"] == 1 and stats["repair_fallback_items"] == 0
    assert cost["calls"] == 1 and cost["input_tokens"] == 10 and cost["output_tokens"] == 2
    assert stats["cut_pairs_judged"] == 3


@pytest.mark.parametrize("invalid,retries", [("once", 1), ("always", 2)])
def test_only_bad_batch_item_retries_and_invalid_pair_stays_separate(tmp_path, monkeypatch, invalid, retries):
    artifact, model, _, _ = run(tmp_path, monkeypatch, invalid=invalid)
    assert len(model.batches) == 1
    assert len(model.repairs) == retries
    expected = {group["group_id"] for group in model.batches[0]["items"][0]["groups"]}
    assert all({group["group_id"] for group in item["groups"]} == expected for item in model.repairs)
    assert artifact.payload["stats"]["repair_fallback_items"] == 1
    assert artifact.payload["cost_summary"]["phases"]["repair"]["calls"] == 1 + retries
    assert artifact.payload["stats"]["cut_pairs_judged"] == (2 if invalid == "always" else 3)
    deferred = artifact.payload["deferred_pairs"]
    assert len([row for row in deferred if row["reason"] == "repair_invalid"]) == (invalid == "always")
    expected_names = {group["name"] for group in model.batches[0]["items"][0]["groups"]}
    names = {candidate["candidate_id"]: candidate["name"] for candidate in artifact.payload["source_candidates"]}
    assert not any(expected_names <= {names[member] for member in node["members"]}
                   for node in artifact.payload["nodes"])


def test_batch_size_one_matches_nodes_and_size_changes_cache(tmp_path, monkeypatch):
    first, model, store, _ = run(tmp_path, monkeypatch, size=1)
    assert len(model.repairs) == 3 and model.batches == []
    second, _, _, _ = run(tmp_path, monkeypatch, size=3, store=store)
    assert {tuple(node["members"]) for node in first.payload["nodes"]} == {
        tuple(node["members"]) for node in second.payload["nodes"]}
    assert first.manifest["config_hash"] != second.manifest["config_hash"]
    again, model, _, reused = run(tmp_path, monkeypatch, size=3, store=store)
    assert reused and again.version == second.version and not model.batches and not model.repairs


@pytest.mark.parametrize("size", [0, -1, True, 1.2])
def test_repair_batch_size_rejects_invalid(size):
    with pytest.raises(ValueError):
        CanonicalReasoning(AnchorModel(), AnchorModel(), repair_batch_size=size)


@pytest.mark.parametrize("invalid", [None, "contradiction"])
def test_each_batch_partition_keeps_relation_rules_and_retries_contradictions(tmp_path, monkeypatch, invalid):
    artifact, model, _, _ = run(tmp_path, monkeypatch, invalid=invalid, relation=True)
    proposed = [edge for edge in artifact.payload["edges"] if "2a" in edge["origins"]]
    if invalid:
        assert len(model.repairs) == 1
        assert artifact.payload["stats"]["partition_contradictions"] == 1
        assert proposed == []
    else:
        assert model.repairs == []
        assert len(proposed) == 1 and proposed[0]["edge_type"] == "subtype_of"
        assert proposed[0]["source"] != proposed[0]["target"]


@pytest.mark.parametrize("invalid,expected", [("missing", 1), ("duplicate", 1), ("envelope", 3)])
def test_malformed_batch_ids_retry_only_affected_items(tmp_path, monkeypatch, invalid, expected):
    artifact, model, _, _ = run(tmp_path, monkeypatch, invalid=invalid)
    assert len(model.batches) == 1 and len(model.repairs) == expected
    assert artifact.payload["stats"]["repair_fallback_items"] == expected
    assert artifact.payload["stats"]["cut_pairs_judged"] == 3
