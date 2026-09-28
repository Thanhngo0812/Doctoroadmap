import pytest

from doc2roadmap.domain import global_validation
from doc2roadmap.domain.global_validation import strongly_connected_components, validate_graph_rules


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


def test_two_edge_cycle_is_flagged_removed_and_does_not_count_toward_quality_gate():
    result = validate_graph_rules(
        [node("a"), node("b")],
        [
            edge("a", "b", "noi_ro", 0.9),
            edge("b", "a", "mach_trinh_bay", 0.7),
        ],
        [],
    )
    assert result["requires_edges"] == []
    assert result["removed_cycle_edges"] == []
    flag = result["two_way_flags"][0]
    assert flag["kind"] == "suspected_relation_type_error"
    assert flag["node_ids"] == ["a", "b"]
    assert [(row["source"], row["target"], row["evidence_kind"]) for row in flag["edges"]] == [
        ("a", "b", "noi_ro"),
        ("b", "a", "mach_trinh_bay"),
    ]
    assert flag["reason"]
    assert result["quality_gate"]["nonredundant_requires_edge_count"] == 0
    assert result["quality_gate"]["passed"] is False
    assert result["quality_gate"]["warning"]


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
        "nonredundant_requires_edge_count": 2,
        "learnable_node_count": 3,
        "isolated_learnable_count": 0,
        "isolated_ratio": 0.0,
        "nonredundant_edges_per_learnable": 2 / 3,
        "fallback": None,
        "warning": None,
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


def test_quality_gate_uses_pipeline_health_threshold():
    passing = validate_graph_rules(
        [node(str(value)) for value in range(20)],
        [edge("0", "1", "noi_ro", 0.9), edge("2", "3", "noi_ro", 0.9), edge("4", "5", "noi_ro", 0.9)],
        [],
    )
    failing = validate_graph_rules(
        [node(str(value)) for value in range(21)],
        [edge("0", "1", "noi_ro", 0.9), edge("2", "3", "noi_ro", 0.9), edge("4", "5", "noi_ro", 0.9)],
        [],
    )
    assert passing["quality_gate"]["passed"] is True
    assert failing["quality_gate"]["passed"] is False
    assert failing["quality_gate"]["warning"]


def test_cycle_count_budget_records_approximation_and_keeps_a_dag():
    nodes = [node(value) for value in "abcde"]
    requires = [
        edge(source, target, "noi_ro", 0.9)
        for index, source in enumerate("abcde")
        for offset in (1, 2)
        for target in ["abcde"[(index + offset) % 5]]
    ]
    result = validate_graph_rules(nodes, requires, [], cycle_budget=2)
    assert result["cycle_resolution"][0]["method"] == "approximate"
    assert result["cycle_resolution"][0]["simple_cycle_count"] > 2
    assert result["cycle_resolution"][0]["removed_weight"] > 0
    kept = {(row["source"], row["target"]) for row in result["requires_edges"]}
    assert not any((target, source) in kept for source, target in kept)
    assert max(map(len, strongly_connected_components([row["node_id"] for row in nodes], result["requires_edges"]))) == 1


def test_exact_cycle_cover_has_independent_work_budget():
    vertices = "abcde"
    internal = [
        edge(source, target, "noi_ro", 0.9)
        for source in vertices for target in vertices if source != target
    ]
    removed, method, cycle_count, _ = global_validation._feedback_edges(
        list(vertices), internal, cycle_budget=1000, work_budget=1
    )
    kept = [row for row in internal if row not in removed]
    assert method == "approximate" and cycle_count > 1
    assert all(len(component) == 1 for component in strongly_connected_components(vertices, kept))


def test_validate_dag_guard_is_a_real_error_even_if_solver_regresses(monkeypatch):
    monkeypatch.setattr(global_validation, "_feedback_edges", lambda *args, **kwargs: ([], "exact", 1, 0))
    with pytest.raises(ValueError, match="A9 cycle removal"):
        validate_graph_rules(
            [node(value) for value in "abc"],
            [edge("a", "b", "noi_ro", 0.9), edge("b", "c", "noi_ro", 0.9),
             edge("c", "a", "noi_ro", 0.9)],
            [],
        )


def test_all_reciprocal_pairs_are_flagged_before_cycle_resolution():
    nodes = [node(value) for value in "abcde"]
    requires = [
        edge(
            source,
            target,
            "noi_ro" if source < target else "mach_trinh_bay",
            0.9 if source < target else 0.7,
        )
        for source in "abcde"
        for target in "abcde"
        if source != target
    ]
    result = validate_graph_rules(nodes, requires, [])
    assert result["requires_edges"] == []
    assert len(result["two_way_flags"]) == 10
    assert result["cycle_resolution"] == []


def test_quality_gate_rejects_all_redundant_edges_despite_moderate_isolation():
    nodes = [node(str(index)) for index in range(10)]
    requires = [
        edge("0", "1", "noi_ro", 0.9),
        edge("1", "2", "noi_ro", 0.9),
        edge("0", "2", "noi_ro", 0.9),
        edge("0", "1", "noi_ro", 0.8),
        edge("1", "2", "noi_ro", 0.8),
    ]
    result = validate_graph_rules(nodes, requires, [])
    assert result["quality_gate"]["requires_edge_count"] == 5
    assert result["quality_gate"]["isolated_ratio"] == 0.7
    assert result["quality_gate"]["nonredundant_requires_edge_count"] == 0
    assert result["quality_gate"]["passed"] is False


def test_weighted_feedback_removes_two_cheap_edges_instead_of_one_expensive_edge():
    nodes = [node(value) for value in "abcd"]
    requires = [
        edge("a", "b", "noi_ro", 0.1),
        edge("b", "c", "mach_trinh_bay", 0.99),
        edge("c", "a", "mach_trinh_bay", 0.99),
        edge("b", "d", "mach_trinh_bay", 0.99),
        edge("d", "a", "mach_trinh_bay", 0.99),
    ]
    result = validate_graph_rules(nodes, requires, [])
    assert len(result["removed_cycle_edges"]) == 2
    assert ("a", "b") in {(row["source"], row["target"]) for row in result["requires_edges"]}
    assert result["cycle_resolution"][0]["simple_cycle_count"] == 2
    assert result["cycle_resolution"][0]["method"] == "exact"
    assert result == validate_graph_rules(nodes, requires, [])


def test_more_than_sixteen_edges_with_one_cycle_is_still_exact():
    ids = [f"n{index:02}" for index in range(17)]
    result = validate_graph_rules(
        [node(value) for value in ids],
        [edge(ids[index], ids[(index + 1) % len(ids)], "noi_ro", 0.9) for index in range(len(ids))],
        [],
    )
    assert result["cycle_resolution"][0]["simple_cycle_count"] == 1
    assert result["cycle_resolution"][0]["method"] == "exact"
    assert len(result["removed_cycle_edges"]) == 1


def test_confidence_does_not_break_equal_priority_cycle_tie():
    nodes = [node(value) for value in "abc"]
    requires = [
        edge("a", "b", "noi_ro", 0.1),
        edge("b", "c", "noi_ro", 0.9),
        edge("c", "a", "noi_ro", 0.9),
    ]
    first = validate_graph_rules(nodes, requires, [])
    second = validate_graph_rules(nodes, [{**row, "confidence": 1 - row["confidence"]} for row in requires], [])
    assert [(row["source"], row["target"]) for row in first["removed_cycle_edges"]] == [
        (row["source"], row["target"]) for row in second["removed_cycle_edges"]
    ]


def test_reciprocal_pair_inside_larger_component_is_removed_before_cycle_cut():
    nodes = [node(value) for value in "abc"]
    requires = [
        edge("a", "b", "noi_ro", 0.9),
        edge("b", "a", "noi_ro", 0.9),
        edge("b", "c", "noi_ro", 0.9),
        edge("c", "a", "noi_ro", 0.9),
    ]
    result = validate_graph_rules(nodes, requires, [])
    assert len(result["two_way_flags"]) == 1
    assert {(row["source"], row["target"]) for row in result["requires_edges"]} == {("b", "c"), ("c", "a")}
    assert result["cycle_resolution"] == []


def test_redundancy_is_marked_only_after_cycle_edge_is_removed():
    nodes = [node(value) for value in "abcd"]
    requires = [
        edge("a", "b", "noi_ro", 0.9),
        edge("a", "c", "noi_ro", 0.9),
        edge("b", "c", "noi_ro", 0.9),
        edge("c", "d", "noi_ro", 0.9),
        edge("d", "b", "mach_trinh_bay", 0.7),
    ]
    result = validate_graph_rules(nodes, requires, [])
    assert [(row["source"], row["target"]) for row in result["removed_cycle_edges"]] == [("d", "b")]
    direct = next(row for row in result["requires_edges"] if (row["source"], row["target"]) == ("a", "b"))
    assert "redundant_via" not in direct
    assert len(result["requires_edges"]) == 4


def test_gate_ignores_redundant_edges_even_if_raw_density_passes():
    nodes = [node(str(value)) for value in range(30)]
    requires = [
        edge("0", "1", "noi_ro", 0.9),
        edge("1", "2", "noi_ro", 0.9),
        edge("0", "2", "noi_ro", 0.9),
        edge("3", "4", "noi_ro", 0.9),
        edge("4", "5", "noi_ro", 0.9),
        edge("3", "5", "noi_ro", 0.9),
    ]
    gate = validate_graph_rules(nodes, requires, [])["quality_gate"]
    assert gate["requires_edge_count"] == 6
    assert gate["nonredundant_requires_edge_count"] == 4
    assert gate["isolated_ratio"] == 0.8
    assert gate["passed"] is False
    assert gate["warning"]


def test_outline_only_requires_is_removed_but_content_evidence_keeps_edge():
    nodes = [node("a"), node("b"), node("c")]
    outline = {**edge("a", "b", "noi_ro", 0.9), "chunk_ids": ["outline", "front", "admin", "back"]}
    content = {**edge("b", "c", "noi_ro", 0.9), "chunk_ids": ["outline", "body"]}
    result = validate_graph_rules(
        nodes, [outline, content], [],
        chunk_roles={"outline": "de_cuong", "front": "mo_dau", "admin": "hanh_chinh",
                     "back": "cuoi_sach", "body": "noi_dung"},
    )
    assert [(row["source"], row["target"]) for row in result["requires_edges"]] == [("b", "c")]
    assert result["region_flags"] == [{
        "kind": "requires_non_teaching_evidence",
        "edge": outline,
        "reason": "all cited chunks are non-teaching regions",
    }]


def test_exercise_only_requires_is_soft_and_does_not_close_hard_dag():
    nodes = [node("a"), node("b")]
    hard = {**edge("a", "b", "noi_ro", 0.9), "chunk_ids": ["body"]}
    exercise = {**edge("b", "a", "noi_ro", 0.9), "chunk_ids": ["exercise"]}
    result = validate_graph_rules(
        nodes, [hard, exercise], [],
        chunk_roles={"body": "noi_dung", "exercise": "bai_tap"},
    )
    assert [(row["source"], row["target"]) for row in result["requires_edges"]] == [("a", "b"), ("b", "a")]
    assert next(row for row in result["requires_edges"] if row["source"] == "b")["soft"] is True
    assert result["two_way_flags"] == []
    assert result["cycle_resolution"] == []
    assert result["quality_gate"]["requires_edge_count"] == 1
