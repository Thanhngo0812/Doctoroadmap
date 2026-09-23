"""So ba cách phá thế hoà của A10 với phân bố nhiễu (30 hoán vị ngẫu nhiên tên node).

- CG hiện tại: Coffman–Graham, thế hoà cuối cùng phá bằng node_id (mã băm — tuỳ ý so với cuốn sách).
- C9 cũ: bỏ nhãn CG, đặt node theo (độ sâu, vị trí sách) — thứ tự sách là khoá chính.
- C9b: giữ nguyên Coffman–Graham; chỉ thay khoá phá thế hoà cuối cùng khi gán nhãn từ node_id sang vị trí sách.
  Bảo chứng số stage của CG không phụ thuộc cách phá thế hoà, nên C9b giữ nó.
"""
import json
import random
import statistics
import sys
from heapq import heappop, heappush
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, "src")
from doc2roadmap.domain import roadmap  # noqa: E402
from doc2roadmap.domain.gold_scoring import gold_order_violations  # noqa: E402

ORIGINAL = roadmap._coffman_graham
POSITION = {}


def c9b(node_ids, edges, width):
    """Bản sao _coffman_graham, khác đúng một chỗ: khoá heap là (nhãn con, -vị trí sách, node_id).

    Nút được gán nhãn nhỏ trước sẽ được đặt muộn hơn; nên khi hoà, nút đứng sau trong sách nhận nhãn trước.
    """
    parents = {node_id: set() for node_id in node_ids}
    children = {node_id: set() for node_id in node_ids}
    for edge in edges:
        parents[edge["target"]].add(edge["source"])
        children[edge["source"]].add(edge["target"])
    remaining = {node_id: len(children[node_id]) for node_id in node_ids}
    ready = [((), -POSITION.get(node_id, 0), node_id) for node_id in node_ids if not remaining[node_id]]
    ready.sort()
    labels = {}
    while ready:
        _, _, node_id = heappop(ready)
        labels[node_id] = len(labels) + 1
        for parent in parents[node_id]:
            remaining[parent] -= 1
            if not remaining[parent]:
                key = tuple(sorted((labels[child] for child in children[parent]), reverse=True))
                heappush(ready, (key, -POSITION.get(parent, 0), parent))
    stages, layer_of, longest = [], {}, {}
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


def c9_old(node_ids, edges, width):
    _, parents, children, longest = ORIGINAL(node_ids, edges, width)
    depth = {}

    def floor(node):
        if node not in depth:
            depth[node] = max((floor(parent) + 1 for parent in parents[node]), default=0)
        return depth[node]

    stages, layer_of = [], {}
    for node_id in sorted(node_ids, key=lambda value: (floor(value), POSITION.get(value, 0), value)):
        layer = max((layer_of[parent] + 1 for parent in parents[node_id]), default=0)
        while layer < len(stages) and len(stages[layer]) >= width:
            layer += 1
        if layer == len(stages):
            stages.append([])
        stages[layer].append(node_id)
        layer_of[node_id] = layer
    return stages, parents, children, longest


def run(payload, gold, labeler=None):
    with patch.object(roadmap, "_coffman_graham", labeler or ORIGINAL):
        result = roadmap.build_roadmap(payload["nodes"], payload["requires_edges"], payload["main_sessions"], [], [],
                                       stage_cap=8, stage_floor=3, quality_gate=payload["quality_gate"])
    stages = [stage["node_ids"] for stage in result["stages"]]
    return gold_order_violations(stages, gold)["learning_order_error"], len(stages)


def noise(payload, gold, runs=30):
    values = []
    for seed in range(runs):
        rng = random.Random(seed)
        ids = [node["node_id"] for node in payload["nodes"]]
        order = ids[:]
        rng.shuffle(order)
        rename = {old: f"n{index:04d}_{old}" for index, old in enumerate(order)}
        back = {new: old for old, new in rename.items()}
        renamed = {**payload,
                   "nodes": [{**node, "node_id": rename[node["node_id"]]} for node in payload["nodes"]],
                   "requires_edges": [{**edge, "source": rename[edge["source"]], "target": rename[edge["target"]]}
                                      for edge in payload["requires_edges"]]}
        with patch.object(roadmap, "_coffman_graham", ORIGINAL):
            result = roadmap.build_roadmap(renamed["nodes"], renamed["requires_edges"], payload["main_sessions"], [],
                                           [], stage_cap=8, stage_floor=3, quality_gate=payload["quality_gate"])
        stages = [[back[node] for node in stage["node_ids"]] for stage in result["stages"]]
        values.append(gold_order_violations(stages, gold)["learning_order_error"])
    return values


for doc, chapter, version in (("doc-1", "10-12", 7), ("doc-1", "10-12", 10), ("doc-2", "98-115", 7)):
    payload = json.loads(Path(f"artifacts/graph/{doc}/v{version}/graph.json").read_text(encoding="utf-8"))
    gold = {(e["prerequisite"], e["target"])
            for e in json.loads(Path(f"artifacts/a8-gold/{doc}-{chapter}-vang.json").read_text(encoding="utf-8"))["edges"]}
    POSITION.clear()
    POSITION.update({node["node_id"]: node.get("first_order_index", 0) for node in payload["nodes"]})
    values = noise(payload, gold)
    mean, sd = statistics.mean(values), statistics.stdev(values)
    print(f"=== {doc} v{version}: nhiễu {mean:.1%} ± {sd:.1%} (thấp nhất {min(values):.1%})")
    for label, labeler in (("CG hiện tại", None), ("C9 cũ", c9_old), ("C9b", c9b)):
        error, stages = run(payload, gold, labeler)
        z = (error - mean) / sd if sd else 0.0
        below = sum(value <= error for value in values)
        print(f"    {label:<12} U1 {error:5.1%} | z = {z:+.2f} | {below:>2}/30 lần ngẫu nhiên tốt bằng hoặc hơn | {stages} stage")
