"""Quy id cạnh và đích vàng qua lịch sử canonical; không sửa đầu vào."""
from __future__ import annotations


def remap_gold(edges, targets, redirects, graph_ids):
    edges, targets, graph_ids = set(edges), set(targets), set(graph_ids)
    resolved, unresolved = {}, []
    for original in sorted(targets | {node_id for edge in edges for node_id in edge}):
        current, seen = original, set()
        while current in redirects:
            if current in seen:
                raise ValueError(f"bảng chuyển hướng có vòng lặp khi quy {original}: {current}")
            seen.add(current)
            current = redirects[current]
        if current not in graph_ids:
            unresolved.append(original)
        else:
            resolved[original] = current
    mapped = {(resolved[a], resolved[b]) for a, b in edges if a in resolved and b in resolved}
    return {
        "edges": {(a, b) for a, b in mapped if a != b},
        "targets": {resolved[target] for target in targets if target in resolved},
        "dropped_gold_edges": sum(a in resolved and b in resolved and resolved[a] == resolved[b]
                                  for a, b in edges),
        "unresolved_concepts": unresolved,
    }
