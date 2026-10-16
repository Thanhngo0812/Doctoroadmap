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
    assert Settings(_env_file=None).secondary_mode == "llm"
    with pytest.raises(ValueError):
        Settings(_env_file=None, secondary_mode="unknown")
    from doc2roadmap import composition
    from doc2roadmap.application.use_cases.build_secondary_ml_edges import BuildSecondaryMLEdges
    from doc2roadmap.application.use_cases.build_secondary_edges import BuildSecondaryEdges

    settings = Settings(_env_file=None, artifact_dir=tmp_path, secondary_mode="ml", gemini_api_key="fake")
    embedding = SimpleNamespace(limiter=None)
    monkeypatch.setattr(composition, "_a3_dependencies", lambda: (settings, fixture(), embedding))
    monkeypatch.setattr("doc2roadmap.infrastructure.secondary_model.LightGBMSecondaryScorer", Scorer)
    monkeypatch.setattr("doc2roadmap.infrastructure.secondary_tokenizer.VietnameseWordTokenizer", Tokenize)
    pipeline, _ = composition.build_learning_graph(allow_spend=False)
    assert isinstance(pipeline.secondary_edges, BuildSecondaryMLEdges)
    assert pipeline.secondary_edges.plan("doc").calls_estimate == 0
    artifact, _ = pipeline.secondary_edges.execute("doc")
    assert len(artifact.payload["secondary_edges"]) == 1
    settings.secondary_mode = "llm"
    pipeline, _ = composition.build_learning_graph(allow_spend=False)
    assert type(pipeline.secondary_edges) is BuildSecondaryEdges
