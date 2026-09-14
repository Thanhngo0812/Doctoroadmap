from __future__ import annotations

from doc2roadmap.domain.retrieval import HybridRetriever, RetrievalDocument, embedding_text


def _document(
    chunk_id: str,
    text: str,
    vector: tuple[float, ...],
    *,
    stage_id: str | None = None,
    order_index: int = 0,
) -> RetrievalDocument:
    return RetrievalDocument(
        chunk_id=chunk_id,
        text=text,
        vector=vector,
        stage_id=stage_id,
        order_index=order_index,
    )


def test_embedding_text_adds_section_path_without_changing_chunk_text() -> None:
    text = "Nội dung chunk giữ nguyên."

    value = embedding_text(["THỐNG KÊ TOÁN", "1.2. Phân loại mẫu"], text)

    assert value == "THỐNG KÊ TOÁN > 1.2. Phân loại mẫu\n\nNội dung chunk giữ nguyên."
    assert text == "Nội dung chunk giữ nguyên."


def test_bm25_finds_exact_mathematical_symbol() -> None:
    retriever = HybridRetriever(
        [
            _document("probability", "Công thức P(A|B) là xác suất có điều kiện.", (1.0, 0.0)),
            _document("other", "Phân phối xác suất của biến ngẫu nhiên.", (0.0, 1.0)),
        ]
    )

    hits = retriever.search_bm25("P(A|B)")

    assert hits[0].chunk_id == "probability"


def test_bm25_matches_a_term_wrapped_in_parentheses_without_changing_inner_symbols() -> None:
    retriever = HybridRetriever(
        [
            _document(
                "terms",
                "Quá khớp (Overfitting) và xác suất P(A|B).",
                (1.0, 0.0),
            )
        ]
    )

    assert retriever.search_bm25("overfitting")[0].chunk_id == "terms"
    assert retriever.search_bm25("P(A|B)")[0].chunk_id == "terms"


def test_dense_branch_finds_a_paraphrase() -> None:
    retriever = HybridRetriever(
        [
            _document("overfit", "Mô hình ghi nhớ dữ liệu huấn luyện.", (1.0, 0.0)),
            _document("database", "Khoá giao dịch cơ sở dữ liệu.", (0.0, 1.0)),
        ]
    )

    hits = retriever.search_dense((0.9, 0.1))

    assert hits[0].chunk_id == "overfit"


def test_rrf_promotes_the_result_supported_by_both_branches() -> None:
    retriever = HybridRetriever(
        [
            _document("dense-only", "unrelated", (1.0, 0.0), order_index=0),
            _document("both", "needle", (0.9, 0.1), order_index=1),
            _document("middle-a", "unrelated a", (0.7, 0.7), order_index=2),
            _document("middle-b", "unrelated b", (0.0, 1.0), order_index=3),
            _document("sparse-only", "needle needle needle", (-1.0, 0.0), order_index=4),
        ]
    )

    dense = retriever.search_dense((1.0, 0.0))
    sparse = retriever.search_bm25("needle")
    hybrid = retriever.search("needle", (1.0, 0.0))

    assert [hit.chunk_id for hit in dense].index("both") == 1
    assert [hit.chunk_id for hit in sparse].index("both") == 1
    assert hybrid[0].chunk_id == "both"


def test_stage_filter_is_applied_to_dense_bm25_and_hybrid_before_ranking() -> None:
    retriever = HybridRetriever(
        [
            _document("hidden", "needle needle", (1.0, 0.0), stage_id="s2"),
            _document("visible", "needle", (0.8, 0.2), stage_id="s1"),
        ]
    )
    allowed = {"s1"}

    assert [hit.chunk_id for hit in retriever.search_dense((1.0, 0.0), allowed_stage_ids=allowed)] == [
        "visible"
    ]
    assert [hit.chunk_id for hit in retriever.search_bm25("needle", allowed_stage_ids=allowed)] == [
        "visible"
    ]
    assert [
        hit.chunk_id
        for hit in retriever.search("needle", (1.0, 0.0), allowed_stage_ids=allowed)
    ] == ["visible"]
