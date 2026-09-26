from __future__ import annotations

from importlib.metadata import version
from time import perf_counter

from doc2roadmap.application.ports.embedding import EmbeddingRequest
from doc2roadmap.application.leiden_cluster import cluster_nodes, weighted_concept_density
from doc2roadmap.domain.canonical import digest
from doc2roadmap.domain.topic_graph import build_topic_edges
from doc2roadmap.application.planning import StagePlan


class BuildClusters:
    def __init__(
        self,
        store,
        embedding,
        *,
        semantic_neighbors=3,
        edge_quantile=0.5,
        resolution=None,
        seed=42,
        concept_cap=12,
    ):
        self.store = store
        self.embedding = embedding
        self.semantic_neighbors = semantic_neighbors
        self.edge_quantile = edge_quantile
        self.resolution = resolution
        self.seed = seed
        self.concept_cap = concept_cap

    def execute(self, doc_id):
        return self._run(doc_id)

    def plan(self, doc_id):
        return self._run(doc_id, planning=True)

    def _run(self, doc_id, *, planning=False):
        canonical = self.store.load_latest_canonical(doc_id)
        candidate_version = canonical.manifest.get("config", {}).get("candidate_version")
        if candidate_version is None:
            chunks = self.store.load_latest_chunks(doc_id)
        else:
            candidates = self.store.load_candidates(doc_id, candidate_version)
            chunks = self.store.load_chunks(doc_id, candidates.manifest["upstream_version"])
        if canonical.manifest["source_hash"] != chunks.manifest["source_hash"]:
            raise ValueError("canonical và chunks không cùng tài liệu nguồn")
        leiden = {
            "library": "leidenalg",
            "version": version("leidenalg"),
            "objective": "CPM",
            "resolution_mode": "override" if self.resolution is not None else "weighted_concept_density",
            "resolution_override": self.resolution,
            "resolution_formula": "sum(concept_edge_weight)/(concept_count*(concept_count-1)/2)",
            "seed": self.seed,
            "concept_cap": self.concept_cap,
            "constraint_enforcement": 1e12,
        }
        config = {
            "algorithm_id": "a6-a7-topic-graph-v3",
            "canonical_version": canonical.version,
            "canonical_config_hash": canonical.manifest["config_hash"],
            "chunks_version": chunks.version,
            "chunks_config_hash": chunks.manifest["config_hash"],
            "embedding_adapter": self.embedding.identifier,
            "embedding_model_id": self.embedding.embedding_model_id,
            "embedding_task": "SEMANTIC_SIMILARITY",
            "semantic_neighbors": self.semantic_neighbors,
            "edge_quantile": self.edge_quantile,
            "channel_weights": {"cooccurrence": 1.0, "semantic": 1.0, "media": 1.0},
            "leiden": leiden,
        }
        config_hash = digest(config)
        chunk_fingerprint = [
            [
                chunk.chunk_id,
                chunk.parent_section_id,
                chunk.order_index,
                sorted(ref.image_id for ref in getattr(chunk, "image_refs", [])),
            ]
            for chunk in chunks.result.chunks
        ]
        source_hash = digest([canonical.payload, chunk_fingerprint])
        cached = self.store.find_graph(doc_id, source_hash, config_hash)
        if cached is not None:
            return StagePlan("reused", artifact=cached) if planning else (cached, True)
        if planning:
            count = len(canonical.payload["nodes"])
            return StagePlan("run", remaining_items=count, unit="embedding_text", calls_estimate=count,
                             usd_estimate=None if count else 0,
                             note="Embedding: số text cần embed (adapter có thể gom batch); giá không nằm trong prerequisite_prompt.")

        started = perf_counter()

        nodes = [dict(node) for node in canonical.payload["nodes"]]
        ordered = sorted(nodes, key=lambda node: node["node_id"])
        requests = [
            EmbeddingRequest(node.get("description") or node["name"], "SEMANTIC_SIMILARITY")
            for node in ordered
        ]
        embedded = self.embedding.embed(requests)
        if len(embedded) != len(ordered):
            raise ValueError("cổng embedding trả sai số lượng vector node")
        vectors = {
            node["node_id"]: tuple(float(value) for value in vector)
            for node, vector in zip(ordered, embedded, strict=True)
        }
        topic_graph = build_topic_edges(
            nodes,
            chunks.result.chunks,
            vectors,
            semantic_neighbors=self.semantic_neighbors,
            edge_quantile=self.edge_quantile,
        )
        density = weighted_concept_density(nodes, topic_graph["edges"])
        effective_resolution = self.resolution if self.resolution is not None else max(density, 1e-12)
        clusters, cluster_stats = cluster_nodes(
            nodes,
            topic_graph["edges"],
            vectors,
            resolution=effective_resolution,
            seed=self.seed,
            concept_cap=self.concept_cap,
        )
        for node in nodes:
            node["cluster_id"] = clusters[node["node_id"]]
        concept_sizes = sorted(
            sum(node.get("learnable", False) and node["cluster_id"] == cluster_id for node in nodes)
            for cluster_id in set(clusters.values())
        )
        stats = {
            "node_count": len(nodes),
            "edge_count": len(topic_graph["edges"]),
            "cluster_count": len(set(clusters.values())),
            "cluster_concept_sizes": concept_sizes,
            "isolated_node_count": topic_graph["isolated_node_count"],
            "runtime_seconds": perf_counter() - started,
            "weighted_concept_density": density,
            "leiden_resolution": effective_resolution,
            **cluster_stats,
        }
        payload = {
            "schema_version": 1,
            "doc_id": doc_id,
            "stage": "clusters",
            "nodes": nodes,
            "topic_edges": topic_graph["edges"],
            "node_vectors": {key: list(value) for key, value in sorted(vectors.items())},
            "warnings": topic_graph["warnings"],
            "cutoff": topic_graph["cutoff"],
            "channel_maxima": topic_graph["channel_maxima"],
            "stats": stats,
        }
        artifact = self.store.save_graph(
            doc_id,
            source_hash,
            config_hash,
            config,
            payload,
            upstream_version=None,
            manifest_fields={
                "stage": "clusters",
                "edge_order": "source,target",
                "stats": stats,
                "warnings": topic_graph["warnings"],
                "leiden_resolution": {
                    "formula": leiden["resolution_formula"],
                    "weighted_concept_density": density,
                    "value": effective_resolution,
                },
            },
        )
        return artifact, False
