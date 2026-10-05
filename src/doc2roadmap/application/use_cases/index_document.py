from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from doc2roadmap.application.stage_measurements import measure_stage
from doc2roadmap.application.ports import ArtifactStore
from doc2roadmap.domain.unicode_text import TEXT_RULE_VERSION
from doc2roadmap.application.ports.embedding import EmbeddingPort, EmbeddingRequest
from doc2roadmap.domain.retrieval import (
    HybridRetriever,
    RetrievalDocument,
    SearchHit,
    embedding_text,
)


@dataclass(slots=True)
class IndexSummary:
    payload: dict[str, Any]
    manifest: dict[str, Any]
    config_hash: str
    reused: bool
    artifact_path: Path
    artifact_version: int


def _hash(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def retriever_from_payload(payload: dict[str, Any]) -> HybridRetriever:
    return HybridRetriever(
        RetrievalDocument(
            chunk_id=item["chunk_id"],
            text=item["text"],
            vector=tuple(float(value) for value in item["vector"]),
            doc_id=item["doc_id"],
            section_id=item["section_id"],
            page=item.get("page"),
            order_index=int(item["order_index"]),
            stage_id=item.get("stage_id"),
        )
        for item in payload["documents"]
    )


class IndexDocument:
    def __init__(self, store: ArtifactStore, embedding: EmbeddingPort) -> None:
        self.store = store
        self.embedding = embedding

    @measure_stage
    def execute(self, doc_id: str) -> IndexSummary:
        stored = self.store.load_latest_chunks(doc_id)
        config = {
            "chunks_config_hash": stored.manifest["config_hash"],
            "embedding_adapter": self.embedding.identifier,
            "embedding_model_id": self.embedding.embedding_model_id,
            "input_format": "section-path-v1",
        }
        config_hash = _hash(config)
        source_hash = stored.manifest["source_hash"]
        cached = self.store.find_retrieval(doc_id, source_hash, config_hash)
        if cached is not None:
            return IndexSummary(
                cached.payload,
                cached.manifest,
                config_hash,
                True,
                cached.path,
                cached.version,
            )

        chunks = sorted(stored.result.chunks, key=lambda item: item.order_index)
        requests = [
            EmbeddingRequest(
                embedding_text(chunk.section_path, chunk.text),
                "RETRIEVAL_DOCUMENT",
            )
            for chunk in chunks
        ]
        vectors = self.embedding.embed(requests)
        if len(vectors) != len(chunks):
            raise ValueError("cổng embedding trả sai số lượng vector chunk")
        payload = {
            "schema_version": 1,
            "documents": [
                {
                    "chunk_id": chunk.chunk_id,
                    "text": chunk.text,
                    "vector": vector,
                    "doc_id": chunk.doc_id,
                    "section_id": chunk.parent_section_id,
                    "page": chunk.page,
                    "order_index": chunk.order_index,
                    "stage_id": None,
                }
                for chunk, vector in zip(chunks, vectors, strict=True)
            ],
        }
        artifact = self.store.save_retrieval(
            doc_id,
            source_hash,
            config_hash,
            config,
            payload,
            upstream_version=stored.version,
            manifest_fields={
                "embedding_model_id": self.embedding.embedding_model_id,
                "embedding_transport": getattr(self.embedding, "transport", "unknown"),
                "chunk_count": len(chunks),
                "text_rules": TEXT_RULE_VERSION,
                "input_format": "section-path-v1",
            },
        )
        return IndexSummary(
            artifact.payload,
            artifact.manifest,
            config_hash,
            False,
            artifact.path,
            artifact.version,
        )


class SearchDocument:
    def __init__(self, store: ArtifactStore, embedding: EmbeddingPort) -> None:
        self.store = store
        self.embedding = embedding

    def execute(
        self,
        doc_id: str,
        query: str,
        *,
        top_k: int = 10,
        allowed_stage_ids: set[str] | None = None,
    ) -> list[SearchHit]:
        if not query.strip():
            raise ValueError("truy vấn không được rỗng")
        stored = self.store.load_latest_retrieval(doc_id)
        expected_model = stored.manifest.get("embedding_model_id")
        if expected_model != self.embedding.embedding_model_id:
            raise ValueError(
                "mô hình embedding truy vấn không khớp mô hình đã lập chỉ mục"
            )
        vectors = self.embedding.embed([EmbeddingRequest(query, "RETRIEVAL_QUERY")])
        if len(vectors) != 1:
            raise ValueError("cổng embedding trả sai số lượng vector truy vấn")
        return retriever_from_payload(stored.payload).search(
            query,
            vectors[0],
            top_k=top_k,
            allowed_stage_ids=allowed_stage_ids,
        )
