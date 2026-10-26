"""Independent HTTP/PG counterexample; only scripted models and fixture actors."""
import json
from pathlib import Path
from uuid import uuid4
from sqlalchemy import text
from test_content_w10 import content
from test_learning_progress_w07 import w07
from wayfinder.fakes.assistant import ScriptedAssistantModel

OUT=Path(__file__).resolve().parents[4] / 'report/w10-r7-evidence'

def test_documents_per_hour_applies_across_button_and_assistant(content):
    w=content
    for _ in range(10):
        r=w.a.client.post(w.base+'/documents',headers=w.a.headers,json={'request':'Ôn tập','module_ids':['m1']})
        assert r.status_code==201 and r.json()['status']=='ready',r.text
    denied=w.a.client.post(w.base+'/documents',headers=w.a.headers,json={'request':'Ôn tập','module_ids':['m1']})
    assert denied.status_code==429 and denied.json()['error']['code']=='rate_limited'
    assert len(w.document.calls)==10
    with w.independent_engine.connect() as c:
        before=c.scalar(text("SELECT count(*) FROM phase_b_record WHERE kind='documents' AND owner=:owner"),{'owner':w.a.actor.user_id})
        rate_before=c.scalar(text("SELECT count(*) FROM rate_limit_event WHERE bucket=:bucket"),{'bucket':'document:'+w.a.actor.user_id})
    assert before==rate_before==10
    assistant=ScriptedAssistantModel(scenario='tools')
    original=w.gateway.runtime.model_for
    w.gateway.runtime.model_for=lambda purpose: assistant if purpose=='assistant' else original(purpose)
    made=w.a.client.post(w.base+'/sessions',headers=w.a.headers,json={'scope':{'kind':'module','module_id':'m1'}})
    assert made.status_code==201,made.text
    response=w.a.client.post(w.base+'/sessions/'+made.json()['session_id']+'/turns',headers=w.a.headers,
        json={'question':'Hãy tạo tài liệu ôn tập.','client_turn_id':uuid4().hex})
    assert response.status_code==200,response.text
    with w.independent_engine.connect() as c:
        rows=list(c.execute(text("SELECT value FROM phase_b_record WHERE kind='documents' AND owner=:owner ORDER BY record_id"),{'owner':w.a.actor.user_id}).scalars())
        rate_after=c.scalar(text("SELECT count(*) FROM rate_limit_event WHERE bucket=:bucket"),{'bucket':'document:'+w.a.actor.user_id})
    observed={'before_documents':before,'after_documents':len(rows),'document_model_calls':len(w.document.calls),
      'direct_over_limit_status':denied.status_code,'assistant_http_status':response.status_code,'rate_bucket_before':rate_before,
      'rate_bucket_after':rate_after,'assistant_ready_documents':sum(r.get('origin')=='assistant' and r.get('status')=='ready' for r in rows),
      'external_cost_usd':0,'test_source':'test_coord_r7_rate_origin.py','expected_model_calls':10}
    (OUT/'observed.json').write_text(json.dumps(observed,indent=2)+'\n',encoding='utf8')
    print(json.dumps(observed))
    assert len(w.document.calls)==10,'11th document must be refused before generation regardless of creation origin'
    assert len(rows)==10


def test_hourly_document_limit_has_safe_tool_error_and_persistent_public_chat_notice(content):
    w = content
    w.courses.settings.documents_per_hour = 1
    first = w.a.client.post(w.base+'/documents', headers=w.a.headers, json={'request':'Ôn', 'module_ids':['m1']})
    assert first.status_code == 201
    assistant = ScriptedAssistantModel(scenario='tools')
    original = w.gateway.runtime.model_for
    w.gateway.runtime.model_for = lambda purpose: assistant if purpose == 'assistant' else original(purpose)
    session = w.a.client.post(w.base+'/sessions', headers=w.a.headers, json={'scope':{'kind':'module','module_id':'m1'}}).json()
    url = w.base+'/sessions/'+session['session_id']+'/turns'
    response = w.a.client.post(url, headers=w.a.headers, json={'question':'Tạo tài liệu', 'client_turn_id':uuid4().hex})
    assert response.status_code == 200
    assert len(w.document.calls) == 1
    tool = next(call for row in w.independent_store.list_records('turn') for call in row['answer']['tool_calls'] if call['name'] == 'make_document')
    assert tool['result_summary']['error']['code'] == 'rate_limited'
    assert 'giờ' in tool['result_summary']['error']['message']
    assert tool['result_summary']['error']['retry_after'] > 0
    final = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ') and '"answer"' in line][-1]['answer']
    assert 'document_rate_limited' in final['warnings']
    assert not any(a['kind'] == 'document' for a in final['artifacts'])
    saved = w.a.client.get(url).json()['turns'][-1]['answer']
    assert 'document_rate_limited' in saved['warnings']
    assert 'tool_calls' not in response.text and 'result_summary' not in response.text


def setup_document_chat(w, gateway=None):
    from wayfinder.testing import ScriptedModel
    from doc2roadmap.application.ports.phase_b import ToolCall, Delta, Done
    gateway = gateway or w.gateway
    model = ScriptedModel(tool_turns=[
        [ToolCall('make_document', {'request':'Ôn bài', 'scope':'module này', 'owner':'forged'}, 'doc'), Done({})],
        [Delta('Tôi đã kiểm tra yêu cầu.'), Done({})],
    ])
    model.is_replay = True
    original = gateway.runtime.model_for
    gateway.runtime.model_for = lambda purpose: model if purpose == 'assistant' else original(purpose)
    return model


def ask_document(w, *, user=None, cid=None, key=None):
    user, cid = user or w.a, cid or w.course.id
    setup_document_chat(w)
    base = '/api/v1/courses/'+cid+'/sessions'
    session = user.client.post(base, headers=user.headers, json={'scope':{'kind':'module','module_id':'m1'}})
    assert session.status_code == 201, session.text
    response = user.client.post(base+'/'+session.json()['session_id']+'/turns', headers=user.headers,
        json={'question':'Tạo tài liệu', 'client_turn_id':key or uuid4().hex})
    assert response.status_code == 200, response.text
    final = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ') and '"answer"' in line][-1]['answer']
    return final, base+'/'+session.json()['session_id']+'/turns'


def counts(w, owner):
    with w.independent_engine.connect() as c:
        return (c.scalar(text("SELECT count(*) FROM rate_limit_event WHERE bucket=:bucket"), {'bucket':'document:'+owner}),
            c.scalar(text("SELECT count(*) FROM phase_b_record WHERE kind='documents' AND owner=:owner AND value->>'status'='ready'"), {'owner':owner}))


def test_assistant_to_button_is_single_admission_across_courses_and_separate_per_person(content):
    w = content; w.courses.settings.documents_per_hour = 2
    key = uuid4().hex
    made, url = ask_document(w, key=key)
    assert len(made['artifacts']) == 1 and made['artifacts'][0]['kind'] == 'document'
    retry = w.a.client.post(url, headers=w.a.headers, json={'question':'Tạo tài liệu','client_turn_id':key})
    assert retry.status_code == 200
    assert counts(w, w.a.actor.user_id) == (1, 1)
    assert len(w.document.calls) == 1
    other = w.courses.create_course(w.a.actor, doc_id='doc-1', title='Other', graph_version=8, module_count=1)
    button = '/api/v1/courses/'+other.id+'/documents'
    allowed = w.a.client.post(button, headers=w.a.headers, json={'request':'Ôn', 'module_ids':['m1']})
    assert allowed.status_code == 201
    denied = w.a.client.post(w.base+'/documents', headers=w.a.headers, json={'request':'Ôn', 'module_ids':['m1']})
    assert denied.status_code == 429
    limited, _ = ask_document(w, cid=other.id)
    assert 'document_rate_limited' in limited['warnings'] and limited['artifacts'] == []
    assert counts(w, w.a.actor.user_id) == (2, 2)
    assert len(w.document.calls) == 2
    other_person, _ = ask_document(w, user=w.b)
    assert len(other_person['artifacts']) == 1
    assert counts(w, w.b.actor.user_id) == (1, 1)
    assert len(w.document.calls) == 3
    assert counts(w, 'forged') == (0, 0)


def test_two_independent_runtime_origins_compete_for_only_one_remaining_document_admission(content):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    w = content; w.courses.settings.documents_per_hour = 2
    first = w.a.client.post(w.base+'/documents', headers=w.a.headers, json={'request':'Ôn', 'module_ids':['m1']})
    assert first.status_code == 201
    setup_document_chat(w, w.other_gateway)
    session = w.other_gateway.create_session(w.a.actor, w.course.id, {'kind':'module','module_id':'m1'})
    gate = Barrier(2)
    def button():
        gate.wait()
        response = w.a.client.post(w.base+'/documents', headers=w.a.headers, json={'request':'Ôn', 'module_ids':['m1']})
        assert response.status_code in (201,429)
        return response.status_code == 201
    def assistant():
        gate.wait()
        rows = []
        w.other_gateway.ask_stream(w.a.actor, w.course.id, session['session_id'], uuid4().hex, 'Tạo tài liệu', rows.append)
        final = next(row['answer'] for row in rows if row['event']=='final')
        if final['artifacts']:
            assert len(final['artifacts']) == 1 and final['artifacts'][0]['kind'] == 'document'
            return True
        assert 'document_rate_limited' in final['warnings']
        return False
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = [pool.submit(button), pool.submit(assistant)]
        assert sum(task.result(timeout=15) for task in outcomes) == 1
    assert counts(w, w.a.actor.user_id) == (2, 2)
    assert len(w.document.calls) == 2


def test_admission_waits_for_the_other_postgres_runtime_before_rechecking_the_last_slot(content):
    import pytest
    from concurrent.futures import ThreadPoolExecutor
    from time import monotonic, sleep
    from sqlalchemy import event
    from wayfinder.api.errors import WebError
    w = content; w.courses.settings.documents_per_hour = 2
    assert w.a.client.post(w.base+'/documents', headers=w.a.headers, json={'request':'Ôn', 'module_ids':['m1']}).status_code == 201
    policy = w.other_gateway.runtime.document_requests
    backend_pid = {}
    def observe(connection, cursor, statement, parameters, context, executemany):
        if 'pg_advisory_xact_lock' in statement:
            backend_pid['value'] = connection.connection.driver_connection.info.backend_pid
    event.listen(w.independent_engine, 'before_cursor_execute', observe)
    pool = ThreadPoolExecutor(max_workers=1)
    try:
        with w.engine.begin() as transaction:
            bucket = 'document:'+w.a.actor.user_id
            transaction.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:bucket,0))'), {'bucket':bucket})
            future = pool.submit(policy.admit, w.a.actor.user_id)
            waiting = False; deadline = monotonic()+5
            while monotonic()<deadline and not future.done():
                with w.independent_engine.connect() as probe:
                    waiting = probe.scalar(text("SELECT wait_event_type='Lock' FROM pg_stat_activity WHERE pid=:pid"), {'pid':backend_pid.get('value')})
                if waiting: break
                sleep(.01)
            assert waiting, 'the independent runtime must wait for the held PostgreSQL account lock'
            transaction.execute(text('INSERT INTO rate_limit_event(bucket,at) VALUES(:bucket,:now)'), {'bucket':bucket,'now':w.clock.now()})
        with pytest.raises(WebError) as denied:
            future.result(timeout=5)
        assert denied.value.code == 'rate_limited'
        assert counts(w,w.a.actor.user_id) == (2,1)
        assert len(w.document.calls) == 1
    finally:
        pool.shutdown(wait=True)
        event.remove(w.independent_engine, 'before_cursor_execute', observe)
