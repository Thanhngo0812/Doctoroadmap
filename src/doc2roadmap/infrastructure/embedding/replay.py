from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from doc2roadmap.application.ports.embedding import EmbeddingPort, EmbeddingRequest


def embedding_request_hash(request: EmbeddingRequest) -> str:
    payload = json.dumps(
        {"task_type": request.task_type, "text": request.text},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class ReplayEmbedding:
    identifier = "embedding-replay-v1"

    def __init__(self, fixture: Path, *, expected_model_id: str) -> None:
        payload = json.loads(fixture.read_text(encoding="utf-8"))
        model_id = payload.get("embedding_model_id")
        if model_id != expected_model_id:
            raise ValueError(
                f"fixture embedding dùng model '{model_id}', cần '{expected_model_id}'"
            )
        vectors = payload.get("vectors")
        if not isinstance(vectors, dict):
            raise ValueError("fixture embedding thiếu từ điển vector")
        self._embedding_model_id = expected_model_id
        self._vectors = vectors

    @property
    def embedding_model_id(self) -> str:
        return self._embedding_model_id

    def embed(self, requests: Sequence[EmbeddingRequest]) -> list[list[float]]:
        result = []
        for request in requests:
            key = embedding_request_hash(request)
            if key not in self._vectors:
                raise LookupError(f"fixture không có vector cho request {key}")
            vector = self._vectors[key]
            if not isinstance(vector, list):
                raise ValueError(f"vector fixture không hợp lệ: {key}")
            result.append([float(value) for value in vector])
        return result


def record_embedding_fixture(
    path: Path,
    embedding: EmbeddingPort,
    requests: Sequence[EmbeddingRequest],
) -> int:
    unique: dict[str, EmbeddingRequest] = {}
    for request in requests:
        unique.setdefault(embedding_request_hash(request), request)
    vectors = embedding.embed(list(unique.values()))
    if len(vectors) != len(unique):
        raise ValueError("cổng embedding trả sai số lượng vector")
    payload: dict[str, Any] = {
        "schema_version": 1,
        "embedding_model_id": embedding.embedding_model_id,
        "vectors": dict(zip(unique, vectors, strict=True)),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    os.replace(temporary, path)
    return path.stat().st_size
