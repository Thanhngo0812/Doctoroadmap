"""0 USD: so câu ứng viên neo doc-4 giữa bản nhãn v6 (canonical cổng dùng) và v8 (05b)."""
import sys
from pathlib import Path
sys.path.insert(0, "scripts/a2-de-cuong")
from mo_phong_neo import GOLD  # noqa: E402
from doc2roadmap.application.use_cases.a8_score import load_gold, merge_gold  # noqa: E402
from doc2roadmap.application.use_cases.canonical_anchors import prepare_anchors  # noqa: E402
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore  # noqa: E402

doc = "doc-4"
store = JsonArtifactStore(Path("artifacts"))
canon = store.load_latest_canonical(doc)
assert canon.manifest["config"]["anchor_chunks_version"] == 6
STRIP = {"teaching_status", "anchor", "anchor_candidate_id", "teaching_chunk_ids", "teaching_order_index", "teaching_conflict",
         "mentioned_in", "defining_chunk_ids", "defining_chunk_ids_source"}


def core(version):
    nodes = []
    for n in canon.payload["nodes"]:
        m = {k: v for k, v in n.items() if k not in STRIP}
        if n.get("defining_chunk_ids_source") is not None:
            m["defining_chunk_ids"] = list(n["defining_chunk_ids_source"])
        nodes.append(m)
    return prepare_anchors(nodes, list(store.load_chunks(doc, version).result.chunks))


before, after = core(6), core(8)
log = {r["input"]["node_id"]: r["input"]["candidates"] for r in canon.payload.get("anchor_decision_log", [])
       if r.get("stage") == "anchor" and r.get("valid", True)}
sig = lambda cands: [(c["chunk_id"], c["sentence"]) for c in cands]  # noqa: E731
print("v6 khớp nhật ký:", sum(sig(v) == sig(before.candidates_of.get(k, [])) for k, v in log.items()), "/", len(log))
changed = [k for k in after.candidates_of if sig(after.candidates_of[k]) != sig(before.candidates_of.get(k, []))]
byid = {n["node_id"]: n for n in canon.payload["nodes"]}
red = canon.payload.get("redirects", {})
cur = lambda i: cur(red[i]) if i in red else i  # noqa: E731
gold = load_gold(Path("artifacts/a8-gold") / GOLD[doc])
gids = {cur(i) for i in set(gold["targets"]) | {x for e in merge_gold([gold], mode="union") for x in e}}
print("khái niệm đổi ứng viên:", len(changed), "| trong vàng:", len(set(changed) & gids),
      "| từ không có ứng viên sang có:", sum(1 for k in changed if not before.candidates_of.get(k)))
for k in changed:
    print(f"  {byid[k]['name'][:50]!r} {byid[k].get('teaching_status')} ứng viên "
          f"{len(before.candidates_of.get(k, []))}->{len(after.candidates_of[k])}{' (vàng)' if k in gids else ''}")
