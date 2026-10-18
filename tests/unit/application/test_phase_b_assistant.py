from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace as NS

import pytest

from doc2roadmap.application.phase_b.assistant import AssistantUseCase
from doc2roadmap.application.ports.phase_b import Delta, Done, ToolCall
from doc2roadmap.domain.learning_graph import LearningGraph
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore


def graph():
    chunks = [NS(chunk_id='c1', text='Ma trận là bảng các số.', page=1, char_start=0, char_end=23,
                 section_path=['Ma trận'], order_index=0, role='noi_dung'),
              NS(chunk_id='c2', text='Định thức dùng ma trận vuông.', page=2, char_start=24, char_end=51,
                 section_path=['Định thức'], order_index=1, role='noi_dung')]
    payload = {'doc_id': 'book', 'nodes': [
        {'node_id': 'a', 'name': 'Ma trận', 'learnable': True, 'module_id': 'm1', 'teaching_chunk_ids': ['c1']},
        {'node_id': 'b', 'name': 'Định thức', 'learnable': True, 'module_id': 'm2',
         'display_prerequisites': ['a'], 'teaching_chunk_ids': ['c2']}],
        'modules': [{'module_id': 'm1', 'index': 0, 'title': 'Ma trận', 'node_ids': ['a']},
                    {'module_id': 'm2', 'index': 1, 'title': 'Định thức', 'node_ids': ['b']}],
        'requires_edges': [{'source': 'a', 'target': 'b', 'edge_type': 'requires',
                           'quote': chunks[1].text, 'chunk_ids': ['c2'], 'quote_chunk_id': 'c2'}],
        'chunk_module_map': {'c1': {'module_id': 'm1'}, 'c2': {'module_id': 'm2'}}}
    return LearningGraph(payload, chunks)


class Model:
    model_id = 'gemini-3.1-flash-lite'

    def __init__(self, turns):
        self.turns, self.calls = iter(turns), []

    def start_session(self, prompt, tools):
        self.prompt, self.tools = prompt, tools
        return self

    def stream(self, messages, *, mode):
        self.calls.append((deepcopy(messages), mode))
        yield from next(self.turns)


def run(model, *, store=None, settings=None, **kwargs):
    store = store or InMemoryPhaseBStore()
    use_case = AssistantUseCase(graph(), store, model, settings=settings)
    result = use_case.ask('book', 1, 'session', 'm1', 'Ma trận là gì?',
                          owner='alice', allow_spend=True, **kwargs)
    return result, store, use_case


def test_answer_one_call_has_grounded_citations_and_measured_usage():
    events = []
    model = Model([[Delta('Ma trận là bảng các số. [S1]'), Done({'promptTokenCount': 100,
                    'candidatesTokenCount': 20, 'thoughtsTokenCount': 7})]])
    result, store, _ = run(model, on_event=events.append)
    assert result['status'] == 'answered'
    assert result['citations'][0]['chunk_id'] == 'c1'
    assert 'Ma trận' in result['answer']
    assert len(model.calls) == len(store.usage_rows()) == 1
    assert store.usage_rows()[0]['thought_tokens'] == 7
    assert any(event['event'] == 'delta' for event in events)


def test_each_assistant_round_records_its_own_first_content_delay(monkeypatch):
    from doc2roadmap.application.phase_b import assistant
    now = [0.0]
    monkeypatch.setattr(assistant, 'perf_counter', lambda: now[0])

    class Timed(Model):
        def stream(self, messages, *, mode):
            now[0] += .1 if not self.calls else .25
            yield from super().stream(messages, mode=mode)

    result, store, _ = run(Timed([
        [ToolCall('lookup_concept', {'name': 'Ma trận'}, '1'), Done({})],
        [Delta('Ma trận là bảng các số. [S1]'), Done({})]]))
    assert [row['ttft_ms'] for row in store.usage_rows()] == [100, 250]
    assert result['usage']['ttft_ms'] == 100


@pytest.mark.parametrize('recorded_ttft', [None, 0, 137])
def test_assistant_replay_retains_recorded_timing_without_measuring_replay_speed(monkeypatch, recorded_ttft):
    from doc2roadmap.application.phase_b import assistant
    monkeypatch.setattr(assistant, 'perf_counter', lambda: 0)
    model = Model([[Delta('Ma trận là bảng các số. [S1]'), Done({}, ttft_ms=recorded_ttft)]])
    model.is_replay = True
    _, store, _ = run(model)
    assert store.usage_rows()[0]['ttft_ms'] == recorded_ttft


def test_tool_result_is_supplied_to_next_turn_and_recorded():
    model = Model([[ToolCall('lookup_concept', {'name': 'Ma trận'}, '1'), Done({})],
                   [Delta('Ma trận là bảng các số. [S1]'), Done({})]])
    result, _, _ = run(model)
    assert len(model.calls) == 2
    tools = model.calls[1][0][-1]['tool_results']
    assert tools[0]['result']['matches'][0]['node_id'] == 'a'
    assert result['tool_calls'][0]['by'] == 'model'


def test_assistant_uses_configured_quote_limit_in_context_and_why_here_tool():
    import json
    source = graph()
    quote = 'Định thức dùng ma trận vuông. ' * 6
    source.chunks['c2'].text = quote
    source.payload['requires_edges'][0]['quote'] = quote.strip()
    model = Model([[ToolCall('why_here', {'concept': 'b'}, '1'), Done({})],
                   [Delta('KHONG_DU'), Done({})]])
    use_case = AssistantUseCase(source, InMemoryPhaseBStore(), model,
                               settings=replace(BSettings(), quote_max_chars=80))
    use_case.ask('book', 1, 'session', 'm2', 'Định thức', owner='alice', allow_spend=True)
    context = json.loads(model.calls[0][0][0]['text'])
    tool_result = model.calls[1][0][-1]['tool_results'][0]['result']
    for detail in (context['concepts'][0], tool_result):
        citation = detail['prerequisites'][0]['citation']
        assert len(citation['quote']) <= 80
        assert quote[citation['char_start'] - 24:citation['char_end'] - 24] == citation['quote']


def test_endless_tool_calls_force_none_on_fifth_round():
    model = Model([[ToolCall('lookup_concept', {'name': 'Ma trận'}, str(i)), Done({})] for i in range(5)])
    result, store, _ = run(model)
    assert result['status'] == 'budget_exhausted'
    assert len(model.calls) == 5
    assert model.calls[-1][1] == 'NONE'
    assert len(store.usage_rows()) == 5


def test_tool_errors_are_structured_and_counted():
    model = Model([[ToolCall('delete_book', {}, '1'), Done({})],
                   [ToolCall('lookup_concept', {'name': 123}, '2'), Done({})],
                   [Delta('Ma trận là bảng các số. [S1]'), Done({})]])
    result, _, _ = run(model)
    assert result['usage']['invalid_tool_calls'] == 2
    assert 'error' in model.calls[1][0][-1]['tool_results'][0]['result']
    assert 'error' in model.calls[2][0][-1]['tool_results'][0]['result']


@pytest.mark.parametrize('answer', ['Ma trận là vũ trụ. [S999]', 'Ma trận là vũ trụ.',
                                    'KHONG_DU\nTôi không có đủ dữ liệu.'])
def test_ungrounded_answers_become_refusals_and_never_stream_raw_claims(answer):
    events = []
    result, _, _ = run(Model([[Delta(answer), Done({})]]), on_event=events.append)
    assert result['status'] in {'not_in_document', 'insufficient_context'}
    assert 'vũ trụ' not in result['answer']
    assert not any('vũ trụ' in event.get('text', '') for event in events)


def test_budget_reserves_a_final_response_instead_of_starting_another_tool_round():
    settings = replace(BSettings(), assistant_max_usd=.000001)
    model = Model([[Delta('Ma trận là bảng các số. [S1]'), Done({})]])
    result, _, _ = run(model, settings=settings)
    assert model.calls == [] or model.calls[0][1] == 'NONE'
    assert result['status'] == 'budget_exhausted'


def test_session_followup_idempotency_and_owner_isolation():
    model = Model([[Delta('Định thức dùng ma trận vuông. [S1]'), Done({})],
                   [Delta('Định thức dùng ma trận vuông. [S1]'), Done({})]])
    store = InMemoryPhaseBStore()
    use_case = AssistantUseCase(graph(), store, model)
    first = use_case.ask('book', 1, 's', 'm1', 'Định thức là gì?', owner='alice',
                         allow_spend=True, client_turn_id='1')
    replay = use_case.ask('book', 1, 's', 'm1', 'Định thức là gì?', owner='alice',
                          allow_spend=True, client_turn_id='1')
    assert replay == first and len(model.calls) == 1
    second = use_case.ask('book', 1, 's', 'm1', 'Còn cái kia thì sao?', owner='alice', allow_spend=True)
    assert second['linked_node_ids'] == ['b']
    assert not second['graph_cards'].get('reminders')
    other = use_case.session_state('book', 's', owner='bob')
    assert not other.get('turns')


def test_dry_run_never_calls_search_model_or_writes_store():
    store = InMemoryPhaseBStore()
    model = Model([])
    def forbidden(*args, **kwargs):
        raise AssertionError('dry run called search')
    use_case = AssistantUseCase(graph(), store, model, search=forbidden)
    result = use_case.ask('book', 1, 's', 'm1', 'Ma trận', owner='alice', dry_run=True)
    assert result['dry_run'] and not model.calls and not store.usage_rows()
    assert not store.list_records('session')
