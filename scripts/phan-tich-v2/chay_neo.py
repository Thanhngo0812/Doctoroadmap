"""Vé v2-04: chạy neo định nghĩa (C8 v3) trên bảy tài liệu rồi A10 neo sách, và chấm trên dữ liệu phát triển.

Có gọi mô hình (≈0,3–0,6 USD). Chạy từ gốc repo:  .venv/Scripts/python.exe scripts/phan-tich-v2/chay_neo.py [doc ...]
"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, "src")
from doc2roadmap.application.use_cases.a8_score import score_roadmap_order  # noqa: E402
from doc2roadmap.application.use_cases.anchor_concepts import AnchorConcepts  # noqa: E402
from doc2roadmap.application.use_cases.build_roadmap import BuildRoadmap  # noqa: E402
from doc2roadmap.composition import build_learning_graph  # noqa: E402

VALIDATED = {"doc-1": 9, "doc-2": 6, "doc-3": 6, "baocao-canhan": 96, "naive-bayes": 26, "nhap-mon-ml": 26, "xstk-ch3-1": 26}
GOLD = {"doc-1": "artifacts/a8-gold/doc-1-10-12-vang.json", "doc-2": "artifacts/a8-gold/doc-2-98-115-vang.json"}
EXCLUDED = {"not_subject_matter", "prior_knowledge"}
# Nhãn đã khoá trước (kế hoạch cũ mục 14) — nay là dữ liệu phát triển, không phải cổng.
DOC3_OUT = {"Class participation", "Final project", "Homework assignments", "Experience", "GPA", "Top node", "Middle node",
            "Bottom node", "A few numbers", "A single number", "Multi-modal example", "Python", "Machine learning concepts"}
DOC3_KEEP = {"Artificial Intelligence", "Traditional approach", "Polanyi's Paradox", "Machine Learning",
             "Classification and Regression Tree", "Linear Regression", "Machine Learning Model", "Support Vector Machines",
             "Gradient Boosted Machines", "Neural Networks", "Random Forests", "Feature extraction", "Deep Learning", "GenAI",
             "Logistic Regression", "Independent variables", "Coefficients", "Intercept", "linear functions", "Layer",
             "Dense", "Activation function", "Linear activation function", "ReLU", "Hidden layers", "Input variables",
             "Output variable", "output layer", "Sigmoid activation function", "Input Layer", "parameters",
             "Feedforward neural network", "Network architecture"}
BORDER = {"naive-bayes": {"Xác suất p(x i |c)", "Bảng từ vựng", "Real time Prediction"},
          "baocao-canhan": {"Project Skeleton", "Refactor", "Branching strategy"},
          "nhap-mon-ml": {"Tập học quá bé", "Mô hình quá phức tạp", "Ghi lịch sử", "Mô tả ảnh", "Lọc thư rác"}}
ADMIN_DOC1 = {"Thang điểm chữ", "Thi viết rọc phách", "Điểm đánh giá học phần"}

pipeline, _ = build_learning_graph(allow_spend=True)
store = pipeline.teaching.store
anchor = AnchorConcepts(store, pipeline.teaching.model, concurrency=4)
roadmap = BuildRoadmap(store, stage_cap=8)
total = 0.0
for doc in (sys.argv[1:] or list(VALIDATED)):
    teaching, _ = anchor.execute(doc, upstream=store.load_graph(doc, VALIDATED[doc]))
    stages, _ = roadmap.execute(doc, upstream=teaching)
    nodes = [n for n in teaching.payload["nodes"] if n.get("learnable")]
    out = {n["name"] for n in nodes if n["teaching_status"] in EXCLUDED}
    usd = teaching.payload["cost_summary"].get("teaching_usd", 0.0)
    total += usd
    anchored = sum(1 for n in nodes if n.get("anchor"))
    line = (f"{doc:<14} teaching v{teaching.version} → stages v{stages.version} | {dict(Counter(n['teaching_status'] for n in nodes))}"
            f" | có câu neo {anchored}/{len(nodes)} | {usd:.3f} USD | {len(stages.payload['modules'])} module")
    print(line)
    if doc == "doc-3":
        print(f"    doc-3 (đã nhìn thấy): loại đúng {len(DOC3_OUT & out)}/13, loại nhầm {len(DOC3_KEEP & out)}/33: "
              f"{sorted(DOC3_KEEP & out)} | lọt {sorted(DOC3_OUT - out)}")
    if doc in BORDER:
        wrong = sorted(out - BORDER[doc])
        print(f"    loại nhầm (mọi node trừ lưng chừng là phải giữ): {len(wrong)} {wrong}")
    if doc == "doc-1":
        print(f"    hành chính bị loại {len(ADMIN_DOC1 & out)}/3 | mọi node bị loại: {sorted(out)}")
    if doc in GOLD:
        report = score_roadmap_order(stages.path / "graph.json", [Path(GOLD[doc])])
        g = report["gold_order"]
        print(f"    Q6 {g['learning_order_error']:.1%} (thiếu đầu {g['out_of_scope']}) | Q7 {report['target_coverage']['mean_coverage']:.0%}"
              f" | độ bám sách {report['presentation_agreement']['tau']:+.3f}")
    elif doc not in BORDER and doc not in ("doc-3", "doc-1"):
        print(f"    mọi node bị loại (đọc tay): {sorted(out)}")
print(f"Tổng chi vòng này: {total:.3f} USD")
