"""A4 rules exercised through canonical on the saved real extraction fixture."""
import json
import os
import subprocess
import sys
from types import SimpleNamespace

import pytest

from doc2roadmap.application.use_cases.canonicalize import Canonicalize
from doc2roadmap.application.use_cases.canonical_reasoning import CanonicalReasoning
from doc2roadmap.application.ports.embedding import EmbeddingRequest
from tests.unit.application.test_a4_pipeline import embedding, fixture_store, graph_with
from tests.unit.application.test_canonical_gop import AnchorModel, DOC


def run(store, model=None, *, embed=None, **kwargs):
    model = model or AnchorModel()
    result = Canonicalize(store, embed or embedding(), reasoning=CanonicalReasoning(model, model), **kwargs).execute(DOC)[0]
    return result, model


def test_hashseed_subprocesses_keep_real_fixture_clusters_and_payload_identical(tmp_path):
    code = '''
import json, sys
from pathlib import Path
from doc2roadmap.application.use_cases.canonicalize import Canonicalize
from doc2roadmap.application.use_cases.canonical_reasoning import CanonicalReasoning
from doc2roadmap.domain.canonical import digest
from tests.unit.application.test_a4_pipeline import fixture_store, embedding
from tests.unit.application.test_canonical_gop import AnchorModel, DOC
model = AnchorModel()
result, _ = Canonicalize(fixture_store(Path(sys.argv[1])), embedding(),
    reasoning=CanonicalReasoning(model, model),
    graph_config={"k": 3, "ngram_threshold": .5, "resolution": .5, "seed": 42, "cap": 3}).execute(DOC)
print(json.dumps({"clusters": result.payload["nominations"]["clusters"], "payload": digest(result.payload)}))
'''
    outputs = [json.loads(subprocess.check_output([sys.executable, "-X", "utf8", "-c", code,
                                                 str(tmp_path / seed)],
                    env={**os.environ, "PYTHONHASHSEED": seed}, text=True)) for seed in ("0", "1")]
    assert outputs[0]["clusters"] == outputs[1]["clusters"]
    assert outputs[0]["payload"] == outputs[1]["payload"]


def test_same_evidence_no_longer_nominates_real_fixture_pairs(tmp_path):
    store = fixture_store(tmp_path)
    result, _ = run(store)
    assert result.payload["nominations"]["edges"]
    assert not any("same_evidence" in edge["channels"] for edge in result.payload["nominations"]["edges"])
    assert result.payload["stats"]["nomination_channels"].get("same_evidence", 0) == 0
    restored, _ = run(store, a4_rules={"same_evidence_enabled": True})
    assert any("same_evidence" in edge["channels"] for edge in restored.payload["nominations"]["edges"])
    assert restored.payload["stats"]["nomination_channels"]["same_evidence"] > 0


def test_only_pure_ngram_cut_is_skipped_logged_and_kept_separate(tmp_path, monkeypatch):
    def graph(*args, **kwargs):
        result = graph_with([], [("WebSocket", "WebSockets"), ("Mutex", "Race Condition")])(*args, **kwargs)
        for index, edge in enumerate(result["edges"]):
            edge["channels"] = ["ngram"] if index == 0 else ["ngram", "name"]
        result["metrics"]["nomination_channels"] = {}
        return result
    monkeypatch.setattr("doc2roadmap.application.use_cases.canonicalize.nomination_graph", graph)
    store = fixture_store(tmp_path)
    result, model = run(store)
    repairs = [call for call in model.calls if call.get("repair_of_cut_edge")]
    assert len(repairs) == 1
    assert {group["name"] for group in repairs[0]["groups"]} == {"Mutex", "Race Condition"}
    edge = result.payload["nominations"]["cut_edges"][0]
    names = {row["candidate_id"]: row["name"] for row in result.payload["source_candidates"]}
    assert not any({"WebSocket", "WebSockets"} <= {names[key] for key in node["members"]}
                   for node in result.payload["nodes"])
    assert result.payload["stats"]["ngram_cut_pairs_skipped"] == 1
    assert any(row.get("stage") == "repair_skipped" and row.get("reason") == "ngram_only_cut"
               and set(row["pair"]) == {edge["source"], edge["target"]}
               for row in result.payload["decision_log"])
    restored, _ = run(store, a4_rules={"ngram_cut_repair_enabled": True})
    assert restored.payload["nominations"] == result.payload["nominations"]
    assert restored.payload["stats"]["ngram_cut_pairs_skipped"] == 0
    assert len([row for row in restored.payload["decision_log"] if row.get("stage") == "repair"]) == 2


def renamed_fixture(tmp_path, left, right):
    store = fixture_store(tmp_path)
    source = store.load_latest_candidates(DOC)
    mapping = {"Golang": left, "Mutex": right}
    for entity in source.payload["entities"]:
        if entity["name"] in mapping:
            entity["name_kind"] = "symbol"
        entity["name"] = mapping.get(entity["name"], entity["name"])
    store._write(source.path / "candidates.json", source.payload)
    original = Canonicalize(store).execute(DOC)[0]
    ids = {node["name"]: node["node_id"] for node in original.payload["nodes"]}

    class RenamedEmbedding:
        delegate = embedding()
        embedding_model_id = delegate.embedding_model_id

        def embed(self, requests):
            back = {value: key for key, value in mapping.items()}
            return self.delegate.embed([EmbeddingRequest(back.get(row.text, row.text), row.task_type)
                                        for row in requests])

    return store, ids, RenamedEmbedding()


class PairModel(AnchorModel):
    def __init__(self, same=()):
        super().__init__()
        self.same = {frozenset(pair) for pair in same}

    def ask_json(self, prompt, *, response_schema):
        data = json.loads(prompt.split("\nCorrect this validation error:")[0])
        if "pair_id" in data:
            return SimpleNamespace(payload={"pair_id": data["pair_id"], "relation": "dong_nhat",
                                             "reason": "independent fixture"}, usage=self.usage)
        if "groups" in data:
            self.calls.append(data)
            groups = data["groups"]
            ids = [group["group_id"] for group in groups]
            merged = frozenset(group["name"] for group in groups) in self.same
            return SimpleNamespace(payload={"nodes": [{"groups": values, "reason": "fixture"}
                for values in ([ids] if merged else [[key] for key in ids])],
                "relations": [], "deferred": []}, usage=self.usage)
        return super().ask_json(prompt, response_schema=response_schema)


def same_members(result, *names):
    members = {row["candidate_id"]: row["name"] for row in result.payload["source_candidates"]}
    return any(set(names) <= {members[key] for key in node["members"]} for node in result.payload["nodes"])


@pytest.mark.parametrize("left,right", [("Gram - Schmidt", "Gram-Schmidt"), ("χα 2", "χα^2"),
                                         ("χ0 2", "χ0^2"), ("Véc tơ tọa độ", "Véctơ tọa độ")])
def test_primary_normalized_names_override_model_different(tmp_path, monkeypatch, left, right):
    store, _, embed = renamed_fixture(tmp_path, left, right)
    def graph(*args, **kwargs):
        result = graph_with([[left, right]], [])(*args, **kwargs)
        result["metrics"]["nomination_channels"] = {}
        return result
    monkeypatch.setattr("doc2roadmap.application.use_cases.canonicalize.nomination_graph", graph)
    result, _ = run(store, PairModel(), embed=embed)
    assert same_members(result, left, right)
    without, _ = run(store, PairModel(), embed=embed, a4_rules={"normalized_name_merge": False})
    assert not same_members(without, left, right)


def test_human_different_wins_primary_normalized_name_constraint(tmp_path, monkeypatch):
    left, right = "Gram - Schmidt", "Gram-Schmidt"
    store, ids, embed = renamed_fixture(tmp_path, left, right)
    def graph(*args, **kwargs):
        result = graph_with([[left, right]], [])(*args, **kwargs)
        result["metrics"]["nomination_channels"] = {}
        return result
    monkeypatch.setattr("doc2roadmap.application.use_cases.canonicalize.nomination_graph", graph)
    result, _ = run(store, PairModel([(left, right)]), embed=embed,
                    merge_review={frozenset((ids[left], ids[right])): "Không gộp"})
    assert not same_members(result, left, right)


@pytest.mark.parametrize("failure", ["invalid", "deferred"])
@pytest.mark.parametrize("constraint", ["normalized_name", "human_same"])
def test_successful_constraint_merge_clears_failed_group_deferrals_only(
        tmp_path, monkeypatch, failure, constraint):
    left, right, third = "Gram - Schmidt", "Gram-Schmidt", "Race Condition"
    store, ids, embed = renamed_fixture(tmp_path, left, right)

    class FailedModel(PairModel):
        def ask_json(self, prompt, *, response_schema):
            data = json.loads(prompt.split("\nCorrect this validation error:")[0])
            if "groups" not in data:
                return super().ask_json(prompt, response_schema=response_schema)
            self.calls.append(data)
            value = {} if failure == "invalid" else {"nodes": [], "relations": [], "deferred": [
                {"group_id": group["group_id"], "reason": "uncertain fixture"} for group in data["groups"]]}
            return SimpleNamespace(payload=value, usage=self.usage)

    def graph(*args, **kwargs):
        result = graph_with([[left, right, third]], [])(*args, **kwargs)
        result["metrics"]["nomination_channels"] = {}
        return result

    monkeypatch.setattr("doc2roadmap.application.use_cases.canonicalize.nomination_graph", graph)
    options = ({"a4_rules": {"normalized_name_merge": False},
                "merge_review": {frozenset((ids[left], ids[right])): "Đồng ý gộp"}}
               if constraint == "human_same" else {})
    result, _ = run(store, FailedModel(), embed=embed, **options)
    assert same_members(result, left, right)
    assert not same_members(result, left, third)
    assert result.payload["deferred"] == [ids[third]]
    assert result.payload["stats"]["deferred_groups"] == 1


@pytest.mark.parametrize("constraint", ["normalized_name", "human_same"])
def test_successful_constraint_merge_clears_only_resolved_deferred_pairs(tmp_path, monkeypatch, constraint):
    left, right, third, fourth = "Gram - Schmidt", "Gram-Schmidt", "Race Condition", "WebSocket"
    store, ids, embed = renamed_fixture(tmp_path, left, right)

    class FailedRepair(PairModel):
        def ask_json(self, prompt, *, response_schema):
            data = json.loads(prompt.split("\nCorrect this validation error:")[0])
            if data.get("repair_of_cut_edge"):
                self.calls.append(data)
                return SimpleNamespace(payload={}, usage=self.usage)
            return super().ask_json(prompt, response_schema=response_schema)

    def graph(*args, **kwargs):
        result = graph_with([], [(left, right), (third, fourth)])(*args, **kwargs)
        result["metrics"]["nomination_channels"] = {}
        return result

    monkeypatch.setattr("doc2roadmap.application.use_cases.canonicalize.nomination_graph", graph)
    options = ({"a4_rules": {"normalized_name_merge": False},
                "merge_review": {frozenset((ids[left], ids[right])): "Đồng ý gộp"}}
               if constraint == "human_same" else {})
    result, _ = run(store, FailedRepair(), embed=embed, **options)
    assert same_members(result, left, right)
    assert not same_members(result, third, fourth)
    assert len(result.payload["deferred_pairs"]) == 1
    pair = result.payload["deferred_pairs"][0]
    assert set(pair["pair"]) == {ids[third], ids[fourth]} and pair["reason"] == "repair_invalid"
    assert result.payload["stats"]["deferred_pairs"] == 1
    failed = [row for row in result.payload["decision_log"] if row.get("stage") == "repair"]
    assert len(failed) == 2 and all(not row["valid"] and len(row["attempts"]) == 2 for row in failed)


def test_shared_alias_does_not_force_primary_name_merge(tmp_path, monkeypatch):
    store = fixture_store(tmp_path)
    source = store.load_latest_candidates(DOC)
    for row in source.payload["entities"]:
        if row["name"] in {"Golang", "Mutex"}:
            row["aliases"] = [{"name": "Shared alias", "evidence": row["evidence"][0]}]
    store._write(source.path / "candidates.json", source.payload)
    def graph(*args, **kwargs):
        result = graph_with([["Golang", "Mutex"]], [])(*args, **kwargs)
        result["metrics"]["nomination_channels"] = {}
        return result
    monkeypatch.setattr("doc2roadmap.application.use_cases.canonicalize.nomination_graph", graph)
    result, _ = run(store, PairModel())
    assert not same_members(result, "Golang", "Mutex")


def test_conflict_keeps_only_normalized_name_pair_and_defers_other_groups(tmp_path, monkeypatch):
    left, right, third = "Gram - Schmidt", "Gram-Schmidt", "Race Condition"
    store, ids, embed = renamed_fixture(tmp_path, left, right)
    def graph(*args, **kwargs):
        result = graph_with([], [(left, right), (right, third), (left, third)])(*args, **kwargs)
        result["metrics"]["nomination_channels"] = {}
        return result
    monkeypatch.setattr("doc2roadmap.application.use_cases.canonicalize.nomination_graph", graph)
    # Turn off forced names so this checks the conservative conflict rule independently.
    result, _ = run(store, PairModel([(left, right), (right, third)]), embed=embed,
                    a4_rules={"normalized_name_merge": False})
    assert same_members(result, left, right)
    assert not same_members(result, left, third)
    assert ids[third] in result.payload["deferred"]
    assert not ({ids[left], ids[right]} & set(result.payload["deferred"]))
    row = next(row for row in result.payload["decision_log"] if row.get("stage") == "transitive_conflict")
    assert {tuple(sorted(pair)) for pair in row["retained_pairs"]} == {tuple(sorted((ids[left], ids[right])))}
    without, _ = run(store, PairModel([(left, right), (right, third)]), embed=embed,
                     a4_rules={"normalized_name_merge": False, "conservative_conflicts": False})
    assert not same_members(without, left, right)


def test_coextensive_relation_between_separate_nodes_is_retried(tmp_path, monkeypatch):
    class CoextensiveModel(PairModel):
        def ask_json(self, prompt, *, response_schema):
            data = json.loads(prompt.split("\nCorrect this validation error:")[0])
            reply = super().ask_json(prompt, response_schema=response_schema)
            if "groups" in data and len([row for row in self.calls if "groups" in row]) == 1:
                left, right = data["groups"]
                reply.payload["relations"] = [{"source": left["group_id"], "target": right["group_id"],
                    "edge_type": "  COEXTENSIVE_WITH  ", "chunk_ids": [left["evidence"][0]["chunk_id"]],
                    "reason": "same extension"}]
            return reply
    def graph(*args, **kwargs):
        result = graph_with([["Golang", "Mutex"]], [])(*args, **kwargs)
        result["metrics"]["nomination_channels"] = {}
        return result
    monkeypatch.setattr("doc2roadmap.application.use_cases.canonicalize.nomination_graph", graph)
    result, model = run(fixture_store(tmp_path), CoextensiveModel())
    assert len([row for row in model.calls if "groups" in row]) == 2
    assert result.payload["stats"]["partition_contradictions"] == 1
    assert not any(edge["edge_type"] == "coextensive_with" for edge in result.payload["edges"])


@pytest.mark.parametrize("rule", ["deterministic_clustering", "same_evidence_enabled", "ngram_cut_repair_enabled",
                                  "conservative_conflicts", "normalized_name_merge", "coextensive_identity"])
def test_each_rule_has_its_own_reversible_cache_entry(tmp_path, rule):
    from doc2roadmap.application.use_cases.canonical_a4_rules import DEFAULT_A4_RULES

    store = fixture_store(tmp_path)
    first, _ = run(store)
    opposite = not DEFAULT_A4_RULES[rule]
    changed, _ = run(store, a4_rules={rule: opposite})
    assert changed.manifest["config"]["a4_rules"][rule]["enabled"] is opposite
    assert first.manifest["config_hash"] != changed.manifest["config_hash"]
    restored, model = run(store)
    assert restored.version == first.version and not model.calls and not model.anchor_calls
