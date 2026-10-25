"""Reviewed Lecture3UseCase + the web gateway + actual PostgreSQL, fake model only."""
import json
from queue import Queue
from threading import Event, Thread
from time import monotonic, sleep

import httpx
import pytest
import uvicorn
from sqlalchemy import text

from test_learning_progress_w07 import w07
from wayfinder.fakes.lecture import BODY, ScriptedLectureModel


pytestmark = pytest.mark.postgres


@pytest.fixture
def core_web(w07):
    w07.graph.nodes['a']['display_prerequisites'] = ['b']
    w07.graph.payload['requires_edges'] = [{'source': 'b', 'target': 'a', 'edge_type': 'requires',
        'quote': w07.graph.nodes['a']['anchor']['sentence'], 'quote_chunk_id': 'c1', 'chunk_ids': ['c1']}]
    model = ScriptedLectureModel()
    w07.gateway.runtime.model = model
    w07.other_gateway.runtime.model = model
    w07.model = model
    w07.url = f'/api/v1/courses/{w07.course.id}/concepts/a/lecture'
    yield w07
    model.release.set()


def events(response):
    return [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]


def test_w08_real_lecture3_cache_validation_stays_private_and_status_is_per_learner(core_web):
    w = core_web
    w.gateway.set_progress(w.a.actor, w.course.id, 'b', True)
    assert w.gateway.runtime.settings.learner_daily_max_usd == 1.0
    assert w.a.client.get(w.url).json()['status'] == 'generating'
    assert not w.model.calls
    streamed = w.a.client.get(w.url + '/stream')
    assert streamed.status_code == 200
    lesson = events(streamed)[-1]['lecture']
    assert lesson['status'] == 'ready' and lesson['contract_version'] == 'lecture-3'
    assert '$x^2+y^2$' in lesson['body_md'] and '[S999]' in lesson['body_md']
    assert lesson['self_check']['answer_md'] == 'Bằng $1$.'
    assert 'validation' not in streamed.text and 'sections' not in streamed.text and 'bridge' not in streamed.text
    assert lesson['prerequisites'][0]['learner_status'] == 'learned'
    other = w.other_gateway.get_lecture(w.b.actor, w.course.id, 'a')
    assert other['lecture_key'] == lesson['lecture_key']
    assert other['prerequisites'][0]['learner_status'] == 'not_learned'
    assert 'validation' not in json.dumps(other)
    assert len(w.model.calls) == 1
    with w.independent_engine.connect() as c:
        stored = c.scalar(text('SELECT value FROM phase_b_cache WHERE key=:key'), {'key': lesson['lecture_key']})
    assert stored['validation']['unknown_labels'] == ['S999']
    assert 'learner_status' not in json.dumps(stored)
    assert 'http' not in json.dumps(stored)


def test_w08_first_delta_precedes_model_finish_and_cache_is_completed_after_http_disconnect(core_web, monkeypatch):
    import socket
    w = core_web
    w.model.pause_after_first = True
    connections = []
    def tracked_connection():
        event = Event(); connections.append(event)
        return event
    monkeypatch.setattr('wayfinder.api.learning.Event', tracked_connection)
    listener = socket.socket()
    listener.bind(('127.0.0.1', 0)); listener.listen(128)
    port = listener.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(w.app, log_config=None, access_log=False, log_level='warning'))
    thread = Thread(target=server.run, kwargs={'sockets': [listener]}, daemon=True)
    thread.start()
    try:
        deadline = monotonic() + 5
        while not server.started and monotonic() < deadline: sleep(.01)
        assert server.started
        with httpx.Client(base_url=f'http://127.0.0.1:{port}', cookies=dict(w.a.client.cookies), timeout=10) as client:
            with client.stream('GET', w.url + '/stream') as response:
                assert response.status_code == 200
                iterator = response.iter_lines()
                skeleton = None
                delta = None
                try:
                    for line in iterator:
                        if line == 'event: skeleton': skeleton = json.loads(next(iterator)[6:])['lecture']
                        if line == 'event: delta':
                            delta = json.loads(next(iterator)[6:])['text']
                            break
                except httpx.ReadTimeout:
                    raise AssertionError('The first delta must arrive while the fake model is paused, before its final output') from None
                assert skeleton and delta == BODY[:100]
                assert w.model.waiting.wait(2) and not w.model.calls[0].finished
            # The client has disconnected while the fake model remains held at its gate.
            assert len(connections) == 1 and connections[0].wait(2)
            assert not w.model.calls[0].finished
            w.model.release.set()
            deadline = monotonic() + 5
            cached = None
            while monotonic() < deadline:
                cached = w.independent_store.get_cache(skeleton['lecture_key'])
                if cached: break
                sleep(.02)
            assert cached and cached['status'] == 'ready'
            after = client.get(w.url)
            assert after.status_code == 200 and after.json()['status'] == 'ready'
            assert len(w.model.calls) == 1 and w.model.calls[0].finished
    finally:
        w.model.release.set()
        server.should_exit = True
        thread.join(5); listener.close()
        assert not thread.is_alive()


def test_w08_concurrent_members_share_one_generation_across_postgres_runtimes(core_web):
    w = core_web
    w.model.pause_after_first = True
    results, failures = Queue(), Queue()
    def run(gateway, actor):
        try:
            rows = []
            gateway.stream_lecture(actor, w.course.id, 'a', rows.append)
            results.put(rows[-1]['lecture'])
        except BaseException as error:
            failures.put(error)
    a = Thread(target=run, args=(w.gateway, w.a.actor))
    b = Thread(target=run, args=(w.other_gateway, w.b.actor))
    a.start()
    assert w.model.waiting.wait(3)
    b.start()
    w.model.release.set()
    a.join(5); b.join(5)
    assert not a.is_alive() and not b.is_alive() and failures.empty()
    first, second = results.get_nowait(), results.get_nowait()
    assert first['status'] == second['status'] == 'ready'
    assert first['lecture_key'] == second['lecture_key'] and len(w.model.calls) == 1


@pytest.mark.parametrize('pieces,expected', [
    ([RuntimeError('private transport detail')], 'failed'),
    (['Đã gửi một phần bài học.', RuntimeError('private transport detail')], 'ready'),
    ([], 'failed'),
])
def test_w08_real_core_failure_policy_and_no_fallback(core_web, pieces, expected):
    w = core_web
    w.model.scripts = [pieces]
    response = w.a.client.get(w.url + '/stream')
    lesson = events(response)[-1]['lecture']
    assert lesson['status'] == expected
    assert 'private transport detail' not in response.text
    if expected == 'ready':
        assert lesson['body_md'] == pieces[0] and 'cat_ngan' in lesson['warnings']
        assert w.independent_store.get_cache(lesson['lecture_key']) is None
    else:
        assert not lesson['body_md'] and lesson['failure']['message'].strip()
        assert lesson['failure']['retryable'] is True
        assert lesson['failure']['reason_code'] != 'kiem_noi_dung'
    assert 'sections' not in response.text


def test_w08_cross_site_navigation_cannot_start_a_paid_generation(core_web):
    w = core_web
    response = w.a.client.get(w.url + '/stream', headers={'Sec-Fetch-Site': 'cross-site', 'Origin': 'https://evil.example'})
    assert response.status_code == 403
    assert not w.model.calls


def test_w08_personal_daily_guard_uses_one_dollar_and_keeps_learner_ledgers_separate(core_web):
    w = core_web
    w.phase_b.append_usage({'purpose': 'assistant', 'model_id': 'fake-ledger',
        'learner_id': w.a.actor.user_id, 'doc_id': 'doc-1', 'created_at': w.clock.now().isoformat(),
        'cost_usd': .5, 'input_tokens': 1, 'output_tokens': 1, 'replayed': True})
    guard = w.gateway.runtime.spend_guard
    assert guard.check('assistant', .1, w.a.actor.user_id) is True  # .5 + .1 fits the new cap.
    assert guard.check('assistant', .6, w.a.actor.user_id) is False
    assert guard.check('assistant', .6, w.b.actor.user_id) is True
    assert not w.model.calls  # The ledger amounts are fixtures, with no provider charge.


def test_w08_http_dto_discards_admin_keys_even_if_a_gateway_returns_them(core_web, monkeypatch):
    w = core_web
    raw = w.gateway.get_lecture(w.a.actor, w.course.id, 'a')
    raw['validation'] = {'W08_ADMIN_ONLY': True}
    raw['definition']['validation'] = {'W08_ADMIN_ONLY': True}
    raw['definition']['public_id'] = 'W08_PRIVATE_PROVIDER_ID'
    monkeypatch.setattr(w.gateway, 'get_lecture', lambda *args: raw)
    response = w.a.client.get(w.url)
    assert response.status_code == 200
    assert 'validation' not in response.text and 'public_id' not in response.text
    assert 'W08_ADMIN_ONLY' not in response.text and 'W08_PRIVATE_PROVIDER_ID' not in response.text


def test_w08_request_context_cannot_override_the_actor_or_published_document(core_web):
    w = core_web
    w.gateway.set_progress(w.a.actor, w.course.id, 'b', True)
    response = w.a.client.get(w.url + f'?owner={w.b.actor.user_id}&doc_id=other&graph_version=999')
    assert response.status_code == 200
    lesson = response.json()
    assert (lesson['doc_id'], lesson['graph_version'], lesson['course_id']) == ('doc-1', 8, w.course.id)
    assert lesson['prerequisites'][0]['learner_status'] == 'learned'
    assert not w.model.calls


def test_w08_no_source_still_has_a_message_and_retry_without_inventing_a_body(core_web):
    w = core_web
    w.graph.nodes['a'].update(name='Bài học chưa có tư liệu', display_name='Bài học chưa có tư liệu',
        aliases=[], teaching_chunk_ids=[], defining_chunk_ids=[], anchor={}, display_prerequisites=[])
    response = w.a.client.get(w.url + '/stream')
    assert response.status_code == 200
    lesson = events(response)[-1]['lecture']
    assert lesson['status'] == 'no_source' and not lesson['body_md']
    assert lesson['failure']['message'].strip() and lesson['failure']['retryable'] is True
    assert 'sections' not in response.text and not w.model.calls
