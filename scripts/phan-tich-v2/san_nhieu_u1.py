"""Sàn nhiễu của U1: cùng đồ thị, chỉ đổi cách phá thế hoà (đổi tên node theo hoán vị ngẫu nhiên), 30 lần.

Cạnh vàng có đường đi trong đồ thị máy luôn được tôn trọng (mọi cách xếp hợp lệ đều phải tôn trọng). Cạnh vàng không
có đường đi được đặt theo may rủi của bộ xếp. Đo cả hai phần.
"""
import json
import random
import statistics
import sys
from pathlib import Path

sys.path.insert(0, "src")
from doc2roadmap.domain.gold_scoring import gold_order_violations, transitive_closure  # noqa: E402
from doc2roadmap.domain.roadmap import build_roadmap  # noqa: E402

RUNS = 30

for doc, chapter, version in (("doc-1", "10-12", 10), ("doc-2", "98-115", 7)):
    payload = json.loads(Path(f"artifacts/graph/{doc}/v{version}/graph.json").read_text(encoding="utf-8"))
    gold = {(e["prerequisite"], e["target"])
            for e in json.loads(Path(f"artifacts/a8-gold/{doc}-{chapter}-vang.json").read_text(encoding="utf-8"))["edges"]}
    reach = transitive_closure({(e["source"], e["target"]) for e in payload["requires_edges"]})
    supported = {pair for pair in gold if pair in reach}
    errors = []
    for seed in range(RUNS):
        rng = random.Random(seed)
        ids = [n["node_id"] for n in payload["nodes"]]
        shuffled = ids[:]
        rng.shuffle(shuffled)
        rename = {old: f"n{index:04d}_{old}" for index, old in zip(range(len(ids)), shuffled)}
        back = {new: old for old, new in rename.items()}
        nodes = [{**n, "node_id": rename[n["node_id"]]} for n in payload["nodes"]]
        edges = [{**e, "source": rename[e["source"]], "target": rename[e["target"]]} for e in payload["requires_edges"]]
        result = build_roadmap(nodes, edges, payload["main_sessions"], [], [], stage_cap=8, stage_floor=3,
                               quality_gate=payload["quality_gate"])
        stages = [[back[node] for node in stage["node_ids"]] for stage in result["stages"]]
        errors.append(gold_order_violations(stages, gold)["learning_order_error"])
    observed = gold_order_violations([s["node_ids"] for s in payload["stages"]], gold)["learning_order_error"]
    print(f"=== {doc} v{version}: {len(gold)} cạnh vàng, {len(supported)} có đường đi trong đồ thị máy "
          f"(luôn được tôn trọng), {len(gold) - len(supported)} phó mặc cho bộ xếp")
    print(f"    U1 qua {RUNS} cách phá thế hoà: trung bình {statistics.mean(errors):.1%}, độ lệch chuẩn "
          f"{statistics.stdev(errors):.1%}, thấp nhất {min(errors):.1%}, cao nhất {max(errors):.1%} | bản đã xuất {observed:.1%}")
