import hashlib
from types import SimpleNamespace

from doc2roadmap.application.use_cases import IngestDocument
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore
from doc2roadmap.infrastructure.parsing.docling_parser import PipelineConfig
from doc2roadmap.presentation.cli.main import _ingest, _parser, main
from tests.conftest import WordCounter, splitter
from tests.unit.application.test_ingest import FakeParser


def test_cli_pipeline_flags_reach_ingest(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr("doc2roadmap.presentation.cli.main._ingest", lambda *a, **kw: calls.append(kw))
    assert main(["ingest", str(tmp_path / "book.pdf"), "--doc-id", "book", "--a1", "docling", "--no-do-ocr",
                 "--table-mode", "fast", "--ocr-engine", "rapidocr", "--ocr-backend", "onnxruntime",
                 "--num-threads", "8", "--layout-model", "egret-medium", "--dry-run"]) == 0
    pipeline = calls[0]["pipeline"]
    assert pipeline == PipelineConfig(do_ocr=False, table_mode="fast", ocr_backend="onnxruntime",
                                      num_threads=8, layout_model="egret-medium")
    assert calls[0]["dry_run"] is True
    default = _parser().parse_args(["ingest", "book.pdf", "--doc-id", "book"])
    assert default.a1 == "nhe"
    assert all(getattr(default, name) is None for name in PipelineConfig.__dataclass_fields__)


def test_legacy_pdf_text_policy_reaches_ingest(monkeypatch):
    calls = []
    monkeypatch.setattr("doc2roadmap.presentation.cli.main._ingest", lambda *a, **kw: calls.append(kw))
    assert main(["ingest", "book.pdf", "--doc-id", "book", "--a1", "docling", "--pdf-text-policy", "legacy", "--dry-run"]) == 0
    assert calls[0]["pipeline"].pdf_text_policy == "legacy"


def test_dry_run_reuses_without_parse_or_writes(monkeypatch, tmp_path, capsys):
    source = tmp_path / "book.pdf"
    source.write_bytes(b"A sentence.")
    store = JsonArtifactStore(tmp_path / "artifacts")
    parser = FakeParser()
    use_case = IngestDocument(parser, store, WordCounter(), splitter())
    use_case.execute(source.read_bytes(), source.name, "book")
    def fail(*args, **kwargs):
        raise AssertionError("dry-run must not parse or write")
    monkeypatch.setattr(parser, "parse", fail)
    monkeypatch.setattr(store, "save_parse", fail)
    monkeypatch.setattr(store, "save_chunks", fail)
    before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in store.root.rglob("*") if p.is_file()}
    monkeypatch.setattr("doc2roadmap.presentation.cli.main.build_ingest",
                        lambda backend: (use_case, SimpleNamespace()))
    _ingest(source, "book", dry_run=True)
    assert '"parse": "tái dùng"' in capsys.readouterr().out
    assert before == {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in store.root.rglob("*") if p.is_file()}
    parser.pipeline_config = {"do_ocr": False}
    _ingest(source, "book", dry_run=True)
    assert '"parse": "cần parse mới"' in capsys.readouterr().out
