import pytest

from doc2roadmap.application.use_cases.canonical_reasoning import CanonicalReasoning
from doc2roadmap.application.use_cases.canonicalize import Canonicalize
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


@pytest.mark.parametrize("operation", ["execute", "plan"])
def test_canonical_never_reads_retired_description_vectors(tmp_path, monkeypatch, operation):
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
    use_case = Canonicalize(store, embed, reasoning=CanonicalReasoning(model, model))
    result = getattr(use_case, operation)(DOC)
    if operation == "execute":
        assert not description_pairs(result[0])
    else:
        assert "merge" in result and not model.calls and not embed.requests
