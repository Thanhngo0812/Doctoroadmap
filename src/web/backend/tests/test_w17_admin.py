"""W17.1: real cookies/PostgreSQL, fake external dependencies, synthetic data only."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import json
import os
import re
from pathlib import Path
from threading import Barrier
from types import SimpleNamespace
from time import sleep
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import text

from doc2roadmap.config import Settings
from wayfinder.api.app import create_app
from wayfinder.composition import compose_services
from wayfinder.domain.auth import Actor
from wayfinder.testing import build_test_application
from wayfinder.settings import WebSettings
from wayfinder.application.accounts import AuthError

ORIGIN = 'https://testserver'
PASSWORD = 'W17 synthetic local passphrase!'


@pytest.fixture
def admin_case(empty_postgres_database_url, monkeypatch, request):
    from wayfinder.infrastructure.database import upgrade_database
    upgrade_database(empty_postgres_database_url)
    bundle = build_test_application()
    clock = bundle.phase_b.clock
    settings = WebSettings(
        _env_file=None, database_url=empty_postgres_database_url.render_as_string(hide_password=False),
        frontend_dist=Path('missing'), public_base_url=ORIGIN, allowed_origins=[ORIGIN],
        artifact_root=Path('tmp/w17-artifacts'))
    attempted = []
    def forbidden(*args, **kwargs):
        attempted.append(True)
        raise AssertionError('W17 forbids provider/ADC/SMTP/Cloudinary')
    for target in ('doc2roadmap.infrastructure.llm.gemini.urlopen',
        'doc2roadmap.infrastructure.llm.phase_b.urlopen',
        'doc2roadmap.infrastructure.embedding.gemini.urlopen',
        'doc2roadmap.infrastructure.google_auth.VertexCredentials.headers',
        'google.auth.default', 'smtplib.SMTP', 'cloudinary.uploader.upload'):
        monkeypatch.setattr(target, forbidden)
    monkeypatch.setattr('wayfinder.composition.compose_mailer', lambda _: bundle.mailer)
    services = compose_services(settings, core_settings=Settings(_env_file=None,
        llm_transport='vertex', vertex_project='w17-no-network', vertex_location='global'),
        auth_validator=lambda *_: None, model_factory=lambda *a, **k: bundle.phase_b.model,
        embedding_factory=lambda *a, **k: bundle.phase_b.embedding, clock=clock,
        graph_loader=lambda *_: bundle.phase_b.graph, build_media=bundle.media_store)
    services.accounts.clock = clock
    app = create_app(settings, services)
    clients = []
    def user(admin=False):
        address = uuid4().hex + '@example.vn'
        if admin:
            account = services.accounts.create_admin(address, PASSWORD)
        client = TestClient(app, base_url=ORIGIN)
        clients.append(client)
        response = client.post('/api/v1/auth/login' if admin else '/api/v1/auth/register',
            headers={'Origin': ORIGIN}, json={'email': address, 'password': PASSWORD,
                **({} if admin else {'display_name': 'Người học'})})
        assert response.status_code == 200, response.text
        identity = client.get('/api/v1/me').json()['account']
        return SimpleNamespace(client=client, id=identity['id'], email=address,
            actor=Actor(identity['id'], identity['role'], identity['email_verified'], 'active'))
    owner, learner = user(True), user()
    rt = SimpleNamespace(services=services, app=app, clock=clock, settings=settings,
        engine=services.accounts.store.engine, owner=owner, learner=learner, user=user)
    try:
        yield rt
    finally:
        record('sql-proof/'+re.sub(r'[^A-Za-z0-9_.-]','_',request.node.name), {
            'source':'Independent PostgreSQL connection; synthetic accounts; no provider spend',
            'accounts':sql(rt,'SELECT id,role,status,build_monthly_max FROM account WHERE id IN (:a,:b)',a=owner.id,b=learner.id),
            'sessions':sql(rt,'SELECT account_id,count(*) AS sessions FROM auth_session WHERE account_id IN (:a,:b) GROUP BY account_id',a=owner.id,b=learner.id),
            'audit':sql(rt,'SELECT action,target_kind,target_id,ip FROM audit_event WHERE actor_id=:a',a=owner.id)})
        for client in clients:
            client.close()
        services.close()
    assert attempted == []
    assert bundle.phase_b.model.json_calls == bundle.phase_b.embedding.requests == []


def headers(user):
    return {'Origin': ORIGIN, 'X-CSRF-Token': user.client.get('/api/v1/me').json()['csrf_token']}


def sql(rt, query, **params):
    with rt.engine.connect() as connection:
        return [dict(row) for row in connection.execute(text(query), params).mappings()]


def patch(rt, data, *, target=None, actor=None):
    return (actor or rt.owner).client.patch('/api/v1/admin/users/' + (target or rt.learner).id,
        headers=headers(actor or rt.owner), json=data)


def record(name, data):
    run = os.environ.get('W17_EVIDENCE_RUN')
    if run:
        path = Path(os.environ.get('W17_EVIDENCE_ROOT','report/w17-evidence')) / run / (name + '.json')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str)+'\n', encoding='utf-8')


def test_users_public_projection_search_and_demo_null(admin_case):
    rt = admin_case
    rt.services.courses.create_course(rt.learner.actor, doc_id='w17-' + uuid4().hex,
        title='Private course', graph_version=1, module_count=1)
    response = rt.owner.client.get('/api/v1/admin/users', params={'email': rt.learner.email.upper()})
    assert response.status_code == 200, response.text
    view = response.json()
    assert view['total'] == 1 and len(view['items']) == 1
    item = view['items'][0]
    assert item['id'] == rt.learner.id and item['owned_courses'] == 1
    assert item['builds_this_month'] == {'used': 0, 'max': None, 'resets_at': '2026-02-01T00:00:00+07:00'}
    assert item['build_monthly_max'] is None and item['created_at']
    assert not {'password_hash', 'token_hash', 'csrf_token', 'email_normalized'} & item.keys()
    record('users', view)


def test_disable_revokes_two_cookies_enable_never_resurrects(admin_case):
    rt = admin_case
    second = TestClient(rt.app, base_url=ORIGIN)
    try:
        assert second.post('/api/v1/auth/login', headers={'Origin': ORIGIN},
            json={'email': rt.learner.email, 'password': PASSWORD}).status_code == 200
        assert len(sql(rt, 'SELECT id FROM auth_session WHERE account_id=:uid', uid=rt.learner.id)) == 2
        response = patch(rt, {'status': 'disabled'})
        assert response.status_code == 200, response.text
        assert sql(rt, 'SELECT id FROM auth_session WHERE account_id=:uid', uid=rt.learner.id) == []
        assert rt.learner.client.get('/api/v1/me').status_code == second.get('/api/v1/me').status_code == 401
        assert second.post('/api/v1/auth/login', headers={'Origin': ORIGIN},
            json={'email': rt.learner.email, 'password': PASSWORD}).json()['error']['code'] == 'account_disabled'
        assert patch(rt, {'status': 'active'}).status_code == 200
        assert rt.learner.client.get('/api/v1/me').status_code == second.get('/api/v1/me').status_code == 401
        assert second.post('/api/v1/auth/login', headers={'Origin': ORIGIN},
            json={'email': rt.learner.email, 'password': PASSWORD}).status_code == 200
        audit = sql(rt, "SELECT action,actor_id,target_kind,target_id,meta FROM audit_event WHERE actor_id=:uid AND action LIKE 'admin_user_%'", uid=rt.owner.id)
        assert [row['action'] for row in audit] == ['admin_user_disabled', 'admin_user_enabled']
        assert all(row['meta'] == {} and row['target_id'] == rt.learner.id for row in audit)
        record('disable', response.json()); record('audit-sql', audit)
    finally:
        second.close()


def test_last_admin_demote_rejected(admin_case):
    rt = admin_case
    # The session database is shared by tests: make this fixture's owner the only admin.
    with rt.engine.begin() as connection:
        connection.execute(text("UPDATE account SET role='user' WHERE role='admin' AND id<>:uid"), {'uid':rt.owner.id})
    response = patch(rt, {'role': 'user'}, target=rt.owner)
    assert response.status_code == 409 and response.json()['error']['code'] == 'protected_admin'
    assert sql(rt, 'SELECT role FROM account WHERE id=:uid', uid=rt.owner.id) == [{'role':'admin'}]
    record('last-admin-conflict',response.json())


def admin_routes(router):
    for route in router.routes:
        included = getattr(route, 'original_router', None)
        if included is not None:
            yield from admin_routes(included)
        elif getattr(route, 'path', '').startswith('/api/v1/admin/'):
            for method in route.methods - {'OPTIONS', 'HEAD'}:
                yield route, method


def assert_admin_routes_protected(rt):
    routes = list(admin_routes(rt.app))
    assert {route.path for route, _ in routes} >= {'/api/v1/admin/users', '/api/v1/admin/users/{uid}', '/api/v1/admin/audit'}
    with TestClient(rt.app, base_url=ORIGIN) as guest:
        for route, method in routes:
            path = route.path.replace('{uid}', rt.learner.id)
            body = {'status':'disabled'} if method == 'PATCH' else None
            for client, extra, status, code in ((rt.learner.client, headers(rt.learner),403,'forbidden'),
                (guest, {'Origin':ORIGIN},401 if method=='GET' else 403,'unauthenticated' if method=='GET' else 'csrf_failed')):
                response = client.request(method,path,headers=extra,json=body)
                assert response.status_code == status, response.text
                assert response.json()['error']['code'] == code
                assert response.headers['cache-control'] == 'no-store'


def test_all_admin_routes_require_admin_and_no_store(admin_case):
    assert_admin_routes_protected(admin_case)


def test_admin_inventory_detects_an_unguarded_new_route(admin_case):
    rt = admin_case
    @rt.app.get('/api/v1/admin/unguarded-probe')
    def unguarded():
        return {'leaked':True}
    with pytest.raises(AssertionError):
        assert_admin_routes_protected(rt)


def test_update_and_audit_rollback_on_audit_failure(admin_case, monkeypatch):
    rt = admin_case
    store = rt.services.admin.store
    def fail(event):
        raise RuntimeError('synthetic audit write failure')
    monkeypatch.setattr(store, 'append_audit', fail)
    before = sql(rt, 'SELECT status,role,build_monthly_max FROM account WHERE id=:uid',uid=rt.learner.id)
    response = patch(rt, {'status':'disabled','role':'admin','build_monthly_max':7})
    assert response.status_code == 500
    assert sql(rt, 'SELECT status,role,build_monthly_max FROM account WHERE id=:uid',uid=rt.learner.id) == before
    assert rt.learner.client.get('/api/v1/me').status_code == 200


@pytest.mark.parametrize('data', [{}, {'role':None}, {'status':None}, {'status':'deleted'},
    {'role':'root'}, {'email':'other@example.vn'}, {'id':'someone'}, {'password_hash':'fake'},
    {'build_monthly_max':0}, {'build_monthly_max':-1}, {'build_monthly_max':True},
    {'build_monthly_max':'3'}, {'build_monthly_max':2147483648},
    {'status':'disabled','owner_id':'attacker'}])
def test_invalid_patch_fields_never_change_account_or_sessions(admin_case, data):
    rt = admin_case
    before = sql(rt,'SELECT status,role,build_monthly_max,updated_at FROM account WHERE id=:uid',uid=rt.learner.id)
    response = patch(rt,data)
    assert response.status_code == 422 and response.json()['error']['code']=='validation', response.text
    assert response.json()['error']['fields']
    if data=={'role':'root'}:
        record('validation',response.json())
    assert sql(rt,'SELECT status,role,build_monthly_max,updated_at FROM account WHERE id=:uid',uid=rt.learner.id)==before
    assert rt.learner.client.get('/api/v1/me').status_code==200


def test_patch_quota_override_null_fallback_role_and_idempotent_audit(admin_case):
    rt = admin_case
    response = patch(rt,{'role':'admin','build_monthly_max':8})
    assert response.status_code==200 and response.json()['builds_this_month']['max']==8
    assert rt.learner.client.get('/api/v1/admin/users').status_code==200
    assert patch(rt,{'role':'admin','build_monthly_max':8}).status_code==200
    assert len(sql(rt,"SELECT id FROM audit_event WHERE actor_id=:uid AND action LIKE 'admin_user_%'",uid=rt.owner.id))==2
    rt.services.admin.settings=rt.settings.model_copy(update={'build_monthly_max':3})
    response=patch(rt,{'role':'user','build_monthly_max':None})
    assert response.status_code==200
    assert response.json()['build_monthly_max'] is None and response.json()['builds_this_month']['max']==3
    assert rt.settings.build_monthly_max is None
    assert rt.learner.client.get('/api/v1/admin/users').status_code==403
    record('patch-quota',response.json())


@pytest.mark.parametrize('params', [{'limit':0},{'limit':101},{'offset':-1},{'offset':100001},
    {'role':'root'},{'status':'gone'},{'email':'x'*255}])
def test_users_filters_are_bounded(admin_case,params):
    response=admin_case.owner.client.get('/api/v1/admin/users',params=params)
    assert response.status_code==422 and response.json()['error']['fields']
    assert response.headers['cache-control']=='no-store'


def test_pagination_literal_email_filters_and_last_login(admin_case):
    rt=admin_case
    second=rt.user()
    response=rt.owner.client.get('/api/v1/admin/users',params={'email':'example.vn','limit':1})
    first=response.json()
    next_page=rt.owner.client.get('/api/v1/admin/users',params={'email':'example.vn','limit':1,'offset':1}).json()
    assert len(first['items'])==len(next_page['items'])==1 and first['items'][0]['id']!=next_page['items'][0]['id']
    assert first['total']==next_page['total']>=3
    assert rt.owner.client.get('/api/v1/admin/users',params={'email':"%' OR 1=1 --"}).json()['total']==0
    assert rt.owner.client.get('/api/v1/admin/users',params={'email':rt.owner.email,'role':'admin','status':'active'}).json()['items'][0]['last_login_at']
    assert rt.owner.client.get('/api/v1/admin/users',params={'email':second.email,'role':'admin'}).json()['total']==0


def test_two_postgres_runtimes_keep_first_admin_while_demoting_later_admin(admin_case):
    from wayfinder.application.admin import AdminService
    from wayfinder.infrastructure.admin_store import PostgresAdminStore
    from wayfinder.infrastructure.database import create_database_engine
    rt=admin_case
    second=rt.user(True)
    with rt.engine.begin() as connection:
        connection.execute(text("UPDATE account SET role='user' WHERE role='admin' AND id NOT IN (:a,:b)"),{'a':rt.owner.id,'b':second.id})
    engine=create_database_engine(rt.engine.url)
    other=AdminService(PostgresAdminStore(engine),settings=rt.settings,clock=rt.clock)
    services=[rt.services.admin,other]
    barrier=Barrier(2)
    def demote(pair):
        service,user=pair
        barrier.wait(5)
        try:
            service.update_user(user.actor,user.id,{'role':'user'})
            return 'changed'
        except AuthError as error:
            return error.code
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(demote,zip(services,[rt.owner,second])))
        assert sorted(results)==['changed','protected_admin']
        remaining=sql(rt,"SELECT id FROM account WHERE role='admin'")
        assert len(remaining)==1
        assert sum(user.client.get('/api/v1/admin/users').status_code==200 for user in (rt.owner,second))==1
        record('concurrent-demotion',{'results':results,'admins':remaining})
    finally:
        engine.dispose()


def test_stale_admin_actor_and_unauthorized_patch_cannot_write(admin_case):
    rt=admin_case
    second=rt.user(True)
    assert patch(rt,{'role':'user'},target=second).status_code==200
    before=sql(rt,'SELECT status FROM account WHERE id=:id',id=rt.learner.id)
    with pytest.raises(AuthError) as error:
        rt.services.admin.update_user(second.actor,rt.learner.id,{'status':'disabled'})
    assert error.value.code=='forbidden'
    response=patch(rt,{'status':'disabled'},actor=second)
    assert response.status_code==403
    record('forbidden',response.json())
    assert sql(rt,'SELECT status FROM account WHERE id=:id',id=rt.learner.id)==before
    assert rt.learner.client.get('/api/v1/me').status_code==200


def test_csrf_and_origin_required_and_missing_user_is_stable(admin_case):
    rt=admin_case
    path='/api/v1/admin/users/'+rt.learner.id
    for bad in ({'Origin':ORIGIN},{**headers(rt.owner),'Origin':'https://evil.invalid'}):
        response=rt.owner.client.patch(path,headers=bad,json={'status':'disabled'})
        assert response.status_code==403 and response.json()['error']['code']=='csrf_failed'
    response=rt.owner.client.patch('/api/v1/admin/users/'+str(uuid4()),headers=headers(rt.owner),json={'status':'disabled'})
    assert response.status_code==404 and response.json()['error']['code']=='not_found'
    assert rt.learner.client.get('/api/v1/me').status_code==200


def test_disabling_only_first_admin_is_rejected_and_preserves_session(admin_case):
    rt=admin_case
    with rt.engine.begin() as connection:
        connection.execute(text("UPDATE account SET role='user' WHERE role='admin' AND id<>:uid"),{'uid':rt.owner.id})
    response=patch(rt,{'status':'disabled'},target=rt.owner)
    assert response.status_code==409 and response.json()['error']['code']=='protected_admin'
    assert len(sql(rt,'SELECT id FROM auth_session WHERE account_id=:uid',uid=rt.owner.id))==1
    assert rt.owner.client.get('/api/v1/me').status_code==200
    assert sql(rt,'SELECT role,status FROM account WHERE id=:uid',uid=rt.owner.id)==[{'role':'admin','status':'active'}]
    record('last-admin-protected',response.json())


def test_audit_filters_half_open_dates_and_never_exposes_arbitrary_meta(admin_case):
    from wayfinder.application.auth_ports import AuditEvent
    rt=admin_case
    start=rt.clock.now()
    marker='W17_PRIVATE_AUDIT_CONTENT_SENTINEL'
    for seconds in (-1,0,59,60):
        rt.services.accounts.store.append_audit(AuditEvent(start+timedelta(seconds=seconds),rt.learner.id,
            'password_changed','account',rt.learner.id,'127.0.0.1',{'password_hash':marker,'token':marker,'extra':{'chat':marker}}))
    params={'actor_id':rt.learner.id,'action':'password_changed','since':start.isoformat(),
        'until':(start+timedelta(minutes=1)).isoformat(),'limit':1}
    first=rt.owner.client.get('/api/v1/admin/audit',params=params)
    assert first.status_code==200,first.text
    assert first.json()['total']==2 and len(first.json()['items'])==1
    second=rt.owner.client.get('/api/v1/admin/audit',params={**params,'offset':1})
    assert second.json()['items'][0]['id']!=first.json()['items'][0]['id']
    assert marker not in first.text+second.text and 'meta' not in first.text
    assert set(first.json()['items'][0])=={'id','at','actor_id','action','target_kind','target_id','ip'}
    assert first.json()['items'][0]['ip']=='127.0.0.1'
    direct=rt.services.admin.list_audit(rt.owner.actor,actor_id=rt.learner.id,action='password_changed',
        since=start,until=start+timedelta(minutes=1))
    assert marker not in json.dumps(direct,default=str) and all('meta' not in row for row in direct['items'])
    record('audit',first.json())


@pytest.mark.parametrize('params',[{'since':'2026-01-01T00:00:00'},
    {'since':'2026-01-02T00:00:00Z','until':'2026-01-01T00:00:00Z'},
    {'actor_id':'not-a-uuid'},{'action':'x'*81},{'action':'bad action'},{'limit':101},{'offset':100001}])
def test_audit_invalid_filters_fail_with_fields(admin_case,params):
    response=admin_case.owner.client.get('/api/v1/admin/audit',params=params)
    assert response.status_code==422 and response.json()['error']['fields'],response.text


def test_private_learning_records_are_inaccessible_to_admin_and_absent_from_every_admin_response(admin_case):
    from test_courses_w06 import assert_private_course_routes_protected
    rt=admin_case
    course=rt.services.courses.create_course(rt.learner.actor,doc_id='w17-private-'+uuid4().hex,
        title='Private course',graph_version=1,module_count=1)
    markers=['W17_PRIVATE_CHAT_Q','W17_PRIVATE_CHAT_A','W17_PRIVATE_DOCUMENT','W17_PRIVATE_QUIZ_ANSWER']
    for kind,marker in zip(('session','turn','document','quiz_attempt'),markers):
        rt.services.phase_b_store.put_record(kind,uuid4().hex,{'owner':rt.learner.id,'doc_id':course.doc_id,'content':marker})
    assert len(sql(rt,'SELECT record_id FROM phase_b_record WHERE owner=:uid',uid=rt.learner.id))==4
    assert_private_course_routes_protected(rt.app,rt.owner.client,headers(rt.owner),course.id)
    for route,method in admin_routes(rt.app):
        response=rt.owner.client.request(method,route.path.replace('{uid}',rt.learner.id),headers=headers(rt.owner),
            json={'build_monthly_max':5} if method=='PATCH' else None)
        assert response.status_code==200,response.text
        assert not any(marker in response.text for marker in markers)
        assert not any(secret in response.text for secret in ('password_hash','token_hash','csrf_token',PASSWORD,'"meta"'))
    for view in (rt.services.admin.list_users(rt.owner.actor),rt.services.admin.list_audit(rt.owner.actor),
        rt.services.admin.update_user(rt.owner.actor,rt.learner.id,{'build_monthly_max':6})):
        assert not any(marker in json.dumps(view,default=str) for marker in markers)


def test_real_response_dtos_strip_repository_extras_at_every_level(admin_case,monkeypatch):
    rt=admin_case
    users=rt.services.admin.list_users(rt.owner.actor,email=rt.learner.email)
    users['private_extra']='W17_DTO_SECRET'
    users['items'][0]['password_hash']='W17_DTO_SECRET'
    users['items'][0]['builds_this_month']['extra']={'answer':'W17_DTO_SECRET'}
    monkeypatch.setattr(rt.services.admin,'list_users',lambda *a,**k:users)
    response=rt.owner.client.get('/api/v1/admin/users')
    assert response.status_code==200 and 'W17_DTO_SECRET' not in response.text
    audit={'items':[{'id':1,'at':rt.clock.now(),'actor_id':rt.owner.id,'action':'login_ok',
        'target_kind':'account','target_id':rt.owner.id,'ip':None,'meta':{'token':'W17_DTO_SECRET'}}],
        'total':1,'limit':50,'offset':0,'extra':'W17_DTO_SECRET'}
    monkeypatch.setattr(rt.services.admin,'list_audit',lambda *a,**k:audit)
    response=rt.owner.client.get('/api/v1/admin/audit')
    assert response.status_code==200 and 'W17_DTO_SECRET' not in response.text


@pytest.mark.parametrize('instant', ['2026-01-31T16:59:00+00:00','2026-12-31T16:59:00+00:00','2028-02-29T16:59:00+00:00'])
def test_user_monthly_counts_match_existing_quota_at_vietnam_boundary(admin_case,instant):
    from test_builds_w14 import pdf
    rt=admin_case
    before=datetime.fromisoformat(instant)
    after=before+timedelta(minutes=1)
    rt.clock.instant=before
    assert rt.owner.client.post('/api/v1/auth/login',headers={'Origin':ORIGIN},
        json={'email':rt.owner.email,'password':PASSWORD}).status_code==200
    for stamp,counted,actor in ((before,True,rt.learner.actor),(before,False,rt.learner.actor),
        (after,True,rt.learner.actor),(before-timedelta(days=35),True,rt.learner.actor),(before,True,rt.owner.actor)):
        item=rt.services.builds.create_upload(actor,'fixture.pdf',pdf()+b'\n%'+uuid4().hex.encode(),rights_confirmed=True)
        with rt.engine.begin() as connection:
            connection.execute(text("UPDATE build SET status='failed',counts_quota=:counted,queued_at=:stamp WHERE id=:id"),
                {'counted':counted,'stamp':stamp,'id':item['build']['build_id']})
    for now in (before,after):
        rt.clock.instant=now
        response=rt.owner.client.get('/api/v1/admin/users',params={'email':rt.learner.email})
        assert response.status_code==200,response.text
        item=response.json()['items'][0]
        quota=rt.services.builds.store.quota(rt.learner.id,now,None)
        assert item['builds_this_month']['used']==quota['builds_used']==1
        assert item['owned_courses']==4
        assert datetime.fromisoformat(item['builds_this_month']['resets_at']).hour==0
    record('monthly-boundary-'+instant[:10],response.json())


def test_update_rolls_back_if_session_delete_fails(admin_case,monkeypatch):
    rt=admin_case
    def fail(*args,**kwargs):
        raise RuntimeError('synthetic session deletion failure')
    monkeypatch.setattr(rt.services.admin.store,'delete_account_sessions',fail)
    response=patch(rt,{'status':'disabled','build_monthly_max':9})
    assert response.status_code==500
    assert sql(rt,'SELECT status,build_monthly_max FROM account WHERE id=:uid',uid=rt.learner.id)==[
        {'status':'active','build_monthly_max':None}]
    assert not sql(rt,"SELECT id FROM audit_event WHERE actor_id=:uid AND action LIKE 'admin_user_%'",uid=rt.owner.id)
    assert rt.learner.client.get('/api/v1/me').status_code==200


def test_inflight_login_cannot_leave_a_session_after_disable(admin_case,monkeypatch):
    from threading import Event
    rt=admin_case
    entered,release=Event(),Event()
    original=rt.services.accounts.hasher.verify
    def pause_login(encoded,password):
        valid=original(encoded,password)
        entered.set()
        assert release.wait(5)
        return valid
    monkeypatch.setattr(rt.services.accounts.hasher,'verify',pause_login)
    admin_headers=headers(rt.owner)
    with TestClient(rt.app,base_url=ORIGIN) as other:
        with ThreadPoolExecutor(max_workers=2) as pool:
            login=pool.submit(other.post,'/api/v1/auth/login',headers={'Origin':ORIGIN},
                json={'email':rt.learner.email,'password':PASSWORD})
            assert entered.wait(5)
            disable=pool.submit(rt.owner.client.patch,'/api/v1/admin/users/'+rt.learner.id,
                headers=admin_headers,json={'status':'disabled'})
            try:
                # Give the second transaction time to enter its account lock, while login is paused.
                sleep(.2)
            finally:
                release.set()
            assert login.result(10).status_code==200
            assert disable.result(10).status_code==200
        assert sql(rt,'SELECT id FROM auth_session WHERE account_id=:uid',uid=rt.learner.id)==[]
        assert other.get('/api/v1/me').status_code==rt.learner.client.get('/api/v1/me').status_code==401

