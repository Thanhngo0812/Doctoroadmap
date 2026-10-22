"""SA-56: the optional focus_node_id tells the assistant which concept the learner has open."""
import json
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


def sent_context(model, call=0):
    return json.loads(model.calls[call][0][0]['text'])


def ask(use_case, question, **kwargs):
    return use_case.ask('book', 1, 's', question, owner='alice', allow_spend=True, **kwargs)


class CitingFocusModel(support.Model):
    """Answers with a sentence citing whatever label the focus block points to."""

    def __init__(self):
        super().__init__([])

    def stream(self, messages, *, mode):
        self.calls.append((messages, mode))
        label = json.loads(messages[0]['text'])['focus']['definition_source']
        yield from answer_turn(f'{DEF_SONG} [{label}]')


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

def test_no_focus_matches_input_recorded_from_main_before_the_change():
    recorded = json.loads(BASELINE.read_text(encoding='utf-8'))
    now = json.loads(json.dumps({'scenarios': support.scenarios(), 'lecture_keys': support.lecture_keys()}))
    assert now['lecture_keys'] == recorded['lecture_keys']
    for name, expected in recorded['scenarios'].items():
        assert now['scenarios'][name] == expected, name


def test_explicit_none_focus_equals_omitted_focus():
    recorded = json.loads(BASELINE.read_text(encoding='utf-8'))
    now = json.loads(json.dumps(support.scenarios({'focus_node_id': None})))
    assert now == recorded['scenarios']


# ---------------------------------------------------------------- linked concepts and the focus block

def test_unnamed_question_links_the_focus_and_cites_its_definition_without_tool_calls():
    use_case, _, store, _ = build([])
    model = use_case.model = CitingFocusModel()
    result = ask(use_case, 'giải thích phần này', focus_node_id='f')
    context = sent_context(model)
    focus = context['focus']
    assert result['linked_node_ids'] == ['f']
    assert result['focus_node_id'] == 'f'
    assert focus['node_id'] == 'f' and focus['name'] == 'Song ánh'
    assert focus['module_title'] == 'Ánh xạ' and focus['module_index'] == 3
    assert (focus['concept_index'], focus['concept_count']) == (2, 2)
    label = focus['definition_source']
    source = next(row for row in context['sources'] if row['label'] == label)
    assert source['chunk_id'] == 'c4' and DEF_SONG in source['text']
    assert 'phần này' in focus['note'] and 'đang mở' in focus['note']
    # the fake model cites the label and passes the citation check without any search or lookup tool
    assert result['status'] == 'answered'
    assert result['citations'][0]['chunk_id'] == 'c4'
    assert result['tool_calls'] == [] and len(model.calls) == 1


def test_focus_definition_chunk_is_deduplicated_when_retrieval_already_found_it():
    use_case, model, _, _ = build([answer_turn(FOCUS_ANSWER)])
    result = ask(use_case, 'Song ánh có ánh xạ ngược không?', focus_node_id='f')
    sources = sent_context(model)['sources']
    assert [row['chunk_id'] for row in sources].count('c4') == 1
    assert sent_context(model)['focus']['definition_source'] == next(
        row['label'] for row in sources if row['chunk_id'] == 'c4')
    assert result['status'] == 'answered'


def test_question_naming_another_concept_keeps_it_linked_and_focus_stays():
    use_case, model, _, _ = build([answer_turn(support.DEF_DON + ' [S1]')])
    result = ask(use_case, 'phần này khác đơn ánh thế nào?', focus_node_id='f')
    assert result['linked_node_ids'] == ['e']
    assert sent_context(model)['focus']['node_id'] == 'f'
    assert [row['node_id'] for row in sent_context(model)['concepts']] == ['e']


def test_followup_links_focus_first_then_the_previous_concept():
    use_case, model, _, _ = build([answer_turn('Ma trận là bảng các số. [S1]'), answer_turn(FOCUS_ANSWER)])
    ask(use_case, 'Ma trận là gì?')
    result = ask(use_case, 'còn cái kia thì sao?', focus_node_id='f')
    assert result['linked_node_ids'] == ['f', 'a']
    assert [row['node_id'] for row in sent_context(model, 1)['concepts']] == ['f', 'a']


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
def test_unknown_or_unlearnable_focus_behaves_like_no_focus_and_warns(bad):
    plain, plain_model, _, _ = build([answer_turn()])
    plain_result = ask(plain, 'giải thích phần này')
    use_case, model, _, _ = build([answer_turn()])
    result = ask(use_case, 'giải thích phần này', focus_node_id=bad)
    assert model.calls == plain_model.calls and model.prompt == plain_model.prompt
    assert result['focus_node_id'] is None
    assert {'kind': 'focus_ignored'} in result['warnings']
    assert result['linked_node_ids'] == plain_result['linked_node_ids'] == []
    assert 'focus' not in sent_context(model)


def test_valid_or_missing_focus_adds_no_focus_ignored_warning():
    use_case, _, _, _ = build([answer_turn(), answer_turn()])
    assert ask(use_case, 'Song ánh là gì?')['warnings'] == []
    assert ask(use_case, 'giải thích phần này', focus_node_id='f')['warnings'] == []


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
    assert 'focus' not in sent_context(model, 1)
    assert result['focus_node_id'] is None


# ---------------------------------------------------------------- lecture ideas, read only

def test_cached_ready_lecture_adds_ideas_without_labels_and_without_generation():
    lecture, lecture_model, store, _ = lecture_setup(items=[
        'Song ánh vừa đơn ánh vừa toàn ánh [S1].', 'Mỗi phần tử đích có đúng một nghịch ảnh.'])
    use_case, model, _, _ = assistant_with(lecture, store, [answer_turn(FOCUS_ANSWER)])
    before = len(store.usage_rows())
    ask(use_case, 'giải thích phần này', focus_node_id='f')
    ideas = sent_context(model)['focus']['lecture_ideas']
    assert ideas['items'] == ['Song ánh vừa đơn ánh vừa toàn ánh.', 'Mỗi phần tử đích có đúng một nghịch ảnh.']
    assert 'không phải nguồn' in ideas['note'] and 'không trích dẫn' in ideas['note']
    assert lecture_model.touched == 0
    assert [row['purpose'] for row in store.usage_rows()[before:]] == ['assistant']


@pytest.mark.parametrize('case', ['no_cache', 'failed_cache', 'failure_record'])
def test_missing_or_failed_lecture_gives_no_ideas_never_generates_and_writes_nothing(case):
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
    focus = sent_context(model)['focus']
    assert 'lecture_ideas' not in focus and focus['node_id'] == 'f'
    assert lecture_model.touched == 0
    assert all(row['purpose'] == 'assistant' for row in store.usage_rows())
    assert store.get_record('lecture_failure', key) == records_before
    if case == 'no_cache':
        assert store.get_cache(key) is None and records_before is None


def test_ideas_are_read_with_the_real_model_cache_key_not_the_unavailable_key():
    # a use case without a model computes a different key; the seeded cache is under the real model key
    lecture, _, store, key = lecture_setup(items=['Một ý đã có trong cache.'])
    unavailable = LectureUseCase(None, store).make('book', 1, make_graph(), 'f', dry_run=True)['lecture_key']
    assert unavailable != key
    use_case, model, _, _ = assistant_with(lecture, store, [answer_turn(FOCUS_ANSWER)])
    ask(use_case, 'giải thích phần này', focus_node_id='f')
    assert sent_context(model)['focus']['lecture_ideas']['items'] == ['Một ý đã có trong cache.']


def test_very_long_lecture_is_cut_in_ideas_first_and_stays_under_the_cap():
    items = [f'Ý số {index}: ' + 'nội dung rất dài về song ánh ' * 8 for index in range(60)]
    items = [text.strip() for text in items]
    lecture, _, store, _ = lecture_setup(items=items)
    use_case, model, _, _ = assistant_with(lecture, store, [answer_turn(FOCUS_ANSWER)])
    ask(use_case, 'giải thích phần này', focus_node_id='f')
    focus = sent_context(model)['focus']
    cap = BSettings().assistant_focus_tokens
    assert cap == 400
    assert len(assistant_module.stable_json(focus)) // 3 <= cap
    kept = focus['lecture_ideas']['items']
    assert 0 < len(kept) < 60 and kept == items[:len(kept)]
    assert focus['node_id'] == 'f' and focus['definition_source']


def test_a_smaller_cap_drops_all_ideas_but_keeps_the_identifying_fields():
    lecture, _, store, _ = lecture_setup(items=['Ý ngắn số một.', 'Ý ngắn số hai.'])
    settings = replace(BSettings(), assistant_focus_tokens=1)
    use_case, model, _, _ = build([answer_turn(FOCUS_ANSWER)], lecture=lecture_reader(lecture), store=store, settings=settings)
    ask(use_case, 'giải thích phần này', focus_node_id='f')
    focus = sent_context(model)['focus']
    assert 'lecture_ideas' not in focus and focus['node_id'] == 'f'


@pytest.mark.parametrize('status', ['failed', 'not_cached', 'generating'])
def test_assistant_ignores_sections_of_a_lecture_that_is_not_ready(status):
    def reader(**kwargs):
        return {'status': status, 'sections': [{'items': [{'text': 'Không được dùng.'}]}]}
    use_case, model, _, _ = build([answer_turn(FOCUS_ANSWER)], lecture=reader)
    ask(use_case, 'giải thích phần này', focus_node_id='f')
    assert 'lecture_ideas' not in sent_context(model)['focus']


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
