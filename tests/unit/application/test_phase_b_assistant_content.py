"""Assistant regressions for generated-content tools and lecture citations."""
from copy import deepcopy
from types import SimpleNamespace as NS

from doc2roadmap.application.phase_b.assistant import AssistantUseCase
from doc2roadmap.application.ports.phase_b import Delta, Done, ToolCall
from doc2roadmap.domain.learning_graph import LearningGraph
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore


def make_graph(*, duplicate=False):
    chunks = [
        NS(chunk_id='c1', text='Ma trận là bảng các số.', page=1, char_start=0, char_end=23,
           section_path=['Ma trận'], order_index=0, role='noi_dung'),
        NS(chunk_id='c2', text='Định thức dùng ma trận vuông.', page=2, char_start=24, char_end=51,
           section_path=['Định thức'], order_index=1, role='noi_dung'),
    ]
    nodes = [
        {'node_id': 'a', 'name': 'Ma trận', 'learnable': True, 'module_id': 'm1', 'teaching_chunk_ids': ['c1']},
        {'node_id': 'b', 'name': 'Định thức', 'learnable': True, 'module_id': 'm2', 'teaching_chunk_ids': ['c2']},
    ]
    if duplicate:
        nodes.append({'node_id': 'c', 'name': 'Ma trận', 'learnable': True, 'module_id': 'm1',
                      'teaching_chunk_ids': ['c1']})
    payload = {
        'doc_id': 'book', 'nodes': nodes,
        'modules': [{'module_id': 'm1', 'index': 0, 'title': 'Ma trận', 'node_ids': ['a']},
                    {'module_id': 'm2', 'index': 1, 'title': 'Định thức', 'node_ids': ['b']}],
        'requires_edges': [],
        'chunk_module_map': {'c1': {'module_id': 'm1'}, 'c2': {'module_id': 'm2'}},
    }
    return LearningGraph(payload, chunks)


class Model:
    model_id = 'fake-model'

    def __init__(self, turns):
        self.turns = iter(turns)
        self.calls = []

    def start_session(self, prompt, tools):
        self.prompt, self.tools = prompt, tools
        return self

    def stream(self, messages, *, mode):
        self.calls.append((deepcopy(messages), mode))
        yield from next(self.turns)


def ask(graph, model, **kwargs):
    store = InMemoryPhaseBStore()
    store.put_record('session', 'session', {'contract_version': 'session-1', 'session_id': 'session',
        'owner': 'alice', 'doc_id': 'book', 'scope': {'kind': 'module', 'node_ids': ['a'],
        'module_id_at_creation': 'm1', 'graph_version_at_creation': 1}, 'title': 'Phiên học mới',
        'title_source': 'rule', 'created_at': '2026-10-18T00:00:00+00:00',
        'updated_at': '2026-10-18T00:00:00+00:00', 'turn_count': 0,
        'last_question_preview': '', 'artifact_refs': [],
        'state': {'reminded_node_ids': [], 'linked_node_ids': [], 'reminders_enabled': True}})
    return AssistantUseCase(graph, store, model, **kwargs).ask(
        'book', 1, 'session', 'Ma trận', owner='alice', allow_spend=True)


def test_ambiguous_lecture_tool_is_an_error_and_does_not_call_lecture_callback():
    callback_calls = []
    def lecture(**kwargs):
        callback_calls.append(kwargs)
        return {'lecture_key': 'lecture', 'node_id': 'a', 'sections': []}

    model = Model([
        [ToolCall('get_lecture', {'concept': 'Ma trận'}, '1'), Done({})],
        [Delta('Mình chưa xác định được khái niệm nào.'), Done({})],
    ])
    result = ask(make_graph(duplicate=True), model, lecture=lecture)
    tool_result = result['tool_calls'][0]['result_summary']
    assert tool_result['error']['code'] == 'tool_error'
    assert 'nhiều' in tool_result['error']['message']
    assert callback_calls == []


def test_successful_artifact_only_quiz_is_answered_without_source_claim():
    def quiz(**kwargs):
        return {'attempt_id': 'attempt-1', 'ready_count': 5, 'items': []}

    model = Model([
        [ToolCall('make_quiz', {'scope': 'Ma trận'}, '1'), Done({})],
        [Delta('Đã tạo quiz.'), Done({})],
    ])
    result = ask(make_graph(), model, quiz=quiz)
    assert result['status'] == 'answered'
    assert result['artifacts'] == [{'kind': 'quiz', 'id': 'attempt-1'}]
    assert result['answer_md'] == 'Đã tạo quiz.'  # the model's own words are kept
    assert result['tool_calls'][0]['result_summary'] == {
        'artifact': {'kind': 'quiz', 'id': 'attempt-1'}, 'count': 5}


def test_quiz_made_but_model_wrote_nothing_gets_a_code_written_note():
    model = Model([[ToolCall('make_quiz', {'scope': 'Ma trận'}, '1'), Done({})], [Done({})]])
    result = ask(make_graph(), model, quiz=lambda **kwargs: {'attempt_id': 'attempt-1', 'ready_count': 5, 'items': []})
    assert result['status'] == 'answered'
    assert result['answer_md'] == 'Đã tạo nội dung theo yêu cầu. Bạn có thể mở bằng liên kết đính kèm.'


def test_lecture_label_import_does_not_mutate_cache_and_rewrites_text_with_taken_s1():
    graph = make_graph()
    assert graph.sources.label('c1') == 'S1'
    cached = {'lecture_key': 'lecture-1', 'node_id': 'a', 'status': 'ready', 'sections': [
        {'items': [{'text': 'Ma trận được trình bày tại [S1].',
                    'citations': [{'label': 'S1', 'chunk_id': 'c2'}]}]}]}
    cached_before = deepcopy(cached)
    def lecture(**kwargs):
        return cached

    model = Model([
        [ToolCall('get_lecture', {'concept': 'a'}, '1'), Done({})],
        [Delta('Mình đã mở bài giảng cho bạn.'), Done({})],
    ])
    result = ask(graph, model, lecture=lecture)
    item = result['tool_calls'][0]['result_summary']['items'][0]
    assert item['citations'][0]['label'] == 'S2'
    assert item['text'] == 'Ma trận được trình bày tại [S2].'
    assert cached == cached_before


def test_assistant_keeps_generated_formulas_and_outside_examples_exactly_as_written():
    written = ('Ma trận là bảng các số. [S1]\nx = 1 [S1]\n'
               ':::outside_document\nVí dụ về hộp đồ chơi.\n:::\n'
               ':::outside_document\nVí dụ thứ hai.\n:::')
    model = Model([[Delta(written), Done({})]])
    result = ask(make_graph(), model)
    assert result['answer_md'] == written
    assert 'outside_document_blocks' not in result


def test_formula_tool_reference_is_reversible_and_preserves_cached_lecture():
    cached = {'lecture_key': 'key', 'node_id': 'a', 'status': 'ready', 'definition': {
        'formula_refs': [{'label': 'CT1', 'formula_id': 'f', 'occurrence_id': 'f@p2:r1',
                          'image_ref': 'images/image.png', 'media_id': 'image', 'page': 2}]},
        'sections': [{'items': [{'text': 'Xem ảnh gốc [CT1].', 'formula_labels': ['CT1'], 'citations': []}]}]}
    model = Model([[ToolCall('get_lecture', {'concept': 'a'}, '1'), Done({})],
                   [Delta('Xem ảnh gốc [CT1].'), Done({})]])
    result = ask(make_graph(), model, lecture=lambda **kwargs: cached)
    assert result['status'] == 'answered'
    assert result['tool_calls'][0]['result_summary']['formula_refs'][0]['occurrence_id'] == 'f@p2:r1'
    assert result['tool_calls'][0]['result_summary']['formula_refs'][0]['media_id'] == 'image'
    assert cached['definition']['formula_refs'][0]['label'] == 'CT1'
