import json
from types import SimpleNamespace

import pytest

from doc2roadmap.application.spend_guard import SpendNotAllowed
from doc2roadmap.application.use_cases.label_chunk_roles import (
    LabelChunkRoles, _batches, _invalid_role, transfer_chunk_roles,
)
from doc2roadmap.domain.models import DocumentNode
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore
from tests.unit.domain.test_section_roles import chunk


class Model:
    model_id = 'fake'
    def __init__(self, broken=False):
        self.calls = []
        self.broken = broken
    def start_session(self, prompt):
        return self
    def ask_json(self, prompt, *, response_schema):
        rows = json.loads(prompt)['headings']
        self.calls.append(rows)
        labels = [{'index':r['index'],'role':'bai_tap' if r['title']=='练习' else 'noi_dung'} for r in rows]
        if self.broken:
            labels = [{'index':r['index'],'role':'invented'} for r in rows[:1]]
            labels += [{'index':rows[0]['index'],'role':'bai_tap'}, {'index':999,'role':'bai_tap'}]
        else:
            labels.append({'index':1,'role':'bai_tap'})  # Front matter is structurally locked.
        return SimpleNamespace(payload={'labels':labels},usage=None)


def stored(tmp_path):
    store = JsonArtifactStore(tmp_path)
    nodes = []
    for title in ('前言','第1章','练习','第2章','课程'):
        nodes += [DocumentNode('section_header',title,len(nodes),level=1),
                  DocumentNode('text','Text.',len(nodes)+1)]
    source = store.save_chunks('roles','source','config',{'chunk':{}},1,chunk(nodes))
    return store,source


def test_semantic_roles_one_call_cache_and_identity_preservation(tmp_path):
    store,base = stored(tmp_path)
    model = Model()
    uc = LabelChunkRoles(store,model,allow_spend=True)
    before = {p:p.read_bytes() for p in tmp_path.rglob('*.json')}
    assert uc.plan('roles',chunks_version=base.version).calls_estimate==2
    assert model.calls==[] and before=={p:p.read_bytes() for p in tmp_path.rglob('*.json')}
    labeled,reused = uc.execute('roles',chunks_version=base.version)
    assert not reused and len(model.calls)==2
    titles = {s.title:s for s in labeled.result.sections}
    assert titles['练习'].role=='bai_tap'
    assert titles['前言'].role=='mo_dau'
    assert titles['第2章'].role=='noi_dung'
    assert next(c for c in labeled.result.chunks if c.parent_section_id==titles['练习'].section_id).role=='bai_tap'
    assert next(c for c in labeled.result.chunks if c.parent_section_id==titles['课程'].section_id).role=='noi_dung'
    assert [{k:v for k,v in c.to_dict().items() if k!='role'} for c in base.result.chunks]==[
        {k:v for k,v in c.to_dict().items() if k!='role'} for c in labeled.result.chunks]
    assert store.load_chunks('roles',base.version).result==base.result
    assert store.load_role_chunks('roles',base.version).version==labeled.version
    assert uc.execute('roles')[1] and len(model.calls)==2
    assert uc.plan('roles').status=='reused'


def test_missing_duplicate_invalid_labels_default_to_content_with_warning(tmp_path):
    store,base = stored(tmp_path)
    artifact,_ = LabelChunkRoles(store,Model(broken=True),allow_spend=True).execute('roles')
    assert all(s.role=='noi_dung' for s in artifact.result.sections if s.role_source=='invalid_default')
    exercise = next(s for s in artifact.result.sections if s.title=='练习')
    assert exercise.role=='noi_dung' and exercise.role_source=='invalid_default'
    assert len(artifact.manifest['role_warnings'])>=3


def test_spend_guard_and_corrupt_metadata_are_not_silently_accepted(tmp_path):
    store,base = stored(tmp_path)
    model = Model()
    with pytest.raises(SpendNotAllowed):
        LabelChunkRoles(store,model).execute('roles')
    assert model.calls==[]
    artifact,_ = LabelChunkRoles(store,model,allow_spend=True).execute('roles')
    rows = json.loads((artifact.path/'chunks.json').read_text(encoding='utf-8'))
    rows[0]['text'] = 'changed source'
    store._write(artifact.path/'chunks.json',rows)
    with pytest.raises(ValueError,match='identity'):
        store.load_role_chunks('roles',base.version)


def test_batches_bound_size_and_keep_chapters_separate():
    sections = [SimpleNamespace(section_id=str(i),title=f'第{i//45+1}章' if i in (0,45) else f'主题 {i}',
                                level=1 if i in (0,45) else 2,order_index=i) for i in range(90)]
    batches = _batches(sections,set(range(90)))
    assert [len(group) for group in batches]==[40,5,40,5]
    assert all(max(group)-min(group)<45 for group in batches)


def test_after_last_chapter_is_its_own_batch():
    sections = [SimpleNamespace(section_id=str(i),title=title,level=level,order_index=i)
                for i,(title,level) in enumerate([('第1章',1),('内容',2),('第2章',1),('内容',2),
                                                   ('索引',1),('术语',2)])]
    assert _batches(sections,set(range(6)))==[[0,1],[2,3],[4,5]]


def test_structural_validation_rejects_impossible_roles_in_other_scripts():
    prose = ('Это длинная строка о линейной алгебре и векторном пространстве.\n'*40)
    assert _invalid_role('mo_dau',4,1,8,'short')=='front_after_chapter'
    assert _invalid_role('cuoi_sach',4,1,8,'short')=='back_before_last_chapter'
    assert _invalid_role('de_cuong',4,1,8,prose)=='long_prose'
    assert _invalid_role('hanh_chinh',4,1,8,prose)=='long_prose'
    assert _invalid_role('cuoi_sach',9,1,8,'索引 42\n概念 43\n空间 44') is None


def test_transfer_uses_majority_text_when_chunk_boundaries_change():
    old = [SimpleNamespace(chunk_id='old',text='alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu')]
    new = [SimpleNamespace(text='alpha beta gamma delta epsilon zeta eta theta iota',role='noi_dung'),
           SimpleNamespace(text='iota kappa lambda mu',role='bai_tap')]
    assert transfer_chunk_roles(old,new)=={'old':'noi_dung'}


def test_transfer_uses_reading_order_for_repeated_text():
    old = [SimpleNamespace(chunk_id='old',text='alpha beta gamma delta epsilon zeta eta theta')]
    new = [SimpleNamespace(text=old[0].text,role='noi_dung'),
           SimpleNamespace(text=old[0].text,role='bai_tap')]
    assert transfer_chunk_roles(old,new)=={'old':'noi_dung'}


def test_invalid_first_label_is_reasked_once_in_small_batch(tmp_path):
    store,base = stored(tmp_path)
    class RetryModel(Model):
        def ask_json(self,prompt,*,response_schema):
            rows = json.loads(prompt)['headings']
            self.calls.append(rows)
            role = 'mo_dau' if len(self.calls)==1 else 'noi_dung'
            return SimpleNamespace(payload={'labels':[{'index':r['index'],'role':role} for r in rows]},usage=None)
    model = RetryModel()
    labeled,_ = LabelChunkRoles(store,model,allow_spend=True).execute('roles',chunks_version=base.version)
    assert len(model.calls)==3  # two chapter batches, then one targeted retry
    assert len(model.calls[-1])==1
    assert labeled.manifest['role_validation_counts']['front_after_chapter']==1
    assert next(s for s in labeled.result.sections if s.title=='练习').role=='noi_dung'
