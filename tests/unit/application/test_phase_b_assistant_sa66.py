"""SA-66: the `answer-3` tutor assistant. One test per invariant of doc/tro-ly-3-spec.md, with scripted models."""
import json
import re
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

from doc2roadmap.application.phase_b.assistant import AssistantUseCase
from doc2roadmap.application.ports.phase_b import Delta, Done, ToolCall
from doc2roadmap.domain.learning_graph import LearningGraph
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.domain.scope import module_scope
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore

SPEC = Path(__file__).resolve().parents[3] / 'doc' / 'tro-ly-3-spec.md'
DEF_SONG = 'Song ánh là ánh xạ vừa đơn ánh vừa toàn ánh.'
ANSWER = 'Song ánh là ánh xạ vừa đơn ánh vừa toàn ánh. [S1]'


def make_graph():
    texts = {
        'c1': 'Ma trận là bảng các số. Mỗi hàng có cùng số cột.',
        'c2': 'Định thức là số gắn với ma trận vuông. Định thức dùng ma trận vuông.',
        'c3': 'Đơn ánh là ánh xạ không gán hai phần tử khác nhau cùng một ảnh.',
        'c4': DEF_SONG + ' Song ánh có ánh xạ ngược.',
        'c5': 'Tích vô hướng của hai véctơ là [formula] trang năm.',
        'c6': 'Độ dài véctơ là [formula] trang sáu.',
        'c7': 'Góc giữa hai véctơ là [formula] trang bảy.',
        'c8': 'Hình chiếu của véctơ là [formula] trang tám.',
    }
    pages = {'c1': 1, 'c2': 2, 'c3': 3, 'c4': 4, 'c5': 5, 'c6': 6, 'c7': 7, 'c8': 8}
    chunks = [NS(chunk_id=cid, text=text, page=pages[cid], char_start=0, char_end=len(text),
                 section_path=['Chương 7', 'Mục ' + cid], order_index=number, role='noi_dung')
              for number, (cid, text) in enumerate(texts.items())]
    nodes = [
        {'node_id': 'a', 'name': 'Ma trận', 'learnable': True, 'module_id': 'm1', 'teaching_chunk_ids': ['c1']},
        {'node_id': 'b', 'name': 'Định thức', 'learnable': True, 'module_id': 'm2',
         'display_prerequisites': ['a'], 'teaching_chunk_ids': ['c2']},
        {'node_id': 'e', 'name': 'Đơn ánh', 'learnable': True, 'module_id': 'm3', 'teaching_chunk_ids': ['c3'],
         'anchor': {'chunk_id': 'c3', 'sentence': 'Đơn ánh là ánh xạ không gán hai phần tử khác nhau cùng một ảnh.'}},
        {'node_id': 'f', 'name': 'Song ánh', 'learnable': True, 'module_id': 'm3', 'teaching_chunk_ids': ['c4'],
         'display_prerequisites': ['e'], 'anchor': {'chunk_id': 'c4', 'sentence': DEF_SONG}},
        {'node_id': 'v', 'name': 'Tích vô hướng', 'learnable': True, 'module_id': 'm4', 'teaching_chunk_ids': ['c5']}]
    payload = {'doc_id': 'book', 'nodes': nodes,
               'modules': [{'module_id': 'm1', 'index': 0, 'title': 'Ma trận', 'node_ids': ['a']},
                           {'module_id': 'm2', 'index': 1, 'title': 'Định thức', 'node_ids': ['b']},
                           {'module_id': 'm3', 'index': 2, 'title': 'Ánh xạ', 'node_ids': ['e', 'f']},
                           {'module_id': 'm4', 'index': 3, 'title': 'Véctơ', 'node_ids': ['v']}],
               'requires_edges': [
                   {'source': 'a', 'target': 'b', 'edge_type': 'requires', 'quote': 'Định thức dùng ma trận vuông.',
                    'chunk_ids': ['c2'], 'quote_chunk_id': 'c2'},
                   {'source': 'e', 'target': 'f', 'edge_type': 'requires', 'quote': 'Song ánh có ánh xạ ngược.',
                    'chunk_ids': ['c4'], 'quote_chunk_id': 'c4'}],
               'chunk_module_map': {cid: {'module_id': {'c1': 'm1', 'c2': 'm2', 'c3': 'm3', 'c4': 'm3'}.get(cid, 'm4')}
                                    for cid in texts}}
    graph = LearningGraph(payload, chunks)
    graph.parse_version = 3
    return graph


class Model:
    """Scripted assistant model; records every message list and the system prompt."""
    model_id = 'gemini-3.1-flash-lite'

    def __init__(self, turns):
        self.turns, self.calls, self.prompt, self.tools = iter(turns), [], None, None

    def start_session(self, prompt, tools):
        self.prompt, self.tools = prompt, tools
        return self

    def stream(self, messages, *, mode):
        self.calls.append((list(messages), mode))
        turn = next(self.turns)
        yield from turn() if callable(turn) else turn


def turn(text=ANSWER):
    return [Delta(text), Done({'promptTokenCount': 100, 'candidatesTokenCount': 20})]


class Images:
    def __init__(self, pages=None):
        self.calls, self.pages = [], pages if pages is not None else {5, 6, 7, 8}

    def get(self, doc_id, parse_version, page):
        self.calls.append((doc_id, parse_version, page))
        return b'jpeg-%d' % page if page in self.pages else None


def search_for(*chunk_ids, seen=None):
    graph = make_graph()

    def search(query, **kwargs):
        if seen is not None:
            seen.append((query, kwargs))
        return [{'chunk_id': cid, 'text': graph.chunks[cid].text, 'page': graph.chunks[cid].page, 'score': 1.0}
                for cid in chunk_ids]
    return search


def seed(store, graph, scope_kind='m3', session_id='s', owner='alice'):
    scope = {'kind': 'roadmap'} if scope_kind == 'roadmap' else module_scope(graph, scope_kind)
    store.put_record('session', session_id, {
        'contract_version': 'session-1', 'session_id': session_id, 'owner': owner, 'doc_id': 'book',
        'scope': scope, 'title': 'Phiên học mới', 'title_source': 'rule',
        'created_at': '2026-10-18T00:00:00+00:00', 'updated_at': '2026-10-18T00:00:00+00:00',
        'turn_count': 0, 'last_question_preview': '', 'artifact_refs': [],
        'state': {'reminded_node_ids': [], 'linked_node_ids': [], 'reminders_enabled': True}})


def build(turns, *, scope_kind='m3', store=None, **kwargs):
    graph, store = make_graph(), store or InMemoryPhaseBStore()
    seed(store, graph, scope_kind)
    model = Model(turns)
    kwargs.setdefault('search', search_for('c4', 'c3'))
    return AssistantUseCase(graph, store, model, **kwargs), model, store


def ask(use_case, question='Song ánh là gì?', **kwargs):
    return use_case.ask('book', 1, 's', question, owner='alice', allow_spend=True, **kwargs)


def first_text(model, call=0):
    return model.calls[call][0][0]['text']


# 1 ------------------------------------------------------------ the first call already has everything
def test_first_model_call_carries_sources_concepts_prerequisites_roadmap_in_app_module_numbers():
    use_case, model, store = build([turn()], scope_kind='m2')
    result = ask(use_case, 'Song ánh là gì?')
    text = first_text(model)
    assert len(model.calls) == 1 and result['tool_calls'] == [] and len(store.usage_rows()) == 1
    assert 'Người học đang mở module 2: Định thức' in text
    assert 'Khái niệm liên quan: Song ánh (module 3: Ánh xạ)' in text
    assert 'tiên quyết: Đơn ánh (module 3, chưa học)' in text
    assert 'lộ trình: module 3: Ánh xạ' in text
    sources = text.split('Tư liệu từ sách:')[1]
    assert re.search(r'\[S1\] \(trang 4, mục Chương 7 > Mục c4\)\n' + re.escape(DEF_SONG), sources)
    assert text.rstrip().endswith('Câu hỏi của người học: Song ánh là gì?')


def test_roadmap_lists_modules_in_app_numbers_not_chapter_numbers_and_session_scope_is_stated():
    use_case, model, _ = build([turn()], scope_kind='m1')
    ask(use_case, 'Định thức là gì?')
    text = first_text(model)
    assert 'lộ trình: module 1: Ma trận; module 2: Định thức' in text
    assert 'Chương 7' in text and 'module 7' not in text  # section path is the book's; module numbers are the app's
    roadmap, model2, _ = build([turn()], scope_kind='roadmap')
    ask(roadmap, 'Định thức là gì?')
    assert first_text(model2).startswith('Người học đang xem cả lộ trình của cuốn sách.')


def test_learned_prerequisite_is_marked_as_learned():
    from doc2roadmap.application.phase_b.progress import ProgressUseCase
    use_case, model, store = build([turn()])
    ProgressUseCase(store, use_case.graph).set_progress('alice', 'book', 'e', True)
    ask(use_case)
    assert 'Đơn ánh (module 3, đã học)' in first_text(model)


# 2 ------------------------------------------------------------ the answer is the model's own words
def test_answer_keeps_every_word_while_the_checks_only_reach_the_log():
    written = ('Song ánh là ánh xạ vừa đơn ánh vừa toàn ánh. [S1]\n\n'
               'Một câu hoàn toàn không có nhãn nguồn nào cả đâu.\n\n$$f(x) = 2x + \\sum_i a_i$$ [S9]\n\n'
               'Ví dụ ngoài sách: một hộp đồ chơi với các khối hình.')
    events = []
    use_case, model, store = build([turn(written)])
    result = ask(use_case, on_event=events.append)
    assert result['answer_md'] == written and result['status'] == 'answered'
    assert ''.join(e['text'] for e in events if e['event'] == 'delta') == written  # what streamed is what is kept
    log = store.get_record('assistant_validation', result['answer_id'])
    assert log['unknown_labels'] == ['S9'] and log['labels_used'] == ['S1', 'S9']
    assert log['unsourced_sentences'] >= 2 and log['has_formula'] is True


# 3 ------------------------------------------------------------ never empty when the model wrote something
@pytest.mark.parametrize('written', ['KHONG_DU\nTôi không chắc về điều này.', 'KHONG_DU', 'Tài liệu chưa đủ bằng chứng.'])
def test_khong_du_and_refusal_looking_text_is_returned_as_written(written):
    use_case, _, _ = build([turn(written)])
    result = ask(use_case)
    assert result['status'] == 'answered' and result['answer_md'] == written


def test_no_text_at_all_is_a_failure_with_reason_and_retryable_and_is_not_kept_for_the_same_turn():
    events = []
    use_case, model, store = build([[Done({})], turn()])
    first = ask(use_case, client_turn_id='t1', on_event=events.append)
    assert first['status'] == 'failed' and first['answer_md'] == ''
    assert first['failure']['reason_code'] == 'khong_dung_duoc' and first['failure']['retryable'] is True
    assert events[-1]['event'] == 'failure'
    second = ask(use_case, client_turn_id='t1')  # "Thử lại" with the same client turn reaches the model again
    assert second['status'] == 'answered' and len(model.calls) == 2


def test_transport_error_before_any_text_is_a_retryable_failure():
    def broken():
        raise OSError('connection reset')
        yield  # pragma: no cover
    use_case, _, _ = build([broken])
    result = ask(use_case)
    assert result['status'] == 'failed' and result['failure']['reason_code'] == 'loi_mang'
    assert result['failure']['retryable'] is True and result['failure']['message']


def test_transport_error_after_some_text_keeps_the_text_as_answered():
    def cut():
        yield Delta('Song ánh là ánh xạ vừa đơn ánh vừa toàn ánh. [S1]')
        raise OSError('connection reset')
    use_case, _, store = build([cut])
    result = ask(use_case)
    assert result['status'] == 'answered' and result['answer_md'].startswith('Song ánh là')
    assert store.get_record('assistant_validation', result['answer_id'])['transport_error'] == 'OSError'


# 4 ------------------------------------------------------------ streaming
def test_first_chunk_reaches_the_caller_before_the_model_has_written_the_rest():
    events, seen_at_second = [], []

    def slow():
        yield Delta('Song ánh là ánh xạ ')
        seen_at_second.extend(e.get('text') for e in events if e['event'] == 'delta')
        yield Delta('vừa đơn ánh vừa toàn ánh. [S1]')
        yield Done({})
    use_case, _, _ = build([slow])
    result = ask(use_case, on_event=events.append)
    assert seen_at_second == ['Song ánh là ánh xạ ']
    assert result['answer_md'] == 'Song ánh là ánh xạ vừa đơn ánh vừa toàn ánh. [S1]'
    assert [e['event'] for e in events][-1] == 'final'


# 5 ------------------------------------------------------------ follow-ups and history
def test_short_followup_is_searched_together_with_the_question_before_it():
    seen = []
    use_case, _, _ = build([turn(), turn(), turn()], search=search_for('c4', seen=seen))
    ask(use_case, 'Song ánh là gì?')
    ask(use_case, 'còn đơn ánh thì sao?')
    ask(use_case, 'Hãy so sánh kỹ song ánh với đơn ánh về mặt định nghĩa và ví dụ minh hoạ nhé')
    assert seen[0][0] == 'Song ánh là gì?'
    assert seen[1][0] == 'Song ánh là gì? còn đơn ánh thì sao?'
    assert seen[2][0].startswith('Hãy so sánh kỹ') and 'Song ánh là gì?' not in seen[2][0]


def test_history_has_the_last_six_turns_with_their_answers_each_cut_to_1200_characters():
    use_case, model, _ = build([turn(f'Trả lời số {n}. ' + 'x' * 1500) for n in range(1, 9)])
    for n in range(1, 9):
        ask(use_case, f'Câu hỏi thứ {n} về song ánh?')
    text = first_text(model, 7)
    history = text.split('Hội thoại trước:')[1].split('Câu hỏi của người học:')[0]
    assert [int(n) for n in re.findall(r'Người học: Câu hỏi thứ (\d+)', history)] == [2, 3, 4, 5, 6, 7]
    answers = re.findall(r'Trợ lý: (Trả lời số \d+\. x+)', history)
    assert len(answers) == 6 and all(len(a) == 1200 for a in answers)  # answer present, and cut at 1200
    assert 'Câu hỏi thứ 1 ' not in history and 'Câu hỏi thứ 8' not in history


def test_history_total_stays_under_the_token_cap():
    settings = replace(BSettings(), assistant_history_tokens=500)
    use_case, model, _ = build([turn('y' * 3000) for _ in range(4)], settings=settings)
    for n in range(4):
        ask(use_case, f'Câu hỏi {n} về song ánh?')
    history = first_text(model, 3).split('Hội thoại trước:')[1].split('Câu hỏi của người học:')[0]
    assert len(history) // 3 <= 500 + 200  # the framing words are not part of the capped content


# 6 ------------------------------------------------------------ page pictures
def test_formula_passages_send_their_page_pictures_and_plain_ones_do_not():
    images = Images()
    use_case, model, _ = build([turn(), turn()], page_images=images, search=search_for('c5', 'c4'))
    ask(use_case, 'Tích vô hướng là gì?')
    sent = model.calls[0][0][0]['images']
    assert sent == [(5, b'jpeg-5')] and images.calls == [('book', 3, 5)]
    plain, model2, _ = build([turn()], page_images=Images(), search=search_for('c4', 'c3'))
    ask(plain)
    assert 'images' not in model2.calls[0][0][0]


def test_at_most_three_pictures_and_missing_pictures_are_skipped():
    use_case, model, _ = build([turn()], page_images=Images({5, 7, 8}), search=search_for('c5', 'c6', 'c7', 'c8'))
    ask(use_case, 'Véctơ là gì?')
    assert [page for page, _ in model.calls[0][0][0]['images']] == [5, 7]  # c6's page has no picture; limit 3 covers c5-c7


def test_pictures_are_kept_on_every_round_of_a_tool_turn():
    use_case, model, _ = build([[ToolCall('lookup_concept', {'name': 'Song ánh'}, '1'), Done({})], turn()],
                               page_images=Images(), search=search_for('c5'))
    ask(use_case, 'Tích vô hướng là gì?')
    assert model.calls[0][0][0]['images'] == model.calls[1][0][0]['images'] and model.calls[1][0][0]['images']


# 7 ------------------------------------------------------------ focus
def lecture_reader(body, calls):
    def reader(concept, **kwargs):
        calls.append(kwargs)
        return {'status': 'ready', 'body_md': body, 'lecture_key': 'k', 'node_id': concept}
    return reader


def test_focus_puts_the_cached_lecture_text_in_the_context_without_its_own_labels_and_without_generating():
    calls = []
    body = '### Song ánh\nSong ánh vừa đơn vừa toàn [S1]. Ví dụ với hàm bậc nhất [S2, S3].\n\n' + 'Ý thêm. ' * 400
    use_case, model, store = build([turn()], lecture=lecture_reader(body, calls))
    before = len(store.usage_rows())
    result = ask(use_case, 'giải thích phần này', focus_node_id='f')
    text = first_text(model)
    assert result['focus_node_id'] == 'f' and len(model.calls) == 1
    assert calls and all(call['cache_only'] is True and call['allow_spend'] is False for call in calls)
    assert 'Người học đang đọc bài giảng của khái niệm "Song ánh" (khái niệm 2/2 của module 3: Ánh xạ)' in text
    lecture_part = text.split('Bài giảng người học đang đọc')[1].split('Khái niệm liên quan:')[0]
    assert 'Song ánh vừa đơn vừa toàn.' in lecture_part and 'Ví dụ với hàm bậc nhất.' in lecture_part
    assert len(lecture_part.split('\n', 1)[1].strip()) <= BSettings().assistant_focus_chars
    # the lecture's [S1]/[S2] must not be mistaken for the assistant's own labels
    assert '[S2' not in lecture_part and '[S1' not in lecture_part
    assert len(re.findall(r'\[S1\]', text)) == 1
    assert [row['purpose'] for row in store.usage_rows()[before:]] == ['assistant']


def test_no_lecture_in_the_cache_leaves_the_focus_without_lecture_text_and_never_generates():
    calls = []

    def reader(concept, **kwargs):
        calls.append(kwargs)
        return {'status': 'not_cached', 'node_id': concept}
    use_case, model, _ = build([turn()], lecture=reader)
    ask(use_case, 'giải thích phần này', focus_node_id='f')
    assert 'Bài giảng người học đang đọc' not in first_text(model) and calls[0]['cache_only'] is True


def test_get_lecture_tool_result_has_its_labels_removed_before_the_model_reads_it():
    body = 'Song ánh vừa đơn vừa toàn [S1]. Ma trận có hàng và cột [S2].'
    use_case, model, _ = build([[ToolCall('get_lecture', {'concept': 'f'}, '1'), Done({})], turn()],
                               lecture=lecture_reader(body, []))
    ask(use_case)
    returned = model.calls[1][0][-1]['tool_results'][0]['result']
    assert returned['body_md'] == 'Song ánh vừa đơn vừa toàn. Ma trận có hàng và cột.'
    assert 'sources' not in returned


# 8 ------------------------------------------------------------ rounds
def test_at_most_three_rounds_and_the_last_one_must_answer_in_text():
    use_case, model, store = build([[ToolCall('lookup_concept', {'name': 'Song ánh'}, str(i)), Done({})]
                                    for i in range(6)])
    result = ask(use_case)
    assert len(model.calls) == 3 and [mode for _, mode in model.calls] == ['AUTO', 'AUTO', 'NONE']
    assert len(store.usage_rows()) == 3 and result['status'] == 'failed'
    assert result['failure']['retryable'] is True


def test_last_round_text_is_the_answer_after_two_tool_rounds():
    use_case, model, _ = build([[ToolCall('lookup_concept', {'name': 'Song ánh'}, '1'), Done({})],
                                [ToolCall('why_here', {'concept': 'f'}, '2'), Done({})], turn()])
    result = ask(use_case)
    assert result['status'] == 'answered' and model.calls[2][1] == 'NONE' and len(result['tool_calls']) == 2


# 9 ------------------------------------------------------------ spending caps
def test_quiz_and_document_tools_report_the_daily_cap_and_the_status_is_daily_limit():
    seen = []

    def capped(**kwargs):
        seen.append(kwargs)
        return {'status': 'failed', 'reason': 'daily_limit'}
    turns = [[ToolCall('make_quiz', {'scope': 'm3'}, '1'), Done({})],
             turn('Mình đã tạo xong quiz cho bạn rồi nhé!')]  # the model claims success; the code must not
    use_case, model, _ = build(turns, quiz=capped)
    result = ask(use_case, 'Tạo quiz giúp mình')
    assert seen and seen[0]['allow_spend'] is True and seen[0]['origin'] == 'assistant'
    assert result['status'] == 'daily_limit' and result['artifacts'] == []
    assert result['answer_md'].startswith('Mình đã tạo xong quiz') and 'hết hạn mức chi hôm nay' in result['answer_md']
    assert model.calls[1][0][-1]['tool_results'][0]['result']['error']['code'] == 'daily_limit'


def test_document_tool_daily_cap_also_gives_daily_limit():
    turns = [[ToolCall('make_document', {'request': 'Tóm tắt', 'scope': ['m3']}, '1'), Done({})], turn('Xong.')]
    use_case, _, _ = build(turns, document=lambda **kwargs: {'status': 'failed', 'reason': 'daily_limit'})
    assert ask(use_case, 'Tạo tài liệu')['status'] == 'daily_limit'


def test_the_learners_daily_cap_is_one_dollar_so_99_cents_already_spent_still_gets_an_answer():
    use_case, model, store = build([turn()])
    store.append_usage({'purpose': 'assistant', 'model_id': 'fake', 'doc_id': 'book', 'learner_id': 'alice',
                        'cost_usd': 0.99, 'created_at': datetime.now(timezone.utc).isoformat()})
    assert ask(use_case)['status'] == 'answered' and len(model.calls) == 1  # the old 0.20 cap would refuse here


def test_spent_cap_returns_daily_limit_without_calling_the_model():
    use_case, model, store = build([turn()])
    store.append_usage({'purpose': 'assistant', 'model_id': 'fake', 'doc_id': 'book', 'learner_id': 'alice',
                        'cost_usd': 1.00, 'created_at': datetime.now(timezone.utc).isoformat()})
    result = ask(use_case)
    assert result['status'] == 'daily_limit' and 'hôm nay' in result['answer_md'] and not model.calls


# 10 ----------------------------------------------------------- validation never reaches the learner
def test_validation_is_in_the_log_but_not_in_the_final_event_the_result_the_contract_or_the_stored_turn():
    events = []
    use_case, _, store = build([turn('Một câu không nhãn nào cả đâu nhé. [S77]')])
    result = ask(use_case, client_turn_id='t', on_event=events.append)
    final = next(e for e in events if e['event'] == 'final')['answer']
    assert set(result) == {'contract_version', 'answer_id', 'owner', 'doc_id', 'graph_version', 'session_id',
                           'client_turn_id', 'status', 'answer_md', 'sources', 'graph_cards', 'artifacts',
                           'focus_node_id', 'failure', 'linked_node_ids', 'tool_calls', 'usage'}
    assert result['contract_version'] == 'answer-3' and final == result
    kept = json.dumps([result, final, store.list_records('answer'), store.list_records('turn', owner='alice')],
                      ensure_ascii=False, default=str)
    assert 'validation' not in kept and 'unknown_labels' not in kept and 'unsourced_sentences' not in kept
    assert store.get_record('assistant_validation', result['answer_id'])['unknown_labels'] == ['S77']
    assert not any('unknown_labels' in json.dumps(e, default=str) for e in events)


def test_sources_listed_in_the_result_carry_label_page_and_section_for_every_passage_shown():
    use_case, _, _ = build([turn()])
    result = ask(use_case)
    assert result['sources'][0] == {'label': 'S1', 'chunk_id': 'c4', 'page': 4, 'section_path': ['Chương 7', 'Mục c4']}
    assert [row['chunk_id'] for row in result['sources']] == ['c4', 'c3']


# 11 ----------------------------------------------------------- the system prompt
def test_system_prompt_is_the_text_block_of_the_spec_word_for_word():
    block = re.search(r'```text\n(.*?)\n```', SPEC.read_text(encoding='utf-8'), re.S).group(1)
    use_case, model, _ = build([turn()])
    ask(use_case)
    assert model.prompt == block and 'KHONG_DU' not in model.prompt and 'chỉ dùng tài liệu' not in model.prompt


# ----------------------------------------------------------- the old checks are gone
def test_postcheck_is_not_called_by_the_assistant(monkeypatch):
    from doc2roadmap.application.phase_b import postcheck

    def forbidden(*args, **kwargs):
        raise AssertionError('check_text must not run in the assistant path')
    monkeypatch.setattr(postcheck, 'check_text', forbidden)
    use_case, _, _ = build([turn('x = 1 và một câu không nhãn.')])
    assert ask(use_case)['answer_md'] == 'x = 1 và một câu không nhãn.'
    import doc2roadmap.application.phase_b.assistant as module
    assert not hasattr(module, 'check_text') and 'postcheck' not in Path(module.__file__).read_text(encoding='utf-8')
