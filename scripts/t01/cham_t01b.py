"""T-01b: chấm nhánh v3 và nhánh gộp trên hai cuốn giữ lại, CHỈ in trường số trong allowlist. 0 USD.

Nhánh v3 dùng `cham_tap_giu_lai.score` (vàng quy qua `identity_map` của đồ thị); nhánh gộp dùng `cham_gop.score` (vàng quy qua bảng chuyển
hướng của canonical). Hai bộ chấm dùng chung `score_roadmap_order` và `grade` trên rút gọn bắc cầu, nên cùng một thước.
Không in tên, câu, đường dẫn hay thông báo lỗi của bộ chấm: chuỗi bị loại ở bước `allow`.
Chạy từ gốc repo: .venv/Scripts/python.exe scripts/t01/cham_t01b.py <doc> <graph v3> <graph gộp>
"""
import json
import sys
from pathlib import Path

GOLD = {"d01-t01": "vang/d01-t01-chuong-36-40-vang-cuoi.json", "d01-t02": "vang/d01-t02-chuong-10-vang-cuoi.json"}
ALLOWED = {"graph_version", "canh_vang", "canh_vang_bi_gop_lam_mot", "Q6", "Q7", "Q7b", "truc_tiep_P", "truc_tiep_R", "bao_dong_P",
           "bao_dong_R", "bao_dong_dem", "dung", "du_doan", "vang", "khai_niem_day_hoc", "dich_vang", "dich_trong_day_hoc",
           "khai_niem_vang_khong_quy_duoc", "tu_choi_cham", "v3", "gop", "dich_cung_trang_thai", "dich_gop_chung_node"}


def allow(value):
    """Giữ đệ quy các khoá trong ALLOWED có giá trị số, bool hoặc None; bỏ mọi chuỗi và khoá lạ."""
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            if key not in ALLOWED:
                continue
            kept = allow(item)
            if kept is not _DROP:
                out[key] = kept
        return out
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return _DROP


_DROP = object()


def _paths():
    for path in ("src", "scripts/doc-lo-trinh", "scripts/pass-phu-ml", "scripts/gop-khau"):
        if path not in sys.path:
            sys.path.insert(0, path)


def _value(row):
    return None if row is None else row.get("value") if isinstance(row, dict) else row


def _in_sequence(payload, ids):
    sequence = set(payload["sequence"])
    return {node_id: node_id in sequence for node_id in ids}


def score_v3(doc, version, root=Path("artifacts")):
    _paths()
    from cham_tap_giu_lai import score
    from doc2roadmap.application.use_cases.a8_score import load_gold

    row = score(doc, GOLD[doc], root, version)
    payload = json.loads((root / "graph" / doc / f"v{version}" / "graph.json").read_text(encoding="utf-8"))
    identity = payload.get("identity_map", {})
    targets = load_gold(Path("artifacts/a8-gold") / GOLD[doc])["targets"]
    status = _in_sequence(payload, {identity.get(t, t) for t in targets})
    closure = row["edges_closure_reduced"]
    return {
        "graph_version": version, "canh_vang": row["gold_edges"], "canh_vang_bi_gop_lam_mot": row["identity_dropped_gold_edges"],
        "Q6": _value(row["Q6_learning_order_error"]), "Q7": row["Q7_mean_coverage"], "Q7b": row["Q7b_mean_precision"],
        "truc_tiep_P": _value(row["edges_direct_reduced"]["precision"]), "truc_tiep_R": _value(row["edges_direct_reduced"]["recall"]),
        "bao_dong_P": _value(closure["precision"]), "bao_dong_R": _value(closure["recall"]),
        "bao_dong_dem": {"dung": closure["precision"]["k"], "du_doan": closure["precision"]["n"], "vang": closure["recall"]["n"]},
        "khai_niem_day_hoc": len(payload["sequence"]), "dich_vang": len(targets),
        "dich_trong_day_hoc": sum(status[identity.get(t, t)] for t in targets),
        "dich_gop_chung_node": len(targets) - len({identity.get(t, t) for t in targets}),
    }, {t: status[identity.get(t, t)] for t in targets}


def score_gop(doc, version, root=Path("artifacts")):
    _paths()
    import cham_gop
    from doc2roadmap.application.use_cases.a8_score import _graph_canonical, load_gold
    from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore

    graph_path = root / "graph" / doc / f"v{version}" / "graph.json"
    payload = json.loads(graph_path.read_text(encoding="utf-8"))
    canonical = _graph_canonical(JsonArtifactStore(root), graph_path, payload).payload
    redirects = canonical.get("redirects", {})
    gold = load_gold(Path("artifacts/a8-gold") / GOLD[doc])
    known = {node["node_id"] for node in canonical["nodes"]}

    def current(node_id):
        seen = set()
        while node_id in redirects and node_id not in seen:
            seen.add(node_id)
            node_id = redirects[node_id]
        return node_id

    from doc2roadmap.application.use_cases.a8_score import merge_gold

    ids = set(gold["targets"]) | {x for edge in merge_gold([gold], mode="union") for x in edge}
    unmapped = sum(1 for node_id in ids if current(node_id) not in known)
    status = _in_sequence(payload, {current(t) for t in gold["targets"]})
    base = {"graph_version": version, "dich_vang": len(gold["targets"]), "khai_niem_vang_khong_quy_duoc": unmapped,
            "khai_niem_day_hoc": len(payload["sequence"]),
            "dich_trong_day_hoc": sum(status[current(t)] for t in gold["targets"]),
            "dich_gop_chung_node": len(gold["targets"]) - len({current(t) for t in gold["targets"]})}
    try:
        cham_gop.GOLD.update(GOLD)
        row = cham_gop.score(doc, str(root), version)
    except ValueError:  # bộ chấm từ chối khi có khái niệm vàng không quy được; không in thông báo vì có thể chứa tên
        return {**base, "tu_choi_cham": True}, {t: status[current(t)] for t in gold["targets"]}
    return {**base, "tu_choi_cham": False, "canh_vang": row["canh_vang"], "canh_vang_bi_gop_lam_mot": row["vang_bi_gop_lam_mot"],
            **{k: row[k] for k in ("Q6", "Q7", "Q7b", "truc_tiep_P", "truc_tiep_R", "bao_dong_P", "bao_dong_R", "bao_dong_dem")}}, \
        {t: status[current(t)] for t in gold["targets"]}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    doc, v3, gop = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    if doc not in GOLD:
        raise SystemExit("chỉ dùng cho d01-t01, d01-t02")
    a, status_a = score_v3(doc, v3)
    b, status_b = score_gop(doc, gop)
    same = sum(status_a[t] == status_b[t] for t in status_a)
    print(json.dumps(allow({"v3": a, "gop": b, "dich_cung_trang_thai": same})))


if __name__ == "__main__":
    main()
