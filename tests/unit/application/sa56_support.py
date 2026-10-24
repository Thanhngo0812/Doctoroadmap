"""Shared fixtures for the SA-56 focus tests and the pre-change baseline recorder."""
from copy import deepcopy
from types import SimpleNamespace as NS

from doc2roadmap.application.phase_b.assistant import AssistantUseCase
from doc2roadmap.application.phase_b.lectures import LectureUseCase
from doc2roadmap.application.ports.phase_b import Delta, Done, ToolCall
from doc2roadmap.domain.learning_graph import LearningGraph
from doc2roadmap.domain.scope import module_scope
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore

DEF_SONG = 'Song ánh là ánh xạ vừa đơn ánh vừa toàn ánh.'
DEF_DON = 'Đơn ánh là ánh xạ không gán hai phần tử khác nhau cùng một ảnh.'


def make_graph():
    chunks = [
        NS(chunk_id='c1', text='Ma trận là bảng các số. Mỗi hàng có cùng số cột.', page=1, char_start=0,
           char_end=48, section_path=['Ma trận'], order_index=0, role='noi_dung'),
        NS(chunk_id='c2', text='Định thức là số gắn với ma trận vuông. Định thức dùng ma trận vuông.', page=2,
           char_start=49, char_end=120, section_path=['Định thức'], order_index=1, role='noi_dung'),
        NS(chunk_id='c3', text=DEF_DON + ' Ví dụ: hàm x -> 2x.', page=3, char_start=121, char_end=200,
           section_path=['Ánh xạ'], order_index=2, role='noi_dung'),
        NS(chunk_id='c4', text=DEF_SONG + ' Song ánh có ánh xạ ngược.', page=4, char_start=201, char_end=270,
           section_path=['Ánh xạ'], order_index=3, role='noi_dung'),
    ]
    nodes = [
        {'node_id': 'a', 'name': 'Ma trận', 'learnable': True, 'module_id': 'm1', 'teaching_chunk_ids': ['c1']},
        {'node_id': 'e', 'name': 'Đơn ánh', 'learnable': True, 'module_id': 'm3', 'teaching_chunk_ids': ['c3'],
         'anchor': {'chunk_id': 'c3', 'sentence': DEF_DON}},
        {'node_id': 'f', 'name': 'Song ánh', 'learnable': True, 'module_id': 'm3', 'teaching_chunk_ids': ['c4'],
         'display_prerequisites': ['e'], 'anchor': {'chunk_id': 'c4', 'sentence': DEF_SONG}},
        {'node_id': 'b', 'name': 'Định thức', 'learnable': True, 'module_id': 'm2',
         'display_prerequisites': ['a'], 'teaching_chunk_ids': ['c2']},
        {'node_id': 'x', 'name': 'Khái niệm nhắc qua', 'learnable': False, 'module_id': 'm1'}]
    payload = {'doc_id': 'book', 'nodes': nodes,
               'modules': [{'module_id': 'm1', 'index': 0, 'title': 'Ma trận', 'node_ids': ['a']},
                           {'module_id': 'm2', 'index': 1, 'title': 'Định thức', 'node_ids': ['b']},
                           {'module_id': 'm3', 'index': 2, 'title': 'Ánh xạ', 'node_ids': ['e', 'f']}],
               'requires_edges': [
                   {'source': 'a', 'target': 'b', 'edge_type': 'requires', 'quote': 'Định thức dùng ma trận vuông.',
                    'chunk_ids': ['c2'], 'quote_chunk_id': 'c2'},
                   {'source': 'e', 'target': 'f', 'edge_type': 'requires', 'quote': 'Song ánh có ánh xạ ngược.',
                    'chunk_ids': ['c4'], 'quote_chunk_id': 'c4'}],
               'chunk_module_map': {'c1': {'module_id': 'm1'}, 'c2': {'module_id': 'm2'},
                                    'c3': {'module_id': 'm3'}, 'c4': {'module_id': 'm3'}}}
    return LearningGraph(payload, chunks)


class Model:
    """Scripted assistant model that records every message list it receives."""
    model_id = 'gemini-3.1-flash-lite'

    def __init__(self, turns):
        self.turns, self.calls, self.prompt, self.tools = iter(turns), [], None, None

    def start_session(self, prompt, tools):
        self.prompt, self.tools = prompt, tools
        return self

    def stream(self, messages, *, mode):
        self.calls.append((deepcopy(messages), mode))
        yield from next(self.turns)


def answer_turn(text='Song ánh là ánh xạ vừa đơn ánh vừa toàn ánh. [S1]'):
    return [Delta(text), Done({'promptTokenCount': 100, 'candidatesTokenCount': 20})]


def session(store, g, scope_kind='m3', session_id='s', owner='alice'):
    scope = {'kind': 'roadmap'} if scope_kind == 'roadmap' else module_scope(g, scope_kind)
    store.put_record('session', session_id, {
        'contract_version': 'session-1', 'session_id': session_id, 'owner': owner, 'doc_id': 'book',
        'scope': scope, 'title': 'Phiên học mới', 'title_source': 'rule',
        'created_at': '2026-10-18T00:00:00+00:00', 'updated_at': '2026-10-18T00:00:00+00:00',
        'turn_count': 0, 'last_question_preview': '', 'artifact_refs': [],
        'state': {'reminded_node_ids': [], 'linked_node_ids': [], 'reminders_enabled': True}})


def build(turns, *, scope_kind='m3', lecture=None, store=None, settings=None, graph=None):
    g = graph or make_graph()
    store = store or InMemoryPhaseBStore()
    session(store, g, scope_kind)
    model = Model(turns)
    return AssistantUseCase(g, store, model, lecture=lecture, settings=settings), model, store, g


def record(question, *, turns, scope_kind='m3', prior=None, dry_run=False, **kwargs):
    """Run one scenario and return the observable inputs and outputs of the model."""
    use_case, model, store, g = build(turns, scope_kind=scope_kind)
    if prior:
        use_case.ask('book', 1, 's', prior, owner='alice', allow_spend=True)
        model.calls.clear()
        model.turns = iter(turns)
    result = use_case.ask('book', 1, 's', question, owner='alice', allow_spend=True, dry_run=dry_run, **kwargs)
    if dry_run:
        return {'dry_run': {key: result[key] for key in
                            ('calls_estimate', 'usd_estimate', 'embedding_calls_estimate', 'context_hash')}}
    return {'prompt': model.prompt, 'tools': model.tools,
            'calls': [{'messages': messages, 'mode': mode} for messages, mode in model.calls],
            'linked_node_ids': result['linked_node_ids'], 'graph_cards': result['graph_cards'],
            'status': result['status'], 'answer_md': result['answer_md'], 'sources': result['sources'],
            'tool_calls': [row['name'] for row in result['tool_calls']]}


def scenarios(extra=None):
    """Representative questions asked without a focus; the baseline fixture pins their model input."""
    extra = extra or {}
    tool_turns = [[ToolCall('lookup_concept', {'name': 'Song ánh'}, '1'), Done({})], answer_turn()]
    return {
        'named': record('Song ánh là gì?', turns=[answer_turn()], **extra),
        'unnamed': record('giải thích phần này', turns=[answer_turn()], **extra),
        'tools': record('Song ánh là gì?', turns=tool_turns, **extra),
        'followup': record('còn cái kia thì sao?', turns=[answer_turn()], prior='Song ánh là gì?', **extra),
        'roadmap': record('Định thức là gì?', turns=[answer_turn('Định thức dùng ma trận vuông. [S1]')],
                          scope_kind='roadmap', **extra),
        'dry_module': record('Song ánh là gì?', turns=[], dry_run=True, **extra),
        'dry_unnamed': record('giải thích phần này', turns=[], dry_run=True, **extra),
        'dry_roadmap': record('Định thức là gì?', turns=[], scope_kind='roadmap', dry_run=True, **extra),
    }


def lecture_keys(settings=None):
    g = make_graph()
    return {node_id: LectureUseCase(None, InMemoryPhaseBStore(), settings=settings).make(
        'book', 1, g, node_id, dry_run=True)['lecture_key'] for node_id in ('a', 'e', 'f', 'b')}
