import re
from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace as NS

import pytest

from doc2roadmap.application.phase_b.assistant import AssistantUseCase
from doc2roadmap.application.ports.phase_b import Delta, Done, ToolCall
from doc2roadmap.domain.learning_graph import LearningGraph
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.domain.scope import module_scope
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
    g = graph()
    seed_session(store, g, 'session', 'alice', 'm1')
    use_case = AssistantUseCase(g, store, model, settings=settings)
    result = use_case.ask('book', 1, 'session', 'Ma trận là gì?',
                          owner='alice', allow_spend=True, **kwargs)
    return result, store, use_case


def seed_session(store, g, session_id, owner, module_id):
    scope = {"kind": "module", "node_ids": list(g.modules[module_id]["node_ids"]),
             "module_id_at_creation": module_id, "graph_version_at_creation": getattr(g, "graph_version", 1)}
    store.put_record('session', session_id, {'contract_version': 'session-1', 'session_id': session_id,
        'owner': owner, 'doc_id': 'book', 'scope': scope, 'title': 'Phiên học mới',
        'title_source': 'rule', 'created_at': '2026-10-18T00:00:00+00:00',
        'updated_at': '2026-10-18T00:00:00+00:00', 'turn_count': 0,
        'last_question_preview': '', 'artifact_refs': [],
        'state': {'reminded_node_ids': [], 'linked_node_ids': [], 'reminders_enabled': True}})


def test_answer_one_call_has_grounded_citations_and_measured_usage():
    events = []
    model = Model([[Delta('Ma trận là bảng các số. [S1]'), Done({'promptTokenCount': 100,
                    'candidatesTokenCount': 20, 'thoughtsTokenCount': 7})]])
    result, store, _ = run(model, on_event=events.append)
    assert result['status'] == 'answered'
    assert result['sources'][0]['chunk_id'] == 'c1'
    assert 'Ma trận' in result['answer_md']
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


def test_assistant_uses_configured_quote_limit_in_the_why_here_tool():
    source = graph()
    quote = 'Định thức dùng ma trận vuông. ' * 6
    source.chunks['c2'].text = quote
    source.payload['requires_edges'][0]['quote'] = quote.strip()
    model = Model([[ToolCall('why_here', {'concept': 'b'}, '1'), Done({})],
                   [Delta('KHONG_DU'), Done({})]])
    store = InMemoryPhaseBStore()
    seed_session(store, source, 'session', 'alice', 'm2')
    use_case = AssistantUseCase(source, store, model,
                               settings=replace(BSettings(), quote_max_chars=80))
    use_case.ask('book', 1, 'session', 'Định thức', owner='alice', allow_spend=True)
    tool_result = model.calls[1][0][-1]['tool_results'][0]['result']
    citation = tool_result['prerequisites'][0]['citation']
    assert len(citation['quote']) <= 80
    assert quote[citation['char_start'] - 24:citation['char_end'] - 24] == citation['quote']
    # the pre-fetched context names the prerequisite (and where it is) but carries no quote of it
    first = model.calls[0][0][0]['text']
    assert 'tiên quyết: Ma trận (module 1, chưa học)' in first


def test_endless_tool_calls_force_none_on_third_round():
    model = Model([[ToolCall('lookup_concept', {'name': 'Ma trận'}, str(i)), Done({})] for i in range(5)])
    result, store, _ = run(model)
    assert result['status'] == 'failed' and result['failure']['retryable'] is True
    assert len(model.calls) == 3
    assert model.calls[-1][1] == 'NONE'
    assert len(store.usage_rows()) == 3


def test_seven_turn_prompt_keeps_only_six_recent_turns_within_history_cap():
    from doc2roadmap.application.phase_b.common import stable_json
    settings = replace(BSettings(), assistant_history_tokens=1000)
    model = Model([[Delta('Ma trận là bảng các số. [S1]'), Done({})] for _ in range(7)])
    store = InMemoryPhaseBStore()
    g = graph()
    seed_session(store, g, 'session', 'alice', 'm1')
    use_case = AssistantUseCase(g, store, model, settings=settings)

    for number in range(7):
        use_case.ask('book', 1, 'session', f'question-{number} ' + 'x' * 500,
                     owner='alice', allow_spend=True)

    text = model.calls[6][0][0]['text']
    block = text.split('Hội thoại trước:')[1].split('Câu hỏi của người học:')[0]
    history = [{'question': q, 'answer': a} for q, a in re.findall(r'Người học: (.*)\nTrợ lý: (.*)\n', block)]
    assert 'Người học đang mở module 1: Ma trận' in text
    assert len(history) == 6
    assert all(f'question-{number}' in row['question'] for number, row in zip((0, 1, 2, 3, 4, 5), history))
    assert len(stable_json(history)) // 3 <= settings.assistant_history_tokens
    assert len(use_case.sessions.list_turns('alice', 'session')) == 7


def test_tool_errors_are_structured_and_counted():
    model = Model([[ToolCall('delete_book', {}, '1'), Done({})],
                   [ToolCall('lookup_concept', {'name': 123}, '2'), Done({})],
                   [Delta('Ma trận là bảng các số. [S1]'), Done({})]])
    result, _, _ = run(model)
    assert result['usage']['invalid_tool_calls'] == 2
    assert 'error' in model.calls[1][0][-1]['tool_results'][0]['result']
    assert 'error' in model.calls[2][0][-1]['tool_results'][0]['result']


def test_document_scope_limit_survives_tool_result_and_final_answer():
    generated = []
    def document(**kwargs):
        generated.append(kwargs)
        return {'status': 'failed', 'reason': 'scope_too_large'}

    model = Model([[ToolCall('make_document', {'request': 'Ghi chú', 'scope': ['m1']}, '1'), Done({})],
                   [Delta('Tôi sẽ giúp bạn thu hẹp phạm vi.'), Done({})]])
    store = InMemoryPhaseBStore()
    g = graph()
    seed_session(store, g, 'session', 'alice', 'm1')
    result = AssistantUseCase(g, store, model, document=document).ask(
        'book', 1, 'session', 'Tạo ghi chú', owner='alice', allow_spend=True)
    tool_result = model.calls[1][0][-1]['tool_results'][0]['result']
    assert generated and tool_result['error']['code'] == 'scope_too_large'
    assert 'tối đa 5 module' in tool_result['error']['message']
    # the model is told, and what it writes is the answer; the code no longer replaces it
    assert result['status'] == 'answered' and result['answer_md'] == 'Tôi sẽ giúp bạn thu hẹp phạm vi.'


def test_document_daily_limit_is_preserved_as_a_code_written_message():
    model = Model([[ToolCall('make_document', {'request': 'Ghi chú', 'scope': ['m1']}, '1'), Done({})],
                   [Delta('Tạo tài liệu hoàn tất.'), Done({})]])
    store = InMemoryPhaseBStore()
    g = graph()
    seed_session(store, g, 'session', 'alice', 'm1')
    result = AssistantUseCase(g, store, model, document=lambda **kwargs: {
        'status': 'failed', 'reason': 'daily_limit'}).ask(
            'book', 1, 'session', 'Tạo ghi chú', owner='alice', allow_spend=True)
    tool_result = model.calls[1][0][-1]['tool_results'][0]['result']
    assert tool_result['error']['code'] == 'daily_limit'
    assert result['status'] == 'daily_limit'
    assert result['answer_md'].startswith('Tạo tài liệu hoàn tất.') and 'hết hạn mức chi hôm nay' in result['answer_md']


@pytest.mark.parametrize('answer', ['Ma trận là vũ trụ. [S999]', 'Ma trận là vũ trụ.',
                                    'KHONG_DU\nTôi không có đủ dữ liệu.'])
def test_ungrounded_looking_answers_are_returned_and_streamed_as_written(answer):
    events = []
    result, store, _ = run(Model([[Delta(answer), Done({})]]), on_event=events.append)
    assert result['status'] == 'answered' and result['answer_md'] == answer
    assert ''.join(event['text'] for event in events if event['event'] == 'delta') == answer
    assert store.get_record('assistant_validation', result['answer_id'])['words'] > 0


def test_budget_reserves_a_final_response_instead_of_starting_another_tool_round():
    settings = replace(BSettings(), assistant_max_usd=.000001)
    model = Model([[Delta('Ma trận là bảng các số. [S1]'), Done({})]])
    result, _, _ = run(model, settings=settings)
    assert model.calls == [] or model.calls[0][1] == 'NONE'
    assert result['status'] == 'failed' and result['failure']['reason_code'] == 'het_ngan_sach_cau'


def test_session_followup_idempotency_and_owner_isolation():
    model = Model([[Delta('Định thức dùng ma trận vuông. [S1]'), Done({})],
                   [Delta('Định thức dùng ma trận vuông. [S1]'), Done({})]])
    store = InMemoryPhaseBStore()
    g = graph()
    seed_session(store, g, 's', 'alice', 'm1')
    use_case = AssistantUseCase(g, store, model)
    first = use_case.ask('book', 1, 's', 'Định thức là gì?', owner='alice',
                         allow_spend=True, client_turn_id='1')
    replay = use_case.ask('book', 1, 's', 'Định thức là gì?', owner='alice',
                          allow_spend=True, client_turn_id='1')
    assert replay == first and len(model.calls) == 1
    second = use_case.ask('book', 1, 's', 'Còn cái kia thì sao?', owner='alice', allow_spend=True)
    assert second['linked_node_ids'] == ['b']
    assert not second['graph_cards'].get('reminders')
    other = use_case.session_state('book', 's', owner='bob')
    assert not other.get('turns')


def test_dry_run_never_calls_search_model_or_writes_store():
    store = InMemoryPhaseBStore()
    model = Model([])
    def forbidden(*args, **kwargs):
        raise AssertionError('dry run called search')
    g = graph()
    seed_session(store, g, 's', 'alice', 'm1')
    use_case = AssistantUseCase(g, store, model, search=forbidden)
    result = use_case.ask('book', 1, 's', 'Ma trận', owner='alice', dry_run=True)
    assert result['dry_run'] and not model.calls and not store.usage_rows()
    before = store.get_record('session', 's')
    assert before['turn_count'] == 0 and not store.list_records('turn') and not store.usage_rows()


def test_roadmap_session_searches_all_and_returns_roadmap_and_module_cards():
    g, store = graph(), InMemoryPhaseBStore()
    store.put_record('session', 'roadmap', {'contract_version': 'session-1', 'session_id': 'roadmap',
        'owner': 'alice', 'doc_id': 'book', 'scope': {'kind': 'roadmap'}, 'title': 'Phiên học mới',
        'title_source': 'rule', 'created_at': '2026-10-18T00:00:00+00:00',
        'updated_at': '2026-10-18T00:00:00+00:00', 'turn_count': 0,
        'last_question_preview': '', 'artifact_refs': [],
        'state': {'reminded_node_ids': [], 'linked_node_ids': [], 'reminders_enabled': True}})
    seen = []
    def search(query, **kwargs):
        seen.append(kwargs)
        return [{'chunk_id': 'c1', 'text': g.chunks['c1'].text, 'page': 1}]
    model = Model([[Delta('Ma trận là bảng các số. [S1]'), Done({})]])
    result = AssistantUseCase(g, store, model, search=search,
        concept_lookup=lambda query: {"matches": [{"node_id": "a"}]}).ask(
        'book', 1, 'roadmap', 'Ma trận', owner='alice', allow_spend=True)
    text = model.calls[0][0][0]['text']
    assert seen[0]['current_module_id'] is None and seen[0]['scope'] == 'ca_tai_lieu'
    assert text.startswith('Người học đang xem cả lộ trình của cuốn sách.')
    assert [row['title'] for row in result['graph_cards']['roadmap']] == ['Ma trận', 'Định thức']
    assert not result['graph_cards']['reminders']
    assert result['linked_node_ids'] == ['a'] and result['status'] == 'answered'
    assert result['graph_cards']['module_cards'][0]['module_id'] == 'm1'


def test_assistant_requires_existing_owned_session_and_rejects_legacy_module_field():
    g, store = graph(), InMemoryPhaseBStore()
    use_case = AssistantUseCase(g, store, Model([]))
    with pytest.raises(KeyError):
        use_case.ask('book', 1, 'missing', 'Ma trận', owner='alice', dry_run=True)
    with pytest.raises(TypeError):
        use_case.ask('book', 1, 'missing', 'm1', 'Ma trận', owner='alice', dry_run=True)


def test_daily_limit_returns_code_written_answer_without_calling_model():
    from datetime import datetime, timezone
    g, store = graph(), InMemoryPhaseBStore()
    seed_session(store, g, 's', 'alice', 'm1')
    store.append_usage({'purpose': 'assistant', 'model_id': 'fake', 'doc_id': 'book',
        'learner_id': 'alice', 'cost_usd': 1.00, 'created_at': datetime.now(timezone.utc).isoformat()})
    model = Model([])
    result = AssistantUseCase(g, store, model).ask('book', 1, 's', 'Ma trận là gì?', owner='alice',
                                                   allow_spend=True)
    assert result['status'] == 'daily_limit'
    assert 'hôm nay' in result['answer_md']
    assert not model.calls and len(store.usage_rows()) == 1
    assert len(store.list_records('turn', owner='alice')) == 1
