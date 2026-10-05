from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context

import pytest

from doc2roadmap.application.stage_measurements import measure_stage, record_model_call, record_usage, resume_measurements
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore


def test_full_execute_time_resume_counts_and_cache(tmp_path, monkeypatch):
    import doc2roadmap.application.stage_measurements as measurements
    clock = [0.0]
    monkeypatch.setattr(measurements, "perf_counter", lambda: clock[0])
    store = JsonArtifactStore(tmp_path)

    class Stage:
        @measure_stage
        def execute(self, fail=False):
            cached = store.find_graph("book", "source", "config")
            if cached:
                return cached
            resume_measurements(store.load_checkpoint("book", "test"))
            with ThreadPoolExecutor(2) as pool:
                def call():
                    record_model_call()
                    record_usage({"promptTokenCount": 5, "candidatesTokenCount": 2, "thoughtsTokenCount": 1})
                list(pool.map(lambda ctx: ctx.run(call), [copy_context(), copy_context()]))
            clock[0] += 4
            store.save_checkpoint("book", "test", {"source_hash": "source"})
            if fail:
                raise RuntimeError("interrupted")
            artifact = store.save_graph("book", "source", "config", {}, {"nodes": []}, upstream_version=1)
            clock[0] += 2  # rendering/other work AFTER save belongs to execute too
            return artifact

    with pytest.raises(RuntimeError):
        Stage().execute(fail=True)
    clock[0] += 1000  # approval/offline wait must NOT count
    artifact = Stage().execute()
    stats = artifact.manifest["stats"]
    assert stats["runtime_seconds"] == 10
    assert (stats["model_calls"], stats["input_tokens"], stats["output_tokens"]) == (4, 20, 12)
    assert store.load_graph("book", artifact.version).manifest["stats"] == stats
    assert artifact.manifest["config_hash"] == "config"
    assert artifact.manifest["config"] == {}
    assert artifact.payload == {"nodes": []}  # measurements cannot invalidate upstream payload hashes
    old_bytes = (artifact.path / "manifest.json").read_bytes()
    clock[0] += 1000
    assert Stage().execute().version == artifact.version
    assert (artifact.path / "manifest.json").read_bytes() == old_bytes


def test_non_model_stage_records_zero_counts(tmp_path):
    store = JsonArtifactStore(tmp_path)
    @measure_stage
    def execute():
        return store.save_graph("book", "s", "c", {}, {}, upstream_version=1)
    stats = execute().manifest["stats"]
    assert stats["runtime_seconds"] >= 0
    assert [stats[key] for key in ("model_calls", "input_tokens", "output_tokens")] == [0, 0, 0]


def test_every_artifact_stage_execute_is_measured():
    import ast
    from pathlib import Path
    stages = ("ingest_document index_document label_chunk_roles extract_entities canonicalize "
              "build_clusters find_implicit verify_relations anchor_concepts judge_identity "
              "build_mentions build_provenance build_main_edges build_secondary_edges "
              "validate_graph name_concept_labels build_roadmap check_teaching name_modules").split()
    for stage in stages:
        tree = ast.parse((Path("src/doc2roadmap/application/use_cases") / (stage + ".py")).read_text(encoding="utf-8-sig"))
        execute = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "execute")
        assert any(isinstance(node, ast.Name) and node.id == "measure_stage" for node in execute.decorator_list), stage
        calls = [node.func for node in ast.walk(tree) if isinstance(node, ast.Call)]
        if any(isinstance(node, ast.Attribute) and node.attr == "load_checkpoint" for node in calls):
            assert any(isinstance(node, ast.Name) and node.id == "resume_measurements" for node in calls), stage


def test_legacy_checkpoint_marks_missing_history(tmp_path):
    store = JsonArtifactStore(tmp_path)
    store.save_checkpoint("book", "old", {"source_hash": "s"})
    @measure_stage
    def execute():
        resume_measurements(store.load_checkpoint("book", "old"))
        return store.save_graph("book", "s", "c", {}, {}, upstream_version=1)
    assert execute().manifest["stats"]["measurement_history_complete"] is False


def test_auxiliary_checkpoint_uses_latest_total_without_double_counting(tmp_path, monkeypatch):
    import doc2roadmap.application.stage_measurements as measurements
    clock = [0.0]
    monkeypatch.setattr(measurements, "perf_counter", lambda: clock[0])
    store = JsonArtifactStore(tmp_path)
    @measure_stage
    def execute(fail=False):
        resume_measurements(store.load_checkpoint("book", "main"))
        resume_measurements(store.load_checkpoint("book", "aux"))
        record_model_call()
        clock[0] += 2
        store.save_checkpoint("book", "main", {})
        clock[0] += 1
        store.save_checkpoint("book", "aux", {})
        resume_measurements(store.load_checkpoint("book", "aux"))  # own snapshot must not become previous-run time/counts
        if fail:
            raise RuntimeError("interrupted")
        return store.save_graph("book", "s", "c", {}, {}, upstream_version=1)
    with pytest.raises(RuntimeError):
        execute(fail=True)
    clock[0] += 100
    stats = execute().manifest["stats"]
    assert stats["runtime_seconds"] == 6
    assert stats["model_calls"] == 2


def test_rejected_checkpoint_does_not_restore_time_or_counts(tmp_path, monkeypatch):
    import doc2roadmap.application.stage_measurements as measurements
    clock = [0.0]
    monkeypatch.setattr(measurements, "perf_counter", lambda: clock[0])
    store = JsonArtifactStore(tmp_path)
    @measure_stage
    def execute(source, fail=False):
        checkpoint = store.load_checkpoint("book", "same-config")
        if checkpoint and checkpoint.get("source_hash") == source:
            resume_measurements(checkpoint)
        clock[0] += 2
        record_model_call()
        store.save_checkpoint("book", "same-config", {"source_hash": source})
        if fail:
            raise RuntimeError("interrupted")
        return store.save_graph("book", source, "c", {}, {}, upstream_version=1)
    with pytest.raises(RuntimeError):
        execute("old-source", fail=True)
    clock[0] += 100
    stats = execute("new-source").manifest["stats"]
    assert stats["runtime_seconds"] == 2
    assert stats["model_calls"] == 1


def test_cached_legacy_artifact_is_never_rewritten(tmp_path):
    store = JsonArtifactStore(tmp_path)
    original = store.save_graph("book", "s", "c", {}, {}, upstream_version=1)
    before = (original.path / "manifest.json").read_bytes()
    @measure_stage
    def execute():
        return store.find_graph("book", "s", "c")
    assert execute().version == original.version
    assert (original.path / "manifest.json").read_bytes() == before
    assert "stats" not in store.load_graph("book", original.version).manifest


def test_exception_flushes_timing_without_advancing_semantic_checkpoint(tmp_path, monkeypatch):
    import doc2roadmap.application.stage_measurements as measurements
    clock = [0.0]
    monkeypatch.setattr(measurements, "perf_counter", lambda: clock[0])
    store = JsonArtifactStore(tmp_path)
    @measure_stage
    def execute():
        clock[0] += 2
        record_model_call()
        store.save_checkpoint("book", "run", {"completed": ["a"]})
        clock[0] += 3
        record_model_call()  # unfinished next batch still spent time / submitted a request
        raise RuntimeError("interrupted")
    with pytest.raises(RuntimeError):
        execute()
    checkpoint = store.load_checkpoint("book", "run")
    assert checkpoint["completed"] == ["a"]
    assert checkpoint["stage_measurements"]["runtime_seconds"] == 5
    assert checkpoint["stage_measurements"]["model_calls"] == 2
