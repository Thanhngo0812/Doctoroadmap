from doc2roadmap.application.build_usage import BuildUsage
from doc2roadmap.config import Settings
from doc2roadmap.composition_build import DocumentPipeline, _pipeline_version
import doc2roadmap.composition_build as composition_build_module


def test_build_usage_tracks_only_calls_made_by_this_pipeline():
    usage = BuildUsage()
    usage.add(model_calls=2, input_tokens=30, output_tokens=8, spent_usd=0.001)
    assert usage.snapshot() == {
        "model_calls": 2,
        "input_tokens": 30,
        "output_tokens": 8,
        "spent_usd": 0.001,
        "usage_complete": True,
        "missing_usage_calls": 0,
    }


def test_build_usage_marks_missing_provider_usage_incomplete():
    usage = BuildUsage()
    usage.add(model_calls=1, usage_complete=False)
    assert usage.snapshot()["usage_complete"] is False


def test_metered_session_counts_each_returned_reply_and_merges_parent_stage():
    from doc2roadmap.application import stage_measurements
    from doc2roadmap.application.build_usage import MeteredModel

    usage = BuildUsage()

    class Session:
        def ask_json(self, *args, **kwargs):
            stage_measurements.record_model_call()
            stage_measurements.record_usage({"promptTokenCount": 4, "candidatesTokenCount": 2})
            return {"ok": True}

    class Model:
        model_id = "gemini-3.1-flash-lite"

        def start_session(self, prompt):
            return Session()

    parent = stage_measurements._Measurements("parent")
    token = stage_measurements._current.set(parent)
    try:
        model = MeteredModel(Model(), usage)
        assert model.start_session("system").ask_json("first") == {"ok": True}
        assert model.start_session("system").ask_json("repair") == {"ok": True}
        assert usage.snapshot() == {
            "model_calls": 2,
            "input_tokens": 8,
            "output_tokens": 4,
            "spent_usd": 0.000008,
            "usage_complete": True,
            "missing_usage_calls": 0,
        }
        assert parent.snapshot()["model_calls"] == 2
        assert parent.snapshot()["input_tokens"] == 8
    finally:
        stage_measurements._current.reset(token)


def test_metered_parallel_calls_and_missing_usage_are_counted_without_claiming_complete():
    from concurrent.futures import ThreadPoolExecutor
    from contextvars import copy_context
    from doc2roadmap.application import stage_measurements
    from doc2roadmap.application.build_usage import MeteredModel

    usage = BuildUsage()

    class Session:
        def ask_json(self):
            stage_measurements.record_model_call()
            stage_measurements.record_usage({})
            raise ValueError("response parse failed")

    class Model:
        model_id = "gemini-3.1-flash-lite"

        def start_session(self, prompt):
            return Session()

    model = MeteredModel(Model(), usage)

    def run():
        try:
            model.start_session("").ask_json()
        except ValueError:
            pass

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(copy_context().run, run) for _ in range(2)]
        [future.result() for future in futures]

    assert usage.snapshot() == {
        "model_calls": 2,
        "input_tokens": 0,
        "output_tokens": 0,
        "spent_usd": 0.0,
        "usage_complete": False,
        "missing_usage_calls": 2,
    }


def test_pipeline_passes_vertex_settings_to_generation_and_embedding(monkeypatch, tmp_path):
    import doc2roadmap.composition_build as composition

    received = []

    class Fake:
        def __init__(self, *args, **kwargs):
            received.append(kwargs)
            self.limiter = kwargs.get("limiter")

    monkeypatch.setattr(composition, "JsonArtifactStore", lambda root: object())
    monkeypatch.setattr(composition, "SentencePieceTokenCounter", lambda *args: object())
    monkeypatch.setattr(composition, "IngestDocument", lambda *args, **kwargs: object())
    monkeypatch.setattr(composition, "GeminiEmbedding", Fake)
    monkeypatch.setattr(composition, "GeminiEntityExtractor", Fake)
    settings = Settings(_env_file=None, artifact_dir=tmp_path, llm_transport="vertex",
                        vertex_project="project-test", vertex_location="us-central1")
    pipeline = DocumentPipeline(settings, allow_spend=False)
    pipeline._extractor("model-test")

    assert [(row["transport"], row["vertex_project"], row["vertex_location"])
            for row in received] == [
        ("vertex", "project-test", "us-central1"),
        ("vertex", "project-test", "us-central1"),
    ]


def test_pipeline_version_tracks_algorithm_config_but_excludes_secrets(tmp_path):
    base = Settings(_env_file=None, artifact_dir=tmp_path, gemini_api_key="secret-one")
    same_except_secret = Settings(_env_file=None, artifact_dir=tmp_path, gemini_api_key="secret-two")
    changed_model = Settings(_env_file=None, artifact_dir=tmp_path, gemini_api_key="secret-two",
                             extraction_model_id="different-model")

    assert _pipeline_version(base) == _pipeline_version(same_except_secret)
    assert _pipeline_version(base) != _pipeline_version(changed_model)


def test_a3_returns_both_concurrent_artifact_versions(monkeypatch):
    import types
    from contextvars import ContextVar
    import doc2roadmap.composition_build as composition

    trace = ContextVar("pipeline_test_trace", default="missing")

    class Extract:
        def __init__(self, *args, **kwargs):
            pass

        def execute(self, doc_id):
            assert trace.get() == "caller-context"
            return types.SimpleNamespace(artifact_version=7, reused=False)

    class Index:
        def __init__(self, *args, **kwargs):
            pass

        def execute(self, doc_id):
            assert trace.get() == "caller-context"
            return types.SimpleNamespace(artifact_version=9, reused=True)

    monkeypatch.setattr(composition, "ExtractEntities", Extract)
    monkeypatch.setattr(composition, "IndexDocument", Index)
    monkeypatch.setattr(composition, "SentencePieceTokenCounter", lambda *args: object())
    monkeypatch.setattr(composition, "load_prompts", lambda *args: object())
    pipeline = object.__new__(DocumentPipeline)
    pipeline.settings = Settings(_env_file=None)
    pipeline.store = object()
    pipeline.embedding_guard = object()
    pipeline.usage_meter = BuildUsage()
    pipeline.allow_spend = False
    pipeline._extractor = lambda *args, **kwargs: object()

    token = trace.set("caller-context")
    try:
        assert pipeline.a3("book") == {
            "candidate_version": 7,
            "retrieval_version": 9,
            "a3_reused": False,
            "a3_prime_reused": True,
        }
    finally:
        trace.reset(token)


def test_canonical_coverage_none_does_not_read_gold_fixture(monkeypatch):
    import types
    import doc2roadmap.application.use_cases.canonicalize as canonicalize_module
    import doc2roadmap.application.use_cases.canonical_reasoning as reasoning_module
    import doc2roadmap.application.use_cases.a4_gold as gold_module

    calls = {}

    class Reasoning:
        def __init__(self, *args, **kwargs):
            pass

    class Canonicalize:
        def __init__(self, *args, **kwargs):
            pass

        def execute(self, doc_id, **kwargs):
            calls["execute"] = kwargs
            return types.SimpleNamespace(version=11), False

    monkeypatch.setattr(canonicalize_module, "Canonicalize", Canonicalize)
    monkeypatch.setattr(reasoning_module, "CanonicalReasoning", Reasoning)
    monkeypatch.setattr(gold_module, "load_gold", lambda *args, **kwargs:
                       (_ for _ in ()).throw(AssertionError("gold fixture must not be read")))
    monkeypatch.setattr(composition_build_module, "SentencePieceTokenCounter", lambda *args: object())
    pipeline = object.__new__(DocumentPipeline)
    pipeline.settings = Settings(_env_file=None)
    pipeline.store = object()
    pipeline.embedding = object()
    pipeline.metered_embedding = object()
    pipeline.allow_spend = False
    pipeline.usage_meter = BuildUsage()
    pipeline._extractor = lambda *args, **kwargs: object()

    assert pipeline.canonical("book", "vi") == {
        "canonical_version": 11, "reused": False, "a4_gold_coverage": "none"
    }
    assert calls["execute"] == {"a4_gold_coverage": "none", "gold_sheet_id": None,
                                "declared_language": "vi"}


def test_read_preserves_empty_pages_and_rejects_cached_quality_override(monkeypatch, tmp_path):
    import types
    import pytest
    from doc2roadmap.application.ports.build import BuildRejected

    path = tmp_path / "synthetic.docx"
    path.write_bytes(b"synthetic")
    monkeypatch.setattr(composition_build_module, "DoclingParser", lambda *args: object())
    pipeline = object.__new__(DocumentPipeline)
    pipeline.settings = Settings(_env_file=None)
    pipeline.ingest = types.SimpleNamespace(execute=lambda *args, **kwargs:
        types.SimpleNamespace(chunk_version=3, parse_version=2, chunk_count=2))
    stored = types.SimpleNamespace(manifest={"text_quality": {"warnings": []}},
                                   result=types.SimpleNamespace(chunks=[]))
    pipeline.store = types.SimpleNamespace(
        load_chunks=lambda *args: stored,
        load_parse=lambda *args: types.SimpleNamespace(tree=types.SimpleNamespace(
            parse_stats={"page_count": 3}, nodes=[
                types.SimpleNamespace(page=1, text="first"),
                types.SimpleNamespace(page=3, text="last"),
            ])),
    )

    reading = pipeline.read(path, "book")
    assert reading["page_texts"] == ["first", "", "last"]

    stored.manifest = {"text_quality": {"warnings": ["bad text"]},
                       "text_quality_override_reason": "legacy override"}
    with pytest.raises(BuildRejected, match="bad text") as error:
        pipeline.read(path, "book")
    assert error.value.code == "chu_loi"


def test_learning_prep_pins_parse_and_returns_only_compact_metadata(monkeypatch, tmp_path):
    import types
    import doc2roadmap.composition_build as composition
    import doc2roadmap.application.phase_b.formula_images as formula_module
    import doc2roadmap.infrastructure.media.formula_images as renderer_module

    versions = []

    class Phase:
        def __init__(self, **kwargs):
            self.store = object()

        def a12(self, doc_id, *, graph_version):
            return {"graph_version": graph_version, "retrieval_version": 9,
                    "assignments": {"chunk": {"vector": [0.1] * 768}}}

    class Concepts:
        def __init__(self, *args):
            pass

        def execute(self, doc_id, graph_version, **kwargs):
            return {"graph_version": graph_version, "model_id": "embed-v1", "reused": False,
                    "concept_count": 1, "items": [{"vector": [0.1] * 768}]}

    class FormulaCutter:
        def __init__(self, renderer):
            pass

        def execute(self, path, tree):
            return {"raw_formula_text": "private", "images": {"big": b"image"}}

    monkeypatch.setattr("doc2roadmap.composition_phase_b.PhaseBRuntime", Phase)
    monkeypatch.setattr("doc2roadmap.application.phase_b.concept_index.IndexConcepts", Concepts)
    monkeypatch.setattr(formula_module, "CutFormulaImages", FormulaCutter)
    monkeypatch.setattr(renderer_module, "PdfiumFormulaRenderer", lambda: object())

    def persist(result, root, doc_id, parse_version):
        versions.append(parse_version)
        return {"index_path": str(root / "formula-index.json"), "cut_count": 2,
                "skipped_count": 1, "images": {"big": b"image"}}

    monkeypatch.setattr(formula_module, "persist_formula_images", persist)
    pipeline = object.__new__(DocumentPipeline)
    pipeline.settings = Settings(_env_file=None, artifact_dir=tmp_path)
    pipeline.allow_spend = False
    pipeline.embedding_guard = object()
    pipeline.store = types.SimpleNamespace(
        load_graph=lambda doc, version: types.SimpleNamespace(
            manifest={"config": {"chunks_version": 5}}),
        load_chunks=lambda doc, version: (
            versions.append(version) or types.SimpleNamespace(manifest={"parse_version": 12})
        ),
        load_parse=lambda doc, version: (versions.append(version) or types.SimpleNamespace(tree=object())),
    )

    result = pipeline.learning_prep(tmp_path / "book.pdf", "book", 8)

    assert versions == [5, 12, 12]
    assert result == {
        "a12": {"graph_version": 8, "retrieval_version": 9, "assignment_count": 1},
        "concept_index": {"graph_version": 8, "model_id": "embed-v1", "reused": False,
                           "concept_count": 1},
        "formulas": {"index_path": str(tmp_path / "formula-index.json"),
                     "parse_version": 12, "cut_count": 2, "skipped_count": 1},
    }
