from __future__ import annotations

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable, Mapping, Sequence

from .models import Chunk
from .normalization import normalize_text


_MEDIA_TYPES = frozenset({"figure", "table"})
_REQUIRES_ALIASES = frozenset({"prerequisite_of", "depends_on", "needs"})


@dataclass(frozen=True, slots=True)
class EvidenceSpan:
    chunk_id: str
    char_start: int
    char_end: int
    quote: str


@dataclass(frozen=True, slots=True)
class EvidenceValidation:
    results: tuple[EvidenceSpan | None, ...]
    rejected_count: int


@dataclass(frozen=True, slots=True)
class VerifiedAlias:
    name: str
    evidence: EvidenceSpan


@dataclass(frozen=True, slots=True)
class SourceRef:
    chunk_id: str
    char_start: int


@dataclass(slots=True)
class EntityCandidate:
    candidate_id: str
    doc_id: str
    node_type: str
    name: str
    description: str | None
    evidence: list[EvidenceSpan] = field(default_factory=list)
    aliases: list[VerifiedAlias] = field(default_factory=list)
    first_order_index: int = 0
    learnable: bool = True
    media_id: str | None = None
    caption_source: str | None = None
    source_refs: list[SourceRef] = field(default_factory=list)
    orphan_reason: str | None = None
    media_evidence_id: str | None = None
    name_kind: str | None = None

    def __post_init__(self) -> None:
        if self.node_type.casefold() in _MEDIA_TYPES and self.learnable:
            raise ValueError("figure/table phải có learnable=false")

    @property
    def is_media(self) -> bool:
        return self.node_type.casefold() in _MEDIA_TYPES

    @property
    def source_chunk_ids(self) -> list[str]:
        return list(
            dict.fromkeys(
                [item.chunk_id for item in self.evidence]
                + [item.chunk_id for item in self.source_refs]
            )
        )


@dataclass(slots=True)
class CandidateEdge:
    source_candidate_id: str
    target_candidate_id: str
    edge_type: str
    evidence: list[EvidenceSpan] = field(default_factory=list)
    source_refs: list[SourceRef] = field(default_factory=list)
    confirmed: bool = False


@dataclass(frozen=True, slots=True)
class TypeRegistryEntry:
    usage_count: int
    learnable: bool


@dataclass(frozen=True, slots=True)
class TypeRegistry:
    node_types: dict[str, TypeRegistryEntry]
    edge_types: dict[str, int]


@dataclass(frozen=True, slots=True)
class EntityMetrics:
    total_entities: int
    learnable_entities: int
    learnable_per_1000_tokens: float
    learnable_per_section: float
    cross_section_duplicate_name_ratio: float
    evidence_ratio: float
    distinct_type_count: int
    type_explosion_ratio: float
    granularity_band: str
    by_type: dict[str, int]


@dataclass(frozen=True, slots=True)
class GoldEntity:
    name: str
    aliases: tuple[str, ...] = ()
    calibration: bool = False


@dataclass(frozen=True, slots=True)
class RecallMetrics:
    gold_count: int
    predicted_count: int
    matched_count: int
    recall: float
    excess_ratio: float
    evidence_ratio: float


def _text_pattern(value: str, *, boundaries: bool = False) -> re.Pattern[str] | None:
    normalized = normalize_text(value)
    if not normalized:
        return None
    body = r"\s+".join(re.escape(part) for part in normalized.split())
    if boundaries and normalized[0].isalnum():
        body = rf"(?<!\w){body}"
    if boundaries and normalized[-1].isalnum():
        body = rf"{body}(?!\w)"
    return re.compile(body, re.IGNORECASE)


def locate_evidence(chunk: Chunk, quote: str) -> EvidenceSpan | None:
    """Locate an exact normalized quote in B0's document-wide coordinates."""
    pattern = _text_pattern(quote)
    match = pattern.search(chunk.text) if pattern else None
    if match is None:
        return None
    return EvidenceSpan(
        chunk_id=chunk.chunk_id,
        char_start=chunk.char_start + match.start(),
        char_end=chunk.char_start + match.end(),
        quote=chunk.text[match.start() : match.end()],
    )


def verify_evidence_quotes(chunk: Chunk, quotes: Iterable[str]) -> EvidenceValidation:
    results = tuple(locate_evidence(chunk, quote) for quote in quotes)
    return EvidenceValidation(results, sum(result is None for result in results))


def verify_alias(chunk: Chunk, name: str, evidence_quote: str) -> VerifiedAlias | None:
    evidence = locate_evidence(chunk, evidence_quote)
    alias_pattern = _text_pattern(name, boundaries=True)
    if evidence is None or alias_pattern is None or alias_pattern.search(evidence.quote) is None:
        return None
    return VerifiedAlias(name=name, evidence=evidence)


def validate_llm_node_type(node_type: str) -> str:
    value = node_type.strip()
    if not value:
        raise ValueError("node_type không được rỗng")
    if value.casefold() in _MEDIA_TYPES:
        raise ValueError("figure/table là tên dành riêng do code tạo")
    return value


def validate_llm_edge_type(edge_type: str) -> str:
    value = edge_type.strip()
    if not value:
        raise ValueError("edge_type không được rỗng")
    if value.casefold() in _REQUIRES_ALIASES:
        raise ValueError(f"{value} đồng nghĩa với requires; hãy dùng requires")
    return value


def _caption_at(chunk: Chunk, char_start: int) -> str | None:
    local_start = char_start - chunk.char_start
    if not 0 <= local_start < len(chunk.text):
        raise ValueError(f"media ref nằm ngoài chunk {chunk.chunk_id}")
    caption = chunk.text[local_start:].partition("\n")[0].strip()
    return None if caption.casefold() == "[figure]" else caption or None


def build_media_candidates(
    chunks: Iterable[Chunk], concepts: Iterable[EntityCandidate]
) -> tuple[list[EntityCandidate], list[CandidateEdge]]:
    chunks = list(chunks)
    concepts = list(concepts)
    media_by_key: dict[tuple[str, str, str], EntityCandidate] = {}

    for chunk in chunks:
        refs = [
            *(('figure', ref.image_id, ref.char_start) for ref in chunk.image_refs),
            *(('table', ref.table_id, ref.char_start) for ref in chunk.table_refs),
        ]
        for node_type, media_id, char_start in refs:
            key = (chunk.doc_id, node_type, media_id)
            candidate = media_by_key.get(key)
            if candidate is None:
                table_description = chunk.context_prefix if node_type == "table" else None
                candidate = EntityCandidate(
                    candidate_id=f"media:{chunk.doc_id}:{node_type}:{media_id}",
                    doc_id=chunk.doc_id,
                    node_type=node_type,
                    name=table_description or f"{node_type}:{media_id}",
                    description=table_description,
                    first_order_index=chunk.order_index,
                    learnable=False,
                    media_id=media_id,
                    caption_source="original" if table_description else "none",
                )
                media_by_key[key] = candidate
            source_ref = SourceRef(chunk.chunk_id, char_start)
            if source_ref not in candidate.source_refs:
                candidate.source_refs.append(source_ref)
            if node_type == "figure" and candidate.description is None:
                caption = _caption_at(chunk, char_start)
                if caption is not None:
                    candidate.description = candidate.name = caption
                    candidate.caption_source = "original"
            if node_type == "table" and candidate.description is None and chunk.context_prefix:
                candidate.description = candidate.name = chunk.context_prefix
                candidate.caption_source = "original"

    edges_by_key: dict[tuple[str, str, str], CandidateEdge] = {}
    for media in media_by_key.values():
        edge_type = "illustrates" if media.node_type == "figure" else "tabulates"
        for concept in concepts:
            shared_refs = [
                ref for ref in media.source_refs if ref.chunk_id in concept.source_chunk_ids
            ]
            if not concept.learnable or not shared_refs:
                continue
            key = (media.candidate_id, concept.candidate_id, edge_type)
            edge = edges_by_key.setdefault(
                key,
                CandidateEdge(media.candidate_id, concept.candidate_id, edge_type),
            )
            for ref in shared_refs:
                if ref not in edge.source_refs:
                    edge.source_refs.append(ref)

    chunks_by_id = {chunk.chunk_id: chunk for chunk in chunks}
    for media in media_by_key.values():
        if any(edge.source_candidate_id == media.candidate_id for edge in edges_by_key.values()):
            continue
        media_chunks = [chunks_by_id[ref.chunk_id] for ref in media.source_refs]
        if media_chunks and all(chunk.page == 1 for chunk in media_chunks):
            media.orphan_reason = "cover_art"
        elif not any(
            set(concept.source_chunk_ids) & {ref.chunk_id for ref in media.source_refs}
            for concept in concepts
            if concept.learnable
        ):
            media.orphan_reason = "no_concept_in_chunk"
        else:
            media.orphan_reason = "unknown"

    return list(media_by_key.values()), list(edges_by_key.values())


def build_type_registry(
    entities: Iterable[EntityCandidate], edges: Iterable[CandidateEdge]
) -> TypeRegistry:
    entities = list(entities)
    node_counts = Counter(entity.node_type for entity in entities)
    learnable_by_type: dict[str, bool] = {}
    for entity in entities:
        previous = learnable_by_type.setdefault(entity.node_type, entity.learnable)
        if previous != entity.learnable:
            raise ValueError(f"learnable không nhất quán cho kiểu {entity.node_type}")
    return TypeRegistry(
        node_types={
            node_type: TypeRegistryEntry(count, learnable_by_type[node_type])
            for node_type, count in sorted(node_counts.items())
        },
        edge_types=dict(sorted(Counter(edge.edge_type for edge in edges).items())),
    )


def entity_metrics(
    entities: Iterable[EntityCandidate],
    *,
    token_count: int,
    section_count: int,
    chunk_sections: Mapping[str, str],
) -> EntityMetrics:
    if token_count <= 0 or section_count <= 0:
        raise ValueError("token_count và section_count phải lớn hơn 0")
    entities = list(entities)
    learnable = [entity for entity in entities if entity.learnable]
    learned_count = len(learnable)
    by_type = dict(sorted(Counter(entity.node_type for entity in entities).items()))
    distinct_types = len(by_type)
    density = learned_count * 1000 / token_count
    sections_by_name: dict[str, set[str]] = {}
    for entity in learnable:
        sections_by_name.setdefault(_normalized_name(entity.name), set()).update(
            chunk_sections[chunk_id]
            for chunk_id in entity.source_chunk_ids
            if chunk_id in chunk_sections
        )
    duplicate_names = {
        name for name, section_ids in sections_by_name.items() if len(section_ids) > 1
    }
    return EntityMetrics(
        total_entities=len(entities),
        learnable_entities=learned_count,
        learnable_per_1000_tokens=density,
        learnable_per_section=learned_count / section_count,
        cross_section_duplicate_name_ratio=(
            sum(_normalized_name(entity.name) in duplicate_names for entity in learnable)
            / learned_count
            if learned_count
            else 0.0
        ),
        evidence_ratio=(
            sum(bool(entity.evidence or entity.media_evidence_id) for entity in learnable)
            / learned_count
            if learned_count
            else 0.0
        ),
        distinct_type_count=distinct_types,
        type_explosion_ratio=distinct_types / len(entities) if entities else 0.0,
        granularity_band="coarse" if density < 8 else "target" if density <= 15 else "fine",
        by_type=by_type,
    )


def _normalized_name(value: str) -> str:
    value = normalize_text(value).casefold()
    without_punctuation = "".join(
        " " if unicodedata.category(character).startswith("P") else character
        for character in value
    )
    return " ".join(without_punctuation.split())


def _entity_names(entity: EntityCandidate | GoldEntity) -> set[str]:
    aliases = (
        [alias.name for alias in entity.aliases]
        if isinstance(entity, EntityCandidate)
        else entity.aliases
    )
    return {
        normalized
        for value in [entity.name, *aliases]
        if (normalized := _normalized_name(value))
    }


def _maximum_matches(
    first: Sequence[EntityCandidate | GoldEntity],
    second: Sequence[EntityCandidate | GoldEntity],
) -> dict[int, int]:
    second_owner: dict[int, int] = {}
    # ponytail: corpus đích dưới 1.000 node; dựng chỉ mục alias khi phép so này thành nút thắt.
    adjacency = [
        [
            right
            for right, other in enumerate(second)
            if _entity_names(entity) & _entity_names(other)
        ]
        for entity in first
    ]

    def augment(left: int, seen: set[int]) -> bool:
        for right in adjacency[left]:
            if right in seen:
                continue
            seen.add(right)
            if right not in second_owner or augment(second_owner[right], seen):
                second_owner[right] = left
                return True
        return False

    for left in range(len(first)):
        augment(left, set())
    return {left: right for right, left in second_owner.items()}


def entity_recall(
    predicted: Iterable[EntityCandidate], gold: Iterable[GoldEntity]
) -> RecallMetrics:
    predicted = [entity for entity in predicted if entity.learnable]
    gold = [entity for entity in gold if not entity.calibration]
    matched = len(_maximum_matches(predicted, gold))
    predicted_count = len(predicted)
    return RecallMetrics(
        gold_count=len(gold),
        predicted_count=predicted_count,
        matched_count=matched,
        recall=matched / len(gold) if gold else 1.0,
        excess_ratio=(predicted_count - matched) / predicted_count if predicted_count else 0.0,
        evidence_ratio=(
            sum(bool(entity.evidence or entity.media_evidence_id) for entity in predicted)
            / predicted_count
            if predicted_count
            else 0.0
        ),
    )


def node_jaccard(
    first: Iterable[EntityCandidate], second: Iterable[EntityCandidate]
) -> float:
    first = list(first)
    second = list(second)
    intersection = len(_maximum_matches(first, second))
    union = len(first) + len(second) - intersection
    return intersection / union if union else 1.0


def edge_jaccard(
    first_edges: Iterable[CandidateEdge],
    first_nodes: Mapping[str, EntityCandidate],
    second_edges: Iterable[CandidateEdge],
    second_nodes: Mapping[str, EntityCandidate],
) -> float:
    first_entities = list(first_nodes.values())
    second_entities = list(second_nodes.values())
    node_matches = _maximum_matches(first_entities, second_entities)
    first_to_second = {
        first_entities[left].candidate_id: second_entities[right].candidate_id
        for left, right in node_matches.items()
    }
    first = {
        (
            edge.source_candidate_id,
            edge.target_candidate_id,
            normalize_text(edge.edge_type).casefold(),
        )
        for edge in first_edges
    }
    second = {
        (
            edge.source_candidate_id,
            edge.target_candidate_id,
            normalize_text(edge.edge_type).casefold(),
        )
        for edge in second_edges
    }
    intersection = sum(
        (
            first_to_second.get(source),
            first_to_second.get(target),
            edge_type,
        )
        in second
        for source, target, edge_type in first
        if source in first_to_second and target in first_to_second
    )
    union = len(first) + len(second) - intersection
    return intersection / union if union else 1.0
