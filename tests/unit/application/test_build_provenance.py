import json
from types import SimpleNamespace

from doc2roadmap.application.use_cases.build_provenance import BuildProvenance


class Model:
    model_id = "fixture-model"

    def __init__(self, selections):
        self.selections = selections
        self.calls = []

    def start_session(self, system_prompt):
        return self

    def ask_json(self, prompt, *, response_schema):
        data = json.loads(prompt)
        self.calls.append(data)
        return SimpleNamespace(
            payload={"node_id": data["node_id"], "selections": self.selections}
        )


class Store:
    def __init__(self, *, definition_text="Alpha is defined as the first concept."):
        nodes = [
            {
                "node_id": "a",
                "name": "Alpha",
                "aliases": ["First concept"],
                "description": "Alpha",
                "learnable": True,
                "cluster_id": "g1",
                "defining_chunk_ids": ["c2"],
                "source_chunk_ids": ["c2"],
                "first_order_index": 1,
            },
            {
                "node_id": "b",
                "name": "Beta",
                "aliases": [],
                "description": "Beta",
                "learnable": True,
                "cluster_id": "g2",
                "defining_chunk_ids": ["c3"],
                "source_chunk_ids": ["c3"],
                "first_order_index": 2,
            },
        ]
        self.mentions = SimpleNamespace(
            payload={
                "stage": "mentions",
                "nodes": nodes,
                "mention_map": {
                    "c1": {
                        "a": {"level": "mention", "channels": ["exact"]},
                        "b": {"level": "mention", "channels": ["exact"]},
                    },
                    "c2": {"a": {"level": "definition", "channels": ["provenance"]}},
                    "c3": {"b": {"level": "definition", "channels": ["provenance"]}},
                },
                "node_vectors_version": 1,
                "flags": [],
            },
            version=2,
            manifest={
                "source_hash": "mentions-source",
                "config_hash": "mentions-config",
                "config": {
                    "chunks_version": 4,
                    "canonical_version": 5,
                    "pair_cluster_top_k": 3,
                },
            },
        )
        chunks = [
            SimpleNamespace(
                chunk_id="c1",
                text=definition_text + " Beta is discussed too.",
                parent_section_id="s1",
                order_index=0,
            ),
            SimpleNamespace(
                chunk_id="c2", text="Alpha overview.", parent_section_id="s2", order_index=1
            ),
            SimpleNamespace(
                chunk_id="c3", text="Beta overview.", parent_section_id="s3", order_index=2
            ),
        ]
        self.chunks = SimpleNamespace(result=SimpleNamespace(chunks=chunks), version=4, manifest={})
        self.canonical = SimpleNamespace(payload={"edges": []}, version=5, manifest={})
        self.saved = None

    def load_latest_graph(self, doc_id):
        return self.saved or self.mentions

    def load_graph(self, doc_id, version):
        assert version == self.mentions.version
        return self.mentions

    def load_chunks(self, doc_id, version):
        assert version == self.chunks.version
        return self.chunks

    def load_canonical(self, doc_id, version):
        assert version == self.canonical.version
        return self.canonical

    def find_graph(self, doc_id, source_hash, config_hash):
        if (
            self.saved
            and self.saved.manifest["source_hash"] == source_hash
            and self.saved.manifest["config_hash"] == config_hash
        ):
            return self.saved
        return None

    def save_graph(self, doc_id, source_hash, config_hash, config, payload, **kwargs):
        self.saved = SimpleNamespace(
            payload=payload,
            version=3,
            path=None,
            manifest={
                "source_hash": source_hash,
                "config_hash": config_hash,
                "config": config,
                "upstream_version": kwargs["upstream_version"],
            },
        )
        return self.saved


def test_valid_quote_adds_provenance_and_rebuilds_derivatives():
    store = Store()
    model = Model([{"chunk_id": "c1", "quote": "Alpha is defined as the first concept."}])

    artifact, reused = BuildProvenance(store, model, concurrency=1).execute("doc")

    assert not reused and len(model.calls) == 1
    assert artifact.payload["stage"] == "provenance"
    assert len(artifact.payload["nodes"]) == 2
    alpha = next(node for node in artifact.payload["nodes"] if node["node_id"] == "a")
    assert alpha["defining_chunk_ids_source"] == ["c2"]
    assert alpha["defining_chunk_ids"] == ["c1", "c2"]
    assert alpha["first_order_index"] == 0
    assert artifact.payload["mention_map"]["c1"]["a"]["level"] == "definition"
    assert artifact.payload["citations"] == [
        {
            "source": "b",
            "target": "a",
            "chunk_ids": ["c1"],
            "channels": ["exact"],
            "strength": "hard",
        }
    ]
    assert artifact.payload["stats"]["first_order_changed_node_count"] == 1
    assert artifact.payload["stats"]["chunk_added_count"] == 1
    assert artifact.payload["stats"]["concept_queried_count"] == 1
    assert "node_vectors" not in artifact.payload
    assert artifact.payload["node_vectors_version"] == 1
    assert len(artifact.payload["provenance_decision_log"]) == 1


def test_missing_source_definition_list_accepts_verified_quote():
    store = Store()
    del store.mentions.payload["nodes"][0]["defining_chunk_ids"]
    model = Model([{"chunk_id": "c1", "quote": "Alpha is defined as the first concept."}])

    artifact, _ = BuildProvenance(store, model, concurrency=1).execute("doc")

    alpha = next(node for node in artifact.payload["nodes"] if node["node_id"] == "a")
    assert alpha["defining_chunk_ids_source"] == []
    assert alpha["defining_chunk_ids"] == ["c1"]
    assert artifact.payload["mention_map"]["c1"]["a"]["level"] == "definition"


def test_non_verbatim_quote_is_rejected_without_retry_or_overwrite():
    store = Store()
    model = Model([{"chunk_id": "c1", "quote": "Alpha is the first concept."}])

    artifact, _ = BuildProvenance(store, model, concurrency=1).execute("doc")

    alpha = next(node for node in artifact.payload["nodes"] if node["node_id"] == "a")
    assert len(model.calls) == 1
    assert alpha["defining_chunk_ids"] == alpha["defining_chunk_ids_source"] == ["c2"]
    assert artifact.payload["provenance_log"][0]["status"] == "rejected_quote"
    assert artifact.payload["stats"]["rejected_quote_count"] == 1


def test_empty_selection_preserves_source_provenance():
    store, model = Store(), Model([])

    artifact, _ = BuildProvenance(store, model, concurrency=1).execute("doc")

    assert all(
        set(node["defining_chunk_ids_source"]) <= set(node["defining_chunk_ids"])
        for node in artifact.payload["nodes"]
    )
    assert artifact.payload["stats"]["chunk_added_count"] == 0
    assert artifact.payload["provenance_log"][0]["status"] == "no_selection"


def test_no_definition_signal_means_no_model_call():
    store, model = Store(definition_text="Alpha appears in this discussion."), Model([])

    artifact, _ = BuildProvenance(store, model, concurrency=1).execute("doc")

    assert model.calls == []
    assert artifact.payload["stats"]["concept_queried_count"] == 0
    assert artifact.payload["provenance_log"] == []


def test_unchanged_input_reuses_artifact_without_model_call():
    store = Store()
    model = Model([])
    use_case = BuildProvenance(store, model, concurrency=1)

    first, reused = use_case.execute("doc")
    call_count = len(model.calls)
    second, reused_again = use_case.execute("doc", upstream=store.mentions)

    assert not reused and reused_again and second is first
    assert len(model.calls) == call_count
