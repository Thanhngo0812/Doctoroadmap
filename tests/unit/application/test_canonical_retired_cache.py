from doc2roadmap.domain.canonical_review import reserve_node_ids
from tests.unit.application.test_canonical_merge_review import MergeModel, run, setup_pair


def test_old_gop_cache_cannot_restore_an_id_retired_by_a_later_review(tmp_path, monkeypatch):
    store, _, left, right = setup_pair(tmp_path, monkeypatch)
    separate = run(store, MergeModel(merge=False))
    review = {frozenset((left["node_id"], right["node_id"])): "Đồng ý gộp"}
    merged = run(store, MergeModel(merge=False), merge_review=review)
    retired = set(merged.payload["redirects"]) & {left["node_id"], right["node_id"]}
    assert len(retired) == 1

    restored = run(store, MergeModel(merge=False))
    active = {node["node_id"] for node in restored.payload["nodes"]}
    assert retired.isdisjoint(active)
    assert retired <= restored.payload["redirects"].keys()
    assert restored.version != separate.version
    model = MergeModel(merge=False)
    again = run(store, model)
    assert again.version == restored.version
    assert not model.calls and not model.anchor_calls and not model.verifications


def test_reserved_id_stays_stable_when_an_unrelated_id_is_retired():
    node = {"node_id": "old", "anchor_candidate_id": "candidate", "members": ["candidate"]}
    first = dict(node)
    reserve_node_ids([first], {"redirects": {"old": "head"}})
    previous = {"nodes": [first], "redirects": {"old": "head", "unrelated": "other"}}
    second = dict(node)
    reserve_node_ids([second], previous)
    assert first["node_id"] == second["node_id"]
