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
    return AssistantUseCase(graph, InMemoryPhaseBStore(), model, **kwargs).ask(
        'book', 1, 'session', 'm1', 'Ma trận', owner='alice', allow_spend=True)


def test_ambiguous_lecture_tool_is_an_error_and_does_not_call_lecture_callback():
    callback_calls = []
    def lecture(**kwargs):
        callback_calls.append(kwargs)
        return {'lecture_key': 'lecture', 'node_id': 'a', 'sections': []}

    model = Model([
        [ToolCall('get_lecture', {'concept': 'Ma trận'}, '1'), Done({})],
        [Delta('KHONG_DU\nKhông đủ dữ liệu.'), Done({})],
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
    assert result['citations'] == []
    assert result['created_artifacts'] == [{'kind': 'quiz', 'id': 'attempt-1'}]
    assert result['answer'] == 'Đã tạo nội dung theo yêu cầu. Bạn có thể mở bằng liên kết đính kèm.'
    assert result['tool_calls'][0]['result_summary'] == {
        'artifact': {'kind': 'quiz', 'id': 'attempt-1'}, 'count': 5}


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
        [Delta('KHONG_DU\nKhông đủ dữ liệu.'), Done({})],
    ])
    result = ask(graph, model, lecture=lecture)
    item = result['tool_calls'][0]['result_summary']['items'][0]
    assert item['citations'][0]['label'] == 'S2'
    assert item['text'] == 'Ma trận được trình bày tại [S2].'
    assert cached == cached_before


def test_assistant_never_accepts_generated_formulas_and_keeps_only_one_outside_block():
    model = Model([[Delta('Ma trận là bảng các số. [S1]\nx = 1 [S1]\n'
                          ':::outside_document\nVí dụ về hộp đồ chơi.\n:::\n'
                          ':::outside_document\nVí dụ thứ hai.\n:::'), Done({})]])
    result = ask(make_graph(), model)
    assert 'x = 1' not in result['answer']
    assert 'Ví dụ về hộp' in result['answer'] and 'Ví dụ thứ hai' not in result['answer']
    assert result['outside_document_blocks'] == 1


def test_formula_tool_reference_is_reversible_and_preserves_cached_lecture():
    cached = {'lecture_key': 'key', 'node_id': 'a', 'status': 'ready', 'definition': {
        'formula_refs': [{'label': 'CT1', 'formula_id': 'f', 'occurrence_id': 'f@p2:r1',
                          'image_ref': 'images/image.png', 'media_id': 'image', 'page': 2}]},
        'sections': [{'items': [{'text': 'Xem ảnh gốc [CT1].', 'formula_labels': ['CT1'], 'citations': []}]}]}
    model = Model([[ToolCall('get_lecture', {'concept': 'a'}, '1'), Done({})],
                   [Delta('Xem ảnh gốc [CT1].'), Done({})]])
    result = ask(make_graph(), model, lecture=lambda **kwargs: cached)
    assert result['status'] == 'answered'
    assert result['formula_refs'][0]['occurrence_id'] == 'f@p2:r1'
    assert result['tool_calls'][0]['result_summary']['formula_refs'][0]['media_id'] == 'image'
    assert cached['definition']['formula_refs'][0]['label'] == 'CT1'
