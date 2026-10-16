from doc2roadmap.application.use_cases.canonicalize import Canonicalize
from doc2roadmap.application.use_cases.canonical_reasoning import CanonicalReasoning
from tests.unit.application.test_a4_pipeline import fixture_store, embedding, FakeModel
from tests.unit.application.test_canonical_gop import AnchorModel, DOC, V3_CONFIG_HASH


class CountEmbedding:
    def __init__(self):
        self.delegate, self.requests = embedding(), []
        self.embedding_model_id = self.delegate.embedding_model_id

    def embed(self, requests):
        self.requests.extend(requests)
        return self.delegate.embed(requests)


def test_real_fixture_uses_saved_vectors_without_merging_or_embedding_descriptions(tmp_path):
    class NoMergeModel(AnchorModel):
        def ask_json(self, prompt, *, response_schema):
            import json
            from types import SimpleNamespace
            data = json.loads(prompt.split("\nCorrect this validation error:")[0])
            if "pair_id" in data:
                return SimpleNamespace(payload={"pair_id": data["pair_id"], "relation": "dong_nhat",
                                                 "reason": "fixture verification"}, usage=self.usage)
            return super().ask_json(prompt, response_schema=response_schema)
    store, model, embed = fixture_store(tmp_path), NoMergeModel(), CountEmbedding()
    source = store.load_latest_candidates(DOC)
    payload = source.payload
    payload["candidate_embeddings"] = {entity["candidate_id"]: [1., .01]
                                        for entity in payload["entities"] if not entity.get("media_id")}
    store._write(source.path / "candidates.json", payload)
    uc = Canonicalize(store, embed, reasoning=CanonicalReasoning(model, model),
                      upstream_chain="gop", anchor_batch_mode="single")
    artifact, _ = uc.execute(DOC)
    baseline, _ = Canonicalize(store).execute(DOC)
    assert len(artifact.payload["nodes"]) == len(baseline.payload["nodes"])
    assert len(embed.requests) == len({entity["name"] for entity in payload["entities"] if not entity.get("media_id")})
    rows = [row for row in artifact.payload["decision_log"] if row.get("stage") == "nomination_pair"]
    assert rows and any("description_similarity" in row["sources"] for row in rows)
    assert all(row["verdict"] == "different" for row in rows)
    for source_name, count in artifact.payload["stats"]["nomination_channels"].items():
        assert count == sum(source_name in row["sources"] for row in rows)
    assert artifact.payload["stats"]["nomination_edges"] == len(rows)
    assert artifact.payload["stats"]["cut_edge_count"] == len(artifact.payload["nominations"]["cut_edges"])
    assert "same set of objects" in artifact.manifest["config"]["reasoning"]["prompts"]["merge"]


def test_special_case_stays_separate_and_has_open_proposed_relation(tmp_path):
    class SubtypeModel(AnchorModel):
        def ask_json(self, prompt, *, response_schema):
            reply = super().ask_json(prompt, response_schema=response_schema)
            value = reply.payload
            if "relations" in value and len(value["nodes"]) >= 2:
                import json
                data = json.loads(prompt.split("\nCorrect this validation error:")[0])
                left, right = data["groups"][:2]
                value["relations"] = [{"source": left["group_id"], "target": right["group_id"],
                    "edge_type": "subtype_of", "chunk_ids": [left["evidence"][0]["chunk_id"]],
                    "reason": "trường hợp riêng"}]
            return reply

    store, model = fixture_store(tmp_path), SubtypeModel()
    result, _ = Canonicalize(store, embedding(), reasoning=CanonicalReasoning(model, model),
                            upstream_chain="gop", anchor_batch_mode="single").execute(DOC)
    edges = [edge for edge in result.payload["edges"] if "2a" in edge["origins"]]
    assert edges and all(edge["source"] != edge["target"] and edge["proposal"] for edge in edges)
    assert any(edge["edge_type"] == "subtype_of" for edge in edges)


def test_nomination_threshold_changes_gop_cache_and_missing_vectors_are_skipped(tmp_path):
    store, model = fixture_store(tmp_path), AnchorModel()
    source = store.load_latest_candidates(DOC)
    source.payload["candidate_embeddings"] = {}
    store._write(source.path / "candidates.json", source.payload)
    def run(threshold):
        return Canonicalize(store, embedding(), reasoning=CanonicalReasoning(model, model),
                            upstream_chain="gop", anchor_batch_mode="single",
                            nomination_config={"semantic_min_similarity": threshold}).execute(DOC)
    first, _ = run(.85)
    second, _ = run(.9)
    again, reused = run(.85)
    assert first.manifest["config_hash"] != second.manifest["config_hash"]
    assert reused and again.version == first.version
    assert first.payload["stats"]["nomination_channels"]["description_similarity"] == 0


def test_reusing_reasoning_between_chains_cannot_contaminate_v3_prompt_or_cache(tmp_path):
    store, model = fixture_store(tmp_path), FakeModel()
    reasoning = CanonicalReasoning(model, model)
    before = reasoning.config()
    v3, _ = Canonicalize(store, embedding(), reasoning=reasoning).execute(DOC)
    Canonicalize(store, embedding(), reasoning=reasoning, upstream_chain="gop",
                 anchor_batch_mode="single").execute(DOC)
    assert reasoning.config() == before
    calls = len(model.calls)
    again, reused = Canonicalize(store, embedding(), reasoning=reasoning).execute(DOC)
    assert reused and again.version == v3.version
    assert again.manifest["config_hash"] == V3_CONFIG_HASH and len(model.calls) == calls
