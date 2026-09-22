import pytest

from doc2roadmap.domain import roadmap
from doc2roadmap.domain.roadmap import build_roadmap


def node(node_id, *, cluster="g1", order=0, chunks=()):
    return {
        "node_id": node_id,
        "name": node_id,
        "learnable": True,
        "cluster_id": cluster,
        "first_order_index": order,
        "defining_chunk_ids": list(chunks),
    }


def test_kahn_ignores_open_edges_and_reports_unreviewed_roots():
    nodes = [node("a", chunks=("c1",)), node("b", order=1, chunks=("c2",)), node("c", order=2, chunks=("c1",))]
    result = build_roadmap(
        nodes,
        [
            {"source": "a", "target": "b", "edge_type": "requires"},
            {"source": "b", "target": "a", "edge_type": "related_to"},
        ],
        [{"session_id": "main", "target_node_ids": ["a", "b"]}],
        [],
        [],
        stage_cap=5,
        quality_gate={"passed": True},
    )
    by_id = {row["node_id"]: row for row in result["nodes"]}
    assert by_id["a"]["layer"] == 1
    assert by_id["b"]["layer"] == 2
    assert by_id["c"]["layer"] in (1, 2)
    assert by_id["a"]["coverage_status"] == "reviewed_no_prerequisite"
    assert by_id["c"]["coverage_status"] == "unreviewed"
    assert result["coverage_flags"] == [{"kind": "unreviewed_learnable_node", "node_id": "c"}]


def test_stage_ignores_cluster_partition_caps_width_and_keeps_chunk_stages():
    nodes = [node(str(index), order=index, chunks=("shared",), cluster=f"g{index % 2}") for index in range(9)]
    result = build_roadmap(
        nodes,
        [],
        [{"session_id": "main", "target_node_ids": [row["node_id"] for row in nodes]}],
        [],
        [],
        stage_cap=5,
        quality_gate={"passed": True},
    )
    assert [len(stage["node_ids"]) for stage in result["stages"]] == [5, 4]
    assert len({result["nodes"][index]["stage_id"] for index in (0, 1)}) == 1
    by_id = {row["node_id"]: row for row in result["nodes"]}
    assert all(
        stage["title"] in {
            by_id[node_id]["name"] for node_id in stage["node_ids"]
            if by_id[node_id]["cluster_id"] == stage["cluster_id"]
        }
        for stage in result["stages"]
    )
    mapping = result["chunk_stage_map"]["shared"]
    assert mapping["stage_id"] == result["stages"][0]["stage_id"]
    assert mapping["all_stage_ids"] == [stage["stage_id"] for stage in result["stages"]]


def test_coffman_graham_respects_prerequisites_and_lower_bound():
    nodes = [node(value) for value in ("a", "b", "c", "d", "z")]
    result = build_roadmap(
        nodes,
        [
            {"source": "a", "target": "b", "edge_type": "requires"},
            {"source": "b", "target": "c", "edge_type": "requires"},
            {"source": "c", "target": "d", "edge_type": "requires"},
            {"source": "z", "target": "d", "edge_type": "requires"},
        ],
        [], [], [],
        stage_cap=5,
        quality_gate={"passed": True},
    )
    by_id = {row["node_id"]: row["layer"] for row in result["nodes"]}
    assert by_id["a"] < by_id["b"] < by_id["c"] < by_id["d"]
    assert by_id["z"] < by_id["d"]
    assert len(result["stages"]) >= 4
    assert all(len(stage["node_ids"]) <= 5 for stage in result["stages"])


def test_chapter_order_cannot_break_a_stage_tie():
    ids = ("a", "b", "c", "d", "e", "f", "g", "h", "i")
    first = build_roadmap([node(value, order=index) for index, value in enumerate(ids)], [], [], [], [], stage_cap=5, quality_gate={"passed": True})
    reverse = build_roadmap([node(value, order=8 - index) for index, value in enumerate(ids)], [], [], [], [], stage_cap=5, quality_gate={"passed": True})
    assert [stage["node_ids"] for stage in first["stages"]] == [stage["node_ids"] for stage in reverse["stages"]]


@pytest.mark.parametrize("cycle", [("a", "b", "a"), ("a", "b", "c", "a")])
def test_roadmap_rejects_any_requires_cycle(cycle):
    nodes = [node(value) for value in "abc"]
    with pytest.raises(ValueError, match="SCC requires"):
        build_roadmap(
            nodes,
            [
                {"source": left, "target": right, "edge_type": "requires"}
                for left, right in zip(cycle, cycle[1:])
            ],
            [], [], [],
            stage_cap=5,
            quality_gate={"passed": True},
        )


def test_closed_gate_does_not_silently_switch_to_document_order():
    result = build_roadmap(
        [node("a", order=10), node("b", order=0)],
        [{"source": "a", "target": "b", "edge_type": "requires"}],
        [], [], [],
        stage_cap=5,
        quality_gate={"passed": False},
    )
    layers = {row["node_id"]: row["layer"] for row in result["nodes"]}
    assert result["mode"] == "requires"
    assert layers["a"] < layers["b"]


def test_balancing_moves_slack_nodes_out_of_overfull_first_layer():
    nodes = [node(value) for value in ("a", "b", "c", "d", "x", "y", "z")]
    result = build_roadmap(nodes, [
        {"source": "a", "target": "b", "edge_type": "requires"},
        {"source": "b", "target": "c", "edge_type": "requires"},
        {"source": "c", "target": "d", "edge_type": "requires"},
    ], [], [], [], stage_cap=5, quality_gate={"passed": True})
    by_id = {row["node_id"]: row["layer"] for row in result["nodes"]}
    assert any(by_id[value] > 1 for value in ("x", "y", "z"))
    assert all(by_id[left] < by_id[right] for left, right in (("a", "b"), ("b", "c"), ("c", "d")))


def test_small_stages_merge_only_without_requires_between_them():
    stages = [["a"], ["b"]]
    assert roadmap._merge_small(stages, {"a": set(), "b": set()}, 3, 2) == []
    assert len(stages) == 1 and set(stages[0]) == {"a", "b"}

    blocked = [["a"], ["b"]]
    assert roadmap._merge_small(blocked, {"a": {"b"}, "b": set()}, 3, 2) == [["a"], ["b"]]
    assert blocked == [["a"], ["b"]]


def test_stage_lower_bound_assertion_rejects_broken_scheduler(monkeypatch):
    monkeypatch.setattr(
        roadmap, "_coffman_graham",
        lambda *args: ([['a', 'b']], {'a': set(), 'b': {'a'}},
                       {'a': {'b'}, 'b': set()}, 2),
    )
    with pytest.raises(AssertionError, match="cận dưới"):
        build_roadmap(
            [node("a"), node("b")],
            [{"source": "a", "target": "b", "edge_type": "requires"}],
            [], [], [], stage_cap=3, stage_floor=1, quality_gate={"passed": True},
        )
