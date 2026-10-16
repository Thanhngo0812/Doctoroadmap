"""Tra tên nhóm ứng viên (id node ban đầu của A4) cho nhật ký nomination_pair của canonical chuỗi gộp. 0 USD."""
import json, sys, glob
sys.path.insert(0, "src")
from pathlib import Path
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore
from doc2roadmap.application.use_cases.extract_entities import DocumentExtraction
from doc2roadmap.domain.canonical import group_names, build_nodes

def group_name_map(root, doc):
    store = JsonArtifactStore(Path(root))
    source = store.load_latest_candidates(doc)
    chunks = store.load_chunks(doc, source.manifest["upstream_version"])
    groups = group_names(DocumentExtraction.from_payload(source.payload).entities)
    nodes, _, _ = build_nodes(groups, chunks.result.normalized_full_text, store.load_type_aliases())
    return {n["node_id"]: n["name"] for n in nodes}

def latest(root, doc):
    v = sorted(glob.glob(f"{root}/canonical/{doc}/v*"), key=lambda p: int(p.split("v")[-1]))[-1]
    return json.load(open(v + "/canonical.json", encoding="utf-8"))

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    root, doc, *pairs = sys.argv[1:]
    names = group_name_map(root, doc)
    c = latest(root, doc)
    rows = [r for r in c["decision_log"] if r.get("stage") == "nomination_pair"]
    for pair in pairs:
        a, b = pair.split("|")
        hit = [r for r in rows if {names.get(r["left"]), names.get(r["right"])} == {a, b}]
        print(doc, a, "|", b, "->", [(r["verdict"], r["sources"], [e["edge_type"] for e in r.get("relations", [])],
                                       (r.get("verification") or {}).get("relation")) for r in hit] or "không có cặp đề cử")
