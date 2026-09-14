"""Print reproducible dense/BM25/hybrid ranks for five reviewed corpus queries."""

from __future__ import annotations

import json
import sys

from doc2roadmap.application.ports.embedding import EmbeddingRequest
from doc2roadmap.application.use_cases.index_document import retriever_from_payload
from doc2roadmap.config import Settings
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore
from doc2roadmap.infrastructure.embedding import GeminiEmbedding


QUERIES = (
    ("nhap-mon-ml", "overfitting", "Overfitting"),
    ("nhap-mon-ml", "học từ dữ liệu đã có nhãn", "Học có giám sát"),
    ("xstk-ch3-1", "hệ số tương quan mẫu", "Hệ số tương quan mẫu"),
    ("naive-bayes", "P(A|B)", "P(A|B)"),
    ("baocao-canhan", "lỗi tranh chấp khi nhiều luồng cùng ghi dữ liệu", "Race Condition"),
)


def _rank(hits, chunk_id: str) -> int | None:
    return next((rank for rank, hit in enumerate(hits, 1) if hit.chunk_id == chunk_id), None)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    settings = Settings()
    if settings.gemini_api_key is None:
        raise ValueError("thiếu DOC2ROADMAP_GEMINI_API_KEY")
    embedding = GeminiEmbedding(
        settings.gemini_api_key.get_secret_value(),
        model=settings.embedding_model_id,
        output_dimensionality=settings.embedding_dimensions,
        timeout=settings.gemini_timeout_seconds,
    )
    vectors = embedding.embed(
        [EmbeddingRequest(query, "RETRIEVAL_QUERY") for _, query, _ in QUERIES]
    )
    store = JsonArtifactStore(settings.artifact_dir)
    rows = []
    for (doc_id, query, needle), vector in zip(QUERIES, vectors, strict=True):
        retriever = retriever_from_payload(store.load_latest_retrieval(doc_id).payload)
        target = next(
            document
            for document in retriever.documents
            if needle.casefold() in document.text.casefold()
        )
        count = len(retriever.documents)
        rows.append(
            {
                "doc_id": doc_id,
                "query": query,
                "target_chunk_id": target.chunk_id,
                "dense_rank": _rank(retriever.search_dense(vector, top_k=count), target.chunk_id),
                "bm25_rank": _rank(retriever.search_bm25(query, top_k=count), target.chunk_id),
                "hybrid_rank": _rank(retriever.search(query, vector, top_k=count), target.chunk_id),
            }
        )
    print(json.dumps(rows, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
