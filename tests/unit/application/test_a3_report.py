from __future__ import annotations

import json

import pytest

from doc2roadmap.application.use_cases.report_a3 import (
    compare_candidate_versions,
    evaluate_gold,
    report_candidates,
    review_candidate_types,
)
from doc2roadmap.application.use_cases.extract_entities import DocumentExtraction
from doc2roadmap.domain.entities import CandidateEdge, EntityCandidate, EvidenceSpan
from doc2roadmap.domain.models import Chunk, ChunkingResult, DocumentTree, Section
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore


def _entity(candidate_id: str, name: str, chunk_id: str) -> EntityCandidate:
    return EntityCandidate(
        candidate_id=candidate_id,
        doc_id="book",
        node_type="concept",
        name=name,
        description=f"Mô tả {name}",
        evidence=[EvidenceSpan(chunk_id, 0, 5, name)],
        first_order_index=0,
    )


def _store(tmp_path) -> JsonArtifactStore:
    store = JsonArtifactStore(tmp_path)
    parsed = store.save_parse("book", "source", "parser", "parse", {}, DocumentTree([]))
    sections = [
        Section("calibration", "book", "Hiệu chỉnh", 1, 1, None, ["Hiệu chỉnh"], 0, True),
        Section("evaluation", "book", "Đánh giá", 1, 1, None, ["Đánh giá"], 1, True),
    ]
    chunks = [
        Chunk(
            "c0", "book", 0, 0, 1, 0, 10, "calibration", ["Hiệu chỉnh"], 1,
            ["text"], "Calibration", None, [], 10, "test",
        ),
        Chunk(
            "c1", "book", 1, 0, 2, 11, 31, "evaluation", ["Đánh giá"], 1,
            ["text"], "Overfitting and extra", None, [], 20, "test",
        ),
    ]
    store.save_chunks(
        "book", "source", "chunks", {"tokenizer_id": "test"}, parsed.version,
        ChunkingResult("book", sections, chunks, "Calibration\nOverfitting and extra"),
    )
    first = DocumentExtraction(
        "book",
        [_entity("a", "Calibration", "c0"), _entity("b", "Overfitting", "c1")],
        [CandidateEdge("a", "b", "requires")],
        {},
        {},
        [],
        [],
    )
    second = DocumentExtraction(
        "book",
        [_entity("x", "Calibration", "c0"), _entity("y", "Quá khớp", "c1")],
        [CandidateEdge("x", "y", "requires")],
        {},
        {},
        [],
        [],
    )
    second.entities[1].aliases = []
    store.save_candidates(
        "book", "source", "first", {}, first.to_payload(), upstream_version=1,
        manifest_fields={"model_id": "model", "stats": {"metrics": {"learnable_entities": 2}}},
    )
    store.save_candidates(
        "book", "source", "second", {}, second.to_payload(), upstream_version=1,
        manifest_fields={"model_id": "model", "stats": {"metrics": {"learnable_entities": 2}}},
    )
    return store


def test_report_recomputes_document_and_corpus_metrics(tmp_path) -> None:
    store = _store(tmp_path)

    result = report_candidates(store, ["book"])

    assert result["documents"]["book"]["metrics"]["learnable_entities"] == 2
    assert result["corpus"]["metrics"]["learnable_per_1000_tokens"] == pytest.approx(200 / 3)
    assert result["corpus"]["section_count"] == 2


def test_review_types_cli_reads_latest_without_mutation(tmp_path, monkeypatch, capsys) -> None:
    from doc2roadmap.presentation.cli.main import main

    store = _store(tmp_path)
    # Two candidates in book plus one in other: rare per document, not globally.
    other = DocumentExtraction("other", [_entity("z", "Other", "c2")], [], {}, {}, [], [])
    other.entities[0].learnable = False
    store.save_candidates(
        "other", "source", "only", {}, other.to_payload(), upstream_version=1
    )
    monkeypatch.setattr("doc2roadmap.presentation.cli.main.build_artifact_store", lambda: store)
    args = ["a3-review-types", "--doc-id", "book", "--doc-id", "other", "--doc-id", "book"]
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert main(args) == 0
    output = capsys.readouterr().out
    assert "concept | 3 | mixed | false | -" in output
    assert "Quá khớp" in output and "Overfitting" not in output
    assert before == {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    store._write(tmp_path / "type_registry.json", {"node_types": {
        "concept": {"learnable": False, "reviewed": True}
    }})
    assert main(args) == 0
    assert "concept | 3 | mixed | true | false" in capsys.readouterr().out


def test_review_types_excludes_common_and_media_but_counts_corpus(tmp_path) -> None:
    store = _store(tmp_path)
    entities = [_entity(str(i), f"Common {i}", "c") for i in range(3)]
    entities.append(EntityCandidate("media", "other", "figure", "Figure", None, learnable=False))
    store.save_candidates(
        "other", "source", "only", {},
        DocumentExtraction("other", entities, [], {}, {}, [], []).to_payload(),
        upstream_version=1,
    )
    assert review_candidate_types(store, ["other"])["types"] == []
    row = review_candidate_types(store, ["book", "other"])["types"][0]
    assert row["candidate_count"] == 2 and row["corpus_candidate_count"] == 5
    assert row["examples"] == ["Calibration", "Quá khớp"]
    with pytest.raises(ValueError):
        review_candidate_types(store, [])
    with pytest.raises(FileNotFoundError):
        review_candidate_types(store, ["missing"])


def test_compare_versions_reports_node_and_edge_jaccard_separately(tmp_path) -> None:
    store = _store(tmp_path)

    result = compare_candidate_versions(store, "book", 1, 2)

    assert result == {
        "doc_id": "book",
        "first_version": 1,
        "second_version": 2,
        "node_jaccard": pytest.approx(1 / 3),
        "edge_jaccard": 0.0,
    }


def test_gold_evaluation_excludes_calibration_section(tmp_path) -> None:
    store = _store(tmp_path)
    gold = tmp_path / "gold.json"
    gold.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "blind_before_first_a3_run": True,
                "documents": {
                    "book": {
                        "calibration_section_ids": ["calibration"],
                        "sections": [
                            {
                                "section_id": "calibration",
                                "entities": [{"name": "Calibration", "aliases": []}],
                            },
                            {
                                "section_id": "evaluation",
                                "entities": [
                                    {"name": "Overfitting", "aliases": ["Quá khớp"]},
                                    {"name": "Regularization", "aliases": []},
                                ],
                            },
                        ],
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    result = evaluate_gold(store, "book", gold, candidate_version=1)

    assert result["gold_count"] == 2
    assert result["predicted_count"] == 1
    assert result["matched_count"] == 1
    assert result["recall"] == 0.5
    assert result["calibration_section_ids"] == ["calibration"]


def test_committed_gold_was_blind_and_has_reviewed_scope() -> None:
    payload = json.loads(
        __import__("pathlib").Path("tests/fixtures/a3/gold-entities.json").read_text(
            encoding="utf-8"
        )
    )

    assert payload["blind_before_first_a3_run"] is True
    expected = {"nhap-mon-ml": (19, 71), "xstk-ch3-1": (9, 40)}
    for doc_id, (section_count, entity_count) in expected.items():
        document = payload["documents"][doc_id]
        scored = [section for section in document["sections"] if section["include_in_score"]]
        assert len(scored) == section_count
        assert sum(len(section["entities"]) for section in scored) == entity_count
        assert len(document["calibration_section_ids"]) == 1
