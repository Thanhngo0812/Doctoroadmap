from __future__ import annotations

from collections import defaultdict
import re
import unicodedata

from .sentence_splitter import UnicodeSentenceSplitter
from .anchors import heading_chunks


EVIDENCE_CONFIDENCE = {
    "noi_ro": 0.9,
    "trong_dinh_nghia": 0.9,
    "mach_trinh_bay": 0.7,
}
HARD_MENTION_CHANNELS = {"provenance", "extraction", "exact"}
REVERSE_ORDER_PENALTY = 0.1


def plan_main_sessions(nodes, chunks, sections, mention_map, *, single_limit):
    learnable = [node for node in nodes if node.get("learnable") and not node.get("merged_into")
                 and node.get("teaching_status", "taught") in {"taught", "uncertain"}]
    node_by_id = {node["node_id"]: node for node in learnable}
    chunk_by_id = {chunk.chunk_id: chunk for chunk in chunks}

    def allowed(chunk_ids, targets):
        result = set(targets)
        for chunk_id in chunk_ids:
            result.update(node_id for node_id in mention_map.get(chunk_id, {}) if node_id in node_by_id)
        return sorted(result)

    if len(learnable) <= single_limit:
        return [{
            "session_id": "main_single",
            "route": "single",
            "chapter_id": "document",
            "sequence": 0,
            "chunk_ids": [chunk.chunk_id for chunk in sorted(chunks, key=lambda value: (value.order_index, value.chunk_id))],
            "target_node_ids": sorted(node_by_id),
            "allowed_node_ids": sorted(node_by_id),
        }]

    section_by_id = {section.section_id: section for section in sections}
    heading_levels = {
        section.level
        for section in sections
        if section.level > 0
    }
    hierarchical = len(heading_levels) >= 2
    if hierarchical:
        def chapter(section_id):
            current = section_by_id[section_id]
            while current.level > 1 and current.parent_section_id in section_by_id:
                current = section_by_id[current.parent_section_id]
            return current.section_id

        rows = []
        for section in sorted(sections, key=lambda value: (value.order_index, value.section_id)):
            chunk_ids = [
                chunk.chunk_id
                for chunk in sorted(chunks, key=lambda value: (value.order_index, value.chunk_id))
                if chunk.parent_section_id == section.section_id
            ]
            if not chunk_ids:
                continue
            target_ids = sorted(
                node_id
                for node_id, node in node_by_id.items()
                if set(node.get("defining_chunk_ids", [])) & set(chunk_ids)
            )
            if not target_ids:
                continue
            rows.append({
                "session_id": "main_section_" + section.section_id,
                "route": "chapter",
                "chapter_id": chapter(section.section_id),
                "sequence": 0,
                "chunk_ids": chunk_ids,
                "target_node_ids": target_ids,
                "allowed_node_ids": allowed(chunk_ids, target_ids),
            })
        sequence = defaultdict(int)
        for row in rows:
            row["sequence"] = sequence[row["chapter_id"]]
            sequence[row["chapter_id"]] += 1
        return rows

    rows = []
    clusters = sorted({node["cluster_id"] for node in learnable})
    for cluster_id in clusters:
        target_ids = sorted(node["node_id"] for node in learnable if node["cluster_id"] == cluster_id)
        chunk_ids = sorted(
            {
                chunk_id
                for node_id in target_ids
                for chunk_id in node_by_id[node_id].get("defining_chunk_ids", [])
                if chunk_id in chunk_by_id
            },
            key=lambda chunk_id: (chunk_by_id[chunk_id].order_index, chunk_id),
        )
        rows.append({
            "session_id": "main_cluster_" + cluster_id,
            "route": "topic_cluster",
            "chapter_id": cluster_id,
            "sequence": 0,
            "chunk_ids": chunk_ids,
            "target_node_ids": target_ids,
            "allowed_node_ids": allowed(chunk_ids, target_ids),
        })
    return rows


def validate_main_response(value):
    if not isinstance(value, dict) or not isinstance(value.get("edges"), list) or not isinstance(value.get("flags"), list):
        raise ValueError("đầu ra pass chính cần edges và flags dạng mảng")
    for edge in value["edges"]:
        if not isinstance(edge, dict):
            raise ValueError("edge phải là object")
        for key in ("target", "prerequisite", "evidence_kind", "reason"):
            if not isinstance(edge.get(key), str) or not edge[key].strip():
                raise ValueError(f"edge thiếu chuỗi {key}")
        if not isinstance(edge.get("chunk_ids"), list) or not all(isinstance(item, str) for item in edge["chunk_ids"]):
            raise ValueError("edge cần chunk_ids dạng mảng chuỗi")
    for flag in value["flags"]:
        if not isinstance(flag, dict) or not isinstance(flag.get("kind"), str):
            raise ValueError("flag cần kind")


def definition_window(node, chunks, *, before=4, after=2):
    anchor = node.get("anchor") or {}
    chunk = next((row for row in chunks if row.chunk_id == anchor.get("chunk_id")), None)
    sentence = anchor.get("sentence")
    if chunk is None or not isinstance(sentence, str) or not sentence:
        return ""
    text = unicodedata.normalize("NFC", chunk.text)
    start = text.find(unicodedata.normalize("NFC", sentence), max(0, int(anchor.get("char_start", 0)) - 8))
    if start < 0:
        start = text.find(unicodedata.normalize("NFC", sentence))
    if start < 0:
        return ""
    boundaries = list(re.finditer(r"\n\s*\n", text))
    paragraph_start = max((match.end() for match in boundaries if match.end() <= start), default=0)
    paragraph_end = min((match.start() for match in boundaries if match.start() > start), default=len(text))
    paragraph = text[paragraph_start:paragraph_end]
    spans = UnicodeSentenceSplitter().split(paragraph)
    local_start = start - paragraph_start
    index = next((i for i, span in enumerate(spans) if span.start <= local_start < span.end), None)
    if index is None:
        return ""
    window = paragraph[spans[max(0, index - before)].start:spans[min(index + after, len(spans) - 1)].end]
    heading = heading_chunks(node, [chunk]).get(chunk.chunk_id)
    if heading and heading[1] <= start:
        window = heading[0] + "\n" + window
    return window


def _order_relation(source, target, node_by_id, chunk_by_id):
    source_chunks = set(node_by_id[source].get("defining_chunk_ids", []))
    target_chunks = set(node_by_id[target].get("defining_chunk_ids", []))
    if source_chunks & target_chunks:
        return "cùng chunk"
    source_order = min((chunk_by_id[value].order_index for value in source_chunks if value in chunk_by_id), default=10**18)
    target_order = min((chunk_by_id[value].order_index for value in target_chunks if value in chunk_by_id), default=10**18)
    return "thuận" if source_order <= target_order else "ngược"


def _source_quote(quote, text):
    if not isinstance(quote, str) or not quote.split():
        return None
    match = re.search(r"\s+".join(re.escape(part) for part in quote.split()), text)
    return match.group(0) if match else None


def validate_main_proposals(output, session, nodes, chunks, mention_map, *, existing_edges, require_kind=False,
                            definition_before=4, definition_after=2):
    validate_main_response(output)
    node_by_id = {node["node_id"]: node for node in nodes}
    chunk_by_id = {chunk.chunk_id: chunk for chunk in chunks}
    allowed = set(session["allowed_node_ids"])
    existing = {(edge["source"], edge["target"], edge.get("edge_type", "requires")):
                not edge.get("soft") for edge in existing_edges}
    accepted, flags, log, retry = [], [], [], []
    for index, edge in enumerate(output["edges"]):
        source, target = edge["prerequisite"], edge["target"]
        evidence_ids = list(edge["chunk_ids"])
        quote = edge.get("quote")
        window_quote = None
        if target in node_by_id and edge.get("prerequisite_kind") == "can_de_hieu":
            anchor_id = (node_by_id[target].get("anchor") or {}).get("chunk_id")
            window = definition_window(node_by_id[target], chunks, before=definition_before, after=definition_after)
            window_quote = _source_quote(quote, window)
            if anchor_id in chunk_by_id and window_quote:
                if anchor_id not in evidence_ids:
                    evidence_ids.append(anchor_id)
        evidence_quote = None
        for chunk_id in evidence_ids:
            if chunk_id in chunk_by_id:
                evidence_quote = _source_quote(quote, chunk_by_id[chunk_id].text)
                if evidence_quote:
                    break
        error = None
        if source not in node_by_id or target not in node_by_id:
            error = "unknown_node"
        elif source not in allowed or target not in allowed:
            error = "outside_session"
        elif node_by_id[target].get("teaching_status") in {"mentioned_only", "unchecked", "prior_knowledge", "not_subject_matter"}:
            error = "target_not_taught"
        elif not node_by_id[source].get("learnable") or not node_by_id[target].get("learnable"):
            error = "non_learnable_node"
        elif "confidence" in edge:
            error = "model_confidence_forbidden"
        elif edge.get("edge_type", "requires") != "requires":
            error = "relation_type_must_be_requires"
        elif edge["evidence_kind"] == "suy_doan":
            error = "speculative_evidence"
        elif edge["evidence_kind"] not in EVIDENCE_CONFIDENCE:
            error = "unknown_evidence_kind"
        elif require_kind and edge.get("prerequisite_kind") not in {"can_de_hieu", "cong_cu"}:
            error = "unknown_prerequisite_kind"
        elif not evidence_ids or any(chunk_id not in chunk_by_id for chunk_id in evidence_ids):
            error = "unknown_evidence_chunk"
        elif require_kind and not evidence_quote:
            error = "quote_outside_evidence_chunk"
        elif edge.get("prerequisite_kind") == "can_de_hieu" and (
            (node_by_id[target].get("anchor") or {}).get("chunk_id") not in evidence_ids
        ):
            error = "definition_chunk_not_cited"
        elif edge.get("prerequisite_kind") != "can_de_hieu" and any(
            source not in mention_map.get(chunk_id, {}) or target not in mention_map.get(chunk_id, {})
            for chunk_id in evidence_ids
        ):
            error = "evidence_missing_both_endpoints"
        elif edge.get("prerequisite_kind") == "can_de_hieu" and (
            not window_quote
        ):
            error = "quote_outside_definition_window"
        if error:
            row = {"session_id": session["session_id"], "operation_index": index, "status": "rejected", "error": error, "operation": edge}
            log.append(row)
            retry.append({"operation_index": index, "error": error, "operation": edge})
            continue
        key = (source, target, "requires")
        if source == target:
            log.append({"session_id": session["session_id"], "operation_index": index, "status": "dropped_self", "operation": edge})
            continue
        if key in existing and (existing[key] or edge.get("prerequisite_kind") != "can_de_hieu"):
            log.append({"session_id": session["session_id"], "operation_index": index, "status": "dropped_duplicate", "operation": edge})
            continue
        order_relation = _order_relation(source, target, node_by_id, chunk_by_id)
        if order_relation == "ngược" and edge["evidence_kind"] not in {"noi_ro", "trong_dinh_nghia"}:
            error = "reverse_order_requires_explicit_evidence"
        if error:
            row = {"session_id": session["session_id"], "operation_index": index, "status": "rejected", "error": error, "operation": edge}
            log.append(row)
            retry.append({"operation_index": index, "error": error, "operation": edge})
            continue
        confidence = EVIDENCE_CONFIDENCE[edge["evidence_kind"]]
        if order_relation == "ngược":
            confidence -= REVERSE_ORDER_PENALTY
        evidence_hard = any(
            bool(HARD_MENTION_CHANNELS & set(mention_map.get(chunk_id, {}).get(source, {}).get("channels", [])))
            and bool(HARD_MENTION_CHANNELS & set(mention_map.get(chunk_id, {}).get(target, {}).get("channels", [])))
            for chunk_id in evidence_ids
        )
        proposal = {
            "source": source,
            "target": target,
            "edge_type": "requires",
            "evidence_kind": edge["evidence_kind"],
            "chunk_ids": sorted(set(evidence_ids)),
            "reason": edge["reason"],
            **({"prerequisite_kind": edge["prerequisite_kind"]} if edge.get("prerequisite_kind") else {}),
            **({"quote": evidence_quote or quote} if quote else {}),
            **({"soft": True, "soft_reason": "cong_cu"} if edge.get("prerequisite_kind") == "cong_cu" else {}),
            "confidence": confidence,
            "explicit_evidence": edge["evidence_kind"] in {"noi_ro", "trong_dinh_nghia"},
            "evidence_hard": evidence_hard,
            "order_relation": order_relation,
            "session_id": session["session_id"],
            "operation_index": index,
        }
        accepted.append(proposal)
        log.append({"session_id": session["session_id"], "operation_index": index, "status": "accepted", "edge": proposal})
    for index, flag in enumerate(output["flags"]):
        flags.append({**flag, "session_id": session["session_id"], "operation_index": index})
        log.append({"session_id": session["session_id"], "flag_index": index, "status": "flagged", "flag": flags[-1]})
    return accepted, flags, log, retry


def merge_main_proposals(proposals, existing_edges):
    result = [dict(edge) for edge in existing_edges]
    seen = {(edge["source"], edge["target"], edge.get("edge_type", "requires")) for edge in result}
    log = []
    ordered = sorted(
        proposals,
        key=lambda edge: (
            edge.get("session_id", ""),
            edge.get("operation_index", 0),
            edge["source"],
            edge["target"],
        ),
    )
    for edge in ordered:
        key = (edge["source"], edge["target"], edge.get("edge_type", "requires"))
        if key in seen:
            log.append({"session_id": edge.get("session_id"), "operation_index": edge.get("operation_index"), "status": "dropped_duplicate", "edge": edge})
            continue
        seen.add(key)
        result.append(dict(edge))
    result.sort(key=lambda edge: (edge["source"], edge["target"], edge.get("session_id", ""), edge.get("operation_index", 0)))
    return result, log
