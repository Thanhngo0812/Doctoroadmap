import json
from itertools import combinations

import pytest

from doc2roadmap.application.use_cases.canonicalize import Canonicalize
from doc2roadmap.application.use_cases.canonical_reasoning import CanonicalReasoning
from doc2roadmap.domain.canonical_review import shared_names
from tests.unit.application.test_a4_pipeline import fixture_store, embedding
from tests.unit.application.test_canonical_gop import AnchorModel, DOC


class MergeModel(AnchorModel):
    def __init__(self, *, merge=True, relation="dong_nhat"):
        super().__init__()
        self.merge_all, self.relation, self.verifications = merge, relation, []

    def ask_json(self, prompt, *, response_schema):
        data = json.loads(prompt.split("\nCorrect this validation error:")[0])
        if "pair_id" in data:
            from types import SimpleNamespace
            self.verifications.append(data)
            return SimpleNamespace(payload={"pair_id": data["pair_id"], "relation": self.relation,
                                             "reason": "independent"}, usage=self.usage)
        return super().ask_json(prompt, response_schema=response_schema)


def setup_pair(tmp_path, monkeypatch, *, shared=False):
    store = fixture_store(tmp_path)
    original, _ = Canonicalize(store).execute(DOC)
    nodes = [node for node in original.payload["nodes"] if not node["media_id"]]
    left, right = next((a, b) for a, b in combinations(nodes, 2) if shared_names(a, b) == shared)
    ids = [left["node_id"], right["node_id"]]
    def nominations(*args, **kwargs):
        return {"clusters": [ids], "edges": [{"source": ids[0], "target": ids[1],
                                              "channels": ["alias"], "weight": 1.}],
                "cut_edges": [], "metrics": {"nomination_channels": {"alias": 1}}}
    monkeypatch.setattr("doc2roadmap.application.use_cases.canonicalize.nomination_graph", nominations)
    return store, original, left, right


def run(store, model, **kwargs):
    return Canonicalize(store, embedding(), reasoning=CanonicalReasoning(model, model),
                        upstream_chain="gop", anchor_batch_mode="single", **kwargs).execute(DOC)[0]


def together(artifact, left, right):
    return any(set(left["members"] + right["members"]) <= set(node["members"])
               for node in artifact.payload["nodes"])


@pytest.mark.parametrize("relation,accepted", [("dong_nhat", True), ("truong_hop_rieng", False),
                                               ("khac", False), ("bad-label", False)])
def test_different_name_merge_requires_blind_independent_confirmation(tmp_path, monkeypatch, relation, accepted):
    store, _, left, right = setup_pair(tmp_path, monkeypatch)
    model = MergeModel(relation=relation)
    artifact = run(store, model)
    assert together(artifact, left, right) is accepted
    assert len(model.verifications) == (2 if relation == "bad-label" else 1)
    for data in model.verifications:
        assert set(data) == {"pair_id", "first", "second"}
        for profile in (data["first"], data["second"]):
            assert set(profile) == {"name", "aliases", "description", "evidence"}
            assert profile["evidence"] and "reason" not in profile and "verdict" not in profile
    assert artifact.payload["merge_review"][0]["first"]["evidence"]
    assert artifact.payload["merge_review"][0]["second"]["evidence"]
    assert artifact.payload["cost_summary"]["phases"]["merge_verify"]["calls"] == len(model.verifications)


def test_shared_name_alias_needs_no_verification(tmp_path, monkeypatch):
    store, _, left, right = setup_pair(tmp_path, monkeypatch, shared=True)
    model = MergeModel()
    artifact = run(store, model)
    assert together(artifact, left, right)
    assert not model.verifications and not artifact.payload["merge_review"]


@pytest.mark.parametrize("decision,model_merge,expected", [("Đồng ý gộp", False, True),
                                                           ("Không gộp", True, False)])
def test_human_overrides_model_both_directions_with_redirected_review_ids(
        tmp_path, monkeypatch, decision, model_merge, expected):
    store, original, left, right = setup_pair(tmp_path, monkeypatch)
    original.payload["redirects"] = {"old_left": left["node_id"]}
    store._write(original.path / "canonical.json", original.payload)
    model = MergeModel(merge=model_merge)
    review = {frozenset(("old_left", right["node_id"])): decision}
    artifact = run(store, model, merge_review=review)
    assert together(artifact, left, right) is expected
    if expected:
        exported = artifact.payload["merge_review"]
        assert len(exported) == 1 and exported[0]["human_override"] and exported[0]["merged"]
        assert exported[0]["first"]["evidence"] and exported[0]["second"]["evidence"]
    calls = len(model.calls), len(model.verifications), len(model.anchor_calls)
    again = run(store, model, merge_review=review)
    assert again.version == artifact.version
    assert calls == (len(model.calls), len(model.verifications), len(model.anchor_calls))


def test_retired_node_ids_are_never_reissued_when_model_splits_again(tmp_path, monkeypatch):
    store, _, left, right = setup_pair(tmp_path, monkeypatch)
    merged = run(store, MergeModel())
    retired = {left["node_id"], right["node_id"]} - {node["node_id"] for node in merged.payload["nodes"]}
    assert len(retired) == 1 and all(key in merged.payload["redirects"] for key in retired)
    splitter = MergeModel(merge=False)
    splitter.model_id = "independent-splitting-model"
    split = run(store, splitter)
    assert not together(split, left, right)
    assert retired.isdisjoint({node["node_id"] for node in split.payload["nodes"]})
    assert retired <= split.payload["redirects"].keys()


def test_review_file_hash_changes_cache_and_same_file_is_reused(tmp_path, monkeypatch):
    store, _, left, right = setup_pair(tmp_path, monkeypatch)
    review = {frozenset((left["node_id"], right["node_id"])): "Không gộp"}
    model = MergeModel()
    first = run(store, model, merge_review=review, merge_review_hash="file-before")
    second = run(store, model, merge_review=review, merge_review_hash="file-after")
    assert first.manifest["config_hash"] != second.manifest["config_hash"]
    assert first.version != second.version
    again = run(store, model, merge_review=review, merge_review_hash="file-after")
    assert again.version == second.version


def test_human_can_reject_an_exported_merge_after_its_ids_have_redirected(tmp_path, monkeypatch):
    store, _, left, right = setup_pair(tmp_path, monkeypatch)
    merged = run(store, MergeModel())
    row = merged.payload["merge_review"][0]
    assert row["merged"]
    rejected = run(store, MergeModel(), merge_review={frozenset((row["left"], row["right"])): "Không gộp"})
    assert not together(rejected, left, right)
