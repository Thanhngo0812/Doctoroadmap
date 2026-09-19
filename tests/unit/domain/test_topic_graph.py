from types import SimpleNamespace

import pytest

from doc2roadmap.application.leiden_cluster import _merge_tiny_groups, cluster_nodes, weighted_concept_density
from doc2roadmap.domain.topic_graph import build_topic_edges


def node(node_id, *, learnable=True, media=False, chunks=()):
    return {
        "node_id": node_id,
        "name": node_id,
        "description": node_id,
        "learnable": learnable,
        "media_id": node_id if media else None,
        "source_chunk_ids": list(chunks),
        "defining_chunk_ids": list(chunks),
        "first_order_index": 0,
    }


def chunk(chunk_id, section_id, order_index, *, images=()):
    return SimpleNamespace(
        chunk_id=chunk_id,
        parent_section_id=section_id,
        order_index=order_index,
        image_refs=[SimpleNamespace(image_id=value) for value in images],
    )


def test_topic_graph_uses_three_channels_and_has_no_cosine_floor():
    nodes = [
        node("a", chunks=("c1",)),
        node("b", chunks=("c1",)),
        node("m", learnable=False, media=True, chunks=("c1",)),
    ]
    result = build_topic_edges(
        nodes,
        [chunk("c1", "s1", 0, images=("m",))],
        {"a": (1.0, 0.0), "b": (-1.0, 0.0), "m": (0.0, 1.0)},
        semantic_neighbors=1,
        edge_quantile=0.0,
    )
    channels = {name for edge in result["edges"] for name in edge["channels"]}
    assert channels == {"cooccurrence", "semantic", "media"}
    negative = build_topic_edges(
        [node("x"), node("y")],
        [],
        {"x": (1.0, 0.0), "y": (-1.0, 0.0)},
        semantic_neighbors=1,
        edge_quantile=0.0,
    )
    assert any(
        edge["channels"].get("semantic")
        for edge in negative["edges"]
        if {edge["source"], edge["target"]} == {"x", "y"}
    )


def test_media_hub_and_busy_chunk_are_downweighted_and_warned():
    nodes = [node(str(i), chunks=("busy",)) for i in range(5)]
    nodes.append(node("media", learnable=False, media=True, chunks=("busy",)))
    result = build_topic_edges(
        nodes,
        [chunk("busy", "s1", 0, images=("media",))],
        {item["node_id"]: (1.0, float(index)) for index, item in enumerate(nodes)},
        semantic_neighbors=1,
        edge_quantile=0.0,
    )
    assert result["warnings"] == ["media_degree:media:5"]
    media_weights = [
        edge["channels"]["media"]
        for edge in result["edges"]
        if "media" in edge["channels"]
    ]
    assert media_weights and max(media_weights) <= 1.0
    assert result["channel_maxima"]["media"] < 1.0


def test_leiden_cap_counts_concepts_not_media_and_keeps_isolates():
    nodes = [node("a"), node("b"), node("c"), node("orphan")]
    nodes += [node(f"m{i}", learnable=False, media=True) for i in range(3)]
    connected = ["a", "b", "c", "m0", "m1", "m2"]
    edges = [
        {"source": left, "target": right, "weight": 1.0, "channels": {}}
        for index, left in enumerate(connected)
        for right in connected[index + 1 :]
    ]
    clusters, stats = cluster_nodes(
        nodes,
        edges,
        {item["node_id"]: (1.0, 0.0) for item in nodes},
        resolution=0.01,
        seed=42,
        concept_cap=2,
    )
    assert set(clusters) == {item["node_id"] for item in nodes}
    members = {}
    for node_id, cluster_id in clusters.items():
        members.setdefault(cluster_id, []).append(node_id)
    assert all(sum(not value.startswith("m") for value in ids) <= 2 for ids in members.values())
    assert any(len(ids) > 2 for ids in members.values())
    assert "orphan" in clusters
    assert max(stats["raw_cluster_node_sizes"]) > 2


def test_leiden_raw_partition_finds_two_clear_communities_before_merging():
    nodes = [node(value) for value in ("a1", "a2", "a3", "b1", "b2", "b3")]
    edges = []
    for prefix in ("a", "b"):
        ids = [f"{prefix}{index}" for index in range(1, 4)]
        edges.extend(
            {"source": left, "target": right, "weight": 1.0, "channels": {}}
            for index, left in enumerate(ids)
            for right in ids[index + 1:]
        )
    _, stats = cluster_nodes(
        nodes,
        edges,
        {item["node_id"]: (1.0, 0.0) if item["node_id"].startswith("a") else (0.0, 1.0) for item in nodes},
        resolution=0.1,
        seed=42,
        concept_cap=6,
    )
    assert stats["raw_cluster_count"] == 2
    assert stats["raw_cluster_concept_sizes"] == [3, 3]
    assert stats["merge_count"] == 0


def test_tiny_merge_includes_two_concepts_and_prefers_cross_weight_before_similarity():
    nodes = [node(value) for value in ("s1", "s2", "w1", "w2", "w3", "v1", "v2", "v3")]
    node_by_id = {row["node_id"]: row for row in nodes}
    groups = {0: {"s1", "s2"}, 1: {"w1", "w2", "w3"}, 2: {"v1", "v2", "v3"}}
    vectors = {
        **{value: (1.0, 0.0) for value in ("s1", "s2", "v1", "v2", "v3")},
        **{value: (0.0, 1.0) for value in ("w1", "w2", "w3")},
    }
    weights = {
        frozenset(("s1", "w1")): 2.0,
        frozenset(("s1", "v1")): 1.0,
    }
    merged, count, affected = _merge_tiny_groups(groups, node_by_id, weights, vectors, 5)
    assert count == 1
    assert {"s1", "s2", "w1", "w2", "w3"} in merged.values()
    assert affected == {"s1", "s2", "w1", "w2", "w3"}


def test_weighted_density_uses_unordered_concept_pairs_and_ignores_media_edges():
    nodes = [node("a"), node("b"), node("c"), node("media", learnable=False, media=True)]
    edges = [
        {"source": "a", "target": "b", "weight": 0.6},
        {"source": "b", "target": "c", "weight": 0.3},
        {"source": "a", "target": "media", "weight": 99.0},
    ]
    assert weighted_concept_density(nodes, edges) == pytest.approx(0.3)


def test_quantile_removes_low_edges_and_busy_chunk_reduces_cooccurrence_weight():
    nodes = [node(value, chunks=("busy",)) for value in ("a", "b", "c", "d", "e")]
    vectors = {value["node_id"]: (1.0, float(index)) for index, value in enumerate(nodes)}
    low = build_topic_edges(nodes, [chunk("busy", "s1", 0)], vectors, semantic_neighbors=1, edge_quantile=0.0)
    high = build_topic_edges(nodes, [chunk("busy", "s1", 0)], vectors, semantic_neighbors=1, edge_quantile=1.0)
    assert len(high["edges"]) < len(low["edges"])

    sparse_nodes = [node("x", chunks=("sparse",)), node("y", chunks=("sparse",))]
    sparse = build_topic_edges(
        sparse_nodes,
        [chunk("sparse", "s1", 0)],
        {"x": (1.0, 0.0), "y": (0.0, 1.0)},
        semantic_neighbors=1,
        edge_quantile=0.0,
    )
    assert sparse["channel_maxima"]["cooccurrence"] > low["channel_maxima"]["cooccurrence"]
