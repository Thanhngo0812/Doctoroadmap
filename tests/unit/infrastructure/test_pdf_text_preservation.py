"""Production A1 must not infer overlapping PDF glyphs from repeated letters."""
import hashlib
from types import SimpleNamespace

import pytest

from doc2roadmap.application.use_cases import IngestDocument
from doc2roadmap.application.use_cases.ingest_document import parse_config, _hash
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore
from doc2roadmap.domain.chunking import chunk_document
from doc2roadmap.domain.normalization import normalize_text
from doc2roadmap.infrastructure.parsing.docling_parser import DoclingParser, PipelineConfig
from tests.conftest import WordCounter, splitter


def document(items):
    return SimpleNamespace(iterate_items=lambda: iter((item, 1) for item in items), texts=items, pages={1: None})


def item(text, label='text', page=1):
    return SimpleNamespace(text=text, orig=text, label=label,
                           prov=[SimpleNamespace(page_no=page, bbox=SimpleNamespace(l=10, t=500, r=300, b=480))])


@pytest.mark.parametrize('label', ['text', 'formula', 'caption', 'section_header', 'list_item'])
def test_default_keeps_legitimate_repeated_variables_and_dna(label):
    value = 'G G G C T T A A G; x x x'
    parsed = DoclingParser().adapt(document([item(value, label)]), 'book.pdf')
    node = parsed.tree.nodes[0]
    assert (node.raw_text if label == 'formula' else node.text) == value
    if label == 'formula':
        assert node.formula_id == hashlib.sha256(normalize_text(value).encode()).hexdigest()


def test_tables_and_linked_captions_use_same_preservation_policy():
    value = 'G G G C'
    table = item(value, 'table')
    table.data = SimpleNamespace(grid=[[SimpleNamespace(text=value)]])
    table.export_to_markdown = lambda **kw: '| G G G C |'
    table.caption_text = lambda **kw: 'Bảng 1. G G G'
    node = DoclingParser().adapt(document([table]), 'book.pdf').tree.nodes[0]
    assert node.table_rows == [[value]]
    assert node.text == '| G G G C |'
    assert node.context_prefix == 'Bảng 1. G G G'
    assert node.table_id == DoclingParser._table_id([[value]])


def test_repeated_letters_survive_downstream_chunk_text_and_formula_reference():
    parsed = DoclingParser().adapt(document([item('DNA G G G C.'), item('x x x', 'formula', 2)]), 'book.pdf')
    result = chunk_document(parsed.tree, 'book', WordCounter(), splitter())
    assert 'G G G C' in result.normalized_full_text
    assert 'x x x' not in result.normalized_full_text  # raw formula remains behind a reference
    assert sum(len(c.formula_refs) for c in result.chunks) == 1
    assert all(result.normalized_full_text[c.char_start:c.char_end] == c.text for c in result.chunks)


def test_legacy_policy_is_explicit_and_preserves_v11_cache_identity():
    legacy = DoclingParser(pipeline=PipelineConfig(pdf_text_policy='legacy'))
    modern = DoclingParser()
    expected = {'adapter': legacy.identifier, 'adapter_version': 11, 'image_scale': 2.0}
    assert parse_config(legacy) == expected
    assert _hash(parse_config(modern)) != _hash(expected)
    assert legacy.adapt(document([item('x x x')]), 'book.pdf').tree.nodes[0].text == 'x'
    assert modern.adapt(document([item('x x x')]), 'book.pdf').tree.nodes[0].text == 'x x x'
    assert legacy.with_pdf_backend('pypdfium2').pipeline.pdf_text_policy == 'legacy'
    with pytest.raises(ValueError, match='pdf_text_policy'):
        PipelineConfig(pdf_text_policy='typo')


def _exercise_policy_cache(tmp_path):
    store = JsonArtifactStore(tmp_path)
    calls = []

    class Parser(DoclingParser):
        def parse(self, source, filename):
            calls.append(self.pipeline.pdf_text_policy)
            return self.adapt(document([item('DNA G G G C.')]), filename)

    versions = []
    for policy in ('legacy', 'preserve', 'preserve', 'legacy'):
        parser = Parser(pipeline=PipelineConfig(pdf_text_policy=policy))
        result = IngestDocument(parser, store, WordCounter(), splitter()).execute(b'pdf', 'book.pdf', 'book')
        versions.append(result.parse_version)
        text = store.load_parse('book', result.parse_version).tree.nodes[0].text
        assert text == ('DNA G C.' if policy == 'legacy' else 'DNA G G G C.')
    assert calls == ['legacy', 'preserve']
    assert versions == [1, 2, 2, 1]


def test_ingest_cache_keeps_both_policies_and_reuses_each(tmp_path):
    _exercise_policy_cache(tmp_path)


def test_cache_assertion_detects_missing_policy_discriminator(tmp_path, monkeypatch):
    monkeypatch.setattr(DoclingParser, 'adapter_version', property(lambda self: 11))
    with pytest.raises(AssertionError):
        _exercise_policy_cache(tmp_path)


def test_policy_is_not_sent_as_an_unknown_docling_option():
    for policy in ('legacy', 'preserve'):
        config = PipelineConfig(pdf_text_policy=policy)
        assert 'pdf_text_policy' not in config.options().model_dump()
