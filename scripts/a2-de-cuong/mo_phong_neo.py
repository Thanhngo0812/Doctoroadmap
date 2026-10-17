"""Mô phỏng 0 USD: câu ứng viên neo trên canonical chuỗi gộp mới nhất, với vai trò hiện tại và với vai trò sửa.

Chỉ đọc kho; không gọi mô hình. Dùng cho tài liệu phát triển (không chạy trên T-01).
"""
import copy, json, sys
from collections import Counter
from pathlib import Path

from doc2roadmap.application.use_cases.canonical_anchors import prepare_anchors
from doc2roadmap.application.use_cases.a8_score import load_gold, merge_gold
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore

GOLD = {"doc-1": "doc-1-10-12-vang.json", "xstk-ch3-1": "xstk-ch3-1-10-13-vang.json", "doc-4": "doc-4-chuong-8-vang.json"}
STRIP = {"teaching_status", "anchor", "anchor_candidate_id", "teaching_chunk_ids", "teaching_order_index", "teaching_conflict",
         "mentioned_in", "defining_chunk_ids", "defining_chunk_ids_source"}


def load(doc):
    store = JsonArtifactStore(Path("artifacts"))
    canon = store.load_latest_canonical(doc)
    assert canon.manifest["config"].get("upstream_chain") == "gop", doc
    cand = store._read(Path("artifacts/candidates") / doc / f"v{canon.manifest['config']['candidate_version']}" / "manifest.json")
    chunks = store.load_role_chunks(doc, cand["upstream_version"])
    assert chunks.version == canon.manifest["config"]["anchor_chunks_version"], (chunks.version,)
    return store, canon, chunks


def run(doc, relabel=None):
    store, canon, stored = load(doc)
    chunks = [copy.copy(c) for c in stored.result.chunks]
    if relabel:
        for c in chunks:
            if relabel(c):
                c.role = "noi_dung"
    nodes = []
    for n in canon.payload["nodes"]:
        m = {k: v for k, v in n.items() if k not in STRIP}
        if n.get("defining_chunk_ids_source") is not None:
            m["defining_chunk_ids"] = list(n["defining_chunk_ids_source"])
        nodes.append(m)
    core = prepare_anchors(nodes, chunks)
    return canon, core, {c.chunk_id: c for c in chunks}


if __name__ == "__main__":
    doc = sys.argv[1]
    canon, core, by_id = run(doc)
    log = {row["input"]["node_id"]: row["input"]["candidates"] for row in canon.payload.get("anchor_decision_log", [])
           if row.get("stage") == "anchor" and row.get("valid", True)}
    same = sum(1 for k, v in log.items() if [c["chunk_id"] + c["sentence"] for c in v]
               == [c["chunk_id"] + c["sentence"] for c in core.candidates_of.get(k, [])])
    print(doc, "ứng viên trùng nhật ký:", same, "/", len(log), "| khái niệm học được:", len(core.candidates_of))
