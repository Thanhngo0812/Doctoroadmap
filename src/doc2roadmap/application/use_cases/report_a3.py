from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable

from doc2roadmap.application.ports import ArtifactStore
from doc2roadmap.application.use_cases.extract_entities import DocumentExtraction
from doc2roadmap.domain.entities import (
    GoldEntity,
    edge_jaccard,
    entity_metrics,
    entity_recall,
    node_jaccard,
)
from doc2roadmap.domain.canonical import candidate_warnings


def _load_candidates(
    store: ArtifactStore, doc_id: str, version: int | None = None
):
    return (
        store.load_candidates(doc_id, version)
        if version is not None
        else store.load_latest_candidates(doc_id)
    )


def review_candidate_types(store: ArtifactStore, doc_ids: Iterable[str]) -> dict[str, Any]:
    reviewed = store.load_reviewed_node_types()
    documents = {}
    by_type: dict[str, list] = {}
    corpus_counts: Counter[str] = Counter()
    for doc_id in dict.fromkeys(doc_ids):
        stored = _load_candidates(store, doc_id)
        documents[doc_id] = stored.version
        entities = DocumentExtraction.from_payload(stored.payload).entities
        counts = Counter(entity.node_type for entity in entities if not entity.is_media)
        corpus_counts.update(counts)
        for entity in entities:
            if not entity.is_media and counts[entity.node_type] <= 2:
                by_type.setdefault(entity.node_type, []).append(entity)
    if not documents:
        raise ValueError("cần ít nhất một doc_id để soát kiểu A3")
    rows = []
    for name in sorted(by_type, key=lambda name: (name in reviewed, name)):
        entities = by_type[name]
        flags = {entity.learnable for entity in entities}
        rows.append({
            "node_type": name,
            "candidate_count": len(entities),
            "corpus_candidate_count": corpus_counts[name],
            "artifact_learnable": next(iter(flags)) if len(flags) == 1 else "mixed",
            "reviewed": name in reviewed,
            "reviewed_learnable": reviewed.get(name),
            "examples": sorted({entity.name for entity in entities})[:3],
        })
    return {"documents": documents, "types": rows}


def report_candidates(store: ArtifactStore, doc_ids: Iterable[str]) -> dict[str, Any]:
    documents: dict[str, Any] = {}
    corpus_entities = []
    corpus_chunk_sections: dict[str, str] = {}
    corpus_tokens = 0
    corpus_sections = 0
    for doc_id in doc_ids:
        stored = _load_candidates(store, doc_id)
        extraction = DocumentExtraction.from_payload(stored.payload)
        chunks = store.load_latest_chunks(doc_id).result
        token_count = sum(chunk.token_count for chunk in chunks.chunks)
        section_count = sum(section.has_direct_content for section in chunks.sections)
        metrics = entity_metrics(
            extraction.entities,
            token_count=token_count,
            section_count=section_count,
            chunk_sections={
                chunk.chunk_id: chunk.parent_section_id for chunk in chunks.chunks
            },
        )
        documents[doc_id] = {
            "candidate_quality": candidate_warnings(extraction.entities, {
                c.chunk_id: c.parent_section_id for c in chunks.chunks
            }),
            "candidate_version": stored.version,
            "model_id": stored.manifest.get("model_id"),
            "token_count": token_count,
            "section_count": section_count,
            "edge_count": len(extraction.edges),
            "metrics": asdict(metrics),
            "warnings": extraction.warnings,
            "stats": extraction.stats,
        }
        corpus_entities.extend(extraction.entities)
        corpus_chunk_sections.update(
            {chunk.chunk_id: chunk.parent_section_id for chunk in chunks.chunks}
        )
        corpus_tokens += token_count
        corpus_sections += section_count
    if not documents:
        raise ValueError("cần ít nhất một doc_id để lập báo cáo A3")
    return {
        "documents": documents,
        "corpus": {
            "document_count": len(documents),
            "token_count": corpus_tokens,
            "section_count": corpus_sections,
            "metrics": asdict(
                entity_metrics(
                    corpus_entities,
                    token_count=corpus_tokens,
                    section_count=corpus_sections,
                    chunk_sections=corpus_chunk_sections,
                )
            ),
        },
    }


def compare_candidate_versions(
    store: ArtifactStore,
    doc_id: str,
    first_version: int,
    second_version: int,
) -> dict[str, Any]:
    first = DocumentExtraction.from_payload(
        store.load_candidates(doc_id, first_version).payload
    )
    second = DocumentExtraction.from_payload(
        store.load_candidates(doc_id, second_version).payload
    )
    return {
        "doc_id": doc_id,
        "first_version": first_version,
        "second_version": second_version,
        "node_jaccard": node_jaccard(first.entities, second.entities),
        "edge_jaccard": edge_jaccard(
            first.edges,
            {entity.candidate_id: entity for entity in first.entities},
            second.edges,
            {entity.candidate_id: entity for entity in second.entities},
        ),
    }


def evaluate_gold(
    store: ArtifactStore,
    doc_id: str,
    gold_path: Path,
    *,
    candidate_version: int | None = None,
) -> dict[str, Any]:
    gold_payload = json.loads(gold_path.read_text(encoding="utf-8"))
    if gold_payload.get("schema_version") != 1:
        raise ValueError("bộ vàng A3 không đúng schema_version")
    if gold_payload.get("blind_before_first_a3_run") is not True:
        raise ValueError("bộ vàng A3 phải xác nhận đã gán mù trước lần chạy đầu")
    try:
        document_gold = gold_payload["documents"][doc_id]
    except (KeyError, TypeError) as error:
        raise ValueError(f"bộ vàng không có tài liệu '{doc_id}'") from error

    calibration = set(document_gold.get("calibration_section_ids", []))
    sections = document_gold.get("sections")
    if not isinstance(sections, list):
        raise ValueError("bộ vàng thiếu danh sách sections")
    evaluation_sections = {
        section["section_id"] for section in sections if section["section_id"] not in calibration
    }
    gold_entities = [
        GoldEntity(entity["name"], tuple(entity.get("aliases", [])))
        for section in sections
        if section["section_id"] in evaluation_sections
        for entity in section.get("entities", [])
    ]

    chunk_sections = {
        chunk.chunk_id: chunk.parent_section_id
        for chunk in store.load_latest_chunks(doc_id).result.chunks
    }
    extraction = DocumentExtraction.from_payload(
        _load_candidates(store, doc_id, candidate_version).payload
    )
    predicted = [
        entity
        for entity in extraction.entities
        if entity.learnable
        and any(
            chunk_sections.get(chunk_id) in evaluation_sections
            for chunk_id in entity.source_chunk_ids
        )
    ]
    result = asdict(entity_recall(predicted, gold_entities))
    return {
        "doc_id": doc_id,
        "candidate_version": candidate_version
        or _load_candidates(store, doc_id).version,
        "calibration_section_ids": sorted(calibration),
        "evaluation_section_count": len(evaluation_sections),
        **result,
    }
