import pytest
from doc2roadmap.domain.chunking import chunk_document
from doc2roadmap.domain.models import DocumentNode, DocumentTree
from tests.conftest import WordCounter, splitter


def fixture():
    return DocumentTree(nodes=[
        DocumentNode('section_header','Chapter 1',0,level=1,tree_depth=1),
        DocumentNode('section_header','1. Basics',1,level=2,tree_depth=1),
        DocumentNode('paragraph','First content.',2),
        DocumentNode('section_header','• A deliberately supplied heading with many words that must not be silently discarded by another heuristic',3,level=2,tree_depth=9),
        DocumentNode('paragraph','Second content.',4),
        DocumentNode('section_header','Chapter 2',5,level=1,tree_depth=12),
        DocumentNode('paragraph','Third content.',6),
    ])


def execute(tree):
    return chunk_document(tree,'book',WordCounter(),splitter(),target_tokens=1,heading_scheme='declared-v1')


def test_declared_tree_controls_actual_chunk_ownership_without_demotion_or_clamp():
    source=fixture()
    saved=source.to_dict()
    out=execute(source)
    assert [(s.title,s.level) for s in out.sections[1:]]==[(n.text,n.level) for n in source.nodes if n.node_type=='section_header']
    assert [c.section_path for c in out.chunks]==[
        ['Chapter 1','1. Basics'],['Chapter 1',source.nodes[3].text],['Chapter 2']]
    assert [c.text for c in out.chunks]==['First content.','Second content.','Third content.']
    assert not any('clamped' in s or 'rejected_heading' in s for s in out.structure_warnings)
    assert source.to_dict()==saved


@pytest.mark.parametrize('levels',[[2],[None],[0],[-1],[True],[1.5],[1,3],[1,2,4]])
def test_declared_tree_rejects_missing_noninteger_or_skipped_parent_depth(levels):
    source=DocumentTree(nodes=[DocumentNode('section_header',f'Section {i}',i,level=level) for i,level in enumerate(levels)])
    with pytest.raises(ValueError,match='declared'):
        execute(source)


def test_explicit_mode_has_separate_chunk_cache_and_reuses_parse(tmp_path):
    from doc2roadmap.application.ports import ParsedDocument
    from doc2roadmap.application.use_cases import IngestDocument
    from doc2roadmap.infrastructure.artifacts import JsonArtifactStore
    from tests.unit.application.test_ingest import FakeParser
    class Parser(FakeParser):
        def parse(self,source,filename):
            self.calls+=1
            return ParsedDocument(fixture())
    parser=Parser(); store=JsonArtifactStore(tmp_path)
    ingest=IngestDocument(parser,store,WordCounter(),splitter())
    old=ingest.execute(b'book','book.pdf','book')
    new=ingest.execute(b'book','book.pdf','book',heading_scheme='declared-v1')
    again=ingest.execute(b'book','book.pdf','book',heading_scheme='declared-v1')
    assert parser.calls==1 and old.parse_version==new.parse_version
    assert old.chunk_version!=new.chunk_version and again.chunk_version==new.chunk_version
    stored=store.load_chunks('book',new.chunk_version)
    assert stored.manifest['config']['chunk']['heading_scheme']=='declared-v1'
    assert any(c.section_path==['Chapter 1','1. Basics'] for c in stored.result.chunks)


def test_declared_guard_is_falsifiable_when_disabled(monkeypatch):
    import doc2roadmap.domain.chunking as chunking
    monkeypatch.setattr(chunking,'_validate_declared_hierarchy',lambda nodes:None)
    with pytest.raises(pytest.fail.Exception):
        test_declared_tree_rejects_missing_noninteger_or_skipped_parent_depth([1,3])


def test_declared_tree_rejects_empty_heading():
    with pytest.raises(ValueError,match='declared'):
        execute(DocumentTree(nodes=[DocumentNode('section_header','  ',0,level=1)]))


def test_cache_guard_catches_omitted_hierarchy_mode(monkeypatch,tmp_path):
    import importlib
    module=importlib.import_module('doc2roadmap.application.use_cases.ingest_document')
    original=module._hash
    def broken(value):
        if isinstance(value,dict) and 'chunk' in value:
            value={**value,'chunk':{k:v for k,v in value['chunk'].items() if k!='heading_scheme'}}
        return original(value)
    monkeypatch.setattr(module,'_hash',broken)
    with pytest.raises(AssertionError):
        test_explicit_mode_has_separate_chunk_cache_and_reuses_parse(tmp_path/'mutation')
