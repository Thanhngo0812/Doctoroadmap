import pytest

from doc2roadmap.application.use_cases.canonical_reasoning import CanonicalReasoning
from doc2roadmap.application.use_cases.canonicalize import Canonicalize
from doc2roadmap.config import Settings
from tests.unit.application.test_a4_pipeline import fixture_store
from tests.unit.application.test_canonical_gop import AnchorModel, DOC
from tests.unit.application.test_canonical_gop_nominations import CountEmbedding


def vector_fixture(tmp_path):
    store = fixture_store(tmp_path)
    source = store.load_latest_candidates(DOC)
    source.payload["candidate_embeddings"] = {
        entity["candidate_id"]: [1., .01] for entity in source.payload["entities"] if not entity.get("media_id")}
    store._write(source.path / "candidates.json", source.payload)
    return store


def description_pairs(artifact):
    return {(edge["source"], edge["target"]) for edge in artifact.payload["nominations"]["edges"]
            if "description_similarity" in edge["channels"]}


def run(store, model, embed, **config):
    return Canonicalize(store, embed, reasoning=CanonicalReasoning(model, model),
                        upstream_chain="gop", anchor_batch_mode="single", nomination_config=config).execute(DOC)


def test_default_skips_description_pairs_and_toggle_changes_cache(tmp_path):
    store, model, embed = vector_fixture(tmp_path), AnchorModel(), CountEmbedding()
    off, _ = run(store, model, embed)
    assert not description_pairs(off)
    assert off.payload["stats"]["nomination_channels"].get("description_similarity", 0) == 0
    assert not any("description_similarity" in row["sources"] for row in off.payload["decision_log"]
                   if row.get("stage") == "nomination_pair")
    assert off.manifest["config"]["additional_nominations"]["semantic_enabled"] is False
    assert off.payload["stats"]["nomination_edges"] > 0
    assert off.payload["stats"]["nomination_channels"].get("same_evidence", 0) == 0

    on, _ = run(store, model, embed, semantic_enabled=True)
    assert description_pairs(on)
    assert on.payload["stats"]["nomination_channels"]["description_similarity"] == len(description_pairs(on))
    assert on.manifest["config"]["additional_nominations"]["semantic_enabled"] is True
    assert on.manifest["config_hash"] != off.manifest["config_hash"]
    calls = len(model.calls), len(model.anchor_calls), len(embed.requests)
    for config, expected in [({}, off), ({"semantic_enabled": True}, on)]:
        again, reused = run(store, model, embed, **config)
        assert reused and again.version == expected.version
    assert calls == (len(model.calls), len(model.anchor_calls), len(embed.requests))


@pytest.mark.parametrize("operation", ["execute", "plan"])
def test_disabled_source_never_reads_stored_vectors(tmp_path, monkeypatch, operation):
    store = vector_fixture(tmp_path)
    load = store.load_latest_candidates

    class GuardedPayload(dict):
        def get(self, key, *args):
            assert key != "candidate_embeddings", "disabled source read A3 description vectors"
            return super().get(key, *args)

    def guarded_load(doc_id):
        source = load(doc_id)
        source.payload = GuardedPayload(source.payload)
        return source

    monkeypatch.setattr(store, "load_latest_candidates", guarded_load)
    model, embed = AnchorModel(), CountEmbedding()
    use_case = Canonicalize(store, embed, reasoning=CanonicalReasoning(model, model),
                           upstream_chain="gop", anchor_batch_mode="single")
    result = getattr(use_case, operation)(DOC)
    if operation == "execute":
        assert not description_pairs(result[0])
    else:
        assert "merge" in result and not model.calls and not embed.requests


@pytest.mark.parametrize("enabled", [False, True])
def test_environment_switch_reaches_composed_canonical(tmp_path, monkeypatch, enabled):
    from doc2roadmap.composition import build_canonical

    monkeypatch.delenv("DOC2ROADMAP_MERGE_DESCRIPTION_ENABLED", raising=False)
    if enabled:
        monkeypatch.setenv("DOC2ROADMAP_MERGE_DESCRIPTION_ENABLED", "true")
    settings = Settings(_env_file=None, merge_description_top_k=1, merge_description_min_similarity=.93)
    assert settings.merge_description_enabled is enabled
    store, model, embed = vector_fixture(tmp_path), AnchorModel(), CountEmbedding()
    embed.limiter = None
    monkeypatch.setattr("doc2roadmap.composition._a3_dependencies", lambda: (settings, store, embed))
    monkeypatch.setattr("doc2roadmap.composition.GeminiEntityExtractor", lambda *args, **kwargs: model)
    monkeypatch.setattr("doc2roadmap.composition.SentencePieceTokenCounter", lambda *args: None)
    use_case = build_canonical(upstream_chain="gop", anchor_batch_mode="single", allow_spend=True)
    artifact, _ = use_case.execute(DOC)
    assert bool(description_pairs(artifact)) is enabled
    assert artifact.manifest["config"]["additional_nominations"]["semantic_enabled"] is enabled
    assert use_case.nomination_config["semantic_top_k"] == 1
    assert use_case.nomination_config["semantic_min_similarity"] == .93


@pytest.mark.parametrize("value", [None, "false", 0])
def test_description_switch_rejects_non_boolean_config(tmp_path, value):
    model = AnchorModel()
    with pytest.raises(ValueError, match="đề cử mô tả"):
        Canonicalize(fixture_store(tmp_path), CountEmbedding(), reasoning=CanonicalReasoning(model, model),
                     upstream_chain="gop", nomination_config={"semantic_enabled": value})
