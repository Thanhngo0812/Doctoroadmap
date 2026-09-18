from __future__ import annotations

import math

import igraph
import leidenalg

from doc2roadmap.domain.canonical import digest


def _unit(vector):
    norm = math.sqrt(sum(float(value) ** 2 for value in vector))
    return tuple(float(value) / norm for value in vector) if norm else tuple(0.0 for _ in vector)


def _dot(left, right):
    return sum(a * b for a, b in zip(left, right, strict=True))


def weighted_concept_density(nodes, edges):
    concept_ids = {node["node_id"] for node in nodes if node.get("learnable")}
    pair_count = len(concept_ids) * (len(concept_ids) - 1) / 2
    if not pair_count:
        return 0.0
    return sum(
        float(edge["weight"])
        for edge in edges
        if edge["source"] in concept_ids and edge["target"] in concept_ids
    ) / pair_count


def _merge_tiny_groups(groups, node_by_id, edge_weights, normalized_vectors, concept_cap):
    groups = {label: set(members) for label, members in groups.items()}

    def concept_members(members):
        return {value for value in members if node_by_id[value].get("learnable")}

    def centroid(members):
        values = [normalized_vectors[value] for value in sorted(members)]
        return _unit(tuple(sum(column) / len(values) for column in zip(*values, strict=True))) if values else ()

    merge_count, affected = 0, set()
    while True:
        changed = False
        tiny = sorted(
            (label for label, members in groups.items() if 1 <= len(concept_members(members)) <= 2),
            key=lambda label: (
                min(node_by_id[value].get("first_order_index", 0) for value in groups[label]),
                tuple(sorted(groups[label])),
            ),
        )
        for source in tiny:
            candidates = [
                target for target in groups
                if target != source
                and len(concept_members(groups[source])) + len(concept_members(groups[target])) <= concept_cap
            ]
            if not candidates:
                continue
            source_centroid = centroid(groups[source])

            def score(target):
                cross_weight = sum(
                    edge_weights.get(frozenset((left, right)), 0.0)
                    for left in groups[source]
                    for right in groups[target]
                )
                similarity = _dot(source_centroid, centroid(groups[target])) if source_centroid else 0.0
                first = min(node_by_id[value].get("first_order_index", 0) for value in groups[target])
                return cross_weight, similarity, -first

            target = max(sorted(candidates, key=lambda value: tuple(sorted(groups[value]))), key=score)
            affected.update(concept_members(groups[source]) | concept_members(groups[target]))
            groups[target] |= groups.pop(source)
            merge_count += 1
            changed = True
            break
        if not changed:
            return groups, merge_count, affected


def cluster_nodes(nodes, edges, vectors, *, resolution, seed, concept_cap):
    if resolution <= 0:
        raise ValueError("resolution phải dương")
    if not isinstance(concept_cap, int) or isinstance(concept_cap, bool) or concept_cap < 1:
        raise ValueError("concept_cap phải là số nguyên dương")
    ids = sorted(node["node_id"] for node in nodes)
    if len(ids) != len(set(ids)):
        raise ValueError("node_id bị trùng")
    if not ids:
        return {}, {
            "raw_cluster_count": 0,
            "raw_tiny_cluster_count": 0,
            "raw_cluster_concept_sizes": [],
            "raw_cluster_node_sizes": [],
            "merge_count": 0,
            "merge_affected_concept_count": 0,
            "merge_affected_concept_ratio": 0.0,
        }
    node_by_id = {node["node_id"]: node for node in nodes}
    index = {node_id: position for position, node_id in enumerate(ids)}
    ordered_edges = sorted(edges, key=lambda edge: (edge["source"], edge["target"]))
    graph = igraph.Graph(
        n=len(ids),
        edges=[(index[edge["source"]], index[edge["target"]]) for edge in ordered_edges],
        directed=False,
    )
    weights = [float(edge["weight"]) for edge in ordered_edges]
    sizes = [1 if node_by_id[node_id].get("learnable") else 0 for node_id in ids]
    partition = leidenalg.CPMVertexPartition(
        graph,
        weights=weights or None,
        node_sizes=sizes,
        resolution_parameter=float(resolution),
    )
    optimiser = leidenalg.Optimiser()
    optimiser.max_comm_size = concept_cap
    optimiser.community_constraint_enforcement = 1e12
    optimiser.set_rng_seed(int(seed))
    optimiser.optimise_partition(partition, n_iterations=-1)
    raw_groups = {
        label: {ids[position] for position, value in enumerate(partition.membership) if value == label}
        for label in sorted(set(partition.membership))
    }
    edge_weights = {frozenset((edge["source"], edge["target"])): float(edge["weight"]) for edge in ordered_edges}
    normalized_vectors = {node_id: _unit(vectors[node_id]) for node_id in ids}

    def concept_count(members):
        return sum(bool(node_by_id[value].get("learnable")) for value in members)

    groups, merge_count, affected = _merge_tiny_groups(
        raw_groups,
        node_by_id,
        edge_weights,
        normalized_vectors,
        concept_cap,
    )
    result = {}
    for members in groups.values():
        cluster_id = "cluster_" + digest(sorted(members))[:24]
        for node_id in members:
            result[node_id] = cluster_id
    if set(result) != set(ids):
        raise AssertionError("Leiden làm rơi node")
    if any(
        concept_count({node_id for node_id, value in result.items() if value == cluster_id}) > concept_cap
        for cluster_id in set(result.values())
    ):
        raise AssertionError("cụm vượt trần khái niệm")
    raw_concept_sizes = sorted(concept_count(members) for members in raw_groups.values())
    concept_total = sum(bool(node.get("learnable")) for node in nodes)
    return result, {
        "raw_cluster_count": len(raw_groups),
        "raw_tiny_cluster_count": sum(1 <= size <= 2 for size in raw_concept_sizes),
        "raw_cluster_concept_sizes": raw_concept_sizes,
        "raw_cluster_node_sizes": sorted(len(members) for members in raw_groups.values()),
        "merge_count": merge_count,
        "merge_affected_concept_count": len(affected),
        "merge_affected_concept_ratio": len(affected) / concept_total if concept_total else 0.0,
    }
