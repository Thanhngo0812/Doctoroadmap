from __future__ import annotations

import json
import math
from collections.abc import Sequence
from time import sleep
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from doc2roadmap.application.ports.embedding import EmbeddingRequest


_TASK_TYPES = {
    "RETRIEVAL_DOCUMENT",
    "RETRIEVAL_QUERY",
    "SEMANTIC_SIMILARITY",
}
_RETRYABLE_HTTP = {408, 429, 500, 502, 503, 504}


class GeminiEmbedding:
    identifier = "gemini-rest-embedding-v1"

    def __init__(
        self,
        api_key: str | None,
        *,
        model: str = "gemini-embedding-001",
        output_dimensionality: int = 768,
        timeout: float = 60.0,
        batch_size: int = 100,
        max_retries: int = 3,
    ) -> None:
        if not api_key or not api_key.strip():
            raise ValueError("thiếu Gemini API key cho embedding")
        if not model or "/" in model:
            raise ValueError("tên mô hình embedding Gemini không hợp lệ")
        if output_dimensionality <= 0 or timeout <= 0 or batch_size <= 0 or max_retries < 0:
            raise ValueError("cấu hình embedding phải lớn hơn 0")
        self._api_key = api_key.strip()
        self._model = model
        self._output_dimensionality = output_dimensionality
        self._timeout = timeout
        self._batch_size = batch_size
        self._max_retries = max_retries

    @property
    def embedding_model_id(self) -> str:
        return f"{self._model}:{self._output_dimensionality}"

    def embed(self, requests: Sequence[EmbeddingRequest]) -> list[list[float]]:
        requests = list(requests)
        if not requests:
            return []
        for item in requests:
            if not item.text:
                raise ValueError("văn bản embedding không được rỗng")
            if item.task_type not in _TASK_TYPES:
                raise ValueError(f"task_type embedding không hỗ trợ: {item.task_type}")

        vectors: list[list[float]] = []
        for start in range(0, len(requests), self._batch_size):
            vectors.extend(self._embed_batch(requests[start : start + self._batch_size]))
        return vectors

    def _embed_batch(self, requests: list[EmbeddingRequest]) -> list[list[float]]:
        model = f"models/{self._model}"
        payload = {
            "requests": [
                {
                    "model": model,
                    "content": {"parts": [{"text": item.text}]},
                    # v1beta batch currently honors these legacy request fields while
                    # silently ignoring embedContentConfig on this endpoint.
                    "taskType": item.task_type,
                    "outputDimensionality": self._output_dimensionality,
                }
                for item in requests
            ]
        }
        request = Request(
            "https://generativelanguage.googleapis.com/v1beta/"
            f"models/{self._model}:batchEmbedContents",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self._api_key,
            },
            method="POST",
        )
        for attempt in range(self._max_retries + 1):
            try:
                with urlopen(request, timeout=self._timeout) as response:
                    value = json.loads(response.read())
                break
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise RuntimeError("Gemini embedding trả JSON không hợp lệ") from error
            except HTTPError as error:
                if error.code not in _RETRYABLE_HTTP or attempt == self._max_retries:
                    raise RuntimeError(f"Gemini embedding lỗi HTTP {error.code}") from error
                sleep(2**attempt)
            except (URLError, TimeoutError) as error:
                if attempt == self._max_retries:
                    raise RuntimeError("không kết nối được Gemini embedding") from error
                sleep(2**attempt)
        embeddings = value.get("embeddings") if isinstance(value, dict) else None
        if not isinstance(embeddings, list) or len(embeddings) != len(requests):
            raise RuntimeError("Gemini embedding trả sai số lượng vector")
        vectors = [embedding.get("values") for embedding in embeddings]
        if any(not isinstance(vector, list) for vector in vectors):
            raise RuntimeError("Gemini embedding thiếu giá trị vector")
        return [self._normalize(vector) for vector in vectors]

    def _normalize(self, values: list[object]) -> list[float]:
        try:
            vector = [float(value) for value in values]
        except (TypeError, ValueError) as error:
            raise RuntimeError("Gemini embedding trả vector không hợp lệ") from error
        if len(vector) != self._output_dimensionality:
            raise RuntimeError("Gemini embedding trả vector sai số chiều")
        norm = math.sqrt(sum(value * value for value in vector))
        if not norm:
            raise RuntimeError("Gemini embedding trả vector zero")
        return [value / norm for value in vector]
