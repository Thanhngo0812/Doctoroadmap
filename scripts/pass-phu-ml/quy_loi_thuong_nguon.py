"""Quy lỗi cạnh vàng về khâu thượng nguồn của A8 (trạng thái dạy, neo, danh tính) hay về chính A8. 0 USD, không gọi mô hình.

Thượng nguồn lấy từ artifact pass phụ v3 (nút sau danh tính, trạng thái dạy, câu neo, chunk), giống nhau cho mọi hệ. Mỗi hệ là một payload A10
đã lưu bởi `phat_lai_e4.py` (`tmp/pass-phu-ml/e4/<nhãn>/graph/<doc>/v1/graph.json`), nên phần "mô hình" so được giữa các hệ cùng thượng nguồn.

**Thiếu (hồi tưởng):** cạnh vàng X→Y (sau `identity_map`) được coi là có khi đồ thị cạnh cứng của A10 có đường X ⇝ Y. Cạnh thiếu nhận **một**
nguyên nhân, xét theo thứ tự:
1. `danh_tinh_gop_hai_dau`: X và Y bị gộp làm một (cạnh vàng thành tự nối);
2. `day_y`: Y có trạng thái không được làm đích (`mentioned_only`, `unchecked`, `prior_knowledge`, `not_subject_matter`): bộ kiểm loại mọi cạnh vào Y;
3. `day_x`: X có trạng thái như trên, nên X không vào dãy học;
4. `neo_y_khong_cua_so`: Y được dạy nhưng không dựng được cửa sổ định nghĩa: không có cạnh cứng nào vào Y qua được bộ kiểm;
5. `x_ngoai_cua_so`: tên X không có trong cửa sổ của Y. Với pass phụ ML đây là chặn cứng; với LLM thì không (bộ kiểm không đòi tên X), chỉ là
   khó hơn. Tách hai loại: `..._trong_chunk_day_y` (tên X có trong chunk neo hay chunk dạy của Y, ngoài cửa sổ) và `..._khong_nhac_gan_y`;
6. `mo_hinh`: tên X có trong cửa sổ mà vẫn thiếu: `mo_hinh_chi_mem` (chỉ có đường qua cạnh mềm), `mo_hinh_go_chu_trinh`, `mo_hinh_khong_tao`.
`--tach-tu` (chạy bằng tmp/venv-ml): "tên X trong cửa sổ" khớp theo ranh giới từ như ứng viên của pass phụ ML; mặc định khớp như kênh exact.

**Thừa (độ chính xác):** cạnh cứng của rút gọn bắc cầu, hai đầu là đích vàng, X không phải tổ tiên vàng của Y. Đếm theo hai cờ thượng nguồn:
`neo_nghi`: câu neo của Y không chứa tên hay bí danh của Y; `x_trong_cua_so`.

**Kiểm riêng từng khâu:** trạng thái dạy của đích vàng (kèm vai trò vùng của chunk định nghĩa); tỉ lệ đích có câu neo chứa tên mình; nhóm danh
tính chạm khái niệm vàng.
Ghi bảng chi tiết (có tên khái niệm của tài liệu phát triển) vào `tmp/pass-phu-ml/quy-loi/`. Chạy từ gốc repo:
  tmp/venv-ml/Scripts/python.exe scripts/pass-phu-ml/quy_loi_thuong_nguon.py [doc ...] [--he=khong,llm-v3,e5-a-hieu-chinh] [--tach-tu]
"""
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import networkx as nx

sys.path.insert(0, "src")
sys.path.insert(0, "scripts/pass-phu-ml")
import dung_bang_cap as dbc  # noqa: E402
from phat_lai_e4 import GOLD_DOCS  # noqa: E402
from doc2roadmap.application.use_cases.a8_score import load_gold  # noqa: E402
from doc2roadmap.domain.gold_scoring import transitive_closure  # noqa: E402
from doc2roadmap.domain.sequence import transitive_reduction  # noqa: E402
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore  # noqa: E402

NOT_TARGET = dbc.NOT_TARGET
CAUSES = ("danh_tinh_gop_hai_dau", "day_y", "day_x", "neo_y_khong_cua_so", "x_ngoai_cua_so_trong_chunk_day_y",
          "x_ngoai_cua_so_khong_nhac_gan_y", "mo_hinh_chi_mem", "mo_hinh_go_chu_trinh", "mo_hinh_khong_tao")


def upstream(doc):
    root, version, _, gold_file = GOLD_DOCS[doc]
    artifact = JsonArtifactStore(Path(root)).load_graph(doc, version)
    payload, config = artifact.payload, artifact.manifest["config"]
    chunks_version = config["chunks_version"]
    chunk_root = Path(root) if (Path(root) / "chunks" / doc / f"v{chunks_version}").exists() else Path("artifacts")
    chunks = JsonArtifactStore(chunk_root).load_role_chunks(doc, chunks_version).result.chunks
    ctx = dbc.Context(payload, chunks, config.get("definition_before", 4), config.get("definition_after", 2))
    return payload, chunks, ctx, load_gold(Path("artifacts/a8-gold") / gold_file)


def named(ctx, x, text):
    if dbc.WORDS:
        return dbc.found(ctx.pattern_cache[x], text) and dbc.found_words(ctx.word_cache[x], text)
    return dbc.found(ctx.pattern_cache[x], text)


def analyse(doc, systems):
    payload, chunks, ctx, gold = upstream(doc)
    identity = payload.get("identity_map", {})
    rep = lambda node_id: identity.get(node_id, node_id)  # noqa: E731
    nodes, chunk_by_id = ctx.node_by_id, ctx.chunk_by_id
    raw = {(e["prerequisite"], e["target"]) for e in gold["edges"]}
    mapped = {(rep(a), rep(b)) for a, b in raw}
    collapsed = sorted({(a, b) for a, b in mapped if a == b})
    edges = sorted({(a, b) for a, b in mapped if a != b})
    targets = {rep(t) for t in gold["targets"]}
    gold_closure = transitive_closure(edges)

    def status(node_id):
        return (nodes.get(node_id) or {}).get("teaching_status")

    def y_chunks(y):
        node = nodes[y]
        ids = set(node.get("teaching_chunk_ids") or []) | set(node.get("defining_chunk_ids") or [])
        anchor = (node.get("anchor") or {}).get("chunk_id")
        return [chunk_by_id[c] for c in ids | ({anchor} if anchor else set()) if c in chunk_by_id]

    def anchor_has_own_name(y):
        sentence = (nodes[y].get("anchor") or {}).get("sentence", "")
        return bool(sentence) and dbc.found(ctx.pattern_cache[y], sentence)

    upstream_rows = []
    for x, y in edges:
        window = ctx.window_cache.get(y, ([], None))[0] if y in nodes else []
        in_window = bool(window) and x in nodes and any(named(ctx, x, s) for s in window)
        in_chunks = x in nodes and y in nodes and any(named(ctx, x, c.text) for c in y_chunks(y))
        if x not in nodes or y not in nodes:
            cause = "thieu_nut"
        elif status(y) in NOT_TARGET or not nodes[y].get("learnable"):
            cause = "day_y"
        elif status(x) in NOT_TARGET or not nodes[x].get("learnable"):
            cause = "day_x"
        elif not window:
            cause = "neo_y_khong_cua_so"
        elif not in_window:
            cause = "x_ngoai_cua_so_trong_chunk_day_y" if in_chunks else "x_ngoai_cua_so_khong_nhac_gan_y"
        else:
            cause = "mo_hinh"
        upstream_rows.append({"x": x, "y": y, "ten_x": nodes.get(x, {}).get("name", x), "ten_y": nodes.get(y, {}).get("name", y),
                              "trang_thai_x": status(x), "trang_thai_y": status(y), "y_co_cua_so": int(bool(window)),
                              "x_trong_cua_so": int(in_window), "x_trong_chunk_day_y": int(in_chunks),
                              "neo_y_co_ten_y": int(y in nodes and anchor_has_own_name(y)), "nguyen_nhan_thuong_nguon": cause,
                              "hai_dau_la_dich": int(x in targets and y in targets)})

    result = {"doc": doc, "canh_vang": len(edges), "canh_vang_tu_noi_do_danh_tinh": len(collapsed), "he": {}}
    for system in systems:
        a10 = json.loads((Path("tmp/pass-phu-ml/e4") / system / "graph" / doc / "v1" / "graph.json").read_text(encoding="utf-8"))
        if a10.get("identity_map", {}) != identity:
            raise SystemExit(f"{doc} {system}: identity_map khác thượng nguồn")
        hard, every = nx.DiGraph(), nx.DiGraph()
        for edge in a10["requires_edges"]:
            every.add_edge(edge["source"], edge["target"])
            if not edge.get("soft"):
                hard.add_edge(edge["source"], edge["target"])
        removed = {(e["source"], e["target"]) for e in [*a10.get("removed_cycle_edges", []), *a10.get("identity_removed_edges", [])]}
        path = lambda graph, a, b: a in graph and b in graph and nx.has_path(graph, a, b)  # noqa: E731
        causes, by_window = Counter(), defaultdict(lambda: [0, 0])
        for row in upstream_rows:
            x, y = row["x"], row["y"]
            got = path(hard, x, y)
            row[f"co_{system}"] = int(got)
            if row["nguyen_nhan_thuong_nguon"] in ("mo_hinh",) or row["nguyen_nhan_thuong_nguon"].startswith("x_ngoai"):
                by_window[row["x_trong_cua_so"]][0] += int(got)
                by_window[row["x_trong_cua_so"]][1] += 1
            if got:
                continue
            cause = row["nguyen_nhan_thuong_nguon"]
            if cause == "mo_hinh":
                cause = "mo_hinh_chi_mem" if path(every, x, y) else "mo_hinh_go_chu_trinh" if (x, y) in removed else "mo_hinh_khong_tao"
            row[f"thieu_{system}"] = cause
            causes[cause] += 1
        causes["danh_tinh_gop_hai_dau"] = len(collapsed)
        # Thừa: cạnh cứng của rút gọn bắc cầu, hai đầu là đích vàng, X không phải tổ tiên vàng của Y.
        reduced = transitive_reduction([e for e in a10["requires_edges"] if not e.get("soft")])
        shown = [(a, b) for a, b in reduced if a in targets and b in targets and a != b]
        wrong = [(a, b) for a, b in shown if (a, b) not in gold_closure]
        flags = Counter()
        for a, b in shown:
            suspicious = b in nodes and not anchor_has_own_name(b)
            flags[("nghi" if suspicious else "on", (a, b) in gold_closure)] += 1
        recovered = sum(row[f"co_{system}"] for row in upstream_rows)
        result["he"][system] = {
            "co": recovered, "thieu": len(edges) - recovered + len(collapsed), "nguyen_nhan_thieu": {c: causes.get(c, 0) for c in CAUSES},
            "co_theo_cua_so": {("x_trong_cua_so" if k else "x_ngoai_cua_so"): f"{v[0]}/{v[1]}" for k, v in sorted(by_window.items())},
            "thua": {"canh_hien": len(shown), "sai": len(wrong),
                     "dich_neo_nghi": f"{flags[('nghi', False)]} sai / {flags[('nghi', False)] + flags[('nghi', True)]}",
                     "dich_neo_on": f"{flags[('on', False)]} sai / {flags[('on', False)] + flags[('on', True)]}"}}

    # Kiểm riêng từng khâu trên đích vàng.
    roles = {c.chunk_id: c.role for c in chunks}
    target_rows = []
    anchor_log = {row["node_id"]: row for row in payload.get("anchor_log", [])}
    for t in sorted(targets):
        node = nodes.get(t, {})
        target_rows.append({"node": t, "ten": node.get("name", t), "trang_thai": node.get("teaching_status"),
                            "vai_tro_chunk_dinh_nghia": "|".join(sorted({roles.get(c, "?") for c in node.get("defining_chunk_ids") or []})),
                            "c8_status": (anchor_log.get(t) or {}).get("status"), "c8_reason": (anchor_log.get(t) or {}).get("reason"),
                            "co_neo": int(bool(node.get("anchor"))), "neo_co_ten_minh": int(t in nodes and anchor_has_own_name(t)),
                            "co_cua_so": int(bool(ctx.window_cache.get(t, ([], None))[0]))})
    merged = defaultdict(list)
    for member, representative in identity.items():
        merged[representative].append(member)
    gold_nodes = {a for edge in raw for a in edge} | set(gold["targets"])
    result["kiem_khau"] = {
        "dich_vang": len(target_rows),
        "dich_theo_trang_thai": dict(Counter(row["trang_thai"] for row in target_rows)),
        "dich_khong_day_theo_vai_tro_chunk": dict(Counter(row["vai_tro_chunk_dinh_nghia"] for row in target_rows
                                                           if row["trang_thai"] in NOT_TARGET)),
        "dich_khong_day_theo_c8": dict(Counter(f"{row['c8_status']}" for row in target_rows if row["trang_thai"] in NOT_TARGET)),
        "dich_day_co_cua_so": f"{sum(r['co_cua_so'] for r in target_rows if r['trang_thai'] not in NOT_TARGET)}/"
                              f"{sum(1 for r in target_rows if r['trang_thai'] not in NOT_TARGET)}",
        "dich_day_neo_co_ten_minh": f"{sum(r['neo_co_ten_minh'] for r in target_rows if r['trang_thai'] not in NOT_TARGET)}/"
                                    f"{sum(1 for r in target_rows if r['trang_thai'] not in NOT_TARGET)}",
        "nhom_danh_tinh": len(merged), "nut_bi_gop": len(identity),
        "nhom_cham_vang": sum(1 for r, members in merged.items() if gold_nodes & {r, *members}),
        "cap_vang_bi_gop_lam_mot": [[nodes.get(a, {}).get("name", a)] for a, _ in collapsed],
        "cua_so_x_trong_cua_so_y_tren_canh_vang": f"{sum(r['x_trong_cua_so'] for r in upstream_rows)}/{len(upstream_rows)}"}
    out = Path("tmp/pass-phu-ml/quy-loi")
    out.mkdir(parents=True, exist_ok=True)
    for name, rows in (("canh", upstream_rows), ("dich", target_rows)):
        fields = list(dict.fromkeys(key for row in rows for key in row))
        with (out / f"{doc}-{name}.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    return result


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    dbc.WORDS = "--tach-tu" in sys.argv
    options = dict(arg[2:].split("=", 1) for arg in sys.argv[1:] if arg.startswith("--") and "=" in arg)
    systems = options.get("he", "khong,llm-v3,e5-a-hieu-chinh").split(",")
    docs = [arg for arg in sys.argv[1:] if not arg.startswith("--")] or ["doc-1", "xstk-ch3-1", "doc-4"]
    results = [analyse(doc, systems) for doc in docs]
    for result in results:
        print(json.dumps(result, ensure_ascii=False))
    path = Path("tmp/pass-phu-ml/ket-qua") / ("quy-loi" + ("-tach-tu" if dbc.WORDS else "") + ".json")
    path.write_text(json.dumps(results, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
