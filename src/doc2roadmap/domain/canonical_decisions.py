from __future__ import annotations

import re
import unicodedata

from .canonical import normalize_edge_type
from .entities import validate_llm_edge_type


def vietnamese(text):
    words = re.findall(r"[^\W\d_]+", unicodedata.normalize("NFC", text))
    accented = sum(any(c in "ăâđêôơưĂÂĐÊÔƠƯ" or any(mark in unicodedata.normalize("NFD", c)
                   for mark in "\u0300\u0301\u0303\u0309\u0323") for c in word) for word in words)
    return bool(words) and accented/len(words) >= .2


NON_PROSE = {"table", "code", "formula", "figure"}


def document_language(chunks):
    chunks = list(chunks)
    prose = [c for c in chunks if not set(getattr(c, "block_types", None) or ["text"]) <= NON_PROSE] or chunks
    vi = sum(c.token_count for c in prose if vietnamese(c.text))
    total = sum(c.token_count for c in prose)
    return "vi" if vi * 2 >= total else "en"


def validate_partition(value, source):
    if not isinstance(value, dict) or set(value) != {"nodes", "relations", "deferred"}:
        raise ValueError("cần nodes, relations, deferred")
    ids = set(source)
    seen, owner = [], {}
    for i, node in enumerate(value["nodes"]):
        if not node["groups"] or not isinstance(node["reason"], str) or not node["reason"].strip():
            raise ValueError("node rỗng hoặc thiếu lý do")
        for group in node["groups"]:
            seen.append(group); owner[group] = i
    for item in value["deferred"]:
        if not item["reason"]:
            raise ValueError("deferred thiếu lý do")
        seen.append(item["group_id"])
    if len(seen) != len(set(seen)) or set(seen) != ids:
        missing, extra = sorted(ids - set(seen)), sorted(set(seen) - ids)
        repeated = sorted({group for group in seen if seen.count(group) > 1})
        raise ValueError(f"mỗi nhóm phải có đúng một lần: thiếu {missing}, lặp {repeated}, id lạ {extra}")
    for edge in value["relations"]:
        if not isinstance(edge, dict) or set(edge) != {"source", "target", "edge_type", "chunk_ids", "reason"}:
            raise ValueError("mỗi relation cần source, target, edge_type, chunk_ids, reason")
    return value


def split_relation_edges(value, source):
    owner = {group: i for i, node in enumerate(value["nodes"]) for group in node["groups"]}
    kept, rejected = {}, []
    for edge in value["relations"]:
        a, b = edge["source"], edge["target"]
        allowed = sorted(set(source.get(a, ())) | set(source.get(b, ())))
        if a not in owner or b not in owner or owner[a] == owner[b]:
            rejected.append({**edge, "invalid_chunk_ids": [], "allowed_chunk_ids": allowed,
                             "error": f"relation {a} → {b} phải nối hai node khác nhau, không deferred"})
            continue
        invalid = sorted(set(edge["chunk_ids"]) - set(allowed))
        if not edge["chunk_ids"] or invalid:
            rejected.append({**edge, "invalid_chunk_ids": invalid, "allowed_chunk_ids": allowed,
                             "error": f"relation {a} → {b}: chunk sai {invalid}, hợp lệ {allowed}"})
            continue
        if not isinstance(edge["reason"], str) or not edge["reason"].strip():
            rejected.append({**edge, "invalid_chunk_ids": invalid, "allowed_chunk_ids": allowed,
                             "error": f"relation {a} → {b} thiếu lý do"})
            continue
        try:
            edge_type = normalize_edge_type(validate_llm_edge_type(edge["edge_type"]))
        except (AttributeError, ValueError) as error:
            rejected.append({**edge, "invalid_chunk_ids": invalid, "allowed_chunk_ids": allowed,
                             "error": f"relation {a} → {b}: {error}"})
            continue
        if edge_type in {"requires", "illustrates", "tabulates"}:
            rejected.append({**edge, "invalid_chunk_ids": invalid, "allowed_chunk_ids": allowed,
                             "error": f"relation {a} → {b}: kiểu dành riêng {edge_type}"})
            continue
        key = (a, b, edge_type)
        if key not in kept:
            kept[key] = {**edge, "edge_type": edge_type, "chunk_ids": sorted(set(edge["chunk_ids"]))}
        else:
            kept[key]["chunk_ids"] = sorted(set(kept[key]["chunk_ids"]) | set(edge["chunk_ids"]))
    return list(kept.values()), rejected


# A3 already relates the pair in a way that is not "is a kind of". Recorded, not dropped: on the gold set the
# subtype_of was right in almost every such pair (A3 often types a variant as component_of).
SUBTYPE_CONFLICTING_EDGE_TYPES = frozenset(
    {"component_of", "uses", "solves", "prevents", "causes", "computed_by", "contrasts_with"})


def find_subtype_conflicts(edges, relation_edges):
    typed = {}
    for edge in edges:
        if edge["edge_type"] in SUBTYPE_CONFLICTING_EDGE_TYPES:
            typed.setdefault(frozenset((edge["source"], edge["target"])), set()).add(edge["edge_type"])
    conflicts = []
    for edge in relation_edges:
        if edge["edge_type"] != "subtype_of":
            continue
        types = typed.get(frozenset((edge["source"], edge["target"])))
        if types:
            conflicts.append({**edge, "a3_edge_types": sorted(types)})
    return conflicts


def guarded_components(ids, same_pairs, different_pairs):
    parent = {id: id for id in ids}
    def root(x):
        while parent[x] != x:
            x = parent[x]
        return x
    for a, b in same_pairs:
        parent[root(b)] = root(a)
    groups = {}
    for id in ids:
        groups.setdefault(root(id), []).append(id)
    result, conflicts = [], []
    for group in groups.values():
        if any(a in group and b in group for a, b in different_pairs):
            conflicts.append(sorted(group))
            result.extend([id] for id in sorted(group))
        else:
            result.append(sorted(group))
    return result, conflicts


def split_sentences(text):
    # ponytail: punctuation-based boundary; ambiguous abbreviations may require a retry.
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]


def validate_description(value, allowed, language=None):
    if not isinstance(value, dict) or set(value) != {"sentences", "defining_chunk_ids", "nghi_gop_nham", "reason"}:
        raise ValueError("mô tả sai khuôn")
    if not 1 <= len(value["sentences"]) <= 4:
        raise ValueError("mô tả phải có 1–4 câu")
    cited = set()
    for index, sentence in enumerate(value["sentences"], 1):
        if not isinstance(sentence["text"], str) or not sentence["text"].strip():
            raise ValueError("câu mô tả rỗng")
        if len(split_sentences(sentence["text"])) != 1:
            raise ValueError("mỗi phần tử chỉ được chứa một câu kèm trích dẫn riêng")
        invalid = sorted(set(sentence["chunk_ids"]) - set(allowed))
        if not sentence["chunk_ids"] or invalid:
            raise ValueError(f"câu {index}: chunk sai {invalid}, hợp lệ {sorted(allowed)}")
        cited.update(sentence["chunk_ids"])
    text = " ".join(s["text"] for s in value["sentences"])
    if language is not None and ("vi" if vietnamese(text) else "en") != language:
        raise ValueError("mô tả khác ngôn ngữ chủ đạo của tài liệu")
    invalid = sorted(set(value["defining_chunk_ids"]) - cited)
    if invalid:
        raise ValueError(f"defining_chunk_ids ngoài trích dẫn: {invalid}; đã trích {sorted(cited)}")
    if not isinstance(value["nghi_gop_nham"], bool) or not isinstance(value["reason"], str):
        raise ValueError("cờ mâu thuẫn sai kiểu")
    if value["nghi_gop_nham"] and not value["reason"].strip():
        raise ValueError("cờ mâu thuẫn thiếu lý do")
    return value
