"""SA-56: the optional focus_node_id tells the assistant which concept the learner has open."""
import json
import re
from dataclasses import replace
from pathlib import Path

import pytest

from doc2roadmap.application.phase_b import assistant as assistant_module
from doc2roadmap.application.phase_b.assistant import AssistantUseCase
from doc2roadmap.application.phase_b.lectures import LectureUseCase
from doc2roadmap.application.ports.phase_b import ToolCall
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore

import sa56_support as support
from sa56_support import DEF_SONG, answer_turn, build, make_graph

BASELINE = Path(__file__).resolve().parents[2] / 'fixtures' / 'phase_b' / 'sa56-baseline-no-focus.json'
FOCUS_ANSWER = 'Song ánh là ánh xạ vừa đơn ánh vừa toàn ánh. [S1]'


def sent_text(model, call=0):
    return model.calls[call][0][0]['text']


def label_of_page(text, page):
    """The assistant label ([S1]...) the first-call context gave to the passage on `page`."""
    return re.search(r'\[(S\d+)\] \(trang %d,' % page, text).group(1)


def ask(use_case, question, **kwargs):
    return use_case.ask('book', 1, 's', question, owner='alice', allow_spend=True, **kwargs)


class CitingFocusModel(support.Model):
    """Answers with a sentence citing the label the context gave to the focus concept's definition passage."""

    def __init__(self):
        super().__init__([])

    def stream(self, messages, *, mode):
        self.calls.append((messages, mode))
        yield from answer_turn(f'{DEF_SONG} [{label_of_page(messages[0]["text"], 4)}]')


class CountingLectureModel:
    """Lecture model that must never be reached from the assistant."""
    model_id = 'gemini-3.1-flash-lite'

    def __init__(self):
        self.touched = 0

    def _touch(self, *args, **kwargs):
        self.touched += 1
        raise RuntimeError('assistant must not generate lectures')

    start_session = ask_json = stream_json = stream = _touch


def lecture_setup(node_id='f', *, failed=False, items=None):
    """A real LectureUseCase over a counting model; its cache is seeded the way a web click would."""
    store, model = InMemoryPhaseBStore(), CountingLectureModel()
    lecture = LectureUseCase(model, store)
    key = lecture.make('book', 1, make_graph(), node_id, dry_run=True)['lecture_key']
    if items is not None:
        status = 'failed' if failed else 'ready'
        body = {'status': status, 'node_id': node_id, 'lecture_key': key, 'sections': [
            {'kind': 'giai_thich', 'items': [{'text': text, 'citations': []} for text in items or []]}]}
        store.put_cache(key, body)
    return lecture, model, store, key


def lecture_reader(lecture):
    """The callable the assistant is built with, shaped like the one in composition_phase_b."""
    def get_lecture(concept, *, owner, doc_id, graph_version, graph, **kwargs):
        return lecture.get(doc_id, graph_version, graph, concept, owner=owner, **kwargs)
    return get_lecture


def assistant_with(lecture, store, turns):
    return build(turns, lecture=lecture_reader(lecture), store=store)


# ---------------------------------------------------------------- unchanged without a focus

def test_no_focus_matches_the_input_pinned_on_answer_3_before_the_focus_code_path_is_touched():
    # Re-pinned for SA-66: the original pin held the answer-2 JSON context. The lecture keys are pinned too.
    recorded = json.loads(BASELINE.read_text(encoding='utf-8'))
    now = json.loads(json.dumps({'scenarios': support.scenarios(), 'lecture_keys': support.lecture_keys()}))
    assert now['lecture_keys'] == recorded['lecture_keys']
    for name, expected in recorded['scenarios'].items():
        assert now['scenarios'][name] == expected, name


def test_lecture_keys_do_not_move_when_only_assistant_limits_change():
    changed = replace(BSettings(), assistant_max_rounds=9, assistant_focus_chars=7, assistant_max_usd=3.0,
                      assistant_history_turns=1, learner_daily_max_usd=9.0)
    assert support.lecture_keys(changed) == support.lecture_keys()


def test_explicit_none_focus_equals_omitted_focus():
    recorded = json.loads(BASELINE.read_text(encoding='utf-8'))
    now = json.loads(json.dumps(support.scenarios({'focus_node_id': None})))
    assert now == recorded['scenarios']


# ---------------------------------------------------------------- linked concepts and the focus block

def test_unnamed_question_links_the_focus_and_cites_its_definition_without_tool_calls():
    use_case, _, store, _ = build([])
    model = use_case.model = CitingFocusModel()
    result = ask(use_case, 'giải thích phần này', focus_node_id='f')
    text = sent_text(model)
    assert result['linked_node_ids'] == ['f']
    assert result['focus_node_id'] == 'f'
    assert 'Người học đang đọc bài giảng của khái niệm "Song ánh" (khái niệm 2/2 của module 3: Ánh xạ).' in text
    assert '"Phần này", "cái này" trong câu hỏi chỉ khái niệm này.' in text
    label = label_of_page(text, 4)
    assert re.search(r'\[%s\] \(trang 4, mục Ánh xạ\)\n%s' % (label, re.escape(DEF_SONG)), text)
    # the definition passage is in the first call, so the answer cites it with no search or lookup tool
    assert result['status'] == 'answered'
    assert next(row for row in result['sources'] if row['label'] == label)['chunk_id'] == 'c4'
    assert result['tool_calls'] == [] and len(model.calls) == 1


def test_focus_definition_chunk_is_deduplicated_when_retrieval_already_found_it():
    use_case, model, _, _ = build([answer_turn(FOCUS_ANSWER)])
    result = ask(use_case, 'Song ánh có ánh xạ ngược không?', focus_node_id='f')
    text = sent_text(model)
    assert text.count('(trang 4,') == 1
    assert [row['chunk_id'] for row in result['sources']].count('c4') == 1
    assert result['status'] == 'answered'


def test_question_naming_another_concept_keeps_it_linked_and_focus_stays():
    use_case, model, _, _ = build([answer_turn(support.DEF_DON + ' [S1]')])
    result = ask(use_case, 'phần này khác đơn ánh thế nào?', focus_node_id='f')
    text = sent_text(model)
    assert result['linked_node_ids'] == ['e']
    assert 'khái niệm "Song ánh"' in text
    assert 'Khái niệm liên quan: Đơn ánh' in text and 'Khái niệm liên quan: Song ánh' not in text


def test_followup_links_focus_first_then_the_previous_concept():
    use_case, model, _, _ = build([answer_turn('Ma trận là bảng các số. [S1]'), answer_turn(FOCUS_ANSWER)])
    ask(use_case, 'Ma trận là gì?')
    result = ask(use_case, 'còn cái kia thì sao?', focus_node_id='f')
    assert result['linked_node_ids'] == ['f', 'a']
    text = sent_text(model, 1)
    assert text.index('Khái niệm liên quan: Song ánh') < text.index('Khái niệm liên quan: Ma trận')


def test_followup_that_already_links_the_focus_is_deduplicated():
    use_case, model, _, _ = build([answer_turn(), answer_turn()])
    ask(use_case, 'Song ánh là gì?')
    result = ask(use_case, 'còn cái kia thì sao?', focus_node_id='f')
    assert result['linked_node_ids'] == ['f']


def test_focus_drives_module_cards_and_background_reminders_when_question_names_nothing():
    use_case, model, _, _ = build([answer_turn(FOCUS_ANSWER)], scope_kind='m1')
    result = ask(use_case, 'giải thích phần này', focus_node_id='f')
    assert result['graph_cards']['module_cards'][0]['node_id'] == 'f'
    assert [row['node_id'] for row in result['graph_cards']['reminders']] == ['e']


# ---------------------------------------------------------------- invalid focus

@pytest.mark.parametrize('bad', ['không-có', 'x', '', 7, ['f'], {'node_id': 'f'}])
def test_unknown_or_unlearnable_focus_behaves_like_no_focus_and_is_logged(bad):
    plain, plain_model, _, _ = build([answer_turn()])
    plain_result = ask(plain, 'giải thích phần này')
    use_case, model, store, _ = build([answer_turn()])
    result = ask(use_case, 'giải thích phần này', focus_node_id=bad)
    assert model.calls == plain_model.calls and model.prompt == plain_model.prompt
    assert result['focus_node_id'] is None
    assert store.get_record('assistant_validation', result['answer_id'])['focus_ignored'] is True  # admin log only
    assert result['linked_node_ids'] == plain_result['linked_node_ids'] == []
    assert 'Người học đang đọc bài giảng' not in sent_text(model)


def test_valid_or_missing_focus_is_not_logged_as_ignored():
    use_case, _, store, _ = build([answer_turn(), answer_turn()])
    for result in (ask(use_case, 'Song ánh là gì?'), ask(use_case, 'giải thích phần này', focus_node_id='f')):
        assert store.get_record('assistant_validation', result['answer_id'])['focus_ignored'] is False


def test_valid_focus_makes_the_assistant_skip_the_embedding_concept_lookup():
    calls = []
    store, g = InMemoryPhaseBStore(), make_graph()
    support.session(store, g)
    model = support.Model([answer_turn(FOCUS_ANSWER)])
    use_case = AssistantUseCase(g, store, model, concept_lookup=lambda text: calls.append(text) or {
        'matches': [{'node_id': 'e'}]})
    result = ask(use_case, 'giải thích phần này', focus_node_id='f')
    assert calls == [] and result['linked_node_ids'] == ['f']
    # without a focus the same question still falls back to the lookup, so the callback is wired
    model.turns = iter([answer_turn(FOCUS_ANSWER)])
    without = ask(use_case, 'giải thích phần này')
    assert calls == ['giải thích phần này'] and without['linked_node_ids'] == ['e']


# ---------------------------------------------------------------- not stored

def test_focus_is_not_stored_in_session_or_state_and_the_next_turn_has_none():
    use_case, model, store, _ = build([answer_turn(FOCUS_ANSWER), answer_turn(FOCUS_ANSWER)])
    ask(use_case, 'giải thích phần này', focus_node_id='f')
    for kind, key in (('session', 's'), ('assistant_state', use_case._session_key('book', 's', 'alice'))):
        assert 'focus' not in json.dumps(store.get_record(kind, key), ensure_ascii=False), kind
    result = ask(use_case, 'giải thích phần này')
    assert 'Người học đang đọc bài giảng' not in sent_text(model, 1)
    assert result['focus_node_id'] is None


# ---------------------------------------------------------------- lecture ideas, read only

def test_cached_ready_lecture_adds_its_text_without_labels_and_without_generation():
    lecture, lecture_model, store, _ = lecture_setup(items=[
        'Song ánh vừa đơn ánh vừa toàn ánh [S1].', 'Mỗi phần tử đích có đúng một nghịch ảnh.'])
    use_case, model, _, _ = assistant_with(lecture, store, [answer_turn(FOCUS_ANSWER)])
    before = len(store.usage_rows())
    ask(use_case, 'giải thích phần này', focus_node_id='f')
    text = sent_text(model)
    assert 'Song ánh vừa đơn ánh vừa toàn ánh. Mỗi phần tử đích có đúng một nghịch ảnh.' in text
    assert 'không phải tư liệu của sách' in text and 'không có nhãn nguồn' in text
    assert 'vừa toàn ánh [S1].' not in text  # the lecture's own [S1] is gone; the only [S1] left is the passage header
    assert lecture_model.touched == 0
    assert [row['purpose'] for row in store.usage_rows()[before:]] == ['assistant']


@pytest.mark.parametrize('case', ['no_cache', 'failed_cache', 'failure_record'])
def test_missing_or_failed_lecture_gives_no_lecture_text_never_generates_and_writes_nothing(case):
    if case == 'failed_cache':
        lecture, lecture_model, store, key = lecture_setup(items=['Ý không được dùng.'], failed=True)
    else:
        lecture, lecture_model, store, key = lecture_setup()
    if case == 'failure_record':
        store.put_record('lecture_failure', key, {'doc_id': 'book', 'expires_at': '2999-01-01T00:00:00+00:00',
                                                   'result': {'status': 'failed', 'sections': []}})
    use_case, model, _, _ = assistant_with(lecture, store, [answer_turn(FOCUS_ANSWER)])
    records_before = store.get_record('lecture_failure', key)
    ask(use_case, 'giải thích phần này', focus_node_id='f')
    text = sent_text(model)
    assert 'Bài giảng người học đang đọc' not in text and 'khái niệm "Song ánh"' in text
    assert 'Ý không được dùng.' not in text
    assert lecture_model.touched == 0
    assert all(row['purpose'] == 'assistant' for row in store.usage_rows())
    assert store.get_record('lecture_failure', key) == records_before
    if case == 'no_cache':
        assert store.get_cache(key) is None and records_before is None


def test_lecture_text_is_read_with_the_real_model_cache_key_not_the_unavailable_key():
    # a use case without a model computes a different key; the seeded cache is under the real model key
    lecture, _, store, key = lecture_setup(items=['Một ý đã có trong cache.'])
    unavailable = LectureUseCase(None, store).make('book', 1, make_graph(), 'f', dry_run=True)['lecture_key']
    assert unavailable != key
    use_case, model, _, _ = assistant_with(lecture, store, [answer_turn(FOCUS_ANSWER)])
    ask(use_case, 'giải thích phần này', focus_node_id='f')
    assert 'Một ý đã có trong cache.' in sent_text(model)


def test_very_long_lecture_is_cut_to_the_focus_character_cap_keeping_its_beginning():
    items = [f'Ý số {index}: ' + 'nội dung rất dài về song ánh ' * 8 for index in range(60)]
    items = [text.strip() for text in items]
    lecture, _, store, _ = lecture_setup(items=items)
    use_case, model, _, _ = assistant_with(lecture, store, [answer_turn(FOCUS_ANSWER)])
    ask(use_case, 'giải thích phần này', focus_node_id='f')
    text = sent_text(model)
    cap = BSettings().assistant_focus_chars
    assert cap == 1500
    shown = text.split('không có nhãn nguồn):\n')[1].split('\nKhái niệm liên quan:')[0]
    assert 0 < len(shown) <= cap and shown.startswith(items[0])
    assert 'Ý số 59' not in text
    assert label_of_page(text, 4)  # the definition passage still travels with the focus


def test_a_zero_focus_cap_drops_the_lecture_text_but_keeps_the_focus_sentence():
    lecture, _, store, _ = lecture_setup(items=['Ý ngắn số một.', 'Ý ngắn số hai.'])
    settings = replace(BSettings(), assistant_focus_chars=0)
    use_case, model, _, _ = build([answer_turn(FOCUS_ANSWER)], lecture=lecture_reader(lecture), store=store, settings=settings)
    ask(use_case, 'giải thích phần này', focus_node_id='f')
    text = sent_text(model)
    assert 'Bài giảng người học đang đọc' not in text and 'khái niệm "Song ánh"' in text


@pytest.mark.parametrize('status', ['failed', 'not_cached', 'generating'])
def test_assistant_ignores_sections_of_a_lecture_that_is_not_ready(status):
    def reader(**kwargs):
        return {'status': status, 'sections': [{'items': [{'text': 'Không được dùng.'}]}]}
    use_case, model, _, _ = build([answer_turn(FOCUS_ANSWER)], lecture=reader)
    ask(use_case, 'giải thích phần này', focus_node_id='f')
    assert 'Không được dùng.' not in sent_text(model)


def test_lecture_cache_only_read_is_pure_for_ready_failed_and_missing_entries():
    lecture, model, store, key = lecture_setup()
    graph = make_graph()
    missing = lecture.make('book', 1, graph, 'f', cache_only=True)
    assert missing['status'] == 'not_cached' and store.get_cache(key) is None
    store.put_cache(key, {'status': 'failed', 'node_id': 'f', 'sections': []})
    assert lecture.make('book', 1, graph, 'f', cache_only=True)['status'] == 'not_cached'
    store.put_cache(key, {'status': 'ready', 'node_id': 'f', 'sections': []})
    assert lecture.make('book', 1, graph, 'f', cache_only=True)['status'] == 'ready'
    assert model.touched == 0 and store.usage_rows() == [] and store.list_records('lecture_failure') == []


# ---------------------------------------------------------------- dry run

def test_dry_run_counts_the_focus_block_in_hash_and_token_estimate(monkeypatch):
    seen = []
    real = assistant_module.estimate_cost
    monkeypatch.setattr(assistant_module, 'estimate_cost',
                        lambda model_id, tokens, out: seen.append(tokens) or real(model_id, tokens, out))
    use_case, model, _, _ = build([])
    plain = ask(use_case, 'giải thích phần này', dry_run=True)
    focused = ask(use_case, 'giải thích phần này', dry_run=True, focus_node_id='f')
    assert plain['context_hash'] != focused['context_hash']
    assert seen[1] > seen[0]
    assert focused['focus_node_id'] == 'f' and model.calls == []
    # naming the concept links it either way, so only the focus block can change the hash
    named = ask(use_case, 'Song ánh là gì?', dry_run=True)
    named_focus = ask(use_case, 'Song ánh là gì?', dry_run=True, focus_node_id='f')
    assert named['context_hash'] != named_focus['context_hash']
