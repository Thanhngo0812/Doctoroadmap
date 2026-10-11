from types import SimpleNamespace as NS

import pytest

from doc2roadmap.domain.models import DocumentTree
from doc2roadmap.infrastructure.parsing.docling_parser import DoclingParser, PipelineConfig
from tests.conftest import load_docling_fixture


def fixture():
    first = NS(page_no=1, bbox=NS(l=10, t=90, r=110, b=80, coord_origin='BOTTOMLEFT'), charspan=(0, 8))
    second = NS(page_no=2, bbox=NS(l=10, t=20, r=110, b=30, coord_origin='TOPLEFT'), charspan=(8, 16))
    cap = NS(label='caption', text='Figure G G G', orig='Figure G G G', self_ref='#/texts/0', prov=[first, second])
    orphan = NS(label='caption', text='Unlinked caption', orig='Unlinked caption', self_ref='#/texts/1', prov=[])
    table = NS(label='table', text='A B', self_ref='#/tables/0', captions=[NS(cref='#/texts/0'), NS(cref='#/texts/missing')],
               prov=[first], data=NS(grid=[[NS(text='A'), NS(text='B')]]),
               caption_text=lambda **kw: 'Figure G G G', export_to_markdown=lambda **kw: '| A | B |')
    items = [table, cap, orphan]
    return NS(iterate_items=lambda: iter((i, 1) for i in items), texts=[cap, orphan], pages={1: None, 2: None})


def test_linked_and_orphan_captions_survive_with_all_source_boxes():
    parsed = DoclingParser().adapt(fixture(), 'book.pdf')
    metadata = parsed.tree.parse_stats['caption_provenance']
    linked, orphan = metadata['items']
    assert linked['source_ref'] == '#/texts/0'
    assert linked['text'] == 'Figure G G G'
    assert [(p['page'], p['bbox'], p['coord_origin'], p['charspan']) for p in linked['provenance']] == [
        (1, [10., 90., 110., 80.], 'BOTTOMLEFT', [0, 8]),
        (2, [10., 20., 110., 30.], 'TOPLEFT', [8, 16]),
    ]
    assert linked['owners'] == [{'source_ref': '#/tables/0', 'node_type': 'table',
                                'table_id': parsed.tree.nodes[0].table_id, 'image_id': None}]
    assert orphan['owners'] == [] and orphan['provenance'] == []
    assert metadata['unresolved_links'] == [{'owner_ref': '#/tables/0', 'caption_ref': '#/texts/missing'}]
    assert DocumentTree.from_dict(parsed.tree.to_dict()).parse_stats == parsed.tree.parse_stats
    assert sum(n.text == 'Unlinked caption' for n in parsed.tree.nodes) == 1
    assert not any(n.text == 'Figure G G G' for n in parsed.tree.nodes)  # no duplicated chunk payload


def test_caption_metadata_does_not_silently_claim_correct_semantic_labels():
    data = DoclingParser().adapt(fixture(), 'book.pdf').tree.parse_stats['caption_provenance']
    assert data['label_source'] == 'docling_unreviewed'
    assert data['schema_version'] == 1


def test_legacy_parse_stays_byte_compatible_without_new_metadata():
    parsed = DoclingParser(pipeline=PipelineConfig(pdf_text_policy='legacy')).adapt(fixture(), 'book.pdf')
    assert 'caption_provenance' not in parsed.tree.parse_stats
    assert parsed.tree.nodes[0].context_prefix == 'Figure G'


def test_real_caption_refs_resolve_to_own_boxes_and_actual_assets():
    doc = load_docling_fixture()
    parsed = DoclingParser().adapt(doc, 'book.pdf')
    records = parsed.tree.parse_stats['caption_provenance']['items']
    raw = {i.self_ref: i for i, _ in doc.iterate_items() if DoclingParser._label(i) == 'caption'}
    assert len(records) == len(raw) == 9
    for record in records:
        expected = raw[record['source_ref']]
        assert record['text'] == expected.text
        assert record['provenance'][0]['bbox'] == list(DoclingParser._bbox(expected))
        for owner in record['owners']:
            assert owner['image_id'] in parsed.images
    assert sum(not r['owners'] for r in records) == 1


def test_missing_provenance_guard_is_falsifiable(monkeypatch):
    original = DoclingParser._caption_provenance
    def broken(cls, document, items, assets):
        data = original(document, items, assets)
        for item in data['items']:
            item['provenance'] = []
        return data
    monkeypatch.setattr(DoclingParser, '_caption_provenance', classmethod(broken))
    with pytest.raises(AssertionError):
        test_linked_and_orphan_captions_survive_with_all_source_boxes()


def exercise_caption_cache(tmp_path):
    from doc2roadmap.application.use_cases import IngestDocument
    from doc2roadmap.infrastructure.artifacts import JsonArtifactStore
    from tests.conftest import WordCounter, splitter
    calls = []

    class Parser(DoclingParser):
        def parse(self, source, filename):
            calls.append(self.adapter_version)
            parsed = self.adapt(fixture(), filename)
            if self.adapter_version == 12:
                parsed.tree.parse_stats.pop('caption_provenance', None)
            return parsed

    class Old(Parser):
        @property
        def adapter_version(self):
            return 12

    store = JsonArtifactStore(tmp_path)
    versions = []
    for parser in (Old(), Parser(), Parser()):
        result = IngestDocument(parser, store, WordCounter(), splitter()).execute(b'pdf', 'book.pdf', 'book')
        versions.append(result.parse_version)
    assert calls == [12, 13] and versions == [1, 2, 2]
    first, second = store.load_parse('book', 1), store.load_parse('book', 2)
    assert 'caption_provenance' not in first.tree.parse_stats
    assert second.tree.parse_stats['caption_provenance']['items'][0]['provenance'][1]['page'] == 2


def test_caption_metadata_is_persisted_without_reusing_v12(tmp_path):
    exercise_caption_cache(tmp_path)


def test_cache_version_mutation_is_detected(tmp_path, monkeypatch):
    import doc2roadmap.infrastructure.parsing.docling_parser as parser_module
    monkeypatch.setattr(parser_module, 'ADAPTER_VERSION', 12)
    with pytest.raises(AssertionError):
        exercise_caption_cache(tmp_path)
