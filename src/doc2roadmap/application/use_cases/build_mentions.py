from __future__ import annotations

from collections import Counter
from time import perf_counter

from doc2roadmap.application.ports.embedding import EmbeddingRequest
from doc2roadmap.domain.canonical import digest
from doc2roadmap.domain.unicode_text import TEXT_RULE_VERSION
from doc2roadmap.application.planning import StagePlan
from doc2roadmap.domain.mentions import (
    build_mention_derivatives,
    build_mention_map,
    dense_mentions,
    exact_mentions,
)


DEFAULT_COMMON_NAMES = {
    "data", "dữ liệu", "hệ thống", "kết quả", "method", "model",
    "mô hình", "phương pháp", "process", "quá trình", "result", "system",
}


class BuildMentions:
    def __init__(
        self,
        store,
        embedding,
        *,
        dense_top_k=3,
        dense_min_z=0.0,
        pair_cluster_top_k=3,
        common_names=None,
    ):
        self.store = store
        self.embedding = embedding
        self.dense_top_k = dense_top_k
        self.dense_min_z = dense_min_z
        self.pair_cluster_top_k = pair_cluster_top_k
        self.common_names = set(DEFAULT_COMMON_NAMES if common_names is None else common_names)

    def _clusters(self, doc_id):
        artifact = self.store.load_latest_graph(doc_id)
        while artifact.payload.get("stage") != "clusters":
            upstream = artifact.manifest.get("upstream_version")
            if upstream is None:
                raise ValueError("artifact graph không trỏ về stage clusters")
            artifact = self.store.load_graph(doc_id, upstream)
        return artifact

    def execute(self, doc_id, *, upstream=None):
        return self._run(doc_id, upstream=upstream)

    def plan(self, doc_id, *, upstream=None):
        return self._run(doc_id, upstream=upstream, planning=True)

    def _run(self, doc_id, *, upstream=None, planning=False):
        clusters = upstream if upstream is not None else self._clusters(doc_id)
        if clusters.payload.get("stage") != "clusters":
            raise ValueError("tầng mentions cần artifact clusters")
        cluster_config = clusters.manifest.get("config", {})
        chunks_version = cluster_config.get("chunks_version")
        chunks = (
            self.store.load_chunks(doc_id, chunks_version)
            if chunks_version is not None
            else self.store.load_latest_chunks(doc_id)
        )
        retrieval = self.store.load_latest_retrieval(doc_id)
        canonical_version = cluster_config.get("canonical_version")
        canonical = (
            self.store.load_canonical(doc_id, canonical_version)
            if canonical_version is not None
            else self.store.load_latest_canonical(doc_id)
        )
        if retrieval.manifest["source_hash"] != chunks.manifest["source_hash"]:
            raise ValueError("retrieval và chunks không cùng tài liệu nguồn")
        if retrieval.manifest.get("embedding_model_id") != self.embedding.embedding_model_id:
            raise ValueError("mô hình embedding query không khớp chỉ mục chunk")
        config = {
            "algorithm_id": "mention-map-v3",
            "clusters_version": clusters.version,
            "clusters_config_hash": clusters.manifest["config_hash"],
            "canonical_version": canonical.version,
            "chunks_version": chunks.version,
            "retrieval_version": retrieval.version,
            "retrieval_config_hash": retrieval.manifest["config_hash"],
            "embedding_adapter": self.embedding.identifier,
            "embedding_model_id": self.embedding.embedding_model_id,
            "query_task": "RETRIEVAL_QUERY",
            "exact_normalization": "nfc-casefold-tone-position-final-i-y-v1",
            "common_names": sorted(self.common_names),
            "dense_top_k": self.dense_top_k,
            "dense_min_z": self.dense_min_z,
            "dense_centering": "2*cos-row_mean-column_mean-v1",
            "pair_cluster_selection": "channel-mean-or-per-cluster-top-k-v1",
            "pair_cluster_top_k": self.pair_cluster_top_k,
            "missing_concept_heuristic": "disabled-unmeasured-precision",
        }
        exact = exact_mentions(clusters.payload["nodes"], chunks.result.chunks, common_names=self.common_names)
        legacy_exact = exact_mentions(clusters.payload["nodes"], chunks.result.chunks, common_names=self.common_names, _legacy=True)
        if exact != legacy_exact:
            config["exact_normalization"] = TEXT_RULE_VERSION
        config_hash = digest(config)
        source_hash = digest([clusters.payload, retrieval.payload, canonical.payload.get("edges", [])])
        cached = self.store.find_graph(doc_id, source_hash, config_hash)
        if cached is not None:
            return StagePlan("reused", artifact=cached) if planning else (cached, True)
        if planning:
            count = sum(bool(n.get("learnable")) for n in clusters.payload["nodes"])
            return StagePlan("run", remaining_items=count, unit="embedding_text", calls_estimate=count,
                             usd_estimate=None if count else 0,
                             note="Embedding: số text cần embed (adapter có thể gom batch); giá không nằm trong prerequisite_prompt.")
        started = perf_counter()
        nodes = [dict(node) for node in clusters.payload["nodes"]]
        learnable = sorted((node for node in nodes if node.get("learnable")), key=lambda node: node["node_id"])
        requests = [
            EmbeddingRequest(node.get("description") or node["name"], "RETRIEVAL_QUERY")
            for node in learnable
        ]
        values = self.embedding.embed(requests)
        if len(values) != len(learnable):
            raise ValueError("cổng embedding trả sai số lượng vector query")
        node_vectors = {
            node["node_id"]: tuple(float(value) for value in vector)
            for node, vector in zip(learnable, values, strict=True)
        }
        chunk_vectors = {
            row["chunk_id"]: tuple(float(value) for value in row["vector"])
            for row in retrieval.payload["documents"]
        }
        missing_vectors = {chunk.chunk_id for chunk in chunks.result.chunks} - set(chunk_vectors)
        if missing_vectors:
            raise ValueError(f"chỉ mục thiếu vector chunk: {', '.join(sorted(missing_vectors))}")
        dense, dense_scores = dense_mentions(
            node_vectors,
            chunk_vectors,
            top_k=self.dense_top_k,
            min_z=self.dense_min_z,
        )
        mention_map = build_mention_map(nodes, chunks.result.chunks, exact, dense, dense_scores)
        derivatives = build_mention_derivatives(
            nodes,
            chunks.result.chunks,
            mention_map,
            canonical.payload.get("edges", []),
            pair_cluster_top_k=self.pair_cluster_top_k,
        )
        flags = []
        levels = Counter(row["level"] for rows in mention_map.values() for row in rows.values())
        channels = Counter(channel for rows in mention_map.values() for row in rows.values() for channel in row["channels"])
        stats = {
            "mention_count": sum(levels.values()),
            "mention_levels": dict(sorted(levels.items())),
            "mention_channels": dict(sorted(channels.items())),
            "citation_count": len(derivatives["citations"]),
            "citation_hard_count": sum(row["strength"] == "hard" for row in derivatives["citations"]),
            "citation_soft_count": sum(row["strength"] == "soft" for row in derivatives["citations"]),
            "contact_pair_count": len(derivatives["contact_pairs"]),
            "suspected_pair_count": len(derivatives["suspected_pairs"]),
            "missing_concept_flag_count": len(flags),
            "embedding_request_count": len(requests),
            "runtime_seconds": perf_counter() - started,
        }
        cluster_payload = {
            key: value for key, value in clusters.payload.items() if key != "node_vectors"
        }
        payload = {
            **cluster_payload,
            "stage": "mentions",
            "node_vectors_version": clusters.version,
            "cluster_stats": clusters.payload.get("stats", {}),
            "mention_map": mention_map,
            **derivatives,
            "flags": flags,
            "stats": stats,
        }
        artifact = self.store.save_graph(
            doc_id,
            source_hash,
            config_hash,
            config,
            payload,
            upstream_version=clusters.version,
            manifest_fields={"stage": "mentions", "stats": stats, "text_rules": TEXT_RULE_VERSION,
                             "embedding_transport": getattr(self.embedding, "transport", "unknown")},
        )
        return artifact, False
