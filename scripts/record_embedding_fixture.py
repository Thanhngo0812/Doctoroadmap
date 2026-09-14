"""Record real Gemini vectors for the four reviewed B0 fixture documents."""

from __future__ import annotations

import argparse
from pathlib import Path

from doc2roadmap.application.ports.embedding import EmbeddingRequest
from doc2roadmap.config import Settings
from doc2roadmap.domain.retrieval import embedding_text
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore
from doc2roadmap.infrastructure.embedding import GeminiEmbedding, record_embedding_fixture


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--doc-id",
        action="append",
        default=[],
        help="lặp lại tùy ý; mặc định là bốn fixture chuẩn",
    )
    parser.add_argument(
        "--output", type=Path, default=Path("tests/fixtures/embedding/a3-chunks.json")
    )
    args = parser.parse_args()
    doc_ids = args.doc_id or [
        "nhap-mon-ml",
        "xstk-ch3-1",
        "baocao-canhan",
        "naive-bayes",
    ]
    settings = Settings()
    if settings.gemini_api_key is None:
        raise ValueError("thiếu DOC2ROADMAP_GEMINI_API_KEY")
    embedding = GeminiEmbedding(
        settings.gemini_api_key.get_secret_value(),
        model=settings.embedding_model_id,
        output_dimensionality=settings.embedding_dimensions,
        timeout=settings.gemini_timeout_seconds,
    )
    store = JsonArtifactStore(settings.artifact_dir)
    requests = [
        EmbeddingRequest(embedding_text(chunk.section_path, chunk.text), "RETRIEVAL_DOCUMENT")
        for doc_id in doc_ids
        for chunk in store.load_latest_chunks(doc_id).result.chunks
    ]
    size = record_embedding_fixture(args.output, embedding, requests)
    print(f"recorded={args.output} vectors={len(requests)} bytes={size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
