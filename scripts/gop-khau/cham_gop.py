"""Vé 17i: chấm lộ trình chuỗi gộp trên vàng A8 cũ, quy id vàng qua bảng chuyển hướng của canonical mà đồ thị dùng. 0 USD.

Cùng phép đo với `scripts/doc-lo-trinh/cham_tap_giu_lai.py` (Q6, Q7, Q7b, P/R cạnh trực tiếp và bao đóng trên rút gọn bắc cầu), khác ở chỗ
bản đồ áp lên vàng là bảng chuyển hướng canonical (`remap_gold` của vé 17h) thay cho `identity_map`. Bộ vàng có khái niệm không quy được thì
từ chối chấm và liệt kê. Chạy từ gốc repo:
  .venv/Scripts/python.exe scripts/gop-khau/cham_gop.py <doc> <phiên bản graph stages> [--kho=tmp/v4-17i/artifacts]
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "scripts/doc-lo-trinh")
sys.path.insert(0, "scripts/pass-phu-ml")
from cham_tap_giu_lai import nearest_baseline, ratio  # noqa: E402
from thu_cua_so_rong_a8 import grade, reduced  # noqa: E402
from doc2roadmap.application.use_cases.a8_score import _graph_canonical, load_gold, merge_gold, score_roadmap_order  # noqa: E402
from doc2roadmap.domain.gold_redirects import remap_gold  # noqa: E402
from doc2roadmap.domain.gold_scoring import target_coverage, target_precision  # noqa: E402
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore  # noqa: E402

GOLD = {"doc-1": "doc-1-10-12-vang.json", "xstk-ch3-1": "xstk-ch3-1-10-13-vang.json", "doc-4": "doc-4-chuong-8-vang.json"}


def score(doc, root, version):
    graph_path = Path(root) / "graph" / doc / f"v{version}" / "graph.json"
    payload = json.loads(graph_path.read_text(encoding="utf-8"))
    gold_path = Path("artifacts/a8-gold") / GOLD[doc]
    store = JsonArtifactStore(Path(root))
    report = score_roadmap_order(graph_path, [gold_path], remap_gold_ids=True, store=store)
    redirects = _graph_canonical(store, graph_path, payload).payload.get("redirects", {})
    gold = load_gold(gold_path)
    present = {node["node_id"] for node in [*payload["nodes"], *payload.get("mentioned_nodes", [])]}
    ids = set(gold["targets"]) | {node_id for edge in merge_gold([gold], mode="union") for node_id in edge}
    mapping = {}
    for node_id in ids:  # bộ chấm phía trên đã từ chối vòng chuyển hướng và id không quy được
        current = node_id
        while current in redirects:
            current = redirects[current]
        mapping[node_id] = current
    mapped = remap_gold(merge_gold([gold], mode="union"), gold["targets"], redirects, present)
    order = report["gold_order"]
    sequence = payload["sequence"]
    hard = [edge for edge in payload["requires_edges"] if not edge.get("soft")
            and edge["source"] in set(sequence) and edge["target"] in set(sequence)]
    n, baseline = nearest_baseline(sequence, len(hard))
    direct, closure = grade(reduced(payload["requires_edges"]), gold, mapping, present)
    coverage = report["target_coverage"]
    value = lambda row: None if row is None else round(row["value"], 3) if isinstance(row, dict) else round(row, 3)  # noqa: E731
    closure_p = ratio(closure["true_positive"], closure["predicted"])
    closure_r = ratio(closure["true_positive"], closure["gold"])
    return {
        "doc": doc, "graph_version": version, "canh_vang": report["gold_edge_count"],
        "vang_bi_gop_lam_mot": report.get("redirect_dropped_gold_edges"),
        "Q6": value(ratio(order["violated"] + order["same_stage"] + order["out_of_scope"], report["gold_edge_count"])),
        "Q7": value(coverage["mean_coverage"]), "Q7b": value(report["target_precision"]["mean_precision"]),
        "co_so_n_gan": {"Q7": value(target_coverage(mapped["edges"], baseline, mapped["targets"])["mean_coverage"]),
                        "Q7b": value(target_precision(mapped["edges"], baseline, mapped["targets"])["mean_precision"])},
        "truc_tiep_P": value(ratio(direct["true_positive"], direct["predicted"])),
        "truc_tiep_R": value(ratio(direct["true_positive"], direct["gold"])),
        "bao_dong_P": value(closure_p), "bao_dong_R": value(closure_r),
        "bao_dong_dem": {"dung": closure["true_positive"], "du_doan": closure["predicted"], "vang": closure["gold"]},
        "canh_cung_A10": len(hard), "khai_niem_day_hoc": len(sequence),
    }


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    options = dict(arg[2:].split("=", 1) for arg in sys.argv[1:] if arg.startswith("--") and "=" in arg)
    doc, version = [arg for arg in sys.argv[1:] if not arg.startswith("--")][:2]
    print(json.dumps(score(doc, options.get("kho", "tmp/v4-17i/artifacts"), int(version)), ensure_ascii=False))


if __name__ == "__main__":
    main()
