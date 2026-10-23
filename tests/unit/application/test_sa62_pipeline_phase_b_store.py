"""SA-62: the build pipeline and PhaseBRuntime accept an injected Phase B store.

Every model and embedding here is fake. Spies replace the JSON store constructor in the
original module and in the names imported by both composition modules, so a stray
`JsonPhaseBStore(...)` anywhere on the injected path raises.
"""
import json
from datetime import datetime, timezone
from types import SimpleNamespace as NS

import pytest

import doc2roadmap.composition_build as composition_build
import doc2roadmap.composition_phase_b as composition_phase_b
import doc2roadmap.infrastructure.artifacts.phase_b_store as phase_b_store_module
from doc2roadmap.application import stage_measurements
from doc2roadmap.application.build_usage import MeteredEmbedding
from doc2roadmap.application.spend_guard import SpendGuard
from doc2roadmap.config import Settings
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore
from tests.unit.application.test_phase_b_naming import Store, upstream, valid_outputs


class NamingSession:
    """One fake provider reply per call; the call is recorded the way real adapters record it."""

    def __init__(self, model):
        self.model = model

    def ask_json(self, prompt, *, response_schema):
        stage_measurements.record_model_call()
        stage_measurements.record_usage({"promptTokenCount": 10, "candidatesTokenCount": 5})
        self.model.calls += 1
        return NS(payload=next(self.model.outputs), usage={"input_tokens": 10, "output_tokens": 5}, raw_text="")


class FakeNamingModel:
    model_id = "gemini-3.1-flash-lite"

    def __init__(self, outputs):
        self.outputs, self.calls = iter(outputs), 0

    def start_session(self, prompt):
        return NamingSession(self)


class FakeEmbedding:
    embedding_model_id = "fake-embed-768"

    def __init__(self):
        self.calls = 0

    def embed(self, requests):
        stage_measurements.record_model_call(embedding=True)
        stage_measurements.record_usage({"promptTokenCount": len(requests)}, embedding=True)
        self.calls += 1
        return [[1.0] + [0.0] * 767 for _ in requests]


class GraphStore(Store):
    def load_graph(self, *_):
        return NS(version=1, payload={"nodes": [
            {"node_id": "n0a", "name": "Ma trận", "description": "Bảng số", "learnable": True},
            {"node_id": "n1a", "name": "Định thức", "description": "Số gắn với ma trận", "learnable": True}]})


def forbid_json_store(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("JsonPhaseBStore must not be built")
    for module in (phase_b_store_module, composition_build, composition_phase_b):
        monkeypatch.setattr(module, "JsonPhaseBStore", forbidden)


def settings_for(tmp_path):
    return Settings(_env_file=None, artifact_dir=tmp_path / "artifacts", llm_transport="vertex",
                    vertex_project="offline", secondary_mode="llm")


def patch_a12_inputs(monkeypatch):
    class Artifacts:
        def __init__(self, *_):
            pass

        def load_latest_retrieval(self, doc_id):
            return NS(version=3, payload={})

    monkeypatch.setattr(composition_phase_b, "JsonArtifactStore", Artifacts)
    monkeypatch.setattr(composition_phase_b, "load_learning_graph", lambda *a, **k: NS(
        modules=[1], chunks={}, graph_version=8, payload={"modules": []}))
    monkeypatch.setattr(composition_phase_b, "assert_retrieval_compatible", lambda *a: "fingerprint")
    monkeypatch.setattr(composition_phase_b, "build_module_assignments",
                        lambda *a: {"assignments": {"c0": {"module_id": "m0"}}})


def make_pipeline(tmp_path, monkeypatch, **kwargs):
    pipeline = composition_build.DocumentPipeline(settings_for(tmp_path), allow_spend=True, **kwargs)
    model = FakeNamingModel(valid_outputs())
    embedding = FakeEmbedding()
    pipeline._extractor = lambda model_id, **kw: model
    pipeline.store = GraphStore()
    pipeline.metered_embedding = MeteredEmbedding(embedding, pipeline.usage_meter)
    pipeline.embedding_guard = SpendGuard(pipeline.metered_embedding, allowed=True)
    return pipeline, model, embedding


def run_titles(pipeline, monkeypatch):
    """Run `roadmap()` far enough to get the real NameModulesB the pipeline built."""
    captured = {}

    class Runner:
        def __init__(self, *stages):
            captured["titles"] = stages[6]

        def execute(self, doc_id):
            return NS(version=1), False

    monkeypatch.setattr("doc2roadmap.application.use_cases.BuildLearningGraph", Runner)
    pipeline.roadmap("book")
    return captured["titles"].execute("book", upstream=upstream())


def spy_runtimes(monkeypatch):
    runtimes = []

    class Spy(composition_phase_b.PhaseBRuntime):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            runtimes.append(self)

    monkeypatch.setattr(composition_phase_b, "PhaseBRuntime", Spy)
    return runtimes


def test_spy_is_live_on_the_default_path(tmp_path, monkeypatch):
    """Without injection the JSON store is built; the spy must fire in both composition paths."""
    forbid_json_store(monkeypatch)
    patch_a12_inputs(monkeypatch)
    pipeline, *_ = make_pipeline(tmp_path, monkeypatch)
    with pytest.raises(AssertionError, match="JsonPhaseBStore must not be built"):
        run_titles(pipeline, monkeypatch)
    with pytest.raises(AssertionError, match="JsonPhaseBStore must not be built"):
        pipeline.learning_prep(tmp_path / "book.docx", "book", 8)


def test_injected_store_builds_no_json_store_and_receives_every_write(tmp_path, monkeypatch):
    forbid_json_store(monkeypatch)
    patch_a12_inputs(monkeypatch)
    runtimes = spy_runtimes(monkeypatch)
    injected = InMemoryPhaseBStore()
    pipeline, model, embedding = make_pipeline(tmp_path, monkeypatch, phase_b_store=injected)

    titles, _ = run_titles(pipeline, monkeypatch)
    result = pipeline.learning_prep(tmp_path / "book.docx", "book", 8)

    assert [m["title"] for m in titles.payload["modules"]] == ["Ma trận", "Định thức", "Hệ phương trình"]
    # module-title cache and concept-index cache live in the injected store
    cache_keys = list(injected._cache)
    assert sum(key.startswith("concept-index:book:") for key in cache_keys) == 1
    assert len(cache_keys) == 3 + 1
    # A12 wrote its assignment record to the injected store
    assignments = injected.list_records("module_assignment")
    assert len(assignments) == 1 and assignments[0]["doc_id"] == "book" and assignments[0]["graph_version"] == 8
    assert result["a12"]["assignment_count"] == 1
    # the child runtime's DailySpendGuard reads the usage rows of the injected store
    runtime = runtimes[0]
    now = datetime.now(timezone.utc).isoformat()
    cap = runtime.b_settings.system_daily_max_usd
    assert runtime.spend_guard.check("lecture", cap - 0.5) is True
    injected.append_usage({"purpose": "lecture", "cost_usd": 1.0, "created_at": now})
    assert runtime.spend_guard.check("lecture", cap - 0.5) is False
    assert not (tmp_path / "artifacts" / "phase_b").exists()


def test_default_store_is_unchanged_live_json_under_artifact_dir(tmp_path, monkeypatch):
    patch_a12_inputs(monkeypatch)
    pipeline, *_ = make_pipeline(tmp_path, monkeypatch)
    path = tmp_path / "artifacts" / "phase_b" / "live.json"
    assert not path.exists()

    run_titles(pipeline, monkeypatch)
    after_titles = json.loads(path.read_text(encoding="utf-8"))
    assert sum(row["purpose"] == "module_title" for row in after_titles["usage"]) == 3

    pipeline.learning_prep(tmp_path / "book.docx", "book", 8)
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert list(saved["records"]["module_assignment"].values())[0]["doc_id"] == "book"
    assert any(key.startswith("concept-index:book:") for key in saved["cache"])
    # the wrapper applies to the default store too
    assert saved["usage"] and all(row["counted_in"] == "build" for row in saved["usage"])


def test_one_spend_source_meter_counts_each_call_once_and_every_phase_b_row_is_flagged(tmp_path, monkeypatch):
    patch_a12_inputs(monkeypatch)
    injected = InMemoryPhaseBStore()
    pipeline, model, embedding = make_pipeline(tmp_path, monkeypatch, phase_b_store=injected)

    run_titles(pipeline, monkeypatch)
    pipeline.learning_prep(tmp_path / "book.docx", "book", 8)

    assert model.calls == 3 and embedding.calls >= 1
    # the meter is the build's spend source: exactly one count per provider call
    assert pipeline.usage()["model_calls"] == model.calls + embedding.calls
    rows = injected.usage_rows()
    assert sorted({row["purpose"] for row in rows}) == ["embedding", "module_title"]
    assert len(rows) == model.calls + 1
    assert all(row.get("counted_in") == "build" for row in rows)
    unflagged = [row for row in rows if row.get("counted_in") != "build"]
    assert sum(row.get("cost_usd", 0) for row in unflagged) == 0


def test_trace_wrapper_flags_a_copy_and_passes_everything_else_through():
    from doc2roadmap.composition_build import BuildTracePhaseBStore

    inner = InMemoryPhaseBStore()
    wrapped = BuildTracePhaseBStore(inner)
    row = {"purpose": "module_title", "cost_usd": 0.5}
    wrapped.append_usage(row)
    assert row == {"purpose": "module_title", "cost_usd": 0.5}
    stored = inner.usage_rows()
    assert len(stored) == 1 and stored[0]["counted_in"] == "build"
    assert stored[0]["purpose"] == "module_title" and stored[0]["cost_usd"] == 0.5
    assert wrapped.usage_rows() == inner.usage_rows()
    wrapped.put_cache("k", {"v": 1})
    wrapped.put_record("kind", "id", {"x": 1})
    assert inner.get_cache("k") == {"v": 1} and wrapped.get_record("kind", "id") == {"x": 1}
    with wrapped.atomic():
        pass
    assert wrapped.single_flight("flight", lambda: 7) == 7 and inner.get_cache("flight") == 7


def test_runtime_with_store_builds_no_json_and_does_not_flag_its_own_usage(tmp_path, monkeypatch):
    forbid_json_store(monkeypatch)
    injected = InMemoryPhaseBStore()
    runtime = composition_phase_b.PhaseBRuntime(settings=settings_for(tmp_path), allow_spend=True,
                                                mode="gemini", store=injected)
    assert runtime.store is injected and runtime.spend_guard.store is injected
    assert not (tmp_path / "artifacts" / "phase_b").exists()

    # a real naming call by the learner-facing runtime is the learner's own spend: no build flag
    runtime._models["module_title"] = FakeNamingModel(valid_outputs())
    runtime.graph = lambda *a, **k: NS(graph_version=1)
    runtime.artifacts = GraphStore()
    runtime.artifacts.load_graph = lambda *a: upstream()
    runtime.naming("book")
    rows = injected.usage_rows()
    assert [row["purpose"] for row in rows] == ["module_title"] * 3
    assert all("counted_in" not in row for row in rows)
    assert runtime.usage()["purposes"]["module_title"]["calls"] == 3


def test_runtime_rejects_store_together_with_store_path(tmp_path, monkeypatch):
    forbid_json_store(monkeypatch)
    with pytest.raises(ValueError):
        composition_phase_b.PhaseBRuntime(settings=settings_for(tmp_path), mode="offline",
                                          store=InMemoryPhaseBStore(), store_path=tmp_path / "x.json")
    assert not (tmp_path / "artifacts" / "phase_b").exists()
