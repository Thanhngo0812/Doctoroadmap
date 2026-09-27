from types import SimpleNamespace

import pytest

from doc2roadmap.domain.canonical import alias_kind
from doc2roadmap.domain.mentions import exact_mentions
from doc2roadmap.domain.retrieval import HybridRetriever, RetrievalDocument, _tokens


@pytest.mark.parametrize('name', ['Векторное пространство','向量空间','ベクトル空間','Διανυσματικός χώρος',
                                 'متجه','सदिश समष्टि','ปริภูมิเวกเตอร์'])
def test_names_are_words_in_any_script(name):
    assert alias_kind(name) == 'name'


@pytest.mark.parametrize('name', ['x','𝑇','ℳ','ₐ','ᵃ','ᵃᵇ','𝛼𝑇'])
def test_math_letters_and_scripts_are_not_words(name):
    assert alias_kind(name) == 'symbol'


def test_unspaced_mentions_are_substrings_but_latin_still_has_boundaries():
    nodes = [{'node_id':'v','name':'向量空间','learnable':True}, {'node_id':'s','name':'set','learnable':True}]
    chunks = [SimpleNamespace(chunk_id='a',text='我们在向量空间中。 A subset is not the full set.'),
              SimpleNamespace(chunk_id='b',text='subset')]
    assert exact_mentions(nodes,chunks,common_names=()) == {'a':{'v','s'}}


def test_bm25_chinese_bigram_and_legacy_latin_tokens():
    docs = [RetrievalDocument('a','我们学习向量空间。',(1.,)), RetrievalDocument('b','另一个主题。',(1.,))]
    assert [h.chunk_id for h in HybridRetriever(docs).search_bm25('向量')] == ['a']
    assert _tokens('Học máy, (Vector space) F(x)') == ['học','máy','(vector','space)','f(x)']
    assert _tokens('向') == ['向']
    assert _tokens('\uf097 Công thức 口 [formula]') == ['\uf097','công','thức','口','formula']


def test_a3_keeps_russian_name_without_latin_alias(tmp_path):
    from doc2roadmap.application.use_cases.extract_entities import ExtractEntities
    from tests.unit.application.test_a3_extract import _Extractor, _reply, _stored_document, _chunk

    text = 'Векторное пространство имеет операции сложения и умножения.'
    model = _Extractor([[_reply(entities=[{'name':'Векторное пространство','node_type':'concept',
        'description_draft':text,'evidence':text,'aliases':[]}]), _reply(),
        {'remove_entity_ids':[],'remove_edge_ids':[]}]])
    result = ExtractEntities(_stored_document(tmp_path, [_chunk(text)]), model, None,
                             generation={'temperature':0}).execute('book',max_workers=1).result
    assert [n.name for n in result.entities] == ['Векторное пространство']
    assert result.stats['rejected_symbol_only_name'] == 0


@pytest.mark.parametrize('rejected,rerun', [(['x'],False),(['Векторное пространство'],True)])
def test_a3_migrates_only_legacy_caches_whose_name_classification_changes(tmp_path,rejected,rerun):
    from doc2roadmap.application.use_cases.extract_entities import ExtractEntities
    from tests.unit.application.test_a3_extract import _Extractor, _reply, _stored_document, _chunk
    text = 'Vector space has vector addition.'
    responses = lambda: [_reply(entities=[{'name':'Vector space','node_type':'concept',
        'description_draft':text,'evidence':text,'aliases':[]}]),_reply(),{'remove_entity_ids':[],'remove_edge_ids':[]}]
    model = _Extractor([responses(),responses()])
    store = _stored_document(tmp_path,[_chunk(text)])
    uc = ExtractEntities(store,model,None,generation={'temperature':0})
    first = uc.execute('book',max_workers=1)
    artifact = store.load_candidates('book',first.artifact_version)
    manifest = dict(artifact.manifest)
    manifest.pop('text_rules')
    store._write(artifact.path/'manifest.json',manifest)
    payload = artifact.payload
    payload['stats']['rejected_symbol_only_names'] = rejected
    store._write(artifact.path/'candidates.json',payload)
    second = uc.execute('book',max_workers=1)
    assert second.reused is not rerun
    assert len(model.sessions)==(2 if rerun else 1)
    assert (second.artifact_version!=first.artifact_version) is rerun
    assert uc.execute('book',max_workers=1).reused


@pytest.mark.parametrize('name,text,changed', [('Alpha','Alpha nhắc Beta',False),('向量空间','我们在向量空间中',True)])
def test_mentions_config_changes_only_for_observably_changed_matches(name,text,changed):
    from doc2roadmap.application.use_cases.build_mentions import BuildMentions
    from tests.unit.application.test_build_mentions import Store, Embedding
    from doc2roadmap.domain.unicode_text import TEXT_RULE_VERSION
    store,embedding = Store(),Embedding()
    store.graph.payload['nodes'][0]['name'] = name
    store.chunks.result.chunks[0].text = text
    uc = BuildMentions(store,embedding)
    artifact,_ = uc.execute('doc')
    assert (artifact.manifest['config']['exact_normalization']==TEXT_RULE_VERSION) is changed
    before = len(embedding.calls)
    assert uc.plan('doc',upstream=store.graph).status=='reused'
    assert len(embedding.calls)==before
