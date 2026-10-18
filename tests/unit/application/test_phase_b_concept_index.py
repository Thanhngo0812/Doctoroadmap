from doc2roadmap.application.phase_b.concept_index import (
    IndexConcepts,
    build_concept_index,
    lookup_by_description,
)
from doc2roadmap.application.ports.embedding import EmbeddingRequest


class FakeEmbedding:
    identifier = "fake"
    embedding_model_id = "fake-768"

    def __init__(self):
        self.calls = []

    def embed(self, requests):
        self.calls.extend(requests)
        return [[1.0, *([0.0] * 767)] if "ma trận" in request.text else [0.0, 1.0, *([0.0] * 766)]
                for request in requests]


class FakeStore:
    def __init__(self):
        self.graphs = {1: {"nodes": [
            {"node_id": "n1", "name": "Khử Gauss", "description": "Biến ma trận về bậc thang", "learnable": True},
            {"node_id": "n2", "name": "Định thức", "description": "Giá trị gắn với ma trận vuông", "learnable": True},
            {"node_id": "x", "name": "No", "description": "", "learnable": False},
        ]}, 2: {"nodes": [
            {"node_id": "n1", "name": "Khử Gauss", "description": "Biến ma trận về bậc thang", "learnable": True},
            {"node_id": "n2", "name": "Định thức", "description": "Giá trị gắn với ma trận vuông", "learnable": True},
            {"node_id": "x", "name": "No", "description": "", "learnable": False},
        ]}}

    def load_graph(self, _doc_id, version):
        return type("Artifact", (), {"payload": self.graphs[version]})()


class FakePhaseStore:
    def __init__(self):
        self.cache = {}
        self.usage = []

    def get_cache(self, key):
        return self.cache.get(key)

    def put_cache(self, key, value):
        self.cache[key] = value

    def append_usage(self, row):
        self.usage.append(dict(row))


def test_description_lookup_returns_only_above_threshold_top_three():
    index = {"items": [
        {"node_id": "n1", "vector": [1.0, 0.0]},
        {"node_id": "n2", "vector": [0.8, 0.6]},
        {"node_id": "n3", "vector": [0.7, 0.7]},
        {"node_id": "n4", "vector": [0.0, 1.0]},
    ]}

    result = lookup_by_description(index, [1.0, 0.0], threshold=0.7, limit=3)

    assert [row["node_id"] for row in result] == ["n1", "n2", "n3"]
    assert all(row["match"] == "mo_ta" for row in result)
    assert lookup_by_description(index, [0.0, 1.0], threshold=1.01) == []


def test_concept_index_embeds_only_learnable_nodes_with_names_and_descriptions():
    embedding = FakeEmbedding()
    nodes = FakeStore().graphs[1]["nodes"]

    result = build_concept_index(nodes, embedding)

    assert [row["node_id"] for row in result["items"]] == ["n1", "n2"]
    assert all(request.task_type == "RETRIEVAL_DOCUMENT" for request in embedding.calls)
    assert all("\n\n" in request.text for request in embedding.calls)


def test_index_use_case_reuses_content_when_graph_version_alone_changes():
    embedding, store, phase_store = FakeEmbedding(), FakeStore(), FakePhaseStore()
    use_case = IndexConcepts(store, embedding, phase_store)

    first = use_case.execute("book", 1, allow_spend=True)
    second = use_case.execute("book", 2, allow_spend=True)

    assert first["reused"] is False
    assert second["reused"] is True
    assert len(embedding.calls) == 2
    assert len(phase_store.usage) == 1
    assert phase_store.usage[0]["operation"] == "concept_index"
    assert phase_store.usage[0]["cost_usd"] > 0


def test_concept_index_dry_run_does_not_embed_or_write_cache():
    embedding, store, phase_store = FakeEmbedding(), FakeStore(), FakePhaseStore()
    use_case = IndexConcepts(store, embedding, phase_store)

    plan = use_case.execute("book", 1, dry_run=True)

    assert plan["estimated_input_tokens"] > 0
    assert plan["estimated_cost_usd"] > 0
    assert embedding.calls == []
    assert phase_store.cache == {}


def test_cached_concept_index_dry_run_returns_no_vectors_or_embedding_calls():
    embedding, store, phase_store = FakeEmbedding(), FakeStore(), FakePhaseStore()
    use_case = IndexConcepts(store, embedding, phase_store)
    cached = use_case.execute("book", 1, allow_spend=True)
    embedding.calls.clear()
    usage_before = list(phase_store.usage)

    plan = use_case.execute("book", 2, dry_run=True)

    assert plan == {
        "dry_run": True,
        "reused": True,
        "graph_version": 2,
        "concept_count": len(cached["items"]),
        "estimated_input_tokens": 0,
        "estimated_cost_usd": 0.0,
        "calls_estimate": 0,
        "cost_basis": "cached index; no embedding calls",
    }
    assert "items" not in plan
    assert embedding.calls == []
    assert phase_store.usage == usage_before


def test_lookup_embedding_uses_query_task_and_returns_best_description_match():
    embedding = FakeEmbedding()
    index = build_concept_index(FakeStore().graphs[1]["nodes"], embedding)
    use_case = IndexConcepts(FakeStore(), embedding)

    result = use_case.lookup(index, "phép biến ma trận", allow_spend=True)

    assert result[0]["node_id"] == "n1"
    assert embedding.calls[-1].task_type == "RETRIEVAL_QUERY"
