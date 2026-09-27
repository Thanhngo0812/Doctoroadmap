import json
from types import SimpleNamespace

import pytest

from doc2roadmap.application.spend_guard import SpendNotAllowed
from doc2roadmap.application.use_cases.label_chunk_roles import LabelChunkRoles
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
    assert uc.plan('roles',chunks_version=base.version).calls_estimate==1
    assert model.calls==[] and before=={p:p.read_bytes() for p in tmp_path.rglob('*.json')}
    labeled,reused = uc.execute('roles',chunks_version=base.version)
    assert not reused and len(model.calls)==1
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
    assert uc.execute('roles')[1] and len(model.calls)==1
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
