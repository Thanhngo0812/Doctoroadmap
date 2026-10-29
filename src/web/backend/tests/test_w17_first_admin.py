"""POL-R10-01 uses actual bootstrap, PostgreSQL and independently read persisted effects."""
from test_w17_admin import admin_case, headers, patch, record, sql
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from time import sleep
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from wayfinder.application.accounts import AuthError
from wayfinder.domain.auth import Actor
from wayfinder.infrastructure.auth_store import PostgresAuthStore
from wayfinder.infrastructure.database import create_database_engine, upgrade_database


def snapshot(rt, uid):
    return {
        'account':sql(rt,'SELECT role,status,build_monthly_max,updated_at FROM account WHERE id=:uid',uid=uid),
        'sessions':sql(rt,'SELECT id FROM auth_session WHERE account_id=:uid ORDER BY id',uid=uid),
        'audit':sql(rt,'SELECT id FROM audit_event ORDER BY id'),
        'registry':sql(rt,'SELECT account_id,established_at FROM bootstrap_admin')}


def test_new_owner_policy_first_admin_cannot_be_disabled(admin_case):
    rt = admin_case
    before = sql(rt, 'SELECT role,status,build_monthly_max,updated_at FROM account WHERE id=:id', id=rt.owner.id)
    sessions = sql(rt, 'SELECT id FROM auth_session WHERE account_id=:id ORDER BY id', id=rt.owner.id)
    audit = sql(rt, 'SELECT id FROM audit_event WHERE actor_id=:id ORDER BY id', id=rt.owner.id)
    response = patch(rt, {'status':'disabled','build_monthly_max':7}, target=rt.owner)
    assert response.status_code == 409 and response.json()['error']['code'] == 'protected_admin', response.text
    assert sql(rt, 'SELECT role,status,build_monthly_max,updated_at FROM account WHERE id=:id', id=rt.owner.id) == before
    assert sql(rt, 'SELECT id FROM auth_session WHERE account_id=:id ORDER BY id', id=rt.owner.id) == sessions
    assert sql(rt, 'SELECT id FROM audit_event WHERE actor_id=:id ORDER BY id', id=rt.owner.id) == audit
    assert rt.owner.client.get('/api/v1/me').status_code == 200
    record('protected-first-admin', response.json())


@pytest.mark.parametrize('self_action',[True,False])
@pytest.mark.parametrize('changes',[{'status':'disabled'},{'role':'user'},
    {'status':'disabled','role':'user','build_monthly_max':11}])
def test_first_identity_protected_even_with_two_admins_and_atomic_patch(admin_case,self_action,changes):
    rt=admin_case
    other=rt.user(True)
    actor=rt.owner if self_action else other
    before=snapshot(rt,rt.owner.id)
    response=patch(rt,changes,target=rt.owner,actor=actor)
    assert response.status_code==409 and response.json()['error']['code']=='protected_admin',response.text
    assert {f['loc'] for f in response.json()['error']['fields']}==set(changes)&{'role','status'}
    assert snapshot(rt,rt.owner.id)==before
    with pytest.raises(AuthError) as error:
        rt.services.admin.update_user(actor.actor,rt.owner.id,changes)
    assert error.value.code=='protected_admin' and snapshot(rt,rt.owner.id)==before
    assert rt.owner.client.get('/api/v1/me').status_code==other.client.get('/api/v1/me').status_code==200


def test_registry_survives_restart_and_older_learner_promotion_and_filtered_lists(admin_case):
    from wayfinder.application.admin import AdminService
    from wayfinder.infrastructure.admin_store import PostgresAdminStore
    rt=admin_case
    with rt.engine.begin() as connection:
        connection.execute(text('UPDATE account SET created_at=:at WHERE id=:uid'),
            {'uid':rt.learner.id,'at':rt.clock.now()-timedelta(days=365)})
    assert patch(rt,{'role':'admin'}).status_code==200
    extra=rt.user(True)
    engine=create_database_engine(rt.engine.url)
    try:
        restarted=AdminService(PostgresAdminStore(engine),settings=rt.settings,clock=rt.clock)
        assert restarted.store.first_admin_id()==rt.owner.id
        first=restarted.list_users(rt.owner.actor,email=rt.owner.email)['items'][0]
        old=restarted.list_users(rt.owner.actor,email=rt.learner.email)['items'][0]
        assert first['is_first_admin'] is True and old['is_first_admin'] is False
        assert patch(rt,{'status':'disabled'},target=extra).status_code==200
        assert patch(rt,{'role':'user'},target=rt.learner).status_code==200
        assert restarted.store.first_admin_id()==rt.owner.id
        assert len(sql(rt,'SELECT account_id FROM bootstrap_admin'))==1
        record('first-admin-user',first); record('older-promoted-user',old)
    finally:
        engine.dispose()


@pytest.mark.parametrize('data',[{'is_first_admin':False},{'first_admin_id':'attacker'},
    {'status':'disabled','singleton':True}])
def test_client_cannot_write_bootstrap_identity(admin_case,data):
    rt=admin_case
    before=snapshot(rt,rt.owner.id)
    response=patch(rt,data,target=rt.owner)
    assert response.status_code==422 and response.json()['error']['fields']
    assert snapshot(rt,rt.owner.id)==before


def test_disabled_actor_and_disabled_admin_not_counted_as_active(admin_case):
    rt=admin_case
    second=rt.user(True)
    assert rt.services.admin.store.admin_count()==2
    assert patch(rt,{'status':'disabled'},target=second).status_code==200
    assert rt.services.admin.store.admin_count()==1
    for method,args in ((rt.services.admin.list_users,()),(rt.services.admin.list_audit,()),
        (rt.services.admin.update_user,(rt.learner.id,{'status':'disabled'}))):
        with pytest.raises(AuthError) as error: method(second.actor,*args)
        assert error.value.code=='forbidden'
        with pytest.raises(AuthError) as error: method(Actor(second.id,'admin',True,'disabled'),*args)
        assert error.value.code=='account_disabled'
    assert second.client.get('/api/v1/admin/users').status_code==401
    assert rt.learner.client.get('/api/v1/me').status_code==200


@pytest.mark.parametrize('statement',[
    'DELETE FROM account WHERE id=:uid',
    "UPDATE account SET role='user',build_monthly_max=9 WHERE id=:uid",
    "UPDATE account SET status='disabled',build_monthly_max=9 WHERE id=:uid",
    'DELETE FROM bootstrap_admin WHERE account_id=:uid',
    'UPDATE bootstrap_admin SET account_id=:other WHERE account_id=:uid'])
def test_database_rejects_delete_and_bypass_of_protected_identity(admin_case,statement):
    rt=admin_case
    other=rt.user(True)
    before=snapshot(rt,rt.owner.id)
    with pytest.raises(IntegrityError) as error:
        with rt.engine.begin() as connection:
            connection.execute(text(statement),{'uid':rt.owner.id,'other':other.id})
    assert 'protected_admin' in str(error.value.orig)
    assert snapshot(rt,rt.owner.id)==before
    assert rt.owner.client.get('/api/v1/me').status_code==200


def test_no_delete_api_bypass_and_normal_accounts_still_deletable_by_repository_sql(admin_case):
    rt=admin_case
    before=snapshot(rt,rt.owner.id)
    for path in ('/api/v1/me','/api/v1/admin/users/'+rt.owner.id):
        response=rt.owner.client.delete(path,headers=headers(rt.owner))
        assert response.status_code==405
    assert snapshot(rt,rt.owner.id)==before
    # W20 self-delete is not implemented; enforce the invariant below all current/future repository callers.
    with rt.engine.begin() as connection:
        connection.execute(text('DELETE FROM account WHERE id=:uid'),{'uid':rt.learner.id})
    assert sql(rt,'SELECT id FROM account WHERE id=:uid',uid=rt.learner.id)==[]
    assert rt.learner.client.get('/api/v1/me').status_code==401


def test_profile_password_and_security_guards_remain_available_for_first_admin(admin_case):
    rt=admin_case
    response=rt.owner.client.patch('/api/v1/me',headers=headers(rt.owner),json={'display_name':'  Chủ dự án  '})
    assert response.status_code==200 and response.json()['account']['display_name']=='Chủ dự án'
    from test_w17_admin import PASSWORD, ORIGIN
    response=rt.owner.client.post('/api/v1/me/password',headers=headers(rt.owner),
        json={'current_password':PASSWORD,'new_password':'W17 protected synthetic new passphrase!'})
    assert response.status_code==200
    assert rt.owner.client.get('/api/v1/me').status_code==200
    response=rt.owner.client.patch('/api/v1/admin/users/'+rt.owner.id,headers={'Origin':ORIGIN},json={'role':'user'})
    assert response.status_code==403 and response.json()['error']['code']=='csrf_failed'
    assert rt.services.accounts.store.first_admin_id()==rt.owner.id


def test_bootstrap_creation_race_persists_exactly_one_identity_and_audit(admin_case,monkeypatch):
    from wayfinder.composition import compose_account_service
    rt=admin_case
    # Use another fresh database for concurrent initial bootstrap, not the already protected fixture database.
    name='w17_bootstrap_'+uuid4().hex
    control=create_database_engine(rt.engine.url).execution_options(isolation_level='AUTOCOMMIT')
    with control.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{name}"'))
    url=rt.engine.url.set(database=name)
    upgrade_database(url)
    engines=[create_database_engine(url),create_database_engine(url)]
    barrier=Barrier(2)
    def create(index):
        service=compose_account_service(rt.settings,engines[index],mailer=rt.services.accounts.mailer)
        original=service.store.first_admin_id
        def slow_first_read():
            result=original()
            sleep(.4)  # Widen the independent transactions' read/claim window if the shared lock is removed.
            return result
        monkeypatch.setattr(service.store,'first_admin_id',slow_first_read)
        barrier.wait(5)
        return service.create_admin(uuid4().hex+'@example.vn','W17 bootstrap synthetic password!').id
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            ids=list(pool.map(create,range(2)))
        with engines[0].connect() as connection:
            registry=connection.execute(text('SELECT account_id FROM bootstrap_admin')).scalars().all()
            assert len(registry)==1 and str(registry[0]) in ids
            assert connection.scalar(text("SELECT count(*) FROM account WHERE role='admin'"))==2
        record('bootstrap-race',{'created_ids':ids,'protected_id':str(registry[0])})
    finally:
        for engine in engines: engine.dispose()
        with control.connect() as connection:
            connection.execute(text(f'DROP DATABASE "{name}" WITH (FORCE)'))
        control.dispose()


def test_bootstrap_insert_and_audit_failure_roll_back_together(empty_postgres_database_url,monkeypatch):
    from wayfinder.composition import compose_account_service
    from wayfinder.settings import WebSettings
    upgrade_database(empty_postgres_database_url)
    engine=create_database_engine(empty_postgres_database_url)
    service=compose_account_service(WebSettings(_env_file=None),engine,mailer=SimpleNamespace(send=lambda **k:None))
    def fail(event): raise RuntimeError('synthetic bootstrap audit failure')
    monkeypatch.setattr(service.store,'append_audit',fail)
    try:
        with pytest.raises(RuntimeError,match='synthetic bootstrap'):
            service.create_admin('bootstrap-fail@example.vn','W17 bootstrap synthetic password!')
        with engine.connect() as connection:
            assert connection.scalar(text('SELECT count(*) FROM bootstrap_admin'))==0
            assert connection.scalar(text('SELECT count(*) FROM account'))==0
            assert connection.scalar(text('SELECT count(*) FROM audit_event'))==0
    finally:
        engine.dispose()


def test_legacy_upgrade_requires_explicit_uuid_without_guessing_and_atomic_assignment(empty_postgres_database_url,monkeypatch):
    from wayfinder.composition import compose_account_service
    from wayfinder.settings import WebSettings
    upgrade_database(empty_postgres_database_url,'w12_0008')
    engine=create_database_engine(empty_postgres_database_url)
    first,older,later=[str(uuid4()) for _ in range(3)]
    try:
        with engine.begin() as connection:
            for uid,role,age in ((older,'user',100),(first,'admin',50),(later,'admin',10)):
                connection.execute(text("""INSERT INTO account(id,email,email_normalized,password_hash,display_name,role,status,created_at,updated_at)
                    VALUES(:id,:email,:email,'synthetic-hash','Synthetic',:role,'active',now()-make_interval(days=>:age),now())"""),
                    {'id':uid,'email':uid+'@example.vn','role':role,'age':age})
        upgrade_database(empty_postgres_database_url)
        service=compose_account_service(WebSettings(_env_file=None),engine,mailer=SimpleNamespace(send=lambda **k:None))
        assert service.store.first_admin_id() is None
        from wayfinder.application.admin import AdminService
        from wayfinder.infrastructure.admin_store import PostgresAdminStore
        legacy_admin=AdminService(PostgresAdminStore(engine),settings=WebSettings(_env_file=None),clock=service.clock)
        actor=Actor(first,'admin',True,'active')
        assert legacy_admin.list_users(actor)['items'][0]['is_first_admin'] is None
        with pytest.raises(AuthError) as error:
            legacy_admin.update_user(actor,later,{'status':'disabled','build_monthly_max':4})
        assert error.value.code=='bootstrap_required'
        with pytest.raises(AuthError) as error:
            service.create_admin('must-not-guess@example.vn','W17 legacy synthetic passphrase!')
        assert error.value.code=='bootstrap_required'
        with engine.connect() as connection:
            assert connection.scalar(text('SELECT count(*) FROM bootstrap_admin'))==0
            assert connection.scalar(text('SELECT count(*) FROM account'))==3
        with pytest.raises(IntegrityError):
            with engine.begin() as connection:
                connection.execute(text('DELETE FROM account WHERE id=:id'),{'id':first})
        original=service.store.append_audit
        def fail(event): raise RuntimeError('synthetic legacy audit failure')
        monkeypatch.setattr(service.store,'append_audit',fail)
        with pytest.raises(RuntimeError): service.assign_first_admin(first)
        assert service.store.first_admin_id() is None
        monkeypatch.setattr(service.store,'append_audit',original)
        with pytest.raises(AuthError): service.assign_first_admin(older)
        service.assign_first_admin(first)  # Explicit operator reconciliation from external bootstrap evidence.
        service.assign_first_admin(first)  # Safe replay, no duplicate success event.
        with pytest.raises(AuthError) as error: service.assign_first_admin(later)
        assert error.value.code=='protected_admin'
        with engine.begin() as connection:
            connection.execute(text("UPDATE account SET role='admin' WHERE id=:id"),{'id':older})
        assert PostgresAuthStore(engine).first_admin_id()==first
        with engine.connect() as connection:
            events=connection.execute(text("SELECT actor_id,target_id,meta FROM audit_event WHERE action='bootstrap_admin_assigned'")).mappings().all()
            assert len(events)==1 and events[0]['target_id']==first and events[0]['meta']=={}
        record('legacy-assignment',{'protected_id':first,'older_user_promoted':older,'later_admin':later,'events':[dict(row) for row in events]})
    finally:
        engine.dispose()


def test_local_cli_assigns_only_explicit_server_uuid(admin_case,monkeypatch):
    from wayfinder import cli
    rt=admin_case
    calls=[]
    monkeypatch.setattr(cli,'WebSettings',lambda **k:rt.settings)
    monkeypatch.setattr(cli,'DatabaseHealth',lambda _:SimpleNamespace(engine=rt.engine,close=lambda:None))
    monkeypatch.setattr('wayfinder.composition.compose_account_service',lambda *a,**k:
        SimpleNamespace(assign_first_admin=lambda uid:calls.append(uid)))
    assert cli.main(['protect-first-admin','--account-id',rt.owner.id])==0
    assert calls==[rt.owner.id]
    with pytest.raises(SystemExit) as error:
        cli.main(['protect-first-admin','--account-id','invalid'])
    assert error.value.code==2 and calls==[rt.owner.id]
