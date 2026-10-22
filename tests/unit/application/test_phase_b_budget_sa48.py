from dataclasses import replace
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from threading import Event, Lock, Thread
from zoneinfo import ZoneInfo

import pytest

from doc2roadmap.application.phase_b.budget import DailyLimitExceeded, DailySpendGuard
from doc2roadmap.application.phase_b.common import call_json
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore, JsonPhaseBStore


# Upper bound only: every wait below ends on an event, so a loaded machine just waits longer.
WAIT = 60


class Clock:
    def __init__(self):
        self.at = datetime(2026, 10, 18, 16, 59, tzinfo=timezone.utc)

    def now(self):
        return self.at

    def today(self, zone):
        return self.at.astimezone(ZoneInfo(zone)).date()


@pytest.fixture(params=['memory', 'json'])
def store(request, tmp_path):
    return (InMemoryPhaseBStore() if request.param == 'memory'
            else JsonPhaseBStore(tmp_path / 'phase-b.json'))


def test_reservations_share_learner_and_system_pools_across_guard_instances(store):
    clock = Clock()
    settings = replace(BSettings(), learner_daily_max_usd=.20, system_daily_max_usd=.20)
    first = DailySpendGuard(store, settings=settings, clock=clock)
    second = DailySpendGuard(store, settings=settings, clock=clock)
    learner = first.reserve('assistant', .12, 'alice')
    with pytest.raises(DailyLimitExceeded):
        second.reserve('document', .12, 'alice')
    other = second.reserve('document', .12, 'bob')
    system = first.reserve('lecture', .12)
    with pytest.raises(DailyLimitExceeded):
        second.reserve('quiz_gen', .12)
    with pytest.raises(DailyLimitExceeded):
        second.reserve('quiz_verify', .12)
    first.release(learner)
    replacement = second.reserve('document', .12, 'alice')
    for token in (other, system, replacement):
        second.release(token)
    assert not store.list_records('spend_reservation')
    assert store.usage_rows() == []


@pytest.mark.parametrize('error_kind', ['network', 'parse'])
def test_failed_calls_release_reservations_and_record_billed_usage_once(store, error_kind):
    clock = Clock()
    settings = replace(BSettings(), learner_daily_max_usd=.20, document_max_output_tokens=80_000)
    guard = DailySpendGuard(store, settings=settings, clock=clock)

    class Model:
        model_id = settings.model_id
        last_usage = {}

        def ask_json(self, prompt, **kwargs):
            if error_kind == 'network':
                raise OSError('connection failed before usage')
            return SimpleNamespace(payload='invalid JSON shape',
                                   usage={'promptTokenCount': 0, 'candidatesTokenCount': 80_000})

    with pytest.raises((OSError, TypeError)):
        call_json(Model(), 'request', response_schema={}, store=store, purpose='document',
                  doc_id='dev', context_hash='failed', allow_spend=True, settings=settings,
                  learner_id='alice', spend_guard=guard, clock=clock)
    rows = store.usage_rows()
    assert len(rows) == 1 and rows[0]['failed']
    assert rows[0]['cost_usd'] == (0 if error_kind == 'network' else .12)
    assert not store.list_records('spend_reservation')
    assert guard.check('document', .12, 'alice') == (error_kind == 'network')


def test_call_uses_admission_day_and_releases_unused_estimate(store):
    clock = Clock()
    settings = replace(BSettings(), learner_daily_max_usd=.20, document_max_output_tokens=80_000)
    guard = DailySpendGuard(store, settings=settings, clock=clock)
    admitted_at = clock.now()

    class Model:
        model_id = settings.model_id

        def ask_json(self, prompt, **kwargs):
            clock.at += timedelta(minutes=2)
            return SimpleNamespace(payload={'ok': True}, usage={'candidatesTokenCount': 40_000})

    call_json(Model(), 'request', response_schema={}, store=store, purpose='document',
              doc_id='dev', context_hash='day', allow_spend=True, settings=settings,
              learner_id='alice', spend_guard=guard, clock=clock)
    assert store.usage_rows()[0]['created_at'] == admitted_at.isoformat()
    assert store.usage_rows()[0]['cost_usd'] == .06
    assert not store.list_records('spend_reservation')
    assert guard.check('assistant', .20, 'alice')


def test_replay_remains_free_when_learner_budget_is_exhausted(store):
    clock = Clock()
    store.append_usage({'purpose': 'document', 'learner_id': 'alice', 'cost_usd': .20,
                        'created_at': clock.now().isoformat()})

    class Replay:
        is_replay = True
        model_id = BSettings().model_id

        def ask_json(self, prompt, **kwargs):
            return SimpleNamespace(payload={'ok': True}, usage={'candidatesTokenCount': 80_000})

    reply = call_json(Replay(), 'request', response_schema={}, store=store, purpose='document',
                      doc_id='dev', context_hash='replay', allow_spend=True, learner_id='alice', clock=clock)
    assert reply.payload == {'ok': True} and reply.cost_usd == 0
    assert sum(row['cost_usd'] for row in store.usage_rows()) == .20
    assert not store.list_records('spend_reservation')


def test_two_lecture_nodes_share_the_system_reservation_and_cached_result_stays_available(store):
    from doc2roadmap.application.phase_b.lectures import LectureUseCase
    from test_phase_b_lecture_b2 import _Model, _payload
    from test_phase_b_lecture_sa26 import _graph

    settings = replace(BSettings(), system_daily_max_usd=.20, lecture_max_output_tokens=80_000)

    class Model(_Model):
        model_id = settings.model_id

        def start_session(self, system_prompt):
            session = super().start_session(system_prompt)
            session.last_usage = {'candidatesTokenCount': 80_000}
            return session

    graph, results, errors = _graph(with_later=True), {}, {}
    model = Model([_payload()[0]])
    model.block = True
    def generate(node):
        try:
            results[node] = LectureUseCase(model, store, settings=settings).make(
                'd1', 'g1', graph, node, allow_spend=True)
        except BaseException as exc:  # a Thread would swallow it and leave a blind KeyError below
            errors[node] = repr(exc)

    first, second = Thread(target=generate, args=('a',)), Thread(target=generate, args=('b',))
    first.start()
    assert model.entered.wait(timeout=WAIT), 'first lecture never reached the model'
    second.start()
    # The second lecture is refused by the reservation without waiting for the model, so its end is the
    # synchronisation point: no guessed delay, and the first call is still blocked inside the model.
    second.join(timeout=WAIT)
    assert not second.is_alive(), 'second lecture did not finish while the first held the reservation'
    assert model.calls == 1 and 'a' not in results
    model.release.set()
    first.join(timeout=WAIT)
    assert not first.is_alive()
    assert not errors, errors
    assert results['a']['status'] == 'ready'
    assert results['b']['failure']['reason_code'] == 'tran_he_thong'
    assert model.calls == 1
    assert sum(row['cost_usd'] for row in store.usage_rows()) == .12
    assert not store.list_records('spend_reservation')
    store.append_usage({'purpose': 'quiz_gen', 'cost_usd': .08,
                        'created_at': datetime.now(timezone.utc).isoformat()})
    cached = LectureUseCase(model, store, settings=settings).make('d1', 'g1', graph, 'a', allow_spend=True)
    assert cached['status'] == 'ready' and model.calls == 1


def test_assistant_sessions_share_learner_reservation_before_streaming(store):
    from doc2roadmap.application.phase_b.assistant import AssistantUseCase
    from doc2roadmap.application.phase_b.sessions import SessionUseCase
    from doc2roadmap.application.ports.phase_b import Delta, Done
    from test_phase_b_assistant_sa36 import graph as make_graph

    settings = replace(BSettings(), learner_daily_max_usd=.20, assistant_max_output_tokens=80_000,
                       assistant_max_usd=.5)
    graph = make_graph()
    sessions = SessionUseCase(store, graph)
    ids = [sessions.create_session('alice', 'book', {'kind': 'roadmap'})['session_id'] for _ in range(2)]
    entered, release = Event(), Event()

    class Model:
        model_id = settings.model_id

        def __init__(self):
            self.calls, self.lock = 0, Lock()

        def start_session(self, *_args):
            return self

        def stream(self, messages, *, mode):
            with self.lock:
                self.calls += 1
                first = self.calls == 1
            if first:
                entered.set()
                assert release.wait(timeout=WAIT)
            yield Delta('Target d is defined. [S1]')
            yield Done({'candidatesTokenCount': 80_000})

    model, results, errors = Model(), {}, {}
    def ask(index):
        try:
            results[index] = AssistantUseCase(graph, store, model, settings=settings).ask(
                'book', 1, ids[index], 'Target d', owner='alice', allow_spend=True)
        except BaseException as exc:  # a Thread would swallow it and leave a blind KeyError below
            errors[index] = repr(exc)

    first, second = Thread(target=ask, args=(0,)), Thread(target=ask, args=(1,))
    first.start()
    assert entered.wait(timeout=WAIT), 'first session never reached the model'
    second.start()
    # The second session is refused by the reservation before streaming, so its end is the sync point.
    second.join(timeout=WAIT)
    assert not second.is_alive(), 'second session did not finish while the first held the reservation'
    assert model.calls == 1 and 0 not in results
    release.set()
    first.join(timeout=WAIT)
    assert not first.is_alive()
    assert not errors, errors
    assert results[0]['status'] == 'answered'
    assert results[1]['status'] == 'daily_limit'
    assert model.calls == 1
    assert sum(row['cost_usd'] for row in store.usage_rows()) == .12
    assert not store.list_records('spend_reservation')


def test_lecture_replay_is_available_when_system_spend_is_exhausted(store):
    from doc2roadmap.application.phase_b.lectures import LectureUseCase
    from test_phase_b_lecture_b2 import _Model, _payload
    from test_phase_b_lecture_sa26 import _graph

    settings = replace(BSettings(), system_daily_max_usd=0)
    model = _Model([_payload()[0]])
    model.is_replay = True
    result = LectureUseCase(model, store, settings=settings).make('d1', 'g1', _graph(), 'a', allow_spend=True)
    assert result['status'] == 'ready' and model.calls == 1
    assert sum(row['cost_usd'] for row in store.usage_rows()) == 0
    assert not store.list_records('spend_reservation')


def test_timed_out_lecture_keeps_budget_until_the_late_provider_finishes(store):
    from doc2roadmap.application.phase_b.lectures import LectureUseCase
    from test_phase_b_lecture_b2 import _Model, _payload
    from test_phase_b_lecture_sa26 import _graph

    settings = replace(BSettings(), system_daily_max_usd=.20, lecture_max_output_tokens=80_000,
                       lecture_click_timeout_seconds=.03)
    released = Event()
    original_delete = store.delete_record
    def observe_release(kind, record_id):
        original_delete(kind, record_id)
        if kind == 'spend_reservation':
            released.set()
    store.delete_record = observe_release

    class Model(_Model):
        model_id = settings.model_id

        def start_session(self, system_prompt):
            session = super().start_session(system_prompt)
            session.last_usage = {'candidatesTokenCount': 80_000}
            return session

    graph = _graph(with_later=True)
    model = Model([_payload()[0]])
    model.block = True
    try:
        timed_out = LectureUseCase(model, store, settings=settings).make(
            'd1', 'g1', graph, 'a', allow_spend=True)
        assert timed_out['failure']['reason_code'] == 'het_thoi_gian'
        assert model.entered.is_set() and len(store.list_records('spend_reservation')) == 1
        blocked = LectureUseCase(model, store, settings=settings).make(
            'd1', 'g1', graph, 'b', allow_spend=True)
        assert blocked['failure']['reason_code'] == 'tran_he_thong' and model.calls == 1
    finally:
        model.release.set()
    assert released.wait(timeout=2)
    assert not store.list_records('spend_reservation')
    assert sum(row['cost_usd'] for row in store.usage_rows()) == .12
    assert timed_out['status'] == 'failed'
