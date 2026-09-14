from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import asdict
from itertools import combinations

from .entities import EntityCandidate
from .normalization import normalize_text


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def unaccented(text: str) -> str:
    text = unicodedata.normalize("NFD", normalize_text(text).casefold()).replace("đ", "d")
    return " ".join(re.findall(r"[^\W_]+", "".join(c for c in text if not unicodedata.combining(c))))


def name_key(text: str) -> str:
    text = " ".join(normalize_text(text).casefold().split())
    tones = "\u0300\u0301\u0303\u0309\u0323"
    decomposed = unicodedata.normalize("NFD", text)
    # Only relocate tone marks; never change base letters (notably y/i).
    pattern = rf"([ou])([{tones}]?)([aey])([{tones}]?)"
    decomposed = re.sub(pattern, lambda m: m[1] + m[3] + m[2] + m[4], decomposed)
    return unicodedata.normalize("NFC", decomposed)


def alias_kind(text: str) -> str:
    text = normalize_text(text).strip()
    if len(text) > 1 and text.isalnum() and text.isupper() and any(c.isalpha() for c in text):
        return "abbreviation"
    words = re.findall(r"[^\W\d_]+", text)
    lexical = [w for w in words if len(w) > 1 and any("LATIN" in unicodedata.name(c, "") for c in w)]
    return "name" if lexical else "symbol"


def evidence_missing_name(entity: EntityCandidate) -> bool:
    if entity.is_media or (entity.media_evidence_id and not entity.evidence):
        return False
    names = [unaccented(entity.name), *(unaccented(a.name) for a in entity.aliases)]
    return not any(f" {name} " in f" {unaccented(e.quote)} "
                   for name in names if name for e in entity.evidence)


def candidate_warnings(entities, chunk_sections) -> dict:
    descriptions = defaultdict(list)
    missing = []
    for entity in entities:
        if entity.is_media:
            continue
        if evidence_missing_name(entity):
            missing.append(entity.candidate_id)
        if entity.description:
            for section in {chunk_sections[c] for c in entity.source_chunk_ids if c in chunk_sections}:
                descriptions[(section, " ".join(entity.description.split()))].append(entity)
    duplicates = [{"section_id": section, "description": description,
                   "names": sorted({e.name for e in members}),
                   "candidate_ids": sorted({e.candidate_id for e in members})}
                  for (section, description), members in sorted(descriptions.items())
                  if len({name_key(e.name) for e in members}) > 1]
    warnings = ["duplicate_description: " + ", ".join(item["names"]) for item in duplicates]
    warnings += ["evidence_missing_name: " + candidate_id for candidate_id in sorted(missing)]
    return {"duplicate_descriptions": duplicates, "evidence_missing_name": sorted(missing),
            "duplicate_description_count": len(duplicates),
            "duplicate_description_name_count": sum(len(d["names"]) for d in duplicates),
            "evidence_missing_name_count": len(missing), "warnings": warnings}


def name_tier(name: str) -> int:
    """Rank plain names before symbol-suffixed names, abbreviations, and symbols."""
    kind = alias_kind(name)
    if kind == "name":
        return 1 if any(alias_kind(token) == "symbol" for token in normalize_text(name).split()) else 0
    return 2 if kind == "abbreviation" else 3


def name_counts(keys, text: str) -> dict:
    """Count longer names first so nested occurrences are not counted twice."""
    counts = {}
    for key in sorted(keys, key=lambda value: (-len(value), value)):
        pattern = r"(?<!\w)" + re.escape(key) + r"(?!\w)"
        counts[key] = len(re.findall(pattern, text))
        text = re.sub(pattern, " \x00 ", text)
    return counts


def group_names(entities) -> list[list[EntityCandidate]]:
    groups = defaultdict(list)
    for entity in entities:
        key = ("media", entity.node_type, entity.media_id) if entity.is_media else ("text", name_key(entity.name))
        groups[key].append(entity)
    return [sorted(members, key=lambda e: (e.first_order_index, e.candidate_id))
            for _, members in sorted(groups.items())]


def build_nodes(groups, document_text: str, type_aliases=None):
    type_aliases = type_aliases or {}
    def node_type(e):
        key = " ".join(e.node_type.casefold().split())
        return type_aliases.get(key, key)
    frequency = Counter(node_type(e) for group in groups for e in group if not e.is_media)
    text = name_key(document_text)
    nodes, log, review = [], [], []
    for members in groups:
        members = sorted(members, key=lambda e: (e.first_order_index, e.candidate_id))
        anchor = members[0]
        node_id = anchor.candidate_id if anchor.is_media else "node_" + digest([anchor.doc_id, anchor.candidate_id])[:24]
        choices = [e for e in members if name_tier(e.name) < 3]
        if not choices and not anchor.is_media:
            raise ValueError(f"node chỉ có tên ký hiệu: {anchor.candidate_id}")
        if anchor.is_media:
            chosen = anchor
        else:
            counts = name_counts({name_key(e.name) for e in choices}, text)
            tier = min(name_tier(e.name) for e in choices)
            pool = [e for e in choices if name_tier(e.name) == tier]
            top = max(counts[name_key(e.name)] for e in pool)
            tied_names = [e for e in pool if counts[name_key(e.name)] == top]
            keys = {name_key(e.name) for e in tied_names}
            fuller = [e for e in tied_names if not any(
                other != name_key(e.name) and re.search(
                    r"(?<!\w)" + re.escape(name_key(e.name)) + r"(?!\w)", other
                )
                for other in keys
            )]
            chosen = min(fuller, key=lambda e: (e.first_order_index, e.candidate_id))
        votes = Counter(node_type(e) for e in members)
        tied_types = [kind for kind, n in votes.items() if n == max(votes.values())]
        kind = min(tied_types, key=lambda k: (k == "concept", -frequency[k], k))
        voting = [e.learnable for e in members if node_type(e) == kind]
        learnable = not anchor.is_media and sum(voting) * 2 >= len(voting)
        if len(tied_types) > 1:
            log.append({"action": "type_tie", "members": [e.candidate_id for e in members],
                        "votes": dict(votes), "selected": kind,
                        "rule": "specific_then_document_frequency_then_alphabetical"})
        if len({node_type(e) for e in members}) > 1 and len({e.learnable for e in members}) > 1:
            review.append({"node_id": node_id, "reason": "cross_type_learnable_conflict"})
        aliases, symbols = [], []
        for e in members:
            alternatives = [(a.name, asdict(a.evidence)) for a in e.aliases]
            if e.name != chosen.name:
                alternatives.extend((e.name, asdict(span)) for span in e.evidence)
            for name, evidence in alternatives:
                if alias_kind(name) != "symbol" and name_key(name) == name_key(chosen.name):
                    continue
                entry = {"name": name, "evidence": evidence, "candidate_id": e.candidate_id}
                collection = symbols if alias_kind(name) == "symbol" else aliases
                if entry not in collection:
                    collection.append(entry)
        nodes.append({"node_id": node_id, "anchor_candidate_id": anchor.candidate_id,
                      "name": chosen.name, "node_type": kind, "learnable": learnable,
                      "members": [e.candidate_id for e in members], "aliases": aliases, "symbols": symbols,
                      "source_chunk_ids": sorted({c for e in members for c in e.source_chunk_ids}),
                      "evidence": [asdict(span) for e in members for span in e.evidence],
                      "source_refs": [asdict(ref) for e in members for ref in e.source_refs],
                      "first_order_index": min(e.first_order_index for e in members),
                      "first_mention_index": min(e.first_order_index for e in members),
                      "description": anchor.description, "media_id": anchor.media_id,
                      "caption_source": anchor.caption_source, "orphan_reason": anchor.orphan_reason})
    return nodes, log, review


def remap_edges(nodes, edges):
    mapping = {candidate: n["node_id"] for n in nodes for candidate in n["members"]}
    result, self_edges, duplicates = {}, 0, 0
    for edge in edges:
        source, target = mapping[edge.source_candidate_id], mapping[edge.target_candidate_id]
        if source == target:
            self_edges += 1
            continue
        key = (source, target, " ".join(edge.edge_type.casefold().split()))
        if key not in result:
            result[key] = {"source": source, "target": target, "edge_type": key[2],
                           "evidence": [], "source_refs": [], "confirmed": False, "proposal": True}
        else:
            duplicates += 1
        row = result[key]
        row["confirmed"] |= edge.confirmed
        for attr in ("evidence", "source_refs"):
            for value in getattr(edge, attr):
                if asdict(value) not in row[attr]:
                    row[attr].append(asdict(value))
    for node in nodes:
        if node["media_id"]:
            has_edge = any(e["source"] == node["node_id"] and e["edge_type"] in {"illustrates", "tabulates"}
                           for e in result.values())
            node["orphan_reason"] = None if has_edge else node["orphan_reason"] or "unknown"
    return list(result.values()), {"a3_edge_count": len(edges), "self_edges_removed": self_edges,
                                  "duplicate_edges_removed": duplicates, "edge_count": len(result)}


def member_pairs(nodes):
    return {pair for n in nodes for pair in combinations(sorted(n["members"]), 2)}


def compare_nodes(first, second):
    def jaccard(a, b):
        return len(a & b) / len(a | b) if a | b else 1.0
    a, b = {n["node_id"] for n in first}, {n["node_id"] for n in second}
    return {"nodes": jaccard(a, b), "members": jaccard(member_pairs(first), member_pairs(second)),
            "only_first": len(a - b), "only_second": len(b - a)}


def redirects(previous, current, old_redirects=None):
    active = {n["node_id"] for n in current}
    result = dict(old_redirects or {})
    for node in previous:
        if node["node_id"] in active:
            continue
        candidates = sorted(current, key=lambda n: (-len(set(n["members"]) & set(node["members"])), n["node_id"]))
        result[node["node_id"]] = candidates[0]["node_id"] if candidates and set(candidates[0]["members"]) & set(node["members"]) else None
    for key in list(result):
        if key in active:
            del result[key]
            continue
        target, seen = result[key], {key}
        while target in result and target not in seen:
            seen.add(target)
            target = result[target]
        result[key] = target if target in active else None
    return result
