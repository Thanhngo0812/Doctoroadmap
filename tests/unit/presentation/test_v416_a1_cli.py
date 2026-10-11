import hashlib
import json

import pytest

from doc2roadmap.application.use_cases.ingest_document import parse_config, _hash, IngestDocument
from doc2roadmap.infrastructure.parsing.docling_parser import DoclingParser, PipelineConfig
from doc2roadmap.infrastructure.parsing.nhe_parser import NheParser
from doc2roadmap.infrastructure.parsing.pdf_scope import require_native_pdf
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore
from doc2roadmap.presentation.cli import main as cli
from tests.conftest import WordCounter, splitter
from tests.unit.infrastructure.test_nhe_parser import combine_pdf, IMAGE, NATIVE


def test_cli_default_light_and_explicit_docling(monkeypatch):
    calls = []
    monkeypatch.setattr(cli, '_ingest', lambda *a, **kw: calls.append(kw))
    assert cli.main(['ingest', 'book.pdf', '--doc-id', 'book']) == 0
    assert calls[-1]['a1'] == 'nhe' and calls[-1]['pipeline'] is None
    assert cli.main(['ingest', 'book.pdf', '--doc-id', 'book', '--a1', 'docling']) == 0
    assert calls[-1]['a1'] == 'docling' and calls[-1]['pipeline'] == PipelineConfig()


@pytest.mark.parametrize('flag', [
    ['--pdf-backend', 'pypdfium2'], ['--pdf-text-policy', 'preserve'],
    ['--no-do-ocr'], ['--images-scale', '2'], ['--table-mode', 'fast'],
])
def test_light_rejects_explicit_docling_flags(monkeypatch, capsys, flag):
    monkeypatch.setattr(cli, '_ingest', lambda *a, **kw: pytest.fail('incompatible flags reached ingest'))
    assert cli.main(['ingest', 'book.pdf', '--doc-id', 'book', *flag]) == 2
    assert '--a1 docling' in capsys.readouterr().err


def test_cache_separates_paths_models_and_versions_without_changing_legacy_key():
    light = NheParser()
    legacy = DoclingParser('docling-parse', pipeline=PipelineConfig(pdf_text_policy='legacy'))
    old = dict(adapter='docling:2.114.0', adapter_version=11, image_scale=2.0)
    assert parse_config(legacy) == old
    original = _hash(parse_config(light))
    assert original != _hash(old)
    light.adapter_version += 1
    assert original != _hash(parse_config(light))
    light.adapter_version -= 1
    light.pipeline_config['models'] = {'heading.joblib': 'different bytes'}
    assert original != _hash(parse_config(light))


@pytest.mark.parametrize('parser', [NheParser(), DoclingParser()])
def test_scope_gate_stops_both_product_paths_before_parse_and_store(tmp_path, monkeypatch, parser):
    source = combine_pdf(tmp_path, [IMAGE, IMAGE, NATIVE])
    store = JsonArtifactStore(tmp_path / 'artifacts')
    case = IngestDocument(parser, store, WordCounter(), splitter(), pdf_scope_validator=require_native_pdf)
    monkeypatch.setattr(parser, 'parse', lambda *a: pytest.fail('scan reached expensive parsing'))
    with pytest.raises(ValueError, match='bản quét'):
        case.execute(source, 'book.pdf', 'book')
    assert not list(store.root.glob('parse_tree/book/v*'))


def test_light_cached_bad_text_stops_even_in_dry_run_and_reason_keeps_warning(tmp_path):
    from doc2roadmap.domain.models import DocumentTree, DocumentNode
    parser = NheParser()
    source = combine_pdf(tmp_path, [NATIVE])
    store = JsonArtifactStore(tmp_path / 'artifacts')
    config = parse_config(parser)
    store.save_parse('book', hashlib.sha256(source).hexdigest(), _hash(config), 'unused', {'parser': config},
                     DocumentTree([DocumentNode('text', 'BOÄ MOÂN TOAÙN', 0, page=1)]), {})
    case = IngestDocument(parser, store, WordCounter(), splitter(), allow_backend_fallback=False)
    with pytest.raises(ValueError, match='--a1 docling'):
        case.select_parse(source, 'book.pdf', 'book', dry_run=True)
    case.select_parse(source, 'book.pdf', 'book', dry_run=True, quality_reason='Đọc bản đã khóa')
    assert case.last_parse_selection['attempts'][0]['quality']['warnings']


def test_light_dry_run_does_not_reuse_docling_parse_and_does_not_write(tmp_path):
    from doc2roadmap.domain.models import DocumentTree, DocumentNode
    source = combine_pdf(tmp_path, [NATIVE])
    store = JsonArtifactStore(tmp_path / 'artifacts')
    legacy = DoclingParser('docling-parse', pipeline=PipelineConfig(pdf_text_policy='legacy'))
    config = parse_config(legacy)
    store.save_parse('book', hashlib.sha256(source).hexdigest(), _hash(config), 'unused', {'parser': config},
                     DocumentTree([DocumentNode('text', 'Nội dung sách.', 0, page=1)]), {})
    before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in store.root.rglob('*') if p.is_file()}
    light = IngestDocument(NheParser(), store, WordCounter(), splitter(), allow_backend_fallback=False)
    _, cached, *_ = light.select_parse(source, 'book.pdf', 'book', dry_run=True)
    assert cached is None
    assert before == {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in store.root.rglob('*') if p.is_file()}


def test_light_docx_dry_run_is_rejected_before_cache_lookup(tmp_path, monkeypatch):
    source = tmp_path / 'book.docx'
    source.write_bytes(b'docx')
    monkeypatch.setattr(cli, 'build_ingest', lambda *a, **kw: pytest.fail('unsupported DOCX reached composition'))
    with pytest.raises(ValueError, match='--a1 docling'):
        cli._ingest(source, 'book', a1='nhe', dry_run=True)
