import pytest

from doc2roadmap.domain.gold_redirects import remap_gold


def test_gold_redirects_resolve_chains_map_targets_and_count_original_collapsed_edges():
    edges = {("old_a", "old_b"), ("old_b", "a"), ("old_a", "old_c")}
    targets = {"old_b", "old_c"}
    redirects = {"old_a": "middle", "middle": "a", "old_b": "a", "old_c": "c"}
    result = remap_gold(edges, targets, redirects, {"a", "c"})

    assert result == {"edges": {("a", "c")}, "targets": {"a", "c"},
                      "dropped_gold_edges": 2, "unresolved_concepts": []}
    assert edges == {("old_a", "old_b"), ("old_b", "a"), ("old_a", "old_c")}
    assert targets == {"old_b", "old_c"}
    assert redirects["old_a"] == "middle"


def test_gold_redirects_report_every_original_unresolved_id_including_target_only_ids():
    result = remap_gold({("vanished", "a"), ("a", "foreign")}, {"target_only"},
                        {"vanished": None, "target_only": "missing"}, {"a"})
    assert result["unresolved_concepts"] == ["foreign", "target_only", "vanished"]


@pytest.mark.parametrize("redirects", [{"old": "middle", "middle": "old"}, {"old": "old"}])
def test_gold_redirect_cycle_is_rejected_even_if_the_source_id_is_in_the_graph(redirects):
    with pytest.raises(ValueError, match="vòng.*old"):
        remap_gold({("old", "a")}, {"a"}, redirects, {"old", "a"})
