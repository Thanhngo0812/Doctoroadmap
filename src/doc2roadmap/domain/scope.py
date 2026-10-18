"""Saved scopes follow concept sets rather than mutable module identifiers."""
from __future__ import annotations


def module_scope(graph, module_id: str) -> dict:
    module = graph.modules[module_id]
    return {"kind": "module", "node_ids": list(module.get("node_ids", [])),
            "module_id_at_creation": module_id, "graph_version_at_creation": graph.graph_version}


def resolve_scope(scope: dict, graph, min_jaccard: float = 0.5) -> dict:
    if scope.get("kind") == "roadmap":
        return {"module_id": None, "stale": False, "jaccard": 0.0}
    if scope.get("kind") != "module" or not scope.get("node_ids"):
        raise ValueError("module scope requires non-empty node_ids")
    saved = set(scope["node_ids"])
    candidates = []
    for position, (module_id, module) in enumerate(graph.modules.items()):
        current = set(module.get("node_ids", []))
        union = saved | current
        score = len(saved & current) / len(union) if union else 0.0
        candidates.append((-score, int(module.get("index", position)), module_id))
    if not candidates:
        return {"module_id": None, "stale": True, "jaccard": 0.0}
    negative_score, _, module_id = min(candidates)
    score = -negative_score
    stale = score < min_jaccard
    return {"module_id": None if stale else module_id, "stale": stale, "jaccard": score}
