import csv
from types import SimpleNamespace

import pytest

from doc2roadmap.config import Settings
from doc2roadmap.presentation.cli.main import main
from doc2roadmap.application.use_cases.export_secondary_features import ExportSecondaryFeatures
from tests.unit.application.test_build_secondary_ml_edges import Scorer, Tokenize, fixture


def test_export_cli_writes_82_features_and_leaves_missing_cells_empty(tmp_path, monkeypatch, capsys):
    store = fixture()
    store.main.manifest["config"]["chunks_version"] = 1
    store.load_chunks = lambda *args: store.chunks
    store.main.payload["nodes"][0]["defining_chunk_ids"] = []
    monkeypatch.setattr("doc2roadmap.presentation.cli.main.build_artifact_store", lambda: store)
    result = main(["a8-secondary-features", "--doc-id", "doc", "--main-version", "3",
                   "--output-dir", str(tmp_path)])
    assert result == 0
    with (tmp_path / "doc.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["ord_x"] == ""
    assert len(rows[0]) == 7 + 82
    assert '"calls": 0' in capsys.readouterr().out
    store.main.payload["secondary_complete"] = True
    with pytest.raises(ValueError, match="không dùng artifact pass phụ"):
        ExportSecondaryFeatures(store, Tokenize()).execute("doc", main_version=3, output_dir=tmp_path)


def test_configuration_default_validation_and_ml_composition_without_allow_spend(monkeypatch, tmp_path):
    monkeypatch.delenv("DOC2ROADMAP_SECONDARY_MODE", raising=False)
    assert Settings(_env_file=None).secondary_mode == "ml"
    with pytest.raises(ValueError):
        Settings(_env_file=None, secondary_mode="unknown")
    from doc2roadmap import composition
    from doc2roadmap.application.use_cases.build_secondary_ml_edges import BuildSecondaryMLEdges
    from doc2roadmap.application.use_cases.build_secondary_edges import BuildSecondaryEdges

    settings = Settings(_env_file=None, artifact_dir=tmp_path, gemini_api_key="fake")
    embedding = SimpleNamespace(limiter=None)
    monkeypatch.setattr(composition, "_a3_dependencies", lambda: (settings, fixture(), embedding))
    monkeypatch.setattr("doc2roadmap.infrastructure.secondary_model.LightGBMSecondaryScorer", Scorer)
    monkeypatch.setattr("doc2roadmap.infrastructure.secondary_tokenizer.VietnameseWordTokenizer", Tokenize)
    pipeline, _ = composition.build_learning_graph(allow_spend=False)
    assert isinstance(pipeline.secondary_edges, BuildSecondaryMLEdges)
    assert pipeline.secondary_edges.plan("doc").calls_estimate == 0
    artifact, _ = pipeline.secondary_edges.execute("doc")
    assert len(artifact.payload["secondary_edges"]) == 1
    monkeypatch.setenv("DOC2ROADMAP_SECONDARY_MODE", "llm")
    settings = Settings(_env_file=None, artifact_dir=tmp_path, gemini_api_key="fake")
    pipeline, _ = composition.build_learning_graph(allow_spend=False)
    assert type(pipeline.secondary_edges) is BuildSecondaryEdges


def test_roadmap_cli_without_mode_option_runs_ml_and_produces_ml_artifact(monkeypatch, tmp_path, capsys):
    from doc2roadmap import composition

    monkeypatch.delenv("DOC2ROADMAP_SECONDARY_MODE", raising=False)
    settings = Settings(_env_file=None, artifact_dir=tmp_path, gemini_api_key="fake")
    store, scorer = fixture(), Scorer()
    monkeypatch.setattr(composition, "_a3_dependencies", lambda: (settings, store, SimpleNamespace(limiter=None)))
    monkeypatch.setattr("doc2roadmap.infrastructure.secondary_model.LightGBMSecondaryScorer", lambda: scorer)
    monkeypatch.setattr("doc2roadmap.infrastructure.secondary_tokenizer.VietnameseWordTokenizer", Tokenize)
    calls = []

    class CachedStage:
        def __init__(self, name):
            self.name = name

        def execute(self, doc_id, *, upstream=None):
            assert doc_id == "doc"
            calls.append(self.name)
            if self.name == "clusters":
                return store.main, True
            assert upstream is not None
            if self.name == "validated":
                assert upstream.manifest["config"]["algorithm_id"] == "a8-secondary-ml-v1"
                assert len(upstream.payload["secondary_edges"]) == 1
            return upstream, True

    def build(**kwargs):
        assert kwargs == {"allow_spend": False, "identity_review": None}
        pipeline, configured = composition.build_learning_graph(**kwargs)
        # Only unrelated stages stand in for cache hits; ML and orchestration are real.
        for name in ("clusters", "mentions", "provenance", "teaching", "identity", "main_edges",
                     "validator", "concept_labels", "roadmap", "module_titles"):
            setattr(pipeline, name, CachedStage("validated" if name == "validator" else name))
        return pipeline, configured

    monkeypatch.setattr("doc2roadmap.presentation.cli.main.build_learning_graph", build)
    assert main(["roadmap", "--doc-id", "doc"]) == 0
    assert store.latest.manifest["config"]["algorithm_id"] == "a8-secondary-ml-v1"
    assert store.latest.manifest["config"]["mode"] == "ml"
    assert store.latest.payload["cost_summary"]["secondary_usd"] == 0
    assert scorer.calls == 1 and store.saved_versions == 1
    assert calls == ["clusters", "mentions", "provenance", "teaching", "identity", "main_edges",
                     "validated", "concept_labels", "roadmap", "module_titles"]
    assert '"stage": "edges"' in capsys.readouterr().out
