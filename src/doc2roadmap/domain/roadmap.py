from __future__ import annotations

from collections import defaultdict

from .canonical import digest
from .global_validation import strongly_connected_components


def _kahn(node_ids, edges):
    indegree = {node_id: 0 for node_id in node_ids}
    adjacency = defaultdict(list)
    for edge in edges:
        if edge.get("edge_type") != "requires" or edge["source"] not in indegree or edge["target"] not in indegree:
            continue
        adjacency[edge["source"]].append(edge["target"])
        indegree[edge["target"]] += 1
    roots = sorted(node_id for node_id, value in indegree.items() if value == 0)
    queue = roots
    layers, visited = {node_id: 1 for node_id in roots}, 0
    while queue:
        node_id = queue.pop(0)
        visited += 1
        for target in sorted(adjacency[node_id]):
            layers[target] = max(layers.get(target, 1), layers[node_id] + 1)
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
                queue.sort()
    if visited != len(node_ids):
        raise ValueError("đồ thị requires còn chu trình sau tầng validate")
    return layers


def _requires_components(node_ids, edges):
    components = strongly_connected_components(node_ids, edges)
    oversized = [component for component in components if len(component) > 2]
    if oversized:
        raise ValueError(f"tầng validate còn SCC requires lớn hơn hai node: {oversized[0]}")
    return components


def _contracted_layers(components, edges):
    component_by_node = {
        node_id: tuple(component)
        for component in components
        for node_id in component
    }
    contracted_edges = {
        (component_by_node[edge["source"]], component_by_node[edge["target"]])
        for edge in edges
        if component_by_node[edge["source"]] != component_by_node[edge["target"]]
    }
    component_layers = _kahn(
        set(component_by_node.values()),
        [
            {"source": source, "target": target, "edge_type": "requires"}
            for source, target in sorted(contracted_edges)
        ],
    )
    return {
        node_id: component_layers[component]
        for node_id, component in component_by_node.items()
    }


def _fallback_layers(components, node_by_id, stage_cap):
    ordered = sorted(
        components,
        key=lambda component: min(
            (node_by_id[node_id].get("first_order_index", 0), node_id)
            for node_id in component
        ),
    )
    layers, layer, count = {}, 1, 0
    for component in ordered:
        if count and count + len(component) > stage_cap:
            layer, count = layer + 1, 0
        layers.update({node_id: layer for node_id in component})
        count += len(component)
    return layers


def build_roadmap(
    nodes,
    requires_edges,
    main_sessions,
    completed_secondary_pairs,
    suspected_pairs,
    *,
    stage_cap,
    quality_gate,
):
    if type(stage_cap) is not int or not 5 <= stage_cap <= 8:
        raise ValueError("stage_cap phải nằm trong [5, 8]")
    learnable = [dict(node) for node in nodes if node.get("learnable")]
    node_by_id = {node["node_id"]: node for node in learnable}
    filtered_edges = [
        edge for edge in requires_edges
        if edge.get("edge_type") == "requires" and edge.get("source") in node_by_id and edge.get("target") in node_by_id
    ]
    components = _requires_components(set(node_by_id), filtered_edges)
    if quality_gate.get("passed", False):
        layers = _contracted_layers(components, filtered_edges)
        mode = "requires"
    else:
        layers = _fallback_layers(components, node_by_id, stage_cap)
        mode = "document_order_fallback"

    reviewed = defaultdict(list)
    for session in main_sessions:
        for node_id in session.get("target_node_ids", []):
            if node_id in node_by_id:
                reviewed[node_id].append(session["session_id"])
    pair_by_id = {row["pair_id"]: row for row in suspected_pairs}
    for pair_id in completed_secondary_pairs:
        pair = pair_by_id.get(pair_id)
        if pair:
            for node_id in (pair["left"], pair["right"]):
                if node_id in node_by_id:
                    reviewed[node_id].append("secondary_" + pair_id)
    incoming = {edge["target"] for edge in filtered_edges}
    coverage_flags = []
    for node in learnable:
        node_id = node["node_id"]
        sessions = sorted(set(reviewed[node_id]))
        node["reviewed_session_ids"] = sessions
        if not sessions:
            node["coverage_status"] = "unreviewed"
            coverage_flags.append({"kind": "unreviewed_learnable_node", "node_id": node_id})
        elif node_id not in incoming:
            node["coverage_status"] = "reviewed_no_prerequisite"
        else:
            node["coverage_status"] = "reviewed_with_prerequisite"
        node["layer"] = layers[node_id]

    grouped = defaultdict(list)
    for node in learnable:
        grouped[node["layer"], node["cluster_id"]].append(node)
    stages = []
    for (layer, cluster_id), members in sorted(grouped.items()):
        members.sort(key=lambda node: (node.get("first_order_index", 0), node["node_id"]))
        for part, start in enumerate(range(0, len(members), stage_cap)):
            batch = members[start : start + stage_cap]
            stage_id = "stage_" + digest([layer, cluster_id, part, [node["node_id"] for node in batch]])[:24]
            stages.append({
                "stage_id": stage_id,
                "layer": layer,
                "cluster_id": cluster_id,
                "part": part,
                "node_ids": [node["node_id"] for node in batch],
                "first_order_index": min(node.get("first_order_index", 0) for node in batch),
            })
            for node in batch:
                node["stage_id"] = stage_id
    stages.sort(key=lambda row: (row["layer"], row["first_order_index"], row["cluster_id"], row["part"]))
    stage_order = {stage["stage_id"]: index for index, stage in enumerate(stages)}
    chunk_stages = defaultdict(set)
    for node in learnable:
        for chunk_id in node.get("defining_chunk_ids", []):
            chunk_stages[chunk_id].add(node["stage_id"])
    chunk_stage_map = {}
    for chunk_id, stage_ids in sorted(chunk_stages.items()):
        ordered = sorted(stage_ids, key=lambda stage_id: stage_order[stage_id])
        chunk_stage_map[chunk_id] = {"stage_id": ordered[0], "all_stage_ids": ordered}
    return {
        "mode": mode,
        "nodes": learnable,
        "stages": stages,
        "chunk_stage_map": chunk_stage_map,
        "coverage_flags": coverage_flags,
        "contracted_components": [component for component in components if len(component) == 2],
    }
