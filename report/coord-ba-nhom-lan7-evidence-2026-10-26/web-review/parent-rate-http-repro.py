"""Independent HTTP/PG counterexample; only scripted models and fixture actors."""
import json
from pathlib import Path
from uuid import uuid4
from sqlalchemy import text
from test_content_w10 import content
from test_learning_progress_w07 import w07
from wayfinder.fakes.assistant import ScriptedAssistantModel

OUT=Path('C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-r7-tools-20261026/http-repro')

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
