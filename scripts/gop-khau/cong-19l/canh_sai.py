"""Cổng 19l: liệt kê cạnh cứng (rút gọn bắc cầu) giữa các đích vàng mà vàng không có (kể cả qua bao đóng), cho hai lượt. 0 USD.
Chạy: .venv/Scripts/python.exe scripts/gop-khau/cong-19l/canh_sai.py <doc> <kho A> <graph A> <kho B> <graph B>"""
import json, sys
from pathlib import Path
sys.path.insert(0, "src"); sys.path.insert(0, "scripts/doc-lo-trinh"); sys.path.insert(0, "scripts/gop-khau")
from cham_gop import GOLD
from thu_cua_so_rong_a8 import reduced
from doc2roadmap.application.use_cases.a8_score import _graph_canonical, load_gold, merge_gold
from doc2roadmap.domain.gold_scoring import transitive_closure
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore

def wrong(doc, root, version, gold):
    path = Path(root) / "graph" / doc / f"v{version}" / "graph.json"
    p = json.loads(path.read_text(encoding="utf-8"))
    red = _graph_canonical(JsonArtifactStore(Path(root)), path, p).payload.get("redirects", {})
    def rep(x):
        while x in red: x = red[x]
        return x
    names = {n["node_id"]: n["name"] for n in [*p["nodes"], *p.get("mentioned_nodes", [])]}
    targets = {rep(t) for t in gold["targets"]} & set(names)
    g = {(rep(a), rep(b)) for a, b in merge_gold([gold], mode="union")}
    g = transitive_closure({(a, b) for a, b in g if a != b and a in targets and b in targets})
    main = {(e["source"], e["target"]) for e in p["main_edges"] if not e.get("soft")}
    pred = {(e["source"], e["target"]) for e in reduced(p["requires_edges"])}
    pred = {(a, b) for a, b in pred if a in targets and b in targets}
    return {(names[a], names[b]): ("chính" if (a, b) in main else "phụ ML") for a, b in pred if (a, b) not in g}

doc = sys.argv[1]; gold = load_gold(Path("artifacts/a8-gold") / GOLD[doc])
A = wrong(doc, sys.argv[2], int(sys.argv[3]), gold); B = wrong(doc, sys.argv[4], int(sys.argv[5]), gold)
print("sai A", len(A), "| sai B", len(B))
for k in sorted(set(A) - set(B)): print("chỉ A:", " → ".join(k), "|", A[k])
for k in sorted(set(B) - set(A)): print("chỉ B:", " → ".join(k), "|", B[k])
