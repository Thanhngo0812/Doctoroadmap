"""Dựng fixture `kho-phat-lai/` bằng cách CẮT chuỗi pass phụ -> A9 của xstk-ch3-1 (tập phát triển) quanh 17 node, rồi CHẠY LẠI A9, đặt tên, A10
bằng mã pipeline hiện tại trên bản cắt. Fixture vì thế tự nhất quán: phát lại không đổi cạnh phải ra đúng `sequence` và `requires_edges` đã lưu.

Chạy một lần để ghi lại; kho chung chỉ được ĐỌC. Fixture không chứa gì của tập giữ lại.
Cách cắt (đều có chủ ý, để thử các nhánh thật):
- 17 node = 7 đầu mút của 4 cạnh bị R17 làm mềm trong A10 v63 (nên tắt R17 có tác dụng) + 10 hàng xóm nhiều cạnh nhất; chỉ giữ cạnh có cả hai đầu trong tập;
- chunks: chỉ các chunk được node hay cạnh nhắc tới, giữ nguyên `order_index`; sections: chuỗi cha của các chunk đó;
- vector node cắt theo node; canonical thay bằng bản tối thiểu (không cạnh canonical, không hoãn);
- chuỗi dựng trong kho mới: v1 clusters (vector), v2 edges, v3 A9, v4 đặt tên, v5 A10, v6 đặt tên module (mô phỏng Pha B).
Cách chạy: python tao_kho_phat_lai.py <đường dẫn artifacts chung> <thư mục đích>   (PYTHONPATH có `src`)
"""
import json
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace

DOC = "xstk-ch3-1"
PHIEN_BAN_EDGES, PHIEN_BAN_A10_GOC, CHUNKS, CANONICAL = 60, 63, 7, 9
SO_HANG_XOM = 10


def doc(duong):
    return json.loads(Path(duong).read_text(encoding="utf-8"))


def ghi(duong, gia_tri):
    duong.parent.mkdir(parents=True, exist_ok=True)
    duong.write_text(json.dumps(gia_tri, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def chon_node(g_edges, g_a10):
    dem, tap = {}, set()
    for e in g_a10["soft_backward_edges"]:
        tap |= {e["source"], e["target"]}
    seq = set(g_a10["sequence"])
    canh = [(e["source"], e["target"]) for e in g_edges["main_edges"] + g_edges["secondary_edges"]]
    for a, b in canh:
        if a in tap and b not in tap and b in seq:
            dem[b] = dem.get(b, 0) + 1
        if b in tap and a not in tap and a in seq:
            dem[a] = dem.get(a, 0) + 1
    them = sorted(dem, key=lambda n: (-dem[n], n))[:SO_HANG_XOM]
    return tap | set(them)


def main(kho, dich):
    from doc2roadmap.application.use_cases.build_roadmap import BuildRoadmap
    from doc2roadmap.application.use_cases.name_concept_labels import NameConceptLabels
    from doc2roadmap.application.use_cases.validate_graph import ValidateGraph
    from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore

    kho, dich = Path(kho), Path(dich)
    if dich.exists():
        shutil.rmtree(dich)
    g = doc(kho / "graph" / DOC / f"v{PHIEN_BAN_EDGES}" / "graph.json")
    gm = doc(kho / "graph" / DOC / f"v{PHIEN_BAN_EDGES}" / "manifest.json")
    a10 = doc(kho / "graph" / DOC / f"v{PHIEN_BAN_A10_GOC}" / "graph.json")
    vectors = doc(kho / "graph" / DOC / f"v{g['node_vectors_version']}" / "graph.json")["node_vectors"]
    chunks = doc(kho / "chunks" / DOC / f"v{CHUNKS}" / "chunks.json")
    sections = doc(kho / "chunks" / DOC / f"v{CHUNKS}" / "sections.json")
    cm = doc(kho / "chunks" / DOC / f"v{CHUNKS}" / "manifest.json")

    giu = chon_node(g, a10)
    nodes = [n for n in g["nodes"] if n["node_id"] in giu]
    main_edges = [e for e in g["main_edges"] if e["source"] in giu and e["target"] in giu]
    secondary_edges = [e for e in g["secondary_edges"] if e["source"] in giu and e["target"] in giu]

    can_chunk = set()
    for n in nodes:
        for khoa in ("teaching_chunk_ids", "defining_chunk_ids", "defining_chunk_ids_source", "source_chunk_ids"):
            can_chunk |= set(n.get(khoa) or [])
        can_chunk |= {x["chunk_id"] for x in n.get("evidence", []) if isinstance(x, dict)}
        if n.get("anchor"):
            can_chunk.add(n["anchor"]["chunk_id"])
    for e in main_edges + secondary_edges:
        can_chunk |= set(e.get("chunk_ids") or [])
    chunks_giu = [c for c in chunks if c["chunk_id"] in can_chunk]
    muc_giu, theo_ma = set(), {s["section_id"]: s for s in sections}
    for c in chunks_giu:
        ma = c["parent_section_id"]
        while ma is not None and ma not in muc_giu:
            muc_giu.add(ma)
            ma = theo_ma[ma]["parent_section_id"]
    sections_giu = [s for s in sections if s["section_id"] in muc_giu]

    cap_giu = {r["pair_id"] for r in g["suspected_pairs"] if r["left"] in giu and r["right"] in giu}
    sessions = []
    for s in g["main_sessions"]:
        muc_tieu = [x for x in s["target_node_ids"] if x in giu]
        if muc_tieu:
            sessions.append({**s, "target_node_ids": muc_tieu,
                             "allowed_node_ids": [x for x in s["allowed_node_ids"] if x in giu],
                             "chunk_ids": [x for x in s["chunk_ids"] if x in can_chunk]})
    ma_phien = {s["session_id"] for s in sessions}
    payload_edges = {
        **{k: v for k, v in g.items() if k not in ("nodes", "main_edges", "secondary_edges", "mention_map", "main_sessions",
                                                    "completed_main_sessions", "suspected_pairs", "secondary_log",
                                                    "completed_secondary_pairs", "secondary_model_metrics", "decision_log",
                                                    "topic_edges", "node_vectors_version", "pair_cluster_ledger",
                                                    "pair_cluster_relative_means", "contact_pairs", "executor_log")},
        "nodes": nodes, "main_edges": main_edges, "secondary_edges": secondary_edges,
        "mention_map": {c: {n: v for n, v in m.items() if n in giu} for c, m in g["mention_map"].items() if c in can_chunk},
        "main_sessions": sessions,
        "completed_main_sessions": [x for x in g["completed_main_sessions"] if x in ma_phien],
        "suspected_pairs": [r for r in g["suspected_pairs"] if r["pair_id"] in cap_giu],
        "secondary_log": [r for r in g["secondary_log"] if r["pair_id"] in cap_giu],
        "completed_secondary_pairs": [x for x in g["completed_secondary_pairs"] if x in cap_giu],
        "node_vectors_version": 1, "topic_edges": [], "decision_log": [], "executor_log": [],
        "pair_cluster_ledger": [], "pair_cluster_relative_means": {}, "contact_pairs": [],
    }
    canonical = {"stage": "gop", "doc_id": DOC, "upstream_chain": "gop", "canonical_has_anchors": True, "edges": [],
                 "deferred": [], "deferred_pairs": [], "redirects": {}, "nodes": [], "members": {}}

    luu = JsonArtifactStore(dich)
    ghi(dich / "chunks" / DOC / "v1" / "chunks.json", chunks_giu)
    ghi(dich / "chunks" / DOC / "v1" / "sections.json", sections_giu)
    ghi(dich / "chunks" / DOC / "v1" / "document.json", {"normalized_full_text": "", "structure_warnings": []})
    ghi(dich / "chunks" / DOC / "v1" / "manifest.json", {**{k: cm[k] for k in ("doc_id",)}, "version": 1,
                                                       "source_hash": "fixture", "config_hash": "fixture", "config": {}})
    ghi(dich / "canonical" / DOC / "v1" / "canonical.json", canonical)
    ghi(dich / "canonical" / DOC / "v1" / "manifest.json", {"version": 1, "doc_id": DOC, "source_hash": "fixture",
                                                          "config_hash": "fixture", "config": {}, "upstream_chain": "gop"})
    nhom = {n["node_id"]: vectors[n["node_id"]] for n in nodes if n["node_id"] in vectors}
    ghi(dich / "graph" / DOC / "v1" / "graph.json", {"stage": "clusters", "node_vectors": nhom, "nodes": [], "doc_id": DOC})
    ghi(dich / "graph" / DOC / "v1" / "manifest.json", {"version": 1, "doc_id": DOC, "source_hash": "fixture",
                                                      "config_hash": "fixture", "config": {}, "stage": "clusters",
                                                      "upstream_version": None})
    config_edges = {**{k: v for k, v in gm["config"].items() if k in ("algorithm_id", "upstream_chain", "definition_after",
                                                                       "definition_before")},
                    "canonical_version": 1, "chunks_version": 1, "upstream_chain": "gop", "canonical_has_anchors": True}
    ghi(dich / "graph" / DOC / "v2" / "graph.json", {**payload_edges, "canonical_version": 1})
    ghi(dich / "graph" / DOC / "v2" / "manifest.json", {"version": 2, "doc_id": DOC, "source_hash": "fixture",
                                                      "config_hash": "fixture-edges", "config": config_edges,
                                                      "stage": "edges", "upstream_version": 1})
    edges = luu.load_graph(DOC, 2)
    validated, _ = ValidateGraph(luu).execute(DOC, upstream=edges)
    mo_hinh = SimpleNamespace(model_id="ghi-san", start_session=lambda p: None)
    labeled, _ = NameConceptLabels(luu, mo_hinh, concurrency=1).execute(DOC, upstream=validated)
    roadmap, _ = BuildRoadmap(luu, stage_cap=8).execute(DOC, upstream=labeled)
    # v6 mô phỏng bước đặt tên module của Pha B (như v68 trên v63): cùng sequence/requires_edges, thêm model_id, trỏ về A10
    ghi(dich / "graph" / DOC / "v6" / "graph.json", {**roadmap.payload, "module_naming_contract": "fixture"})
    ghi(dich / "graph" / DOC / "v6" / "manifest.json", {
        "version": 6, "doc_id": DOC, "source_hash": "fixture", "config_hash": "fixture-ten-module", "stage": "stages",
        "upstream_version": roadmap.version,
        "config": {"algorithm_id": "phase-b-module-names-v6", "model_id": "ghi-san", "chunks_version": 1,
                   "upstream_version": roadmap.version, "module_cap": 8}})
    print("đã dựng", dich, "node", len(nodes), "cạnh", len(main_edges), len(secondary_edges),
          "A10 v", roadmap.version, "dãy", len(roadmap.payload["sequence"]),
          "mềm", roadmap.payload["stats"]["soft_backward_edge_count"])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
