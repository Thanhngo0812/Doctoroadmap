from __future__ import annotations

import math
from collections import defaultdict
from itertools import combinations

def _unit(vector):
    norm = math.sqrt(sum(float(value) ** 2 for value in vector))
    return tuple(float(value) / norm for value in vector) if norm else tuple(0.0 for _ in vector)


def _dot(left, right):
    return sum(a * b for a, b in zip(left, right, strict=True))


def _npmi(total, left_count, right_count, together):
    if not together or not total:
        return 0.0
    joint = together / total
    if joint == 1.0:
        return 1.0
    value = math.log(joint / ((left_count / total) * (right_count / total))) / -math.log(joint)
    return max(0.0, value)


def _context_channel(node_contexts, all_contexts, context_nodes, scale=1.0):
    result = {}
    total = len(all_contexts)
    ids = sorted(node_contexts)
    for left, right in combinations(ids, 2):
        shared = node_contexts[left] & node_contexts[right]
        if not shared:
            continue
        association = _npmi(
            total,
            len(node_contexts[left]),
            len(node_contexts[right]),
            len(shared),
        )
        if not association:
            continue
        penalty = sum(1.0 / max(len(context_nodes[value]) - 1, 1) for value in shared) / len(shared)
        result[(left, right)] = scale * association * penalty
    return result


def _quantile(values, q):
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def build_topic_edges(
    nodes,
    chunks,
    vectors,
    *,
    semantic_neighbors,
    edge_quantile,
):
    if not isinstance(semantic_neighbors, int) or isinstance(semantic_neighbors, bool) or semantic_neighbors < 1:
        raise ValueError("semantic_neighbors phải là số nguyên dương")
    if not 0.0 <= edge_quantile <= 1.0:
        raise ValueError("edge_quantile phải nằm trong [0, 1]")
    node_by_id = {node["node_id"]: node for node in nodes}
    if set(vectors) != set(node_by_id):
        raise ValueError("mỗi node cần đúng một vector mô tả")
    chunk_by_id = {chunk.chunk_id: chunk for chunk in chunks}
    chunk_nodes = defaultdict(set)
    node_chunks = {}
    for node in nodes:
        node_id = node["node_id"]
        provenance = node.get("defining_chunk_ids") or node.get("source_chunk_ids") or []
        node_chunks[node_id] = {value for value in provenance if value in chunk_by_id}
        for chunk_id in node_chunks[node_id]:
            chunk_nodes[chunk_id].add(node_id)
    section_nodes = defaultdict(set)
    node_sections = {}
    for node_id, chunk_ids in node_chunks.items():
        node_sections[node_id] = {chunk_by_id[value].parent_section_id for value in chunk_ids}
        for section_id in node_sections[node_id]:
            section_nodes[section_id].add(node_id)

    cooccurrence = _context_channel(
        node_chunks,
        set(chunk_by_id),
        chunk_nodes,
    )
    for pair, weight in _context_channel(
        node_sections,
        {chunk.parent_section_id for chunk in chunks},
        section_nodes,
        scale=0.5,
    ).items():
        cooccurrence[pair] = cooccurrence.get(pair, 0.0) + weight

    normalized_vectors = {node_id: _unit(vector) for node_id, vector in vectors.items()}
    ids = sorted(node_by_id)
    neighbors = {}
    for node_id in ids:
        ranked = sorted(
            (other for other in ids if other != node_id),
            key=lambda other: (-_dot(normalized_vectors[node_id], normalized_vectors[other]), other),
        )[: min(semantic_neighbors, len(ids) - 1)]
        neighbors[node_id] = {other: rank for rank, other in enumerate(ranked, 1)}
    semantic = {}
    for left, right in combinations(ids, 2):
        if right in neighbors[left] and left in neighbors[right]:
            semantic[(left, right)] = 2.0 / (neighbors[left][right] + neighbors[right][left])

    media = defaultdict(float)
    warnings = []
    media_nodes = {
        node.get("media_id") or node["node_id"]: node["node_id"]
        for node in nodes
        if node.get("media_id")
    }
    for chunk in chunks:
        located_media = {
            media_nodes[ref.image_id]
            for ref in getattr(chunk, "image_refs", [])
            if ref.image_id in media_nodes
        }
        located_media |= {
            node_id
            for node_id in chunk_nodes[chunk.chunk_id]
            if node_by_id[node_id].get("media_id")
        }
        concepts = sorted(
            node_id
            for node_id in chunk_nodes[chunk.chunk_id]
            if not node_by_id[node_id].get("media_id")
        )
        for media_id in sorted(located_media):
            degree = len(concepts)
            if degree >= 5:
                warnings.append(f"media_degree:{media_id}:{degree}")
            penalty = 1.0 / max(degree - 1, 1)
            for concept_id in concepts:
                pair = tuple(sorted((media_id, concept_id)))
                media[pair] += penalty

    raw_channels = {
        "cooccurrence": cooccurrence,
        "semantic": semantic,
        "media": dict(media),
    }
    maxima = {
        name: max(values.values(), default=0.0)
        for name, values in raw_channels.items()
    }
    combined = defaultdict(dict)
    for name, values in raw_channels.items():
        maximum = maxima[name]
        if not maximum:
            continue
        for pair, value in values.items():
            combined[pair][name] = value / maximum
    weighted = {
        pair: sum(channels.values())
        for pair, channels in combined.items()
    }
    cutoff = _quantile(list(weighted.values()), edge_quantile) if weighted else None
    edges = [
        {
            "source": pair[0],
            "target": pair[1],
            "weight": weight,
            "channels": dict(sorted(combined[pair].items())),
        }
        for pair, weight in sorted(weighted.items())
        if cutoff is not None and weight >= cutoff
    ]
    connected = {edge[key] for edge in edges for key in ("source", "target")}
    return {
        "edges": edges,
        "warnings": sorted(set(warnings)),
        "channel_maxima": maxima,
        "cutoff": cutoff,
        "isolated_node_count": len(node_by_id) - len(connected),
    }
