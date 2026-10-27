"""W17.1: real cookies/PostgreSQL, fake external dependencies, synthetic data only."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
from threading import Barrier
from types import SimpleNamespace
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

ORIGIN = 'https://testserver'
PASSWORD = 'W17 synthetic local passphrase!'


@pytest.fixture
def admin_case(postgres_database_url, monkeypatch):
    bundle = build_test_application()
    clock = bundle.phase_b.clock
    settings = WebSettings(
        _env_file=None, database_url=postgres_database_url.render_as_string(hide_password=False),
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
        path = Path('report/w17-evidence') / run / (name + '.json')
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
    assert response.status_code == 409 and response.json()['error']['code'] == 'conflict'
    assert sql(rt, 'SELECT role FROM account WHERE id=:uid', uid=rt.owner.id) == [{'role':'admin'}]


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

