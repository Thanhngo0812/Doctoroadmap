"""SA-70 (spec bài giảng mục 11.7): a page-picture failure does not fail the book build; other failures still do."""
import logging
import types

import pytest

from doc2roadmap.composition_build import DocumentPipeline
from doc2roadmap.composition_phase_b import PhaseBRuntime
from doc2roadmap.config import Settings
from doc2roadmap.domain.models import DocumentNode
from tests.unit.presentation.test_a1_d02_packets import make_pdf


def prepared(monkeypatch, tmp_path, *, capture=None, persist=None):
    monkeypatch.setattr(PhaseBRuntime, "a12", lambda self, doc_id, **kwargs: {
        "graph_version": 8, "retrieval_version": 1, "assignments": {}})
    monkeypatch.setattr("doc2roadmap.application.phase_b.concept_index.IndexConcepts",
                        lambda *args: types.SimpleNamespace(execute=lambda *a, **k: {"concept_count": 0}))
    monkeypatch.setattr("doc2roadmap.application.phase_b.formula_images.persist_formula_images", persist or (
        lambda *a, **k: {"index_path": "i", "cut_count": 0, "skipped_count": 0}))
    monkeypatch.setattr("doc2roadmap.application.phase_b.formula_images.CutFormulaImages",
                        lambda renderer: types.SimpleNamespace(execute=lambda *a, **k: {}))
    if capture:
        monkeypatch.setattr("doc2roadmap.application.phase_b.page_images.CapturePageImages",
                            lambda renderer: types.SimpleNamespace(execute=capture))
    pdf = tmp_path / "book.pdf"
    make_pdf(pdf)
    tree = types.SimpleNamespace(nodes=[DocumentNode("formula", "[formula]", 1, page=1)], parse_stats={"page_count": 1})
    pipeline = object.__new__(DocumentPipeline)
    pipeline.settings = Settings(_env_file=None, artifact_dir=tmp_path / "art")
    pipeline.allow_spend = False
    pipeline.embedding_guard = object()
    pipeline.store = types.SimpleNamespace(
        load_graph=lambda doc, version: types.SimpleNamespace(manifest={"config": {"chunks_version": 5}}),
        load_chunks=lambda doc, version: types.SimpleNamespace(manifest={"parse_version": 4},
                                                               result=types.SimpleNamespace(chunks=[])),
        load_parse=lambda doc, version: types.SimpleNamespace(tree=tree))
    return pipeline, pdf


@pytest.mark.parametrize("error", [OSError("disk full"), RuntimeError("pdfium")])
def test_a_failing_picture_capture_leaves_the_step_succeeded_and_records_the_error_name(monkeypatch, tmp_path, caplog, error):
    def capture(*args, **kwargs):
        raise error
    pipeline, pdf = prepared(monkeypatch, tmp_path, capture=capture)
    with caplog.at_level(logging.WARNING):
        result = pipeline.learning_prep(pdf, "book", 8)
    assert result["page_images"] == {"failed": type(error).__name__}
    assert result["formulas"]["cut_count"] == 0 and result["a12"]["graph_version"] == 8
    assert any(record.levelno == logging.WARNING and "page_images" in record.getMessage() for record in caplog.records)


def test_a_failure_of_another_step_is_not_swallowed(monkeypatch, tmp_path):
    def persist(*args, **kwargs):
        raise OSError("cannot write formula images")
    pipeline, pdf = prepared(monkeypatch, tmp_path, persist=persist,
                             capture=lambda *a, **k: {"page_count": 1})
    with pytest.raises(OSError, match="formula images"):
        pipeline.learning_prep(pdf, "book", 8)
