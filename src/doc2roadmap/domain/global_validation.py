from __future__ import annotations

import math
import re
from collections import defaultdict, deque
from itertools import combinations


EVIDENCE_RANK = {"noi_ro": 3, "trong_dinh_nghia": 2, "mach_trinh_bay": 1}
ORDER_RANK = {"thuận": 2, "cùng chunk": 1, "ngược": 0}


def strongly_connected_components(node_ids, edges):
    adjacency = defaultdict(list)
    for edge in edges:
        adjacency[edge["source"]].append(edge["target"])
    for values in adjacency.values():
        values.sort()
    index = 0
    stack, on_stack = [], set()
    indices, low, result = {}, {}, []

    def visit(node_id):
        nonlocal index
        indices[node_id] = low[node_id] = index
        index += 1
        stack.append(node_id)
        on_stack.add(node_id)
        for target in adjacency[node_id]:
            if target not in indices:
                visit(target)
                low[node_id] = min(low[node_id], low[target])
            elif target in on_stack:
                low[node_id] = min(low[node_id], indices[target])
        if low[node_id] == indices[node_id]:
            component = []
            while True:
                value = stack.pop()
                on_stack.remove(value)
                component.append(value)
                if value == node_id:
                    break
            result.append(sorted(component))

    for node_id in sorted(node_ids):
        if node_id not in indices:
            visit(node_id)
    return result


def _acyclic(node_ids, edges):
    indegree = {node_id: 0 for node_id in node_ids}
    adjacency = defaultdict(list)
    for edge in edges:
        adjacency[edge["source"]].append(edge["target"])
        indegree[edge["target"]] += 1
    queue = deque(sorted(node_id for node_id, degree in indegree.items() if degree == 0))
    visited = 0
    while queue:
        node_id = queue.popleft()
        visited += 1
        for target in sorted(adjacency[node_id]):
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    return visited == len(indegree)


def _edge_key(edge):
    return edge["source"], edge["target"], edge.get("session_id", ""), edge.get("operation_index", 0)


def _keep_priority(edge):
    return (
        EVIDENCE_RANK.get(edge.get("evidence_kind"), 0),
        ORDER_RANK.get(edge.get("order_relation"), 0),
        int(edge.get("independent_source_count", len(edge.get("origins", [])) or 1)),
        float(edge.get("confidence", 0.0)),
    )


def _feedback_edges(component, internal, *, exhaustive_limit=16):
    if len(internal) > exhaustive_limit:
        remaining = set(component)
        left, right = [], []

        def score(edge):
            evidence, order, sources, confidence = _keep_priority(edge)
            return evidence * 1_000_000 + order * 100_000 + sources * 1_000 + confidence

        while remaining:
            active = [
                edge for edge in internal
                if edge["source"] in remaining and edge["target"] in remaining
            ]
            outgoing = {node_id: [edge for edge in active if edge["source"] == node_id] for node_id in remaining}
            incoming = {node_id: [edge for edge in active if edge["target"] == node_id] for node_id in remaining}
            sinks = sorted(node_id for node_id in remaining if not outgoing[node_id])
            if sinks:
                for node_id in sinks:
                    remaining.remove(node_id)
                    right.insert(0, node_id)
                continue
            sources = sorted(node_id for node_id in remaining if not incoming[node_id])
            if sources:
                for node_id in sources:
                    remaining.remove(node_id)
                    left.append(node_id)
                continue
            node_id = max(
                sorted(remaining),
                key=lambda value: (
                    sum(score(edge) for edge in outgoing[value])
                    - sum(score(edge) for edge in incoming[value]),
                    value,
                ),
            )
            remaining.remove(node_id)
            left.append(node_id)
        position = {node_id: index for index, node_id in enumerate([*left, *right])}
        removed = [edge for edge in internal if position[edge["source"]] >= position[edge["target"]]]
        return removed, "eades_priority"
    indexed = list(enumerate(internal))
    candidates = []
    for count in range(1, len(internal) + 1):
        for removed in combinations(indexed, count):
            removed_indexes = {index for index, _ in removed}
            kept = [edge for index, edge in indexed if index not in removed_indexes]
            if _acyclic(component, kept):
                removed_edges = [edge for _, edge in removed]
                candidates.append(removed_edges)
        if candidates:
            break
    return min(
        candidates,
        key=lambda values: (
            sorted(_keep_priority(edge) for edge in values),
            sorted(_edge_key(edge) for edge in values),
        ),
    ), "exhaustive"


def _alternate_path(edges, source, target, excluded_index):
    adjacency = defaultdict(list)
    for index, edge in enumerate(edges):
        if index != excluded_index:
            adjacency[edge["source"]].append(edge["target"])
    queue = deque([(source, [source])])
    seen = {source}
    while queue:
        node_id, path = queue.popleft()
        for next_id in sorted(adjacency[node_id]):
            if next_id == target:
                return path + [next_id]
            if next_id not in seen:
                seen.add(next_id)
                queue.append((next_id, path + [next_id]))
    return None


def _type_name(value):
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", value.casefold())).strip("_")


def _type_registry(open_edges, type_aliases):
    normalized = []
    grouped = defaultdict(lambda: {"count": 0, "original_names": set()})
    flags = []
    aliases = {_type_name(key): _type_name(value) for key, value in type_aliases.items()}
    for edge in open_edges:
        original = edge.get("edge_type", "")
        key = _type_name(original)
        target = aliases.get(key, key)
        if target == "requires" and key != "requires":
            canonical = key
            flags.append({"kind": "suspected_requires_synonym", "edge_type": original})
        else:
            canonical = target[3:] if target.startswith("is_") else target
        normalized.append({**edge, "edge_type": canonical})
        grouped[canonical]["count"] += 1
        grouped[canonical]["original_names"].add(original)
    registry = {
        key: {"count": value["count"], "original_names": sorted(value["original_names"])}
        for key, value in sorted(grouped.items())
    }
    flags.extend(
        {"kind": "singleton_edge_type", "edge_type": key}
        for key, value in registry.items()
        if value["count"] == 1 and key != "requires"
    )
    return normalized, registry, flags


def _unit(vector):
    norm = math.sqrt(sum(float(value) ** 2 for value in vector))
    return tuple(float(value) / norm for value in vector) if norm else tuple(0.0 for _ in vector)


def apply_resolved_nodes(nodes, flags, node_vectors):
    result = [dict(node) for node in nodes]
    vectors = {key: _unit(value) for key, value in node_vectors.items()}
    log = []
    for flag in flags:
        node = flag.get("resolved_node") if isinstance(flag, dict) else None
        vector = flag.get("semantic_vector") if isinstance(flag, dict) else None
        if not isinstance(node, dict) or not vector or node.get("node_id") in {value["node_id"] for value in result}:
            continue
        candidate = _unit(vector)
        centroids = {}
        for cluster_id in sorted({value["cluster_id"] for value in result}):
            members = [vectors[value["node_id"]] for value in result if value["cluster_id"] == cluster_id and value["node_id"] in vectors]
            if members:
                centroids[cluster_id] = _unit(tuple(sum(column) / len(members) for column in zip(*members, strict=True)))
        if not centroids:
            continue
        cluster_id = max(
            sorted(centroids),
            key=lambda value: sum(left * right for left, right in zip(candidate, centroids[value], strict=True)),
        )
        resolved = {**node, "cluster_id": cluster_id}
        result.append(resolved)
        vectors[resolved["node_id"]] = candidate
        log.append({"action": "incremental_cluster_assignment", "node_id": resolved["node_id"], "cluster_id": cluster_id})
    return result, {key: list(value) for key, value in vectors.items()}, log


def validate_graph_rules(nodes, requires_edges, open_edges, *, type_aliases=None):
    learnable = {node["node_id"] for node in nodes if node.get("learnable")}
    requires = [
        dict(edge)
        for edge in requires_edges
        if edge.get("edge_type") == "requires" and edge.get("source") in learnable and edge.get("target") in learnable
    ]
    requires.sort(key=_edge_key)
    two_way_flags, removed, cycle_resolution = [], [], []
    for component in strongly_connected_components(learnable, requires):
        if len(component) < 2:
            continue
        internal = [edge for edge in requires if edge["source"] in component and edge["target"] in component]
        if len(component) == 2 and {(edge["source"], edge["target"]) for edge in internal} >= {
            (component[0], component[1]), (component[1], component[0])
        }:
            two_way_flags.append({
                "kind": "two_way_requires",
                "node_ids": component,
                "reason": "two_edge_requires_cycle",
                "edges": sorted((dict(edge) for edge in internal), key=_edge_key),
            })
            continue
        component_removed, method = _feedback_edges(component, internal)
        removed.extend(component_removed)
        cycle_resolution.append({
            "node_ids": component,
            "internal_edge_count": len(internal),
            "removed_edge_count": len(component_removed),
            "method": method,
        })
    removed_keys = {_edge_key(edge) for edge in removed}
    kept = [edge for edge in requires if _edge_key(edge) not in removed_keys]
    marked = []
    for index, edge in enumerate(kept):
        alternate = _alternate_path(kept, edge["source"], edge["target"], index)
        marked.append({**edge, **({"redundant_via": alternate} if alternate else {})})
    incident = {edge["source"] for edge in marked} | {edge["target"] for edge in marked}
    isolated = len(learnable - incident)
    ratio = isolated / len(learnable) if learnable else 0.0
    passed = len(marked) >= 0.5 * len(learnable) and ratio <= 0.6
    quality_gate = {
        "passed": passed,
        "requires_edge_count": len(marked),
        "learnable_node_count": len(learnable),
        "isolated_learnable_count": isolated,
        "isolated_ratio": ratio,
        "fallback": None if passed else "document_order",
    }
    normalized_open, registry, type_flags = _type_registry(open_edges, type_aliases or {})
    return {
        "requires_edges": marked,
        "removed_cycle_edges": sorted((dict(edge) for edge in removed), key=_edge_key),
        "cycle_resolution": cycle_resolution,
        "two_way_flags": two_way_flags,
        "quality_gate": quality_gate,
        "open_edges": normalized_open,
        "type_registry": registry,
        "type_flags": type_flags,
    }
