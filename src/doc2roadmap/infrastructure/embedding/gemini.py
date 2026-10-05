from __future__ import annotations

import json
import math
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context
from time import sleep
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from doc2roadmap.application.ports.embedding import EmbeddingRequest
from doc2roadmap.application.stage_measurements import record_model_call, record_usage
from doc2roadmap.infrastructure.google_auth import VertexCredentials
from doc2roadmap.infrastructure.llm.rate_limit import AdaptiveModelLimiter


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
        transport: str = "developer_api",
        vertex_project: str | None = None,
        vertex_location: str = "global",
        limiter: AdaptiveModelLimiter | None = None,
    ) -> None:
        if transport not in {"developer_api", "vertex"}:
            raise ValueError("Gemini embedding transport không hợp lệ")
        if transport == "developer_api" and not (api_key and api_key.strip()):
            raise ValueError("thiếu Gemini API key cho embedding")
        if not model or "/" in model:
            raise ValueError("tên mô hình embedding Gemini không hợp lệ")
        if output_dimensionality <= 0 or timeout <= 0 or batch_size <= 0 or max_retries < 0:
            raise ValueError("cấu hình embedding phải lớn hơn 0")
        self._api_key = api_key.strip() if api_key else None
        self.transport = transport
        self._vertex = VertexCredentials(vertex_project, vertex_location) if transport == "vertex" else None
        self._model = model
        self._output_dimensionality = output_dimensionality
        self._timeout = timeout
        self._batch_size = batch_size
        self._max_retries = max_retries
        self.limiter = limiter

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
        if self._vertex:
            workers = min(len(requests), self.limiter.max_in_flight if self.limiter else self._batch_size)
            with ThreadPoolExecutor(max_workers=workers) as pool:
                return list(pool.map(lambda item: item[0].run(self._embed_vertex, item[1]),
                                     ((copy_context(), item) for item in requests)))
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
        url = (self._vertex.url(self._model, "batchEmbedContents") if self._vertex else
               f"https://generativelanguage.googleapis.com/v1beta/models/{self._model}:batchEmbedContents")
        headers = self._vertex.headers() if self._vertex else {"x-goog-api-key": self._api_key}
        request = Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json", **headers},
            method="POST",
        )
        for attempt in range(self._max_retries + 1):
            try:
                record_model_call(embedding=True)
                with urlopen(request, timeout=self._timeout) as response:
                    value = json.loads(response.read())
                record_usage(value.get("usageMetadata", {}), embedding=True)
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

    def _embed_vertex(self, item: EmbeddingRequest) -> list[float]:
        payload = {"instances": [{"content": item.text, "task_type": item.task_type}],
                   "parameters": {"outputDimensionality": self._output_dimensionality}}
        request = Request(
            self._vertex.url(self._model, "predict"),
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json", **self._vertex.headers()},
            method="POST",
        )
        for attempt in range(self._max_retries + 1):
            estimated_tokens = len(item.text.encode("utf-8")) // 3 + 32
            permit = self.limiter.acquire(estimated_tokens) if self.limiter is not None else None
            try:
                record_model_call(embedding=True)
                with urlopen(request, timeout=self._timeout) as response:
                    value = json.loads(response.read())
                statistics = value["predictions"][0]["embeddings"].get("statistics", {})
                record_usage({"promptTokenCount": statistics["token_count"]} if "token_count" in statistics else {}, embedding=True)
                vector = self._normalize(value["predictions"][0]["embeddings"]["values"])
                if self.limiter is not None:
                    self.limiter.release(permit, success=True)
                    self.limiter.reconcile(permit, estimated_tokens)
                return vector
            except (UnicodeDecodeError, json.JSONDecodeError, KeyError, IndexError, TypeError, RuntimeError) as error:
                if self.limiter is not None:
                    self.limiter.release(permit, success=False)
                raise RuntimeError("Vertex embedding trả phản hồi không hợp lệ") from error
            except HTTPError as error:
                if self.limiter is not None:
                    retry_after = error.headers.get("Retry-After") if error.headers else None
                    try:
                        retry_after = float(retry_after) if retry_after is not None else None
                    except ValueError:
                        retry_after = None
                    self.limiter.release(permit, success=False, throttled=error.code in {429, 503}, retry_after=retry_after)
                if error.code not in _RETRYABLE_HTTP or attempt == self._max_retries:
                    raise RuntimeError(f"Vertex embedding lỗi HTTP {error.code}") from error
            except (URLError, TimeoutError) as error:
                if self.limiter is not None:
                    self.limiter.release(permit, success=False)
                if attempt == self._max_retries:
                    raise RuntimeError("không kết nối được Vertex embedding") from error
            sleep(2**attempt)
        raise AssertionError("unreachable")

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
