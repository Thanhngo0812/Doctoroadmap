import json
from types import SimpleNamespace

import pytest

from doc2roadmap.application.use_cases.anchor_concepts import AnchorConcepts
from doc2roadmap.application.use_cases.build_roadmap import BuildRoadmap
from doc2roadmap.domain.anchors import candidate_sentences
from doc2roadmap.domain.canonical import digest
from tests.unit.application.test_anchor_concepts import Store, Model, node
from tests.unit.application.test_build_roadmap import Store as RoadmapStore


def test_non_content_candidate_is_never_sent_and_outline_only_never_calls_model():
    store, model = Store(), Model()
    store.chunks.result.chunks[0].role = 'de_cuong'
    store.validated.payload['nodes'] = [node('cs', 'Cơ sở', ['c5']), node('only', 'Số chiều', ['c5'])]
    result, _ = AnchorConcepts(store, model).execute('doc', upstream=store.validated)
    assert [r['chunk_id'] for r in model.calls[0]['candidates']] == ['c40']
    assert len(model.calls) == 1
    by_id = {n['node_id']: n for n in result.payload['nodes']}
    assert by_id['only']['teaching_status'] == 'mentioned_only'
    assert by_id['only']['mentioned_in'] == 'de_cuong'
    assert by_id['only']['teaching_chunk_ids'] == []
    assert by_id['cs']['anchor']['chunk_id'] == 'c40'


def test_unicode_candidate_sentences_and_region_filter():
    chunks = [SimpleNamespace(chunk_id='a', order_index=0, role='de_cuong', text='向量空间：概述。'),
              SimpleNamespace(chunk_id='b', order_index=1, role='noi_dung', text='这是导言。向量空间具有加法。下一句。')]
    rows = candidate_sentences({'name':'向量空间'}, chunks)
    assert [(r['chunk_id'],r['sentence']) for r in rows] == [('b','向量空间具有加法。')]
    assert chunks[1].text[rows[0]['char_start']:].startswith(rows[0]['sentence'])


def test_content_name_match_outside_a6_mention_map_is_still_candidate():
    store=Store()
    store.chunks.result.chunks[0].role='de_cuong'
    store.chunks.result.chunks[1].text='Đa thức là một biểu thức đại số.'
    store.validated.payload['nodes']=[node('poly','Đa thức',['c5'])]
    store.validated.payload['mention_map']={}
    class Define:
        model_id='fixture-model'
        def start_session(self,prompt):
            return self
        def ask_json(self,prompt,*,response_schema):
            data=json.loads(prompt)
            candidate=data['candidates'][0]
            return SimpleNamespace(payload={'node_id':data['node_id'],'status':'defined_here',
                'anchor':candidate['cand_id'],'quote':'Đa thức','reason':'definition'},usage=None)
    artifact,_=AnchorConcepts(store,Define()).execute('doc',upstream=store.validated)
    assert artifact.payload['nodes'][0]['teaching_status']=='taught'
    assert artifact.payload['nodes'][0]['teaching_chunk_ids']==['c40']


def test_previous_verdict_is_reused_only_when_exact_model_input_is_unchanged():
    store,model=Store(),Model()
    store.validated.payload['nodes']=[node('cs','Cơ sở',['c5'])]
    previous,_=AnchorConcepts(store,model).execute('doc',upstream=store.validated)
    assert len(model.calls)==1
    config=previous.manifest['config']
    config['algorithm_id']='a10-teaching-anchor-v4'
    config['candidate_rule']='content-only+unicode-sentences+nfkc-latex-dash+a3+symbolic-v4'
    previous.manifest['config_hash']=digest(config)
    store.saved=[previous]
    store.checkpoints.clear()
    current,_=AnchorConcepts(store,model).execute('doc',upstream=store.validated)
    assert len(model.calls)==1
    assert current.version != previous.version
    assert current.payload['anchor_decision_log'][-1]['reused'] is True
    store.saved=[previous]
    store.checkpoints.clear()
    store.chunks.result.chunks[1].text+=' Cơ sở xuất hiện ở phần giảng mới.'
    AnchorConcepts(store,model).execute('doc',upstream=store.validated)
    assert len(model.calls)==2


class PriorModel:
    model_id = 'fixture-model'

    def __init__(self, confirmed):
        self.confirmed, self.calls = confirmed, []

    def start_session(self, prompt):
        return self

    def ask_json(self, prompt, *, response_schema):
        data = json.loads(prompt.split('\nCorrect this validation error:')[0])
        self.calls.append(data)
        if 'explicit_prior' in response_schema['properties']:
            assert set(data) == {'node_id','concept','quote'}
            assert 'FIRST-SECRET' not in json.dumps(data)
            value = {'node_id':data['node_id'],'explicit_prior':self.confirmed,'reason':'independent'}
        else:
            value = {'node_id':data['node_id'],'status':'prior_knowledge',
                     'quote':data['candidates'][0]['sentence'],'reason':'FIRST-SECRET'}
        return SimpleNamespace(payload=value, usage=None)


@pytest.mark.parametrize('confirmed,status', [(True,'prior_knowledge'),(False,'uncertain'),('invalid','uncertain')])
def test_prior_is_verified_independently_without_language_signals(confirmed, status):
    store, model = Store(), PriorModel(confirmed)
    store.validated.payload['nodes'] = [{'node_id':'v','name':'espace vectoriel','learnable':True,'defining_chunk_ids':['c5']}]
    store.chunks.result.chunks[0].text = "La connaissance préalable de l'espace vectoriel est nécessaire."
    uc = AnchorConcepts(store, model)
    result, _ = uc.execute('doc', upstream=store.validated)
    assert result.payload['nodes'][0]['teaching_status'] == status
    assert len(model.calls) >= 2
    assert any(set(call) == {'node_id','concept','quote'} for call in model.calls)
    before = len(model.calls)
    uc.execute('doc', upstream=store.validated)
    assert len(model.calls) == before


def test_roadmap_never_places_at_non_content_even_with_stale_anchor(tmp_path):
    store = RoadmapStore(tmp_path)
    for c in store.chunks.result.chunks:
        c.text = 'Alpha explanation.' if c.chunk_id == 'c6' else ''
        c.role = 'de_cuong' if c.chunk_id == 'c1' else 'noi_dung'
    a = store.validated.payload['nodes'][0]
    a.update(teaching_chunk_ids=['c1'], teaching_order_index=0, anchor={'chunk_id':'c1'})
    store.validated.payload['nodes'] = [a]
    store.validated.payload['requires_edges'] = []
    result, _ = BuildRoadmap(store).execute('doc', upstream=store.validated)
    assert result.payload['modules'][0]['title'] == '1.2 Tiếp theo'
