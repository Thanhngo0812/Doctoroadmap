"""Hand-built shapes of xstk/doc-6/doc-4, without opening held-out documents."""
import json
import unicodedata
from copy import deepcopy
from types import SimpleNamespace

import pytest

from doc2roadmap.application.ports import ParsedDocument
from doc2roadmap.application.prompt_library import load_prompt
from doc2roadmap.application.use_cases.ingest_document import IngestDocument, refresh_chunk_roles
from doc2roadmap.application.use_cases.label_chunk_roles import (
    LabelChunkRoles, ROLE_SCHEMA, BATCH_SIZE, RETRY_SIZE, PROSE_MIN_CHARS, PROSE_LINE_MIN_CHARS,
)
from doc2roadmap.domain.canonical import digest
from doc2roadmap.domain.chunking import CHUNK_ALGORITHM_ID, assign_section_roles, chunk_document
from doc2roadmap.domain.document_structure import STRUCTURE_RULE
from doc2roadmap.domain.models import DocumentNode, DocumentTree
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore
from tests.conftest import WordCounter, splitter
from tests.unit.application.test_ingest import FakeParser


def repeated_tree(title='Cách giải', bodies=None):
    bodies = bodies if bodies is not None else ['Đặt biến rồi thay vào công thức để tìm kết quả.'] * 3
    nodes = []
    for i, body in enumerate(bodies, 1):
        for text, level in [(f'Chương {i}', 1), (title, 2),
                            (body, None), (f'{i}.1. ' + ['Xác suất', 'Ước lượng', 'Phân phối', 'Thống kê'][i-1], 2),
                            ('Một định nghĩa được dạy ở đây.', None)]:
            if text:
                nodes.append(DocumentNode('section_header' if level else 'text', text, len(nodes), level=level))
    return DocumentTree(nodes)


def result(title='Cách giải', bodies=None):
    return chunk_document(repeated_tree(title, bodies), 'roles', WordCounter(), splitter(),
                          target_tokens=1, heading_scheme='declared-v1')


class Model:
    model_id = 'fake'

    def __init__(self):
        self.calls = []

    def start_session(self, prompt):
        return self

    def ask_json(self, prompt, *, response_schema):
        rows = json.loads(prompt)['headings']
        self.calls.extend(rows)
        return SimpleNamespace(payload={'labels': [{'index': row['index'], 'role': 'noi_dung'} for row in rows]})


@pytest.mark.parametrize('title,bodies,outline', [
    ('Cách giải', None, False),
    ('Nội dung', ['Xác suất\nƯớc lượng\nPhân phối'] * 3, True),
    ('CÂU HỎI ÔN TẬP', [''] * 3, False),
    ('Câu hỏi ôn tập', ['Hãy giải thích Xác suất và trình bày bằng lời của em kèm một ví dụ minh hoạ.'] * 3, False),
    ('方法概要', ['Xác suất\nƯớc lượng\nPhân phối'] * 3, True),
    ('Nội dung', ['', 'Xác suất', 'Phân phối'], True),
    ('Nội dung', ['Xác suất', 'Xác suất'], False),
])
def test_repeated_heading_needs_body_evidence_before_structural_lock(title, bodies, outline):
    value = result(title, bodies)
    assign_section_roles(value.sections, value.chunks)
    members = [s for s in value.sections if s.title == title]
    assert len(members) == len(bodies or [0, 0, 0])
    assert {(s.role, s.role_source) for s in members} == {
        ('de_cuong', 'structure') if outline else ('noi_dung', '')}
    assert all(c.role == ('de_cuong' if outline else 'noi_dung') for c in value.chunks
               if c.parent_section_id in {s.section_id for s in members})


def test_cach_giai_reaches_label_roles_model_instead_of_being_silently_excluded(tmp_path):
    store, model = JsonArtifactStore(tmp_path), Model()
    base = store.save_chunks('roles', 'source', 'base', {'chunk': {}}, 1, result())
    labeled, _ = LabelChunkRoles(store, model, allow_spend=True).execute('roles', chunks_version=base.version)
    assert sum(row['title'] == 'Cách giải' for row in model.calls) == 3
    assert {(s.role, s.role_source) for s in labeled.result.sections if s.title == 'Cách giải'} == {('noi_dung', 'model')}


@pytest.mark.parametrize('body,coverage', [
    (unicodedata.normalize('NFD', 'XÁC SUẤT!!!'), 1),
    ('Xác suất abcdefg', .5),
    ('Xác suất abcdefgh', 7 / 15),
    ('tiềnXác suấtabc', 0),
    ('Nội dung', 0),
    ('... !!!', None),
])
def test_repeated_coverage_normalizes_titles_and_body_without_subword_or_self_matches(body, coverage):
    from doc2roadmap.domain.chunking import repeated_heading_coverage
    value = result('Nội dung', [body] * 3)
    assert repeated_heading_coverage(value.sections, value.chunks)['Nội dung'] == coverage
    assert all(s.role == ('de_cuong' if coverage is not None and coverage >= .5 else 'noi_dung')
               for s in value.sections if s.title == 'Nội dung')


def test_overlapping_title_matches_count_characters_once_and_ignore_short_titles():
    from doc2roadmap.domain.chunking import _heading_body_coverage
    assert _heading_body_coverage('linear algebra zzz', {'linear', 'linear algebra', 'algebra', 'zz'}) == 13 / 16
    assert _heading_body_coverage('ax abc', {'ax'}) == 0


def test_audit_is_read_only_and_skips_held_out_and_all_smoke_directories(tmp_path):
    import importlib.util
    from pathlib import Path
    path = Path('scripts/a2-de-cuong/kiem_05a.py')
    spec = importlib.util.spec_from_file_location('audit_05a', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    store = JsonArtifactStore(tmp_path)
    old = result()
    for section in old.sections:
        if section.title == 'Cách giải':
            section.role, section.role_source = 'de_cuong', 'structure'
    store.save_chunks('roles', 'source', 'base', {'chunk': {}}, 1, old)
    for doc in ('d01-t01', 'd01-t02', 'smoke', 'smoke-anything'):
        excluded = tmp_path / 'chunks' / doc / 'v1'
        excluded.mkdir(parents=True)
        (excluded / 'sections.json').write_text('must never be read', encoding='utf-8')
    before = {p: p.read_bytes() for p in tmp_path.rglob('*.json')}
    report = module.audit(tmp_path)
    assert report['documents'] == ['roles'] and report['group_count'] == 1
    row = report['groups'][0]
    assert row['old_roles'] == ['de_cuong'] and row['new_roles'] == ['noi_dung']
    assert row['new_role_sources'] == [''] and row['median_coverage'] == 0
    assert before == {p: p.read_bytes() for p in tmp_path.rglob('*.json')}


def test_label_roles_does_not_reuse_pre_05a_semantic_cache(tmp_path):
    store, model = JsonArtifactStore(tmp_path), Model()
    base = store.save_chunks('roles', 'source', 'base', {'chunk': {}}, 1, result())
    uc = LabelChunkRoles(store, model, allow_spend=True)
    config = {**base.manifest['config'], 'region_roles': {
        'algorithm_id': STRUCTURE_RULE + '+semantic-v3', 'chunks_version': base.version,
        'transfer_reference_version': None, 'batch_rule': 'chapter-and-separate-tail-v2',
        'batch_size': BATCH_SIZE, 'retry_size': RETRY_SIZE, 'prose_min_chars': PROSE_MIN_CHARS,
        'prose_line_min_chars': PROSE_LINE_MIN_CHARS,
        'prompt_hash': digest([load_prompt('a2', 'region-roles'), ROLE_SCHEMA]),
        'model_id': model.model_id, 'generation': uc.generation}}
    old = store.save_chunks('roles', 'source', digest(config), config, 1, deepcopy(base.result),
                            manifest_fields={'semantic_roles': True, 'roles_from_chunks_version': base.version})
    assert uc.plan('roles', chunks_version=base.version).status == 'run'
    new, reused = uc.execute('roles', chunks_version=base.version)
    assert not reused and new.version > old.version
    assert new.manifest['config_hash'] != old.manifest['config_hash']
    assert any(row['title'] == 'Cách giải' for row in model.calls)
    assert uc.execute('roles', chunks_version=base.version)[1]


def test_refresh_roles_invalidates_only_its_role_cache(tmp_path):
    store = JsonArtifactStore(tmp_path)
    config = {'chunk': {'algorithm_id': CHUNK_ALGORITHM_ID}}
    base = store.save_chunks('roles', 'source', digest(config), config, 1, result())
    old_config = {'chunk': {**config['chunk'], 'role_algorithm_id': CHUNK_ALGORITHM_ID}}
    old = store.save_chunks('roles', 'source', digest(old_config), old_config, 1, deepcopy(base.result))
    before = (base.path / 'chunks.json').read_bytes()
    new = refresh_chunk_roles(store, 'roles', version=base.version)
    assert new.version > old.version and new.manifest['config_hash'] != old.manifest['config_hash']
    assert new.manifest['config']['chunk']['algorithm_id'] == CHUNK_ALGORITHM_ID
    assert (base.path / 'chunks.json').read_bytes() == before
    assert refresh_chunk_roles(store, 'roles', version=base.version).version == new.version


def test_ingest_keeps_pre_05a_chunk_config_identity_and_cached_version(tmp_path):
    from doc2roadmap.application.extraction_prompt import load_prompts, prompt_hash
    from doc2roadmap.application.use_cases.extract_entities import ExtractEntities

    class Parser(FakeParser):
        def parse(self, source, filename):
            self.calls += 1
            return ParsedDocument(repeated_tree())

    store, parser = JsonArtifactStore(tmp_path), Parser()
    uc = IngestDocument(parser, store, WordCounter(), splitter())
    first = uc.execute(b'frozen source', 'book.pdf', 'roles', target_tokens=1, heading_scheme='declared-v1')
    base = store.load_chunks('roles', first.chunk_version)
    identity = [{k: v for k, v in c.to_dict().items() if k != 'role'} for c in base.result.chunks]
    assert base.manifest['config_hash'] == 'e55402903a795e9e8418ab6579c2869f582e97cb7c4fac7a2cc349f99c851147'
    assert digest(identity) == '4f08fb3fbd078695f7d054d9bfc347e860d7ff68cf7a93f082495a12e9b3e31a'
    extractor = SimpleNamespace(identifier='cached-only', model_id='fake',
                                start_session=lambda *_: pytest.fail('A3 must reuse its pre-05a cache'))
    generation, prompts = {'temperature': 0, 'max_output_tokens': 8192}, load_prompts()
    a3_config = {'algorithm_id': 'a3-section-conversation-v10', 'reviewed_node_types': {},
                 'chunks_config_hash': 'e55402903a795e9e8418ab6579c2869f582e97cb7c4fac7a2cc349f99c851147',
                 'extractor_id': extractor.identifier, 'model_id': extractor.model_id,
                 'prompt_hash': prompt_hash(model_id=extractor.model_id, generation=generation, prompts=prompts),
                 'generation': generation, 'embedding_model_id': None}
    cached = store.save_candidates('roles', base.manifest['source_hash'], digest(a3_config), a3_config,
        {'doc_id': 'roles', 'entities': [], 'edges': [], 'stats': {}}, upstream_version=base.version)
    before = (base.path / 'chunks.json').read_bytes()
    again = uc.execute(b'frozen source', 'book.pdf', 'roles', target_tokens=1, heading_scheme='declared-v1')
    assert parser.calls == 1 and again.chunk_version == first.chunk_version
    assert (base.path / 'chunks.json').read_bytes() == before
    extraction = ExtractEntities(store, extractor, None, generation=generation, prompts=prompts).execute('roles')
    assert extraction.reused and extraction.artifact_version == cached.version
