"""Vé 17i: chi phí một lượt chạy từ đầu (không cache) của các bước trước A8, chuỗi v3 so với chuỗi gộp. 0 USD.

Cộng token của mọi lời gọi có ghi `usage` trong nhật ký, kể cả lời được tái dùng (nhật ký giữ `usage` gốc), theo giá trong mã
(flash-lite: 0,25 USD/triệu token vào, 1,5 USD/triệu token ra):
- v3 = canonical v3 (A4/A5) + provenance + neo C8 + xác minh kiến thức nền + danh tính + xác minh danh tính, đọc ở artifact `identity`;
- gộp = canonical chuỗi gộp mới nhất trong kho riêng.
Chạy từ gốc repo:  .venv/Scripts/python.exe scripts/gop-khau/chi_phi_lanh.py <doc> [...] [--kho-gop=tmp/v4-17i/artifacts]
"""
import glob
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from so_chuoi_gop import V3, latest_gop, read  # noqa: E402

PRICE = (0.25, 1.5)


def usage_cost(rows, by):
    calls, cost = Counter(), Counter()
    for row in rows:
        usage = row.get("usage")
        if not isinstance(usage, dict) or "input_hash" not in row:
            continue
        tokens_in = int(usage.get("promptTokenCount", 0))
        tokens_out = int(usage.get("candidatesTokenCount", 0)) + int(usage.get("thoughtsTokenCount", 0))
        calls[by(row)] += 1
        cost[by(row)] += (tokens_in * PRICE[0] + tokens_out * PRICE[1]) / 1e6
    return calls, cost


def current_anchor_rows(rows, node_ids):
    """Nhật ký neo mang theo hàng của các lượt trước; chỉ giữ hàng cuối của mỗi khái niệm còn trong tập node hiện tại."""
    last = {}
    for row in rows:
        node_id = (row.get("input") or {}).get("node_id")
        if node_id in node_ids and "usage" in row:
            last[node_id] = row
    return list(last.values())


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    options = dict(arg[2:].split("=", 1) for arg in sys.argv[1:] if arg.startswith("--") and "=" in arg)
    for doc in [arg for arg in sys.argv[1:] if not arg.startswith("--")]:
        canonical_version, _, identity_version, _ = V3[doc]
        v3_canonical = read(f"artifacts/canonical/{doc}/v{canonical_version}/canonical.json")
        identity = read(f"artifacts/graph/{doc}/v{identity_version}/graph.json")
        v3_ids = {n["node_id"] for n in [*identity["nodes"], *identity.get("merged_nodes", [])]}
        rows = [("A4/A5", r) for r in v3_canonical["decision_log"]]
        for key, part in (("provenance_decision_log", "provenance"), ("identity_decision_log", "danh tinh"),
                          ("identity_verify_decision_log", "danh tinh")):
            rows += [(part, r) for r in identity.get(key, [])]
        for key in ("anchor_decision_log", "anchor_prior_verify_decision_log"):
            rows += [("neo C8", r) for r in current_anchor_rows(identity.get(key, []), v3_ids)]
        calls, cost = usage_cost([dict(r, _part=p) for p, r in rows], lambda r: r["_part"])
        gop, _ = latest_gop(options.get("kho-gop", "tmp/v4-17i/artifacts"), doc)
        gop_ids = {n["node_id"] for n in gop["nodes"]}
        gop_rows = [*gop["decision_log"],
                    *current_anchor_rows([r for r in gop.get("anchor_decision_log", []) if r.get("stage") == "anchor"], gop_ids),
                    *current_anchor_rows(gop.get("anchor_prior_verify_decision_log", []), gop_ids)]
        gop_calls, gop_cost = usage_cost(gop_rows, lambda r: r.get("stage"))
        print(json.dumps({"doc": doc,
                          "v3": {"loi_goi": sum(calls.values()), "usd": round(sum(cost.values()), 3),
                                 "theo_phan": {k: [calls[k], round(cost[k], 3)] for k in calls}},
                          "gop": {"loi_goi": sum(gop_calls.values()), "usd": round(sum(gop_cost.values()), 3),
                                  "theo_phan": {k: [gop_calls[k], round(gop_cost[k], 3)] for k in gop_calls}}},
                         ensure_ascii=False))


if __name__ == "__main__":
    main()
