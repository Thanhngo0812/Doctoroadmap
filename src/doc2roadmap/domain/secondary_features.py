"""E5 pair features: research --tach-tu semantics, without main_* inputs."""
from __future__ import annotations

import math
import re
import unicodedata
from collections import defaultdict
from functools import cache

from .canonical import alias_kind
from .mentions import _mention_normalize, _names
from .prerequisites import definition_window
from .secondary import select_secondary_pairs
from .sentence_splitter import UnicodeSentenceSplitter
from .unicode_text import unspaced_character

FEATURE_NAMES = (
    "src_same_section",
    "src_citation_hard",
    "src_citation_soft",
    "src_contact",
    "src_proposed_relation",
    "src_so_chunk_contact",
    "cit_hard_xy",
    "cit_soft_xy",
    "cit_hard_yx",
    "cit_soft_yx",
    "cit_chunk_xy",
    "cit_chunk_yx",
    "cung_cum",
    "w_exact",
    "w_dense",
    "ord_x",
    "ord_y",
    "ord_hieu",
    "x_truoc_y",
    "cung_chunk",
    "cung_muc",
    "cung_chuong",
    "muc_chung",
    "sau_muc_x",
    "sau_muc_y",
    "ywin_cau",
    "x_trong_ywin",
    "x_trong_neo_y",
    "x_trong_ywin_tu",
    "x_trong_neo_y_tu",
    "y_trong_xwin_tu",
    "x_ywin_vi_tri",
    "xwin_cau",
    "y_trong_xwin",
    "y_trong_neo_x",
    "y_xwin_vi_tri",
    "tu_bao_la",
    "tu_bao_cua",
    "tu_bao_theo",
    "tu_bao_dua",
    "tu_bao_vi_du",
    "tu_bao_khac",
    "tu_bao_gom",
    "tu_bao_goi",
    "y_truoc_x_trong_neo",
    "x_trong_ywin_truoc_neo",
    "x_khung",
    "y_khung",
    "ywin_so_ten",
    "xwin_so_ten",
    "x_trong_ydef",
    "y_trong_xdef",
    "refd",
    "x_exact_ydef",
    "y_exact_xdef",
    "phu_x",
    "phu_y",
    "phu_log_ti",
    "trai_x",
    "trai_y",
    "dong_xh",
    "jaccard",
    "pr_x",
    "pr_y",
    "pr_hieu",
    "x_day",
    "y_day",
    "x_hoc_duoc",
    "y_hoc_duoc",
    "x_so_def",
    "y_so_def",
    "ten_x_trong_ten_y",
    "ten_y_trong_ten_x",
    "do_dai_ten_x",
    "do_dai_ten_y",
    "neo_y_noi_dung",
    "neo_y_bai_tap",
    "neo_y_loi_giai",
    "neo_y_de_cuong",
    "neo_y_mo_dau",
    "neo_y_hanh_chinh",
    "neo_y_cuoi_sach",
)
FEATURE_VERSION = "e5-82-v1"
CANDIDATE_RULE = "contract-and-exact-and-word-boundary-syllable-normalized-v1"
ROLES = ("noi_dung", "bai_tap", "loi_giai", "de_cuong", "mo_dau", "hanh_chinh", "cuoi_sach")

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


def matchable_names(node):
    return [(value or "", None) for value in _names(node)]


def regexes(node):
    """Mẫu khớp tên như kênh `exact` của mention map: chuẩn hoá giống hệt, bỏ ký hiệu, ranh giới từ trừ chữ viết không cách từ.
    Mỗi mẫu là cặp (mẫu trên văn bản chuẩn hoá, mẫu chữ hoa trên văn bản gốc hay None)."""
    result = []
    for value, raw in matchable_names(node):
        pattern = _mention_normalize(value)
        if not pattern or alias_kind(value) == "symbol":
            continue
        result.append((re.compile(re.escape(pattern) if any(map(unspaced_character, pattern))
                                  else rf"(?<!\w){re.escape(pattern)}(?!\w)"), raw))
    return result


def hit(patterns, text, normalized):
    return any(pattern.search(normalized) and (raw is None or raw.search(text)) for pattern, raw in patterns)


def found(patterns, text):
    return hit(patterns, text, _mention_normalize(text))


def segmented(text, tokenize):
    # Normalize each syllable before joining compounds (not the underscored sentence).
    return " ".join("_".join(_mention_normalize(part) for part in word.split()) for word in tokenize(text))


def word_regexes(node):
    """Mẫu khớp tên theo ranh giới **từ**: giữa các âm tiết của tên cho phép cách hoặc `_`; hai đầu không được dính chữ hay `_`, nên tên
    một âm tiết không khớp vào giữa từ ghép ("chất" không khớp "vật_chất")."""
    result = []
    for value, raw in matchable_names(node):
        pattern = _mention_normalize(value)
        if not pattern or alias_kind(value) == "symbol":
            continue
        result.append((re.compile(r"(?<!\w)" + "[ _]".join(re.escape(part) for part in pattern.split()) + r"(?!\w)"), raw))
    return result


def found_words(patterns, text, tokenize):
    return hit(patterns, text, segmented(text, tokenize))


def cues_before(patterns, text):
    """Nhóm từ báo (CUES) đứng ngay trước một lần nhắc tên trong câu; mọi lần nhắc đều xét."""
    normalized = _mention_normalize(text)
    result = set()
    for pattern, raw in patterns:
        if raw is not None and not raw.search(text):
            continue
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


class SecondaryFeatureContext:
    """Document-local caches; tokenizer is injected, never imported by the domain."""

    def __init__(self, payload, chunks, before=4, after=2, *, tokenize):
        self.tokenize = tokenize
        self.normalized = cache(_mention_normalize)
        self.segmented = cache(lambda text: segmented(text, tokenize))
        self.window_features = cache(self.window_features)
        import networkx as nx
        self.nodes = payload["nodes"]
        self.node_by_id = {node["node_id"]: node for node in self.nodes}
        self.chunk_by_id = {chunk.chunk_id: chunk for chunk in chunks}
        self.chunk_count = max(len(chunks), 1)
        # Nhắc tên theo chunk, theo mức (definition/extracted/mention) và kênh.
        self.mentioned = defaultdict(set)
        self.exact_in = defaultdict(set)
        for chunk_id, rows in payload["mention_map"].items():
            for node_id, row in rows.items():
                self.mentioned[node_id].add(chunk_id)
                if "exact" in row.get("channels", []):
                    self.exact_in[node_id].add(chunk_id)
        self.order = {chunk.chunk_id: chunk.order_index for chunk in chunks}
        # Đồ thị trích dẫn có hướng (Y trích X: X được nhắc trong chunk định nghĩa của Y) và PageRank trên hướng "Y tham chiếu X".
        self.citation = {(row["source"], row["target"]): row for row in payload.get("citations", [])}
        refers = nx.DiGraph()
        refers.add_nodes_from(self.node_by_id)
        refers.add_edges_from((target, source) for source, target in self.citation)
        self.rank = nx.pagerank(refers) if refers.number_of_edges() else {node_id: 0.0 for node_id in self.node_by_id}
        self.ledger = {frozenset((row["left_cluster"], row["right_cluster"])): row for row in payload.get("pair_cluster_ledger", [])}
        self.pattern_cache = {node_id: regexes(node) for node_id, node in self.node_by_id.items()}
        self.word_cache = {node_id: word_regexes(node) for node_id, node in self.node_by_id.items()}
        self.window_cache = {node_id: window_sentences(node, chunks, before, after) for node_id, node in self.node_by_id.items()}
        # Ai được nhắc trong cửa sổ của ai: độ "khung" của X (bao nhiêu khái niệm được dạy nhắc X trong cửa sổ định nghĩa) và số khái niệm cùng
        # được nhắc trong một cửa sổ.
        taught = [node_id for node_id, node in self.node_by_id.items()
                  if node.get("teaching_status") == "taught" and self.window_cache[node_id][0]]
        normalized_windows = {y: [(s, self.normalized(s)) for s in self.window_cache[y][0]] for y in taught}
        self.named_in = {y: {x for x in self.node_by_id
                             if x != y and any(hit(self.pattern_cache[x], s, n) for s, n in normalized_windows[y])}
                         for y in taught}
        self.frame_count = defaultdict(int)
        for y, named in self.named_in.items():
            for x in named:
                self.frame_count[x] += 1
        self.taught_count = max(len(taught), 1)

    def provenance(self, node_id):
        values = [self.order[c] for c in self.node_by_id[node_id].get("defining_chunk_ids", []) if c in self.order]
        return min(values) if values else None

    def first_chunk(self, node_id):
        values = sorted((self.order[c], c) for c in self.node_by_id[node_id].get("defining_chunk_ids", []) if c in self.order)
        return self.chunk_by_id[values[0][1]] if values else None

    def span(self, node_id):
        values = [self.order[c] for c in self.mentioned[node_id] if c in self.order]
        return (max(values) - min(values)) / self.chunk_count if values else 0.0

    def found(self, patterns, text):
        return hit(patterns, text, self.normalized(text))

    def found_words(self, patterns, text):
        return hit(patterns, text, self.segmented(text))

    def window_features(self, x, y):
        """Tên X trong cửa sổ định nghĩa của Y: số câu có tên, có trong câu neo không, vị trí câu gần neo nhất, từ báo đứng trước."""
        sentences, anchor_index = self.window_cache[y]
        hits = [i for i, sentence in enumerate(sentences) if self.found(self.pattern_cache[x], sentence)]
        anchor = (self.node_by_id[y].get("anchor") or {}).get("sentence", "")
        relative = min((i - anchor_index for i in hits), key=abs) if hits and anchor_index is not None else None
        cues = set().union(*(cues_before(self.pattern_cache[x], sentences[i]) for i in hits)) if hits else set()
        # Trong câu neo, tên Y đứng trước tên X ("Y là … X") hay sau.
        normalized = self.normalized(anchor)
        x_at = min((m.start() for p, raw in self.pattern_cache[x] if raw is None or raw.search(anchor)
                    for m in p.finditer(normalized)), default=None)
        y_at = min((m.start() for p, raw in self.pattern_cache[y] if raw is None or raw.search(anchor)
                    for m in p.finditer(normalized)), default=None)
        word_hits = [i for i in hits if self.found_words(self.word_cache[x], sentences[i])]
        return {"cau": len(sentences), "co_ten": len(hits), "trong_neo": int(bool(anchor) and self.found(self.pattern_cache[x], anchor)),
                "co_tu": len(word_hits),
                "neo_tu": int(bool(anchor) and self.found(self.pattern_cache[x], anchor) and self.found_words(self.word_cache[x], anchor)),
                "vi_tri": relative, "cues": cues, "y_truoc_x_neo": int(x_at is not None and y_at is not None and y_at < x_at),
                "truoc_neo": int(any(anchor_index is not None and i < anchor_index for i in hits))}


def pair_features(ctx, x, y, pair=None):
    """Đặc trưng có hướng X→Y. `pair` là cặp ứng viên của luồng (nguồn, chi tiết tiếp xúc); không có thì nhóm `src_*` bằng 0."""
    pair = pair or {}
    node_by_id, chunk_by_id, mentioned, exact_in, chunk_count = ctx.node_by_id, ctx.chunk_by_id, ctx.mentioned, ctx.exact_in, ctx.chunk_count
    rank, pattern_cache = ctx.rank, ctx.pattern_cache
    nx_, ny = node_by_id[x], node_by_id[y]
    cluster_row = ctx.ledger.get(frozenset((nx_["cluster_id"], ny["cluster_id"])), {})
    details = pair.get("details", {})
    px, py = ctx.provenance(x), ctx.provenance(y)
    cx, cy = ctx.first_chunk(x), ctx.first_chunk(y)
    path_x = cx.section_path if cx else []
    path_y = cy.section_path if cy else []
    common = next((i for i, (a, b) in enumerate(zip(path_x, path_y)) if a != b), min(len(path_x), len(path_y)))
    def_x, def_y = set(nx_.get("defining_chunk_ids", [])), set(ny.get("defining_chunk_ids", []))
    x_in_ydef = len(def_y & mentioned[x]) / len(def_y) if def_y else 0.0
    y_in_xdef = len(def_x & mentioned[y]) / len(def_x) if def_x else 0.0
    both = mentioned[x] & mentioned[y]
    union = mentioned[x] | mentioned[y]
    wx, wy = ctx.window_features(x, y), ctx.window_features(y, x)
    cit_xy, cit_yx = ctx.citation.get((x, y)), ctx.citation.get((y, x))
    result = {
        # Nguồn cặp và sổ cặp cụm.
        **{f"src_{name}": int(name in pair.get("sources", [])) for name in SOURCES},
        "src_so_chunk_contact": len(details.get("contact", [])),
        "cit_hard_xy": int(bool(cit_xy) and cit_xy["strength"] == "hard"), "cit_soft_xy": int(bool(cit_xy) and cit_xy["strength"] == "soft"),
        "cit_hard_yx": int(bool(cit_yx) and cit_yx["strength"] == "hard"), "cit_soft_yx": int(bool(cit_yx) and cit_yx["strength"] == "soft"),
        "cit_chunk_xy": len(cit_xy["chunk_ids"]) if cit_xy else 0, "cit_chunk_yx": len(cit_yx["chunk_ids"]) if cit_yx else 0,
        "cung_cum": int(nx_["cluster_id"] == ny["cluster_id"]),
        "w_exact": cluster_row.get("exact_weight", 0.0), "w_dense": cluster_row.get("dense_weight", 0.0),
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
        "x_trong_ywin_tu": wx["co_tu"], "x_trong_neo_y_tu": wx["neo_tu"], "y_trong_xwin_tu": wy["co_tu"],
        "x_ywin_vi_tri": "" if wx["vi_tri"] is None else wx["vi_tri"],
        "xwin_cau": wy["cau"], "y_trong_xwin": wy["co_ten"], "y_trong_neo_x": wy["trong_neo"],
        "y_xwin_vi_tri": "" if wy["vi_tri"] is None else wy["vi_tri"],
        **{f"tu_bao_{name}": int(name in wx["cues"]) for name in CUES},
        "y_truoc_x_trong_neo": wx["y_truoc_x_neo"], "x_trong_ywin_truoc_neo": wx["truoc_neo"],
        "x_khung": ctx.frame_count[x] / ctx.taught_count, "y_khung": ctx.frame_count[y] / ctx.taught_count,
        "ywin_so_ten": len(ctx.named_in.get(y, ())), "xwin_so_ten": len(ctx.named_in.get(x, ())),
        "x_trong_ydef": x_in_ydef, "y_trong_xdef": y_in_xdef, "refd": x_in_ydef - y_in_xdef,
        "x_exact_ydef": int(bool(def_y & exact_in[x])), "y_exact_xdef": int(bool(def_x & exact_in[y])),
        # Độ phủ, đồng xuất hiện.
        "phu_x": len(mentioned[x]) / chunk_count, "phu_y": len(mentioned[y]) / chunk_count,
        "phu_log_ti": math.log((len(mentioned[x]) + 1) / (len(mentioned[y]) + 1)),
        "trai_x": ctx.span(x), "trai_y": ctx.span(y), "dong_xh": len(both), "jaccard": len(both) / len(union) if union else 0.0,
        # Đồ thị: PageRank trên quan hệ "được tham chiếu", cạnh pass chính.
        "pr_x": rank.get(x, 0.0), "pr_y": rank.get(y, 0.0), "pr_hieu": rank.get(x, 0.0) - rank.get(y, 0.0),
        # Thuộc tính nút và tên.
        "x_day": int(nx_.get("teaching_status") == "taught"), "y_day": int(ny.get("teaching_status") == "taught"),
        # Hợp đồng `validate_main_proposals`: đích bị loại khi trạng thái thuộc NOT_TARGET; hai đầu phải học được.
        "hop_dong_cho_phep": int(ny.get("teaching_status") not in NOT_TARGET and bool(ny.get("learnable"))
                                 and bool(nx_.get("learnable"))),
        "x_hoc_duoc": int(bool(nx_.get("learnable"))), "y_hoc_duoc": int(bool(ny.get("learnable"))),
        "x_so_def": len(def_x), "y_so_def": len(def_y),
        "vai_tro_neo_y": (chunk_by_id.get((ny.get("anchor") or {}).get("chunk_id")).role
                          if (ny.get("anchor") or {}).get("chunk_id") in chunk_by_id else ""),
        "ten_x_trong_ten_y": int(ctx.found(pattern_cache[x], ny["name"])), "ten_y_trong_ten_x": int(ctx.found(pattern_cache[y], nx_["name"])),
        "do_dai_ten_x": len(ctx.normalized(nx_["name"]).split()), "do_dai_ten_y": len(ctx.normalized(ny["name"]).split()),
    }

    role = result.pop("vai_tro_neo_y")
    result.update({f"neo_y_{role_name}": int(role == role_name) for role_name in ROLES})
    return {name: result[name] for name in FEATURE_NAMES}


def is_candidate(ctx, x, y, features):
    source, target = ctx.node_by_id[x], ctx.node_by_id[y]
    return (target.get("teaching_status") not in NOT_TARGET and bool(source.get("learnable"))
            and bool(target.get("learnable")) and features["x_trong_ywin_tu"] > 0)


def feature_rows(payload, chunks, tokenize, *, before=4, after=2):
    ctx = SecondaryFeatureContext(payload, chunks, before, after, tokenize=tokenize)
    pairs, _ = select_secondary_pairs(payload["nodes"], payload.get("suspected_pairs", []),
                                      payload.get("pair_cluster_ledger", []), [], route=payload["routing"]["route"])
    for index, pair in enumerate(pairs):
        for x, y in ((pair["left"], pair["right"]), (pair["right"], pair["left"])):
            features = pair_features(ctx, x, y, pair)
            yield {"pair_id": pair["pair_id"], "thu_tu_cap": index, "x": x, "y": y,
                   "ten_x": ctx.node_by_id[x]["name"], "ten_y": ctx.node_by_id[y]["name"],
                   "ung_vien": int(is_candidate(ctx, x, y, features)), **features}
