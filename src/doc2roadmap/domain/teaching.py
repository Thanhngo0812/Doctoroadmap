from __future__ import annotations

from collections import deque

EXCLUDED_STATUSES = {"prior_knowledge", "not_subject_matter"}


def bypass_excluded(edges, excluded):
    """Bỏ node bị loại khỏi DAG mà không làm mất ràng buộc học trước: a → x → b thành a → b.

    Chỉ đi xuyên qua node bị loại, nên cạnh thêm vào đúng bằng phần khả đạt mà việc bỏ node làm mất. Đầu vào là
    DAG đã qua A9 nên phép co không thể sinh chu trình.
    """
    excluded = set(excluded)
    children = {}
    for edge in edges:
        if edge.get("soft"):
            continue
        children.setdefault(edge["source"], set()).add(edge["target"])
    kept = [edge for edge in edges if not edge.get("soft") and edge["source"] not in excluded and edge["target"] not in excluded]
    present = {(edge["source"], edge["target"]) for edge in kept}
    added = []
    for source in sorted({edge["source"] for edge in edges} - excluded):
        queue = deque((child, [child]) for child in sorted(children.get(source, ())) if child in excluded)
        seen = {child for child, _ in queue}
        while queue:
            node, path = queue.popleft()
            for child in sorted(children.get(node, ())):
                if child in excluded:
                    if child not in seen:
                        seen.add(child)
                        queue.append((child, path + [child]))
                elif (source, child) not in present:
                    present.add((source, child))
                    added.append({"source": source, "target": child, "edge_type": "requires", "via_excluded": path})
    return kept + added, added
