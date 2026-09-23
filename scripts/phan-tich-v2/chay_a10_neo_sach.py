"""Vé v2-02: chạy A10 neo sách trên bảy tài liệu (không gọi mô hình) và kiểm cổng bằng assertion độc lập.

Chạy từ gốc repo:  .venv/Scripts/python.exe scripts/phan-tich-v2/chay_a10_neo_sach.py
"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, "src")
from doc2roadmap.application.use_cases.a8_score import score_roadmap_order  # noqa: E402
from doc2roadmap.application.use_cases.build_roadmap import BuildRoadmap  # noqa: E402
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore  # noqa: E402

W = 8
# Upstream đúng của chuỗi hiện hành (C8 v2 bản tạm): artifact teaching, không phải artifact C10 đã bị loại.
TEACHING = {"doc-1": 13, "doc-2": 8, "doc-3": 10, "baocao-canhan": 98, "naive-bayes": 28, "nhap-mon-ml": 28,
            "xstk-ch3-1": 28}
GOLD = {"doc-1": "artifacts/a8-gold/doc-1-10-12-vang.json", "doc-2": "artifacts/a8-gold/doc-2-98-115-vang.json"}
CG_STRICT = {"doc-1": 0.100, "doc-2": 0.148}  # U1 khắt khe của Coffman–Graham trên cùng đồ thị (v14, v9)

store = JsonArtifactStore(Path("artifacts"))
use_case = BuildRoadmap(store, stage_cap=W)
print(f"{'tài liệu':<15}{'khái niệm':>10}{'module':>8}  {'cỡ module':<34}{'cấp':>8}{'Q6':>8}{'bám sách':>10}")
for doc, version in TEACHING.items():
    upstream = store.load_graph(doc, version)
    assert upstream.payload["stage"] == "teaching", (doc, upstream.payload["stage"])
    artifact, reused = use_case.execute(doc, upstream=upstream)
    payload = artifact.payload

    # --- assertion độc lập với mã sinh ---
    eligible = {n["node_id"] for n in upstream.payload["nodes"]
                if n.get("learnable") and n.get("teaching_status") not in ("not_subject_matter", "prior_knowledge")}
    sequence = payload["sequence"]
    assert len(sequence) == len(set(sequence)) and set(sequence) == eligible, f"{doc}: dãy không phủ đúng một lần"
    flat = [node for module in payload["modules"] for node in module["node_ids"]]
    assert flat == sequence, f"{doc}: nối các module không ra đúng dãy"
    assert all(1 <= len(module["node_ids"]) <= W for module in payload["modules"]), f"{doc}: module vượt trần"
    index = {node: i for i, node in enumerate(sequence)}
    edges = [*payload["requires_edges"], *payload.get("bypassed_edges", [])]
    backward = [e for e in edges if e["source"] in index and e["target"] in index and index[e["source"]] >= index[e["target"]]]
    assert not backward, f"{doc}: {len(backward)} cạnh cứng đi ngược dãy"
    assert "stages" not in payload

    sizes = Counter(len(module["node_ids"]) for module in payload["modules"])
    levels = f"{payload['stats']['chapter_level']}/{payload['stats']['unit_level']}"
    q6 = tau = "—"
    if doc in GOLD:
        report = score_roadmap_order(artifact.path / "graph.json", [Path(GOLD[doc])])
        error = report["gold_order"]["learning_order_error"]
        assert report["order_unit"] == "sequence"
        assert error <= CG_STRICT[doc], f"{doc}: Q6 {error:.1%} tệ hơn Coffman–Graham {CG_STRICT[doc]:.1%}"
        q6 = f"{error:.1%}"
        tau = f"{report['presentation_agreement']['tau']:+.3f}"
    print(f"{doc + ' v' + str(artifact.version):<15}{len(sequence):>10}{len(payload['modules']):>8}  "
          f"{str(dict(sorted(sizes.items()))):<34}{levels:>8}{q6:>8}{tau:>10}")
print("\nCổng vé 02: mọi assertion qua trên bảy tài liệu.")
