"""E0 (R-02 mục 7.7): bảng cặp × đặc trưng × phán quyết của pass phụ v3, mỗi tài liệu một tệp CSV. 0 USD, không gọi mô hình.

Mỗi cặp ứng viên (trái, phải) của pass phụ thành hai dòng có hướng X→Y, đọc là "X là tiên quyết của Y":
- **Đặc trưng** chỉ dùng thứ có trước khi pass phụ chạy: nút, chunk, mention map, nguồn cặp, sổ cặp cụm, cạnh pass chính. Bộ thay pass phụ
  vì vậy dùng lại được đúng các đặc trưng này. Bước này chưa có danh sách từ của ngôn ngữ nào: chỉ thứ tự, cấu trúc mục, khớp tên.
- **Nhãn** lấy từ kết quả pass phụ v3: `y` = 1 khi v3 tạo cạnh X→Y cho cặp này (`secondary_edges`, khớp theo `session_id`).
  `status` lấy từ `secondary_log`: created, rejected, deferred, pruned_direct_edge, pruned_explicit_path. Cặp bị tỉa không có phán quyết;
  dòng vẫn được giữ để mô phỏng thứ tự tỉa, nhưng không dùng để học hay đo.
- `dec_trai`, `dec_phai`: phán quyết từng thứ tự trình bày trong `decision_log` (mỗi thứ tự lấy bản ghi cuối, hợp lệ hay không; `!` = bị
  loại vì trượt kiểm); `loai_trai`, `loai_phai`: `prerequisite_kind` của phán quyết `create` ở thứ tự đó.
- `vang_xy`: (X, Y) là cạnh vàng (sau `identity_map`); `vang_pham_vi`: Y là đích vàng.
- `--tach-tu` (chạy bằng `tmp/venv-ml`, cần underthesea): thêm `x_trong_ywin_tu`, `x_trong_neo_y_tu`, `y_trong_xwin_tu` — khớp tên theo ranh
  giới từ tiếng Việt, để tên một âm tiết không khớp vào giữa từ ghép ("Chất" trong "vật chất").
Ghi ra `tmp/` vì dòng có tên khái niệm lấy từ giáo trình. Chạy từ gốc repo:
  .venv/Scripts/python.exe scripts/pass-phu-ml/dung_bang_cap.py [doc ...] [--ra=tmp/pass-phu-ml/bang]
  tmp/venv-ml/Scripts/python.exe scripts/pass-phu-ml/dung_bang_cap.py [doc ...] --tach-tu
"""
import csv
import json
import math
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, "src")
from doc2roadmap.domain.canonical import alias_kind  # noqa: E402
from doc2roadmap.domain.mentions import _mention_normalize, _names  # noqa: E402
from doc2roadmap.domain.prerequisites import definition_window  # noqa: E402
from doc2roadmap.domain.secondary import select_secondary_pairs  # noqa: E402
from doc2roadmap.domain.sentence_splitter import UnicodeSentenceSplitter  # noqa: E402
from doc2roadmap.domain.unicode_text import unspaced_character  # noqa: E402
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore  # noqa: E402

# tài liệu: (kho, phiên bản artifact pass phụ v3, ngôn ngữ, tệp vàng trong artifacts/a8-gold hoặc None)
DOCS = {
    "doc-1": ("artifacts/v3-r12-final-evaluation", 2, "vi", "doc-1-10-12-vang.json"),
    "nhap-mon-ml": ("artifacts/v3-r12-final-evaluation", 2, "vi", None),
    "xstk-ch3-1": ("artifacts", 42, "vi", "xstk-ch3-1-10-13-vang.json"),
    "doc-4": ("artifacts", 8, "vi", "doc-4-chuong-8-vang.json"),
    "doc-2": ("artifacts/v3-r12-final-evaluation", 2, "en", "doc-2-98-115-vang.json"),
    "doc-3": ("artifacts/v3-r12-final-evaluation", 2, "en", None),
}
NOT_TARGET = {"mentioned_only", "unchecked", "prior_knowledge", "not_subject_matter"}  # như `validate_main_proposals`
SOURCES = ("same_section", "citation_hard", "citation_soft", "contact", "proposed_relation")
SPLITTER = UnicodeSentenceSplitter()
# Từ đứng ngay trước tên X trong câu của cửa sổ định nghĩa Y. Riêng tiếng Việt: từ 2026-10-05 đồ án chỉ làm tài liệu tiếng Việt (chủ dự án
# chốt), nên dấu hiệu từ vựng được phép. Chỉ là đặc trưng cho bộ phân loại học, không phải luật tạo cạnh.
CUES = {
    "la": ("là", "là một", "là những", "là các", "là mọi"),
    "cua": ("của",),
    "theo": ("theo",),
    "dua": ("dựa trên", "dựa vào", "nhờ", "sử dụng", "dùng", "áp dụng"),
    "vi_du": ("ví dụ", "chẳng hạn", "như"),
    "khac": ("khác với", "so với", "ngược với", "trái với", "phân biệt với"),
    "gom": ("gồm", "bao gồm", "chứa"),
    "goi": ("gọi là", "được gọi là", "kí hiệu", "ký hiệu"),
}


def regexes(node):
    """Mẫu khớp tên như kênh `exact` của mention map: chuẩn hoá giống hệt, bỏ ký hiệu, ranh giới từ trừ chữ viết không cách từ."""
    result = []
    for value in _names(node):
        value = (value or "").strip()
        pattern = _mention_normalize(value)
        if not pattern or alias_kind(value) == "symbol":
            continue
        result.append(re.compile(re.escape(pattern) if any(map(unspaced_character, pattern))
                                 else rf"(?<!\w){re.escape(pattern)}(?!\w)"))
    return result


def found(patterns, text):
    normalized = _mention_normalize(text)
    return any(pattern.search(normalized) for pattern in patterns)


_SEGMENTED = {}


def segmented(text):
    """Câu đã tách từ tiếng Việt (underthesea), từ ghép nối bằng `_`, rồi chuẩn hoá như kênh exact. Chỉ dùng khi có `--tach-tu`."""
    if text not in _SEGMENTED:
        from underthesea import word_tokenize
        _SEGMENTED[text] = _mention_normalize(word_tokenize(text, format="text"))
    return _SEGMENTED[text]


def word_regexes(node):
    """Mẫu khớp tên theo ranh giới **từ**: giữa các âm tiết của tên cho phép cách hoặc `_`; hai đầu không được dính chữ hay `_`, nên tên
    một âm tiết không khớp vào giữa từ ghép ("chất" không khớp "vật_chất")."""
    result = []
    for value in _names(node):
        value = (value or "").strip()
        pattern = _mention_normalize(value)
        if not pattern or alias_kind(value) == "symbol":
            continue
        result.append(re.compile(r"(?<!\w)" + "[ _]".join(re.escape(part) for part in pattern.split()) + r"(?!\w)"))
    return result


def found_words(patterns, text):
    normalized = segmented(text)
    return any(pattern.search(normalized) for pattern in patterns)


def cues_before(patterns, text):
    """Nhóm từ báo (CUES) đứng ngay trước một lần nhắc tên trong câu; mọi lần nhắc đều xét."""
    normalized = _mention_normalize(text)
    result = set()
    for pattern in patterns:
        for match in pattern.finditer(normalized):
            before = " " + " ".join(normalized[:match.start()].split()[-3:])
            for name, words in CUES.items():
                if any(before.endswith(" " + _mention_normalize(word)) for word in words):
                    result.add(name)
    return result


def window_sentences(node, chunks, before, after):
    """Câu của cửa sổ định nghĩa và chỉ số câu neo trong cửa sổ (None nếu không định vị được)."""
    window = definition_window(node, chunks, before=before, after=after)
    if not window:
        return [], None
    sentences = [window[span.start:span.end] for span in SPLITTER.split(window)]
    anchor = unicodedata.normalize("NFC", (node.get("anchor") or {}).get("sentence", ""))
    first = anchor.split("\n")[0][:60]
    index = next((i for i, sentence in enumerate(sentences) if first and first in unicodedata.normalize("NFC", sentence)), None)
    return sentences, index


def build(doc):
    root, version, language, gold_file = DOCS[doc]
    store = JsonArtifactStore(Path(root))
    artifact = store.load_graph(doc, version)
    payload, config = artifact.payload, artifact.manifest["config"]
    if not str(config.get("algorithm_id", "")).startswith("a8-secondary"):
        raise ValueError(f"{doc} v{version} không phải artifact pass phụ")
    chunks_version = config["chunks_version"]
    chunk_root = Path(root) if (Path(root) / "chunks" / doc / f"v{chunks_version}").exists() else Path("artifacts")
    chunks = JsonArtifactStore(chunk_root).load_chunks(doc, chunks_version).result.chunks
    before, after = config.get("definition_before", 4), config.get("definition_after", 2)
    nodes = payload["nodes"]
    node_by_id = {node["node_id"]: node for node in nodes}
    chunk_by_id = {chunk.chunk_id: chunk for chunk in chunks}
    chunk_count = max(len(chunks), 1)
    mention_map = payload["mention_map"]
    route = payload["routing"]["route"]
    pairs, _ = select_secondary_pairs(nodes, payload.get("suspected_pairs", []), payload.get("pair_cluster_ledger", []), [], route=route)

    # Nhắc tên theo chunk, theo mức (definition/extracted/mention) và kênh.
    mentioned = defaultdict(set)
    exact_in = defaultdict(set)
    for chunk_id, rows in mention_map.items():
        for node_id, row in rows.items():
            mentioned[node_id].add(chunk_id)
            if "exact" in row.get("channels", []):
                exact_in[node_id].add(chunk_id)
    order = {chunk.chunk_id: chunk.order_index for chunk in chunks}

    def provenance(node_id):
        values = [order[c] for c in node_by_id[node_id].get("defining_chunk_ids", []) if c in order]
        return min(values) if values else None

    def first_chunk(node_id):
        values = sorted((order[c], c) for c in node_by_id[node_id].get("defining_chunk_ids", []) if c in order)
        return chunk_by_id[values[0][1]] if values else None

    def span(node_id):
        values = [order[c] for c in mentioned[node_id] if c in order]
        return (max(values) - min(values)) / chunk_count if values else 0.0

    # Đồ thị trích dẫn có hướng (Y trích X: X được nhắc trong chunk định nghĩa của Y) và PageRank trên hướng "Y tham chiếu X".
    citation = {(row["source"], row["target"]): row for row in payload.get("citations", [])}
    import networkx as nx
    refers = nx.DiGraph()
    refers.add_nodes_from(node_by_id)
    refers.add_edges_from((target, source) for source, target in citation)
    rank = nx.pagerank(refers) if refers.number_of_edges() else {node_id: 0.0 for node_id in node_by_id}
    main_hard = nx.DiGraph()
    main_hard.add_nodes_from(node_by_id)
    main_any = nx.DiGraph()
    main_any.add_nodes_from(node_by_id)
    for edge in payload.get("main_edges", []):
        if edge.get("edge_type", "requires") != "requires":
            continue
        main_any.add_edge(edge["source"], edge["target"])
        if not edge.get("soft"):
            main_hard.add_edge(edge["source"], edge["target"])
    ledger = {frozenset((row["left_cluster"], row["right_cluster"])): row for row in payload.get("pair_cluster_ledger", [])}

    # Nhãn v3.
    log = {row["pair_id"]: row for row in payload.get("secondary_log", []) if "pair_id" in row}
    created = defaultdict(list)
    for edge in payload.get("secondary_edges", []):
        created[edge.get("session_id", "").removeprefix("secondary_")].append(edge)
    decisions = {}
    for row in payload.get("decision_log", []):
        session = (row.get("input") or {}).get("session_id", "")
        if not session.startswith("secondary_"):
            continue
        output = row.get("output") if row.get("valid") else (row.get("output") or row.get("last_output"))
        decisions[session] = (output or {}, bool(row.get("valid")))

    def decision(pair_id, side, x, y):
        output, valid = decisions.get(f"secondary_{pair_id}_{side}", ({}, False))
        value = output.get("decision", "")
        if value == "create":
            value = "create_xy" if (output.get("prerequisite"), output.get("target")) == (x, y) else "create_yx"
        return value + ("" if valid else "!") if value else ""

    def decision_kind(pair_id, side):
        output, _ = decisions.get(f"secondary_{pair_id}_{side}", ({}, False))
        return output.get("prerequisite_kind", "") if output.get("decision") == "create" else ""

    identity = payload.get("identity_map", {})
    gold_edges, gold_targets = set(), set()
    if gold_file:
        gold = json.loads((Path("artifacts/a8-gold") / gold_file).read_text(encoding="utf-8"))
        gold_edges = {(identity.get(e["prerequisite"], e["prerequisite"]), identity.get(e["target"], e["target"])) for e in gold["edges"]}
        gold_targets = {identity.get(t, t) for t in gold["targets"]}

    pattern_cache = {node_id: regexes(node) for node_id, node in node_by_id.items()}
    word_cache = {node_id: word_regexes(node) for node_id, node in node_by_id.items()} if WORDS else {}
    window_cache = {node_id: window_sentences(node, chunks, before, after) for node_id, node in node_by_id.items()}
    # Ai được nhắc trong cửa sổ của ai: độ "khung" của X (bao nhiêu khái niệm được dạy nhắc X trong cửa sổ định nghĩa) và số khái niệm cùng
    # được nhắc trong một cửa sổ.
    taught = [node_id for node_id, node in node_by_id.items() if node.get("teaching_status") == "taught" and window_cache[node_id][0]]
    normalized_windows = {y: [_mention_normalize(s) for s in window_cache[y][0]] for y in taught}
    named_in = {y: {x for x in node_by_id if x != y and any(p.search(s) for p in pattern_cache[x] for s in normalized_windows[y])}
                for y in taught}
    frame_count = defaultdict(int)
    for y, named in named_in.items():
        for x in named:
            frame_count[x] += 1
    taught_count = max(len(taught), 1)

    def window_features(x, y):
        """Tên X trong cửa sổ định nghĩa của Y: số câu có tên, có trong câu neo không, vị trí câu gần neo nhất, từ báo đứng trước."""
        sentences, anchor_index = window_cache[y]
        hits = [i for i, sentence in enumerate(sentences) if found(pattern_cache[x], sentence)]
        anchor = (node_by_id[y].get("anchor") or {}).get("sentence", "")
        relative = min((i - anchor_index for i in hits), key=abs) if hits and anchor_index is not None else None
        cues = set().union(*(cues_before(pattern_cache[x], sentences[i]) for i in hits)) if hits else set()
        # Trong câu neo, tên Y đứng trước tên X ("Y là … X") hay sau.
        normalized = _mention_normalize(anchor)
        x_at = min((m.start() for p in pattern_cache[x] for m in p.finditer(normalized)), default=None)
        y_at = min((m.start() for p in pattern_cache[y] for m in p.finditer(normalized)), default=None)
        word_hits = [i for i in hits if found_words(word_cache[x], sentences[i])] if WORDS else []
        return {"cau": len(sentences), "co_ten": len(hits), "trong_neo": int(bool(anchor) and found(pattern_cache[x], anchor)),
                "co_tu": len(word_hits),
                "neo_tu": int(WORDS and bool(anchor) and found(pattern_cache[x], anchor) and found_words(word_cache[x], anchor)),
                "vi_tri": relative, "cues": cues, "y_truoc_x_neo": int(x_at is not None and y_at is not None and y_at < x_at),
                "truoc_neo": int(any(anchor_index is not None and i < anchor_index for i in hits))}

    rows = []
    for index, pair in enumerate(pairs):
        left, right = pair["left"], pair["right"]
        status_row = log.get(pair["pair_id"], {})
        status = status_row.get("status", "missing")
        reason = status_row.get("reason", "")
        edges = created.get(pair["pair_id"], [])
        same_cluster = node_by_id[left]["cluster_id"] == node_by_id[right]["cluster_id"]
        cluster_row = ledger.get(frozenset((node_by_id[left]["cluster_id"], node_by_id[right]["cluster_id"])), {})
        details = pair.get("details", {})
        for x, y in ((left, right), (right, left)):
            nx_, ny = node_by_id[x], node_by_id[y]
            px, py = provenance(x), provenance(y)
            cx, cy = first_chunk(x), first_chunk(y)
            path_x = cx.section_path if cx else []
            path_y = cy.section_path if cy else []
            common = next((i for i, (a, b) in enumerate(zip(path_x, path_y)) if a != b), min(len(path_x), len(path_y)))
            def_x, def_y = set(nx_.get("defining_chunk_ids", [])), set(ny.get("defining_chunk_ids", []))
            x_in_ydef = len(def_y & mentioned[x]) / len(def_y) if def_y else 0.0
            y_in_xdef = len(def_x & mentioned[y]) / len(def_x) if def_x else 0.0
            both = mentioned[x] & mentioned[y]
            union = mentioned[x] | mentioned[y]
            wx, wy = window_features(x, y), window_features(y, x)
            edge = next((e for e in edges if (e["source"], e["target"]) == (x, y)), None)
            cit_xy, cit_yx = citation.get((x, y)), citation.get((y, x))
            rows.append({
                "doc": doc, "ngon_ngu": language, "pair_id": pair["pair_id"], "thu_tu_cap": index, "x": x, "y": y,
                "ten_x": nx_["name"], "ten_y": ny["name"],
                "status": status, "reason": reason if status != "rejected" or len(reason) < 40 else "llm_reason",
                "y_label": int(edge is not None),
                "kind": (edge or {}).get("prerequisite_kind", ""), "evidence_kind": (edge or {}).get("evidence_kind", ""),
                "llm_quote_co_ten_x": int(found(pattern_cache[x], edge["quote"])) if edge and edge.get("quote") else "",
                "dec_trai": decision(pair["pair_id"], "left", x, y), "dec_phai": decision(pair["pair_id"], "right", x, y),
                "loai_trai": decision_kind(pair["pair_id"], "left"), "loai_phai": decision_kind(pair["pair_id"], "right"),
                "vang_xy": int((x, y) in gold_edges), "vang_yx": int((y, x) in gold_edges), "vang_pham_vi": int(y in gold_targets),
                # Nguồn cặp và sổ cặp cụm.
                **{f"src_{name}": int(name in pair.get("sources", [])) for name in SOURCES},
                "src_so_chunk_contact": len(details.get("contact", [])),
                "cit_hard_xy": int(bool(cit_xy) and cit_xy["strength"] == "hard"), "cit_soft_xy": int(bool(cit_xy) and cit_xy["strength"] == "soft"),
                "cit_hard_yx": int(bool(cit_yx) and cit_yx["strength"] == "hard"), "cit_soft_yx": int(bool(cit_yx) and cit_yx["strength"] == "soft"),
                "cit_chunk_xy": len(cit_xy["chunk_ids"]) if cit_xy else 0, "cit_chunk_yx": len(cit_yx["chunk_ids"]) if cit_yx else 0,
                "cung_cum": int(same_cluster), "w_exact": cluster_row.get("exact_weight", 0.0), "w_dense": cluster_row.get("dense_weight", 0.0),
                # Thứ tự và cấu trúc mục.
                "ord_x": px / chunk_count if px is not None else "", "ord_y": py / chunk_count if py is not None else "",
                "ord_hieu": (py - px) / chunk_count if px is not None and py is not None else "",
                "x_truoc_y": int(px is not None and py is not None and px < py),
                "cung_chunk": int(bool(def_x & def_y)),
                "cung_muc": int(bool(cx and cy and cx.parent_section_id == cy.parent_section_id)),
                "cung_chuong": int(bool(path_x and path_y and path_x[0] == path_y[0])),
                "muc_chung": common, "sau_muc_x": len(path_x), "sau_muc_y": len(path_y),
                # Tham chiếu có hướng: cửa sổ định nghĩa (S2) và RefD trên chunk định nghĩa (S4).
                "ywin_cau": wx["cau"], "x_trong_ywin": wx["co_ten"], "x_trong_neo_y": wx["trong_neo"],
                **({"x_trong_ywin_tu": wx["co_tu"], "x_trong_neo_y_tu": wx["neo_tu"], "y_trong_xwin_tu": wy["co_tu"]} if WORDS else {}),
                "x_ywin_vi_tri": "" if wx["vi_tri"] is None else wx["vi_tri"],
                "xwin_cau": wy["cau"], "y_trong_xwin": wy["co_ten"], "y_trong_neo_x": wy["trong_neo"],
                "y_xwin_vi_tri": "" if wy["vi_tri"] is None else wy["vi_tri"],
                **{f"tu_bao_{name}": int(name in wx["cues"]) for name in CUES},
                "y_truoc_x_trong_neo": wx["y_truoc_x_neo"], "x_trong_ywin_truoc_neo": wx["truoc_neo"],
                "x_khung": frame_count[x] / taught_count, "y_khung": frame_count[y] / taught_count,
                "ywin_so_ten": len(named_in.get(y, ())), "xwin_so_ten": len(named_in.get(x, ())),
                "x_trong_ydef": x_in_ydef, "y_trong_xdef": y_in_xdef, "refd": x_in_ydef - y_in_xdef,
                "x_exact_ydef": int(bool(def_y & exact_in[x])), "y_exact_xdef": int(bool(def_x & exact_in[y])),
                # Độ phủ, đồng xuất hiện.
                "phu_x": len(mentioned[x]) / chunk_count, "phu_y": len(mentioned[y]) / chunk_count,
                "phu_log_ti": math.log((len(mentioned[x]) + 1) / (len(mentioned[y]) + 1)),
                "trai_x": span(x), "trai_y": span(y), "dong_xh": len(both), "jaccard": len(both) / len(union) if union else 0.0,
                # Đồ thị: PageRank trên quan hệ "được tham chiếu", cạnh pass chính.
                "pr_x": rank.get(x, 0.0), "pr_y": rank.get(y, 0.0), "pr_hieu": rank.get(x, 0.0) - rank.get(y, 0.0),
                "main_duong_xy": int(nx.has_path(main_hard, x, y)), "main_duong_yx": int(nx.has_path(main_hard, y, x)),
                "main_mem_xy": int(main_any.has_edge(x, y)), "main_mem_yx": int(main_any.has_edge(y, x)),
                "main_vao_y": main_hard.in_degree(y), "main_ra_x": main_hard.out_degree(x),
                "main_vao_x": main_hard.in_degree(x), "main_ra_y": main_hard.out_degree(y),
                # Thuộc tính nút và tên.
                "x_day": int(nx_.get("teaching_status") == "taught"), "y_day": int(ny.get("teaching_status") == "taught"),
                # Hợp đồng `validate_main_proposals`: đích bị loại khi trạng thái thuộc NOT_TARGET; hai đầu phải học được.
                "hop_dong_cho_phep": int(ny.get("teaching_status") not in NOT_TARGET and bool(ny.get("learnable"))
                                         and bool(nx_.get("learnable"))),
                "x_hoc_duoc": int(bool(nx_.get("learnable"))), "y_hoc_duoc": int(bool(ny.get("learnable"))),
                "x_so_def": len(def_x), "y_so_def": len(def_y),
                "vai_tro_neo_y": (chunk_by_id.get((ny.get("anchor") or {}).get("chunk_id")).role
                                  if (ny.get("anchor") or {}).get("chunk_id") in chunk_by_id else ""),
                "ten_x_trong_ten_y": int(found(pattern_cache[x], ny["name"])), "ten_y_trong_ten_x": int(found(pattern_cache[y], nx_["name"])),
                "do_dai_ten_x": len(_mention_normalize(nx_["name"]).split()), "do_dai_ten_y": len(_mention_normalize(ny["name"]).split()),
            })
    return rows, {"doc": doc, "pairs": len(pairs), "secondary_pair_count": artifact.manifest.get("stats", {}).get("secondary_pair_count"),
                  "edges_v3": len(payload.get("secondary_edges", [])),
                  "edges_in_table": sum(row["y_label"] for row in rows), "nodes": len(nodes), "chunks": len(chunks)}


WORDS = "--tach-tu" in sys.argv


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    options = dict(arg[2:].split("=", 1) for arg in sys.argv[1:] if arg.startswith("--") and "=" in arg)
    out = Path(options.get("ra", "tmp/pass-phu-ml/bang"))
    out.mkdir(parents=True, exist_ok=True)
    docs = [arg for arg in sys.argv[1:] if not arg.startswith("--")] or list(DOCS)
    for doc in docs:
        rows, summary = build(doc)
        with (out / f"{doc}.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        print(json.dumps(summary, ensure_ascii=False), flush=True)
        if summary["pairs"] != summary["secondary_pair_count"] or summary["edges_in_table"] != summary["edges_v3"]:
            print(f"  CẢNH BÁO {doc}: số cặp hoặc số cạnh không khớp manifest", flush=True)


if __name__ == "__main__":
    main()
