from __future__ import annotations

import json
import re
import unicodedata
import uuid
from datetime import datetime, timedelta
from collections import Counter
from collections.abc import Callable, Mapping
from inspect import signature
from queue import Empty, Queue
from threading import Thread
from time import perf_counter
from typing import Any
from zoneinfo import ZoneInfo

from doc2roadmap.application.phase_b.common import quote_is_verbatim, stable_json
from doc2roadmap.application.phase_b.budget import DailyLimitExceeded
from doc2roadmap.application.phase_b.budget import DailySpendGuard, spending_call
from doc2roadmap.application.phase_b.clock import SystemClock
from doc2roadmap.domain.phase_b_limits import BSettings, context_hash, lecture_cache_key, usage_row
from doc2roadmap.domain.phase_b_pricing import estimate_cost, token_cost


def _without_learner_status(lecture: dict[str, Any]) -> dict[str, Any]:
    result = json.loads(stable_json(lecture))
    for field in ("prerequisites", "next_up"):
        for item in result.get(field, []):
            item.pop("learner_status", None)
    return result


def _grounded_item_schema() -> dict[str, Any]:
    return {"type": "object", "properties": {
        "text": {"type": "string"}, "sources": {"type": "array", "items": {"type": "string"}},
        "quote": {"type": "string"}, "outside_document": {"type": "boolean"},
        "prereq": {"type": "string"}, "relation": {"type": "string"},
    }, "required": ["text", "sources", "quote", "outside_document"]}


LECTURE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "bridges": {"type": "array", "items": {"type": "object", "properties": {
            "prereq": {"type": "string"}, "text": {"type": "string"},
            "sources": {"type": "array", "items": {"type": "string"}}, "quote": {"type": "string"},
        }, "required": ["prereq", "text", "sources", "quote"]}},
        "explanation": {"type": "array", "items": _grounded_item_schema()},
        "example": {"type": "array", "items": _grounded_item_schema()},
        "contrasts": {"type": "array", "items": _grounded_item_schema()},
        "self_check": {"type": "object", "properties": {
                "kind": {"type": "string"}, "question": {"type": "string"},
                "answer": {"type": "string"}, "sources": {"type": "array", "items": {"type": "string"}},
                "quote": {"type": "string"}},
             "required": ["question", "answer", "sources", "quote"]},
        "gaps": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["bridges", "explanation", "example", "contrasts", "gaps"],
}

_SYSTEM = """Bạn viết bài giảng ngắn bằng tiếng Việt từ các nguồn đã đánh nhãn. Chỉ khẳng định về sách khi có nhãn và quote nguyên văn. Không chép lại công thức; chỉ dùng nhãn công thức. Chỉ giảng khái niệm đích. Với mỗi bridge, chỉ viết câu nối trung tính có trong bridge_candidates, dùng đúng nhãn Q và quote của chính tiên quyết; không viết về người học. Mọi giới hạn dưới đây là bắt buộc.
"""


def _get(value: Any, key: str, default: Any = None) -> Any:
    return value.get(key, default) if isinstance(value, Mapping) else getattr(value, key, default)


def _id(item: Any) -> str:
    return str(_get(item, "chunk_id", ""))


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+|[\r\n]+", text) if part.strip()]


def _trim_context(context: dict[str, Any], settings: BSettings) -> dict[str, Any]:
    """Respect soft budget in the specified drop order without cutting core sources."""
    registry = context.get("registry")
    value = json.loads(stable_json({key: val for key, val in context.items() if key != "registry"}))
    def size() -> int:
        return len(stable_json(value)) // 3
    for key in ("exercise", "next_up", "open_edges", "extra_definitions"):
        while value.get(key) and size() > settings.lecture_context_tokens:
            value[key].pop()
    referenced = set()
    def collect(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key in {"label", "source", "N", "Q"} and isinstance(child, str):
                    referenced.add(child)
                collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)
    collect({key: val for key, val in value.items() if key != "sources"})
    source_map = value.get("sources", {})
    value["sources"] = {label: source for label, source in source_map.items() if label in referenced}
    if registry is not None:
        value["registry"] = registry
    return value


def _next_up(graph: Any, node_id: str, module_id: str, source_registry: Any,
             settings: BSettings) -> list[dict[str, Any]]:
    current_index = int(graph.modules.get(module_id, {}).get("index", 0) or 0)
    candidates = []
    seen = set()
    for edge in graph.payload.get("requires_edges", []):
        target_id = edge.get("target")
        if (edge.get("edge_type", "requires") != "requires" or edge.get("source") != node_id or edge.get("soft") or target_id not in graph.nodes
                or target_id in seen):
            continue
        seen.add(target_id)
        node = graph.nodes[target_id]
        target_module = graph.modules.get(node.get("module_id"), {})
        module_index = int(target_module.get("index", 0) or 0)
        candidates.append((0 if module_index > current_index else 1,
                           abs(module_index - current_index), target_id, edge, node, target_module))
    candidates.sort(key=lambda row: row[:3])
    result = []
    for _, _, target_id, edge, node, target_module in candidates[:settings.next_up_max]:
        item = {"node_id": target_id, "name": node.get("display_name") or node.get("name"),
                "module_index": target_module.get("index"),
                "module_title": target_module.get("display_name") or target_module.get("title"),
                "learner_status": "unknown"}
        evidence = []
        quote = edge.get("quote")
        chunk_ids = list(edge.get("chunk_ids", []))
        if edge.get("quote_chunk_id"):
            chunk_ids.insert(0, edge["quote_chunk_id"])
        for chunk_id in chunk_ids:
            if quote:
                evidence.append((chunk_id, str(quote)))
        for field in ("evidence", "source_refs"):
            for row in edge.get(field, []) or []:
                if isinstance(row, Mapping) and row.get("chunk_id") and row.get("quote"):
                    evidence.append((row["chunk_id"], str(row["quote"])))
        for chunk_id, source_quote in evidence:
            chunk = graph.chunks.get(chunk_id)
            if chunk is None or not quote_is_verbatim(source_quote, _get(chunk, "text", "")):
                continue
            cited = source_registry.citation_for_chunk(chunk_id, "Q", source_quote)
            if cited:
                item.update({"quote": source_quote, "citation": cited[1]})
                break
        result.append(item)
    return result


def _assemble(graph: Any, node_id: str, settings: BSettings, source_registry: Any | None = None) -> tuple[dict[str, Any], dict[str, Any], dict[str, str]]:
    node = graph.nodes.get(node_id)
    if node is None:
        raise KeyError(node_id)
    source_registry = source_registry or (graph.new_source_registry() if hasattr(graph, "new_source_registry") else graph.sources)
    module_id = node.get("module_id")
    module = graph.modules.get(module_id, {})
    node_ids = list(module.get("node_ids", []))
    position_index = node_ids.index(node_id) if node_id in node_ids else -1
    teaching_ids = list(node.get("teaching_chunk_ids") or [])
    defining_ids = list(node.get("defining_chunk_ids") or [])
    teaching_ids = [cid for cid in teaching_ids if cid in graph.chunks]
    defining_ids = [cid for cid in defining_ids if cid in graph.chunks and cid not in teaching_ids]

    sources: dict[str, Any] = {}
    label_to_chunk: dict[str, str] = {}

    def add_chunk(chunk_id: str, family: str, quote: str | None = None) -> str:
        label = source_registry.label(chunk_id, family)
        row = source_registry.resolve(label)
        assert row is not None
        sources[label] = {
            "label": label,
            "chunk_id": chunk_id,
            "page": row.get("page"),
            "section_path": row.get("section_path", []),
            "text": row.get("source_text", ""),
            "quote": quote,
            "citation": source_registry.citation(label, quote) if quote else source_registry.citation(label),
        }
        label_to_chunk[label] = chunk_id
        return label

    anchor = node.get("anchor") or {}
    anchor_sentence = str(anchor.get("sentence") or "")
    anchor_chunk = anchor.get("chunk_id")
    if not anchor_chunk and teaching_ids:
        anchor_chunk = teaching_ids[0]
    if anchor_chunk in graph.chunks:
        s1 = add_chunk(anchor_chunk, "S", anchor_sentence or None)
    elif teaching_ids:
        anchor_chunk = teaching_ids[0]
        s1 = add_chunk(anchor_chunk, "S")
    else:
        s1 = None

    if s1 and not anchor_sentence:
        anchor_sentence = _sentences(sources[s1]["text"])[0] if _sentences(sources[s1]["text"]) else ""
        if anchor_sentence and quote_is_verbatim(anchor_sentence, sources[s1]["text"]):
            sources[s1]["quote"] = anchor_sentence
            sources[s1]["citation"] = source_registry.citation(s1, anchor_sentence)

    teaching = []
    for chunk_id in teaching_ids:
        label = s1 if chunk_id == anchor_chunk and s1 else add_chunk(chunk_id, "S")
        teaching.append({"label": label, "text": sources[label]["text"]})
    extra_definitions = []
    for chunk_id in defining_ids[:2]:
        label = add_chunk(chunk_id, "S")
        extra_definitions.append({"label": label, "text": sources[label]["text"]})

    prereq_context = []
    prerequisites = graph.why_here(node_id, source_registry=source_registry, settings=settings).get("prerequisites", [])[:settings.lecture_max_prerequisites]
    for index, prereq in enumerate(prerequisites, 1):
        q_label = prereq.get("source_label")
        quote = str(prereq.get("quote") or "")
        citation_source = prereq.get("citation_source")
        q_chunk = None
        if q_label:
            record = source_registry.resolve(q_label)
            q_chunk = record.get("chunk_id") if record else None
        if not q_chunk and prereq.get("node_id") in graph.nodes:
            parent = graph.nodes[prereq["node_id"]]
            parent_anchor = parent.get("anchor") or {}
            q_chunk = parent_anchor.get("chunk_id") or next(iter(parent.get("teaching_chunk_ids", [])), None)
        why_label = None
        if q_chunk in graph.chunks:
            why_label = add_chunk(q_chunk, "S" if citation_source == "legacy_excerpt" else "Q", quote or None)
        parent_node = graph.nodes.get(prereq.get("node_id"), {})
        parent_anchor = parent_node.get("anchor") or {}
        parent_teaching = parent_node.get("teaching_chunk_ids") or []
        note_label = None
        note_quote = str(parent_anchor.get("sentence") or "")
        note_chunk = parent_anchor.get("chunk_id") or (parent_teaching[0] if parent_teaching else None)
        if note_chunk in graph.chunks:
            note_label = add_chunk(note_chunk, "N", note_quote or None)
        if prereq.get("order_relation"):
            order = "sach_trinh_bay_sau"
        elif prereq.get("module_id") == module_id and prereq.get("node_id") in node_ids and position_index >= 0:
            order = "cung_module_truoc" if node_ids.index(prereq["node_id"]) < position_index else "khong_ro"
        else:
            order = "module_truoc"
        parent_module_id = parent_node.get("module_id")
        parent_module = graph.modules.get(parent_module_id, {})
        parent_aliases = [str(alias.get("name") if isinstance(alias, Mapping) else alias)
                          for alias in parent_node.get("aliases", [])]
        resolved_why = source_registry.resolve(why_label) if why_label else None
        family = resolved_why.get("family") if resolved_why else None
        prereq_context.append({"node_id": prereq.get("node_id"), "name": prereq.get("name"),
                               "aliases": parent_aliases,
                               "N": note_label, "Q": why_label, "quote": quote,
                               "order_note": order, "citation_source": citation_source,
                               "warning": prereq.get("warning"), "note": prereq.get("note"),
                               "family": family, "module_id": parent_module_id,
                               "module_index": parent_module.get("index"),
                               "module_title": parent_module.get("display_name") or parent_module.get("title")})

    open_context = []
    allowed_relations = {"contrasts_with", "subtype_of", "example_of", "component_of", "uses"}
    for edge in graph.payload.get("open_edges", []):
        if edge.get("edge_type") not in allowed_relations or edge.get("soft") or not edge.get("quote"):
            continue
        if node_id not in {edge.get("source"), edge.get("target")}:
            continue
        chunk_id = edge.get("quote_chunk_id") or edge.get("chunk_id") or next(iter(edge.get("chunk_ids", [])), None)
        if chunk_id not in graph.chunks:
            continue
        label = add_chunk(chunk_id, "R", str(edge["quote"]))
        other = edge.get("target") if edge.get("source") == node_id else edge.get("source")
        open_context.append({"label": label, "relation": edge.get("edge_type"),
                             "name": graph.nodes.get(other, {}).get("display_name") or graph.nodes.get(other, {}).get("name"),
                             "quote": edge.get("quote")})
        if len(open_context) == settings.lecture_max_contrasts + 1:
            break

    media = graph.get_media(node_id)
    module_index = int(module.get("index", 0) or 0)
    later_nodes = []
    for edge in graph.traverse(node_id, "requires", "out").get("edges", []):
        later_id = edge.get("node_id")
        later = graph.nodes.get(later_id, {})
        if later:
            later_module = graph.modules.get(later.get("module_id"), {})
            later_index = int(later_module.get("index", 0) or 0)
            later_nodes.append((later_index, later_id, later))
    later_nodes.sort(key=lambda row: (0 if row[0] >= module_index else 1,
                                     abs(row[0] - module_index), row[1]))
    # `next_up` is a code-built preview; it is never prompt material.
    next_up = _next_up(graph, node_id, module_id, source_registry, settings)

    exercise = []
    for chunk in graph.chunks.values():
        if _get(chunk, "role", "") == "bai_tap" and any(name.casefold() in str(_get(chunk, "text", "")).casefold()
               for name in (node.get("display_name") or node.get("name"),) if name):
            label = add_chunk(_id(chunk), "B")
            exercise.append({"label": label, "text": sources[label]["text"]})
            break

    formula_refs = _formula_refs(graph, teaching_ids)
    missing_formula = any(row.get("bbox") is None or not row.get("image_ref") for row in formula_refs)

    context = {
        "concept": {"node_id": node_id, "name": node.get("display_name") or node.get("name"),
                    "aliases": node.get("aliases", []), "module_id": module_id,
                    "module_index": module.get("index"), "module_title": module.get("display_name") or module.get("title"),
                    "position": position_index + 1 if position_index >= 0 else None, "count": len(node_ids)},
        "definition": {"quote": anchor_sentence, "source": s1},
        "teaching": teaching,
        "extra_definitions": extra_definitions,
        "prerequisites": prereq_context,
        "open_edges": open_context[:settings.lecture_max_contrasts],
        "media": media,
        "exercise": exercise,
        "formula_refs_for_generation": [
            {"label": row["label"], "raw_text": row["raw_text"],
             "instruction": "chữ thô, có thể sai cấu trúc; không chép thành công thức"}
            for row in formula_refs if row.get("raw_text")
        ],
        "bridge_candidates": [
            {"prereq": row["node_id"], "name": row["name"], "aliases": row["aliases"],
             "source": row["Q"], "quote": row["quote"]}
            for row in prereq_context if row.get("family") == "Q" and row.get("Q")
        ],
        "task": "Viết đúng cấu trúc JSON; mỗi nhận định trong sách phải có nguồn và quote nguyên văn.",
        "sources": sources,
        "registry": source_registry,
    }
    context = _trim_context(context, settings)

    position = {
        "module_id": module_id,
        "module_index": module.get("index"),
        "index_in_module": position_index + 1 if position_index >= 0 else None,
        "count_in_module": len(node_ids),
        "previous_node_id": node_ids[position_index - 1] if position_index > 0 else None,
        "next_node_id": node_ids[position_index + 1] if 0 <= position_index < len(node_ids) - 1 else None,
    }
    definition = {"quote": anchor_sentence, "citation": source_registry.citation(s1, anchor_sentence),
                 "chunk_id": anchor_chunk,
                 "page": sources.get(s1, {}).get("page"),
                 "formula_refs": [{key: value for key, value in row.items() if key != "raw_text"}
                                  for row in formula_refs]}
    visible_prereqs = []
    for row in prereq_context:
        n_source = sources.get(row.get("N"), {})
        parent_node = graph.nodes.get(row["node_id"], {})
        parent_anchor = parent_node.get("anchor") or {}
        definition_quote = str(parent_anchor.get("sentence") or n_source.get("quote") or "")
        if not definition_quote and n_source.get("text"):
            definition_quote = next(iter(_sentences(n_source["text"])), "")
        definition_citation = source_registry.citation(row["N"], definition_quote) if row.get("N") and definition_quote else None
        visible_prereqs.append({
            "recall": {"node_id": row["node_id"], "name": row["name"],
                       "module_index": row["module_index"], "module_title": row["module_title"],
                       "order_note": row["order_note"],
                       "definition": {"quote": definition_quote, "citation": definition_citation}},
            "bridge": None,
        })
    skeleton = {
        "contract_version": settings.contract_version, "doc_id": graph.doc_id, "graph_version": graph.graph_version,
        "node_id": node_id, "position": position, "definition": definition,
        "prerequisites": visible_prereqs, "next_up": next_up, "media": media,
        "sections": [], "self_check": None, "failure": None,
        "status": "generating", "warnings": ["thieu_cong_thuc"] if missing_formula else [], "usage": {},
    }
    return context, skeleton, label_to_chunk


def _formula_refs(graph: Any, chunk_ids: list[str]) -> list[dict[str, Any]]:
    refs = []
    seen = set()
    formula_nodes = {}
    tree = getattr(graph, "tree", None)
    for node in getattr(tree, "nodes", []) or []:
        if _get(node, "node_type") == "formula" and _get(node, "formula_id"):
            occurrence_id = f"{_get(node, 'formula_id')}@p{_get(node, 'page')}:r{_get(node, 'reading_order')}"
            formula_nodes.setdefault(_get(node, "formula_id"), []).append((node, occurrence_id))
    image_refs = getattr(graph, "formula_images", {}) or {}
    for chunk_id in chunk_ids:
        chunk = graph.chunks.get(chunk_id)
        for formula in _get(chunk, "formula_refs", []) or []:
            formula_id = _get(formula, "formula_id")
            if not formula_id:
                continue
            candidates = formula_nodes.get(formula_id, [])
            candidate = next(((candidate, occurrence) for candidate, occurrence in candidates
                              if _get(candidate, "page") == _get(chunk, "page") and occurrence not in seen), None)
            if candidate is None:
                candidate = next(((candidate, occurrence) for candidate, occurrence in candidates
                                  if occurrence not in seen), (None, None))
            node, occurrence_id = candidate
            page = _get(node, "page", _get(chunk, "page")) if node else _get(chunk, "page")
            occurrence_id = (_get(formula, "occurrence_id") or occurrence_id
                             or f"{formula_id}@p{page}:r{_get(formula, 'reading_order', 0)}")
            if occurrence_id in seen:
                continue
            seen.add(occurrence_id)
            image = image_refs.get(occurrence_id, {}) if isinstance(image_refs, Mapping) else {}
            bbox = _get(node, "bbox") if node else None
            if isinstance(image, Mapping):
                bbox = image.get("bbox", bbox)
                image_ref = image.get("image_ref")
                media_id = image.get("media_id")
                status = image.get("status")
                raw_text = image.get("raw_text", _get(node, "raw_text") if node else None)
                page = image.get("page", _get(node, "page", _get(chunk, "page")))
            else:
                image_ref = image
                media_id = _get(formula, "media_id")
                status = _get(formula, "status")
                raw_text = _get(node, "raw_text") if node else None
                page = _get(node, "page", _get(chunk, "page"))
            refs.append({"label": f"CT{len(refs) + 1}", "formula_id": formula_id,
                         "occurrence_id": occurrence_id, "media_id": media_id, "status": status,
                         "image_ref": image_ref, "page": page,
                         "bbox": list(bbox) if bbox is not None else None,
                         "raw_text": raw_text})
    return refs


def _citation(registry: Any, label: Any, quote: Any) -> dict[str, Any] | None:
    if not isinstance(label, str):
        return None
    if quote is None or quote == "":
        return registry.citation(label)
    return registry.citation(label, str(quote))


def _symbols_valid(text: str, source_texts: list[str]) -> bool:
    source = "".join(source_texts)
    protected = re.findall(r"\d+|\b[A-Za-z]\b|[=+×÷*/^<>≤≥±−-]", text)
    source_tokens = set(re.findall(r"\d+|\b[A-Za-z]\b|[=+×÷*/^<>≤≥±−-]", source))
    return all(token in source_tokens for token in protected)


def _source_coverage(text: str, source_texts: list[str]) -> float:
    words = [word.casefold() for word in re.findall(r"\w+", text) if len(word) > 2]
    if not words:
        return 1.0
    source_words = {word.casefold() for source in source_texts for word in re.findall(r"\w+", source)}
    return sum(word in source_words for word in words) / len(words)


def _has_repeated_ngram(text: str) -> bool:
    words = re.findall(r"\w+", text.casefold())
    counts = Counter(tuple(words[index:index + 8]) for index in range(max(0, len(words) - 7)))
    return any(count >= 3 for count in counts.values())


def _lecture_output_text(output: Any) -> str:
    if not isinstance(output, dict):
        return ""
    texts = []
    for field in ("bridges", "explanation", "example", "contrasts"):
        for item in output.get(field, []) if isinstance(output.get(field, []), list) else []:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                texts.append(item["text"])
    self_check = output.get("self_check")
    if isinstance(self_check, dict):
        for field in ("question", "answer"):
            if isinstance(self_check.get(field), str):
                texts.append(self_check[field])
    return "\n".join(texts)


def _validate_bridge(item: Any, context: dict[str, Any], settings: BSettings,
                     diagnostics: dict[str, Any] | None = None) -> dict[str, Any] | None:
    def drop(rule: str) -> None:
        if diagnostics is not None:
            counts = diagnostics.setdefault("dropped_by_rule", {})
            counts[rule] = counts.get(rule, 0) + 1
            rules = diagnostics.setdefault("validation_rules", [])
            if rule not in rules:
                rules.append(rule)

    if not isinstance(item, dict):
        drop("K11")
        return None
    prereq_id = str(item.get("prereq") or "")
    candidates = {str(row.get("prereq")): row for row in context.get("bridge_candidates", [])}
    candidate = candidates.get(prereq_id)
    text, quote = item.get("text"), item.get("quote")
    expected_source = candidate.get("source") if candidate else None
    sources = item.get("sources")
    valid_k11 = bool(candidate and isinstance(text, str) and text.strip() and
                     isinstance(quote, str) and quote and sources == [expected_source] and
                     quote_is_verbatim(quote, candidate.get("quote", ""), max_chars=settings.quote_max_chars) and
                     any(str(name).casefold() in text.casefold() for name in
                         [candidate.get("name", ""), *candidate.get("aliases", [])] if name))
    if not valid_k11:
        drop("K11")
        return None
    if len(text) > settings.bridge_max_chars or any(
            str(phrase).casefold() in text.casefold() for phrase in settings.bridge_forbidden_phrases):
        drop("K12")
        return None
    citation = context.get("registry").citation(expected_source, quote)
    if citation is None:
        drop("K11")
        return None
    return {"prereq": prereq_id, "text": text.strip(), "citations": [citation], "check": "pass"}


def _three_grams(text: str) -> set[str]:
    words = unicodedata.normalize("NFC", text).casefold().split()
    return {" ".join(words[index:index + 3]) for index in range(max(0, len(words) - 2))}


def _is_duplicate_idea(text: str, previous: list[str], definition: str, threshold: float) -> bool:
    grams = _three_grams(text)
    if not grams:
        return False
    for earlier in [definition, *previous]:
        other = _three_grams(earlier)
        if other and len(grams & other) / len(grams | other) >= threshold:
            return True
    return False


def _valid_item(item: Any, context: dict[str, Any], *, section: str, settings: BSettings,
                outside_seen: int = 0, dropped_by_rule: dict[str, int] | None = None,
                dropped_by_source_label: dict[str, int] | None = None) -> dict[str, Any] | None:
    def drop(rule: str, labels: list[str] | None = None) -> None:
        if dropped_by_rule is not None:
            dropped_by_rule[rule] = dropped_by_rule.get(rule, 0) + 1
        if dropped_by_source_label is not None:
            for label in labels or []:
                dropped_by_source_label[label] = dropped_by_source_label.get(label, 0) + 1

    if not isinstance(item, dict) or not isinstance(item.get("text"), str) or not item["text"].strip():
        drop("K1")
        return None
    sources = item.get("sources", [])
    outside = bool(item.get("outside_document", False))
    if outside:
        if not settings.allow_outside_examples or section not in {"example", "contrasts"} or outside_seen >= 1:
            drop("K7")
            return None
        if sources or item.get("quote"):
            drop("K7")
            return None
        return {"text": item["text"].strip(), "citations": [], "formula_labels": [],
                "outside_document": True, "check": "pass"}
    if not isinstance(sources, list) or not sources:
        drop("K2")
        return None
    source_map = {**context["sources"]}
    valid_labels = set(source_map)
    if any(label not in valid_labels for label in sources):
        drop("K2", [str(label) for label in sources if label not in valid_labels])
        return None
    if section == "prereq_notes":
        prereq = item.get("prereq")
        if not isinstance(prereq, str) or not prereq.startswith("N") or prereq not in sources:
            drop("K2", [str(prereq)] if prereq else [])
            return None
    if section == "contrasts":
        relation = item.get("relation")
        if not isinstance(relation, str) or not relation.startswith("R") or relation not in sources:
            drop("K2", [str(relation)] if relation else [])
            return None
    quote = item.get("quote")
    first = str(sources[0])
    text = source_map[first]["text"]
    if not quote_is_verbatim(str(quote or ""), text, max_chars=settings.quote_max_chars):
        drop("K3", [first])
        return None
    cited_texts = [source_map[label]["text"] for label in sources]
    if not _symbols_valid(item["text"], cited_texts):
        drop("K5", [str(label) for label in sources])
        return None
    citations = [citation for label in sources if (citation := _citation(context["registry"], label, quote if label == first else None))]
    if not citations:
        drop("K2", [str(label) for label in sources])
        return None
    check = "pass" if _source_coverage(item["text"], cited_texts) >= settings.lecture_min_source_coverage else "can_soat"
    return {"text": item["text"].strip(), "citations": citations,
            "formula_labels": re.findall(r"\[CT\d+\]", item["text"]),
            "outside_document": False, "check": check}


def _validate_top_level(output: Any, settings: BSettings) -> None:
    if not isinstance(output, dict):
        raise ValueError("K1: output must be a JSON object")
    if not isinstance(output.get("bridges"), list):
        output["bridges"] = []
    limits = {"explanation": settings.lecture_max_explanations,
              "example": settings.lecture_max_examples,
              "contrasts": settings.lecture_max_contrasts}
    for field, maximum in limits.items():
        if not isinstance(output.get(field), list) or len(output[field]) > maximum:
            raise ValueError(f"K1: invalid {field} array")
    if not isinstance(output.get("gaps", []), list):
        raise ValueError("K1: gaps must be an array")
    if output.get("self_check") is not None and not isinstance(output.get("self_check"), dict):
        raise ValueError("K1: self_check must be an object or null")


def _find_closed_array_items(buffer: str, arrays: tuple[str, ...]) -> list[tuple[str, int, dict[str, Any]]]:
    """Extract complete objects from top-level JSON arrays in a partial stream."""
    found: list[tuple[str, int, dict[str, Any]]] = []
    for name in arrays:
        key = json.dumps(name)
        start = buffer.find(key)
        if start < 0:
            continue
        array_start = buffer.find("[", start + len(key))
        if array_start < 0:
            continue
        index = 0
        cursor = array_start + 1
        while cursor < len(buffer):
            while cursor < len(buffer) and (buffer[cursor].isspace() or buffer[cursor] == ","):
                cursor += 1
            if cursor >= len(buffer) or buffer[cursor] != "{":
                break
            item_start = cursor
            depth, in_string, escaped = 0, False, False
            while cursor < len(buffer):
                char = buffer[cursor]
                if in_string:
                    if escaped:
                        escaped = False
                    elif char == "\\":
                        escaped = True
                    elif char == '"':
                        in_string = False
                else:
                    if char == '"':
                        in_string = True
                    elif char == "{":
                        depth += 1
                    elif char == "}":
                        depth -= 1
                        if depth == 0:
                            try:
                                item = json.loads(buffer[item_start:cursor + 1])
                            except json.JSONDecodeError:
                                break
                            found.append((name, index, item))
                            cursor += 1
                            index += 1
                            break
                cursor += 1
            else:
                break
            if cursor < item_start:
                break
    return found


def _fallback_sections(context: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    sentences = []
    allowed = {row.get("label") for row in context.get("teaching", [])}
    allowed.update(row.get("label") for row in context.get("extra_definitions", []))
    if context.get("definition", {}).get("source"):
        allowed.add(context["definition"]["source"])
    for label, source in context["sources"].items():
        if label not in allowed:
            continue
        sentences.extend((sentence, source) for sentence in _sentences(source["text"]))
    if not sentences:
        return []
    # Small deterministic TextRank: sentence overlap edges, PageRank, then source order.
    tokens = [set(re.findall(r"\w+", sentence.casefold())) for sentence, _ in sentences]
    scores = [1.0] * len(sentences)
    for _ in range(12):
        next_scores = [0.15] * len(sentences)
        for i in range(len(sentences)):
            for j in range(len(sentences)):
                if i == j:
                    continue
                similarity = len(tokens[i] & tokens[j]) / max(1, len(tokens[i] | tokens[j]))
                if similarity:
                    next_scores[i] += 0.85 * similarity * scores[j] / max(1, sum(
                        len(tokens[j] & tokens[k]) / max(1, len(tokens[j] | tokens[k]))
                        for k in range(len(sentences)) if k != j
                    ))
        scores = next_scores
    ranked = sorted(range(len(sentences)), key=lambda i: (-scores[i], i))[:4]
    selected = sorted(ranked)
    for index in selected:
        sentence, source = sentences[index]
        citation = context["registry"].citation(source["label"], sentence)
        if citation:
            rows.append({"text": sentence, "citations": [citation], "formula_labels": [],
                         "outside_document": False, "check": "pass"})
    return [{"kind": "giai_thich", "items": rows}]


def _merge_emitted(sections: list[dict[str, Any]], emitted: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    kinds = {"bridges": "cau_noi", "explanation": "giai_thich",
             "example": "vi_du", "contrasts": "phan_biet"}
    for field, items in emitted.items():
        section = next((row for row in sections if row["kind"] == kinds[field]), None)
        if section is None and items:
            section = {"kind": kinds[field], "items": []}
            sections.append(section)
        if section is not None:
            ordered = []
            seen: set[str] = set()
            seen_prerequisites: set[str] = set()
            for item in [*items, *section["items"]]:
                if field == "bridges":
                    prereq_id = str(item.get("prereq"))
                    if prereq_id in seen_prerequisites:
                        continue
                    seen_prerequisites.add(prereq_id)
                key = stable_json(item)
                if key not in seen:
                    seen.add(key)
                    ordered.append(item)
            section["items"] = ordered
    return sections


def _aggregate_usage(rows: list[dict[str, Any]]) -> dict[str, int | float]:
    return {
        "promptTokenCount": sum(int(row.get("promptTokenCount", row.get("input_tokens", 0)) or 0) for row in rows),
        "candidatesTokenCount": sum(int(row.get("candidatesTokenCount", row.get("output_tokens", 0)) or 0) for row in rows),
        "thoughtsTokenCount": sum(int(row.get("thoughtsTokenCount", row.get("thought_tokens", 0)) or 0) for row in rows),
        "cost_usd": sum(float(row.get("cost_usd", 0) or 0) for row in rows),
    }


def summarize_lecture_diagnostics(rows: list[dict[str, Any]], *, doc_id: str | None = None) -> dict[str, Any]:
    """Summarize validation companion rows without counting them as billed usage."""
    selected = [row for row in rows if row.get("purpose") == "lecture_validation"
                and (doc_id is None or row.get("doc_id") == doc_id)]
    failed = [row for row in selected if not row.get("passed", False)]

    def totals(field: str) -> dict[str, int]:
        result: dict[str, int] = {}
        for row in selected:
            for key, value in (row.get(field) or {}).items():
                result[str(key)] = result.get(str(key), 0) + int(value or 0)
        return dict(sorted(result.items()))

    failed_by_rule: dict[str, int] = {}
    for row in failed:
        for rule in set(row.get("validation_rules") or ()):
            failed_by_rule[rule] = failed_by_rule.get(rule, 0) + 1
    return {
        "doc_id": doc_id,
        "generation_count": len(selected),
        "passed_generations": len(selected) - len(failed),
        "failed_generations": len(failed),
        "failed_by_rule": dict(sorted(failed_by_rule.items())),
        "dropped_by_rule": totals("dropped_by_rule"),
        "dropped_by_source_label": totals("dropped_by_source_label"),
        "generations": [{key: row.get(key) for key in (
            "doc_id", "generation_id", "generation_index", "validator_version", "validation_rules",
            "dropped_by_rule", "dropped_by_source_label", "passed", "failure_reason")}
            for row in selected],
    }


def _rule_for_error(error: BaseException) -> str:
    match = re.match(r"\s*(K[1-8])\s*:", str(error))
    return match.group(1) if match else "K1"


class LectureUseCase:
    def __init__(self, model: Any, store: Any, *, settings: BSettings | None = None,
                 clock: Any | None = None, progress: Any | None = None,
                 spend_guard: Any | None = None) -> None:
        self.model = model
        self.store = store
        self.settings = settings or BSettings()
        self.clock = clock or SystemClock()
        self.progress = progress
        self.spend_guard = spend_guard or DailySpendGuard(store, settings=self.settings, clock=self.clock)

    def get(self, doc_id: str, graph_version: str, graph: Any, node_id: str, **kwargs: Any) -> dict[str, Any]:
        return self.make(doc_id, graph_version, graph, node_id, **kwargs)

    def make(
        self, doc_id: str, graph_version: str, graph: Any, node_id: str, *,
        dry_run: bool = False, allow_spend: bool = False,
        on_event: Callable[[dict[str, Any]], None] | None = None,
        preload_next: bool = False,
        _background: bool = False,
        owner: str | None = None,
    ) -> dict[str, Any]:
        call_started = perf_counter()
        context, skeleton, _ = _assemble(graph, node_id, self.settings)
        # Registry labels are created as contexts are assembled; hand a compact source map to the prompt.
        context_for_prompt = {key: value for key, value in context.items() if key != "registry"}
        context_for_prompt.pop("prerequisites", None)
        prompt = stable_json(context_for_prompt) + "\n" + stable_json({
            "limits": {
                "prerequisite_notes": self.settings.lecture_max_prerequisites,
                "explanation_items": [self.settings.lecture_min_explanations, self.settings.lecture_max_explanations],
                "examples": self.settings.lecture_max_examples,
                "contrasts": self.settings.lecture_max_contrasts,
                "quote_chars_max": self.settings.quote_max_chars,
                "bridge_max_chars": self.settings.bridge_max_chars,
                "bridge_forbidden_phrases": list(self.settings.bridge_forbidden_phrases),
                "outside_examples": 1 if self.settings.allow_outside_examples else 0,
            }
        })
        generation_mode = ("unavailable" if self.model is None
                           else str(getattr(self.model, "model_id", self.settings.model_id)))
        cache_context = {**context_for_prompt, "generation_mode": generation_mode}
        key, ctx_hash = lecture_cache_key(doc_id=doc_id, node_id=node_id, context=cache_context,
                                         prompt=_SYSTEM + prompt, schema=LECTURE_SCHEMA, settings=self.settings)
        skeleton.update({"graph_version": graph_version, "lecture_key": key})
        skeleton = self._attach_progress(skeleton, owner, doc_id, graph)
        skeleton_ms = round((perf_counter() - call_started) * 1000)
        if on_event:
            on_event({"event": "skeleton", "lecture": skeleton})
        if not context["teaching"] and not context["extra_definitions"]:
            result = {**skeleton, "status": "no_source",
                      "warnings": list(dict.fromkeys([*skeleton.get("warnings", []), "khong_co_doan_day"])),
                      "mention_sources": _mention_sources(graph, node_id)}
            if on_event:
                on_event({"event": "final", "lecture": result})
            return result
        if dry_run:
            result = {**skeleton, "status": "generating", "dry_run": True,
                      "dry_run_limits": {"bridge_max_chars": self.settings.bridge_max_chars,
                                         "bridge_forbidden_phrases": list(self.settings.bridge_forbidden_phrases),
                                         "max_output_tokens": self.settings.lecture_max_output_tokens},
                      "estimate_input_tokens": len(_SYSTEM + prompt) // 3,
                      "estimate_usd": estimate_cost(self.settings.model_id, len(_SYSTEM + prompt) // 3,
                                                     self.settings.lecture_max_output_tokens)}
            if on_event:
                on_event({"event": "final", "lecture": result})
            return result
        cached = self.store.get_cache(key)
        if isinstance(cached, dict) and cached.get("status") == "ready":
            result = self._attach_progress({**cached, "graph_version": graph_version}, owner, doc_id, graph)
            if on_event:
                on_event({"event": "final", "lecture": result})
            return result

        failure = self.store.get_record("lecture_failure", key)
        if failure:
            expires = datetime.fromisoformat(str(failure.get("expires_at", "")))
            if expires.tzinfo is not None and expires > self.clock.now():
                result = self._attach_progress({**failure["result"], "graph_version": graph_version}, owner, doc_id, graph)
                if on_event:
                    on_event({"event": "failure", "lecture": result})
                return result
            self.store.delete_record("lecture_failure", key)

        event_stopped = __import__("threading").Event()
        click_deadline = call_started + self.settings.lecture_click_timeout_seconds
        generation_ids: list[str] = []
        live_items: list[dict[str, Any]] = []
        def stream_callback(event: dict[str, Any]) -> None:
            if event.get("event") == "item" and not event_stopped.is_set():
                live_items.append(event)
            if on_event and not event_stopped.is_set():
                on_event(event)

        def generate() -> dict[str, Any]:
            emitted: dict[str, list[dict[str, Any]]] = {"bridges": [], "explanation": [], "example": [], "contrasts": []}
            outside_count = 0
            generation_index = 0

            def active_request_timeout() -> float:
                remaining = click_deadline - perf_counter()
                if event_stopped.is_set() or remaining <= 0:
                    raise TimeoutError("lecture click deadline reached")
                backoff = sum(2 ** attempt for attempt in range(transport_retries))
                return max(0.1, (remaining - backoff) / (transport_retries + 1))

            def click_rows() -> list[dict[str, Any]]:
                generation_set = set(generation_ids)
                return [row for row in self.store.usage_rows(doc_id)
                        if row.get("purpose") == "lecture" and row.get("context_hash") == ctx_hash
                        and row.get("generation_id") in generation_set]

            try:
                if self.model is None:
                    return self._failure(skeleton, "khong_co_mo_hinh", False, key, ctx_hash, doc_id, owner)
                if not allow_spend:
                    return self._failure(skeleton, "khong_co_mo_hinh", False, key, ctx_hash, doc_id, owner)
                diag = self._new_validation_row(doc_id, ctx_hash, generation_index)
                generation_ids.append(diag["generation_id"])
                generation_index += 1
                try:
                    timeout_seconds = active_request_timeout()
                    output, _, elapsed, finish_reason, repeated_idea_text = self._generate(
                        prompt, emitted, stream_callback, context, outside_count, doc_id, ctx_hash, diag,
                        click_started=call_started, transport_retries=transport_retries,
                        timeout_seconds=timeout_seconds)
                    _validate_top_level(output, self.settings)
                    sections, outside_count = self._validate(output, context, diag)
                    sections = _merge_emitted(sections, emitted)
                    if finish_reason in {"MAX_TOKENS", "LENGTH"} or repeated_idea_text:
                        if diag.get("gate_ms") is not None:
                            finish_reason = "TRUNCATED"
                        else:
                            raise ValueError("K6: repeated text or truncated output")
                    if len(next((s["items"] for s in sections if s["kind"] == "giai_thich"), [])) < self.settings.lecture_min_explanations:
                        raise ValueError("K8: explanation items below minimum")
                    self._finish_validation_row(diag, passed=True)
                    rows = click_rows()
                    return self._finish(skeleton, sections, "ready",
                                        ["cat_ngan"] if finish_reason == "TRUNCATED" else [], _aggregate_usage(rows),
                                        sum(int(row.get("elapsed_ms", 0) or 0) for row in rows), key, ctx_hash, doc_id)
                except Exception as first_error:
                    diag["validation_rules"].append(_rule_for_error(first_error))
                    self._finish_validation_row(diag, passed=False, error=first_error)
                    if diag.get("gate_ms") is not None:
                        rows = click_rows()
                        sections = _merge_emitted([], emitted)
                        return self._finish(skeleton, sections, "ready", ["cat_ngan"],
                                            _aggregate_usage(rows),
                                            sum(int(row.get("elapsed_ms", 0) or 0) for row in rows),
                                            key, ctx_hash, doc_id)
                    first_reason = self._reason_code(first_error)
                    if first_reason != "kiem_noi_dung":
                        return self._failure(skeleton, first_reason, first_reason in {"loi_mang", "het_thoi_gian", "tran_he_thong"}, key, ctx_hash, doc_id, owner)
                    raise first_error
            except Exception as first_error:
                # One repair attempt follows K1, K6, and K8 failures. Already emitted items remain live.
                diag = self._new_validation_row(doc_id, ctx_hash, generation_index)
                generation_ids.append(diag["generation_id"])
                try:
                    repair_prompt = prompt + "\nLần trước mắc lỗi: " + str(first_error) + ". Trả JSON đã sửa, giữ nguyên các luật."
                    timeout_seconds = active_request_timeout()
                    output, _, elapsed, finish_reason, repeated_idea_text = self._generate(
                        repair_prompt, emitted, stream_callback, context, outside_count, doc_id, ctx_hash, diag,
                        temperature=self.settings.lecture_retry_temperature, click_started=call_started,
                        transport_retries=transport_retries, timeout_seconds=timeout_seconds)
                    _validate_top_level(output, self.settings)
                    sections, outside_count = self._validate(output, context, diag)
                    sections = _merge_emitted(sections, emitted)
                    if finish_reason in {"MAX_TOKENS", "LENGTH"} or repeated_idea_text:
                        if diag.get("gate_ms") is not None:
                            finish_reason = "TRUNCATED"
                        else:
                            raise ValueError("K6: repeated text or truncated output")
                    if len(next((s["items"] for s in sections if s["kind"] == "giai_thich"), [])) < self.settings.lecture_min_explanations:
                        raise ValueError("K8: explanation items below minimum")
                    self._finish_validation_row(diag, passed=True)
                    rows = click_rows()
                    return self._finish(skeleton, sections, "ready",
                                        ["cat_ngan"] if finish_reason == "TRUNCATED" else [], _aggregate_usage(rows),
                                        sum(int(row.get("elapsed_ms", 0) or 0) for row in rows), key, ctx_hash, doc_id)
                except Exception as repair_error:
                    diag["validation_rules"].append(_rule_for_error(repair_error))
                    self._finish_validation_row(diag, passed=False, error=repair_error)
                    rows = click_rows()
                    if diag.get("gate_ms") is not None:
                        return self._finish(skeleton, _merge_emitted([], emitted), "ready", ["cat_ngan"],
                                            _aggregate_usage(rows),
                                            sum(int(row.get("elapsed_ms", 0) or 0) for row in rows),
                                            key, ctx_hash, doc_id)
                    reason = self._reason_code(repair_error)
                    return self._failure(skeleton, reason, reason in {"loi_mang", "het_thoi_gian", "tran_he_thong"},
                                         key, ctx_hash, doc_id, owner, _aggregate_usage(rows))

        completed: Queue[tuple[bool, Any]] = Queue(maxsize=1)
        transport_retries = (self.settings.lecture_preload_transport_retries if _background
                             else self.settings.lecture_click_transport_retries)
        def run_single_flight() -> None:
            try:
                completed.put((True, self.store.single_flight(
                    key, generate,
                    cache_if=lambda value: (isinstance(value, dict) and value.get("status") == "ready"
                                            and not event_stopped.is_set()),
                    negative_ttl_seconds=0,
                )))
            except BaseException as error:
                completed.put((False, error))
        Thread(target=run_single_flight, daemon=True).start()
        try:
            remaining = self.settings.lecture_click_timeout_seconds - (perf_counter() - call_started)
            if remaining <= 0:
                raise Empty
            succeeded, payload = completed.get(timeout=remaining)
        except Empty:
            event_stopped.set()
            if len(live_items) >= self.settings.lecture_min_explanations:
                sections: list[dict[str, Any]] = []
                for event in live_items:
                    section = next((item for item in sections if item["kind"] == event["section_kind"]), None)
                    if section is None:
                        section = {"kind": event["section_kind"], "items": []}
                        sections.append(section)
                    section["items"].append(event["item"])
                result = self._finish(skeleton, sections, "ready", ["cat_ngan"], {}, 0, key, ctx_hash, doc_id)
                result = self._attach_progress(result, owner, doc_id, graph)
                self.store.put_cache(key, _without_learner_status(result))
                final_ms = round((perf_counter() - call_started) * 1000)
                gate_ms = next((row.get("gate_ms") for row in self.store.usage_rows(doc_id)
                                if row.get("purpose") == "lecture" and row.get("context_hash") == ctx_hash
                                and row.get("generation_id") in set(generation_ids)
                                and row.get("gate_ms") is not None), final_ms)
                self.store.append_usage({"purpose": "lecture_timing", "model_id": getattr(self.model, "model_id", self.settings.model_id),
                                         "doc_id": doc_id, "learner_id": None, "context_hash": ctx_hash,
                                         "input_tokens": 0, "output_tokens": 0, "thought_tokens": 0, "cost_usd": 0.0,
                                         "ttft_ms": None, "elapsed_ms": final_ms, "skeleton_ms": skeleton_ms,
                                         "gate_ms": gate_ms, "final_ms": final_ms,
                                         "gate_to_final_ms": max(0, final_ms - gate_ms),
                                         "created_at": self.clock.now().isoformat()})
            else:
                result = self._failure(skeleton, "het_thoi_gian", True, key, ctx_hash, doc_id, owner)
                expiry = self.clock.now() + timedelta(seconds=self.settings.negative_cache_seconds)
                self.store.put_record("lecture_failure", key, {"doc_id": doc_id, "expires_at": expiry.isoformat(),
                                                                "result": _without_learner_status(result)})
            if on_event:
                on_event({"event": "final" if result.get("status") == "ready" else "failure", "lecture": result})
            return result
        if succeeded:
            result = payload
        else:
            reason = self._reason_code(payload)
            result = self._failure(skeleton, reason,
                                   reason in {"loi_mang", "het_thoi_gian", "tran_he_thong"},
                                   key, ctx_hash, doc_id, owner)
        # Negative-cache entries are context-identical but may have been generated
        # for an older pinned graph version; bind their public metadata per request.
        result = self._attach_progress({**result, "graph_version": graph_version}, owner, doc_id, graph)
        if result.get("status") == "ready":
            generation_rows = [row for row in self.store.usage_rows(doc_id)
                               if row.get("purpose") == "lecture" and row.get("context_hash") == ctx_hash
                               and row.get("generation_id") in set(generation_ids)]
            gate_ms = next((row.get("gate_ms") for row in generation_rows if row.get("gate_ms") is not None), None)
            final_ms = round((perf_counter() - call_started) * 1000)
            gate_ms = gate_ms if gate_ms is not None else final_ms
            timing = {"skeleton_ms": skeleton_ms, "gate_ms": gate_ms,
                      "final_ms": final_ms,
                      "gate_to_final_ms": max(0, final_ms - gate_ms)}
            result["diagnostics"] = {**result.get("diagnostics", {}), **timing}
            self.store.append_usage({"purpose": "lecture_timing", "model_id": getattr(self.model, "model_id", self.settings.model_id),
                                     "doc_id": doc_id, "learner_id": None, "context_hash": ctx_hash,
                                     "input_tokens": 0, "output_tokens": 0, "thought_tokens": 0, "cost_usd": 0.0,
                                     "ttft_ms": None, "elapsed_ms": final_ms, **timing,
                                     "created_at": self.clock.now().isoformat()})
        if result.get("status") == "failed":
            ttl = self.settings.lecture_failure_ttl_seconds if result.get("failure", {}).get("reason_code") == "kiem_noi_dung" else self.settings.negative_cache_seconds
            if result.get("failure", {}).get("reason_code") == "tran_he_thong":
                local_today = self.clock.today(self.settings.spend_day_timezone)
                tomorrow = local_today + timedelta(days=1)
                zone = ZoneInfo(self.settings.spend_day_timezone)
                expiry = datetime.combine(tomorrow, datetime.min.time(), tzinfo=zone).astimezone(self.clock.now().tzinfo)
            else:
                expiry = self.clock.now() + timedelta(seconds=ttl)
            self.store.put_record("lecture_failure", key, {"doc_id": doc_id, "expires_at": expiry.isoformat(),
                                                            "result": _without_learner_status(result)})
        if on_event:
            on_event({"event": "final" if result.get("status") == "ready" else "failure", "lecture": result})
        if preload_next:
            next_id = skeleton["position"].get("next_node_id")
            if next_id:
                Thread(target=self.make, args=(doc_id, graph_version, graph, next_id),
                       kwargs={"allow_spend": allow_spend, "preload_next": False,
                               "_background": True}, daemon=True).start()
        return result

    def _reason_code(self, error: BaseException) -> str:
        if isinstance(error, DailyLimitExceeded):
            return "tran_he_thong"
        if isinstance(error, TimeoutError):
            return "het_thoi_gian"
        if isinstance(error, (OSError, ConnectionError)) or "network" in str(error).casefold() or "request failed" in str(error).casefold():
            return "loi_mang"
        if isinstance(error, (ValueError, json.JSONDecodeError)):
            return "kiem_noi_dung"
        return "loi_mang"

    def _failure(self, skeleton: dict[str, Any], reason: str, retryable: bool, key: str,
                 ctx_hash: str, doc_id: str, owner: str | None,
                 usage: dict[str, Any] | None = None) -> dict[str, Any]:
        page = skeleton.get("definition", {}).get("page") or skeleton.get("position", {}).get("page")
        chunk_id = skeleton.get("definition", {}).get("chunk_id")
        failure = {"reason_code": reason, "retryable": bool(retryable), "read_page": page,
                   "ask_assistant": True, "message": "Bài giảng chưa sẵn sàng; bạn có thể đọc trang sách hoặc hỏi trợ lý."}
        failure["read_page"] = {"page": page, "chunk_id": chunk_id}
        result = {**skeleton, "status": "failed", "sections": [], "failure": failure,
                  "usage": {"model_id": getattr(self.model, "model_id", self.settings.model_id),
                            "cost_usd": float((usage or {}).get("cost_usd", 0) or 0), **(usage or {})},
                  "lecture_key": key}
        return self._attach_progress(result, owner, doc_id, None)

    def _attach_progress(self, lecture: dict[str, Any], owner: str | None, doc_id: str, graph: Any) -> dict[str, Any]:
        result = json.loads(stable_json(lecture))
        if result.get("status") in {"generating", "ready", "failed", "no_source"}:
            progress = self.progress.get_progress(owner, doc_id) if self.progress is not None and owner else None
            states = (progress or {}).get("nodes", {})
            for prerequisite in result.get("prerequisites", []):
                node_id = prerequisite.get("node_id") or prerequisite.get("recall", {}).get("node_id")
                row = states.get(node_id, {})
                prerequisite["learner_status"] = ("unknown" if not owner else
                    "learned" if row.get("state") == "learned" else "not_learned")
            for item in result.get("next_up", []):
                row = states.get(item.get("node_id"), {})
                item["learner_status"] = ("unknown" if not owner else
                    "learned" if row.get("state") == "learned" else "not_learned")
        return result

    def _new_validation_row(self, doc_id: str, ctx_hash: str, index: int) -> dict[str, Any]:
        return {"generation_id": str(uuid.uuid4()), "generation_index": index,
                "doc_id": doc_id, "context_hash": ctx_hash, "validator_version": self.settings.lecture_validator_version,
                "validation_rules": [], "dropped_by_rule": {}, "dropped_by_source_label": {}}

    def _finish_validation_row(self, row: dict[str, Any], *, passed: bool,
                               error: BaseException | None = None) -> None:
        row["validation_rules"] = list(dict.fromkeys([*row["validation_rules"], *row["dropped_by_rule"]]))
        self.store.append_usage({
            "purpose": "lecture_validation", "model_id": getattr(self.model, "model_id", self.settings.model_id),
            "doc_id": row.get("doc_id"), "learner_id": None, "context_hash": row["context_hash"],
            "input_tokens": 0, "output_tokens": 0, "thought_tokens": 0, "cost_usd": 0.0,
            "ttft_ms": None, "elapsed_ms": 0, "generation_id": row["generation_id"],
            "generation_index": row["generation_index"], "validator_version": row["validator_version"],
            "validation_rules": list(dict.fromkeys(row["validation_rules"])),
            "dropped_by_rule": dict(row["dropped_by_rule"]),
            "dropped_by_source_label": dict(row["dropped_by_source_label"]),
            "passed": passed, "failure_reason": str(error) if error else None,
            "created_at": self.clock.now().isoformat(),
        })

    def _lecture_rows(self, doc_id: str, ctx_hash: str, offset: int) -> list[dict[str, Any]]:
        rows = [row for row in self.store.usage_rows(doc_id)
                if row.get("purpose") == "lecture" and row.get("context_hash") == ctx_hash]
        return rows[offset:]

    def _generate(self, prompt: str, emitted: dict[str, list[dict[str, Any]]], on_event: Any,
                  context: dict[str, Any], outside_count: int, doc_id: str, ctx_hash: str,
                  diagnostics: dict[str, Any], *, temperature: float | None = None,
                  click_started: float | None = None,
                  transport_retries: int | None = None,
                  timeout_seconds: float | None = None) -> tuple[dict[str, Any], dict[str, Any], int, str | None, bool]:
        replayed = bool(getattr(self.model, 'is_replay', False))
        estimate = estimate_cost(self.settings.model_id, len(_SYSTEM + prompt) // 3,
                                 self.settings.lecture_max_output_tokens)
        with spending_call(self.spend_guard, 'lecture', estimate,
                           replayed=replayed, clock=self.clock) as admitted_at:
            started = perf_counter()
            if hasattr(self.model, "start_session"):
                session = self.model.start_session(_SYSTEM)
                method = session.stream_json
                kwargs = {"response_schema": LECTURE_SCHEMA}
                try:
                    parameters = signature(method).parameters
                except (TypeError, ValueError):
                    parameters = {}
                if "temperature" in parameters:
                    kwargs["temperature"] = self.settings.lecture_temperature if temperature is None else temperature
                if "transport_retries" in parameters:
                    kwargs["transport_retries"] = (self.settings.lecture_click_transport_retries
                                                    if transport_retries is None else transport_retries)
                if "timeout_seconds" in parameters:
                    kwargs["timeout_seconds"] = (self.settings.lecture_click_timeout_seconds
                                                   if timeout_seconds is None else timeout_seconds)
                stream = method(prompt, **kwargs)
            else:
                session = None
                stream = self.model.stream_json(_SYSTEM, prompt, LECTURE_SCHEMA)
            buffer = ""
            emitted_indices: set[tuple[str, int]] = set()
            retained_indices: set[tuple[str, int]] = set()
            cut_tail = False
            dropped_indices: dict[str, set[int]] = {field: set() for field in emitted}
            stream_dropped_by_rule: dict[str, int] = {}
            stream_dropped_by_source_label: dict[str, int] = {}
            first_chunk_ttft_ms: int | None = None
            previous_texts = [item["text"] for items in emitted.values() for item in items]
            definition_text = str(context.get("definition", {}).get("quote", ""))
            gate_open = False
            pending_events: list[tuple[str, dict[str, Any]]] = []
            explanation_count = len(emitted.get("explanation", []))
            dropped_k6 = False
            forced_finish_reason: str | None = None
            try:
                for delta in stream:
                    if first_chunk_ttft_ms is None and delta:
                        first_chunk_ttft_ms = round((perf_counter() - started) * 1000)
                    buffer += delta
                    for field, index, item in _find_closed_array_items(buffer, ("bridges", "explanation", "example", "contrasts")):
                        marker = (field, index)
                        if marker in emitted_indices:
                            continue
                        emitted_indices.add(marker)
                        if cut_tail:
                            continue
                        maximum = {"bridges": self.settings.lecture_max_prerequisites,
                                   "explanation": self.settings.lecture_max_explanations,
                                   "example": self.settings.lecture_max_examples,
                                   "contrasts": self.settings.lecture_max_contrasts}[field]
                        if index >= maximum:
                            continue
                        if field == "bridges":
                            checked = _validate_bridge(item, context, self.settings)
                            if checked is None:
                                stream_dropped_by_rule["K11"] = stream_dropped_by_rule.get("K11", 0) + 1
                        else:
                            checked = _valid_item(item, context, section=field, settings=self.settings,
                                                  outside_seen=outside_count,
                                                  dropped_by_rule=stream_dropped_by_rule,
                                                  dropped_by_source_label=stream_dropped_by_source_label)
                        if checked is None:
                            continue
                        if field == "bridges" and any(
                                str(existing.get("prereq")) == str(checked.get("prereq"))
                                for existing in emitted["bridges"]):
                            continue
                        if (_is_duplicate_idea(checked["text"], previous_texts, definition_text,
                                               self.settings.lecture_duplicate_jaccard_threshold)
                                or _has_repeated_ngram("\n".join([*previous_texts, checked["text"]]))):
                            dropped_indices[field].add(index)
                            dropped_k6 = True
                            diagnostics["dropped_by_rule"]["K6"] = diagnostics["dropped_by_rule"].get("K6", 0) + 1
                            if "K6" not in diagnostics["validation_rules"]:
                                diagnostics["validation_rules"].append("K6")
                            if gate_open:
                                cut_tail = True
                            continue
                        if checked.get("outside_document", False):
                            outside_count += 1
                        if checked in emitted[field]:
                            continue
                        emitted[field].append(checked)
                        retained_indices.add(marker)
                        previous_texts.append(checked["text"])
                        section_kind = {"bridges": "cau_noi", "explanation": "giai_thich",
                                        "example": "vi_du", "contrasts": "phan_biet"}[field]
                        pending_events.append((section_kind, checked))
                        if field == "explanation":
                            explanation_count += 1
                        if not gate_open and explanation_count >= self.settings.lecture_min_explanations:
                            gate_open = True
                            diagnostics["gate_ms"] = round((perf_counter() - (started if click_started is None else click_started)) * 1000)
                            if on_event:
                                on_event({"event": "gate", "gate_open": True})
                                for bridge in emitted["bridges"]:
                                    if not any(kind == "cau_noi" and item == bridge
                                               for kind, item in pending_events):
                                        on_event({"event": "item", "section_kind": "cau_noi",
                                                  "item": bridge, "gate_open": True})
                                for pending_kind, pending_item in pending_events:
                                    on_event({"event": "item", "section_kind": pending_kind,
                                              "item": pending_item, "gate_open": True})
                            pending_events.clear()
                        elif gate_open and on_event:
                            on_event({"event": "item", "section_kind": section_kind,
                                      "item": checked, "gate_open": True})
                try:
                    output = json.loads(buffer)
                except json.JSONDecodeError:
                    if not gate_open:
                        raise
                    output = {"bridges": [], "explanation": [], "example": [], "contrasts": [],
                              "gaps": [], "self_check": None}
                    forced_finish_reason = "TRUNCATED"
                accepted_bridge_prerequisites: set[str] = set()
                filtered_bridges = []
                for bridge in output.get("bridges", []):
                    prereq_id = str(bridge.get("prereq")) if isinstance(bridge, dict) else None
                    if prereq_id is not None and prereq_id in accepted_bridge_prerequisites:
                        continue
                    filtered_bridges.append(bridge)
                    if prereq_id is not None and _validate_bridge(bridge, context, self.settings) is not None:
                        accepted_bridge_prerequisites.add(prereq_id)
                output["bridges"] = filtered_bridges
                repeated_idea_text = _has_repeated_ngram(_lecture_output_text(output))
                if cut_tail:
                    for field in emitted:
                        output[field] = [item for index, item in enumerate(output.get(field, []))
                                         if (field, index) in retained_indices]
                    output['self_check'] = None
                for field, indices in dropped_indices.items():
                    if indices and not cut_tail:
                        output[field] = [item for index, item in enumerate(output.get(field, [])) if index not in indices]
                if dropped_k6:
                    forced_finish_reason = "TRUNCATED"
                usage = getattr(session, "last_usage", {}) if session is not None else getattr(stream, "usage", {})
                if not usage and getattr(self.model, "last_usage", None):
                    usage = self.model.last_usage
                finish_reason = forced_finish_reason or (getattr(session, "last_finish_reason", None) if session is not None else None)
                elapsed = round((perf_counter() - started) * 1000)
                adapter_ttft = getattr(session, "last_ttft_ms", None) if session is not None else None
                ttft = (adapter_ttft if adapter_ttft is not None and adapter_ttft > 0 else
                        None if getattr(self.model, "is_replay", False) else first_chunk_ttft_ms)
                cost = token_cost(getattr(self.model, "model_id", self.settings.model_id), usage)
                if getattr(self.model, 'is_replay', False):
                    cost = 0.0
                ledger = usage_row(purpose="lecture", model_id=getattr(self.model, "model_id", self.settings.model_id),
                    doc_id=doc_id, context_hash=ctx_hash, usage=usage, elapsed_ms=elapsed,
                    ttft_ms=ttft, cost_usd=cost)
                ledger.update(generation_id=diagnostics["generation_id"], generation_index=diagnostics["generation_index"])
                ledger["created_at"] = admitted_at
                ledger["replayed"] = replayed
                ledger["gate_ms"] = diagnostics.get("gate_ms")
                ledger["first_item_ms"] = diagnostics.get("gate_ms")
                self.store.append_usage(ledger)
                return output, dict(usage), elapsed, finish_reason, repeated_idea_text
            except BaseException:
                # A complete candidate may be rejected before a later truncated portion makes the
                # enclosing JSON invalid. In that case `_validate` never sees it, so preserve the
                # local stream counts; complete JSON instead gets its single count from `_validate`.
                for rule, count in stream_dropped_by_rule.items():
                    diagnostics["dropped_by_rule"][rule] = diagnostics["dropped_by_rule"].get(rule, 0) + count
                for label, count in stream_dropped_by_source_label.items():
                    diagnostics["dropped_by_source_label"][label] = diagnostics["dropped_by_source_label"].get(label, 0) + count
                usage = getattr(session, "last_usage", {}) if session is not None else getattr(self.model, "last_usage", {})
                elapsed = round((perf_counter() - started) * 1000)
                cost = token_cost(getattr(self.model, "model_id", self.settings.model_id), usage)
                if getattr(self.model, 'is_replay', False):
                    cost = 0.0
                ledger = usage_row(purpose="lecture", model_id=getattr(self.model, "model_id", self.settings.model_id),
                    doc_id=doc_id, context_hash=ctx_hash, usage=usage, elapsed_ms=elapsed,
                    ttft_ms=(getattr(session, "last_ttft_ms", None)
                             if session is not None and getattr(session, "last_ttft_ms", None) else
                             None if getattr(self.model, "is_replay", False) else first_chunk_ttft_ms),
                    cost_usd=cost)
                ledger.update(generation_id=diagnostics["generation_id"], generation_index=diagnostics["generation_index"])
                ledger["created_at"] = admitted_at
                ledger["replayed"] = replayed
                self.store.append_usage(ledger)
                raise

    def _validate(self, output: dict[str, Any], context: dict[str, Any],
                  diagnostics: dict[str, Any] | None = None) -> tuple[list[dict[str, Any]], int]:
        outside_count = 0
        sections = []
        valid_bridges: dict[str, dict[str, Any]] = {}
        output_bridges = output.get("bridges", [])
        for candidate in context.get("bridge_candidates", []):
            prereq_id = str(candidate.get("prereq"))
            if prereq_id in valid_bridges:
                continue
            for bridge in output_bridges:
                if not isinstance(bridge, dict) or str(bridge.get("prereq")) != prereq_id:
                    continue
                checked_bridge = _validate_bridge(bridge, context, self.settings, diagnostics)
                if checked_bridge is not None:
                    valid_bridges[prereq_id] = checked_bridge
                    break
            if prereq_id not in valid_bridges and diagnostics is not None:
                counts = diagnostics["dropped_by_rule"]
                counts["K10"] = counts.get("K10", 0) + 1
                if "K10" not in diagnostics["validation_rules"]:
                    diagnostics["validation_rules"].append("K10")
        if valid_bridges:
            sections.append({"kind": "cau_noi", "items": list(valid_bridges.values())})
        for field, kind in (("explanation", "giai_thich"),
                            ("example", "vi_du"), ("contrasts", "phan_biet")):
            items = []
            limit = {"explanation": self.settings.lecture_max_explanations,
                     "example": self.settings.lecture_max_examples,
                     "contrasts": self.settings.lecture_max_contrasts}[field]
            for item in output.get(field, [])[:limit]:
                checked = _valid_item(item, context, section=field, settings=self.settings,
                                      outside_seen=outside_count,
                                      dropped_by_rule=diagnostics["dropped_by_rule"] if diagnostics else None,
                                      dropped_by_source_label=diagnostics["dropped_by_source_label"] if diagnostics else None)
                if checked:
                    outside_count += int(checked["outside_document"])
                    items.append(checked)
            if items:
                sections.append({"kind": kind, "items": items})
        self_check = output.get("self_check")
        if isinstance(self_check, dict):
            checked = _valid_item({"text": self_check.get("question"), "sources": self_check.get("sources"),
                                   "quote": self_check.get("quote")}, context, section="self_check", settings=self.settings,
                                   dropped_by_rule=diagnostics["dropped_by_rule"] if diagnostics else None,
                                   dropped_by_source_label=diagnostics["dropped_by_source_label"] if diagnostics else None)
            if checked:
                answer_ok = _valid_item({"text": self_check.get("answer"), "sources": self_check.get("sources"),
                                         "quote": self_check.get("quote")}, context, section="self_check", settings=self.settings,
                                         dropped_by_rule=diagnostics["dropped_by_rule"] if diagnostics else None,
                                         dropped_by_source_label=diagnostics["dropped_by_source_label"] if diagnostics else None)
                if answer_ok:
                    sections.append({"kind": "tu_kiem_tra", "items":[{"kind":self_check.get("kind"),
                        "question": self_check.get("question"), "answer": self_check.get("answer"),
                        "citations": answer_ok["citations"]}]})
        return sections, outside_count

    def _finish(self, skeleton: dict[str, Any], sections: list[dict[str, Any]], status: str,
                warnings: list[str], usage: dict[str, Any], elapsed: int,
                key: str, ctx_hash: str, doc_id: str) -> dict[str, Any]:
        model_id = getattr(self.model, "model_id", self.settings.model_id)
        cost = float(usage.get("cost_usd", token_cost(model_id, usage)) or 0)
        if getattr(self.model, 'is_replay', False):
            cost = 0.0
        row = usage_row(purpose="lecture", model_id=model_id,
                        doc_id=doc_id, context_hash=ctx_hash, usage=usage, elapsed_ms=elapsed,
                        cost_usd=cost)
        result = json.loads(stable_json({**skeleton, "status": status, "sections": sections,
                  "warnings": list(dict.fromkeys([*skeleton.get("warnings", []), *warnings])),
                  "self_check": next((section["items"][0] for section in sections
                                      if section.get("kind") == "tu_kiem_tra" and section.get("items")), None),
                  "usage": {"model_id": row["model_id"], "cost_usd": row["cost_usd"],
                            "elapsed_ms": elapsed, **usage}, "lecture_key": key}))
        bridges = {}
        for section in sections:
            if section.get("kind") != "cau_noi":
                continue
            for item in section.get("items", []):
                bridges.setdefault(item.get("prereq"), item)
        for prereq in result.get("prerequisites", []):
            node_id = prereq.get("node_id") or prereq.get("recall", {}).get("node_id")
            if node_id in bridges:
                prereq["bridge"] = bridges[node_id]
            prereq.pop("learner_status", None)
        for next_item in result.get("next_up", []):
            next_item.pop("learner_status", None)
        result["contract_version"] = self.settings.contract_version
        result.pop("used_later", None)
        result["diagnostics"] = {"generation_count": sum(
            row.get("purpose") == "lecture" and row.get("context_hash") == ctx_hash
            for row in self.store.usage_rows(doc_id))}
        return result


def _mention_sources(graph: Any, node_id: str) -> list[dict[str, Any]]:
    node = graph.nodes[node_id]
    registry = graph.new_source_registry() if hasattr(graph, "new_source_registry") else graph.sources
    names = [str(node.get("display_name") or node.get("name") or "").casefold()]
    rows = []
    for chunk_id, chunk in graph.chunks.items():
        text = str(_get(chunk, "text", ""))
        if any(name and name in text.casefold() for name in names):
            label = registry.label(chunk_id, "S")
            rows.append(registry.citation(label))
            if len(rows) == 5:
                break
    return [row for row in rows if row]
