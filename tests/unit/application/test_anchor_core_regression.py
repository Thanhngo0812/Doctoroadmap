"""Frozen v3 teaching replay on the real baocao-canhan document fixture."""
import json
from pathlib import Path
from types import SimpleNamespace

from doc2roadmap.application.use_cases.anchor_concepts import AnchorConcepts
from doc2roadmap.application.use_cases.canonical_reasoning import CanonicalReasoning
from doc2roadmap.application.use_cases.canonicalize import Canonicalize
from doc2roadmap.domain.canonical import digest
from tests.unit.application.test_a4_pipeline import FakeModel, embedding, fixture_store


FIXTURE = Path("tests/fixtures/anchors/baocao-canhan-v3.json")


def real_upstream(tmp_path):
    store = fixture_store(tmp_path)
    model = FakeModel()
    canonical, _ = Canonicalize(
        store, embedding(), reasoning=CanonicalReasoning(model, model)
    ).execute("baocao-canhan")
    config = {"chunks_version": store.load_latest_candidates("baocao-canhan").manifest["upstream_version"],
              "canonical_version": canonical.version}
    upstream = SimpleNamespace(
        payload={**canonical.payload, "stage": "provenance", "mention_map": {}},
        version=canonical.version,
        manifest={"config": config, "config_hash": digest(config)},
    )
    return store, upstream


class ReplayAnchors:
    model_id = "fixture-model"

    def __init__(self, recorded):
        self.recorded, self.calls = recorded, []

    def start_session(self, system_prompt):
        assert digest(system_prompt) == self.recorded["system_prompt_hash"]
        return self

    def ask_json(self, prompt, *, response_schema):
        assert digest(response_schema) == self.recorded["schema_hash"]
        data = json.loads(prompt)
        row = self.recorded["replies"][data["node_id"]]
        assert digest(data) == row["input_hash"]
        self.calls.append(data["node_id"])
        return SimpleNamespace(payload=row["output"], usage=row["usage"])


def test_real_document_teaching_payload_and_cache_key_match_before_extraction(tmp_path):
    recorded = json.loads(FIXTURE.read_text(encoding="utf-8"))
    store, upstream = real_upstream(tmp_path)
    model = ReplayAnchors(recorded)
    artifact, reused = AnchorConcepts(store, model).execute("baocao-canhan", upstream=upstream)
    assert not reused and len(model.calls) == len(recorded["replies"])
    assert digest(artifact.payload) == recorded["teaching_payload_hash"]
    assert artifact.manifest["config_hash"] == recorded["teaching_config_hash"]
    checkpoints = {path.stem: digest({key: value for key, value in json.loads(path.read_text(encoding="utf-8")).items()
                                     if key != "stage_measurements"})
                   for path in tmp_path.rglob("anchor-*.json")}
    assert checkpoints == recorded["checkpoint_payload_hashes"]

    # Reload the artifact from disk; checkpoints cannot hide a cache-key change.
    model = ReplayAnchors(recorded)
    cached, reused = AnchorConcepts(store, model).execute("baocao-canhan", upstream=upstream)
    assert reused and cached.version == artifact.version
    assert model.calls == []
