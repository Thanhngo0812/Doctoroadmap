from types import SimpleNamespace

from doc2roadmap.application.use_cases.build_clusters import BuildClusters


class Embedding:
    identifier = "fake-v1"
    embedding_model_id = "fake-embedding"

    def __init__(self):
        self.calls = []

    def embed(self, requests):
        self.calls.extend(requests)
        return [[1.0, float(index)] for index, _ in enumerate(requests)]


class Store:
    def __init__(self):
        nodes = [
            {
                "node_id": value,
                "name": value,
                "description": value,
                "learnable": True,
                "media_id": None,
                "source_chunk_ids": ["c1"],
                "defining_chunk_ids": ["c1"],
                "first_order_index": index,
            }
            for index, value in enumerate(("a", "b", "c"))
        ]
        self.canonical = SimpleNamespace(
            payload={"nodes": nodes},
            version=4,
            manifest={"source_hash": "source", "config_hash": "canonical-config"},
        )
        chunk = SimpleNamespace(
            chunk_id="c1",
            parent_section_id="s1",
            order_index=0,
            image_refs=[],
        )
        self.chunks = SimpleNamespace(
            result=SimpleNamespace(chunks=[chunk], sections=[], normalized_full_text=""),
            version=2,
            manifest={"source_hash": "source", "config_hash": "chunks-config"},
        )
        self.saved = None

    def load_latest_canonical(self, doc_id):
        return self.canonical

    def load_latest_chunks(self, doc_id):
        return self.chunks

    def find_graph(self, doc_id, source_hash, config_hash):
        if self.saved and self.saved.manifest["source_hash"] == source_hash and self.saved.manifest["config_hash"] == config_hash:
            return self.saved
        return None

    def save_graph(self, doc_id, source_hash, config_hash, config, payload, **kwargs):
        self.saved = SimpleNamespace(
            payload=payload,
            version=1,
            path=None,
            manifest={
                "source_hash": source_hash,
                "config_hash": config_hash,
                "config": config,
                **kwargs.get("manifest_fields", {}),
            },
        )
        return self.saved


def test_clusters_stage_is_deterministic_and_reused_without_embedding_call():
    store, embedding = Store(), Embedding()
    use_case = BuildClusters(
        store,
        embedding,
        semantic_neighbors=2,
        edge_quantile=0.0,
        resolution=0.1,
        seed=7,
        concept_cap=2,
    )
    first, reused = use_case.execute("doc")
    assert not reused
    assert first.payload["stage"] == "clusters"
    assert all(node["cluster_id"] for node in first.payload["nodes"])
    assert all(request.task_type == "SEMANTIC_SIMILARITY" for request in embedding.calls)
    calls = len(embedding.calls)
    second, reused = use_case.execute("doc")
    assert reused and second is first
    assert len(embedding.calls) == calls
    config = first.manifest["config"]
    assert config["leiden"] == {
        "library": "leidenalg",
        "version": "0.12.0",
        "objective": "CPM",
        "resolution_mode": "override",
        "resolution_override": 0.1,
        "resolution_formula": "sum(concept_edge_weight)/(concept_count*(concept_count-1)/2)",
        "seed": 7,
        "concept_cap": 2,
        "constraint_enforcement": 1e12,
    }
    assert first.manifest["edge_order"] == "source,target"


def test_default_resolution_comes_from_weighted_concept_density_and_is_reported():
    store, embedding = Store(), Embedding()
    artifact, _ = BuildClusters(store, embedding, semantic_neighbors=2, edge_quantile=0.0).execute("doc")
    resolution = artifact.manifest["leiden_resolution"]
    assert resolution["formula"] == "sum(concept_edge_weight)/(concept_count*(concept_count-1)/2)"
    assert resolution["value"] == artifact.payload["stats"]["leiden_resolution"]
    assert set(artifact.payload["stats"]) >= {
        "raw_cluster_count", "raw_tiny_cluster_count", "merge_count", "merge_affected_concept_ratio"
    }
