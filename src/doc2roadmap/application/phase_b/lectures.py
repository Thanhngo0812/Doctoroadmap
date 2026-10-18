from __future__ import annotations

import json
import re
import unicodedata
import uuid
from collections import Counter
from collections.abc import Callable, Mapping
from threading import Thread
from time import perf_counter
from typing import Any

from doc2roadmap.application.phase_b.common import quote_is_verbatim, stable_json
from doc2roadmap.domain.phase_b_limits import BSettings, context_hash, lecture_cache_key, usage_row
from doc2roadmap.domain.phase_b_pricing import estimate_cost, token_cost


def _grounded_item_schema() -> dict[str, Any]:
    return {"type": "object", "properties": {
        "text": {"type": "string"}, "sources": {"type": "array", "items": {"type": "string"}},
        "quote": {"type": "string"}, "outside_document": {"type": "boolean"},
        "prereq": {"type": "string"}, "relation": {"type": "string"},
    }, "required": ["text", "sources", "quote", "outside_document"]}


LECTURE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "prereq_notes": {"type": "array", "items": _grounded_item_schema()},
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
    "required": ["prereq_notes", "explanation", "example", "contrasts", "gaps"],
}

_SYSTEM = """Bạn viết bài giảng ngắn bằng tiếng Việt từ các nguồn đã đánh nhãn. Chỉ khẳng định về sách khi có nhãn và quote nguyên văn. Không chép lại công thức; chỉ dùng nhãn công thức. Chỉ giảng khái niệm đích. Mọi giới hạn dưới đây là bắt buộc.
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
    for key in ("exercise", "used_later", "open_edges", "extra_definitions"):
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
    prerequisites = graph.why_here(node_id, source_registry=source_registry).get("prerequisites", [])[:settings.lecture_max_prerequisites]
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
        prereq_context.append({"node_id": prereq.get("node_id"), "name": prereq.get("name"),
                               "N": note_label, "Q": why_label, "quote": quote,
                               "order_note": order, "citation_source": citation_source,
                               "warning": prereq.get("warning"), "note": prereq.get("note")})

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
    used_later = [row[2].get("display_name") or row[2].get("name")
                  for row in later_nodes[:3] if row[2].get("display_name") or row[2].get("name")]

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
        "used_later": used_later,
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
    definition = {"quote": anchor_sentence, "chunk_id": anchor_chunk,
                 "page": sources.get(s1, {}).get("page"),
                 "formula_refs": [{key: value for key, value in row.items() if key != "raw_text"}
                                  for row in formula_refs]}
    visible_prereqs = []
    for row in prereq_context:
        q_source = sources.get(row.get("Q"), {})
        n_source = sources.get(row.get("N"), {})
        visible_prereqs.append({
            "node_id": row["node_id"], "name": row["name"], "module_index": graph.modules.get(graph.nodes.get(row["node_id"], {}).get("module_id"), {}).get("index"),
            "order_note": row["order_note"],
            "why": {"quote": row["quote"], "chunk_id": q_source.get("chunk_id"), "page": q_source.get("page"),
                    "citation": q_source.get("citation"),
                    "citation_source": row.get("citation_source"), "warning": row.get("warning"),
                    "note": row.get("note")},
            "note": {"text": n_source.get("quote") or "", "citations": [n_source["citation"]] if n_source.get("citation") else [], "check": "pass"},
        })
    skeleton = {
        "contract_version": "lecture-1", "doc_id": graph.doc_id, "graph_version": graph.graph_version,
        "node_id": node_id, "position": position, "definition": definition,
        "prerequisites": visible_prereqs, "media": media,
        "used_later": used_later,
        "sections": [], "self_check": None,
        "warnings": ["thieu_cong_thuc"] if missing_formula else [], "usage": {},
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
    limits = {"prereq_notes": settings.lecture_max_prerequisites,
              "explanation": settings.lecture_max_explanations,
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
    kinds = {"prereq_notes": "nhac_nen", "explanation": "giai_thich",
             "example": "vi_du", "contrasts": "phan_biet"}
    for field, items in emitted.items():
        section = next((row for row in sections if row["kind"] == kinds[field]), None)
        if section is None and items:
            section = {"kind": kinds[field], "items": []}
            sections.append(section)
        if section is not None:
            ordered = []
            seen: set[str] = set()
            for item in [*items, *section["items"]]:
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
    def __init__(self, model: Any, store: Any, *, settings: BSettings | None = None) -> None:
        self.model = model
        self.store = store
        self.settings = settings or BSettings()

    def get(self, doc_id: str, graph_version: str, graph: Any, node_id: str, **kwargs: Any) -> dict[str, Any]:
        return self.make(doc_id, graph_version, graph, node_id, **kwargs)

    def make(
        self, doc_id: str, graph_version: str, graph: Any, node_id: str, *,
        dry_run: bool = False, allow_spend: bool = False,
        on_event: Callable[[dict[str, Any]], None] | None = None,
        preload_next: bool = False,
    ) -> dict[str, Any]:
        started = perf_counter()
        context, skeleton, _ = _assemble(graph, node_id, self.settings)
        # Registry labels are created as contexts are assembled; hand a compact source map to the prompt.
        context_for_prompt = {key: value for key, value in context.items() if key != "registry"}
        prompt = stable_json(context_for_prompt) + "\n" + stable_json({
            "limits": {
                "prerequisite_notes": self.settings.lecture_max_prerequisites,
                "explanation_items": [self.settings.lecture_min_explanations, self.settings.lecture_max_explanations],
                "examples": self.settings.lecture_max_examples,
                "contrasts": self.settings.lecture_max_contrasts,
                "quote_chars_max": self.settings.quote_max_chars,
                "outside_examples": 1 if self.settings.allow_outside_examples else 0,
            }
        })
        generation_mode = ("extractive" if self.model is None
                           else str(getattr(self.model, "model_id", self.settings.model_id)))
        cache_context = {**context_for_prompt, "generation_mode": generation_mode}
        key, ctx_hash = lecture_cache_key(doc_id=doc_id, node_id=node_id, context=cache_context,
                                         prompt=_SYSTEM + prompt, schema=LECTURE_SCHEMA, settings=self.settings)
        skeleton.update({"graph_version": graph_version, "lecture_key": key})
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
                      "estimate_usd": estimate_cost(self.settings.model_id, len(_SYSTEM + prompt) // 3,
                                                     self.settings.lecture_max_output_tokens)}
            if on_event:
                on_event({"event": "final", "lecture": result})
            return result
        if self.store.get_cache(key) is not None:
            result = self.store.get_cache(key)
            result = {**result, "graph_version": graph_version}
            if on_event:
                on_event({"event": "final", "lecture": result})
            return result

        def generate() -> dict[str, Any]:
            emitted: dict[str, list[dict[str, Any]]] = {"prereq_notes": [], "explanation": [], "example": [], "contrasts": []}
            outside_count = 0
            starting_rows = len([row for row in self.store.usage_rows(doc_id)
                                 if row.get("purpose") == "lecture" and row.get("context_hash") == ctx_hash])
            generation_index = 0
            try:
                if self.model is None:
                    sections = _fallback_sections(context)
                    return self._finish(skeleton, sections, "fallback", ["model_unavailable"], {}, 0, key, ctx_hash, doc_id)
                if not allow_spend:
                    raise PermissionError("paid model call requires allow_spend=True")
                diag = self._new_validation_row(doc_id, ctx_hash, generation_index)
                generation_index += 1
                try:
                    output, _, elapsed, finish_reason = self._generate(
                        prompt, emitted, on_event, context, outside_count, doc_id, ctx_hash, diag)
                    _validate_top_level(output, self.settings)
                    sections, outside_count = self._validate(output, context, diag)
                    sections = _merge_emitted(sections, emitted)
                    if finish_reason in {"MAX_TOKENS", "LENGTH"} or _has_repeated_ngram(stable_json(output)):
                        raise ValueError("K6: repeated text or truncated output")
                    if len(next((s["items"] for s in sections if s["kind"] == "giai_thich"), [])) < self.settings.lecture_min_explanations:
                        raise ValueError("K8: explanation items below minimum")
                    self._finish_validation_row(diag, passed=True)
                    rows = self._lecture_rows(doc_id, ctx_hash, starting_rows)
                    return self._finish(skeleton, sections, "ready", [], _aggregate_usage(rows),
                                        sum(int(row.get("elapsed_ms", 0) or 0) for row in rows), key, ctx_hash, doc_id)
                except Exception as first_error:
                    diag["validation_rules"].append(_rule_for_error(first_error))
                    self._finish_validation_row(diag, passed=False, error=first_error)
                    raise
            except Exception as first_error:
                if not allow_spend:
                    raise
                # One repair attempt follows K1, K6, and K8 failures. Already emitted items remain live.
                diag = self._new_validation_row(doc_id, ctx_hash, generation_index)
                try:
                    repair_prompt = prompt + "\nLần trước mắc lỗi: " + str(first_error) + ". Trả JSON đã sửa, giữ nguyên các luật."
                    output, _, elapsed, finish_reason = self._generate(
                        repair_prompt, emitted, on_event, context, outside_count, doc_id, ctx_hash, diag)
                    _validate_top_level(output, self.settings)
                    sections, outside_count = self._validate(output, context, diag)
                    sections = _merge_emitted(sections, emitted)
                    if finish_reason in {"MAX_TOKENS", "LENGTH"} or _has_repeated_ngram(stable_json(output)):
                        raise ValueError("K6: repeated text or truncated output")
                    if len(next((s["items"] for s in sections if s["kind"] == "giai_thich"), [])) < self.settings.lecture_min_explanations:
                        raise ValueError("K8: explanation items below minimum")
                    self._finish_validation_row(diag, passed=True)
                    rows = self._lecture_rows(doc_id, ctx_hash, starting_rows)
                    return self._finish(skeleton, sections, "ready", [], _aggregate_usage(rows),
                                        sum(int(row.get("elapsed_ms", 0) or 0) for row in rows), key, ctx_hash, doc_id)
                except Exception as repair_error:
                    diag["validation_rules"].append(_rule_for_error(repair_error))
                    self._finish_validation_row(diag, passed=False, error=repair_error)
                    sections = _fallback_sections(context)
                    rows = self._lecture_rows(doc_id, ctx_hash, starting_rows)
                    sections = _merge_emitted(sections, emitted)
                    return self._finish(skeleton, sections, "fallback", ["ban_trich_cau"], _aggregate_usage(rows),
                                        sum(int(row.get("elapsed_ms", 0) or 0) for row in rows), key, ctx_hash, doc_id)

        result = self.store.single_flight(key, generate)
        if on_event:
            on_event({"event": "final", "lecture": result})
        if preload_next:
            next_id = skeleton["position"].get("next_node_id")
            if next_id:
                Thread(target=self.make, args=(doc_id, graph_version, graph, next_id),
                       kwargs={"allow_spend": allow_spend, "preload_next": False}, daemon=True).start()
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
        })

    def _lecture_rows(self, doc_id: str, ctx_hash: str, offset: int) -> list[dict[str, Any]]:
        rows = [row for row in self.store.usage_rows(doc_id)
                if row.get("purpose") == "lecture" and row.get("context_hash") == ctx_hash]
        return rows[offset:]

    def _generate(self, prompt: str, emitted: dict[str, list[dict[str, Any]]], on_event: Any,
                  context: dict[str, Any], outside_count: int, doc_id: str, ctx_hash: str,
                  diagnostics: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], int, str | None]:
        started = perf_counter()
        if hasattr(self.model, "start_session"):
            session = self.model.start_session(_SYSTEM)
            stream = session.stream_json(prompt, response_schema=LECTURE_SCHEMA)
        else:
            session = None
            stream = self.model.stream_json(_SYSTEM, prompt, LECTURE_SCHEMA)
        buffer = ""
        emitted_indices: set[tuple[str, int]] = set()
        dropped_indices: dict[str, set[int]] = {field: set() for field in emitted}
        stream_dropped_by_rule: dict[str, int] = {}
        stream_dropped_by_source_label: dict[str, int] = {}
        previous_texts = [item["text"] for items in emitted.values() for item in items]
        definition_text = str(context.get("definition", {}).get("quote", ""))
        try:
            for delta in stream:
                buffer += delta
                for field, index, item in _find_closed_array_items(buffer, ("prereq_notes", "explanation", "example", "contrasts")):
                    marker = (field, index)
                    if marker in emitted_indices:
                        continue
                    emitted_indices.add(marker)
                    maximum = {"prereq_notes": self.settings.lecture_max_prerequisites,
                               "explanation": self.settings.lecture_max_explanations,
                               "example": self.settings.lecture_max_examples,
                               "contrasts": self.settings.lecture_max_contrasts}[field]
                    if index >= maximum:
                        continue
                    checked = _valid_item(item, context, section=field, settings=self.settings,
                                          outside_seen=outside_count,
                                          dropped_by_rule=stream_dropped_by_rule,
                                          dropped_by_source_label=stream_dropped_by_source_label)
                    if checked is None:
                        continue
                    if _is_duplicate_idea(checked["text"], previous_texts, definition_text,
                                          self.settings.lecture_duplicate_jaccard_threshold):
                        dropped_indices[field].add(index)
                        diagnostics["dropped_by_rule"]["K6"] = diagnostics["dropped_by_rule"].get("K6", 0) + 1
                        if "K6" not in diagnostics["validation_rules"]:
                            diagnostics["validation_rules"].append("K6")
                        continue
                    if checked["outside_document"]:
                        outside_count += 1
                    if checked in emitted[field]:
                        continue
                    emitted[field].append(checked)
                    previous_texts.append(checked["text"])
                    section_kind = {"prereq_notes": "nhac_nen", "explanation": "giai_thich",
                                    "example": "vi_du", "contrasts": "phan_biet"}[field]
                    if on_event:
                        on_event({"event": "item", "section_kind": section_kind, "item": checked})
            output = json.loads(buffer)
            for field, indices in dropped_indices.items():
                if indices:
                    output[field] = [item for index, item in enumerate(output.get(field, [])) if index not in indices]
            usage = getattr(session, "last_usage", {}) if session is not None else getattr(stream, "usage", {})
            if not usage and getattr(self.model, "last_usage", None):
                usage = self.model.last_usage
            finish_reason = getattr(session, "last_finish_reason", None) if session is not None else None
            elapsed = round((perf_counter() - started) * 1000)
            ttft = getattr(session, "last_ttft_ms", None) if session is not None else None
            cost = token_cost(getattr(self.model, "model_id", self.settings.model_id), usage)
            if getattr(self.model, 'is_replay', False):
                cost = 0.0
            ledger = usage_row(purpose="lecture", model_id=getattr(self.model, "model_id", self.settings.model_id),
                doc_id=doc_id, context_hash=ctx_hash, usage=usage, elapsed_ms=elapsed,
                ttft_ms=ttft, cost_usd=cost)
            ledger.update(generation_id=diagnostics["generation_id"], generation_index=diagnostics["generation_index"])
            self.store.append_usage(ledger)
            return output, dict(usage), elapsed, finish_reason
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
                ttft_ms=getattr(session, "last_ttft_ms", None) if session is not None else None, cost_usd=cost)
            ledger.update(generation_id=diagnostics["generation_id"], generation_index=diagnostics["generation_index"])
            self.store.append_usage(ledger)
            raise

    def _validate(self, output: dict[str, Any], context: dict[str, Any],
                  diagnostics: dict[str, Any] | None = None) -> tuple[list[dict[str, Any]], int]:
        outside_count = 0
        sections = []
        for field, kind in (("prereq_notes", "nhac_nen"), ("explanation", "giai_thich"),
                            ("example", "vi_du"), ("contrasts", "phan_biet")):
            items = []
            limit = {"prereq_notes": self.settings.lecture_max_prerequisites,
                     "explanation": self.settings.lecture_max_explanations,
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
        result = {**skeleton, "status": status, "sections": sections,
                  "warnings": list(dict.fromkeys([*skeleton.get("warnings", []), *warnings])),
                  "self_check": next((section["items"][0] for section in sections
                                      if section.get("kind") == "tu_kiem_tra" and section.get("items")), None),
                  "usage": {"model_id": row["model_id"], "cost_usd": row["cost_usd"],
                            "elapsed_ms": elapsed, **usage}, "lecture_key": key}
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
