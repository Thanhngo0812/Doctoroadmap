from __future__ import annotations

import math
import re
from collections import defaultdict, deque


EVIDENCE_RANK = {"noi_ro": 3, "trong_dinh_nghia": 2, "mach_trinh_bay": 1}
ORDER_RANK = {"thuận": 2, "cùng chunk": 1, "ngược": 0}
NON_TEACHING_ROLES = {"de_cuong", "mo_dau", "hanh_chinh", "cuoi_sach"}


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


def _edge_weights(edges):
    count = len(edges)
    sources = [max(0, int(edge.get("independent_source_count", len(edge.get("origins", [])) or 1))) for edge in edges]
    max_sources = max(sources, default=1)
    order_base = count * max_sources + 1
    evidence_base = count * (2 * order_base + max_sources) + 1
    return [
        EVIDENCE_RANK.get(edge.get("evidence_kind"), 0) * evidence_base
        + ORDER_RANK.get(edge.get("order_relation"), 0) * order_base
        + source_count
        for edge, source_count in zip(edges, sources, strict=True)
    ]


def _simple_cycles(component, edges, budget):
    adjacency = defaultdict(list)
    for index, edge in enumerate(edges):
        adjacency[edge["source"]].append((edge["target"], index))
    for values in adjacency.values():
        values.sort(key=lambda value: (value[0], _edge_key(edges[value[1]])))
    cycles = []
    for start in sorted(component):
        def visit(node_id, visited, path):
            for target, index in adjacency[node_id]:
                if target == start:
                    cycles.append(tuple(path + [index]))
                    if len(cycles) > budget:
                        return True
                elif target > start and target not in visited:
                    if visit(target, visited | {target}, path + [index]):
                        return True
            return False
        if visit(start, {start}, []):
            break
    return cycles


class _CycleWorkLimit(Exception):
    pass


def _minimum_cycle_cover(cycles, weights, edges, work_budget):
    coverage = [0] * len(edges)
    for cycle_index, cycle in enumerate(cycles):
        for edge_index in cycle:
            coverage[edge_index] |= 1 << cycle_index
    edge_keys = [_edge_key(edge) for edge in edges]

    memo = {}
    work = 0

    def solve(uncovered):
        nonlocal work
        work += 1
        if work > work_budget:
            raise _CycleWorkLimit
        if not uncovered:
            return 0, ()
        if uncovered in memo:
            return memo[uncovered]
        cycle_index = min(
            (index for index in range(len(cycles)) if uncovered & (1 << index)),
            key=lambda index: (len(cycles[index]), cycles[index]),
        )
        best = None
        for edge_index in sorted(cycles[cycle_index], key=lambda index: (weights[index], edge_keys[index])):
            cost, selected = solve(uncovered & ~coverage[edge_index])
            candidate = (
                cost + weights[edge_index],
                tuple(sorted((*selected, edge_index), key=lambda index: edge_keys[index])),
            )
            if best is None or (candidate[0], tuple(edge_keys[index] for index in candidate[1])) < (
                best[0], tuple(edge_keys[index] for index in best[1])
            ):
                best = candidate
        memo[uncovered] = best
        return best

    return list(solve((1 << len(cycles)) - 1)[1])


def _feedback_edges(component, internal, *, cycle_budget=1000, work_budget=10000):
    weights = _edge_weights(internal)
    weight_by_id = {id(edge): weight for edge, weight in zip(internal, weights, strict=True)}
    cycles = _simple_cycles(component, internal, cycle_budget)
    work_limited = False
    if len(cycles) <= cycle_budget:
        try:
            removed_indexes = _minimum_cycle_cover(cycles, weights, internal, work_budget)
        except _CycleWorkLimit:
            work_limited = True
        else:
            return [internal[index] for index in removed_indexes], "exact", len(cycles), sum(weights[index] for index in removed_indexes)
    if len(cycles) > cycle_budget or work_limited:
        remaining = set(component)
        left, right = [], []

        def score(edge):
            return weight_by_id[id(edge)]

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
        return removed, "approximate", len(cycles), sum(weight_by_id[id(edge)] for edge in removed)
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


def apply_resolved_nodes(nodes, flags, node_vectors, *, assign_clusters=True):
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
        for cluster_id in sorted({value["cluster_id"] for value in result if "cluster_id" in value}):
            members = [vectors[value["node_id"]] for value in result if value.get("cluster_id") == cluster_id and value["node_id"] in vectors]
            if members:
                centroids[cluster_id] = _unit(tuple(sum(column) / len(members) for column in zip(*members, strict=True)))
        if not centroids:
            continue
        if assign_clusters:
            cluster_id = max(
                sorted(centroids),
                key=lambda value: sum(left * right for left, right in zip(candidate, centroids[value], strict=True)),
            )
            resolved = {**node, "cluster_id": cluster_id}
        else:
            resolved = {key: value for key, value in node.items() if key != "cluster_id"}
        result.append(resolved)
        vectors[resolved["node_id"]] = candidate
        if assign_clusters:
            log.append({"action": "incremental_cluster_assignment", "node_id": resolved["node_id"], "cluster_id": cluster_id})
    return result, {key: list(value) for key, value in vectors.items()}, log


def validate_graph_rules(nodes, requires_edges, open_edges, *, type_aliases=None, cycle_budget=1000, work_budget=10000, chunk_roles=None):
    learnable = {node["node_id"] for node in nodes if node.get("learnable")}
    candidates = [
        dict(edge)
        for edge in requires_edges
        if edge.get("edge_type") == "requires" and edge.get("source") in learnable and edge.get("target") in learnable
    ]
    requires, soft_edges, region_flags = [], [], []
    for edge in candidates:
        roles = [chunk_roles.get(chunk_id) for chunk_id in edge.get("chunk_ids", [])] if chunk_roles else []
        if roles and all(role in NON_TEACHING_ROLES for role in roles):
            region_flags.append({"kind": "requires_non_teaching_evidence", "edge": edge,
                                 "reason": "all cited chunks are non-teaching regions"})
        elif roles and all(role == "bai_tap" for role in roles):
            soft_edges.append({**edge, "soft": True})
        else:
            requires.append(edge)
    requires.sort(key=_edge_key)
    soft_edges.sort(key=_edge_key)
    normalized_open, registry, type_flags = _type_registry(open_edges, type_aliases or {})
    two_way_flags, removed, cycle_resolution = [], [], []
    by_pair = {(edge["source"], edge["target"]) for edge in requires}
    reciprocal = {
        frozenset((source, target))
        for source, target in by_pair
        if source != target and (target, source) in by_pair
    }
    for pair in sorted(reciprocal, key=lambda value: sorted(value)):
        two_way_flags.append({
            "kind": "suspected_relation_type_error",
            "node_ids": sorted(pair),
            "reason": "reciprocal_requires_may_have_wrong_relation_type; review both directions",
            "edges": [dict(edge) for edge in requires if frozenset((edge["source"], edge["target"])) == pair],
        })
    requires = [edge for edge in requires if frozenset((edge["source"], edge["target"])) not in reciprocal]
    for component in strongly_connected_components(learnable, requires):
        if len(component) < 2:
            continue
        internal = [edge for edge in requires if edge["source"] in component and edge["target"] in component]
        component_removed, method, cycle_count, removed_weight = _feedback_edges(
            component, internal, cycle_budget=cycle_budget, work_budget=work_budget
        )
        removed.extend(component_removed)
        cycle_resolution.append({
            "node_ids": component,
            "internal_edge_count": len(internal),
            "removed_edge_count": len(component_removed),
            "method": method,
            "simple_cycle_count": cycle_count,
            "simple_cycle_count_capped": cycle_count > cycle_budget,
            "work_budget_exceeded": method == "approximate" and cycle_count <= cycle_budget,
            "removed_weight": removed_weight,
        })
    removed_keys = {_edge_key(edge) for edge in removed}
    kept = [edge for edge in requires if _edge_key(edge) not in removed_keys]
    if not _acyclic(learnable, kept):
        raise ValueError("A9 cycle removal must precede redundancy marking")
    marked = []
    for index, edge in enumerate(kept):
        alternate = _alternate_path(kept, edge["source"], edge["target"], index)
        marked.append({**{key: value for key, value in edge.items() if key != "redundant_via"}, **({"redundant_via": alternate} if alternate else {})})
    incident = {edge["source"] for edge in marked} | {edge["target"] for edge in marked}
    isolated = len(learnable - incident)
    ratio = isolated / len(learnable) if learnable else 0.0
    nonredundant = sum("redundant_via" not in edge for edge in marked)
    density = nonredundant / len(learnable) if learnable else 0.0
    passed = density >= 0.15 and ratio <= 0.85
    quality_gate = {
        "passed": passed,
        "requires_edge_count": len(marked),
        "nonredundant_requires_edge_count": nonredundant,
        "learnable_node_count": len(learnable),
        "isolated_learnable_count": isolated,
        "isolated_ratio": ratio,
        "nonredundant_edges_per_learnable": density,
        "fallback": None if passed else "document_order",
        "warning": None if passed else "A9 structural consistency gate closed: prerequisite graph is too sparse or isolated; A10 will use document order",
    }
    return {
        "requires_edges": sorted([*marked, *soft_edges], key=_edge_key),
        "region_flags": region_flags,
        "removed_cycle_edges": sorted((dict(edge) for edge in removed), key=_edge_key),
        "cycle_resolution": cycle_resolution,
        "two_way_flags": two_way_flags,
        "quality_gate": quality_gate,
        "open_edges": normalized_open,
        "type_registry": registry,
        "type_flags": type_flags,
    }
