"""Answer-3 through real HTTP/PostgreSQL; provider calls are scripted only."""
import json
from uuid import uuid4

import pytest
from sqlalchemy import text

from test_learning_progress_w07 import w07
from wayfinder.testing import ScriptedModel
from doc2roadmap.application.ports.phase_b import Delta, Done, ToolCall


pytestmark = pytest.mark.postgres


@pytest.fixture
def chat(w07):
    model = ScriptedModel(tool_turns=[[Delta('Câu trả lời $x^2$. [S1] [S999]'), Done({'input_tokens': 100, 'output_tokens': 30})]])
    model.is_replay = True
    w07.gateway.runtime.model = model
    w07.other_gateway.runtime.model = model
    w07.model = model
    w07.url = f'/api/v1/courses/{w07.course.id}/sessions'
    return w07


def create(w, *, client=None, scope=None):
    user = client or w.a
    response = user.client.post(w.url, headers=user.headers, json={'scope': scope or {'kind': 'roadmap'}})
    assert response.status_code == 201, response.text
    return response.json()


def ask(w, sid, *, user=None, key=None, question='Tập hợp là gì?', **extra):
    user = user or w.a
    return user.client.post(f'{w.url}/{sid}/turns', headers=user.headers,
        json={'question': question, 'client_turn_id': key or uuid4().hex, **extra})


def events(response):
    assert response.status_code == 200, response.text
    return [dict(event=frame.splitlines()[0][7:], **json.loads(next(line[6:] for line in frame.splitlines() if line.startswith('data: '))))
        for frame in response.text.strip().split('\n\n') if frame.startswith('event: ')]


def test_w09_sessions_bind_actor_document_and_scope_from_published_graph(chat):
    w = chat
    session = create(w, scope={'kind': 'module', 'module_id': 'm1', 'node_ids': ['attacker']})
    sid = session['session_id']
    assert 'owner' not in session and 'state' not in session
    with w.independent_engine.connect() as c:
        row = c.scalar(text("SELECT value FROM phase_b_record WHERE kind='session' AND record_id=:sid"), {'sid': sid})
    assert row['owner'] == w.a.actor.user_id and row['doc_id'] == 'doc-1'
    assert row['scope']['node_ids'] == ['a', 'b']
    assert w.b.client.get(w.url).json()['sessions'] == []
    assert w.b.client.get(f'{w.url}/{sid}/turns').status_code == 404
    assert ask(w, sid, user=w.b).status_code == 404
    assert w.b.client.patch(f'{w.url}/{sid}', headers=w.b.headers, json={'title': 'stolen'}).status_code == 404
    assert w.b.client.delete(f'{w.url}/{sid}', headers=w.b.headers).status_code == 404
    renamed = w.a.client.patch(f'{w.url}/{sid}', headers=w.a.headers, json={'title': 'Ôn tập hợp'})
    assert renamed.json()['title'] == 'Ôn tập hợp'
    assert w.a.client.get(w.url + '?filter=module:m1').json()['sessions'][0]['session_id'] == sid
    assert not w.model.tool_calls


def test_w09_answer3_history_and_idempotency_keep_private_fields_on_server(chat):
    w = chat; sid = create(w)['session_id']; key = uuid4().hex
    first = events(ask(w, sid, key=key))
    assert any(row['event'] == 'delta' and 'x^2' in row['text'] for row in first)
    final = first[-1]['answer']
    assert final['contract_version'] == 'answer-3' and final['status'] == 'answered'
    assert final['answer_md'] == 'Câu trả lời $x^2$. [S1] [S999]'
    second = events(ask(w, sid, key=key))[-1]['answer']
    assert second['answer_id'] == final['answer_id'] and len(w.model.tool_calls) == 1
    from dataclasses import replace
    w.gateway.runtime.settings = replace(w.gateway.runtime.settings, assistant_prompt_version='fake-new-prompt')
    assert events(ask(w, sid, key=key))[-1]['answer']['answer_id'] == final['answer_id']
    assert len(w.model.tool_calls) == 1
    history = w.a.client.get(f'{w.url}/{sid}/turns').json()['turns']
    assert len(history) == 1 and history[0]['client_turn_id'] == key
    raw = json.dumps([first, second, history])
    assert all(value not in raw for value in ['validation', 'tool_calls', 'result_summary', 'public_id', 'res.cloudinary.com'])
    with w.independent_engine.connect() as c:
        assert c.scalar(text("SELECT count(*) FROM phase_b_record WHERE kind='assistant_validation'")) == 1
        assert c.scalar(text("SELECT count(*) FROM phase_b_record WHERE kind='turn'")) == 1
    assert ask(w, sid, key=key, question='Câu hỏi khác').status_code == 409
    assert len(w.model.tool_calls) == 1


def test_w09_focus_is_per_turn_and_cache_only_never_generates_lectures(chat, monkeypatch):
    w = chat; sid = create(w)['session_id']; reads = []
    def cached_lecture(graph):
        class Reader:
            def make(self, *args, **kwargs):
                reads.append(kwargs)
                assert kwargs['cache_only'] is True
                return {'status': 'not_cached'}
        return Reader()
    monkeypatch.setattr(w.gateway.runtime, 'lecture', cached_lecture)
    events(ask(w, sid, focus_node_id='a'))
    assert reads and all(row['cache_only'] for row in reads)
    assert 'focus' not in json.dumps(w.phase_b.get_record('session', sid)['state'])
    w.model.tool_turns.append([Delta('Lượt sau.'), Done({})])
    assert events(ask(w, sid))[-1]['answer']['focus_node_id'] is None
    w.model.tool_turns.append([Delta('ID lạ vẫn trả lời.'), Done({})])
    invalid = events(ask(w, sid, focus_node_id='not-in-graph'))[-1]['answer']
    assert invalid['focus_node_id'] is None and 'focus_ignored' in invalid['warnings']
    assert len(reads) == 1


def test_w09_rate_limit_counts_new_intents_across_courses_but_not_retries(chat):
    w = chat; sid = create(w)['session_id']
    w.model.tool_turns = [[Delta('Đã trả lời.'), Done({})] for _ in range(10)]
    keys = [uuid4().hex for _ in range(10)]
    for key in keys:
        assert ask(w, sid, key=key).status_code == 200
    assert ask(w, sid, key=keys[0]).status_code == 200
    response = ask(w, sid)
    assert response.status_code == 429 and response.json()['error']['retry_after'] > 0
    other_course = w.courses.create_course(w.a.actor, doc_id='doc-1', title='Khoá thứ hai', graph_version=8, module_count=1)
    other_url = f'/api/v1/courses/{other_course.id}/sessions'
    other_sid = w.a.client.post(other_url, headers=w.a.headers, json={'scope': {'kind': 'roadmap'}}).json()['session_id']
    denied = w.a.client.post(f'{other_url}/{other_sid}/turns', headers=w.a.headers,
        json={'question': 'Khoá khác vẫn dùng chung giới hạn phút', 'client_turn_id': uuid4().hex})
    assert denied.status_code == 429 and denied.json()['error']['code'] == 'rate_limited'
    assert len(w.model.tool_calls) == 10
    w.clock.advance(61)
    w.model.tool_turns.append([Delta('Đã đặt lại.'), Done({})])
    assert ask(w, sid).status_code == 200


def test_w09_usage_ratio_has_one_ledger_and_does_not_double_count_build_receipts(chat):
    w = chat
    for cost, extra in [(.35, {}), (.7, {'counted_in': 'build'})]:
        w.phase_b.append_usage({'purpose': 'assistant', 'learner_id': w.a.actor.user_id, 'doc_id': 'other-book',
            'created_at': w.clock.now().isoformat(), 'cost_usd': cost, **extra})
    w.phase_b.append_usage({'purpose': 'document', 'learner_id': w.b.actor.user_id, 'doc_id': 'other-book',
        'created_at': w.clock.now().isoformat(), 'cost_usd': .9})
    data = w.a.client.get('/api/v1/me/usage').json()
    assert data['contract_version'] == 'usage-1'
    assert data['learner_today']['used_ratio'] == pytest.approx(.35)
    assert data['learner_today']['limited'] is False
    assert data['learner_today']['resets_at'].endswith('+07:00')
    assert data['builds_this_month']['used'] == data['builds_used']
    assert data['builds_this_month']['max'] == data['build_monthly_max']
    assert data['builds_this_month']['resets_at'].endswith('+07:00')
    assert not any(word in json.dumps(data) for word in ['cost_usd', 'tokens', 'usd'])


def test_w09_revoked_membership_denies_next_session_and_stream_request(chat):
    w = chat; sid = create(w)['session_id']
    with w.engine.begin() as c:
        c.execute(text('DELETE FROM membership WHERE course_id=:cid AND account_id=:uid'), {'cid': w.course.id, 'uid': w.b.actor.user_id})
    assert w.b.client.get(w.url).status_code == 404
    assert ask(w, sid, user=w.b).status_code == 404
    assert not w.model.tool_calls


@pytest.mark.parametrize('scope', ['module 4', ['module 1: Cơ sở'], 'Không phân giải được'])
def test_w09_tools_create_real_quiz3_document3_with_server_identity_and_core_scope(chat, scope):
    from copy import deepcopy
    from doc2roadmap.domain.learning_graph import LearningGraph
    from wayfinder.fakes.lecture import ScriptedLectureModel
    w = chat
    payload = deepcopy(w.graph.payload)
    base = deepcopy(payload['nodes'][0]); payload['nodes'], payload['modules'] = [], []
    for i in range(1, 5):
        nid, mid = f'n{i}', f'm{i}'
        payload['nodes'].append({**base, 'node_id': nid, 'module_id': mid})
        distractors = []
        for k, name in enumerate(['Phần tử', 'Quy tắc', 'Đặc điểm']):
            extra_id = f'{nid}_d{k}'; distractors.append(extra_id)
            payload['nodes'].append({**base, 'node_id': extra_id, 'name': name, 'display_name': name, 'module_id': mid})
        payload['modules'].append({'module_id': mid, 'title': f'Cơ sở {i}', 'index': i - 1, 'node_ids': [nid, *distractors]})
    payload['doc_id'] = 'doc-1'
    graph = LearningGraph(payload, list(w.graph.chunks.values())); graph.graph_version = 8
    w.gateway.graph_loader = lambda *_: graph; w.gateway._graphs.clear()
    doc_model = ScriptedLectureModel([['# Tài liệu ôn tập\n\nMột tập hợp gồm các phần tử. [S1]']])
    w.gateway.runtime.model_for = lambda purpose: w.model if purpose == 'assistant' else doc_model if purpose == 'document' else None
    w.model.tool_turns = [
        [ToolCall('make_quiz', {'scope': scope, 'n': 1, 'owner': 'forged', 'doc_id': 'other', 'graph_version': 999}, 'quiz'),
         ToolCall('make_document', {'request': 'Tóm tắt giúp tôi', 'scope': scope, 'owner': 'forged'}, 'doc'), Done({})],
        [Delta('Đã tạo xong. [Link giả](quiz:not-real)'), Done({})],
    ]
    sid = create(w, scope={'kind': 'module', 'module_id': 'm1'})['session_id']
    rows = events(ask(w, sid)); final = rows[-1]['answer']
    assert {row['artifact']['kind'] for row in rows if row['event'] == 'artifact'} == {'quiz', 'document'}, [
        (call['name'], call['result_summary']) for turn in w.phase_b.list_records('turn') for call in turn['answer'].get('tool_calls', [])]
    assert len(final['artifacts']) == 2
    timeline = [(row['event'], row.get('name') if row['event'] == 'tool_call' else row.get('artifact', {}).get('kind'), row.get('state')) for row in rows]
    assert timeline.index(('tool_call', 'make_quiz', 'running')) < timeline.index(('artifact', 'quiz', None))
    assert timeline.index(('tool_call', 'make_quiz', 'done')) < timeline.index(('tool_call', 'make_document', 'running'))
    assert timeline.index(('tool_call', 'make_document', 'done')) < timeline.index(('artifact', 'quiz', None))
    assert timeline.index(('tool_call', 'make_document', 'running')) < timeline.index(('artifact', 'document', None))
    expected = ['n4'] if scope == 'module 4' else ['n1']
    for item in final['artifacts']:
        raw = w.independent_store.get_record('quiz_attempt' if item['kind'] == 'quiz' else 'documents', item['id'])
        assert raw['owner'] == w.a.actor.user_id and raw['doc_id'] == 'doc-1'
        assert raw['node_ids'] == (expected if item['kind'] == 'quiz' else [expected[0], *[f'{expected[0]}_d{k}' for k in range(3)]])
        content = w.a.client.get(f"{w.url}/{sid}/artifacts/{item['kind']}/{item['id']}")
        assert content.status_code == 200 and content.json()['contract_version'] == ('quiz-3' if item['kind'] == 'quiz' else 'document-3')
        assert all(word not in content.text for word in ['_private', 'is_correct', 'validation', 'public_id', 'usage', 'cost_usd'])
        assert w.b.client.get(f"{w.url}/{sid}/artifacts/{item['kind']}/{item['id']}").status_code == 404
    assert 'forged' not in json.dumps(w.phase_b.list_records('quiz_attempt') + w.phase_b.list_records('documents'))
    assert 'result_summary' not in json.dumps(rows) and '"args"' not in json.dumps(rows)
    assert w.a.client.delete(f'{w.url}/{sid}', headers=w.a.headers).status_code == 200
    assert w.a.client.get(f'{w.url}/{sid}/turns').status_code == 404
    assert len(w.independent_store.list_records('documents', owner=w.a.actor.user_id)) == 1
    assert len(w.independent_store.list_records('quiz_attempt', owner=w.a.actor.user_id)) == 1
    library = w.a.client.get(f'/api/v1/courses/{w.course.id}/library?scope=all')
    assert library.status_code == 200
    assert {item['id'] for item in library.json()['items']} == {item['id'] for item in final['artifacts']}
    assert all(item['session_deleted'] for item in library.json()['items'])
    assert w.b.client.get(f'/api/v1/courses/{w.course.id}/library?scope=all').json()['items'] == []


def test_w09_two_concurrent_distinct_intents_are_serialized_not_coalesced(chat):
    from threading import Event, Thread
    from time import monotonic, sleep
    from wayfinder.fakes.assistant import ScriptedAssistantModel
    w = chat; model = ScriptedAssistantModel(pause=True); w.gateway.runtime.model = model
    sid = create(w)['session_id']; keys = [uuid4().hex, uuid4().hex]
    for i, key in enumerate(keys):
        w.gateway.prepare_turn(w.a.actor, w.course.id, sid, key, f'Câu hỏi {i}')
    results, errors, second_started = {}, [], Event()
    def run(i):
        try:
            if i == 1: second_started.set()
            rows = []
            w.gateway.ask_stream(w.a.actor, w.course.id, sid, keys[i], f'Câu hỏi {i}', rows.append)
            results[i] = rows[-1]['answer']
        except BaseException as error:
            errors.append(error)
    first, second = Thread(target=run, args=(0,)), Thread(target=run, args=(1,))
    try:
        first.start(); assert model.waiting.wait(5)
        second.start(); assert second_started.wait(2)
        deadline = monotonic() + 5
        waiting = 0
        while monotonic() < deadline:
            with w.independent_engine.connect() as c:
                waiting = c.scalar(text("SELECT count(*) FROM pg_locks l JOIN pg_stat_activity a USING(pid) WHERE a.datname=current_database() AND l.locktype='advisory' AND NOT l.granted"))
            if waiting: break
            sleep(.02)
        assert waiting == 1, 'Independent SQL must see the second turn waiting for the session lock'
        assert len(model.calls) == 1, 'The second intent must wait for the first session turn to be saved'
        model.release.set(); first.join(10); second.join(10)
        assert not first.is_alive() and not second.is_alive() and not errors
        assert results[0]['client_turn_id'] == keys[0] and results[1]['client_turn_id'] == keys[1]
        assert results[0]['answer_id'] != results[1]['answer_id'] and len(model.calls) == 2
        with w.independent_engine.connect() as c:
            rows = list(c.scalars(text("SELECT value->>'client_turn_id' FROM phase_b_record WHERE kind='turn'")))
        assert set(rows) == set(keys)
    finally:
        model.release.set()
        if first.ident: first.join(10)
        if second.ident: second.join(10)


def test_w09_http_disconnect_completes_and_retry_reuses_the_saved_turn(chat, monkeypatch):
    import socket
    from threading import Event, Thread
    from time import monotonic, sleep
    import httpx
    import uvicorn
    from wayfinder.fakes.assistant import ScriptedAssistantModel
    w = chat; model = ScriptedAssistantModel(pause=True); w.gateway.runtime.model = model
    sid = create(w)['session_id']; key = uuid4().hex
    observed = []
    def connection_event():
        e = Event(); observed.append(e); return e
    monkeypatch.setattr('wayfinder.api.assistant.Event', connection_event)
    listener = socket.socket(); listener.bind(('127.0.0.1', 0)); listener.listen(128)
    server = uvicorn.Server(uvicorn.Config(w.app, log_config=None, access_log=False, log_level='warning'))
    thread = Thread(target=server.run, kwargs={'sockets': [listener]}, daemon=True); thread.start()
    body = {'question': 'Phần này là gì?', 'client_turn_id': key, 'focus_node_id': 'a'}
    try:
        deadline = monotonic() + 5
        while not server.started and monotonic() < deadline: sleep(.01)
        assert server.started
        with httpx.Client(base_url=f'http://127.0.0.1:{listener.getsockname()[1]}', cookies=dict(w.a.client.cookies), timeout=10) as client:
            with client.stream('POST', f'{w.url}/{sid}/turns', headers=w.a.headers, json=body) as response:
                assert response.status_code == 200
                for line in response.iter_lines():
                    if line == 'event: delta': break
                else: pytest.fail('First assistant delta did not arrive before provider completion')
                assert model.waiting.wait(2) and not model.calls[0].finished
            assert len(observed) == 1 and observed[0].wait(3)
            assert not model.calls[0].finished
            model.release.set()
            deadline = monotonic() + 5
            while monotonic() < deadline and not w.independent_store.list_records('turn', owner=w.a.actor.user_id): sleep(.02)
            saved = w.independent_store.list_records('turn', owner=w.a.actor.user_id)
            assert len(saved) == 1 and saved[0]['client_turn_id'] == key
            assert 'x^2+y^2' in saved[0]['answer']['answer_md'] and 'Quiz tự bịa' in saved[0]['answer']['answer_md']
            retried = events(client.post(f'{w.url}/{sid}/turns', headers=w.a.headers, json=body))[-1]['answer']
            assert retried['answer_id'] == saved[0]['answer']['answer_id'] and len(model.calls) == 1
    finally:
        model.release.set(); server.should_exit = True; thread.join(10); listener.close()
        assert not thread.is_alive()


def test_w09_daily_limit_is_shared_across_courses_and_separate_for_each_learner(chat):
    w = chat; w.model.is_replay = False; w.model.model_id = 'gemini-3.1-flash-lite'
    w.phase_b.append_usage({'purpose': 'document', 'learner_id': w.a.actor.user_id, 'doc_id': 'another-book',
        'created_at': w.clock.now().isoformat(), 'cost_usd': 1.0})
    sid = create(w)['session_id']; final = events(ask(w, sid))[-1]['answer']
    assert final['status'] == 'daily_limit' and not w.model.tool_calls
    assert w.a.client.get('/api/v1/me/usage').json()['learner_today']['limited'] is True
    other = create(w, client=w.b)['session_id']
    assert events(ask(w, other, user=w.b))[-1]['answer']['status'] == 'answered'
    assert len(w.model.tool_calls) == 1


def test_w09_focus_reads_actual_lecture3_cache_and_a_cache_miss_never_generates(chat):
    from wayfinder.fakes.lecture import ScriptedLectureModel
    w = chat
    lecture = ScriptedLectureModel([['LECTURE_CACHE_SENTINEL. Nội dung bài có sẵn.']])
    w.gateway.runtime.model = lecture
    made = w.gateway.runtime.lecture(w.graph).make('doc-1', 8, w.graph, 'a', owner=w.a.actor.user_id, allow_spend=True)
    assert made['status'] == 'ready' and len(lecture.calls) == 1
    w.gateway.runtime.model = w.model
    sid = create(w)['session_id']; events(ask(w, sid, focus_node_id='a'))
    assert 'LECTURE_CACHE_SENTINEL' in json.dumps(w.model.tool_calls[0], ensure_ascii=False)
    with w.engine.begin() as c:
        c.execute(text("DELETE FROM phase_b_cache WHERE value->>'contract_version'='lecture-3'"))
    w.model.tool_turns.append([Delta('Cache miss vẫn trả lời.'), Done({})])
    events(ask(w, sid, focus_node_id='a'))
    current_context = w.model.tool_calls[-1][0][0]['text']
    assert 'LECTURE_CACHE_SENTINEL' not in current_context
    assert len(lecture.calls) == 1
    with w.independent_engine.connect() as c:
        assert c.scalar(text("SELECT count(*) FROM phase_b_cache WHERE value->>'contract_version'='lecture-3'")) == 0


def test_w09_ordinary_lecture_tool_generates_through_http_and_postgresql(chat):
    w = chat
    model = ScriptedModel(tool_turns=[
        [ToolCall('get_lecture', {'concept': 'a'}, 'open-lecture'), Done({})],
        [Delta('Đã mở bài học được yêu cầu.'), Done({})],
    ], text_replies=[['HTTP_PG_LECTURE_SENTINEL. Nội dung bài mới. [S1]']])
    w.gateway.runtime.model = model
    sid = create(w)['session_id']
    result = events(ask(w, sid))
    assert result[-1]['answer']['status'] == 'answered'
    assert len(model.text_calls) == 1
    artifact = next(row['artifact'] for row in result if row['event'] == 'artifact')
    assert artifact['kind'] == 'lecture' and artifact['node_id'] == 'a'
    with w.independent_engine.connect() as c:
        cached = c.scalar(text("SELECT value FROM phase_b_cache WHERE value->>'contract_version'='lecture-3'"))
        assert cached['status'] == 'ready' and 'HTTP_PG_LECTURE_SENTINEL' in cached['body_md']
        assert c.scalar(text("SELECT owner FROM phase_b_record WHERE kind='session' AND record_id=:sid"), {'sid': sid}) == w.a.actor.user_id
    assert len(w.b.client.get(w.url).json()['sessions']) == 0


def test_w09_sse_dto_discards_tool_args_and_nested_admin_data_even_from_bad_gateway(chat, monkeypatch):
    w = chat; sid = create(w)['session_id']
    raw = events(ask(w, sid))[-1]['answer']
    raw.update(validation={'ADMIN_SENTINEL': True}, public_id='PRIVATE_SENTINEL', usage={'cost_usd': 10})
    raw['sources'][0].update(public_id='PRIVATE_SENTINEL')
    def bad_gateway(actor, cid, sid, key, question, emit, focus):
        emit({'event': 'tool_call', 'name': 'search_document', 'args': {'owner': 'PRIVATE_SENTINEL'},
            'text': 'PRIVATE_SENTINEL', 'result_summary': {'validation': 'ADMIN_SENTINEL'}})
        emit({'event': 'admin_log', 'validation': 'ADMIN_SENTINEL'})
        emit({'event': 'final', 'answer': raw, 'validation': 'ADMIN_SENTINEL'})
    monkeypatch.setattr(w.gateway, 'ask_stream', bad_gateway)
    response = ask(w, sid)
    assert response.status_code == 200
    assert all(word not in response.text for word in ['ADMIN_SENTINEL', 'PRIVATE_SENTINEL', '"args"', 'validation', 'cost_usd', 'public_id', 'admin_log'])
    assert events(response)[0]['text'] == 'Đang tìm trong tài liệu…'


@pytest.mark.parametrize('foreign', ['owner', 'doc_id', 'status'])
def test_w09_artifact_card_and_content_recheck_owner_book_and_ready_state(chat, foreign):
    w = chat; sid = create(w)['session_id']; aid = uuid4().hex
    row = {'contract_version': 'document-3', 'document_id': aid, 'owner': w.a.actor.user_id,
        'doc_id': 'doc-1', 'status': 'ready', 'title': 'Private document', 'markdown': 'SECRET_OTHER_ARTIFACT', 'sources': []}
    row[foreign] = {'owner': w.b.actor.user_id, 'doc_id': 'other-book', 'status': 'failed'}[foreign]
    w.phase_b.put_record('documents', aid, row)
    session = w.phase_b.get_record('session', sid)
    session['artifact_refs'] = [{'kind': 'document', 'artifact_id': aid}]
    w.phase_b.put_record('session', sid, session)
    course, graph = w.gateway._context(w.a.actor, w.course.id)
    assert w.gateway._artifact(w.a.actor, course, graph, {'kind': 'document', 'id': aid}) is None
    response = w.a.client.get(f'{w.url}/{sid}/artifacts/document/{aid}')
    assert response.status_code == 404 and 'SECRET_OTHER_ARTIFACT' not in response.text


def test_w09_composition_uses_role_models_with_shared_vertex_credentials_without_live_auth(w07):
    from types import SimpleNamespace
    from wayfinder.composition import compose_services
    from doc2roadmap.config import Settings
    calls = []
    def factory(*args, **kwargs):
        model = SimpleNamespace(options=kwargs)
        calls.append(model)
        return model
    configured = w07.courses.settings.model_copy(update={'database_url': w07.engine.url.render_as_string(hide_password=False)})
    services = compose_services(configured, health_check=lambda: 'ok',
        phase_b_store=w07.phase_b, clock=w07.clock, graph_loader=lambda *_: w07.graph,
        auth_validator=lambda *_: None, model_factory=factory, embedding_factory=factory,
        core_settings=Settings(_env_file=None, llm_transport='vertex', vertex_project='fake-project', vertex_location='us-central1'))
    try:
        runtime = services.learning.runtime
        assistant = runtime.model_for('assistant'); document = runtime.model_for('document')
        assert assistant is runtime.model_for('assistant') and document is runtime.model_for('document')
        assert assistant is not document and assistant is not services.model
        assert assistant.options['max_output_tokens'] == runtime.settings.assistant_max_output_tokens
        assert document.options['max_output_tokens'] == runtime.settings.document_max_output_tokens
        assert all(model.options['transport'] == 'vertex' for model in calls)
        assert len({id(model.options['vertex_credentials']) for model in calls}) == 1
    finally:
        services.close()
