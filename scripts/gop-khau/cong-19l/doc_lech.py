"""Cổng 19l: đọc chỗ lệch E4 giữa hai lượt (cạnh vàng bao đóng tìm thấy / bỏ lỡ), theo tên khái niệm. 0 USD.
Chạy từ gốc repo: .venv/Scripts/python.exe scripts/gop-khau/cong-19l/doc_lech.py <doc> <kho A> <graph A> <kho B> <graph B>"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "scripts/doc-lo-trinh")
sys.path.insert(0, "scripts/gop-khau")
from cham_gop import GOLD  # noqa: E402
from thu_cua_so_rong_a8 import reduced  # noqa: E402
from doc2roadmap.application.use_cases.a8_score import _graph_canonical, load_gold, merge_gold  # noqa: E402
from doc2roadmap.domain.gold_scoring import transitive_closure  # noqa: E402
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore  # noqa: E402


def run(doc, root, version, gold):
    path = Path(root) / "graph" / doc / f"v{version}" / "graph.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    redirects = _graph_canonical(JsonArtifactStore(Path(root)), path, payload).payload.get("redirects", {})
    def rep(node_id):
        while node_id in redirects:
            node_id = redirects[node_id]
        return node_id
    present = {n["node_id"] for n in [*payload["nodes"], *payload.get("mentioned_nodes", [])]}
    names = {n["node_id"]: n["name"] for n in [*payload["nodes"], *payload.get("mentioned_nodes", [])]}
    targets = {rep(t) for t in gold["targets"]} & present
    sequence = set(payload["sequence"])
    gold_edges = {(rep(a), rep(b)) for a, b in merge_gold([gold], mode="union")}
    gold_edges = {(a, b) for a, b in gold_edges if a != b and a in targets and b in targets}
    hard = {(e["source"], e["target"]) for e in reduced(payload["requires_edges"])}
    predicted = {(a, b) for a, b in hard if a in targets and b in targets}
    main = {(e["source"], e["target"]) for e in payload.get("main_edges", []) if not e.get("soft")}
    found = transitive_closure(gold_edges) & transitive_closure(predicted)
    # khoá theo id vàng gốc để so hai lượt có canonical khác nhau
    by_gold = {}
    for a, b in merge_gold([gold], mode="union"):
        pair = (rep(a), rep(b))
        if pair in gold_edges:
            by_gold[(a, b)] = {"found_closure": pair in found, "found_direct": pair in predicted,
                               "in_main": pair in main, "src_in_seq": pair[0] in sequence, "dst_in_seq": pair[1] in sequence,
                               "names": (names.get(pair[0]), names.get(pair[1]))}
    return by_gold, {"targets": len(targets), "gold_edges": len(gold_edges), "found_closure_gold_direct": sum(v["found_closure"] for v in by_gold.values())}


doc = sys.argv[1]
gold = load_gold(Path("artifacts/a8-gold") / GOLD[doc])
a, sa = run(doc, sys.argv[2], int(sys.argv[3]), gold)
b, sb = run(doc, sys.argv[4], int(sys.argv[5]), gold)
print("A", sa, "| B", sb)
for key in sorted(set(a) | set(b)):
    x, y = a.get(key), b.get(key)
    fx, fy = bool(x and x["found_closure"]), bool(y and y["found_closure"])
    if fx != fy:
        row = x or y
        print(("chỉ A" if fx else "chỉ B"), "|", " → ".join(str(n) for n in row["names"]),
              "| A:", None if not x else {k: x[k] for k in ("found_direct", "in_main", "src_in_seq", "dst_in_seq")},
              "| B:", None if not y else {k: y[k] for k in ("found_direct", "in_main", "src_in_seq", "dst_in_seq")})
