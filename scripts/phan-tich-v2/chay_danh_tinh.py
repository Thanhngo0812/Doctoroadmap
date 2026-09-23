"""Vé v2-05: phán danh tính trên bản neo lượt 2 của vé 04, rồi A10, rồi chấm trên dữ liệu phát triển.

Có gọi mô hình (< 0,1 USD). Chạy từ gốc repo:  .venv/Scripts/python.exe scripts/phan-tich-v2/chay_danh_tinh.py [doc ...]
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "src")
from doc2roadmap.application.use_cases.a8_score import score_roadmap_order  # noqa: E402
from doc2roadmap.application.use_cases.build_roadmap import BuildRoadmap  # noqa: E402
from doc2roadmap.application.use_cases.judge_identity import JudgeIdentity  # noqa: E402
from doc2roadmap.composition import build_learning_graph  # noqa: E402
from doc2roadmap.domain.global_validation import strongly_connected_components  # noqa: E402

TEACHING = {"doc-1": 21, "doc-2": 16, "doc-3": 16, "naive-bayes": 34, "nhap-mon-ml": 34, "baocao-canhan": 104}
GOLD = {"doc-1": "artifacts/a8-gold/doc-1-10-12-vang.json", "doc-2": "artifacts/a8-gold/doc-2-98-115-vang.json"}

pipeline, _ = build_learning_graph(allow_spend=True)
store = pipeline.teaching.store
judge = JudgeIdentity(store, pipeline.teaching.model, concurrency=4)
roadmap = BuildRoadmap(store, stage_cap=8)
total, summary = 0.0, {}
for doc in (sys.argv[1:] or list(TEACHING)):
    identity, _ = judge.execute(doc, upstream=store.load_graph(doc, TEACHING[doc]))
    stages, _ = roadmap.execute(doc, upstream=identity)
    p = identity.payload
    usd = p["cost_summary"].get("identity_usd", 0.0)
    total += usd
    merged = set(p["identity_map"])
    edges = p["requires_edges"]
    cycles = [c for c in strongly_connected_components({n for e in edges for n in (e["source"], e["target"])}, edges)
              if len(c) > 1]
    dangling = [e for e in edges if e["source"] in merged or e["target"] in merged]
    stats = p["stats"]
    print(f"{doc:<14} identity v{identity.version} → stages v{stages.version} | {stats['identity_pair_count']} cặp "
          f"{stats['identity_verdicts']} | gộp {len(merged)} | gỡ {stats['identity_removed_edge_count']} cạnh | "
          f"mở {stats['identity_open_count']} | chu trình {len(cycles)} | cạnh treo {len(dangling)} | {usd:.3f} USD")
    names = {n["node_id"]: n["name"] for n in [*p["nodes"], *p["merged_nodes"]]}
    for source, head in p["identity_map"].items():
        print(f"    gộp: {names[source]!r} → {names[head]!r}")
    for group in p["identity_open_groups"]:
        print(f"    nhóm mở: {[names[n] for n in group]}")
    touched = []
    if doc in GOLD:
        gold = json.loads(Path(GOLD[doc]).read_text(encoding="utf-8"))
        concepts = {n for e in gold["edges"] for n in (e["prerequisite"], e["target"])} | set(gold["targets"])
        touched = [(s, h) for s, h in p["identity_map"].items() if s in concepts or h in concepts]
        report = score_roadmap_order(stages.path / "graph.json", [Path(GOLD[doc])])
        g = report["gold_order"]
        print(f"    Q6 {g['learning_order_error']:.1%} (thiếu đầu {g['out_of_scope']}, cạnh vàng rời do gộp "
              f"{report['identity_dropped_gold_edges']}) | Q7 {report['target_coverage']['mean_coverage']:.0%} | "
              f"gộp chạm vàng {len(touched)}")
    summary[doc] = {"identity_version": identity.version, "stages_version": stages.version,
                    "gold_touching": [{"merged": s, "into": h} for s, h in touched]}
Path("artifacts/a8-gold/danh-tinh-luot-1.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                                                           encoding="utf-8")
print(f"Tổng chi vòng này: {total:.3f} USD")
