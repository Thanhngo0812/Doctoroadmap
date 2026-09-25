"""Vé v2-04 lượt 3: neo với luật so tên mới (bỏ dấu LaTeX, gộp gạch nối), rồi danh tính + A10 cho hai chương vàng.

Có gọi mô hình (≈ 0,5 USD). Chạy từ gốc repo:  .venv/Scripts/python.exe scripts/phan-tich-v2/chay_luot3.py
"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "scripts/phan-tich-v2")
from doc2roadmap.application.use_cases.a8_score import score_roadmap_order  # noqa: E402
from doc2roadmap.application.use_cases.anchor_concepts import AnchorConcepts  # noqa: E402
from doc2roadmap.application.use_cases.build_roadmap import BuildRoadmap  # noqa: E402
from doc2roadmap.application.use_cases.judge_identity import JudgeIdentity  # noqa: E402
from doc2roadmap.composition import build_learning_graph  # noqa: E402
from doc2roadmap.domain.teaching import EXCLUDED_STATUSES  # noqa: E402
from chay_neo import ADMIN_DOC1, BORDER, DOC3_KEEP, DOC3_OUT  # noqa: E402
from chay_danh_tinh import load_review  # noqa: E402

VALIDATED = {"doc-1": 9, "doc-2": 6, "doc-3": 6, "baocao-canhan": 96, "naive-bayes": 26, "nhap-mon-ml": 26, "doc-5": 6}
GOLD = {"doc-1": "artifacts/a8-gold/doc-1-10-12-vang.json", "doc-2": "artifacts/a8-gold/doc-2-98-115-vang.json"}

pipeline, _ = build_learning_graph(allow_spend=True)
store = pipeline.teaching.store
anchor = AnchorConcepts(store, pipeline.teaching.model, concurrency=4)
judge = JudgeIdentity(store, pipeline.teaching.model, concurrency=4, review=load_review())
roadmap = BuildRoadmap(store, stage_cap=8)
total = 0.0
for doc, version in VALIDATED.items():
    teaching, _ = anchor.execute(doc, upstream=store.load_graph(doc, version))
    nodes = [n for n in teaching.payload["nodes"] if n.get("learnable")]
    out = {n["name"] for n in nodes if n["teaching_status"] in EXCLUDED_STATUSES}
    usd = teaching.payload["cost_summary"].get("teaching_usd", 0.0)
    total += usd
    print(f"{doc:<14} teaching v{teaching.version} | {dict(Counter(n['teaching_status'] for n in nodes))} | {usd:.3f} USD")
    if doc == "doc-1":
        print(f"    loại ngoài hành chính + det(Y): {sorted(out - ADMIN_DOC1 - {'det(Y)'})} | hành chính {len(ADMIN_DOC1 & out)}/3")
    if doc == "doc-3":
        print(f"    doc-3 loại đúng {len(DOC3_OUT & out)}/13, loại nhầm {len(DOC3_KEEP & out)}/33 {sorted(DOC3_KEEP & out)}")
    if doc in BORDER:
        print(f"    loại nhầm: {sorted(out - BORDER[doc])}")
    if doc == "doc-5":
        print(f"    doc-5 loại: {sorted(out)} (nhãn: cả 25 là giữ)")
    if doc in GOLD:
        identity, _ = judge.execute(doc, upstream=teaching)
        total += identity.payload["cost_summary"].get("identity_usd", 0.0)
        stages, _ = roadmap.execute(doc, upstream=identity)
        report = score_roadmap_order(stages.path / "graph.json", [Path(GOLD[doc])])
        g = report["gold_order"]
        names = {n["node_id"]: n["name"] for n in [*stages.payload["nodes"], *stages.payload.get("excluded_nodes", [])]}
        fmn = next((n for n in teaching.payload["nodes"] if n["name"] == "𝐅^{m,n}"), None)
        print(f"    identity v{identity.version} → stages v{stages.version} | Q6 {g['learning_order_error']:.1%}"
              f" (vi phạm {g['violated']}, thiếu đầu {g['out_of_scope']}) | Q7 {report['target_coverage']['mean_coverage']:.0%}"
              f" ({report['target_coverage']['complete']}/{report['target_coverage']['targets']} đích đủ)")
        for row in report["violations"]:
            if row.get("bucket") == "violated":
                print(f"      vi phạm: {names.get(row['prerequisite'])!r} → {names.get(row['target'])!r}")
        if fmn:
            print(f"    𝐅^{{m,n}}: {fmn['teaching_status']} vị trí {fmn.get('teaching_order_index')}")
print(f"Tổng chi vòng này: {total:.3f} USD")
