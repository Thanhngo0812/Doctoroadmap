from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest

from doc2roadmap.domain.entities import (
    CandidateEdge,
    EntityCandidate,
    EvidenceSpan,
    EvidenceValidation,
    GoldEntity,
    VerifiedAlias,
    build_media_candidates,
    build_type_registry,
    edge_jaccard,
    entity_metrics,
    entity_recall,
    locate_evidence,
    node_jaccard,
    validate_llm_edge_type,
    validate_llm_node_type,
    verify_alias,
    verify_evidence_quotes,
)
from doc2roadmap.domain.models import Chunk, ImageRef, TableRef
from doc2roadmap.domain.chunking import chunk_document
from doc2roadmap.infrastructure.parsing import DoclingParser
from doc2roadmap.infrastructure.text import SentencePieceTokenCounter, UnicodeSentenceSplitter

from tests.conftest import load_docling_fixture


def _chunk(
    text: str,
    *,
    chunk_id: str = "c1",
    doc_id: str = "doc",
    char_start: int = 100,
    image_refs: list[ImageRef] | None = None,
    table_refs: list[TableRef] | None = None,
    context_prefix: str | None = None,
    page: int | None = 1,
) -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        doc_id=doc_id,
        order_index=0,
        split_index=0,
        page=page,
        char_start=char_start,
        char_end=char_start + len(text),
        parent_section_id="s1",
        section_path=["Chương 1"],
        heading_level=1,
        block_types=["paragraph"],
        text=text,
        context_prefix=context_prefix,
        image_refs=image_refs or [],
        table_refs=table_refs or [],
        token_count=10,
        tokenizer_id="test",
    )


def _entity(
    candidate_id: str,
    name: str,
    *,
    node_type: str = "concept",
    aliases: tuple[str, ...] = (),
    chunks: tuple[str, ...] = ("c1",),
    learnable: bool = True,
) -> EntityCandidate:
    return EntityCandidate(
        candidate_id=candidate_id,
        doc_id="doc",
        node_type=node_type,
        name=name,
        description=None,
        evidence=[EvidenceSpan(chunk, 0, 1, "x") for chunk in chunks],
        aliases=[
            VerifiedAlias(alias, EvidenceSpan(chunks[0], 0, 1, "x"))
            for alias in aliases
        ],
        first_order_index=0,
        learnable=learnable,
    )


def test_evidence_is_exact_after_b0_normalization_and_uses_document_offsets() -> None:
    chunk = _chunk("Mở đầu.\nNaïve Bayes phân loại thư điện tử.")

    exact = locate_evidence(chunk, "Naïve Bayes phân loại thư điện tử.")
    normalized = locate_evidence(chunk, "  naïve   BAYES\nphân loại thư điện tử.  ")

    local_start = chunk.text.index("Naïve")
    assert exact == EvidenceSpan(
        "c1",
        chunk.char_start + local_start,
        chunk.char_start + len(chunk.text),
        "Naïve Bayes phân loại thư điện tử.",
    )
    assert normalized == exact
    assert locate_evidence(chunk, "Naïve Bayes phân loại tin nhắn.") is None
    assert locate_evidence(chunk, "Mô hình này dùng để phân loại thư điện tử.") is None
    assert locate_evidence(chunk, "") is None

    checked = verify_evidence_quotes(
        chunk,
        ["Naïve Bayes phân loại thư điện tử.", "Naïve Bayes phân loại tin nhắn."],
    )
    assert checked == EvidenceValidation((exact, None), rejected_count=1)


def test_alias_must_occur_inside_its_verified_quote() -> None:
    chunk = _chunk("Quá khớp (overfitting) làm giảm khả năng tổng quát.")

    alias = verify_alias(
        chunk,
        "overfitting",
        "Quá khớp (overfitting) làm giảm khả năng tổng quát.",
    )

    assert alias == VerifiedAlias(
        "overfitting",
        EvidenceSpan(
            "c1",
            100,
            100 + len(chunk.text),
            chunk.text,
        ),
    )
    assert verify_alias(chunk, "NB", chunk.text) is None
    assert verify_alias(chunk, "overfitting", "Quá khớp làm giảm lỗi huấn luyện.") is None


def test_media_are_deduplicated_by_document_type_and_content_id() -> None:
    image_id = "a" * 64
    table_id = "b" * 64
    first_text = "Hình 1: Đường cong học.\nNội dung"
    second_text = "[figure]\nBảng"
    first = _chunk(
        first_text,
        chunk_id="c1",
        image_refs=[ImageRef(image_id, 100)],
        table_refs=[TableRef(table_id, 100 + first_text.index("Nội dung"))],
    )
    second = _chunk(
        second_text,
        chunk_id="c2",
        char_start=200,
        image_refs=[ImageRef(image_id, 200)],
        table_refs=[TableRef(table_id, 200 + second_text.index("Bảng"))],
    )
    concepts = [
        _entity("n1", "Học có giám sát", chunks=("c1",)),
        _entity("n2", "Naïve Bayes", chunks=("c2",)),
    ]

    media, edges = build_media_candidates([first, second], concepts)

    assert [(item.node_type, item.media_id) for item in media] == [
        ("figure", image_id),
        ("table", table_id),
    ]
    figure = media[0]
    assert figure.learnable is False
    assert figure.description == "Hình 1: Đường cong học."
    assert figure.caption_source == "original"
    assert media[1].description is None
    assert media[1].caption_source == "none"
    assert all(item.orphan_reason is None for item in media)
    assert figure.source_chunk_ids == ["c1", "c2"]
    assert [(ref.chunk_id, ref.char_start) for ref in figure.source_refs] == [
        ("c1", 100),
        ("c2", 200),
    ]
    assert {(edge.edge_type, edge.target_candidate_id) for edge in edges} == {
        ("illustrates", "n1"),
        ("illustrates", "n2"),
        ("tabulates", "n1"),
        ("tabulates", "n2"),
    }


def test_uncaptioned_figure_stays_without_description() -> None:
    image_id = "a" * 64
    chunk = _chunk("[figure]", image_refs=[ImageRef(image_id, 100)])

    media, _ = build_media_candidates([chunk], [])

    assert media[0].description is None
    assert media[0].caption_source == "none"


def test_table_uses_declared_context_prefix_as_original_caption() -> None:
    table_id = "b" * 64
    chunk = _chunk(
        "Bảng 1: Kết quả\n\n| X | Y |",
        table_refs=[TableRef(table_id, 100)],
        context_prefix="Bảng 1: Kết quả",
    )

    media, _ = build_media_candidates([chunk], [])

    assert media[0].description == "Bảng 1: Kết quả"
    assert media[0].caption_source == "original"


def test_orphan_media_declares_cover_or_no_concept_reason() -> None:
    cover = _chunk(
        "[figure]",
        image_refs=[ImageRef("a" * 64, 100)],
        page=1,
    )
    body = _chunk(
        "[figure]",
        chunk_id="c2",
        char_start=200,
        image_refs=[ImageRef("b" * 64, 200)],
        page=5,
    )

    media, edges = build_media_candidates([cover, body], [])

    assert edges == []
    assert [item.orphan_reason for item in media] == [
        "cover_art",
        "no_concept_in_chunk",
    ]


def test_four_b0_fixtures_yield_19_figures_and_60_unique_tables() -> None:
    counter = SentencePieceTokenCounter(
        Path("vendor/gemma/tokenizer.model"), "google-gemma-sentencepiece-v1"
    )
    counts: Counter[str] = Counter()
    for name, extension in {
        "nhap-mon-ml": ".pdf",
        "xstk-ch3-1": ".pdf",
        "baocao-canhan": ".docx",
        "naive-bayes": ".pdf",
    }.items():
        parsed = DoclingParser().adapt(load_docling_fixture(name), name + extension)
        chunks = chunk_document(
            parsed.tree, name, counter, UnicodeSentenceSplitter()
        ).chunks
        media, _ = build_media_candidates(chunks, [])
        counts.update(item.node_type for item in media)

    assert counts == {"figure": 19, "table": 60}


def test_open_type_registry_counts_usage_and_guards_reserved_names() -> None:
    nodes = [
        _entity("n1", "A", node_type="theorem"),
        _entity("n2", "B", node_type="theorem"),
        _entity("n3", "C", node_type="new_kind"),
        _entity("m1", "Hình", node_type="figure", learnable=False),
    ]
    edges = [
        CandidateEdge("n1", "n2", "requires"),
        CandidateEdge("n3", "n1", "contrasts_with"),
        CandidateEdge("m1", "n1", "illustrates"),
    ]

    registry = build_type_registry(nodes, edges)

    assert registry.node_types["theorem"].usage_count == 2
    assert registry.node_types["new_kind"].learnable is True
    assert registry.node_types["figure"].learnable is False
    assert registry.edge_types == {
        "contrasts_with": 1,
        "illustrates": 1,
        "requires": 1,
    }
    validate_llm_node_type("new_kind")
    validate_llm_edge_type("contrasts_with")
    validate_llm_edge_type("requires")
    with pytest.raises(ValueError, match="dành riêng"):
        validate_llm_node_type("Figure")
    with pytest.raises(ValueError, match="requires"):
        validate_llm_edge_type("depends_on")


def test_entity_metrics_separate_learnable_nodes_and_measure_granularity() -> None:
    entities = [
        _entity("n1", "A", node_type="concept", chunks=("c1",)),
        _entity("n2", "A", node_type="theorem", chunks=("c2",)),
        _entity("m1", "Hình", node_type="figure", chunks=("c1",), learnable=False),
    ]

    metrics = entity_metrics(
        entities,
        token_count=250,
        section_count=2,
        chunk_sections={"c1": "s1", "c2": "s2"},
    )

    assert metrics.total_entities == 3
    assert metrics.learnable_entities == 2
    assert metrics.learnable_per_1000_tokens == 8.0
    assert metrics.learnable_per_section == 1.0
    assert metrics.cross_section_duplicate_name_ratio == 1.0
    assert metrics.evidence_ratio == 1.0
    assert metrics.distinct_type_count == 3
    assert metrics.type_explosion_ratio == 1.0
    assert metrics.granularity_band == "target"
    assert metrics.by_type == {"concept": 1, "figure": 1, "theorem": 1}

    same_section = entity_metrics(
        entities,
        token_count=250,
        section_count=2,
        chunk_sections={"c1": "s1", "c2": "s1"},
    )
    assert same_section.cross_section_duplicate_name_ratio == 0.0


def test_gold_recall_matches_names_or_aliases_and_excludes_calibration_rows() -> None:
    predicted = [
        _entity("n1", "Overfitting", aliases=("quá khớp",)),
        _entity("n2", "Naïve Bayes"),
        _entity("n3", "Extra"),
    ]
    gold = [
        GoldEntity("Quá khớp", ("overfitting",)),
        GoldEntity("Naive Bayes", ("Naïve Bayes",)),
        GoldEntity("Regularization"),
        GoldEntity("Calibration only", calibration=True),
    ]

    result = entity_recall(predicted, gold)

    assert result.gold_count == 3
    assert result.matched_count == 2
    assert result.predicted_count == 3
    assert result.recall == pytest.approx(2 / 3)
    assert result.excess_ratio == pytest.approx(1 / 3)


def test_node_jaccard_uses_one_to_one_alias_matching() -> None:
    first = [
        _entity("a1", "Overfitting", aliases=("quá khớp", "overfit")),
        _entity("a2", "Regularization"),
    ]
    second = [
        _entity("b1", "Quá khớp", aliases=("overfitting",)),
        _entity("b2", "Underfitting"),
    ]

    assert node_jaccard(first, first) == 1.0
    assert node_jaccard(first, []) == 0.0
    assert node_jaccard([], []) == 1.0
    assert node_jaccard(first, second) == pytest.approx(1 / 3)

    # Greedy matching would find one pair here; maximum one-to-one matching finds two.
    ambiguous_first = [
        _entity("x1", "X1", aliases=("shared", "second")),
        _entity("x2", "X2", aliases=("shared",)),
    ]
    ambiguous_second = [
        _entity("y1", "Y1", aliases=("shared",)),
        _entity("y2", "Y2", aliases=("second",)),
    ]
    assert node_jaccard(ambiguous_first, ambiguous_second) == 1.0


def test_edge_jaccard_reports_a_separate_fraction() -> None:
    first_nodes = {
        "a": _entity("a", "Overfitting", aliases=("quá khớp",)),
        "b": _entity("b", "Regularization"),
        "c": _entity("c", "Validation"),
    }
    second_nodes = {
        "x": _entity("x", "Quá khớp", aliases=("overfitting",)),
        "y": _entity("y", "Regularization"),
        "z": _entity("z", "Dataset"),
    }
    first_edges = [
        CandidateEdge("a", "b", "requires"),
        CandidateEdge("c", "a", "contrasts_with"),
    ]
    second_edges = [
        CandidateEdge("x", "y", "requires"),
        CandidateEdge("z", "x", "contrasts_with"),
    ]

    assert edge_jaccard(
        first_edges, first_nodes, second_edges, second_nodes
    ) == pytest.approx(1 / 3)
    assert edge_jaccard(first_edges, first_nodes, first_edges, first_nodes) == 1.0
    assert edge_jaccard(first_edges, first_nodes, [], {}) == 0.0
    assert edge_jaccard([], {}, [], {}) == 1.0
