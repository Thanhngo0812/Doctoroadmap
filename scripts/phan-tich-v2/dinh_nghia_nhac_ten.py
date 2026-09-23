"""Bộ dò cạnh không gọi mô hình: câu căn cứ (evidence, nguyên văn) của B có nhắc tên hoặc alias của A không?"""
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, "src")
from doc2roadmap.domain.gold_scoring import score_edges  # noqa: E402

CASES = [("doc-1", "10-12", 14), ("doc-2", "98-115", 9)]


def norm(text):
    text = unicodedata.normalize("NFC", str(text)).lower()
    return " " + re.sub(r"[^\w]+", " ", text).strip() + " "


def names(node):
    values = {node["name"]} | {a["name"] if isinstance(a, dict) else a for a in node.get("aliases", [])}
    # Tên quá ngắn (1 ký tự, ký hiệu) bắn bừa: bỏ, trừ khi là ký hiệu toán ≥ 2 ký tự.
    return {norm(v) for v in values if len(norm(v).strip()) >= 2}


for doc, chapter, version in CASES:
    payload = json.loads(Path(f"artifacts/graph/{doc}/v{version}/graph.json").read_text(encoding="utf-8"))
    gold_file = json.loads(Path(f"artifacts/a8-gold/{doc}-{chapter}-vang.json").read_text(encoding="utf-8"))
    gold = {(e["prerequisite"], e["target"]): e for e in gold_file["edges"]}
    targets = set(gold_file["targets"])
    nodes = {n["node_id"]: n for n in payload["nodes"]}
    quotes = {nid: [norm(ev["quote"]) for ev in n.get("evidence", []) if isinstance(ev, dict) and ev.get("quote")]
              for nid, n in nodes.items()}
    lexicon = {nid: names(n) for nid, n in nodes.items()}

    predicted = set()
    for b in targets:
        if b not in nodes:
            continue
        own = lexicon[b]
        for a in nodes:
            if a == b:
                continue
            # Không đếm khi tên A nằm trọn trong tên của chính B ("Ma trận" trong "Ma trận nghịch đảo" vẫn là cạnh thật,
            # nhưng tính riêng để thấy nó đóng góp bao nhiêu).
            if any(name in q for q in quotes[b] for name in lexicon[a]):
                predicted.add((a, b))
    machine = {(e["source"], e["target"]) for e in payload["requires_edges"]}
    s = score_edges(predicted, set(gold), targets=targets)
    by_kind = {}
    for pair, e in gold.items():
        by_kind.setdefault(e.get("evidence_kind"), [0, 0])
        by_kind[e.get("evidence_kind")][1] += 1
        by_kind[e.get("evidence_kind")][0] += pair in predicted
    union = score_edges(predicted | machine, set(gold), targets=targets)
    only_new = {p for p in predicted if p in gold and p not in machine}
    print(f"=== {doc}: bộ dò bắn {s['predicted']} cặp trong phạm vi | TP {s['true_positive']} | "
          f"P {s['precision']:.3f} R {s['recall']:.3f}")
    print(f"    recall theo loại bằng chứng vàng: " +
          ", ".join(f"{k}: {v[0]}/{v[1]}" for k, v in sorted(by_kind.items(), key=lambda kv: str(kv[0]))))
    print(f"    cạnh vàng bộ dò bắt được mà máy CHƯA có: {len(only_new)} | hợp với đồ thị máy: "
          f"P {union['precision']:.3f} R {union['recall']:.3f} (máy một mình R "
          f"{score_edges(machine, set(gold), targets=targets)['recall']:.3f})")
    evid = sum(1 for n in nodes.values() if quotes[n['node_id']])
    print(f"    node có câu căn cứ: {evid}/{len(nodes)}")
