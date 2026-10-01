"""Chấm tự động một lộ trình `stages` theo giao thức T10/07 v2 (`task/v3-lo-trinh-doc-duoc/T10-07v2-giao-thuc-tap-giu-lai.md`).

Một lệnh, một bảng, phép đo cố định trước khi chạy tập giữ lại; dùng y hệt cho tài liệu phát triển để có mức so sánh:
  - Q6 `learning_order_error`, Q7 độ phủ tổ tiên tới đích (+ tỉ lệ đích trọn), Q7b độ chính xác tổ tiên trong chương — `score_roadmap_order`;
  - đường cơ sở "n gần nhất" (bài học v2-06): nối mỗi khái niệm với n khái niệm đứng ngay trước nó trong dãy học, n chọn sao cho số cạnh
    xấp xỉ số cạnh cứng của máy; báo Q7/Q7b của đường cơ sở cạnh Q7/Q7b của máy;
  - P/R cạnh trực tiếp và theo bao đóng, hai đầu thuộc đích vàng, trên **rút gọn bắc cầu** của cạnh cứng (đúng các cạnh hiện ở "cần:");
  - Q2: xung đột danh tính còn mở;
  - tỉ lệ kèm khoảng tin cậy Wilson 95% khi là tỉ lệ đếm được.
Không gọi mô hình. Không in nội dung nhãn vàng, chỉ in số đếm. Chạy từ gốc repo:
  .venv/Scripts/python.exe scripts/doc-lo-trinh/cham_tap_giu_lai.py <doc> <tệp vàng> [--goc=<kho>] [--phien-ban=<v>] [--json=<tệp>]
"""
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "scripts/doc-lo-trinh")
from thu_cua_so_rong_a8 import grade, reduced  # noqa: E402
from doc2roadmap.application.use_cases.a8_score import load_gold, merge_gold, score_roadmap_order  # noqa: E402
from doc2roadmap.domain.gold_scoring import target_coverage, target_precision  # noqa: E402


def wilson(k, n, z=1.96):
    if not n:
        return None, None
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, centre - half), min(1.0, centre + half)


def ratio(k, n):
    if not n:
        return {"k": k, "n": n, "value": None, "wilson95": [None, None]}
    low, high = wilson(k, n)
    return {"k": k, "n": n, "value": k / n, "wilson95": [low, high]}


def nearest_baseline(sequence, edge_count):
    """Nối mỗi khái niệm với n khái niệm đứng ngay trước nó; n = làm tròn(số cạnh máy / số khái niệm), tối thiểu 1."""
    n = max(1, round(edge_count / max(len(sequence), 1)))
    return n, {(sequence[i - j], sequence[i]) for i in range(len(sequence)) for j in range(1, n + 1) if i - j >= 0}


def score(doc, gold_file, root, version):
    graph_path = root / "graph" / doc / f"v{version}" / "graph.json"
    payload = json.loads(graph_path.read_text(encoding="utf-8"))
    gold_path = Path("artifacts/a8-gold") / gold_file
    report = score_roadmap_order(graph_path, [gold_path])
    order = report["gold_order"]
    identity = payload.get("identity_map", {})
    gold = load_gold(gold_path)
    edges = {(identity.get(a, a), identity.get(b, b)) for a, b in merge_gold([gold], mode="union")}
    edges = {(a, b) for a, b in edges if a != b}
    targets = sorted({identity.get(target, target) for target in gold["targets"]})
    sequence = payload["sequence"]
    hard = [edge for edge in payload["requires_edges"] if not edge.get("soft")
            and edge["source"] in set(sequence) and edge["target"] in set(sequence)]
    n, baseline = nearest_baseline(sequence, len(hard))
    present = {node["node_id"] for node in [*payload["nodes"], *payload.get("mentioned_nodes", [])]}
    direct, closure = grade(reduced(payload["requires_edges"]), gold, identity, present)
    coverage = report["target_coverage"]
    return {
        "doc_id": doc, "graph": str(graph_path), "gold": gold_file, "inputs": report["inputs"],
        "gold_edges": report["gold_edge_count"], "identity_dropped_gold_edges": report["identity_dropped_gold_edges"],
        "Q6_learning_order_error": ratio(order["violated"] + order["same_stage"] + order["out_of_scope"], report["gold_edge_count"]),
        "Q6_buckets": {key: order[key] for key in ("respected", "violated", "same_stage", "out_of_scope")},
        "Q7_mean_coverage": coverage["mean_coverage"],
        "Q7_complete_targets": ratio(coverage["complete"], coverage["targets"]),
        "Q7b_mean_precision": report["target_precision"]["mean_precision"],
        "nearest_baseline": {"n": n, "edges": len(baseline), "machine_hard_edges": len(hard),
                             "Q7_mean_coverage": target_coverage(edges, baseline, targets)["mean_coverage"],
                             "Q7b_mean_precision": target_precision(edges, baseline, targets)["mean_precision"]},
        "edges_direct_reduced": {"precision": ratio(direct["true_positive"], direct["predicted"]),
                                 "recall": ratio(direct["true_positive"], direct["gold"])},
        "edges_closure_reduced": {"precision": ratio(closure["true_positive"], closure["predicted"]),
                                  "recall": ratio(closure["true_positive"], closure["gold"])},
        "Q2_open_identity": {"groups": len(payload.get("identity_open_groups", [])),
                             "pairs": len(payload.get("identity_open_pairs", []))},
    }


def show(value):
    if isinstance(value, dict) and "k" in value:
        if value["value"] is None:
            return f"{value['k']}/{value['n']}"
        low, high = value["wilson95"]
        return f"{value['k']}/{value['n']} = {value['value']:.3f} (Wilson 95% {low:.3f}–{high:.3f})"
    return "—" if value is None else f"{value:.3f}"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    doc, gold_file = args[0], args[1]
    root = Path(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--goc=")), "artifacts"))
    version = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--phien-ban=")), None)
    if version is None:
        version = max(int(p.name[1:]) for p in (root / "graph" / doc).glob("v*")
                      if json.loads((p / "manifest.json").read_text(encoding="utf-8")).get("stage") == "stages"
                      and "modules" in json.loads((p / "graph.json").read_text(encoding="utf-8")))
    result = score(doc, gold_file, root, version)
    base = result["nearest_baseline"]
    print(f"# {doc} — {result['graph']} — {result['gold_edges']} cạnh vàng (sau bản đồ danh tính)")
    print(f"  Q6 lỗi thứ tự học           {show(result['Q6_learning_order_error'])}  {result['Q6_buckets']}")
    print(f"  Q7 độ phủ tổ tiên (TB)       {show(result['Q7_mean_coverage'])}   | n gần nhất (n={base['n']}, {base['edges']} cạnh so "
          f"{base['machine_hard_edges']} cạnh máy): {show(base['Q7_mean_coverage'])}")
    print(f"  Q7 đích trọn                 {show(result['Q7_complete_targets'])}")
    print(f"  Q7b độ chính xác tổ tiên (TB) {show(result['Q7b_mean_precision'])}  | n gần nhất: {show(base['Q7b_mean_precision'])}")
    print(f"  cạnh trực tiếp (rút gọn)     P {show(result['edges_direct_reduced']['precision'])} · "
          f"R {show(result['edges_direct_reduced']['recall'])}")
    print(f"  cạnh bao đóng (rút gọn)      P {show(result['edges_closure_reduced']['precision'])} · "
          f"R {show(result['edges_closure_reduced']['recall'])}")
    print(f"  Q2 danh tính còn mở          nhóm {result['Q2_open_identity']['groups']}, cặp {result['Q2_open_identity']['pairs']}")
    out = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--json=")), None)
    if out:
        Path(out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
