import sys
from pathlib import Path
from types import SimpleNamespace
import pytest
sys.path.insert(0,str(Path('scripts/doc-nhe').resolve()))
import tach_nhan_cay_r16 as r16
from doc2roadmap.domain.models import DocumentNode, DocumentTree
from tests.conftest import WordCounter, splitter


def test_parent_projection_skips_removed_heading_without_reopening_branch():
    assert r16.project([-1,0,1,0,-1],[True,False,True,True,False])==[-1,0,0]


def test_same_leaf_wrong_ancestor_is_not_correct_path():
    def c(path): return SimpleNamespace(text='A meaningful body sentence',page=1,section_path=path)
    assert r16.path_score([c(['Root','Leaf'])],[c(['Wrong','Leaf'])])['hits']==0
    assert r16.path_score([c(['Root','Leaf'])],[c(['Root','Leaf'])])['hits']==1
    assert r16.path_score([c([])],[c([])])['hits']==0
    assert r16.path_score([c(['Root'])],[])['total']==1


def source():
    return DocumentTree(nodes=[DocumentNode('section_header','Chapter 1',0,level=1),
        DocumentNode('section_header','• not a heading',1,level=1),
        DocumentNode('paragraph','Body here.',2),
        DocumentNode('section_header','Repeated title',3,level=1),
        DocumentNode('paragraph','Body two.',4),
        DocumentNode('section_header','Repeated title',5,level=1),
        DocumentNode('paragraph','Body three.',6)])


def test_acceptance_replay_preserves_duplicate_headings_and_all_chunk_content():
    tree=source(); saved=tree.to_dict()
    before,keep,parents=r16.capture(tree,'test',WordCounter(),{'target_tokens':1})
    assert keep==[True,False,True,True]
    after=r16.chunking.chunk_document(r16.declared(tree,keep,parents),'test',WordCounter(),splitter(),
                                      target_tokens=1,heading_scheme='declared-v1')
    assert [r16.asdict(c) for c in before.chunks]==[r16.asdict(c) for c in after.chunks]
    assert tree.to_dict()==saved
    assert sum(s.title=='Repeated title' for s in after.sections)==2
    assert any('not a heading' in c.text for c in after.chunks)


def test_acceptance_guard_mutation_is_detected(monkeypatch):
    monkeypatch.setattr(r16.chunking,'_false_heading_reason',lambda *a,**kw:None)
    with pytest.raises(AssertionError):
        test_acceptance_replay_preserves_duplicate_headings_and_all_chunk_content()


def test_declared_depth_normalization_changes_only_legacy_level_field():
    tree=DocumentTree(nodes=[DocumentNode('section_header','1.2 Topic',0,level=2),
        DocumentNode('paragraph','Some body text.',1)])
    before,keep,parents=r16.capture(tree,'test',WordCounter(),{})
    after=r16.chunking.chunk_document(r16.declared(tree,keep,parents),'test',WordCounter(),splitter(),heading_scheme='declared-v1')
    assert before.chunks[0].heading_level==2 and after.chunks[0].heading_level==1
    assert [{**r16.asdict(c),'heading_level':len(c.section_path)} for c in before.chunks]==[r16.asdict(c) for c in after.chunks]
