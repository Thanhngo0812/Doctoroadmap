from doc2roadmap.domain.global_validation import validate_graph_rules


def node(node_id, *, learnable=True):
    return {"node_id": node_id, "learnable": learnable, "cluster_id": "g1"}


def edge(source, target, evidence, confidence, *, order="thuận", edge_type="requires"):
    return {
        "source": source,
        "target": target,
        "edge_type": edge_type,
        "evidence_kind": evidence,
        "order_relation": order,
        "independent_source_count": 1,
        "confidence": confidence,
    }


def test_cycle_cut_keeps_evidence_before_confidence_and_ignores_open_or_media_edges():
    nodes = [node("a"), node("b"), node("c"), node("media", learnable=False)]
    requires = [
        edge("a", "b", "noi_ro", 0.1, order="ngược"),
        edge("b", "c", "noi_ro", 0.2, order="thuận"),
        edge("c", "a", "mach_trinh_bay", 0.99, order="thuận"),
    ]
    open_edges = [
        edge("b", "media", "noi_ro", 1.0, edge_type="illustrated_by"),
        edge("media", "a", "noi_ro", 1.0, edge_type="illustrates"),
    ]
    result = validate_graph_rules(nodes, requires, open_edges)
    assert [(row["source"], row["target"]) for row in result["requires_edges"]] == [("a", "b"), ("b", "c")]
    assert [(row["source"], row["target"]) for row in result["removed_cycle_edges"]] == [("c", "a")]
    assert result["two_way_flags"] == []


def test_two_edge_cycle_is_flagged_kept_and_does_not_fail_quality_gate():
    result = validate_graph_rules(
        [node("a"), node("b")],
        [
            edge("a", "b", "noi_ro", 0.9),
            edge("b", "a", "mach_trinh_bay", 0.7),
        ],
        [],
    )
    assert [(row["source"], row["target"]) for row in result["requires_edges"]] == [("a", "b"), ("b", "a")]
    assert result["removed_cycle_edges"] == []
    flag = result["two_way_flags"][0]
    assert flag["kind"] == "two_way_requires"
    assert flag["node_ids"] == ["a", "b"]
    assert [(row["source"], row["target"], row["evidence_kind"]) for row in flag["edges"]] == [
        ("a", "b", "noi_ro"),
        ("b", "a", "mach_trinh_bay"),
    ]
    assert result["quality_gate"]["passed"] is True
    assert result["quality_gate"]["fallback"] is None


def test_redundant_edge_is_marked_not_removed_and_gate_counts_only_requires_learnable():
    nodes = [node("a"), node("b"), node("c")] + [node(f"m{i}", learnable=False) for i in range(10)]
    requires = [
        edge("a", "b", "noi_ro", 0.9),
        edge("b", "c", "noi_ro", 0.9),
        edge("a", "c", "noi_ro", 0.9),
    ]
    open_edges = [edge("c", "a", "noi_ro", 1.0, edge_type="related_to") for _ in range(20)]
    result = validate_graph_rules(nodes, requires, open_edges)
    direct = next(row for row in result["requires_edges"] if row["source"] == "a" and row["target"] == "c")
    assert direct["redundant_via"] == ["a", "b", "c"]
    assert len(result["requires_edges"]) == 3
    assert result["quality_gate"] == {
        "passed": True,
        "requires_edge_count": 3,
        "learnable_node_count": 3,
        "isolated_learnable_count": 0,
        "isolated_ratio": 0.0,
        "fallback": None,
    }


def test_requires_synonym_is_flagged_not_promoted():
    result = validate_graph_rules(
        [node("a"), node("b")],
        [],
        [{"source": "a", "target": "b", "edge_type": "prerequisite_of"}],
        type_aliases={"prerequisite_of": "requires"},
    )
    assert result["open_edges"][0]["edge_type"] == "prerequisite_of"
    assert any(flag["kind"] == "suspected_requires_synonym" for flag in result["type_flags"])
    assert not result["quality_gate"]["passed"]


def test_open_edge_cycle_does_not_change_requires_dag():
    result = validate_graph_rules(
        [node("a"), node("b")],
        [edge("a", "b", "noi_ro", 0.9)],
        [edge("b", "a", "noi_ro", 0.9, edge_type="related_to")],
    )
    assert [(row["source"], row["target"]) for row in result["requires_edges"]] == [("a", "b")]
    assert result["removed_cycle_edges"] == []


def test_quality_gate_keeps_exact_half_threshold():
    passing = validate_graph_rules(
        [node(value) for value in "abcd"],
        [edge("a", "b", "noi_ro", 0.9), edge("c", "d", "noi_ro", 0.9)],
        [],
    )
    failing = validate_graph_rules(
        [node(value) for value in "abcde"],
        [edge("a", "b", "noi_ro", 0.9), edge("c", "d", "noi_ro", 0.9)],
        [],
    )
    assert passing["quality_gate"]["passed"] is True
    assert failing["quality_gate"]["passed"] is False


def test_large_strong_component_uses_bounded_cycle_heuristic():
    nodes = [node(value) for value in "abcde"]
    requires = [
        edge(source, target, "noi_ro", 0.9)
        for source in "abcde"
        for target in "abcde"
        if source != target
    ]
    result = validate_graph_rules(nodes, requires, [])
    assert result["cycle_resolution"] == [{
        "node_ids": list("abcde"),
        "internal_edge_count": 20,
        "removed_edge_count": 10,
        "method": "eades_priority",
    }]
    kept = {(row["source"], row["target"]) for row in result["requires_edges"]}
    assert not any((target, source) in kept for source, target in kept)
