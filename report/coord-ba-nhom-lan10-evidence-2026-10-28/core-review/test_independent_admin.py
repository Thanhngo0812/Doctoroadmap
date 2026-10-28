"""Independent R10 probes of the delivered service, SQL queries and HTTP DTOs.

SQLite substitutes only dialect-specific DDL/advisory locking. It does not prove
PostgreSQL serialization; the coordinator owns that gate. All records are synthetic.
"""
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.pool import StaticPool

from wayfinder.api.app import create_app
from wayfinder.api.auth import get_actor
from wayfinder.application.accounts import AuthError
from wayfinder.application.admin import AdminService
from wayfinder.application.auth_ports import AuditEvent
from wayfinder.composition import WebServices
from wayfinder.domain.auth import Actor
from wayfinder.infrastructure.admin_store import PostgresAdminStore
from wayfinder.settings import WebSettings

NOW = datetime(2026, 10, 28, 6, tzinfo=timezone.utc)
MARKER = 'R10_SYNTHETIC_PRIVATE_CONTENT'


class OfflineSQLStore(PostgresAdminStore):
    """Use delivered SQL methods unchanged, with SQLite transactions instead of PG locks."""
    @contextmanager
    def atomic(self, keys):
        self.lock_requests.append(tuple(keys))
        with self.engine.begin() as connection:
            token = self._connection.set(connection)
            try:
                if self.after_lock:
                    callback, self.after_lock = self.after_lock, None
                    callback(connection)
                yield
            finally:
                self._connection.reset(token)


@pytest.fixture
def case():
    engine = create_engine('sqlite+pysqlite:///:memory:',
        connect_args={'check_same_thread': False}, poolclass=StaticPool)
    @event.listens_for(engine, 'connect')
    def sqlite_strpos(connection, _):
        connection.create_function('strpos', 2, lambda value, needle: value.find(needle) + 1)
    with engine.begin() as conn:
        conn.execute(text('''CREATE TABLE account (id TEXT PRIMARY KEY,email TEXT,email_normalized TEXT,
          password_hash TEXT,display_name TEXT,role TEXT,status TEXT,email_verified_at DATETIME,
          created_at DATETIME,updated_at DATETIME,last_login_at DATETIME,build_monthly_max INTEGER)'''))
        conn.execute(text('CREATE TABLE auth_session (id TEXT PRIMARY KEY,account_id TEXT)'))
        conn.execute(text('''CREATE TABLE audit_event (id INTEGER PRIMARY KEY AUTOINCREMENT,at DATETIME,
          actor_id TEXT,action TEXT,target_kind TEXT,target_id TEXT,ip TEXT,meta TEXT)'''))
        conn.execute(text('CREATE TABLE course (id TEXT PRIMARY KEY,owner_id TEXT,private_content TEXT)'))
        conn.execute(text('CREATE TABLE build (id TEXT PRIMARY KEY,requested_by TEXT,counts_quota BOOLEAN,queued_at DATETIME)'))
    store = OfflineSQLStore(engine)
    store.lock_requests, store.after_lock = [], None
    settings = WebSettings(_env_file=None, frontend_dist=Path('absent'),
        public_base_url='https://testserver', allowed_origins=['https://testserver'])
    service = AdminService(store, settings=settings, clock=SimpleNamespace(now=lambda: NOW))
    def seed(role='user', status='active', email=None):
        # SQLAlchemy's UUID type uses compact hex with SQLite's non-native UUID dialect.
        uid = uuid4().hex
        email = email or uid + '@example.vn'
        with engine.begin() as conn:
            conn.execute(text('''INSERT INTO account VALUES (:id,:email,:email,:secret,'Synthetic',:role,
              :status,:at,:at,:at,:at,NULL)'''),
              dict(id=uid,email=email,secret=MARKER,role=role,status=status,at=NOW))
        return Actor(uid, role, True, status)
    admin, learner = seed('admin'), seed(email='literal_%@example.vn')
    rt = SimpleNamespace(engine=engine, store=store, service=service, settings=settings,
        admin=admin, learner=learner, seed=seed)
    yield rt
    engine.dispose()


def rows(rt, sql, **params):
    with rt.engine.connect() as conn:
        return [dict(row) for row in conn.execute(text(sql), params).mappings()]


def snapshot(rt):
    return {table: rows(rt, 'SELECT * FROM ' + table + ' ORDER BY id')
        for table in ('account', 'auth_session', 'audit_event')}


def test_sql_user_filters_are_literal_and_public(case):
    rt = case
    with rt.engine.begin() as conn:
        conn.execute(text('INSERT INTO course VALUES (:id,:uid,:private)'),
            dict(id=str(uuid4()),uid=rt.learner.user_id,private=MARKER))
        for at, counts in [('2026-10-01 00:00:00+07:00', True),
                           ('2026-10-20 00:00:00+07:00', True),
                           ('2026-11-01 00:00:00+07:00', True),
                           ('2026-10-15 00:00:00+07:00', False)]:
            conn.execute(text('INSERT INTO build VALUES (:id,:uid,:counts,:at)'),
                dict(id=str(uuid4()),uid=rt.learner.user_id,counts=counts,at=at))
    result = rt.service.list_users(rt.admin, email=' LITERAL_% ')
    assert result['total'] == 1
    item = result['items'][0]
    assert item['owned_courses'] == 1
    assert item['builds_this_month']['used'] == 2
    assert item['builds_this_month']['max'] is None
    assert item['builds_this_month']['resets_at'].isoformat() == '2026-11-01T00:00:00+07:00'
    assert MARKER not in json.dumps(result, default=str)
    assert rt.service.list_users(rt.admin, email="%' OR 1=1 --")['total'] == 0
    assert rt.service.list_users(rt.admin, email='literal_%',role='admin')['total'] == 0


@pytest.mark.parametrize('actor_kind,code', [('guest','unauthenticated'),('user','forbidden'),
    ('disabled','account_disabled'),('stale_role','forbidden'),('stale_status','forbidden')])
def test_service_denies_every_operation_before_mutation(case, actor_kind, code):
    rt = case
    actor = {'guest': None, 'user': rt.learner,
        'disabled': Actor(rt.admin.user_id,'admin',True,'disabled')}.get(actor_kind, rt.admin)
    if actor_kind.startswith('stale_'):
        assignment = "role='user'" if actor_kind=='stale_role' else "status='disabled'"
        with rt.engine.begin() as conn:
            conn.execute(text('UPDATE account SET ' + assignment + ' WHERE id=:id'),{'id':rt.admin.user_id})
    before = snapshot(rt)
    for operation in (lambda: rt.service.list_users(actor), lambda: rt.service.list_audit(actor),
                      lambda: rt.service.update_user(actor,rt.learner.user_id,{'status':'disabled'})):
        with pytest.raises(AuthError) as caught:
            operation()
        assert caught.value.code == code
    assert snapshot(rt) == before


def test_after_lock_recheck_prevents_stale_actor_write(case):
    rt = case
    rt.store.after_lock = lambda conn: conn.execute(text("UPDATE account SET role='user' WHERE id=:id"),
        {'id':rt.admin.user_id})
    before = snapshot(rt)
    with pytest.raises(AuthError) as caught:
        rt.service.update_user(rt.admin,rt.learner.user_id,{'status':'disabled'})
    assert caught.value.code == 'forbidden'
    assert snapshot(rt) == before  # The synthetic concurrent change is in this transaction too.


def test_disable_then_enable_never_recreates_sessions_and_is_idempotent(case):
    rt = case
    with rt.engine.begin() as conn:
        conn.execute(text('INSERT INTO auth_session VALUES (:id,:uid)'),
            [dict(id=str(uuid4()),uid=rt.learner.user_id) for _ in range(2)])
    result = rt.service.update_user(rt.admin, rt.learner.user_id, {'status':'disabled','build_monthly_max':8})
    assert result['status'] == 'disabled' and result['builds_this_month']['max'] == 8
    assert rows(rt,'SELECT * FROM auth_session') == []
    rt.service.update_user(rt.admin,rt.learner.user_id,{'status':'disabled','build_monthly_max':8})
    assert len(rows(rt,'SELECT id FROM audit_event')) == 2
    rt.settings.build_monthly_max = 3
    result = rt.service.update_user(rt.admin,rt.learner.user_id,{'status':'active','build_monthly_max':None})
    assert result['builds_this_month']['max'] == 3
    assert rows(rt,'SELECT * FROM auth_session') == []
    assert rows(rt,'SELECT action FROM audit_event ORDER BY id') == [
        {'action':'admin_user_disabled'},{'action':'admin_user_quota_changed'},
        {'action':'admin_user_enabled'},{'action':'admin_user_quota_changed'}]
    email = rt.store.get_account(rt.learner.user_id).email_normalized
    assert set(rt.store.lock_requests[0]) == {'admin:users','account:'+rt.learner.user_id,'account:'+email}


@pytest.mark.parametrize('failure_point', ['audit','session_delete'])
def test_sql_transaction_rolls_back_role_status_quota_and_sessions(case, monkeypatch, failure_point):
    rt = case
    with rt.engine.begin() as conn:
        conn.execute(text('INSERT INTO auth_session VALUES (:id,:uid)'),dict(id=str(uuid4()),uid=rt.learner.user_id))
    before = snapshot(rt)
    def fail(*_):
        raise RuntimeError('R10 injected failure')
    monkeypatch.setattr(rt.store,'append_audit' if failure_point=='audit' else 'delete_account_sessions',fail)
    with pytest.raises(RuntimeError,match='R10 injected failure'):
        rt.service.update_user(rt.admin,rt.learner.user_id,
            {'role':'admin','status':'disabled','build_monthly_max':7})
    assert snapshot(rt) == before


def test_last_role_admin_demote_rejected_but_disable_is_explicit_gap(case):
    rt = case
    before = snapshot(rt)
    with pytest.raises(AuthError) as caught:
        rt.service.update_user(rt.admin,rt.admin.user_id,{'role':'user'})
    assert caught.value.code == 'conflict'
    assert snapshot(rt) == before
    rt.service.update_user(rt.admin,rt.admin.user_id,{'status':'disabled'})
    assert rows(rt,"SELECT id FROM account WHERE role='admin' AND status='active'") == []
    assert rows(rt,"SELECT id FROM account WHERE role='admin'") == [{'id':rt.admin.user_id}]


def test_sql_audit_boundary_and_projection(case):
    rt = case
    for seconds in (-1,0,59,60):
        rt.store.append_audit(AuditEvent(NOW+timedelta(seconds=seconds),rt.learner.user_id,
            'password_changed','account',rt.learner.user_id,'127.0.0.1',{'password_hash':MARKER,'token':MARKER}))
    result = rt.service.list_audit(rt.admin,actor_id=rt.learner.user_id,action='password_changed',
        since=NOW,until=NOW+timedelta(seconds=60),limit=1)
    assert result['total'] == 2 and len(result['items']) == 1
    assert set(result['items'][0]) == {'id','at','actor_id','action','target_kind','target_id','ip'}
    assert MARKER not in json.dumps(result,default=str)
    later = rt.service.list_audit(rt.admin,actor_id=rt.learner.user_id,action='password_changed',
        since=NOW,until=NOW+timedelta(seconds=60),limit=1,offset=1)
    assert result['items'][0]['id'] != later['items'][0]['id']


def test_actual_http_guards_dtos_and_filter_errors(case, monkeypatch):
    rt = case
    app = create_app(rt.settings,WebServices(health_check=lambda:'ok',admin=rt.service))
    actor = [rt.admin]
    app.dependency_overrides[get_actor] = lambda: actor[0]
    with TestClient(app,base_url='https://testserver') as client:
        for path in ('/api/v1/admin/users','/api/v1/admin/audit'):
            actor[0] = rt.learner
            assert client.get(path).status_code == 403
            actor[0] = rt.admin
            for parameters in ({'limit':101},{'offset':-1}):
                response = client.get(path,params=parameters)
                assert response.status_code == 422 and response.json()['error']['fields']
                assert response.headers['cache-control'] == 'no-store'
        for parameters in ({'actor_id':'invalid'}, {'action':'bad name'}, {'action':'x'*81},
                           {'since':'2026-10-01'}, {'since':NOW.isoformat(),'until':NOW.isoformat()}):
            response = client.get('/api/v1/admin/audit',params=parameters)
            assert response.status_code == 422 and response.json()['error']['fields']
        original = rt.store.list_users
        def extra(**kwargs):
            result = original(**kwargs)
            result['meta'] = MARKER
            for item in result['items']:
                item['password_hash'] = MARKER
                item['builds_this_month']['private'] = MARKER
            return result
        monkeypatch.setattr(rt.store,'list_users',extra)
        response = client.get('/api/v1/admin/users')
        assert response.status_code == 200
        assert MARKER not in response.text


@pytest.mark.parametrize('changes', [{}, {'role':None}, {'status':None},{'build_monthly_max':True},
    {'build_monthly_max':0},{'build_monthly_max':'3'},{'build_monthly_max':2147483648},{'email':'other@example.vn'}])
def test_bad_patch_leaves_all_sql_state_unchanged(case, changes):
    before = snapshot(case)
    with pytest.raises(AuthError) as caught:
        case.service.update_user(case.admin,case.learner.user_id,changes)
    assert caught.value.code == 'validation'
    assert snapshot(case) == before


def test_delivery_evidence_manifest_and_junit_are_consistent():
    import subprocess
    import xml.etree.ElementTree as ET
    delivery = Path(__file__).resolve().parents[1] / 'w17-admin-users-backend'
    manifest = json.loads((delivery/'report/w17-evidence/manifest.json').read_text(encoding='utf-8'))
    for row in manifest['files']:
        assert hashlib.sha256((delivery/row['path']).read_bytes()).hexdigest() == row['sha256'],row['path']
    mutations = json.loads((delivery/'report/w17-evidence/mutations.json').read_text(encoding='utf-8'))
    for row in mutations:
        xml = ET.parse(delivery/('report/w17-evidence/runs/mutation-'+row['name']+'.xml'))
        assert row['native_exit']==1 and row['caught'] and xml.findall('.//failure') and not xml.findall('.//error')
    xml = ET.parse(delivery/'report/w17-evidence/runs/full-01.xml')
    assert not xml.findall('.//failure') and not xml.findall('.//error')
    assert len(xml.findall('.//testcase')) == 3485
    paths = subprocess.check_output(['git','diff','--name-only','8a8a46cb1e7eef2c95daddbe6cc36192b5aeff20',
        '9cf405acbbf8838d05a17b4bb7936d171cb5afa5','--','src','scripts','tests','pyproject.toml'],
        cwd=delivery,text=True)
    assert paths == ''  # Delivery commit packages evidence only after the tested source commit.


def test_registration_login_and_cli_admin_last_login_semantics():
    from wayfinder.application.accounts import AccountService, AuthPolicy
    from wayfinder.fakes.auth import FakeAuthStore
    clock = SimpleNamespace(instant=NOW)
    clock.now = lambda: clock.instant
    hasher = SimpleNamespace(hash=lambda password:'synthetic:'+password,
        verify=lambda encoded,password:encoded=='synthetic:'+password,dummy_hash='synthetic:dummy')
    store = FakeAuthStore()
    accounts = AccountService(store,hasher,clock,AuthPolicy(),frozenset())
    password = 'R10 local synthetic passphrase!'
    result = accounts.register('r10-register@example.vn',password,'Synthetic',ip=None,user_agent=None)
    uid = result.session.account.id
    assert store.get_account(uid).last_login_at == NOW
    clock.instant += timedelta(minutes=2)
    accounts.login('r10-register@example.vn',password,ip=None,user_agent=None)
    assert store.get_account(uid).last_login_at == clock.instant
    admin = accounts.create_admin('r10-cli-admin@example.vn',password)
    assert admin.last_login_at is None
