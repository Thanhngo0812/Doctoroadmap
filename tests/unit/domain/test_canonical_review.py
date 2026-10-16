import pytest

from doc2roadmap.domain.canonical_review import reviewed_components, review_constraints, validate_merge_verification


def test_human_same_block_survives_transitive_model_conflict():
    groups, conflicts = reviewed_components(["a", "b", "c"], [("b", "c")], [("a", "b"), ("a", "c")],
                                            [("a", "b")], [])
    assert ["a", "b"] in groups and ["c"] in groups
    assert conflicts == [["a", "b", "c"]]


def test_human_different_breaks_transitive_model_merge_and_conflicting_human_file_is_rejected():
    groups, _ = reviewed_components(["a", "b", "c"], [("a", "c"), ("b", "c")], [], [], [("a", "b")])
    assert groups == [["a"], ["b"], ["c"]]
    with pytest.raises(ValueError, match="bắc cầu"):
        reviewed_components(["a", "b", "c"], [], [], [("a", "c"), ("b", "c")], [("a", "b")])


@pytest.mark.parametrize("previous,review,message", [
    ({"redirects": {"a": "b", "b": "a"}}, {frozenset(("a", "c")): "Không gộp"}, "vòng"),
    ({}, {frozenset(("missing", "c")): "Không gộp"}, "không thuộc"),
    ({}, {frozenset(("a", "c")): "unknown"}, "không hợp lệ"),
])
def test_review_rejects_invalid_ids_cycles_and_decisions(previous, review, message):
    nodes = [{"node_id": key, "members": [key]} for key in "abc"]
    with pytest.raises(ValueError, match=message):
        review_constraints(review, previous, nodes)


@pytest.mark.parametrize("bad", [{}, {"pair_id": "other"},
                                  {"pair_id": "p", "relation": "bad", "reason": "x"},
                                  {"pair_id": "p", "relation": "dong_nhat", "reason": " "}])
def test_merge_verification_rejects_invalid_contract(bad):
    with pytest.raises(ValueError):
        validate_merge_verification(bad, pair_id="p")
