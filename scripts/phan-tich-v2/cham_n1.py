"""Vé v2-04, cổng 2 trên N1: chạy neo định nghĩa (C8 v3) trên đồ thị validated của tài liệu N1 và chấm với nhãn mù T3.

Có gọi mô hình khi neo chưa có trong cache (≈ 0,01–0,05 USD cho 25–40 khái niệm). Chạy từ gốc repo:
    .venv/Scripts/python.exe scripts/phan-tich-v2/cham_n1.py doc-5
"""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import openpyxl

sys.path.insert(0, "src")
from doc2roadmap.application.use_cases.anchor_concepts import AnchorConcepts  # noqa: E402
from doc2roadmap.composition import build_learning_graph  # noqa: E402
from doc2roadmap.domain.teaching import EXCLUDED_STATUSES  # noqa: E402

KEEP_TAUGHT, KEEP_MENTIONED = "Giữ — được dạy", "Giữ — chỉ được nhắc"
EXCLUDE = {"Loại — hành chính của khoá học", "Loại — chi tiết của một ví dụ, hình hoặc bộ dữ liệu",
           "Loại — người, tổ chức, siêu dữ liệu", "Kiến thức nền cần có trước"}


def latest(store, doc, stage):
    artifact = store.load_latest_graph(doc)
    while artifact.payload.get("stage") != stage:
        artifact = store.load_graph(doc, artifact.manifest["upstream_version"])
    return artifact


def labels_of(doc):
    key = json.loads(Path(f"artifacts/a8-gold/nhan-khai-niem-{doc}-khoa.json").read_text(encoding="utf-8"))
    path = Path(f"artifacts/a8-gold/nhan-khai-niem-{doc}-output.xlsx")
    rows = list(openpyxl.load_workbook(path, read_only=True)["Khái niệm"].iter_rows(values_only=True))[1:]
    by_item = {row["item"]: row for row in key["items"]}
    labels = {by_item[int(r[0])]["node_id"]: r[4] for r in rows if r and r[0] is not None and r[4]}
    return labels, hashlib.sha256(path.read_bytes()).hexdigest(), len(key["items"])


def score(name, nodes, labels):
    status = {n["node_id"]: n.get("teaching_status") for n in nodes}
    keep = [n for n, label in labels.items() if label in (KEEP_TAUGHT, KEEP_MENTIONED)]
    exclude = [n for n, label in labels.items() if label in EXCLUDE]
    wrong = [n for n in keep if status.get(n) in EXCLUDED_STATUSES]
    right = [n for n in exclude if status.get(n) in EXCLUDED_STATUSES]
    taught = [n for n, label in labels.items() if label == KEEP_TAUGHT]
    mentioned = [n for n, label in labels.items() if label == KEEP_MENTIONED]
    print(f"  {name}: trạng thái {dict(Counter(status.get(n) for n in labels))}")
    print(f"    loại nhầm {len(wrong)}/{len(keep)} (cổng: 0) | loại đúng "
          f"{f'{len(right)}/{len(exclude)}' if exclude else 'không có mẫu số'}")
    print(f"    'được dạy' → taught {sum(status.get(n) == 'taught' for n in taught)}/{len(taught)}"
          f" | 'chỉ được nhắc' → mentioned_only {sum(status.get(n) == 'mentioned_only' for n in mentioned)}/{len(mentioned)}")
    return wrong


def main(doc):
    labels, sha, total = labels_of(doc)
    pipeline, _ = build_learning_graph(allow_spend=True)
    store = pipeline.teaching.store
    # Lấy bản C8 v2 của chuỗi mặc định TRƯỚC khi chạy neo: sau đó artifact `teaching` mới nhất là bản neo.
    v2 = latest(store, doc, "teaching")
    validated = store.load_graph(doc, v2.manifest["upstream_version"])
    anchors, cached = AnchorConcepts(store, pipeline.teaching.model, concurrency=4).execute(doc, upstream=validated)
    names = {n["node_id"]: n["name"] for n in anchors.payload["nodes"]}
    print(f"{doc}: nhãn {len(labels)}/{total} (SHA-256 {sha[:16]}…) | validated v{validated.version}"
          f" | neo v{anchors.version}{' (cache)' if cached else ''}"
          f" {anchors.payload['cost_summary'].get('teaching_usd', 0.0):.3f} USD | C8 v2 v{v2.version}")
    wrong = score("C8 v3 (neo)", anchors.payload["nodes"], labels)
    for node_id in wrong:
        log = next(a for a in anchors.payload["anchor_log"] if a["node_id"] == node_id)
        print(f"      loại nhầm: {names[node_id]!r} nhãn {labels[node_id]!r} → {log['status']} | {log.get('quote')!r}")
    if v2.manifest["config"].get("algorithm_id") != "a10-teaching-anchor-v3":
        score("C8 v2 (bản tạm)", v2.payload["nodes"], labels)


if __name__ == "__main__":
    main(sys.argv[1])
