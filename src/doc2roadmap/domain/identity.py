from __future__ import annotations

import unicodedata
from itertools import combinations

from .global_validation import strongly_connected_components

# Danh tính (spec v2, W14–W15). Ứng viên chỉ từ tín hiệu hẹp; mọi ứng viên phải qua phán — chung tên hay chung alias
# là lý do đưa ra xét, không phải bằng chứng trùng. "Tên này chứa tên kia" bị loại có chủ ý: `Ma trận` nằm trong
# `Ma trận nghịch đảo` mà hai khái niệm khác hẳn nhau.
GENERIC_PREFIXES = ("hệ véc tơ ", "hệ vectơ ", "hệ vector ", "tính ", "khái niệm ", "the notion of ", "the concept of ")


def _norm(text):
    return " ".join(unicodedata.normalize("NFC", str(text)).casefold().split())


def _names(node):
    return {_norm(node["name"]), *(_norm(a["name"] if isinstance(a, dict) else a) for a in node.get("aliases", []))}


def _stripped(name):
    for prefix in GENERIC_PREFIXES:
        if name.startswith(prefix) and len(name) > len(prefix):
            return name[len(prefix):]
    return name


def identity_candidates(nodes):
    rows = []
    for left, right in combinations(sorted(nodes, key=lambda n: n["node_id"]), 2):
        reasons = []
        if _names(left) & _names(right):
            reasons.append("shared_name_or_alias")
        elif {_stripped(n) for n in _names(left)} & {_stripped(n) for n in _names(right)}:
            reasons.append("generic_prefix")
        a, b = left.get("anchor"), right.get("anchor")
        if a and b and (a["chunk_id"], a["char_start"]) == (b["chunk_id"], b["char_start"]):
            reasons.append("same_anchor")
        if reasons:
            rows.append({"left": left["node_id"], "right": right["node_id"], "reasons": reasons})
    return rows


def apply_identity_map(edges, identity):
    """Chuyển cạnh sang khái niệm đại diện, bỏ cạnh tự nối và cạnh trùng; báo chu trình mà phép gộp sinh ra.

    Gộp có thể tạo chu trình (a → b → a' với a' gộp vào a), nên kết quả phải qua bước gỡ chu trình của A9.
    """
    merged, seen = [], set()
    for edge in edges:
        source, target = identity.get(edge["source"], edge["source"]), identity.get(edge["target"], edge["target"])
        if source == target or (source, target) in seen:
            continue
        seen.add((source, target))
        merged.append({**edge, "source": source, "target": target})
    nodes = {n for pair in seen for n in pair}
    cycles = sorted(sorted(c) for c in strongly_connected_components(nodes, merged) if len(c) > 1)
    return merged, cycles
