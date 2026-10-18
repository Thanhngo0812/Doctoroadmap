"""In tên và mô tả module của đồ thị A10 mới nhất cho SÁU cuốn phát triển (không bao giờ T-01). Dùng: python in_ten_module_sau_cuon.py <tệp ra>"""
import json, sys
from doc2roadmap.composition import build_artifact_store
from doc2roadmap.application.phase_b.retrieval import load_learning_graph
DOCS = ["doc-1", "nhap-mon-ml", "naive-bayes", "doc-6", "xstk-ch3-1", "doc-4"]
store = build_artifact_store()
out = []
for doc in DOCS:
    g = load_learning_graph(store, doc)
    p = g.payload
    man = store.load_graph(doc, p["graph_version"]).manifest
    out.append(f"##### {doc} v{p['graph_version']} chain={man.get('config',{}).get('upstream_chain')} contract={p.get('module_naming_contract')}")
    nodes = {n["node_id"]: n for n in p["nodes"]} if isinstance(p["nodes"], list) else p["nodes"]
    for m in p["modules"]:
        names = [ (nodes.get(n) or {}).get("display_name") or (nodes.get(n) or {}).get("name") for n in m["node_ids"]]
        desc = " | ".join(d["text"] for d in m.get("description", [])) if isinstance(m.get("description"), list) else m.get("description")
        out.append(f"[{m['index']+1}] {m['module_id']} sc={m.get('section_code')!r} T({m.get('title_source')})={m.get('title')!r} D({m.get('description_source')})={desc!r} flags={m.get('naming_flags')}")
        out.append("     concepts: " + "; ".join(str(x) for x in names))
open(sys.argv[1], "w", encoding="utf-8").write("\n".join(out))
print("ok", len(out))
