import pytest

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
    assert by_id["c"]["layer"] == 1
    assert by_id["a"]["coverage_status"] == "reviewed_no_prerequisite"
    assert by_id["c"]["coverage_status"] == "unreviewed"
    assert result["coverage_flags"] == [{"kind": "unreviewed_learnable_node", "node_id": "c"}]


def test_stage_is_layer_intersection_cluster_capped_and_chunk_keeps_all_stages():
    nodes = [node(str(index), order=index, chunks=("shared",), cluster="g1") for index in range(9)]
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
    mapping = result["chunk_stage_map"]["shared"]
    assert mapping["stage_id"] == result["stages"][0]["stage_id"]
    assert mapping["all_stage_ids"] == [stage["stage_id"] for stage in result["stages"]]


def test_kahn_uses_longest_parent_path_for_diamond_layer():
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
    assert {row["node_id"]: row["layer"] for row in result["nodes"]} == {
        "a": 1, "b": 2, "c": 3, "d": 4, "z": 1,
    }


def test_two_way_requires_is_contracted_and_surrounding_edges_still_set_layers():
    nodes = [node(value, order=index) for index, value in enumerate(("d", "a", "b", "c"))]
    result = build_roadmap(
        nodes,
        [
            {"source": "d", "target": "a", "edge_type": "requires"},
            {"source": "a", "target": "b", "edge_type": "requires"},
            {"source": "b", "target": "a", "edge_type": "requires"},
            {"source": "b", "target": "c", "edge_type": "requires"},
        ],
        [], [], [],
        stage_cap=5,
        quality_gate={"passed": True},
    )
    assert result["mode"] == "requires"
    assert result["contracted_components"] == [["a", "b"]]
    assert {row["node_id"]: row["layer"] for row in result["nodes"]} == {
        "d": 1, "a": 2, "b": 2, "c": 3,
    }


def test_roadmap_rejects_strong_component_larger_than_two_nodes():
    nodes = [node(value) for value in "abc"]
    with pytest.raises(ValueError, match="SCC requires lớn hơn hai node"):
        build_roadmap(
            nodes,
            [
                {"source": "a", "target": "b", "edge_type": "requires"},
                {"source": "b", "target": "c", "edge_type": "requires"},
                {"source": "c", "target": "a", "edge_type": "requires"},
            ],
            [], [], [],
            stage_cap=5,
            quality_gate={"passed": True},
        )


def test_document_order_fallback_keeps_a_two_node_component_in_one_layer():
    result = build_roadmap(
        [node("a", order=0), node("b", order=10), node("c", order=1)],
        [
            {"source": "a", "target": "b", "edge_type": "requires"},
            {"source": "b", "target": "a", "edge_type": "requires"},
        ],
        [], [], [],
        stage_cap=5,
        quality_gate={"passed": False},
    )
    layers = {row["node_id"]: row["layer"] for row in result["nodes"]}
    assert result["mode"] == "document_order_fallback"
    assert layers["a"] == layers["b"]
