"""Baseline "đọc sách theo thứ tự" so với lộ trình hiện tại. Chỉ đọc artifact, không gọi mô hình."""
import heapq
import json
import sys
from pathlib import Path

sys.path.insert(0, "src")
from doc2roadmap.domain.gold_scoring import gold_order_violations, transitive_closure  # noqa: E402

W = 8
CASES = [("doc-1", "10-12", 14), ("doc-2", "98-115", 9)]  # lộ trình C8 hiện hành


def position(node):
    value = node.get("teaching_order_index")
    return value if value is not None else node.get("first_order_index", 0)


def book_sequence(nodes):
    return [n["node_id"] for n in sorted(nodes, key=lambda n: (position(n), n["node_id"]))]


def linear_extension(nodes, edges):
    """Sắp topo ưu tiên vị trí sách: luôn lấy node sẵn sàng đứng sớm nhất trong sách."""
    pos = {n["node_id"]: position(n) for n in nodes}
    parents = {n: set() for n in pos}
    children = {n: set() for n in pos}
    for e in edges:
        if e["source"] in pos and e["target"] in pos:
            parents[e["target"]].add(e["source"])
            children[e["source"]].add(e["target"])
    waiting = {n: len(parents[n]) for n in pos}
    ready = [(pos[n], n) for n in pos if not waiting[n]]
    heapq.heapify(ready)
    order = []
    while ready:
        _, node = heapq.heappop(ready)
        order.append(node)
        for child in children[node]:
            waiting[child] -= 1
            if not waiting[child]:
                heapq.heappush(ready, (pos[child], child))
    assert len(order) == len(pos), "còn chu trình"
    return order, parents


def cut(sequence, parents=None):
    """Cắt dãy thành stage: tối đa W node, và (nếu có parents) không cạnh nào nằm trong một stage."""
    stages, current = [], []
    for node in sequence:
        clash = parents is not None and any(p in current for p in parents[node])
        if current and (len(current) >= W or clash):
            stages.append(current)
            current = []
        current.append(node)
    if current:
        stages.append(current)
    return stages


def violations_of(stages, edges):
    rank = {n: i for i, s in enumerate(stages) for n in s}
    return sum(1 for e in edges if e["source"] in rank and e["target"] in rank and rank[e["source"]] >= rank[e["target"]])


for doc, chapter, version in CASES:
    payload = json.loads(Path(f"artifacts/graph/{doc}/v{version}/graph.json").read_text(encoding="utf-8"))
    gold = {(e["prerequisite"], e["target"])
            for e in json.loads(Path(f"artifacts/a8-gold/{doc}-{chapter}-vang.json").read_text(encoding="utf-8"))["edges"]}
    placed = {n for s in payload["stages"] for n in s["node_ids"]}
    nodes = [n for n in payload["nodes"] if n["node_id"] in placed]
    edges = [*payload["requires_edges"], *payload.get("bypassed_edges", [])]
    edges = [e for e in edges if e["source"] in placed and e["target"] in placed]

    rows = {}
    seq0 = book_sequence(nodes)
    rows["B0 thứ tự sách thuần"] = (cut(seq0), seq0)
    seq1, parents = linear_extension(nodes, edges)
    rows["B1 topo ưu tiên sách"] = (cut(seq1, parents), seq1)
    rows["CG lộ trình hiện tại"] = ([s["node_ids"] for s in payload["stages"]], None)

    print(f"=== {doc} v{version}: {len(nodes)} node, {len(edges)} cạnh máy, {len(gold)} cạnh vàng")
    for label, (stages, sequence) in rows.items():
        staged = gold_order_violations(stages, gold)
        line = ""
        if sequence is not None:
            linear = gold_order_violations([[n] for n in sequence], gold)
            line = f" | dãy tuyến tính: ngược {linear['violated']} ({linear['learning_order_error']:.1%})"
        print(f"    {label:<22} {len(stages):>3} stage | U1 {staged['learning_order_error']:5.1%} "
              f"(ngược {staged['violated']:>2}, cùng stage {staged['same_stage']:>2}) | vi phạm cạnh máy "
              f"{violations_of(stages, edges):>3}{line}")
    # Sách tự nó vi phạm vàng ở đâu?
    rank = {n: i for i, n in enumerate(seq0)}
    back = [(a, b) for a, b in gold if a in rank and b in rank and rank[a] > rank[b]]
    names = {n["node_id"]: n["name"] for n in nodes}
    print(f"    sách tự đặt ngược {len(back)}/{len(gold)} cạnh vàng: " +
          "; ".join(f"{names.get(a, a)} → {names.get(b, b)}" for a, b in back[:6]))
