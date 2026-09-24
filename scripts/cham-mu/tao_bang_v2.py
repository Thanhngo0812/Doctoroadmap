"""Bảng chấm mù vòng hai T11 (cổng 2 của vé 06): mọi cạnh ngầm tới khái niệm đích của chương vàng.

Trộn ba loại, đảo chiều ngẫu nhiên như T1: cạnh ngầm (`fp` nếu không có trong vàng, `tp` nếu có — cờ `implicit` giữ
nguồn), thêm vài cạnh vàng khác để đo độ tin của chính lần chấm, và cặp ngẫu nhiên không có cạnh. Dùng lại sheet Khái niệm
của bảng gán vàng A1 và khuôn của `tao_bang.py`, nên `cham_bang.py` chấm được như T1.

Chạy từ gốc repo:  .venv/Scripts/python.exe scripts/cham-mu/tao_bang_v2.py
"""
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, "scripts/cham-mu")
from tao_bang import concept_sheet, write_sheet  # noqa: E402

SEED = 20260925
CASES = [
    # (tài liệu, chương vàng, stages sau pass cạnh ngầm, số cạnh vàng khác lấy thêm, số cặp ngẫu nhiên)
    ("doc-1", "10-12", 29, 5, 8),
    ("doc-2", "98-115", 23, 5, 8),
]


def build(doc, chapter, version, extra_gold, random_sample, rng):
    graph_path = Path(f"artifacts/graph/{doc}/v{version}/graph.json")
    gold_path = Path(f"artifacts/a8-gold/{doc}-{chapter}-vang.json")
    payload = json.loads(graph_path.read_text(encoding="utf-8"))
    gold_file = json.loads(gold_path.read_text(encoding="utf-8"))
    identity = payload.get("identity_map", {})
    targets = {identity.get(t, t) for t in gold_file["targets"]}
    gold = {(identity.get(e["prerequisite"], e["prerequisite"]), identity.get(e["target"], e["target"]))
            for e in gold_file["edges"]}
    gold = {pair for pair in gold if pair[0] != pair[1]}
    implicit = {(e["source"], e["target"]) for e in payload["requires_edges"]
                if e.get("origin") == "implicit_pass" and e["target"] in targets}
    sheet_path, header, body, by_node = concept_sheet(doc, chapter)
    machine = {(e["source"], e["target"]) for e in payload["requires_edges"]}

    fp = sorted(implicit - gold)
    tp = sorted(implicit & gold)
    others = sorted(gold - implicit)
    tp_extra = rng.sample(others, min(extra_gold, len(others)))
    touched = machine | gold | {(b, a) for a, b in machine | gold}
    sources = sorted({a for a, _ in implicit | gold} & set(by_node))
    pool = [(a, b) for a in sources for b in sorted(targets & set(by_node)) if a != b and (a, b) not in touched]
    randoms = rng.sample(pool, random_sample)

    items = []
    for category, pairs, is_implicit in (("fp", fp, True), ("tp", tp, True), ("tp", tp_extra, False),
                                         ("random", randoms, False)):
        for a, b in pairs:
            flip = rng.random() < 0.5
            x, y = (b, a) if flip else (a, b)
            items.append({"category": category, "implicit": is_implicit, "x": x, "y": y,
                          "machine": [a, b] if category != "random" else None})
    counts = {"implicit_in_scope": len(implicit), "fp": len(fp), "tp_implicit": len(tp), "tp_extra": len(tp_extra),
              "random": len(randoms)}
    out, key_path = write_sheet(doc, items, rng, header, body, by_node, sheet_path, graph_path, gold_path, counts,
                                name=f"cham-mu-v2-{doc}")
    return out, key_path, counts


if __name__ == "__main__":
    rng = random.Random(SEED)
    for case in CASES:
        out, key_path, counts = build(*case, rng)
        print(f"{case[0]}: {out} | khoá {key_path} | {counts}")
