from __future__ import annotations

import math
import re
import unicodedata
from collections import defaultdict
from itertools import combinations

from .canonical import alias_kind, _legacy_alias_kind, digest, name_key
from .unicode_text import unspaced_character


def _mention_normalize(text):
    decomposed = unicodedata.normalize("NFD", name_key(text))
    decomposed = re.sub(
        r"y([\u0300-\u036f]*)(?=$|[^\w\u0300-\u036f])",
        r"i\1",
        decomposed,
    )
    return unicodedata.normalize("NFC", decomposed)


def _names(node):
    values = [node.get("name", "")]
    for alias in node.get("aliases", []):
        values.append(alias.get("name", "") if isinstance(alias, dict) else str(alias))
    return values


def exact_mentions(nodes, chunks, *, common_names, _legacy=False):
    common = {_mention_normalize(value) for value in common_names}
    pattern_nodes = defaultdict(set)
    for node in nodes:
        if not node.get("learnable"):
            continue
        for value in _names(node):
            normalized = _mention_normalize(value.strip())
            kind = _legacy_alias_kind(value) if _legacy else alias_kind(value)
            if not normalized or normalized in common or kind == "symbol":
                continue
            pattern_nodes[normalized].add(node["node_id"])
    result = {}
    for chunk in chunks:
        text = _mention_normalize(chunk.text)
        candidates = []
        for pattern, node_ids in pattern_nodes.items():
            expression = (re.escape(pattern) if not _legacy and any(map(unspaced_character, pattern))
                          else rf"(?<!\w){re.escape(pattern)}(?!\w)")
            for match in re.finditer(expression, text):
                candidates.append((match.start(), match.end(), pattern, node_ids))
        selected = set()
        covered_until = -1
        for start, end, _, node_ids in sorted(candidates, key=lambda row: (row[0], -(row[1] - row[0]), row[2])):
            if start < covered_until:
                continue
            selected.update(node_ids)
            covered_until = end
        if selected:
            result[chunk.chunk_id] = selected
    return result


def _unit(vector):
    norm = math.sqrt(sum(float(value) ** 2 for value in vector))
    return tuple(float(value) / norm for value in vector) if norm else tuple(0.0 for _ in vector)


def dense_mentions(node_vectors, chunk_vectors, *, top_k, min_z):
    if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 1:
        raise ValueError("dense top_k phải là số nguyên dương")
    node_ids, chunk_ids = sorted(node_vectors), sorted(chunk_vectors)
    nodes = {key: _unit(node_vectors[key]) for key in node_ids}
    chunks = {key: _unit(chunk_vectors[key]) for key in chunk_ids}
    raw = {
        (node_id, chunk_id): sum(
            left * right for left, right in zip(nodes[node_id], chunks[chunk_id], strict=True)
        )
        for node_id in node_ids
        for chunk_id in chunk_ids
    }
    row_mean = {
        node_id: sum(raw[node_id, chunk_id] for chunk_id in chunk_ids) / len(chunk_ids)
        for node_id in node_ids
    } if chunk_ids else {node_id: 0.0 for node_id in node_ids}
    column_mean = {
        chunk_id: sum(raw[node_id, chunk_id] for node_id in node_ids) / len(node_ids)
        for chunk_id in chunk_ids
    } if node_ids else {chunk_id: 0.0 for chunk_id in chunk_ids}
    centered = {
        key: 2.0 * value - row_mean[key[0]] - column_mean[key[1]]
        for key, value in raw.items()
    }
    zscores = {}
    selected = defaultdict(set)
    for node_id in node_ids:
        values = [centered[node_id, chunk_id] for chunk_id in chunk_ids]
        mean = sum(values) / len(values) if values else 0.0
        variance = sum((value - mean) ** 2 for value in values) / len(values) if values else 0.0
        deviation = math.sqrt(variance)
        for chunk_id in chunk_ids:
            zscores[node_id, chunk_id] = (
                (centered[node_id, chunk_id] - mean) / deviation if deviation else 0.0
            )
        ranked = sorted(chunk_ids, key=lambda chunk_id: (-zscores[node_id, chunk_id], chunk_id))
        for chunk_id in ranked[:top_k]:
            if zscores[node_id, chunk_id] >= min_z:
                selected[chunk_id].add(node_id)
    return dict(selected), zscores


def _pair(left, right):
    return tuple(sorted((left, right)))


def build_mention_derivatives(nodes, chunks, mentions, proposed_edges, *, pair_cluster_top_k):
    node_by_id = {node["node_id"]: node for node in nodes if node.get("learnable")}
    chunk_by_id = {chunk.chunk_id: chunk for chunk in chunks}
    citation_chunks = defaultdict(dict)
    for target, node in node_by_id.items():
        for chunk_id in node.get("defining_chunk_ids", []):
            for source, mention in mentions.get(chunk_id, {}).items():
                if (
                    source in node_by_id
                    and source != target
                    and mention.get("level") != "definition"
                ):
                    citation_chunks[source, target][chunk_id] = mention.get("channels", [])
    citations = [
        {
            "source": source,
            "target": target,
            "chunk_ids": sorted(rows),
            "channels": sorted({channel for channels in rows.values() for channel in channels}),
            "strength": "soft" if rows and all(set(channels) <= {"dense"} for channels in rows.values()) else "hard",
        }
        for (source, target), rows in sorted(citation_chunks.items())
    ]

    contact_chunks = defaultdict(set)
    ledger = defaultdict(lambda: {"exact_weight": 0.0, "dense_weight": 0.0, "chunk_ids": set()})
    for chunk_id, rows in mentions.items():
        present = sorted(node_id for node_id in rows if node_id in node_by_id)
        penalty = 1.0 / max(len(present) - 1, 1)
        for left, right in combinations(present, 2):
            left_cluster = node_by_id[left]["cluster_id"]
            right_cluster = node_by_id[right]["cluster_id"]
            if left_cluster == right_cluster:
                continue
            contact_chunks[_pair(left, right)].add(chunk_id)
            cluster_pair = _pair(left_cluster, right_cluster)
            channels = set(rows[left].get("channels", [])) | set(rows[right].get("channels", []))
            if "exact" in channels:
                ledger[cluster_pair]["exact_weight"] += penalty
            if "dense" in channels:
                ledger[cluster_pair]["dense_weight"] += penalty
            ledger[cluster_pair]["chunk_ids"].add(chunk_id)
    contact_pairs = [
        {"left": left, "right": right, "chunk_ids": sorted(chunk_ids)}
        for (left, right), chunk_ids in sorted(contact_chunks.items())
    ]
    means = {}
    for channel in ("exact_weight", "dense_weight"):
        positive = [row[channel] for row in ledger.values() if row[channel] > 0]
        means[channel] = sum(positive) / len(positive) if positive else None
    selected = set()
    for pair, row in ledger.items():
        if any(means[channel] is not None and row[channel] >= means[channel] for channel in means):
            selected.add(pair)
    clusters = sorted({value for pair in ledger for value in pair})
    for cluster in clusters:
        related = [pair for pair in ledger if cluster in pair]
        for channel in ("exact_weight", "dense_weight"):
            selected.update(sorted(related, key=lambda pair: (-ledger[pair][channel], pair))[:pair_cluster_top_k])
    pair_cluster_ledger = [
        {
            "left_cluster": pair[0],
            "right_cluster": pair[1],
            "exact_weight": row["exact_weight"],
            "dense_weight": row["dense_weight"],
            "chunk_ids": sorted(row["chunk_ids"]),
            "selected": pair in selected,
        }
        for pair, row in sorted(ledger.items())
    ]

    sources = defaultdict(set)
    details = defaultdict(lambda: defaultdict(list))
    section_nodes = defaultdict(set)
    for node_id, node in node_by_id.items():
        for chunk_id in node.get("defining_chunk_ids", []):
            if chunk_id in chunk_by_id:
                section_nodes[chunk_by_id[chunk_id].parent_section_id].add(node_id)
    for section_id, node_ids in section_nodes.items():
        for pair in combinations(sorted(node_ids), 2):
            sources[pair].add("same_section")
            details[pair]["same_section"].append(section_id)
    for row in citations:
        pair = _pair(row["source"], row["target"])
        source = "citation_" + row["strength"]
        sources[pair].add(source)
        details[pair][source].extend(row["chunk_ids"])
    for row in contact_pairs:
        pair = _pair(row["left"], row["right"])
        sources[pair].add("contact")
        details[pair]["contact"].extend(row["chunk_ids"])
    for edge in proposed_edges:
        if edge.get("source") not in node_by_id or edge.get("target") not in node_by_id or edge["source"] == edge["target"]:
            continue
        pair = _pair(edge["source"], edge["target"])
        sources[pair].add("proposed_relation")
        details[pair]["proposed_relation"].append(
            {"edge_type": edge.get("edge_type"), "origins": sorted(edge.get("origins", []))}
        )
    suspected_pairs = [
        {
            "pair_id": "pair_" + digest(pair)[:24],
            "left": pair[0],
            "right": pair[1],
            "sources": sorted(values),
            "details": {
                key: sorted(value, key=str)
                for key, value in sorted(details[pair].items())
            },
        }
        for pair, values in sorted(sources.items())
    ]
    return {
        "citations": citations,
        "contact_pairs": contact_pairs,
        "pair_cluster_ledger": pair_cluster_ledger,
        "pair_cluster_relative_means": means,
        "suspected_pairs": suspected_pairs,
    }


def build_mention_map(nodes, chunks, exact, dense, dense_scores):
    result = {}
    for chunk in chunks:
        rows = {}
        for node in nodes:
            if not node.get("learnable"):
                continue
            node_id = node["node_id"]
            channels = []
            if chunk.chunk_id in node.get("defining_chunk_ids", []):
                level = "definition"
                channels.append("provenance")
            elif chunk.chunk_id in node.get("source_chunk_ids", []):
                level = "extracted"
                channels.append("extraction")
            else:
                level = "mention"
            if node_id in exact.get(chunk.chunk_id, set()):
                channels.append("exact")
            if node_id in dense.get(chunk.chunk_id, set()):
                channels.append("dense")
            if not channels:
                continue
            row = {"level": level, "channels": sorted(channels)}
            if level == "definition":
                row["confidence"] = 1.0
            if "dense" in channels:
                row["dense_z"] = dense_scores[node_id, chunk.chunk_id]
            rows[node_id] = row
        if rows:
            result[chunk.chunk_id] = dict(sorted(rows.items()))
    return result
