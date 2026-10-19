"""Real readers, temporary artifact/SQL stores, and a hard network prohibition."""
import json
import sqlite3
import shutil
from pathlib import Path

import pytest

from doc2roadmap.composition_build import build_document_runner
from doc2roadmap.config import Settings
from tests.unit.presentation.test_a1_d02_packets import make_pdf


pytestmark = pytest.mark.integration


@pytest.fixture
def offline_settings(tmp_path, monkeypatch):
    calls = []

    def forbidden(*args, **kwargs):
        calls.append(True)
        raise AssertionError("W-13 acceptance must never call the provider")

    monkeypatch.setattr("doc2roadmap.infrastructure.llm.gemini.urlopen", forbidden)
    monkeypatch.setattr("doc2roadmap.infrastructure.embedding.gemini.urlopen", forbidden)
    monkeypatch.setattr("doc2roadmap.infrastructure.google_auth.VertexCredentials.headers", forbidden)
    return Settings(_env_file=None, artifact_dir=tmp_path / "artifacts",
                    llm_transport="vertex", vertex_project="offline-acceptance"), calls


@pytest.mark.parametrize("line", [
    "Students learn systems and data.",
    "This chapter explains probability.",
])
def test_english_pdf_stops_before_models_and_records_rejection(tmp_path, offline_settings, line):
    settings, calls = offline_settings
    source = tmp_path / "english.pdf"
    content = "BT /F1 7 Tf 8 188 Td " + " 0 -8 Td ".join(
        f"({line}) Tj" for _ in range(20)
    ) + " ET"
    make_pdf(source, content)
    result = build_document_runner(settings).execute(source, "english-new")
    assert result.status == "rejected", result.to_dict()
    assert result.error["code"] == "ngon_ngu_khong_ho_tro"
    assert calls == []
    assert result.model_calls == result.spent_usd == 0
    with sqlite3.connect(settings.artifact_dir / "builds.sqlite3") as connection:
        row = connection.execute("SELECT status, model_calls, result_json FROM build_runs").fetchone()
    assert row[:2] == ("rejected", 0)
    assert json.loads(row[2])["error"]["code"] == "ngon_ngu_khong_ho_tro"
    assert not (settings.artifact_dir / "graph").exists()


def test_image_only_pdf_is_rejected_without_models(tmp_path, offline_settings):
    settings, calls = offline_settings
    source = tmp_path / "scan.pdf"
    make_pdf(source, "q 200 0 0 200 0 0 cm /I Do Q", image=True)
    result = build_document_runner(settings).execute(source, "scan-new")
    assert result.status == "rejected"
    assert result.error["code"] == "ban_quet"
    assert calls == []
    assert result.spent_usd == result.model_calls == 0


def test_doc6_dry_run_uses_real_reader_without_graph_or_provider_calls(offline_settings):
    settings, calls = offline_settings
    source = Path(__file__).resolve().parents[2] / "doc-6.pdf"
    assert source.is_file(), "W-13 acceptance requires the original development doc-6.pdf"
    result = build_document_runner(settings).execute(source, "doc-6", dry_run=True)
    assert result.status == "dry_run", result.to_dict()
    assert result.completed_steps == ["doc_reading"]
    assert result.graph_version is None
    assert result.step_details["doc_reading"]["page_count"] == 25
    assert calls == []
    assert result.spent_usd == result.model_calls == 0
    assert not (settings.artifact_dir / "graph").exists()
    assert not any("estimate" in key for key in result.to_dict())


def test_doc6_missing_role_cache_stops_before_spend(offline_settings, monkeypatch):
    from doc2roadmap.composition_build import DocumentPipeline

    settings, calls = offline_settings
    source = Path(__file__).resolve().parents[2] / "doc-6.pdf"
    labels = []
    label_roles = DocumentPipeline.label_roles

    def checked_labels(pipeline, doc_id):
        labels.append(doc_id)
        return label_roles(pipeline, doc_id)

    monkeypatch.setattr(DocumentPipeline, "label_roles", checked_labels)
    result = build_document_runner(settings).execute(source, "doc-6")
    assert labels == ["doc-6"]
    assert result.status == "failed", result.to_dict()
    assert result.error["stage"] == "concepts"
    assert result.error["error_type"] == "SpendNotAllowed"
    assert result.completed_steps == ["doc_reading"]
    assert result.spent_usd == result.model_calls == 0
    assert calls == []
    assert not (settings.artifact_dir / "candidates").exists()
    assert not (settings.artifact_dir / "graph").exists()
    with sqlite3.connect(settings.artifact_dir / "builds.sqlite3") as connection:
        row = connection.execute("SELECT status, model_calls, spent_usd FROM build_runs").fetchone()
    assert row == ("failed", 0, 0.0)


def test_real_and_fake_share_the_dry_run_contract(offline_settings):
    from doc2roadmap.infrastructure.artifacts.fake_build_runner import FakeBuildRunner

    settings, calls = offline_settings
    source = Path(__file__).resolve().parents[2] / "doc-6.pdf"
    recorded = []
    real_events, fake_events = [], []
    real = build_document_runner(settings, recorder=recorded.append).execute(
        source, "doc-6", dry_run=True, progress=lambda step, detail: real_events.append((step, detail["status"]))
    )
    fake = FakeBuildRunner(settings.artifact_dir, "doc-6", recorder=recorded.append).execute(
        source, "copied-dry", dry_run=True,
        progress=lambda step, detail: fake_events.append((step, detail["status"]))
    )
    for result in (real, fake):
        assert result.status == "dry_run"
        assert result.completed_steps == ["doc_reading"]
        assert result.graph_version is None
        assert result.spent_usd == result.model_calls == 0
    assert real_events == fake_events
    assert recorded == [real, fake]
    assert calls == []
    assert not (settings.artifact_dir / "graph").exists()


def test_direct_canonical_reuses_doc6_without_gold_or_other_books(offline_settings, monkeypatch):
    from doc2roadmap.application.use_cases import a4_gold
    from doc2roadmap.composition_build import DocumentPipeline

    settings, calls = offline_settings
    original = Path(__file__).resolve().parents[2] / "artifacts"
    for kind in ("parse_tree", "chunks", "candidates", "canonical"):
        shutil.copytree(original / kind / "doc-6", settings.artifact_dir / kind / "doc-6")

    def forbidden_gold(*args, **kwargs):
        raise AssertionError("new-book path cannot load gold")

    monkeypatch.setattr(a4_gold, "load_gold", forbidden_gold)
    pipeline = DocumentPipeline(settings, allow_spend=False)
    before = pipeline.store.load_latest_canonical("doc-6")
    original_manifest = (before.path / "manifest.json").read_bytes()
    result = pipeline.canonical("doc-6", "vi")
    after = pipeline.store.load_latest_canonical("doc-6")
    assert result["reused"] is True
    assert result["canonical_version"] == before.version == after.version
    assert before.manifest["config_hash"] == after.manifest["config_hash"]
    assert pipeline.usage()["model_calls"] == pipeline.usage()["spent_usd"] == 0
    assert (before.path / "manifest.json").read_bytes() == original_manifest
    assert {path.name for path in (settings.artifact_dir / "canonical").iterdir()} == {"doc-6"}
    assert calls == []
