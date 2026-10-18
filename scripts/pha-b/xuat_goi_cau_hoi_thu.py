"""Xuất gói đầu vào cho agentic soạn bộ câu hỏi thử của trợ lý Pha B (vé SA-19). 0 USD, không gọi mô hình.

Chạy:  .venv/Scripts/python.exe scripts/pha-b/xuat_goi_cau_hoi_thu.py --ra <thư mục> [--doc doc-1 ...]

Mỗi cuốn ra goi/<doc_id>/: thong_tin.json, module.jsonl, khai_niem.jsonl, doan.jsonl.
Gói cố ý KHÔNG có cạnh đồ thị, câu neo hay chunk dạy: câu hỏi và đoạn tham chiếu phải đến từ việc đọc sách, không từ đồ thị,
để bộ câu không thiên về cấu hình trợ lý có công cụ đồ thị (vé SA-23 so sánh có và không có công cụ đồ thị).
Chỉ nhận sáu cuốn phát triển; tập giữ lại bị từ chối.
"""
import argparse
import json
from pathlib import Path

from doc2roadmap.application.phase_b.retrieval import load_learning_graph
from doc2roadmap.composition import build_artifact_store
from doc2roadmap.composition_phase_b import DEVELOPMENT_DOCS

# Chỉ tiêu mỗi loại câu theo cuốn; tổng 200 (đặc tả 19a, mục 3).
CHI_TIEU = {
    "doc-1": {"dinh_nghia": 8, "tien_quyet": 6, "so_sanh": 6, "vi_du": 4, "lo_trinh": 4, "ngoai_tai_lieu": 6, "nhieu_luot": 6},
    "doc-4": {"dinh_nghia": 10, "tien_quyet": 7, "so_sanh": 8, "vi_du": 5, "lo_trinh": 5, "ngoai_tai_lieu": 8, "nhieu_luot": 7},
    "xstk-ch3-1": {"dinh_nghia": 7, "tien_quyet": 5, "so_sanh": 5, "vi_du": 4, "lo_trinh": 4, "ngoai_tai_lieu": 5, "nhieu_luot": 5},
    "nhap-mon-ml": {"dinh_nghia": 6, "tien_quyet": 4, "so_sanh": 5, "vi_du": 3, "lo_trinh": 3, "ngoai_tai_lieu": 5, "nhieu_luot": 4},
    "naive-bayes": {"dinh_nghia": 5, "tien_quyet": 3, "so_sanh": 4, "vi_du": 3, "lo_trinh": 2, "ngoai_tai_lieu": 4, "nhieu_luot": 4},
    "doc-6": {"dinh_nghia": 4, "tien_quyet": 3, "so_sanh": 3, "vi_du": 2, "lo_trinh": 2, "ngoai_tai_lieu": 3, "nhieu_luot": 3},
}


def _get(item, key, default=None):
    return item.get(key, default) if isinstance(item, dict) else getattr(item, key, default)


def _write(path, rows):
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def export(store, doc, out):
    if doc not in DEVELOPMENT_DOCS:
        raise SystemExit(f"{doc} không thuộc sáu cuốn phát triển; không xuất")
    graph = load_learning_graph(store, doc)
    payload = graph.payload
    manifest = store.load_graph(doc, payload["graph_version"]).manifest
    nodes = {n["node_id"]: n for n in payload["nodes"]}
    base = out / "goi" / doc
    base.mkdir(parents=True, exist_ok=True)
    modules, concepts = [], []
    for m in payload["modules"]:
        modules.append({"module_id": m["module_id"], "so_thu_tu": m["index"] + 1, "ten": m.get("title", ""),
                        "section_code": m.get("section_code", ""), "khai_niem": list(m["node_ids"])})
        for nid in m["node_ids"]:
            n = nodes[nid]
            aliases = [a.get("name") if isinstance(a, dict) else str(a) for a in n.get("aliases", [])]
            concepts.append({"node_id": nid, "ten": n.get("display_name") or n.get("name") or nid,
                             "bi_danh": [a for a in aliases if a], "module_id": m["module_id"],
                             "mo_ta": str(n.get("description") or "")[:200]})
    chunks = sorted(graph.chunks.values(), key=lambda c: _get(c, "order_index", 0))
    doan = [{"chunk_id": _get(c, "chunk_id"), "trang": _get(c, "page"), "muc": list(_get(c, "section_path", []) or []),
             "thu_tu": _get(c, "order_index", 0), "text": _get(c, "text", "")} for c in chunks]
    config = manifest.get("config", {})
    info = {"doc_id": doc, "graph_version": payload["graph_version"], "chunks_version": config.get("chunks_version"),
            "upstream_chain": config.get("upstream_chain") or "v3", "so_module": len(modules),
            "so_khai_niem": len(concepts), "so_doan": len(doan), "chi_tieu": CHI_TIEU[doc]}
    (base / "thong_tin.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
    _write(base / "module.jsonl", modules)
    _write(base / "khai_niem.jsonl", concepts)
    _write(base / "doan.jsonl", doan)
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ra", required=True)
    ap.add_argument("--doc", action="append")
    args = ap.parse_args()
    store = build_artifact_store()
    for doc in args.doc or list(CHI_TIEU):
        info = export(store, doc, Path(args.ra))
        print(json.dumps({k: v for k, v in info.items() if k != "chi_tieu"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
