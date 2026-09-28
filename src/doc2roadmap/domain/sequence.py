from __future__ import annotations

import heapq
from collections import Counter

# Mặc định thiết kế (spec v2, W3), không chỉnh trên bộ vàng: Q6 không phụ thuộc cách chia module, còn độ mạch lạc chỉ
# được chấm bằng người.
# `floor`/`small`: module dưới 3 khái niệm bị phạt 2 đơn vị cho mỗi khái niệm thiếu. Không có phạt này thì một
# khái niệm bị đồ thị kéo từ mục khác lên thành module đứng một mình (đo được 13 module như vậy trên doc-1).
DEFAULT_WEIGHTS = {"alpha": 1, "unit": 2, "chapter": 4, "cut": 1, "floor": 3, "small": 2}
_UNKNOWN = (10**12, 10**12)


def learning_sequence(node_ids, edges, position):
    """Dãy học: sắp topo, luôn lấy khái niệm sẵn sàng đứng sớm nhất theo thứ tự dạy (spec v2, W2).

    `position[node_id]` là khoá so sánh được, ví dụ `(chỉ số chunk dạy, vị trí ký tự)`. Kết quả là phần mở rộng tuyến
    tính gần thứ tự dạy nhất theo nghĩa từ điển; mọi cạnh `requires` đi từ trước ra sau.
    """
    nodes = set(node_ids)
    parents = {node: set() for node in nodes}
    children = {node: set() for node in nodes}
    for edge in edges:
        if edge.get("edge_type", "requires") != "requires" or edge.get("soft"):
            continue
        source, target = edge["source"], edge["target"]
        if source in nodes and target in nodes and source != target:
            parents[target].add(source)
            children[source].add(target)
    waiting = {node: len(parents[node]) for node in nodes}
    ready = [(position.get(node, _UNKNOWN), node) for node in nodes if not waiting[node]]
    heapq.heapify(ready)
    order = []
    while ready:
        _, node = heapq.heappop(ready)
        order.append(node)
        for child in children[node]:
            waiting[child] -= 1
            if not waiting[child]:
                heapq.heappush(ready, (position.get(child, _UNKNOWN), child))
    if len(order) != len(nodes):
        raise ValueError("đồ thị requires còn chu trình; A9 phải giao DAG")
    return order


def soften_backward_edges(edges, position):
    """R17: a prerequisite taught in a later chunk must not reorder an earlier lesson.

    Same-chunk edges stay hard regardless of character offset. A missing teaching position
    (A10's 10**9 sentinel) is left to the mentioned-only bridge, not classified backward.
    """
    hard, soft = [], []
    for edge in edges:
        if edge.get("soft"):
            soft.append(edge)
            continue
        source, target = position.get(edge["source"]), position.get(edge["target"])
        if (edge.get("edge_type", "requires") == "requires"
                and source is not None and target is not None
                and source[0] < 10**9 and target[0] < 10**9 and source[0] > target[0]):
            soft.append({**edge, "soft": True, "soft_reason": "ngược thứ tự sách"})
        else:
            hard.append(edge)
    return hard, soft


def choose_levels(ancestry, width):
    """Chọn cấp "chương" và cấp "mục" theo chính tài liệu (spec v2, W4).

    `ancestry[node_id]` là danh sách section từ cấp 1 xuống section chứa đoạn dạy khái niệm. Cấp đủ điều kiện khi trung
    vị số khái niệm mỗi mục ≥ `width / 2`. Mục = cấp đủ điều kiện sâu nhất, chương = nông nhất; trùng nhau thì bỏ chương
    để không phạt hai lần cùng một ranh giới; không cấp nào đủ điều kiện thì tắt cả hai.
    """
    paths = [path for path in ancestry.values() if path]
    depth = max((len(path) for path in paths), default=0)
    qualifying = []
    for level in range(1, depth + 1):
        counts = sorted(Counter(path[min(level, len(path)) - 1] for path in paths).values())
        middle = len(counts) // 2
        median = counts[middle] if len(counts) % 2 else (counts[middle - 1] + counts[middle]) / 2
        if median >= width / 2:
            qualifying.append(level)
    if not qualifying:
        return None, None
    chapter, unit = min(qualifying), max(qualifying)
    return (None if chapter == unit else chapter), unit


def segment_modules(sequence, *, width, unit_of=None, chapter_of=None, weights=None):
    """Chia dãy thành module liền mạch ≤ `width` bằng quy hoạch động kiểu ngắt dòng (spec v2, W3).

    Chi phí nhân với `width²` để mọi số là số nguyên — ca hoà là hoà thật. Khi hoà, module phía trước đầy hơn: điểm cắt
    được duyệt từ phải sang trái và chỉ đổi khi rẻ hơn hẳn.
    """
    weights = weights or DEFAULT_WEIGHTS
    unit_of, chapter_of = unit_of or {}, chapter_of or {}
    count = len(sequence)
    if count == 0:
        return []
    scale = width * width
    best = [0] + [None] * count
    back = [0] * (count + 1)
    for end in range(1, count + 1):
        for start in range(end - 1, max(0, end - width) - 1, -1):
            segment = sequence[start:end]
            units = len({unit_of[node] for node in segment if unit_of.get(node) is not None})
            chapters = len({chapter_of[node] for node in segment if chapter_of.get(node) is not None})
            cost = scale * (1 + weights["unit"] * max(units - 1, 0) + weights["chapter"] * max(chapters - 1, 0))
            cost += weights["alpha"] * (width - len(segment)) ** 2
            cost += scale * weights["small"] * max(0, weights["floor"] - len(segment))
            if start > 0:
                left, right = unit_of.get(sequence[start - 1]), unit_of.get(sequence[start])
                if left is not None and left == right:
                    cost += scale * weights["cut"]
            total = best[start] + cost
            if best[end] is None or total < best[end]:
                best[end], back[end] = total, start
    modules, end = [], count
    while end > 0:
        start = back[end]
        modules.append(sequence[start:end])
        end = start
    return modules[::-1]


def _at(path, level):
    if not path or not level:
        return None
    return path[min(level, len(path)) - 1]


def _longest_path(order, parents):
    depth = {}
    for node in order:
        depth[node] = 1 + max((depth[parent] for parent in parents[node]), default=0)
    return max(depth.values(), default=0)


def transitive_reduction(edges):
    """Return only the direct arcs of a DAG; keep the original graph elsewhere."""
    pairs = {(edge["source"], edge["target"]) for edge in edges
             if edge.get("edge_type", "requires") == "requires" and not edge.get("soft")
             and edge["source"] != edge["target"]}
    children = {}
    for source, target in pairs:
        children.setdefault(source, set()).add(target)
    reduced = set()
    for source, target in pairs:
        stack = list(children.get(source, set()) - {target})
        seen = set()
        while stack:
            current = stack.pop()
            if current == target:
                break
            if current not in seen:
                seen.add(current)
                stack.extend(children.get(current, ()))
        else:
            reduced.add((source, target))
    return reduced


def module_dependencies(modules, edges):
    module_of = {node: module["module_id"] for module in modules for node in module["node_ids"]}
    pairs = {(module_of[edge["source"]], module_of[edge["target"]]) for edge in edges
             if edge.get("edge_type", "requires") == "requires" and not edge.get("soft")
             and edge["source"] in module_of and edge["target"] in module_of
             and module_of[edge["source"]] != module_of[edge["target"]]}
    reduced = transitive_reduction({"source": source, "target": target} for source, target in pairs)
    order = {module["module_id"]: index for index, module in enumerate(modules)}
    return {module["module_id"]: sorted((source for source, target in reduced
                                           if target == module["module_id"]), key=order.get)
            for module in modules}


def build_sequence_roadmap(nodes, edges, *, position, ancestry, section_titles, width, reviewed, weights=None):
    """A10 neo sách (ADR 0010): dãy học, module, và các trường giải thích cho từng khái niệm.

    `ancestry[node_id]` là chuỗi section từ cấp 1 xuống nơi dạy; `reviewed[node_id]` là các phiên A8 đã xét khái niệm.
    """
    learnable = [dict(node) for node in nodes if node.get("learnable")]
    by_id = {node["node_id"]: node for node in learnable}
    hard = [edge for edge in edges if edge.get("edge_type", "requires") == "requires" and not edge.get("soft")
            and edge["source"] in by_id and edge["target"] in by_id and edge["source"] != edge["target"]]
    sequence = learning_sequence(list(by_id), hard, position)
    chapter_level, unit_level = choose_levels({node: ancestry.get(node, []) for node in by_id}, width)
    unit_of = {node: _at(ancestry.get(node), unit_level) for node in sequence}
    chapter_of = {node: _at(ancestry.get(node), chapter_level) for node in sequence}
    groups = segment_modules(sequence, width=width, unit_of=unit_of, chapter_of=chapter_of, weights=weights)

    index = {node: i for i, node in enumerate(sequence)}
    parents = {node: set() for node in sequence}
    for edge in hard:
        parents[edge["target"]].add(edge["source"])
    # Tên module lấy từ mục; tài liệu phẳng (không cấp nào đủ điều kiện) thì lấy mục sâu nhất, tức tiêu đề slide.
    title_of = {node: _at(ancestry.get(node), unit_level) if unit_level else (ancestry.get(node) or [None])[-1]
                for node in sequence}
    modules, coverage_flags = [], []
    for number, members in enumerate(groups, 1):
        module_id = f"module_{number:03d}"
        counts = Counter(title_of[node] for node in members if title_of[node] is not None)
        first_seen = {}
        for node in members:
            first_seen.setdefault(title_of[node], index[node])
        ranked = sorted(counts, key=lambda section: (-counts[section], first_seen[section]))
        # Module vắt qua nhiều mục thì ghép hai tiêu đề đầu — không đặt một tên đẹp để che việc trộn.
        title = " · ".join(section_titles.get(section, section) for section in ranked[:2]) or by_id[members[0]]["name"]
        modules.append({
            "module_id": module_id,
            "index": number - 1,
            "title": title,
            "node_ids": list(members),
            "section_ids": ranked,
            "first_order_index": min(by_id[node].get("first_order_index", 0) for node in members),
        })
        for node_id in members:
            node = by_id[node_id]
            sessions = sorted(set(reviewed.get(node_id, [])))
            node["reviewed_session_ids"] = sessions
            if not sessions:
                node["coverage_status"] = "unreviewed"
                coverage_flags.append({"kind": "unreviewed_learnable_node", "node_id": node_id})
            elif not parents[node_id]:
                node["coverage_status"] = "reviewed_no_prerequisite"
            else:
                node["coverage_status"] = "reviewed_with_prerequisite"
            node["sequence_index"] = index[node_id]
            node["module_id"] = module_id
            node["prerequisites"] = sorted(parents[node_id], key=index.get)
            for stale in ("layer", "stage_id"):
                node.pop(stale, None)
    module_of = {node: module["module_id"] for module in modules for node in module["node_ids"]}
    chunk_modules = {}
    for node_id in sequence:
        node = by_id[node_id]
        for chunk_id in node.get("teaching_chunk_ids") or node.get("defining_chunk_ids", []):
            chunk_modules.setdefault(chunk_id, set()).add(module_of[node_id])
    chunk_module_map = {
        chunk_id: {"module_id": min(ids), "all_module_ids": sorted(ids)} for chunk_id, ids in sorted(chunk_modules.items())
    }
    return {
        "mode": "requires",
        "sequence": sequence,
        "modules": modules,
        "nodes": [by_id[node] for node in sequence],
        "chunk_module_map": chunk_module_map,
        "coverage_flags": coverage_flags,
        "levels": {"chapter": chapter_level, "unit": unit_level},
        "longest_path": _longest_path(sequence, parents),
    }


def target_modules(modules, edges, targets):
    """Keep complete modules on the module-level prerequisite path to a target."""
    module_of = {node: module["module_id"] for module in modules for node in module["node_ids"]}
    parents = module_dependencies(modules, edges)
    keep, stack = {module_of[node] for node in targets if node in module_of}, [module_of[node] for node in targets
                                                                    if node in module_of]
    while stack:
        module_id = stack.pop()
        for parent in parents.get(module_id, ()):
            if parent not in keep:
                keep.add(parent)
                stack.append(parent)
    return [module for module in modules if module["module_id"] in keep]
