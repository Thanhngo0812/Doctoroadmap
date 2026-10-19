import json
import shutil
from pathlib import Path

import pytest

from doc2roadmap.application.phase_b.retrieval import load_learning_graph
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore
from doc2roadmap.infrastructure.artifacts.fake_build_runner import FakeBuildRunner


DEV_ARTIFACTS = ("parse_tree", "chunks", "candidates", "canonical", "retrieval", "graph")


def test_fake_copies_allowlisted_artifacts_and_remaps_ids(tmp_path):
    root = tmp_path / "artifacts"
    for artifact in ("parse_tree", "chunks"):
        path = root / artifact / "doc-1" / "v1"
        path.mkdir(parents=True)
        (path / "manifest.json").write_text(json.dumps({"doc_id": "doc-1", "version": 1}))
    events = []
    (root / "canonical/doc-1/v1").mkdir(parents=True)
    (root / "candidates/doc-1/v1").mkdir(parents=True)
    (root / "graph/doc-1/v1").mkdir(parents=True)
    (root / "graph/doc-1/v1/manifest.json").write_text('{"doc_id":"doc-1"}')
    result = FakeBuildRunner(root, "doc-1").execute(tmp_path / "input.pdf", "copy-1", dry_run=True,
        progress=lambda step, detail: events.append((step, detail)))
    assert result.status == "dry_run"
    assert result.completed_steps == ["doc_reading"]
    assert [detail["status"] for _, detail in events] == ["started", "completed", "planned", "planned", "planned"]
    assert json.loads((root / "parse_tree/copy-1/v1/manifest.json").read_text())["doc_id"] == "copy-1"
    assert json.loads((root / "parse_tree/doc-1/v1/manifest.json").read_text())["doc_id"] == "doc-1"


def test_fake_dry_run_only_completes_reading_and_plans_remaining_steps(tmp_path):
    root = tmp_path / "artifacts"
    for artifact in ("parse_tree", "chunks"):
        path = root / artifact / "doc-1" / "v1"
        path.mkdir(parents=True)
        (path / "manifest.json").write_text('{"doc_id":"doc-1"}')
    events = []
    result = FakeBuildRunner(root, "doc-1").execute(
        tmp_path / "in.pdf", "copy-1", dry_run=True,
        progress=lambda step, detail: events.append((step, detail)),
    )
    assert result.status == "dry_run"
    assert result.completed_steps == ["doc_reading"]
    assert [detail["status"] for _, detail in events] == ["started", "completed", "planned", "planned", "planned"]
    assert (root / "parse_tree/copy-1").exists() and (root / "chunks/copy-1").exists()
    assert not (root / "graph/copy-1").exists()


def test_cancellation_after_concepts_prevents_graph_copy(tmp_path):
    root = tmp_path / "artifacts"
    for artifact in DEV_ARTIFACTS:
        path = root / artifact / "doc-1" / "v1"
        path.mkdir(parents=True)
        (path / "manifest.json").write_text('{"doc_id":"doc-1"}')
    cancelled = False
    recorded = []

    def progress(step, detail):
        nonlocal cancelled
        if step == "concepts" and detail["status"] == "completed":
            cancelled = True

    result = FakeBuildRunner(root, "doc-1", recorder=recorded.append).execute(
        tmp_path / "in.pdf", "copy-1", progress=progress, cancelled=lambda: cancelled
    )
    assert result.status == "cancelled"
    assert result.completed_steps == ["doc_reading", "concepts"]
    assert not (root / "graph/copy-1").exists()
    assert recorded == [result]


def test_fake_graph_version_is_latest_loadable_complete_graph(tmp_path):
    source_root = Path("artifacts")
    root = tmp_path / "artifacts"
    for artifact in DEV_ARTIFACTS:
        source = source_root / artifact / "doc-6"
        if source.exists():
            shutil.copytree(source, root / artifact / "doc-6")
    formula_source = source_root / "phase_b/formula_images/doc-6"
    if formula_source.exists():
        shutil.copytree(formula_source, root / "phase_b/formula_images/doc-6")
    source_store = JsonArtifactStore(root)
    source_graph = load_learning_graph(source_store, "doc-6")
    unfinished = source_store.save_graph("doc-6", "unfinished", "unfinished", {},
        {"modules": [], "main_complete": False}, upstream_version=None, manifest_fields={"stage": "stages"})
    source_latest_version = unfinished.version
    assert source_latest_version > source_graph.graph_version
    latest_manifest = (root / "graph/doc-6" / f"v{source_latest_version}" / "manifest.json").read_bytes()

    result = FakeBuildRunner(root, "doc-6").execute(tmp_path / "in.pdf", "copy-6")
    target = load_learning_graph(JsonArtifactStore(root), "copy-6")
    assert result.graph_version == target.graph_version == source_graph.graph_version
    assert target.payload["doc_id"] == "copy-6"
    assert result.completed_steps == ["doc_reading", "concepts", "graph", "learning_prep"]
    assert result.model_calls == result.spent_usd == 0
    assert (root / "graph/doc-6" / f"v{source_latest_version}" / "manifest.json").read_bytes() == latest_manifest
    assert "retrieval" in result.step_details["concepts"]["artifacts_copied"]
    formula_index = root / "phase_b/formula_images/copy-6/parse-v2/index.json"
    assert json.loads(formula_index.read_text())["doc_id"] == "copy-6"

    cancel = False

    def cancel_at_prep(step, detail):
        nonlocal cancel
        if step == "learning_prep" and detail["status"] == "completed":
            cancel = True

    cancelled = FakeBuildRunner(root, "doc-6").execute(
        tmp_path / "in.pdf", "copy-cancelled", progress=cancel_at_prep,
        cancelled=lambda: cancel,
    )
    assert cancelled.status == "cancelled"
    assert cancelled.completed_steps == ["doc_reading", "concepts", "graph", "learning_prep"]


@pytest.mark.parametrize("source,target", [
    ("unapproved", "copy"), ("doc-2", "copy"), ("doc-3", "copy"), ("doc-5", "copy"),
    ("doc-1", "doc-1"), ("doc-1", "../bad"),
])
def test_fake_rejects_unapproved_or_unsafe_ids(tmp_path, source, target):
    if source in FakeBuildRunner.SOURCES:
        result = FakeBuildRunner(tmp_path, source).execute(tmp_path / "in.pdf", target)
        assert result.status == "failed"
        assert result.error["code"] == "loi_noi_bo"
        assert result.error["error_type"] == "ValueError"
    else:
        with pytest.raises(ValueError):
            FakeBuildRunner(tmp_path, source).execute(tmp_path / "in.pdf", target)


def test_fake_refuses_existing_target_without_overwriting(tmp_path):
    source = tmp_path / "chunks/doc-1/v1"
    source.mkdir(parents=True)
    (source / "manifest.json").write_text('{"doc_id":"doc-1"}')
    target = tmp_path / "chunks/copy/v1/manifest.json"
    target.parent.mkdir(parents=True)
    target.write_text('{"doc_id":"copy"}')
    result = FakeBuildRunner(tmp_path, "doc-1").execute(tmp_path / "in.pdf", "copy")
    assert result.status == "failed"
    assert target.read_text() == '{"doc_id":"copy"}'


def test_fake_records_missing_artifacts_as_failed(tmp_path):
    recorded = []
    result = FakeBuildRunner(tmp_path, "doc-1", recorder=recorded.append).execute(
        tmp_path / "in.pdf", "copy"
    )
    assert result.status == "failed"
    assert result.error["code"] == "loi_noi_bo"
    assert result.error["error_type"] == "FileNotFoundError"
    assert result.error["retryable"] is False
    assert recorded == [result]


def test_fake_rejects_non_vietnamese_language(tmp_path):
    result = FakeBuildRunner(tmp_path, "doc-1").execute(
        tmp_path / "in.pdf", "copy", language="en"
    )
    assert result.status == "rejected"
    assert result.error["code"] == "ngon_ngu_khong_ho_tro"
