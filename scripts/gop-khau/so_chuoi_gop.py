"""Vé 17i: so canonical chuỗi gộp với chuỗi v3 (A4 cũ + danh tính, và C8) trên cùng bộ ứng viên A3. 0 USD, không gọi mô hình.

- **Gộp:** phân hoạch ứng viên của v3 = node canonical v3 hợp lại theo `identity_map`; của chuỗi gộp = node canonical gộp. Liệt kê
  `gop_moi` (node gộp trải trên nhiều node v3) và `gop_mat` (node v3 bị tách ra nhiều node gộp), đánh dấu `khac_ten` khi các phần không chung
  khoá tên nào (tên và alias sau `name_key`).
- **Trạng thái dạy và neo:** với mỗi node v3 học được ở stage `teaching` (trước danh tính), lấy node gộp chứa ứng viên đầu của nó; so trạng thái
  và câu neo.
- **Đích vàng:** như trên nhưng chỉ cho đích của tệp vàng A8, in cả hai câu neo để Claude đọc.
In ra tệp JSON; có tên khái niệm và câu neo vì Claude phải đọc. Chạy từ gốc repo:
  .venv/Scripts/python.exe scripts/gop-khau/so_chuoi_gop.py <doc> [--kho-gop=tmp/v4-17i/artifacts] [--ra=tmp/v4-17i/so]
"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, "src")
from doc2roadmap.domain.canonical import name_key  # noqa: E402

# tài liệu: (phiên bản canonical v3, artifact teaching v3, artifact identity v3, tệp vàng A8 hoặc None) — đều ở kho artifacts/
V3 = {
    "doc-1": (4, 40, 41, "doc-1-10-12-vang.json"),
    "nhap-mon-ml": (7, 41, 42, None),
    "naive-bayes": (7, 41, 42, None),
    "doc-6": (1, 12, 13, None),
    "xstk-ch3-1": (7, 38, 40, "xstk-ch3-1-10-13-vang.json"),
    "doc-4": (1, 4, 6, "doc-4-chuong-8-vang.json"),
}


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def latest_gop(root, doc):
    for path in sorted((Path(root) / "canonical" / doc).glob("v*"), key=lambda p: -int(p.name[1:])):
        manifest = read(path / "manifest.json")
        if manifest["config"].get("upstream_chain") == "gop":
            return read(path / "canonical.json"), manifest
    raise SystemExit(f"{doc}: chưa có canonical chuỗi gộp trong {root}")


def head(identity, node_id):
    seen = set()
    while node_id in identity and node_id not in seen:
        seen.add(node_id)
        node_id = identity[node_id]
    return node_id


def keys(node):
    names = [node["name"], *[a["name"] if isinstance(a, dict) else a for a in node.get("aliases", [])]]
    return {name_key(name) for name in names if name}


def anchor_text(node):
    anchor = node.get("anchor") or {}
    return anchor.get("sentence")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    options = dict(arg[2:].split("=", 1) for arg in sys.argv[1:] if arg.startswith("--") and "=" in arg)
    doc = [arg for arg in sys.argv[1:] if not arg.startswith("--")][0]
    canonical_version, teaching_version, identity_version, gold_file = V3[doc]
    v3 = read(f"artifacts/canonical/{doc}/v{canonical_version}/canonical.json")
    teaching = read(f"artifacts/graph/{doc}/v{teaching_version}/graph.json")
    identity = read(f"artifacts/graph/{doc}/v{identity_version}/graph.json").get("identity_map", {})
    gop, manifest = latest_gop(options.get("kho-gop", "tmp/v4-17i/artifacts"), doc)

    v3_nodes = {n["node_id"]: n for n in v3["nodes"] if not n.get("media_id")}
    gop_nodes = {n["node_id"]: n for n in gop["nodes"] if not n.get("media_id")}
    gop_of = {member: n["node_id"] for n in gop_nodes.values() for member in n["members"]}
    final_v3 = {}
    for node_id, node in v3_nodes.items():
        final_v3.setdefault(head(identity, node_id), []).append(node_id)

    # Gộp: so hai phân hoạch ứng viên.
    new_merges, lost_merges = [], []
    v3_final_of = {m: head(identity, nid) for nid, n in v3_nodes.items() for m in n["members"]}
    for node_id, node in gop_nodes.items():
        parts = sorted({v3_final_of[m] for m in node["members"] if m in v3_final_of})
        if len(parts) > 1:
            part_keys = [set().union(*(keys(v3_nodes[x]) for x in final_v3[p])) for p in parts]
            shared = set.intersection(*part_keys)
            new_merges.append({"gop_node": node_id, "ten": node["name"], "khac_ten": not shared,
                               "cac_phan": [[v3_nodes[x]["name"] for x in final_v3[p]] for p in parts]})
    for final, members in final_v3.items():
        candidates = [m for x in members for m in v3_nodes[x]["members"]]
        parts = sorted({gop_of[m] for m in candidates if m in gop_of})
        if len(parts) > 1:
            lost_merges.append({"v3_node": final, "ten_v3": [v3_nodes[x]["name"] for x in members],
                                "khac_ten_v3": len(members) > 1 and not set.intersection(*(keys(v3_nodes[x]) for x in members)),
                                "cac_phan_gop": [gop_nodes[p]["name"] for p in parts]})

    # Trạng thái dạy và neo: node v3 học được ở stage teaching (trước danh tính).
    matrix, differences = Counter(), []
    for node in teaching["nodes"]:
        if not node.get("learnable") or node.get("media_id") or not node.get("members"):
            continue
        target = gop_nodes.get(gop_of.get(node["members"][0]))
        if target is None:
            matrix[(node.get("teaching_status"), "khong_co")] += 1
            continue
        status = (node.get("teaching_status"), target.get("teaching_status"))
        same_anchor = anchor_text(node) == anchor_text(target)
        matrix[status] += 1
        if status[0] == status[1] == "taught":
            matrix[("taught_cung_neo" if same_anchor else "taught_khac_neo", "")] += 1
        if status[0] != status[1] or not same_anchor:
            differences.append({"v3_node": node["node_id"], "ten": node["name"], "gop_ten": target["name"],
                                "trang_thai": list(status), "neo_v3": anchor_text(node), "neo_gop": anchor_text(target)})

    # Đích vàng.
    targets = []
    if gold_file:
        gold = read(Path("artifacts/a8-gold") / gold_file)
        by_id = {n["node_id"]: n for n in teaching["nodes"]}
        for target_id in gold["targets"]:
            node = by_id.get(target_id) or v3_nodes.get(target_id)
            gop_node = gop_nodes.get(gop_of.get(node["members"][0])) if node and node.get("members") else None
            targets.append({"dich": target_id, "ten": node["name"] if node else None,
                            "gop_node": gop_node["node_id"] if gop_node else None,
                            "trang_thai": [node.get("teaching_status") if node else None,
                                           gop_node.get("teaching_status") if gop_node else None],
                            "cung_neo": bool(node and gop_node and anchor_text(node) == anchor_text(gop_node)),
                            "neo_v3": anchor_text(node) if node else None,
                            "neo_gop": anchor_text(gop_node) if gop_node else None})

    stats = gop["stats"]
    result = {
        "doc": doc, "gop_canonical": manifest["version"] if "version" in manifest else None,
        "so_node": {"v3_canonical": len(v3_nodes), "v3_sau_danh_tinh": len(final_v3), "gop": len(gop_nodes)},
        "gop_moi": len(new_merges), "gop_moi_khac_ten": sum(r["khac_ten"] for r in new_merges),
        "gop_mat": len(lost_merges), "gop_mat_khac_ten": sum(r["khac_ten_v3"] for r in lost_merges),
        "trang_thai": {f"{a}->{b}": n for (a, b), n in sorted(matrix.items(), key=lambda kv: (-kv[1], str(kv[0])))},
        "dich_vang": {"tong": len(targets), "cung_trang_thai": sum(t["trang_thai"][0] == t["trang_thai"][1] for t in targets),
                      "cung_neo": sum(t["cung_neo"] for t in targets)},
        "de_cu_theo_nguon": {k: v for k, v in stats.items() if "nomination" in k or "source" in k},
        "chi_phi": manifest.get("cost_summary"),
        "do_thoi_gian": manifest.get("phase_measurements"),
        "stats": stats,
        "chi_tiet": {"gop_moi": new_merges, "gop_mat": lost_merges, "lech_neo": differences, "dich": targets},
    }
    out = Path(options.get("ra", "tmp/v4-17i/so"))
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{doc}.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k not in ("chi_tiet", "stats", "do_thoi_gian")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
