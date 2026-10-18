from types import SimpleNamespace as NS

import pytest

from doc2roadmap.application.phase_b.common import call_json
from doc2roadmap.domain import phase_b_pricing as pricing
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore
from doc2roadmap.application.phase_b.assistant import AssistantUseCase
from doc2roadmap.application.phase_b.documents import DocumentUseCase
from doc2roadmap.domain.learning_graph import LearningGraph


@pytest.fixture
def graph():
    text = 'CSDL là dữ liệu có cấu trúc.'
    chunks = [NS(chunk_id=f'c{i}', text=text, page=i, char_start=(i - 1) * 100,
        char_end=(i - 1) * 100 + len(text), section_path=['Dữ liệu'], order_index=i,
        role='noi_dung') for i in range(1, 6)]
    payload = {'doc_id': 'book', 'nodes': [
        {'node_id': 'n', 'name': 'CSDL', 'aliases': ['Cơ sở dữ liệu'], 'learnable': True,
         'module_id': 'm', 'teaching_chunk_ids': ['c1'],
         'anchor': {'chunk_id': 'c1', 'sentence': text}},
        {'node_id': 's', 'name': 'Supervised learning', 'aliases': ['Học có giám sát'],
         'learnable': True, 'module_id': 'm', 'teaching_chunk_ids': ['c1']}],
        'modules': [{'module_id': 'm', 'index': 0, 'title': 'Dữ liệu', 'node_ids': ['n', 's']}],
        'requires_edges': [], 'sequence': ['n', 's']}
    graph = LearningGraph(payload, chunks)
    for chunk in chunks:
        graph.sources.label(chunk.chunk_id, 'S')
    return graph


def checked(graph, text):
    return AssistantUseCase(graph, InMemoryPhaseBStore(), None)._checked_answer(graph, text)


def seed_assistant_session(store, graph, session_id, owner):
    store.put_record('session', session_id, {'contract_version': 'session-1', 'session_id': session_id,
        'owner': owner, 'doc_id': graph.doc_id, 'scope': {'kind': 'module', 'node_ids': ['n', 's'],
        'module_id_at_creation': 'm', 'graph_version_at_creation': getattr(graph, 'graph_version', 1)},
        'title': 'Phiên học mới', 'title_source': 'rule', 'created_at': '2026-10-18T00:00:00+00:00',
        'updated_at': '2026-10-18T00:00:00+00:00', 'turn_count': 0,
        'last_question_preview': '', 'artifact_refs': [],
        'state': {'reminded_node_ids': [], 'linked_node_ids': [], 'reminders_enabled': True}})


@pytest.mark.parametrize('citation', ['[S1].', '. [S1]'])
def test_sentence_citation_does_not_cover_next_numeric_claim(graph, citation):
    answer, citations, warnings, _ = checked(graph,
        'CSDL có cấu trúc' + citation + ' Một hệ quản trị có đúng 7 thành phần.')
    assert 'CSDL có cấu trúc' in answer
    assert '7 thành phần' not in answer
    assert len(citations) == 1
    assert any(row['kind'] == 'unsourced_sentence' for row in warnings)


@pytest.mark.parametrize('labels', ['[S1, S5, S999]', '[S1; S5; S999]', '[S1][S5][S999]'])
def test_compound_real_and_fake_labels_are_checked_individually(graph, labels):
    answer, citations, warnings, _ = checked(graph, 'CSDL có cấu trúc ' + labels + '.')
    assert 'S999' not in answer
    assert {row['label'] for row in citations} == {'S1', 'S5'}
    assert any(row['kind'] == 'unknown_label' for row in warnings)


def test_short_connector_is_kept_but_short_concept_claim_is_not(graph):
    answer, _, warnings, _ = checked(graph,
        'CSDL có cấu trúc [S1]. Tiếp theo. CSDL gồm các bảng.')
    assert 'Tiếp theo.' in answer
    assert 'gồm các bảng' not in answer
    assert any(row['kind'] == 'unsourced_sentence' for row in warnings)


@pytest.mark.parametrize('body', ['Supervised learning là một nhánh của học máy.',
    'Học có giám sát nghĩa là học từ dữ liệu gắn nhãn.',
    'Supervised   learning là một nhánh của học máy.',
    'CSDL (cơ sở dữ liệu) là tập hợp dữ liệu.',
    'Cơ sở dữ liệu (CSDL) là tập hợp dữ liệu.',
    'Supervised learning được gọi là học từ ví dụ.'])
def test_outside_definition_of_in_scope_name_or_alias_is_removed(graph, body):
    answer, _, warnings, outside_count = checked(graph,
        'CSDL có cấu trúc [S1].\n:::outside_document\n' + body + '\n:::')
    assert body not in answer
    assert outside_count == 0
    assert any(row['kind'] == 'outside_document_removed' for row in warnings)


def make_document(graph, markdown, outside=None):
    class Model:
        model_id = pricing.GENERATION_MODEL

        def ask_json(self, prompt, *, response_schema):
            return NS(payload={'title': 'Dữ liệu', 'markdown': markdown,
                'citations': [{'label': 'S1', 'quote': graph.chunks['c1'].text}],
                'outside_document_blocks': outside or []}, usage={})

    return DocumentUseCase(Model(), InMemoryPhaseBStore()).create(
        'book', 1, graph, 'Giải thích CSDL', 'n', owner='test', allow_spend=True)


def test_document_removes_uncited_definitions_and_fake_compound_labels_without_duplicate_h1(graph):
    document = make_document(graph, '# Dữ liệu\n\nCSDL có cấu trúc [S1, S999]. '
        'Supervised learning là học từ dữ liệu.\n\nCSDL có đúng 7 phần [S999].')
    assert document['status'] == 'ready'
    assert document['markdown'].count('# Dữ liệu') == 1
    assert 'Supervised learning' not in document['markdown']
    assert '7 phần' not in document['markdown']
    assert 'S999' not in document['markdown']
    assert {row['label'] for row in document['citations']} == {'S1'}
    assert document['postcheck']['unsourced_sentence'] == 2


def test_document_requires_a_retained_sourced_sentence_and_rejects_outside_definition(graph):
    document = make_document(graph, 'CSDL có đúng 7 phần.',
        ['Supervised learning là một nhánh của học máy.'])
    assert document['status'] == 'failed'
    assert document['outside_document_blocks'] == 0
    assert 'Supervised learning' not in document['markdown']


def test_markdown_heading_cannot_hide_an_unsourced_definition_or_numeric_claim(graph):
    document = make_document(graph, '# Dữ liệu\n\n## CSDL có đúng 7 phần\n\n'
        '## Supervised learning là một nhánh học máy\n\nCSDL có cấu trúc [S1].')
    assert document['status'] == 'ready'
    assert '7 phần' not in document['markdown']
    assert 'Supervised learning' not in document['markdown']
    assert document['postcheck']['unsourced_sentence'] == 2


def test_traverse_never_leaks_distinct_open_requires_edge(graph):
    graph.payload['requires_edges'] = [{'source': 'n', 'target': 's', 'edge_type': 'requires',
        'quote': 'CSDL có cấu trúc.', 'chunk_ids': ['c1']}]
    graph.payload['open_edges'] = [{'source': 'n', 'target': 'unknown', 'edge_type': 'requires',
        'quote': 'Một quan hệ khác.', 'chunk_ids': ['c2'], 'confirmed': True}]
    rows = graph.traverse('n', 'requires', 'out')['edges']
    assert [row['target'] for row in rows] == ['s']


def test_shared_price_change_reaches_assistant_and_document_plans_and_ledgers(graph, monkeypatch):
    from dataclasses import replace
    from doc2roadmap.application.ports.phase_b import Delta, Done
    from doc2roadmap.domain.phase_b_limits import BSettings

    usage = {'promptTokenCount': 1000, 'candidatesTokenCount': 200, 'thoughtsTokenCount': 50}
    class Model:
        model_id = pricing.GENERATION_MODEL

        def start_session(self, *args):
            return self

        def stream(self, *args, **kwargs):
            yield Delta('CSDL có cấu trúc [S1].')
            yield Done(usage)

        def ask_json(self, *args, **kwargs):
            return NS(payload={'title': 'Dữ liệu', 'markdown': 'CSDL có cấu trúc [S1].',
                'citations': [{'label': 'S1', 'quote': graph.chunks['c1'].text}],
                'outside_document_blocks': []}, usage=usage)

    settings = replace(BSettings(), assistant_max_usd=1, document_max_usd=1)
    store = InMemoryPhaseBStore()
    seed_assistant_session(store, graph, 's', 'local')
    assistant = AssistantUseCase(graph, store, Model(), settings=settings)
    documents = DocumentUseCase(Model(), store, settings=settings)
    first_a = assistant.ask('book', 1, 's', 'CSDL là gì?', dry_run=True)['usd_estimate']
    first_d = documents.create('book', 1, graph, 'Giải thích', 'n', owner='test', dry_run=True)['estimate_usd']
    old = pricing.PRICES_USD_PER_MILLION[pricing.GENERATION_MODEL]
    monkeypatch.setitem(pricing.PRICES_USD_PER_MILLION, pricing.GENERATION_MODEL,
        {key: value * 2 for key, value in old.items()})
    assert assistant.ask('book', 1, 's', 'CSDL là gì?', dry_run=True)['usd_estimate'] == pytest.approx(first_a * 2)
    assert documents.create('book', 1, graph, 'Giải thích', 'n', owner='test', dry_run=True)['estimate_usd'] == pytest.approx(first_d * 2)
    answer = assistant.ask('book', 1, 's', 'CSDL là gì?', allow_spend=True)
    document = documents.create('book', 1, graph, 'Giải thích', 'n', owner='test', allow_spend=True)
    expected = pricing.token_cost(pricing.GENERATION_MODEL, usage)
    assert answer['usage']['usd'] == pytest.approx(expected)
    assert document['usage']['cost_usd'] == pytest.approx(expected)
    assert all(row['cost_usd'] == pytest.approx(expected) for row in store.usage_rows())


def test_old_client_turn_cache_cannot_bypass_new_sentence_validator(graph):
    from doc2roadmap.application.ports.phase_b import Delta, Done
    from doc2roadmap.domain.phase_b_limits import context_hash

    class Model:
        model_id = pricing.GENERATION_MODEL
        calls = 0

        def start_session(self, *args):
            return self

        def stream(self, *args, **kwargs):
            self.calls += 1
            yield Delta('CSDL có cấu trúc [S1].')
            yield Done({})

    store, model = InMemoryPhaseBStore(), Model()
    store.put_record('answer', context_hash(['test', 'book', 's', 't']),
        {'answer': 'Một hệ quản trị có đúng 7 thành phần.', 'status': 'answered'})
    seed_assistant_session(store, graph, 's', 'test')
    use_case = AssistantUseCase(graph, store, model)
    answer = use_case.ask('book', 1, 's', 'CSDL là gì?', owner='test', client_turn_id='t', allow_spend=True)
    assert '7 thành phần' not in answer['answer']
    assert model.calls == 1
    assert use_case.ask('book', 1, 's', 'CSDL là gì?', owner='test', client_turn_id='t', allow_spend=True) == answer
    assert model.calls == 1


def test_shared_price_change_reaches_lecture_plan_and_billed_usage(graph, monkeypatch):
    import json
    from doc2roadmap.application.phase_b.lectures import LectureUseCase

    usage = {'promptTokenCount': 1000, 'candidatesTokenCount': 200, 'thoughtsTokenCount': 50}
    class Model:
        model_id = pricing.GENERATION_MODEL
        last_usage = usage
        last_finish_reason = 'STOP'

        def start_session(self, *args):
            return self

        def stream_json(self, *args, **kwargs):
            return iter([json.dumps({'bridges': [], 'explanation': [
                {'text': 'Dữ liệu được tổ chức có cấu trúc.', 'sources': ['S1'],
                 'quote': graph.chunks['c1'].text, 'outside_document': False},
                {'text': 'Các thông tin được lưu trữ cùng nhau.', 'sources': ['S1'],
                 'quote': graph.chunks['c1'].text, 'outside_document': False}],
                'example': [], 'contrasts': [], 'gaps': []})])

    store = InMemoryPhaseBStore()
    lectures = LectureUseCase(Model(), store)
    before = lectures.make('book', 1, graph, 'n', dry_run=True)['estimate_usd']
    old = pricing.PRICES_USD_PER_MILLION[pricing.GENERATION_MODEL]
    monkeypatch.setitem(pricing.PRICES_USD_PER_MILLION, pricing.GENERATION_MODEL,
        {key: value * 2 for key, value in old.items()})
    assert lectures.make('book', 1, graph, 'n', dry_run=True)['estimate_usd'] == pytest.approx(before * 2)
    result = lectures.make('book', 1, graph, 'n', allow_spend=True)
    assert result['status'] == 'ready'
    billed = [row for row in store.usage_rows() if row['purpose'] == 'lecture']
    assert len(billed) == 1
    assert result['usage']['cost_usd'] == billed[0]['cost_usd'] == pytest.approx(pricing.token_cost(Model.model_id, usage))


def test_shared_prices_change_common_dry_run_and_measured_ledger(monkeypatch):
    monkeypatch.setitem(pricing.PRICES_USD_PER_MILLION, pricing.GENERATION_MODEL, {'input': 2.0, 'output': 4.0})
    class Model:
        model_id = pricing.GENERATION_MODEL

        def ask_json(self, prompt, *, response_schema):
            return NS(payload={'ok': True}, usage={'promptTokenCount': 1000,
                'candidatesTokenCount': 200, 'thoughtsTokenCount': 50})

    store = InMemoryPhaseBStore()
    options = dict(response_schema={}, store=store, purpose='assistant', doc_id='book', context_hash='x', learner_id='test')
    result = call_json(Model(), 'abc', allow_spend=True, **options)
    assert result.cost_usd == pytest.approx(0.003)
    assert store.usage_rows()[0]['cost_usd'] == pytest.approx(0.003)
    plan = call_json(Model(), 'abc', dry_run=True, **options)
    assert plan.cost_usd == pytest.approx(pricing.estimate_cost(pricing.GENERATION_MODEL,
        plan.usage['estimated_input_tokens'], plan.usage['estimated_output_tokens']))


def test_embedding_suffix_uses_verified_embedding_price(monkeypatch):
    assert pricing.embedding_cost('gemini-embedding-001:768', 1_000_000) == pytest.approx(0.15)
    monkeypatch.setitem(pricing.PRICES_USD_PER_MILLION, pricing.EMBEDDING_MODEL, {'input': 0.9, 'output': 0})
    assert pricing.embedding_cost('gemini-embedding-001:768', 1000) == pytest.approx(0.0009)
