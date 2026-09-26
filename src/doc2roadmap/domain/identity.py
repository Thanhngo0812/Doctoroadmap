from __future__ import annotations

import unicodedata
import re
from itertools import combinations

from .anchors import _compact
from .global_validation import _feedback_edges, strongly_connected_components
from .topic_graph import _dot, _unit

# Danh tính (spec v2, W14–W15). Ứng viên chỉ từ tín hiệu hẹp; mọi ứng viên phải qua phán — chung tên hay chung alias
# là lý do đưa ra xét, không phải bằng chứng trùng. "Tên này chứa tên kia" bị loại có chủ ý: `Ma trận` nằm trong
# `Ma trận nghịch đảo` mà hai khái niệm khác hẳn nhau.
VERDICTS = ("same", "different", "sense_split")
GENERIC_PREFIXES = ("hệ véc tơ ", "hệ vectơ ", "hệ vector ", "tính ", "khái niệm ", "the notion of ", "the concept of ",
                    "hệ ", "phép ")
SEMANTIC_TOP_K = 3
SEMANTIC_MIN_SIMILARITY = 0.85


def _norm(text):
    return " ".join(unicodedata.normalize("NFC", str(text)).casefold().split())


def _names(node):
    return {_norm(node["name"]), *(_norm(a["name"] if isinstance(a, dict) else a) for a in node.get("aliases", []))}


def _stripped(name):
    for prefix in GENERIC_PREFIXES:
        if name.startswith(prefix) and len(name) > len(prefix):
            return name[len(prefix):]
    return name


def _initialism(name):
    folded = "".join(c for c in unicodedata.normalize("NFD", name).replace("đ", "d")
                     if not unicodedata.combining(c))
    words = re.findall(r"[^\W\d_]+", folded)
    return "".join(w[0] for w in words) if len(words) >= 2 else None


def _normalized(name):
    # _compact giữ gạch nối để khớp câu; danh tính coi gạch nối giữa các từ và khoảng trắng tương đương.
    return re.sub(r"(?<=[^\W\d_])-(?=[^\W\d_])", "", _compact(name))


def identity_candidates(nodes, *, vectors=None, semantic_top_k=SEMANTIC_TOP_K,
                        semantic_min_similarity=SEMANTIC_MIN_SIMILARITY):
    if type(semantic_top_k) is not int or semantic_top_k < 1:
        raise ValueError("semantic_top_k phải là số nguyên dương")
    if not 0 <= semantic_min_similarity <= 1:
        raise ValueError("semantic_min_similarity phải thuộc [0, 1]")
    ordered = sorted(nodes, key=lambda n: n["node_id"])
    names = {n["node_id"]: _names(n) for n in ordered}
    normalized = {key: {_normalized(n) for n in values if _normalized(n)} for key, values in names.items()}
    initials = {key: {_initialism(n) for n in values} - {None} for key, values in names.items()}
    vectors = {n["node_id"]: _unit(vectors[n["node_id"]]) for n in ordered
               if vectors is not None and n["node_id"] in vectors}
    similar = set()
    for left in sorted(vectors):
        nearest = sorted(((_dot(vectors[left], vectors[right]), right) for right in vectors if right != left),
                         key=lambda row: (-row[0], row[1]))[:semantic_top_k]
        for score, right in nearest:
            if score >= semantic_min_similarity:
                similar.add(tuple(sorted((left, right))))
    rows = []
    for left, right in combinations(ordered, 2):
        a_id, b_id = left["node_id"], right["node_id"]
        reasons = []
        if names[a_id] & names[b_id]:
            reasons.append("shared_name_or_alias")
        elif normalized[a_id] & normalized[b_id]:
            reasons.append("normalized_name")
        elif {_normalized(_stripped(n)) for n in names[a_id]} & {_normalized(_stripped(n)) for n in names[b_id]}:
            reasons.append("generic_prefix")
        if (names[a_id] & initials[b_id]) or (names[b_id] & initials[a_id]):
            reasons.append("initialism")
        if (a_id, b_id) in similar:
            reasons.append("description_similarity")
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


def validate_identity_response(value, *, pair_id):
    if not isinstance(value, dict) or value.get("pair_id") != pair_id:
        raise ValueError("phán quyết sai pair_id")
    if value.get("verdict") not in VERDICTS:
        raise ValueError("verdict ngoài ba giá trị cho phép")
    if not isinstance(value.get("reason"), str) or not value["reason"].strip():
        raise ValueError("phán quyết thiếu reason")


def identity_map(verdicts, position):
    """Bản đồ `node → đại diện` từ các phán `same`; đại diện là khái niệm được dạy sớm nhất trong nhóm.

    Chỉ gộp nhóm mà mọi cặp đều được phán `same`: a≈b và b≈c không đủ để gộp a với c khi chưa ai so a với c. Nhóm như vậy
    trả về là nhóm mở (tính vào Q2), không gộp phần nào của nó.
    """
    same = {frozenset((row["left"], row["right"])) for row in verdicts if row["verdict"] == "same"}
    parent = {}

    def find(node):
        while parent.setdefault(node, node) != node:
            node = parent[node]
        return node

    for pair in same:
        left, right = sorted(pair)
        parent[find(left)] = find(right)
    groups = {}
    for node in parent:
        groups.setdefault(find(node), []).append(node)
    mapping, open_groups = {}, []
    for members in groups.values():
        if len(members) < 2:
            continue
        if not all(frozenset(pair) in same for pair in combinations(members, 2)):
            open_groups.append(sorted(members))
            continue
        head = min(members, key=lambda node: (position.get(node, float("inf")), node))
        mapping.update({node: head for node in members if node != head})
    return dict(sorted(mapping.items())), sorted(open_groups)


def merge_and_break_cycles(edges, identity):
    """Áp bản đồ rồi gỡ chu trình mà phép gộp sinh ra bằng đúng hàm gỡ của A9 (thuần, không gọi mô hình)."""
    merged, cycles = apply_identity_map(edges, identity)
    removed = []
    for component in cycles:
        members = set(component)
        internal = [edge for edge in merged if edge["source"] in members and edge["target"] in members]
        removed += _feedback_edges(sorted(members), internal)[0]
    dropped = {id(edge) for edge in removed}
    return [edge for edge in merged if id(edge) not in dropped], removed
