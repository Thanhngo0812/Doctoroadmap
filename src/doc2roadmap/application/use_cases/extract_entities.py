from __future__ import annotations

import hashlib
import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

from doc2roadmap.application.extraction_prompt import (
    ENTITY_SCHEMA,
    ExtractionPrompts,
    VALIDATION_SCHEMA,
    glean_prompt,
    load_prompts,
    prompt_hash,
    section_prompt,
    validation_prompt,
)
from doc2roadmap.application.ports import ArtifactStore, StoredChunks
from doc2roadmap.application.ports.embedding import EmbeddingPort, EmbeddingRequest
from doc2roadmap.application.ports.extraction import EntityExtractor, PromptImage
from doc2roadmap.domain.entities import (
    CandidateEdge,
    EntityCandidate,
    EvidenceSpan,
    SourceRef,
    VerifiedAlias,
    build_media_candidates,
    build_type_registry,
    edge_jaccard,
    entity_metrics,
    locate_evidence,
    node_jaccard,
    validate_llm_edge_type,
    validate_llm_node_type,
    verify_alias,
)
from doc2roadmap.domain.models import Chunk
from doc2roadmap.domain.canonical import candidate_warnings
from doc2roadmap.domain.normalization import normalize_text
from doc2roadmap.domain.ports import TokenCounter


MAX_GLEAN_ROUNDS = 5


class ExtractionGateError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class FormulaContext:
    chunk_id: str
    char_start: int
    raw_text: str


@dataclass(slots=True)
class SectionContext:
    section_id: str
    title: str
    section_path: list[str]
    chunks: list[Chunk]
    images: list[PromptImage]
    formulas: list[FormulaContext]
    media_captions: dict[tuple[str, str], str] = field(default_factory=dict)


@dataclass(slots=True)
class SectionExtraction:
    section_id: str
    title: str
    entities: list[EntityCandidate]
    edges: list[CandidateEdge]
    stats: dict[str, Any]

    @property
    def empty(self) -> bool:
        return not self.entities


@dataclass(slots=True)
class DocumentExtraction:
    doc_id: str
    entities: list[EntityCandidate]
    edges: list[CandidateEdge]
    candidate_embeddings: dict[str, list[float]]
    stats: dict[str, Any]
    warnings: list[str]
    failed_sections: list[str]
    coverage_incomplete: bool = False

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "doc_id": self.doc_id,
            "entities": [_entity_to_dict(entity) for entity in self.entities],
            "edges": [_edge_to_dict(edge) for edge in self.edges],
            "candidate_embeddings": self.candidate_embeddings,
            "stats": self.stats,
            "warnings": self.warnings,
            "failed_sections": self.failed_sections,
            "coverage_incomplete": self.coverage_incomplete,
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> DocumentExtraction:
        return cls(
            doc_id=payload["doc_id"],
            entities=[_entity_from_dict(item) for item in payload["entities"]],
            edges=[_edge_from_dict(item) for item in payload["edges"]],
            candidate_embeddings={
                key: [float(value) for value in vector]
                for key, vector in payload.get("candidate_embeddings", {}).items()
            },
            stats=payload["stats"],
            warnings=list(payload.get("warnings", [])),
            failed_sections=list(payload.get("failed_sections", [])),
            coverage_incomplete=bool(payload.get("coverage_incomplete")),
        )


@dataclass(slots=True)
class ExtractionSummary:
    result: DocumentExtraction
    config_hash: str
    reused: bool
    artifact_path: Path | None
    artifact_version: int | None


def _identity(value: str) -> str:
    return " ".join(normalize_text(value).casefold().split())


def candidate_id_for(doc_id: str, section_id: str, name: str) -> str:
    payload = f"{doc_id}\0{section_id}\0{_identity(name)}".encode("utf-8")
    return "candidate_" + hashlib.sha256(payload).hexdigest()[:24]


def _edge_id(edge: CandidateEdge) -> str:
    payload = (
        f"{edge.source_candidate_id}\0{edge.target_candidate_id}\0"
        f"{_identity(edge.edge_type)}"
    ).encode("utf-8")
    return "edge_" + hashlib.sha256(payload).hexdigest()[:24]


def ensure_empty_rate(empty_count: int, section_count: int) -> None:
    if section_count <= 0:
        raise ValueError("section_count phải lớn hơn 0")
    if empty_count / section_count > 0.4:
        raise ExtractionGateError(
            f"dừng A3: {empty_count}/{section_count} section rỗng, vượt cổng 40%"
        )


def _list(payload: Any, key: str) -> list[Any]:
    if not isinstance(payload, dict) or not isinstance(payload.get(key), list):
        raise ValueError(f"phản hồi trích thiếu mảng '{key}'")
    return payload[key]


def _find_evidence(chunks: Iterable[Chunk], quote: str) -> EvidenceSpan | None:
    for chunk in chunks:
        if evidence := locate_evidence(chunk, quote):
            return evidence
    return None


def _entity_names(entity: EntityCandidate) -> set[str]:
    return {_identity(entity.name), *(_identity(alias.name) for alias in entity.aliases)}


def _add_entity(
    raw: Any,
    context: SectionContext,
    entities: list[EntityCandidate],
    stats: dict[str, Any],
) -> tuple[EntityCandidate | None, bool]:
    if not isinstance(raw, dict):
        stats["rejected_malformed_entities"] += 1
        return None, False
    try:
        name = str(raw["name"]).strip()
        node_type = validate_llm_node_type(str(raw["node_type"]))
        quote = str(raw["evidence"])
    except (KeyError, ValueError):
        stats["rejected_reserved_or_missing_type"] += 1
        return None, False
    if not name:
        stats["rejected_malformed_entities"] += 1
        return None, False
    learnable = raw.get("learnable", True)
    if not isinstance(learnable, bool):
        stats["rejected_malformed_entities"] += 1
        return None, False
    evidence = _find_evidence(context.chunks, quote)
    media_evidence_id = str(raw.get("media_evidence_id", "")).strip() or None
    media_ref = next(
        (
            (chunk, reference)
            for chunk in context.chunks
            for reference in chunk.image_refs
            if reference.image_id == media_evidence_id
        ),
        None,
    )
    if evidence is None and media_ref is None:
        stats["rejected_entity_evidence"] += 1
        return None, False
    source_chunk = (
        next(chunk for chunk in context.chunks if chunk.chunk_id == evidence.chunk_id)
        if evidence is not None
        else media_ref[0]
    )
    aliases = []
    for alias in raw.get("aliases", []):
        if not isinstance(alias, dict) or "name" not in alias or "evidence" not in alias:
            stats["rejected_alias_evidence"] += 1
            continue
        verified = None
        for chunk in context.chunks:
            verified = verify_alias(chunk, str(alias["name"]), str(alias["evidence"]))
            if verified is not None:
                break
        if verified is None:
            stats["rejected_alias_evidence"] += 1
        elif all(_identity(item.name) != _identity(verified.name) for item in aliases):
            aliases.append(verified)
    description = str(raw.get("description_draft", "")).strip() or None
    candidate = EntityCandidate(
        candidate_id=candidate_id_for(source_chunk.doc_id, context.section_id, name),
        doc_id=source_chunk.doc_id,
        node_type=node_type,
        name=name,
        description=description,
        evidence=[evidence] if evidence is not None else [],
        aliases=aliases,
        first_order_index=source_chunk.order_index,
        learnable=learnable,
        source_refs=(
            [SourceRef(source_chunk.chunk_id, media_ref[1].char_start)]
            if media_ref is not None and evidence is None
            else []
        ),
        media_evidence_id=media_evidence_id if evidence is None else None,
    )

    names = _entity_names(candidate)
    existing = next((item for item in entities if names & _entity_names(item)), None)
    if existing is None:
        entities.append(candidate)
        return candidate, True
    if evidence is not None and evidence not in existing.evidence:
        existing.evidence.append(evidence)
    for reference in candidate.source_refs:
        if reference not in existing.source_refs:
            existing.source_refs.append(reference)
    if existing.media_evidence_id is None:
        existing.media_evidence_id = candidate.media_evidence_id
    for alias in aliases:
        if all(_identity(item.name) != _identity(alias.name) for item in existing.aliases):
            existing.aliases.append(alias)
    if existing.description is None:
        existing.description = description
    return existing, False


def _name_index(entities: Iterable[EntityCandidate]) -> dict[str, EntityCandidate]:
    result = {}
    for entity in entities:
        for name in _entity_names(entity):
            result[name] = entity
    return result


def _add_edge(
    raw: Any,
    context: SectionContext,
    entities: list[EntityCandidate],
    edges: list[CandidateEdge],
    stats: dict[str, Any],
) -> None:
    if not isinstance(raw, dict):
        stats["rejected_malformed_edges"] += 1
        return
    try:
        edge_type = validate_llm_edge_type(str(raw["edge_type"]))
        source_name = _identity(str(raw["source"]))
        target_name = _identity(str(raw["target"]))
        quote = str(raw["evidence"])
    except (KeyError, ValueError):
        stats["rejected_edge_type"] += 1
        return
    names = _name_index(entities)
    if source_name not in names or target_name not in names:
        stats["rejected_edge_endpoint"] += 1
        return
    evidence = _find_evidence(context.chunks, quote)
    if evidence is None:
        stats["rejected_edge_evidence"] += 1
        return
    candidate = CandidateEdge(
        names[source_name].candidate_id,
        names[target_name].candidate_id,
        edge_type,
        evidence=[evidence],
    )
    existing = next((edge for edge in edges if _edge_id(edge) == _edge_id(candidate)), None)
    if existing is None:
        edges.append(candidate)
    elif evidence not in existing.evidence:
        existing.evidence.append(evidence)


def _process_reply(
    payload: Any,
    context: SectionContext,
    entities: list[EntityCandidate],
    edges: list[CandidateEdge],
    media_descriptions: dict[tuple[str, str], tuple[str, list[str]]],
    stats: dict[str, Any],
) -> int:
    new_count = 0
    for raw in _list(payload, "entities"):
        _, created = _add_entity(raw, context, entities, stats)
        new_count += created
    for raw in _list(payload, "edges"):
        _add_edge(raw, context, entities, edges, stats)
    known_media = {
        *(('figure', reference.image_id) for chunk in context.chunks for reference in chunk.image_refs),
        *(('table', reference.table_id) for chunk in context.chunks for reference in chunk.table_refs),
    }
    for raw in _list(payload, "media_descriptions"):
        if not isinstance(raw, dict):
            continue
        media_id = str(raw.get("media_id", raw.get("image_id", "")))
        media_type = str(raw.get("media_type", "figure" if raw.get("image_id") else ""))
        description = str(raw.get("description", "")).strip()
        key = (media_type, media_id)
        if key not in known_media or not description:
            stats["rejected_media_descriptions"] += 1
            continue
        if key in media_descriptions:
            stats["rejected_media_descriptions"] += 1
            continue
        confirmed = raw.get("confirmed_entities", [])
        if not isinstance(confirmed, list) or any(not isinstance(name, str) for name in confirmed):
            stats["rejected_media_descriptions"] += 1
            continue
        media_descriptions[key] = (description, list(dict.fromkeys(confirmed)))
        stats["model_media_descriptions"] += 1
    return new_count


def _validation_items(
    entities: list[EntityCandidate], edges: list[CandidateEdge]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return (
        [
            {
                "candidate_id": entity.candidate_id,
                "name": entity.name,
                "node_type": entity.node_type,
                "evidence": [span.quote for span in entity.evidence],
                "media_evidence_id": entity.media_evidence_id,
            }
            for entity in entities
        ],
        [
            {
                "edge_id": _edge_id(edge),
                "source_candidate_id": edge.source_candidate_id,
                "target_candidate_id": edge.target_candidate_id,
                "edge_type": edge.edge_type,
                "evidence": [span.quote for span in edge.evidence],
            }
            for edge in edges
        ],
    )


def extract_section(
    context: SectionContext,
    extractor: EntityExtractor,
    *,
    prompts: ExtractionPrompts | None = None,
) -> SectionExtraction:
    if not context.chunks:
        raise ValueError("section trích phải có ít nhất một chunk")
    prompts = prompts or load_prompts()
    stats: dict[str, Any] = {
        "new_entities_per_round": [],
        "glean_limit_reached": False,
        "rejected_entity_evidence": 0,
        "rejected_alias_evidence": 0,
        "rejected_edge_evidence": 0,
        "rejected_edge_endpoint": 0,
        "rejected_edge_type": 0,
        "rejected_reserved_or_missing_type": 0,
        "rejected_malformed_entities": 0,
        "rejected_malformed_edges": 0,
        "validation_removed_entities": 0,
        "validation_removed_edges": 0,
        "rejected_media_descriptions": 0,
        "rejected_confirmation_labels": 0,
        "missing_media_descriptions": 0,
        "generated_media_descriptions": 0,
        "model_media_descriptions": 0,
        "confirmed_media_edges": 0,
        "confirmed_media_edge_ratio": 0.0,
        "orphan_media": 0,
        "unknown_orphan_media": 0,
        "media_grounded_entities": 0,
    }
    entities: list[EntityCandidate] = []
    edges: list[CandidateEdge] = []
    media_descriptions: dict[tuple[str, str], tuple[str, list[str]]] = {}
    session = extractor.start_session(prompts.system)
    first = session.ask_json(
        section_prompt(
            context.section_path,
            [(chunk.chunk_id, chunk.text) for chunk in context.chunks],
            [
                (formula.chunk_id, formula.raw_text, formula.char_start)
                for formula in context.formulas
            ],
            [
                *(
                    (
                        "figure",
                        reference.image_id,
                        chunk.chunk_id,
                        reference.char_start,
                        "original"
                        if ("figure", reference.image_id) in context.media_captions
                        else "missing",
                    )
                    for chunk in context.chunks
                    for reference in chunk.image_refs
                ),
                *(
                    (
                        "table",
                        reference.table_id,
                        chunk.chunk_id,
                        reference.char_start,
                        "original"
                        if ("table", reference.table_id) in context.media_captions
                        else "missing",
                    )
                    for chunk in context.chunks
                    for reference in chunk.table_refs
                ),
            ],
            prompts=prompts,
        ),
        response_schema=ENTITY_SCHEMA,
        images=context.images,
    )
    stats["new_entities_per_round"].append(
        _process_reply(first.payload, context, entities, edges, media_descriptions, stats)
    )

    for round_index in range(MAX_GLEAN_ROUNDS):
        reply = session.ask_json(
            glean_prompt([entity.name for entity in entities], prompts),
            response_schema=ENTITY_SCHEMA,
        )
        added = _process_reply(
            reply.payload, context, entities, edges, media_descriptions, stats
        )
        stats["new_entities_per_round"].append(added)
        if added == 0:
            break
        if round_index == MAX_GLEAN_ROUNDS - 1:
            stats["glean_limit_reached"] = True

    validation_entities, validation_edges = _validation_items(entities, edges)
    validation = session.ask_json(
        validation_prompt(validation_entities, validation_edges, prompts),
        response_schema=VALIDATION_SCHEMA,
    ).payload
    remove_entities = set(_list(validation, "remove_entity_ids"))
    remove_edges = set(_list(validation, "remove_edge_ids"))
    stats["validation_removed_entities"] = sum(
        entity.candidate_id in remove_entities for entity in entities
    )
    entities = [
        entity for entity in entities if entity.candidate_id not in remove_entities
    ]
    kept_ids = {entity.candidate_id for entity in entities}
    stats["validation_removed_edges"] = sum(
        _edge_id(edge) in remove_edges
        or edge.source_candidate_id not in kept_ids
        or edge.target_candidate_id not in kept_ids
        for edge in edges
    )
    edges = [
        edge
        for edge in edges
        if _edge_id(edge) not in remove_edges
        and edge.source_candidate_id in kept_ids
        and edge.target_candidate_id in kept_ids
    ]

    media, media_edges = build_media_candidates(context.chunks, entities)
    for item in media:
        declared_caption = context.media_captions.get(
            (item.node_type, item.media_id or "")
        )
        if item.caption_source == "none" and declared_caption:
            item.description = item.name = declared_caption
            item.caption_source = "original"
        descriptor = media_descriptions.get((item.node_type, item.media_id or ""))
        if item.caption_source == "none" and descriptor is not None:
            item.description = descriptor[0]
            item.caption_source = (
                "generated_multimodal"
                if item.node_type == "figure"
                else "generated_from_content"
            )
            stats["generated_media_descriptions"] += 1
        if not item.description:
            stats["missing_media_descriptions"] += 1
        if item.orphan_reason:
            stats["orphan_media"] += 1
            stats["unknown_orphan_media"] += item.orphan_reason == "unknown"

        confirmed_names = descriptor[1] if descriptor is not None else []
        for confirmed_name in confirmed_names:
            target = _name_index(entities).get(_identity(confirmed_name))
            edge = next(
                (
                    edge
                    for edge in media_edges
                    if edge.source_candidate_id == item.candidate_id
                    and target is not None
                    and edge.target_candidate_id == target.candidate_id
                ),
                None,
            )
            if edge is None:
                stats["rejected_confirmation_labels"] += 1
            else:
                edge.confirmed = True
                stats["confirmed_media_edges"] += 1
    stats["confirmed_media_edge_ratio"] = (
        stats["confirmed_media_edges"] / len(media_edges) if media_edges else 0.0
    )
    stats["llm_calls"] = session.call_count
    stats["json_repairs"] = session.repair_count
    stats["formula_context_count"] = len(context.formulas)
    stats["image_context_count"] = len(context.images)
    stats["media_grounded_entities"] = sum(bool(entity.media_evidence_id) for entity in entities)
    return SectionExtraction(
        context.section_id,
        context.title,
        [*entities, *media],
        [*edges, *media_edges],
        stats,
    )


def _evidence_to_dict(item: EvidenceSpan) -> dict[str, Any]:
    return asdict(item)


def _evidence_from_dict(item: dict[str, Any]) -> EvidenceSpan:
    return EvidenceSpan(**item)


def _entity_to_dict(entity: EntityCandidate) -> dict[str, Any]:
    return {
        "candidate_id": entity.candidate_id,
        "doc_id": entity.doc_id,
        "node_type": entity.node_type,
        "name": entity.name,
        "description_draft": entity.description if entity.learnable else None,
        "description": entity.description if not entity.learnable else None,
        "evidence": [_evidence_to_dict(item) for item in entity.evidence],
        "aliases": [
            {"name": alias.name, "evidence": _evidence_to_dict(alias.evidence)}
            for alias in entity.aliases
        ],
        "first_order_index": entity.first_order_index,
        "learnable": entity.learnable,
        "media_id": entity.media_id,
        "caption_source": entity.caption_source,
        "source_refs": [asdict(item) for item in entity.source_refs],
        "orphan_reason": entity.orphan_reason,
        "media_evidence_id": entity.media_evidence_id,
    }


def _entity_from_dict(item: dict[str, Any]) -> EntityCandidate:
    learnable = bool(item.get("learnable", True))
    return EntityCandidate(
        candidate_id=item["candidate_id"],
        doc_id=item["doc_id"],
        node_type=item["node_type"],
        name=item["name"],
        description=(
            item.get("description_draft") if learnable else item.get("description")
        ),
        evidence=[_evidence_from_dict(value) for value in item.get("evidence", [])],
        aliases=[
            VerifiedAlias(value["name"], _evidence_from_dict(value["evidence"]))
            for value in item.get("aliases", [])
        ],
        first_order_index=int(item.get("first_order_index", 0)),
        learnable=learnable,
        media_id=item.get("media_id"),
        caption_source=item.get("caption_source"),
        source_refs=[SourceRef(**value) for value in item.get("source_refs", [])],
        orphan_reason=item.get("orphan_reason"),
        media_evidence_id=item.get("media_evidence_id"),
    )


def _edge_to_dict(edge: CandidateEdge) -> dict[str, Any]:
    return {
        "edge_id": _edge_id(edge),
        "source_candidate_id": edge.source_candidate_id,
        "target_candidate_id": edge.target_candidate_id,
        "edge_type": edge.edge_type,
        "evidence": [_evidence_to_dict(item) for item in edge.evidence],
        "source_refs": [asdict(item) for item in edge.source_refs],
        "confirmed": edge.confirmed,
    }


def _edge_from_dict(item: dict[str, Any]) -> CandidateEdge:
    return CandidateEdge(
        source_candidate_id=item["source_candidate_id"],
        target_candidate_id=item["target_candidate_id"],
        edge_type=item["edge_type"],
        evidence=[_evidence_from_dict(value) for value in item.get("evidence", [])],
        source_refs=[SourceRef(**value) for value in item.get("source_refs", [])],
        confirmed=bool(item.get("confirmed", item.get("primary", False))),
    )


def _hash(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _collapse_warnings(warnings: Iterable[str]) -> list[str]:
    counts = Counter(warnings)
    return [
        warning if count == 1 else f"{warning} ×{count}"
        for warning, count in counts.items()
    ]


def _build_contexts(store: ArtifactStore, stored: StoredChunks) -> list[SectionContext]:
    parse_version = int(stored.manifest["parse_version"])
    tree = store.load_parse(stored.result.doc_id, parse_version).tree
    formulas = {
        node.formula_id: node.raw_text
        for node in tree.nodes
        if node.formula_id and node.raw_text
    }
    declared_captions: dict[tuple[str, str], str] = {}
    for node in tree.nodes:
        if node.image_id and node.text.strip().casefold() != "[figure]":
            declared_captions[("figure", node.image_id)] = node.text.strip()
        if node.table_id and node.context_prefix:
            declared_captions[("table", node.table_id)] = node.context_prefix.strip()
    sections = {section.section_id: section for section in stored.result.sections}
    chunks_by_section: dict[str, list[Chunk]] = {}
    for chunk in sorted(stored.result.chunks, key=lambda item: item.order_index):
        chunks_by_section.setdefault(chunk.parent_section_id, []).append(chunk)

    contexts = []
    for section_id, chunks in chunks_by_section.items():
        section = sections[section_id]
        images = []
        seen_images = set()
        formula_context = []
        for chunk in chunks:
            for reference in chunk.image_refs:
                if reference.image_id not in seen_images:
                    images.append(
                        PromptImage(
                            reference.image_id,
                            store.load_image(
                                stored.result.doc_id, parse_version, reference.image_id
                            ),
                        )
                    )
                    seen_images.add(reference.image_id)
            for reference in chunk.formula_refs:
                raw = formulas.get(reference.formula_id)
                if raw is None:
                    raise ValueError(
                        f"formula_ref không có raw_text: {reference.formula_id}"
                    )
                formula_context.append(
                    FormulaContext(chunk.chunk_id, reference.char_start, raw)
                )
        contexts.append(
            SectionContext(
                section_id,
                section.title,
                list(section.section_path),
                chunks,
                images,
                formula_context,
                {
                    key: caption
                    for key, caption in declared_captions.items()
                    if key[1]
                    in {
                        *(reference.image_id for chunk in chunks for reference in chunk.image_refs),
                        *(reference.table_id for chunk in chunks for reference in chunk.table_refs),
                    }
                },
            )
        )
    return sorted(contexts, key=lambda context: sections[context.section_id].order_index)


def _run_contexts(
    contexts: list[SectionContext],
    extractor: EntityExtractor,
    *,
    max_workers: int,
    prompts: ExtractionPrompts,
) -> tuple[list[SectionExtraction], list[SectionContext]]:
    if max_workers <= 0:
        raise ValueError("max_workers phải lớn hơn 0")
    outcomes: list[SectionExtraction] = []
    failed: list[SectionContext] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(extract_section, context, extractor, prompts=prompts): context
            for context in contexts
        }
        for future in as_completed(futures):
            context = futures[future]
            try:
                outcome = future.result()
            except Exception:
                failed.append(context)
                continue
            if outcome.stats["missing_media_descriptions"]:
                failed.append(context)
                continue
            outcomes.append(outcome)
            try:
                ensure_empty_rate(sum(item.empty for item in outcomes), len(contexts))
            except ExtractionGateError:
                for pending in futures:
                    pending.cancel()
                raise

    retry_failed = []
    for context in sorted(failed, key=lambda item: contexts.index(item)):
        try:
            outcome = extract_section(context, extractor, prompts=prompts)
        except Exception:
            retry_failed.append(context)
            continue
        # Keep the final partial result for diagnostics; failed blocks artifact publication.
        outcomes.append(outcome)
        if outcome.stats["missing_media_descriptions"]:
            retry_failed.append(context)
        ensure_empty_rate(sum(item.empty for item in outcomes), len(contexts))
    order = {context.section_id: index for index, context in enumerate(contexts)}
    outcomes.sort(key=lambda item: order[item.section_id])
    return outcomes, retry_failed


def _dedupe_document_candidates(
    outcomes: Iterable[SectionExtraction],
) -> tuple[list[EntityCandidate], list[CandidateEdge]]:
    entities: dict[str, EntityCandidate] = {}
    for item in (entity for outcome in outcomes for entity in outcome.entities):
        existing = entities.get(item.candidate_id)
        if existing is None:
            entities[item.candidate_id] = item
            continue
        for value in item.evidence:
            if value not in existing.evidence:
                existing.evidence.append(value)
        for value in item.aliases:
            if value not in existing.aliases:
                existing.aliases.append(value)
        for value in item.source_refs:
            if value not in existing.source_refs:
                existing.source_refs.append(value)
        if item.caption_source == "original" or existing.description is None:
            existing.description = item.description
            existing.name = item.name
            existing.caption_source = item.caption_source
        if existing.orphan_reason == "cover_art" and item.orphan_reason != "cover_art":
            existing.orphan_reason = item.orphan_reason

    edges: dict[str, CandidateEdge] = {}
    for item in (edge for outcome in outcomes for edge in outcome.edges):
        key = _edge_id(item)
        existing = edges.get(key)
        if existing is None:
            edges[key] = item
            continue
        for value in item.evidence:
            if value not in existing.evidence:
                existing.evidence.append(value)
        for value in item.source_refs:
            if value not in existing.source_refs:
                existing.source_refs.append(value)
        existing.confirmed = existing.confirmed or item.confirmed

    media_with_edges = {edge.source_candidate_id for edge in edges.values()}
    for entity in entities.values():
        if entity.is_media and entity.candidate_id in media_with_edges:
            entity.orphan_reason = None
    return list(entities.values()), list(edges.values())


class ExtractEntities:
    def __init__(
        self,
        store: ArtifactStore,
        extractor: EntityExtractor,
        embedding: EmbeddingPort | None,
        *,
        generation: dict[str, Any],
        counter: TokenCounter | None = None,
        prompts: ExtractionPrompts | None = None,
    ) -> None:
        self.store = store
        self.extractor = extractor
        self.embedding = embedding
        self.generation = generation
        self.counter = counter
        self.prompts = prompts or load_prompts()

    def execute(
        self, doc_id: str, *, max_workers: int = 4, force: bool = False
    ) -> ExtractionSummary:
        stored = self.store.load_latest_chunks(doc_id)
        reviewed_types = self.store.load_reviewed_node_types()
        digest = prompt_hash(
            model_id=self.extractor.model_id,
            generation=self.generation,
            prompts=self.prompts,
        )
        embedding_model_id = (
            self.embedding.embedding_model_id if self.embedding is not None else None
        )
        config = {
            "algorithm_id": "a3-section-conversation-v4",
            "reviewed_node_types": reviewed_types,
            "chunks_config_hash": stored.manifest["config_hash"],
            "extractor_id": self.extractor.identifier,
            "model_id": self.extractor.model_id,
            "prompt_hash": digest,
            "generation": self.generation,
            "embedding_model_id": embedding_model_id,
        }
        config_hash = _hash(config)
        source_hash = stored.manifest["source_hash"]
        cached = None if force else self.store.find_candidates(
            doc_id, source_hash, config_hash
        )
        if cached is not None:
            return ExtractionSummary(
                DocumentExtraction.from_payload(cached.payload),
                config_hash,
                True,
                cached.path,
                cached.version,
            )

        contexts = _build_contexts(self.store, stored)
        if not contexts:
            raise ExtractionGateError("dừng A3: tài liệu không có section có nội dung")
        outcomes, failed = _run_contexts(
            contexts,
            self.extractor,
            max_workers=max_workers,
            prompts=self.prompts,
        )
        entities, edges = _dedupe_document_candidates(outcomes)
        learnable_votes: dict[str, Counter[bool]] = {}
        for entity in entities:
            learnable_votes.setdefault(entity.node_type, Counter())[entity.learnable] += 1
        conflicting_learnable_types = sorted(
            node_type for node_type, votes in learnable_votes.items() if len(votes) > 1
        )
        learnable_type_resolutions = {
            node_type: learnable_votes[node_type][True]
            >= learnable_votes[node_type][False]
            for node_type in conflicting_learnable_types
        }
        learnable_type_resolutions.update(
            (name, value) for name, value in reviewed_types.items()
            if name in learnable_votes
        )
        for entity in entities:
            if entity.node_type in learnable_type_resolutions:
                entity.learnable = learnable_type_resolutions[entity.node_type]

        entities_by_name: dict[str, list[EntityCandidate]] = {}
        for entity in entities:
            entities_by_name.setdefault(_identity(entity.name), []).append(entity)
        cross_type_learnable_conflicts = []
        for same_name in entities_by_name.values():
            type_flags = {
                entity.node_type: entity.learnable
                for entity in sorted(same_name, key=lambda item: item.node_type)
            }
            if len(type_flags) > 1 and len(set(type_flags.values())) > 1:
                cross_type_learnable_conflicts.append(
                    {"name": same_name[0].name, "types": type_flags}
                )
        cross_type_learnable_conflicts.sort(key=lambda item: _identity(item["name"]))
        warnings = [
            f"empty_extraction: {outcome.title}"
            for outcome in outcomes
            if outcome.empty
        ]
        warnings.extend(f"coverage_incomplete: {context.title}" for context in failed)
        warnings.extend(
            f"learnable_low_confidence: {name} ({sum(votes.values())})"
            for name, votes in sorted(learnable_votes.items())
            if sum(votes.values()) <= 2 and name not in reviewed_types
            and name not in {"figure", "table"}
        )
        warnings.extend(
            f"learnable_conflict_resolved_{str(resolution).lower()}: {node_type}"
            for node_type, resolution in learnable_type_resolutions.items()
            if node_type in conflicting_learnable_types
        )
        warnings.extend(
            "cross_type_learnable_conflict: "
            f"{item['name']} ({', '.join(f'{key}={str(value).lower()}' for key, value in item['types'].items())})"
            for item in cross_type_learnable_conflicts
        )
        warnings.extend(
            f"missing_media_description: {entity.name}"
            for entity in entities
            if entity.is_media and not entity.description
        )
        warnings.extend(
            f"orphan_media_unknown: {entity.name}"
            for entity in entities
            if entity.orphan_reason == "unknown"
        )

        aggregate: dict[str, Any] = {
            "media_grounded_entities": sum(bool(entity.media_evidence_id) for entity in entities),
            "section_count": len(contexts),
            "completed_section_count": len(outcomes),
            "empty_section_count": sum(outcome.empty for outcome in outcomes),
            "failed_section_count": len(failed),
            "conflicting_learnable_types": conflicting_learnable_types,
            "learnable_type_resolutions": learnable_type_resolutions,
            "reviewed_node_types": reviewed_types,
            "cross_type_learnable_conflicts": cross_type_learnable_conflicts,
            "llm_calls": sum(outcome.stats["llm_calls"] for outcome in outcomes),
            "json_repairs": sum(outcome.stats["json_repairs"] for outcome in outcomes),
            "new_entities_per_round": {
                outcome.section_id: outcome.stats["new_entities_per_round"]
                for outcome in outcomes
            },
            "glean_limit_sections": [
                outcome.section_id
                for outcome in outcomes
                if outcome.stats["glean_limit_reached"]
            ],
            "formula_context_sections": sum(bool(context.formulas) for context in contexts),
            "formula_context_count": sum(len(context.formulas) for context in contexts),
            "formula_context_tokens": sum(
                self.counter.count(formula.raw_text)
                if self.counter is not None
                else len(formula.raw_text.split())
                for context in contexts
                for formula in context.formulas
            ),
        }
        rejection_keys = [
            key
            for key in outcomes[0].stats
            if key.startswith("rejected_") or key.startswith("validation_removed_")
        ] if outcomes else []
        aggregate.update(
            {
                key: sum(int(outcome.stats[key]) for outcome in outcomes)
                for key in rejection_keys
            }
        )
        media_count = sum(entity.is_media for entity in entities)
        aggregate["missing_media_descriptions"] = sum(
            entity.is_media and not entity.description for entity in entities
        )
        aggregate["generated_media_descriptions"] = sum(
            entity.caption_source in {"generated_multimodal", "generated_from_content"}
            for entity in entities
        )
        aggregate["model_media_descriptions"] = sum(
            int(outcome.stats["model_media_descriptions"]) for outcome in outcomes
        )
        media_edges = [
            edge for edge in edges if edge.edge_type in {"illustrates", "tabulates"}
        ]
        aggregate["model_edge_types"] = sorted(
            {edge.edge_type for edge in edges if edge.evidence}
        )
        aggregate["model_edge_type_count"] = len(aggregate["model_edge_types"])
        aggregate["confirmed_media_edges"] = sum(edge.confirmed for edge in media_edges)
        aggregate["confirmed_media_edge_ratio"] = (
            aggregate["confirmed_media_edges"] / len(media_edges) if media_edges else 0.0
        )
        aggregate["orphan_media"] = sum(
            bool(entity.orphan_reason) for entity in entities if entity.is_media
        )
        aggregate["unknown_orphan_media"] = sum(
            entity.orphan_reason == "unknown"
            for entity in entities
            if entity.is_media
        )
        aggregate["orphan_media_ratio"] = (
            aggregate["orphan_media"] / media_count if media_count else 0.0
        )
        aggregate["caption_source_counts"] = dict(
            sorted(
                Counter(
                    entity.caption_source
                    for entity in entities
                    if entity.is_media and entity.caption_source
                ).items()
            )
        )

        candidate_embeddings: dict[str, list[float]] = {}
        vector_counts: Counter[str] = Counter()
        if not failed and self.embedding is not None:
            described = []
            for entity in entities:
                if not entity.learnable and not entity.is_media:
                    continue
                if entity.description:
                    described.append(entity)
                else:
                    kind = "description_draft" if entity.learnable else "media_description"
                    if entity.learnable:
                        warnings.append(f"missing_{kind}: {entity.name}")
            requests = [
                EmbeddingRequest(entity.description or "", "SEMANTIC_SIMILARITY")
                for entity in described
            ]
            vectors = self.embedding.embed(requests) if requests else []
            if len(vectors) != len(described):
                raise ValueError("cổng embedding trả sai số lượng vector ứng viên")
            for entity, vector in zip(described, vectors, strict=True):
                candidate_embeddings[entity.candidate_id] = vector
                vector_counts[entity.node_type] += 1
        aggregate["vector_counts"] = dict(sorted(vector_counts.items()))

        token_count = sum(chunk.token_count for context in contexts for chunk in context.chunks)
        metrics = entity_metrics(
            entities,
            token_count=token_count,
            section_count=len(contexts),
            chunk_sections={
                chunk.chunk_id: context.section_id
                for context in contexts
                for chunk in context.chunks
            },
        )
        aggregate["metrics"] = asdict(metrics)
        quality = candidate_warnings(entities, {
            chunk.chunk_id: context.section_id for context in contexts for chunk in context.chunks
        })
        aggregate["candidate_quality"] = quality
        warnings.extend(quality["warnings"])
        registry = build_type_registry(entities, edges)
        aggregate["type_registry"] = asdict(registry)
        media_description_incomplete = bool(aggregate["missing_media_descriptions"])
        result = DocumentExtraction(
            doc_id,
            entities,
            edges,
            candidate_embeddings,
            aggregate,
            _collapse_warnings(warnings),
            [context.section_id for context in failed],
            coverage_incomplete=bool(failed) or media_description_incomplete,
        )
        if result.coverage_incomplete:
            return ExtractionSummary(result, config_hash, False, None, None)

        previous_jaccard = None
        try:
            previous = DocumentExtraction.from_payload(
                self.store.load_latest_candidates(doc_id).payload
            )
        except FileNotFoundError:
            pass
        else:
            previous_jaccard = {
                "nodes": node_jaccard(previous.entities, entities),
                "edges": edge_jaccard(
                    previous.edges,
                    {item.candidate_id: item for item in previous.entities},
                    edges,
                    {item.candidate_id: item for item in entities},
                ),
            }
        manifest_fields = {
            "model_id": self.extractor.model_id,
            "embedding_model_id": embedding_model_id,
            "prompt_hash": digest,
            "tokenizer_id": stored.manifest["config"].get("tokenizer_id"),
            "type_registry": asdict(registry),
            "stats": aggregate,
            "vector_stage": "description_draft",
            "jaccard_previous": previous_jaccard,
        }
        artifact = self.store.save_candidates(
            doc_id,
            source_hash,
            config_hash,
            config,
            result.to_payload(),
            upstream_version=stored.version,
            manifest_fields=manifest_fields,
            force_new=force,
        )
        return ExtractionSummary(
            result, config_hash, False, artifact.path, artifact.version
        )
