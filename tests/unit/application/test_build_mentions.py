from types import SimpleNamespace

from doc2roadmap.application.use_cases.build_mentions import BuildMentions


class Embedding:
    identifier = "fake-v1"
    embedding_model_id = "same-model"

    def __init__(self):
        self.calls = []

    def embed(self, requests):
        self.calls.extend(requests)
        return [[1.0, 0.0], [0.0, 1.0]]


class Store:
    def __init__(self):
        nodes = [
            {
                "node_id": "a",
                "name": "Alpha",
                "aliases": [],
                "symbols": [],
                "description": "Alpha",
                "learnable": True,
                "cluster_id": "g1",
                "defining_chunk_ids": ["c1"],
                "source_chunk_ids": ["c1"],
            },
            {
                "node_id": "b",
                "name": "Beta",
                "aliases": [],
                "symbols": [],
                "description": "Beta",
                "learnable": True,
                "cluster_id": "g2",
                "defining_chunk_ids": ["c2"],
                "source_chunk_ids": ["c2"],
            },
        ]
        self.graph = SimpleNamespace(
            payload={"stage": "clusters", "nodes": nodes, "topic_edges": [], "stats": {}},
            version=1,
            manifest={"source_hash": "graph-source", "config_hash": "graph-config"},
        )
        chunks = [
            SimpleNamespace(chunk_id="c1", text="Alpha nhắc Beta", parent_section_id="s1", order_index=0),
            SimpleNamespace(chunk_id="c2", text="Beta", parent_section_id="s1", order_index=1),
        ]
        self.chunks = SimpleNamespace(
            result=SimpleNamespace(chunks=chunks),
            version=1,
            manifest={"source_hash": "source", "config_hash": "chunks-config"},
        )
        self.retrieval = SimpleNamespace(
            payload={
                "documents": [
                    {"chunk_id": "c1", "vector": [1.0, 0.0]},
                    {"chunk_id": "c2", "vector": [0.0, 1.0]},
                ]
            },
            version=1,
            manifest={"source_hash": "source", "embedding_model_id": "same-model", "config_hash": "retrieval-config"},
        )
        self.canonical = SimpleNamespace(payload={"edges": []}, version=1, manifest={})
        self.saved = None

    def load_latest_graph(self, doc_id):
        return self.saved or self.graph

    def load_graph(self, doc_id, version):
        assert version == self.graph.version
        return self.graph

    def load_latest_chunks(self, doc_id):
        return self.chunks

    def load_latest_retrieval(self, doc_id):
        return self.retrieval

    def load_latest_canonical(self, doc_id):
        return self.canonical

    def find_graph(self, doc_id, source_hash, config_hash):
        if self.saved and self.saved.manifest["source_hash"] == source_hash and self.saved.manifest["config_hash"] == config_hash:
            return self.saved
        return None

    def save_graph(self, doc_id, source_hash, config_hash, config, payload, **kwargs):
        self.saved = SimpleNamespace(
            payload=payload,
            version=2,
            path=None,
            manifest={
                "source_hash": source_hash,
                "config_hash": config_hash,
                "config": config,
                "upstream_version": kwargs["upstream_version"],
            },
        )
        return self.saved


def test_mentions_stage_reuses_chunk_vectors_and_reuses_artifact():
    store, embedding = Store(), Embedding()
    use_case = BuildMentions(store, embedding, dense_top_k=1, dense_min_z=0.0)
    first, reused = use_case.execute("doc")
    assert not reused and first.payload["stage"] == "mentions"
    assert all(request.task_type == "RETRIEVAL_QUERY" for request in embedding.calls)
    assert first.payload["mention_map"]["c1"]["a"]["level"] == "definition"
    assert first.payload["mention_map"]["c1"]["a"]["confidence"] == 1.0
    assert "confidence" not in first.payload["mention_map"]["c1"]["b"]
    assert first.payload["stats"]["citation_count"] == (
        first.payload["stats"]["citation_hard_count"] + first.payload["stats"]["citation_soft_count"]
    )
    assert first.payload["flags"] == []
    calls = len(embedding.calls)
    second, reused = use_case.execute("doc")
    assert reused and second is first and len(embedding.calls) == calls
