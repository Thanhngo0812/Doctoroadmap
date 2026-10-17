from copy import deepcopy
from types import SimpleNamespace as NS

import pytest

from doc2roadmap.application.phase_b.naming import NameModulesB
from doc2roadmap.domain.models import Chunk, ChunkingResult, Section
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore


class Store:
    def __init__(self):
        self.saved = []
        sections = [Section(f's{i}', 'book', title, 1, 1, None, [title], i)
                    for i, title in enumerate(['2.1 Ma trận', '2.2 Định thức', '2.3 Hệ phương trình'])]
        chunks = [Chunk(f'c{i}', 'book', i, 0, i + 1, 0, len(title), f's{i}', [title], 1,
                        ['text'], title, None, [], 10, 'test')
                  for i, title in enumerate(['Ma trận và hạng ma trận.', 'Định thức và tính chất định thức.',
                                            'Hệ phương trình và nghiệm.'])]
        self.chunks = NS(version=1, manifest={}, result=ChunkingResult('book', sections, chunks, ''))

    def load_role_chunks(self, *_):
        return self.chunks

    def load_chunks(self, *_):
        return self.chunks

    def find_graph(self, *_):
        return None

    def save_graph(self, doc_id, source_hash, config_hash, config, payload, **kwargs):
        item = NS(payload=payload, manifest={'config': config, 'config_hash': config_hash},
                  version=len(self.saved) + 1, path=None)
        self.saved.append(item)
        return item


def upstream():
    nodes = []
    modules = []
    for i, names in enumerate([['Ma trận', 'Hạng ma trận'], ['Định thức', 'Tính chất định thức'],
                               ['Hệ phương trình', 'Nghiệm']]):
        ids = [f'n{i}a', f'n{i}b']
        nodes.extend({'node_id': nid, 'name': 'Tính chất 3' if i == 0 and j else name,
                      'display_name': name, 'description': name, 'aliases': [], 'learnable': True,
                      'teaching_chunk_ids': [f'c{i}'], 'module_id': f'm{i}'}
                     for j, (nid, name) in enumerate(zip(ids, names)))
        modules.append({'module_id': f'm{i}', 'index': i, 'title': names[0], 'node_ids': ids,
                        'module_dependencies': [], 'title_section_ids': [f's{i}', f's{i}']})
    return NS(version=1, payload={'stage': 'stages', 'doc_id': 'book', 'nodes': nodes,
                                 'modules': modules, 'sequence': [n['node_id'] for n in nodes],
                                 'requires_edges': []},
              manifest={'config': {'chunks_version': 1}, 'config_hash': 'a10'})


class Model:
    model_id = 'gemini-3.1-flash-lite'

    def __init__(self, outputs):
        self.outputs = iter(outputs)
        self.calls = []

    def start_session(self, prompt):
        self.calls.append(prompt)
        return self

    def ask_json(self, prompt, *, response_schema):
        return NS(payload=next(self.outputs), usage={}, raw_text='')


def valid_outputs():
    return [{'title': title, 'description': [{'text': title, 'node_ids': [f'n{i}a']}]}
            for i, title in enumerate(['Ma trận', 'Định thức', 'Hệ phương trình'])]


def test_deterministic_naming_changes_only_presentation_and_uses_display_names():
    source = upstream()
    original = deepcopy(source.payload)
    result, _ = NameModulesB(Store(), deterministic=True).execute('book', upstream=source)
    assert result.payload['modules'][0]['title'] == 'Ma trận'
    assert result.payload['modules'][0]['section_code'] == '2.1'
    assert 'Tính chất 3' not in str(result.payload['modules'][0])
    for key in ('nodes', 'sequence', 'requires_edges'):
        assert result.payload[key] == original[key]
    for module in result.payload['modules']:
        assert module['description_source'] == 'template'
        assert all(set(sentence['node_ids']) <= set(module['node_ids']) for sentence in module['description'])


@pytest.mark.parametrize('bad', [
    {'title': 'Định thức', 'description': [{'text': 'Ma trận', 'node_ids': ['n0a']}]},
    {'title': 'Vũ trụ', 'description': [{'text': 'Ma trận', 'node_ids': ['n0a']}]},
    {'title': 'Ma trận', 'description': [{'text': 'Ma trận', 'node_ids': ['n1a']}]},
    {'title': '2.1 Ma trận', 'description': [{'text': 'Ma trận', 'node_ids': ['n0a']}]},
    {'title': 'Ma · trận', 'description': [{'text': 'Ma trận', 'node_ids': ['n0a']}]},
])
def test_invalid_model_naming_falls_back_without_changing_learning_graph(bad):
    model = Model([bad, *valid_outputs()[1:]])
    result, _ = NameModulesB(Store(), model, phase_b_store=InMemoryPhaseBStore(), allow_spend=True).execute(
        'book', upstream=upstream())
    module = result.payload['modules'][0]
    assert module['title'] == 'Ma trận'
    assert module['title_source'] == 'fallback'
    assert module['naming_flags']
    assert len(model.calls) == 3


def test_naming_cache_is_per_context_and_dry_run_never_writes_or_calls():
    model = Model(valid_outputs())
    phase_store = InMemoryPhaseBStore()
    graph_store = Store()
    use_case = NameModulesB(graph_store, model, phase_b_store=phase_store, allow_spend=True)
    source = upstream()
    plan = use_case.plan('book', upstream=source)
    assert plan.calls_estimate == 3
    assert not graph_store.saved and not model.calls and not phase_store.usage_rows()
    use_case.execute('book', upstream=source)
    source.version += 1
    use_case.execute('book', upstream=source)
    assert len(model.calls) == 3
    assert len(phase_store.usage_rows()) == 3


def test_prompt_and_validation_share_configured_character_limit():
    from dataclasses import replace
    from doc2roadmap.domain.phase_b_limits import BSettings
    settings = replace(BSettings(), title_max_chars=5)
    model = Model(valid_outputs())
    result, _ = NameModulesB(Store(), model, settings=settings,
                            phase_b_store=InMemoryPhaseBStore(), allow_spend=True).execute(
                                'book', upstream=upstream())
    assert all('5' in prompt for prompt in model.calls)
    assert all(module['title_source'] == 'fallback' for module in result.payload['modules'])


def test_overlong_author_heading_uses_complete_fallback_after_title_validation_failure():
    graph_store = Store()
    long_title = 'Quy luật sự phù hợp của quan hệ sản xuất với trình độ phát triển của lực lượng sản xuất'
    graph_store.chunks.result.sections[0].title = long_title
    model = Model([{'title': long_title, 'description': [{'text': 'Ma trận', 'node_ids': ['n0a']}]},
                   *valid_outputs()[1:]])
    use_case = NameModulesB(graph_store, model, phase_b_store=InMemoryPhaseBStore(), allow_spend=True)
    _, prepared = use_case._prepare('book', upstream())
    assert long_title in [item['title'] for item in prepared[0][2]['candidates']]
    result, _ = use_case.execute('book', upstream=upstream())
    title = result.payload['modules'][0]['title']
    assert title == 'Ma trận · Hạng ma trận'
    assert len(title) <= 60
    assert result.payload['modules'][0]['title_source'] == 'fallback'
    assert result.payload['modules'][0]['naming_flags'] == ['title_form']
    assert len(model.calls) == 3


def test_transport_failure_uses_fallback_and_keeps_other_modules_available():
    class Failing(Model):
        def ask_json(self, prompt, *, response_schema):
            if len(self.calls) == 1:
                raise RuntimeError('transport unavailable')
            return super().ask_json(prompt, response_schema=response_schema)
    model = Failing(valid_outputs()[1:])
    store = InMemoryPhaseBStore()
    result, _ = NameModulesB(Store(), model, phase_b_store=store, allow_spend=True).execute(
        'book', upstream=upstream())
    assert result.payload['modules'][0]['title'] == 'Ma trận'
    assert result.payload['modules'][0]['naming_flags'] == ['model_error']
    assert result.payload['modules'][1]['title_source'] == 'llm'
    assert len(store.usage_rows()) == 3
