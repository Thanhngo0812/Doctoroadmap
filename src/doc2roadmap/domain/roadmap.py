from __future__ import annotations

from collections import Counter, defaultdict
from heapq import heappop, heappush

from .canonical import digest
from .global_validation import strongly_connected_components


def _coffman_graham(node_ids, edges, width):
    parents = {node_id: set() for node_id in node_ids}
    children = {node_id: set() for node_id in node_ids}
    for edge in edges:
        source, target = edge["source"], edge["target"]
        parents[target].add(source)
        children[source].add(target)

    # Coffman–Graham: label sinks first by their decreasing successor-label vectors.
    remaining = {node_id: len(children[node_id]) for node_id in node_ids}
    ready = [((), node_id) for node_id in node_ids if not remaining[node_id]]
    ready.sort()
    labels = {}
    while ready:
        _, node_id = heappop(ready)
        labels[node_id] = len(labels) + 1
        for parent in parents[node_id]:
            remaining[parent] -= 1
            if not remaining[parent]:
                heappush(ready, (tuple(sorted((labels[child] for child in children[parent]), reverse=True)), parent))
    if len(labels) != len(node_ids):
        raise ValueError("đồ thị requires còn chu trình sau tầng validate")

    stages = []
    layer_of = {}
    longest = {}
    for node_id in sorted(node_ids, key=lambda value: -labels[value]):
        earliest = max((layer_of[parent] + 1 for parent in parents[node_id]), default=0)
        longest[node_id] = 1 + max((longest[parent] for parent in parents[node_id]), default=0)
        layer = earliest
        while layer < len(stages) and len(stages[layer]) >= width:
            layer += 1
        if layer == len(stages):
            stages.append([])
        stages[layer].append(node_id)
        layer_of[node_id] = layer
    return stages, parents, children, max(longest.values(), default=0)


def _balance(stages, parents, children, width):
    layer_of = {node_id: layer for layer, members in enumerate(stages) for node_id in members}
    # One adjacent move per node; both feasibility and population checks are O(V+E).
    for node_id in sorted(layer_of):
        old = layer_of[node_id]
        if len(stages[old]) == 1:
            continue
        earliest = max((layer_of[parent] + 1 for parent in parents[node_id]), default=0)
        latest = min((layer_of[child] - 1 for child in children[node_id]), default=len(stages) - 1)
        choices = [layer for layer in (old - 1, old + 1) if earliest <= layer <= latest and len(stages[layer]) < width]
        if choices:
            new = min(choices, key=lambda layer: (len(stages[layer]), layer))
            if len(stages[new]) < len(stages[old]):
                stages[old].remove(node_id)
                stages[new].append(node_id)
                layer_of[node_id] = new


def _merge_small(stages, children, width, floor):
    unmergeable = []
    index = 0
    while index < len(stages):
        if len(stages[index]) >= floor:
            index += 1
            continue
        choices = []
        for neighbor in (index - 1, index + 1):
            if not 0 <= neighbor < len(stages) or len(stages[index]) + len(stages[neighbor]) > width:
                continue
            left, right = set(stages[index]), set(stages[neighbor])
            if any(child in right for node_id in left for child in children[node_id]):
                continue
            if any(child in left for node_id in right for child in children[node_id]):
                continue
            choices.append(neighbor)
        if not choices:
            unmergeable.append(sorted(stages[index]))
            index += 1
            continue
        neighbor = min(choices, key=lambda value: (len(stages[value]), value))
        stages[neighbor].extend(stages[index])
        stages.pop(index)
        if neighbor < index:
            index = max(neighbor - 1, 0)
    return unmergeable


def _order_stages(stages, children):
    stage_of = {node_id: index for index, members in enumerate(stages) for node_id in members}
    keys = [digest(sorted(members)) for members in stages]
    stage_children = [set() for _ in stages]
    indegree = [0] * len(stages)
    for node_id, targets in children.items():
        source_stage = stage_of[node_id]
        for target in targets:
            target_stage = stage_of[target]
            if target_stage == source_stage:
                raise AssertionError("cạnh requires nằm trong cùng stage")
            if target_stage not in stage_children[source_stage]:
                stage_children[source_stage].add(target_stage)
                indegree[target_stage] += 1
    descendants = [set() for _ in stages]
    for index in reversed(range(len(stages))):
        for child in stage_children[index]:
            descendants[index].add(child)
            descendants[index].update(descendants[child])
    ready = []
    for index, count in enumerate(indegree):
        if not count:
            heappush(ready, (-len(descendants[index]), keys[index], index))
    ordered = []
    while ready:
        _, _, index = heappop(ready)
        ordered.append(stages[index])
        for child in stage_children[index]:
            indegree[child] -= 1
            if not indegree[child]:
                heappush(ready, (-len(descendants[child]), keys[child], child))
    if len(ordered) != len(stages):
        raise AssertionError("stage graph còn chu trình")
    return ordered


def reviewed_sessions(node_ids, main_sessions, completed_secondary_pairs, suspected_pairs):
    """Phiên A8 nào đã xét từng khái niệm: phiên pass chính nhận nó làm đích, hoặc cặp pass phụ có nó ở một đầu."""
    node_ids = set(node_ids)
    reviewed = defaultdict(list)
    for session in main_sessions:
        for node_id in session.get("target_node_ids", []):
            if node_id in node_ids:
                reviewed[node_id].append(session["session_id"])
    pair_by_id = {row["pair_id"]: row for row in suspected_pairs}
    for pair_id in completed_secondary_pairs:
        pair = pair_by_id.get(pair_id)
        if pair:
            for node_id in (pair["left"], pair["right"]):
                if node_id in node_ids:
                    reviewed[node_id].append("secondary_" + pair_id)
    return reviewed


def build_roadmap(
    nodes,
    requires_edges,
    main_sessions,
    completed_secondary_pairs,
    suspected_pairs,
    *,
    stage_cap,
    quality_gate,
    stage_floor=3,
):
    if type(stage_cap) is not int or stage_cap < 1:
        raise ValueError("stage_cap phải là số nguyên dương")
    if type(stage_floor) is not int or not 1 <= stage_floor <= stage_cap:
        raise ValueError("stage_floor phải nằm trong [1, stage_cap]")
    learnable = [dict(node) for node in nodes if node.get("learnable")]
    node_by_id = {node["node_id"]: node for node in learnable}
    filtered_edges = [
        edge for edge in requires_edges
        if edge.get("edge_type") == "requires" and edge.get("source") in node_by_id and edge.get("target") in node_by_id
    ]
    components = strongly_connected_components(set(node_by_id), filtered_edges)
    cyclic = [component for component in components if len(component) > 1]
    if cyclic:
        raise ValueError(f"tầng validate còn SCC requires: {cyclic[0]}")
    if any(edge["source"] == edge["target"] for edge in filtered_edges):
        raise ValueError("tầng validate còn SCC requires tự nối")
    stages, parents, children, longest_path = _coffman_graham(set(node_by_id), filtered_edges, stage_cap)
    _balance(stages, parents, children, stage_cap)
    unmergeable = _merge_small(stages, children, stage_cap, stage_floor)
    if len(stages) < max(longest_path, (len(learnable) + stage_cap - 1) // stage_cap):
        raise AssertionError("số stage nhỏ hơn cận dưới xếp tầng")
    stages = _order_stages(stages, children)

    reviewed = reviewed_sessions(node_by_id, main_sessions, completed_secondary_pairs, suspected_pairs)
    incoming = {edge["target"] for edge in filtered_edges}
    coverage_flags = []
    result_stages = []
    for layer, members in enumerate(stages, 1):
        members.sort(key=lambda node_id: (node_by_id[node_id].get("cluster_id", ""), node_id))
        cluster_id = min(Counter(node_by_id[node_id].get("cluster_id", "") for node_id in members).items(), key=lambda item: (-item[1], item[0]))[0]
        title = min(
            (node_by_id[node_id].get("name", node_id) for node_id in members
             if node_by_id[node_id].get("cluster_id", "") == cluster_id),
            key=lambda name: (len(name.split()), len(name), name.casefold()),
        )
        stage_id = "stage_" + digest([layer, members])[:24]
        result_stages.append({
            "stage_id": stage_id,
            "layer": layer,
            "cluster_id": cluster_id,
            "title": title,
            "node_ids": members,
            "first_order_index": min(node_by_id[node_id].get("first_order_index", 0) for node_id in members),
        })
        for node_id in members:
            node = node_by_id[node_id]
            sessions = sorted(set(reviewed[node_id]))
            node["reviewed_session_ids"] = sessions
            if not sessions:
                node["coverage_status"] = "unreviewed"
                coverage_flags.append({"kind": "unreviewed_learnable_node", "node_id": node_id})
            elif node_id not in incoming:
                node["coverage_status"] = "reviewed_no_prerequisite"
            else:
                node["coverage_status"] = "reviewed_with_prerequisite"
            node["layer"] = layer
            node["stage_id"] = stage_id
    stage_order = {stage["stage_id"]: index for index, stage in enumerate(result_stages)}
    chunk_stages = defaultdict(set)
    for node in learnable:
        for chunk_id in node.get("defining_chunk_ids", []):
            chunk_stages[chunk_id].add(node["stage_id"])
    chunk_stage_map = {}
    for chunk_id, stage_ids in sorted(chunk_stages.items()):
        ordered = sorted(stage_ids, key=lambda stage_id: stage_order[stage_id])
        chunk_stage_map[chunk_id] = {"stage_id": ordered[0], "all_stage_ids": ordered}
    return {
        "mode": "requires",
        "nodes": learnable,
        "stages": result_stages,
        "chunk_stage_map": chunk_stage_map,
        "coverage_flags": coverage_flags,
        "contracted_components": [],
        "unmergeable_small_stages": unmergeable,
        "longest_path": longest_path,
    }
