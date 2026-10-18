from __future__ import annotations

import hashlib
import json
import math
import time
from typing import Any

from doc2roadmap.application.ports.embedding import EmbeddingPort, EmbeddingRequest


def _hash(value: Any) -> str:
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def concept_text(node: dict[str, Any]) -> str:
    name = node.get("display_name") or node.get("name") or ""
    description = node.get("description") or ""
    return f"{name}\n\n{description}".strip()


def concept_inputs(nodes: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {"node_id": node["node_id"], "text": concept_text(node)}
        for node in sorted(nodes, key=lambda row: row["node_id"])
        if node.get("learnable") and concept_text(node)
    ]


def build_concept_index(nodes: list[dict[str, Any]], embedding: EmbeddingPort) -> dict[str, Any]:
    inputs = concept_inputs(nodes)
    vectors = embedding.embed([EmbeddingRequest(row["text"], "RETRIEVAL_DOCUMENT") for row in inputs])
    if len(vectors) != len(inputs):
        raise ValueError("cổng embedding trả sai số lượng vector khái niệm")
    if any(len(vector) != 768 for vector in vectors):
        raise ValueError("chỉ mục khái niệm yêu cầu vector 768 chiều")
    return {
        "schema_version": 1,
        "model_id": embedding.embedding_model_id,
        "input_hash": _hash(inputs),
        "items": [{**row, "vector": vector} for row, vector in zip(inputs, vectors, strict=True)],
    }


def lookup_by_description(index: dict[str, Any], query_vector: list[float], *, threshold: float,
                          limit: int = 3) -> list[dict[str, Any]]:
    if limit < 1:
        raise ValueError("limit phải lớn hơn 0")
    qnorm = math.sqrt(sum(float(value) ** 2 for value in query_vector))
    if not qnorm:
        return []
    scored = []
    for item in index.get("items", []):
        vector = item["vector"]
        if len(vector) != len(query_vector):
            raise ValueError("vector truy vấn sai số chiều")
        norm = math.sqrt(sum(float(value) ** 2 for value in vector))
        score = sum(float(a) * float(b) for a, b in zip(query_vector, vector, strict=True)) / (qnorm * norm) if norm else 0
        if score >= threshold:
            scored.append({"node_id": item["node_id"], "score": score, "match": "mo_ta"})
    scored.sort(key=lambda row: (-row["score"], row["node_id"]))
    return scored[:limit]


class IndexConcepts:
    """Cached concept embeddings; graph role/version changes alone do not invalidate text inputs."""

    def __init__(self, store, embedding: EmbeddingPort, phase_b_store=None) -> None:
        self.store = store
        self.embedding = embedding
        self.phase_b_store = phase_b_store

    def execute(self, doc_id: str, graph_version: int, *, dry_run: bool = False,
                allow_spend: bool = False) -> dict[str, Any]:
        graph = self.store.load_graph(doc_id, graph_version)
        nodes = graph.payload.get("nodes", [])
        inputs = concept_inputs(nodes)
        input_hash = _hash(inputs)
        key = f"concept-index:{doc_id}:{self.embedding.embedding_model_id}:{input_hash}"
        cached = self.phase_b_store.get_cache(key) if self.phase_b_store else None
        if cached is not None:
            if dry_run:
                return {"dry_run": True, "reused": True, "graph_version": graph_version,
                        "concept_count": len(inputs), "estimated_input_tokens": 0,
                        "estimated_cost_usd": 0.0, "calls_estimate": 0,
                        "cost_basis": "cached index; no embedding calls"}
            return {**cached, "reused": True, "graph_version": graph_version}

        estimated_tokens = sum(max(1, (len(row["text"]) + 2) // 3) for row in inputs)
        estimated_cost = estimated_tokens * 0.25 / 1_000_000
        if dry_run:
            return {"dry_run": True, "graph_version": graph_version, "concept_count": len(inputs),
                    "estimated_input_tokens": estimated_tokens, "estimated_cost_usd": estimated_cost,
                    "cost_basis": "ước tính bảo thủ 0,25 USD/triệu token; giá embedding chưa được chốt"}
        if not allow_spend:
            raise PermissionError("embedding khái niệm cần allow_spend=True")

        started = time.perf_counter()
        index = build_concept_index(nodes, self.embedding)
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        if self.phase_b_store:
            self.phase_b_store.put_cache(key, index)
            self.phase_b_store.append_usage({
                "doc_id": doc_id,
                "model_id": self.embedding.embedding_model_id,
                "purpose": "embedding",
                "operation": "concept_index",
                "input_count": len(inputs),
                "input_tokens": estimated_tokens,
                "cost_usd": estimated_cost,
                "cost_basis": "estimated; 0.25 USD per million input tokens",
                "elapsed_ms": elapsed_ms,
                "context_hash": input_hash,
            })
        return {**index, "reused": False, "graph_version": graph_version}

    def lookup(self, index: dict[str, Any], query: str, *, threshold: float = 0.65,
               dry_run: bool = False, allow_spend: bool = False) -> list[dict[str, Any]] | dict[str, Any]:
        if index.get("model_id") != self.embedding.embedding_model_id:
            raise ValueError("mô hình embedding truy vấn không khớp chỉ mục khái niệm")
        estimated_tokens = max(1, (len(query) + 2) // 3)
        estimated_cost = estimated_tokens * 0.25 / 1_000_000
        if dry_run:
            return {"dry_run": True, "estimated_input_tokens": estimated_tokens,
                    "estimated_cost_usd": estimated_cost,
                    "cost_basis": "ước tính bảo thủ 0,25 USD/triệu token; giá embedding chưa được chốt"}
        if not allow_spend:
            raise PermissionError("embedding truy vấn cần allow_spend=True")
        started = time.perf_counter()
        vectors = self.embedding.embed([EmbeddingRequest(query, "RETRIEVAL_QUERY")])
        if len(vectors) != 1:
            raise ValueError("cổng embedding trả sai số lượng vector truy vấn")
        if len(vectors[0]) != 768:
            raise ValueError("truy vấn khái niệm yêu cầu vector 768 chiều")
        if self.phase_b_store:
            self.phase_b_store.append_usage({
                "model_id": self.embedding.embedding_model_id,
                "purpose": "embedding",
                "operation": "concept_query",
                "input_count": 1,
                "input_tokens": estimated_tokens,
                "cost_usd": estimated_cost,
                "cost_basis": "estimated; 0.25 USD per million input tokens",
                "elapsed_ms": round((time.perf_counter() - started) * 1000),
                "context_hash": _hash(query),
            })
        return lookup_by_description(index, vectors[0], threshold=threshold)
