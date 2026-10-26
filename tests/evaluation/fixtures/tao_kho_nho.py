"""Dựng fixture `kho-nho/` bằng cách CẮT graph xstk-ch3-1 v68 (tập phát triển) quanh các đầu cạnh của vàng cũ.

Chạy một lần để ghi lại; kho chung chỉ được ĐỌC. Fixture không chứa gì của tập giữ lại.
Sửa đổi so với bản gốc (đều có chủ ý, để test các nhánh thật):
- nút chỉ giữ các trường bộ xuất và bộ chấm cũ dùng; `sequence_index` tính lại theo dãy đã cắt;
- chunks và sections chỉ giữ năm trường cần, không giữ văn bản;
- `identity_map` thêm tay một mục `{một nút nhắc-đến-thôi: một nút trong dãy}` để thử bản đồ danh tính, vì graph thật không có.
Cách chạy: python tao_kho_nho.py <đường dẫn artifacts chung>
"""
import json
import sys
from pathlib import Path

DOC = "xstk-ch3-1"
PHIEN_BAN, CANONICAL, CHUNKS = 68, 9, 7
GIU_NUT = ("node_id", "name", "aliases", "node_type", "teaching_status", "anchor", "members", "module_id",
           "sequence_index", "learnable", "teaching_order_index", "first_order_index")
GIU_CANH = ("source", "target", "edge_type", "session_id", "quote", "chunk_ids", "soft", "soft_reason")


def doc(duong):
    return json.loads(Path(duong).read_text(encoding="utf-8"))


def ghi(duong, gia_tri):
    duong.parent.mkdir(parents=True, exist_ok=True)
    duong.write_text(json.dumps(gia_tri, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def main(kho, dich):
    kho, dich = Path(kho), Path(dich)
    vang = doc(kho / "a8-gold" / "xstk-ch3-1-10-13-vang.json")
    graph = doc(kho / "graph" / DOC / f"v{PHIEN_BAN}" / "graph.json")
    manifest = doc(kho / "graph" / DOC / f"v{PHIEN_BAN}" / "manifest.json")
    canonical = doc(kho / "canonical" / DOC / f"v{CANONICAL}" / "canonical.json")
    redirects = canonical["redirects"]

    def quy(ma):
        while ma in redirects:
            ma = redirects[ma]
        return ma

    dau = {quy(x) for e in vang["edges"] for x in (e["prerequisite"], e["target"])} | {quy(t) for t in vang["targets"]}
    nut = {n["node_id"]: n for n in [*graph["nodes"], *graph["mentioned_nodes"], *graph["excluded_nodes"]]}
    giu = {ma for ma in dau if ma in nut}
    trong_day = [ma for ma in graph["sequence"] if ma in giu]
    ngoai_day = sorted(giu - set(trong_day))
    assert ngoai_day, "cần ít nhất một nút nhắc-đến-thôi để thử bản đồ danh tính"
    chi_so = {ma: i for i, ma in enumerate(trong_day)}

    def cat_nut(n):
        ket = {k: n[k] for k in GIU_NUT if k in n}
        ket["sequence_index"] = chi_so.get(n["node_id"])
        return ket

    nodes = [cat_nut(nut[ma]) for ma in trong_day]
    nhac = [cat_nut(nut[ma]) for ma in ngoai_day if ma in {n["node_id"] for n in graph["mentioned_nodes"]}]
    loai = [cat_nut(nut[ma]) for ma in ngoai_day if ma in {n["node_id"] for n in graph["excluded_nodes"]}]
    in_giu = lambda e: e["source"] in giu and e["target"] in giu  # noqa: E731
    cat_canh = lambda e: {k: e[k] for k in GIU_CANH if k in e}  # noqa: E731
    requires = [cat_canh(e) for e in graph["requires_edges"] if in_giu(e)]
    mem_nguoc = [cat_canh(e) for e in graph["soft_backward_edges"] if in_giu(e)]
    ma_chunk = {c for n in [*nodes, *nhac, *loai] if n.get("anchor") for c in [n["anchor"]["chunk_id"]]}
    ma_chunk |= {c for e in [*requires, *mem_nguoc] for c in e.get("chunk_ids", [])}
    chunks_goc = {c["chunk_id"]: c for c in doc(kho / "chunks" / DOC / f"v{CHUNKS}" / "chunks.json")}
    chunks = [{k: chunks_goc[m][k] for k in ("chunk_id", "page", "parent_section_id", "role", "section_path")}
              for m in sorted(ma_chunk)]
    muc_can = {c["parent_section_id"] for c in chunks}
    sections = [{k: s[k] for k in ("section_id", "title", "level", "parent_section_id", "role")}
                for s in doc(kho / "chunks" / DOC / f"v{CHUNKS}" / "sections.json")
                if s["section_id"] in muc_can or s["level"] == 0]
    cap_giu = [p for p in graph["suspected_pairs"] if p["left"] in giu and p["right"] in giu]
    ma_cap = {p["pair_id"] for p in cap_giu}
    modules = []
    for m in graph["modules"]:
        thanh_vien = [x for x in m["node_ids"] if x in chi_so]
        if thanh_vien:
            modules.append({"module_id": m["module_id"], "title": m["title"], "node_ids": thanh_vien})
    nut_a, nut_b = ngoai_day[0], trong_day[0]
    graph_nho = {
        "doc_id": DOC, "stage": "stages", "canonical_version": CANONICAL, "nodes": nodes, "mentioned_nodes": nhac,
        "excluded_nodes": loai, "requires_edges": requires, "soft_backward_edges": mem_nguoc, "bypassed_edges": [],
        "sequence": trong_day, "modules": modules, "suspected_pairs": cap_giu,
        "secondary_log": [r for r in graph["secondary_log"] if r["pair_id"] in ma_cap],
        "cost_summary": graph["cost_summary"], "identity_map": {nut_a: nut_b},
    }
    ghi(dich / "graph" / DOC / f"v{PHIEN_BAN}" / "graph.json", graph_nho)
    ghi(dich / "graph" / DOC / f"v{PHIEN_BAN}" / "manifest.json", {
        "artifact_type": "graph", "doc_id": DOC, "stage": "stages", "version": PHIEN_BAN, "upstream_version": None,
        "config_hash": manifest["config_hash"],
        "config": {"model_id": manifest["config"]["model_id"], "canonical_version": CANONICAL, "chunks_version": CHUNKS}})
    ghi(dich / "canonical" / DOC / f"v{CANONICAL}" / "canonical.json",
        {"doc_id": DOC, "redirects": {k: v for k, v in redirects.items()
                                      if k in {x for e in vang["edges"] for x in (e["prerequisite"], e["target"])}
                                      | set(vang["targets"])}})
    ghi(dich / "canonical" / DOC / f"v{CANONICAL}" / "manifest.json",
        {"artifact_type": "canonical", "doc_id": DOC, "version": CANONICAL})
    ghi(dich / "chunks" / DOC / f"v{CHUNKS}" / "chunks.json", chunks)
    ghi(dich / "chunks" / DOC / f"v{CHUNKS}" / "sections.json", sections)
    ghi(dich / "a8-gold" / "xstk-nho-vang.json", {
        k: vang[k] for k in ("doc_id", "canonical_version", "chapter", "concept_hash", "targets", "edges", "errors",
                             "annotator")})
    print("nút", len(nodes), "nhắc", len(nhac), "loại", len(loai), "cạnh", len(requires), "mềm", len(mem_nguoc),
          "chunk", len(chunks), "danh tính", {nut_a: nut_b})


if __name__ == "__main__":
    main(sys.argv[1], Path(__file__).resolve().parent / "kho-nho")
