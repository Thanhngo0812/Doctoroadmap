"""W12 uses actual cookie auth, separate PG connections and fake external dependencies."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import hashlib
import json
import os
from pathlib import Path
import re
from threading import Barrier
from time import sleep
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from doc2roadmap.config import Settings
from wayfinder.api.app import create_app
from wayfinder.api.errors import WebError
from wayfinder.composition import compose_services
from wayfinder.domain.auth import Actor
from wayfinder.infrastructure.database import create_database_engine
from wayfinder.infrastructure.sharing_store import PostgresSharingStore
from wayfinder.application.sharing import SharingService
from wayfinder.settings import WebSettings
from wayfinder.testing import build_test_application

ORIGIN = 'https://testserver'
PASSWORD = 'W12 synthetic local test passphrase!'


@pytest.fixture
def invited(postgres_database_url, monkeypatch, request):
    bundle = build_test_application()
    clock = bundle.phase_b.clock
    settings = WebSettings(_env_file=None, database_url=postgres_database_url.render_as_string(hide_password=False), frontend_dist=Path('missing'),
        public_base_url=ORIGIN, allowed_origins=[ORIGIN], artifact_root=Path('tmp/w12-artifacts'))
    forbidden_calls = []
    def forbidden(*args, **kwargs):
        forbidden_calls.append(True)
        raise AssertionError('W12 forbids real provider/ADC/SMTP/Cloudinary')
    for target in ('doc2roadmap.infrastructure.llm.gemini.urlopen',
        'doc2roadmap.infrastructure.embedding.gemini.urlopen',
        'doc2roadmap.infrastructure.google_auth.VertexCredentials.headers', 'smtplib.SMTP',
        'cloudinary.uploader.upload'):
        monkeypatch.setattr(target, forbidden)
    monkeypatch.setattr('wayfinder.composition.compose_mailer', lambda _: bundle.mailer)
    services = compose_services(settings, core_settings=Settings(_env_file=None,
        llm_transport='vertex', vertex_project='w12-no-network', vertex_location='global'),
        auth_validator=lambda *_: None, model_factory=lambda *a, **k: bundle.phase_b.model,
        embedding_factory=lambda *a, **k: bundle.phase_b.embedding, clock=clock,
        graph_loader=lambda *_: bundle.phase_b.graph, build_media=bundle.media_store)
    services.accounts.clock = clock
    app = create_app(settings, services)
    clients = []
    def user(verified=True, email=None):
        email = email or uuid4().hex + '@example.vn'
        client = TestClient(app, base_url=ORIGIN)
        clients.append(client)
        response = client.post('/api/v1/auth/register', headers={'Origin': ORIGIN}, json={
            'email': email, 'password': PASSWORD, 'display_name': 'Người học'})
        assert response.status_code == 200
        if verified:
            verify(client, bundle.mailer.messages[-1])
        return client
    owner, receiver, outsider = user(), user(), user()
    def actor(client):
        account = client.get('/api/v1/me').json()['account']
        return Actor(account['id'], account['role'], account['email_verified'], 'active')
    course = services.courses.create_course(actor(owner), doc_id='w12-' + uuid4().hex,
        title='Khoá <An & Bình>', graph_version=1, module_count=2)
    rt = SimpleNamespace(services=services, service=services.sharing, engine=services.sharing.store.engine,
        clock=clock, settings=settings, mailer=bundle.mailer, owner=owner, receiver=receiver,
        outsider=outsider, course=course, user=user, actor=actor, app=app)
    try:
        yield rt
    finally:
        record_data('sql-proof/'+re.sub(r'[^A-Za-z0-9_.-]','_',request.node.name), {
            'source':'Independent SQL connection, synthetic accounts, zero external mail/provider calls',
            'course_id':course.id,
            'invitations':sql(rt,'SELECT id,email_normalized,invitee_account_id,status,expires_at,responded_at FROM invitation WHERE course_id=:cid',cid=course.id),
            'membership':sql(rt,'SELECT account_id,role,via FROM membership WHERE course_id=:cid',cid=course.id),
            'audit':sql(rt,"SELECT action,actor_id,target_id,meta FROM audit_event WHERE target_id IN (SELECT id::text FROM invitation WHERE course_id=:cid)",cid=course.id)})
        for client in clients:
            client.close()
        services.close()
    assert forbidden_calls == []
    assert bundle.phase_b.model.json_calls == bundle.phase_b.embedding.requests == []


def verify(client, message):
    token = re.search(r'#token=([^\s]+)', message['body']).group(1)
    result = client.post('/api/v1/auth/verify-email', headers={'Origin': ORIGIN}, json={'token': token})
    assert result.status_code == 200


def headers(client):
    return {'Origin': ORIGIN, 'X-CSRF-Token': client.get('/api/v1/me').json()['csrf_token']}


def email(client):
    return client.get('/api/v1/me').json()['account']['email']


def send(rt, emails=None, client=None, course=None):
    client = client or rt.owner
    return client.post(f'/api/v1/courses/{(course or rt.course).id}/invitations', headers=headers(client),
                       json={'emails': emails or [email(rt.receiver)]})


def sql(rt, query, **params):
    # Deliberately bypass the repository connection/transaction when checking persisted effects.
    with rt.engine.connect() as connection:
        return [dict(row) for row in connection.execute(text(query), params).mappings()]


def iid(response):
    assert response.status_code == 200, response.text
    return response.json()['items'][0]['id']


def accept(client, identity):
    return client.post(f'/api/v1/invitations/{identity}/accept', headers=headers(client))


def test_pending_dedup_reinvite_token_hash_ttl_and_public_dto(invited):
    rt = invited
    recipient = email(rt.receiver)
    first = send(rt, [recipient, '  ' + recipient.upper() + '  '])
    identity = iid(first)
    rows = sql(rt, 'SELECT * FROM invitation WHERE course_id=:cid', cid=rt.course.id)
    assert len(rows) == 1 and rows[0]['status'] == 'pending'
    assert str(rows[0]['invitee_account_id']) == rt.actor(rt.receiver).user_id
    assert rows[0]['expires_at'] == rt.clock.now() + timedelta(days=7)
    token = re.search(r'#invitation=([^\s]+)', rt.mailer.messages[-1]['body']).group(1)
    assert len(__import__('base64').urlsafe_b64decode(token + '=')) == 32
    assert bytes(rows[0]['token_hash']) == hashlib.sha256(token.encode()).digest()
    assert token not in first.text and 'token_hash' not in first.text
    before = rows[0]
    rt.clock.advance(3600)
    second = send(rt)
    assert iid(second) == identity
    after = sql(rt, 'SELECT * FROM invitation WHERE id=:id', id=identity)[0]
    assert after['expires_at'] == rt.clock.now() + timedelta(days=7)
    assert bytes(after['token_hash']) != bytes(before['token_hash'])
    assert len(sql(rt, 'SELECT id FROM invitation WHERE course_id=:cid AND status=\'pending\'', cid=rt.course.id)) == 1
    listed = rt.owner.get(f'/api/v1/courses/{rt.course.id}/invitations')
    mine = rt.receiver.get('/api/v1/me/invitations')
    assert listed.status_code == mine.status_code == 200
    assert mine.json()['items'][0]['id'] == identity
    assert mine.json()['items'][0]['course_title'] == rt.course.title
    assert 'token' not in listed.text and 'token' not in mine.text
    assert first.headers['cache-control'] == mine.headers['cache-control'] == 'no-store'
    record('created', first); record('owner-list', listed); record('my-invitations', mine)
    audits = sql(rt, "SELECT action,actor_id,target_kind,target_id,meta FROM audit_event WHERE target_id=:id", id=identity)
    assert len(audits) == 2 and all(row['action']=='invitation_sent' and row['meta']=={} for row in audits)
    assert token not in str(audits)
    record_data('invitation-audit', audits)
    html = rt.mailer.messages[-1]['html_body']
    latest = re.search(r'#invitation=([^\s]+)', rt.mailer.messages[-1]['body']).group(1)
    assert '<An & Bình>' not in html and '&lt;An &amp; Bình&gt;' in html
    assert '7 ngày' in html and '/dang-ky#invitation=' in html
    record_html(html.replace(latest, 'INVITATION_TOKEN_OMITTED'))


def test_registration_not_bound_until_matching_email_verified(invited):
    rt = invited
    address = uuid4().hex + '@example.vn'
    identity = iid(send(rt, [address]))
    assert sql(rt, 'SELECT invitee_account_id FROM invitation WHERE id=:id', id=identity)[0]['invitee_account_id'] is None
    wrong = rt.user(False)
    verify(wrong, rt.mailer.messages[-1])
    assert wrong.get('/api/v1/me/invitations').json()=={'items':[]}
    assert accept(wrong,identity).status_code==404
    assert sql(rt, 'SELECT invitee_account_id FROM invitation WHERE id=:id', id=identity)[0]['invitee_account_id'] is None
    unverified = rt.user(False, address)
    message = rt.mailer.messages[-1]
    assert unverified.get('/api/v1/me/invitations').json() == {'items': []}
    assert sql(rt, 'SELECT invitee_account_id FROM invitation WHERE id=:id', id=identity)[0]['invitee_account_id'] is None
    denied = accept(rt.outsider, identity)
    assert denied.status_code == 404 and denied.json()['error']['code'] == 'not_found'
    assert accept(unverified, identity).status_code == 403
    verify(unverified, message)
    bound = sql(rt, 'SELECT invitee_account_id FROM invitation WHERE id=:id', id=identity)[0]['invitee_account_id']
    assert str(bound) == rt.actor(unverified).user_id
    assert unverified.get('/api/v1/me/invitations').json()['items'][0]['id'] == identity
    assert accept(unverified, identity).status_code == 200


def test_direct_binding_does_not_attach_unverified_or_mismatched_account(invited):
    rt=invited
    client=rt.user(False)
    address=email(client)
    identity=iid(send(rt,[address]))
    for actor in (rt.actor(client),rt.actor(rt.outsider)):
        rt.service.attach_verified_invitations(SimpleNamespace(id=actor.user_id))
    assert sql(rt,'SELECT invitee_account_id FROM invitation WHERE id=:id',id=identity)==[{'invitee_account_id':None}]
    assert rt.service.mailer is rt.services.accounts.mailer is rt.mailer


@pytest.mark.parametrize('action', ['accept', 'decline'])
def test_other_user_and_unverified_cannot_respond(invited, action):
    rt = invited
    unverified = rt.user(False)
    identity = iid(send(rt, [email(unverified)]))
    for client, code in ((rt.outsider, 'not_found'), (unverified, 'email_unverified')):
        response = client.post(f'/api/v1/invitations/{identity}/{action}', headers=headers(client))
        assert response.status_code == (404 if code=='not_found' else 403)
        assert response.json()['error']['code'] == code
    assert sql(rt, 'SELECT status FROM invitation WHERE id=:id', id=identity)[0]['status'] == 'pending'
    assert sql(rt, 'SELECT account_id FROM membership WHERE course_id=:cid', cid=rt.course.id) == [
        {'account_id': __import__('uuid').UUID(rt.actor(rt.owner).user_id)}]


def test_expiry_exact_boundary_and_expired_reinvite(invited):
    rt = invited
    identity = iid(send(rt))
    rt.clock.advance(7 * 86400 - 1)
    assert rt.receiver.get('/api/v1/me/invitations').json()['items'][0]['id']==identity
    rt.clock.advance(1)
    # Refresh login because the old session reaches the W02 idle boundary at the same instant.
    rt.receiver.post('/api/v1/auth/login', headers={'Origin': ORIGIN}, json={'email': email_from_store(rt, rt.receiver), 'password': PASSWORD})
    response = accept(rt.receiver, identity)
    assert response.status_code == 410 and response.json()['error']['code'] == 'link_invalid'
    assert not sql(rt, 'SELECT * FROM membership WHERE course_id=:cid AND via=\'email\'', cid=rt.course.id)
    assert rt.service.list_my_invitations(rt.actor(rt.receiver)) == {'items': []}
    rt.owner.post('/api/v1/auth/login', headers={'Origin': ORIGIN}, json={'email': email_from_store(rt, rt.owner), 'password': PASSWORD})
    assert iid(send(rt)) == identity
    assert accept(rt.receiver, identity).status_code == 200
    record('expired', response)


def email_from_store(rt, client):
    token = client.cookies.get('d2r_session')
    session = rt.services.accounts.store.get_session(hashlib.sha256(token.encode()).digest())
    return rt.services.accounts.store.get_account(session.account_id).email


def test_accept_replay_decline_cancel_and_course_scope(invited):
    rt = invited
    identity = iid(send(rt))
    first, again = accept(rt.receiver, identity), accept(rt.receiver, identity)
    assert first.status_code == again.status_code == 200
    assert first.json()['already_member'] is False and again.json()['already_member'] is True
    assert len(sql(rt, 'SELECT * FROM membership WHERE course_id=:cid AND via=\'email\'', cid=rt.course.id)) == 1
    assert len(sql(rt, 'SELECT * FROM audit_event WHERE target_id=:id AND action=\'invitation_accepted\'', id=identity)) == 1
    second = iid(send(rt))
    assert second != identity
    declined = rt.receiver.post(f'/api/v1/invitations/{second}/decline', headers=headers(rt.receiver))
    assert declined.status_code == 200
    assert accept(rt.receiver, second).status_code == 410
    third = iid(send(rt))
    wrong = rt.owner.delete(f'/api/v1/courses/{uuid4()}/invitations/{third}', headers=headers(rt.owner))
    assert wrong.status_code == 404
    cancelled = rt.owner.delete(f'/api/v1/courses/{rt.course.id}/invitations/{third}', headers=headers(rt.owner))
    assert cancelled.status_code == 200 and accept(rt.receiver, third).status_code == 410
    assert rt.service.list_my_invitations(rt.actor(rt.receiver)) == {'items': []}
    record('accepted', first); record('accepted-replay', again); record('declined', declined); record('cancelled', cancelled)


def test_owner_authorization_validation_and_csrf(invited):
    rt = invited
    raw = [email(rt.receiver)]
    for addresses in ([], ['invalid'], ['a@example.vn'] * 51):
        response = rt.owner.post(f'/api/v1/courses/{rt.course.id}/invitations', headers=headers(rt.owner), json={'emails': addresses})
        assert response.status_code == 422 and response.json()['error']['fields']
    assert send(rt, raw, rt.outsider).status_code == 404
    uid = rt.actor(rt.owner).user_id
    with rt.engine.begin() as c:
        c.execute(text('UPDATE account SET email_verified_at=NULL WHERE id=:id'), {'id': uid})
    assert send(rt).json()['error']['code'] == 'email_unverified'
    with rt.engine.begin() as c:
        c.execute(text('UPDATE account SET email_verified_at=:now WHERE id=:id'), {'id': uid, 'now': rt.clock.now()})
    for extra in ({'owner': uid}, {'session_id': 'forged'}, {'invitee_account_id': uid}):
        response = rt.owner.post(f'/api/v1/courses/{rt.course.id}/invitations', headers=headers(rt.owner), json={'emails': raw, **extra})
        assert response.status_code == 422
    identity = iid(send(rt))
    routes = [('POST', f'/courses/{rt.course.id}/invitations', {'emails': raw}),
        ('DELETE', f'/courses/{rt.course.id}/invitations/{identity}', None),
        ('POST', f'/invitations/{identity}/accept', None), ('POST', f'/invitations/{identity}/decline', None)]
    for method, route, body in routes:
        for bad in ({}, {'Origin': ORIGIN}, {**headers(rt.owner), 'Origin': 'https://evil.example'},
                    {**headers(rt.owner), 'X-CSRF-Token': headers(rt.receiver)['X-CSRF-Token']}):
            denied = rt.owner.request(method, '/api/v1'+route, headers=bad, json=body)
            assert denied.status_code == 403 and denied.json()['error']['code'] == 'csrf_failed'


def test_201st_daily_mail_and_vietnam_day_reset(invited):
    rt = invited
    rt.clock.instant = rt.clock.instant.replace(hour=16, minute=59)
    for _ in range(4):
        assert send(rt, [f'{uuid4().hex}@example.vn' for _ in range(50)]).status_code == 200
    blocked = send(rt)
    assert blocked.status_code == 429 and blocked.json()['error']['code'] == 'rate_limited'
    rt.clock.advance(60)
    assert send(rt).status_code == 200
    record('daily-limit', blocked)


@pytest.mark.parametrize('race', ['mail', 'capacity', 'link-email', 'same-accept', 'same-invite'])
def test_two_runtimes_race_on_last_mail_or_course_seat(invited, race):
    rt = invited
    actor = rt.actor(rt.owner)
    if race == 'mail':
        rt.settings.invite_emails_per_day = 1
    other_course = rt.services.courses.create_course(actor, doc_id='race-'+uuid4().hex,
        title='Khoá thứ hai cùng chủ', graph_version=1, module_count=1) if race=='mail' else rt.course
    if race in ('capacity','link-email'):
        rt.settings.course_max_members = 2
    identities = [iid(send(rt, [email(client)])) for client in (rt.receiver, rt.outsider)] if race in ('capacity','link-email', 'same-accept') else []
    link=rt.service.create_share_link(actor,rt.course.id)['link']['token'] if race=='link-email' else None
    barrier = Barrier(2)
    def work(index):
        engine = create_database_engine(rt.settings.database_url)
        try:
            service = SharingService(PostgresSharingStore(engine), rt.settings, rt.clock, mailer=rt.mailer)
            # Enlarge the real read→write race window; correct locks serialize these reads.
            original = service.store.invitation_send_count if race=='mail' else service.store.member_count
            def delayed_read(*args):
                result = original(*args)
                sleep(0.15)
                return result
            if race == 'mail':
                service.store.invitation_send_count = delayed_read
            elif race in ('capacity','link-email'):
                service.store.member_count = delayed_read
            barrier.wait(timeout=10)
            try:
                if race in ('mail', 'same-invite'):
                    course = rt.course if index==0 or race!='mail' else other_course
                    return service.invite_by_email(actor, course.id, [email(rt.receiver)])
                if race=='link-email' and index==1:
                    return service.join_by_link(rt.actor(rt.outsider),link)
                client = rt.receiver if race == 'same-accept' else (rt.receiver, rt.outsider)[index]
                return service.accept_invitation(rt.actor(client), identities[0 if race == 'same-accept' else index])
            except WebError as error:
                return error.code
        finally:
            engine.dispose()
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(work, range(2)))
    if race == 'mail':
        assert results.count('rate_limited') == 1 and sum(isinstance(r, dict) for r in results) == 1
        assert len(sql(rt, 'SELECT id FROM audit_event WHERE action=\'invitation_sent\' AND actor_id=:uid', uid=actor.user_id)) == 1
    elif race in ('capacity','link-email'):
        assert results.count('course_full') == 1 and sum(isinstance(r, dict) for r in results) == 1
    elif race == 'same-accept':
        assert sorted(r['already_member'] for r in results) == [False, True]
    else:
        assert all(isinstance(r, dict) for r in results)
        assert len(sql(rt, 'SELECT id FROM invitation WHERE course_id=:cid', cid=rt.course.id)) == 1
    if race in ('capacity','link-email', 'same-accept'):
        assert len(sql(rt, 'SELECT account_id FROM membership WHERE course_id=:cid', cid=rt.course.id)) == 2


@pytest.mark.parametrize('operation', ['invite', 'accept', 'decline', 'cancel'])
def test_pg_rollback_on_audit_failure(invited, monkeypatch, operation):
    rt = invited
    identity = iid(send(rt)) if operation != 'invite' else None
    before = sql(rt, 'SELECT * FROM invitation WHERE course_id=:cid', cid=rt.course.id) if identity else []
    mail_count = len(rt.mailer.messages)
    def fail(_):
        raise RuntimeError('synthetic audit write failure')
    monkeypatch.setattr(rt.service.store, 'append_audit', fail)
    with pytest.raises(RuntimeError, match='synthetic audit write failure'):
        if operation == 'invite':
            rt.service.invite_by_email(rt.actor(rt.owner), rt.course.id, [email(rt.receiver)])
        elif operation == 'accept':
            rt.service.accept_invitation(rt.actor(rt.receiver), identity)
        elif operation == 'decline':
            rt.service.decline_invitation(rt.actor(rt.receiver), identity)
        else:
            rt.service.cancel_invitation(rt.actor(rt.owner), rt.course.id, identity)
    assert sql(rt, 'SELECT * FROM invitation WHERE course_id=:cid', cid=rt.course.id) == before
    assert len(sql(rt, 'SELECT * FROM membership WHERE course_id=:cid', cid=rt.course.id)) == 1
    assert len(rt.mailer.messages) == mail_count


def test_schema_pending_unique_hash_and_head(invited):
    rt = invited
    assert sql(rt, 'SELECT version_num FROM alembic_version') == [{'version_num': 'w12_0008'}]
    assert set(c['name'] for c in inspect(rt.engine).get_columns('invitation')) == {
        'id','course_id','email_normalized','invitee_account_id','invited_by','token_hash','status','expires_at','created_at','responded_at'}
    identity = iid(send(rt))
    with pytest.raises(IntegrityError):
        with rt.engine.begin() as c:
            c.execute(text('UPDATE invitation SET token_hash=:hash WHERE id=:id'),{'hash':b'short','id':identity})
    with pytest.raises(IntegrityError):
        with rt.engine.begin() as c:
            c.execute(text('INSERT INTO invitation SELECT :newid,course_id,email_normalized,invitee_account_id,invited_by, '
                ':hash,status,expires_at,created_at,responded_at FROM invitation WHERE id=:id'),
                {'newid': str(uuid4()), 'hash': b'X'*32, 'id': identity})
    assert len(sql(rt, 'SELECT * FROM invitation WHERE course_id=:cid', cid=rt.course.id)) == 1


def test_partial_invalid_batch_writes_nothing_and_service_limits_are_enforced(invited):
    rt = invited
    before = len(rt.mailer.messages)
    actor = rt.actor(rt.owner)
    for addresses in (['valid@example.vn','invalid'], [], ['a@example.vn']*51):
        with pytest.raises(WebError) as failure:
            rt.service.invite_by_email(actor, rt.course.id, addresses)
        assert failure.value.code=='validation' and failure.value.fields
    assert not sql(rt, 'SELECT id FROM invitation WHERE course_id=:cid', cid=rt.course.id)
    assert len(rt.mailer.messages)==before


def test_verified_callback_covers_all_courses_and_list_recovers_after_hook_interruption(invited, monkeypatch):
    rt = invited
    other_course = rt.services.courses.create_course(rt.actor(rt.owner), doc_id='hook-'+uuid4().hex,
        title='Khóa khác', graph_version=1, module_count=1)
    address = uuid4().hex+'@example.vn'
    identities = [iid(send(rt,[address],course=course)) for course in (rt.course,other_course)]
    client = rt.user(False,address)
    token = re.search(r'#token=([^\s]+)',rt.mailer.messages[-1]['body']).group(1)
    def interrupted(_):
        raise RuntimeError('synthetic post-commit interruption')
    monkeypatch.setattr(rt.services.accounts,'on_email_verified',interrupted)
    with pytest.raises(RuntimeError,match='synthetic post-commit interruption'):
        rt.services.accounts.verify_email(token)
    assert client.get('/api/v1/me').json()['account']['email_verified']
    assert all(row['invitee_account_id'] is None for row in sql(rt,
        'SELECT invitee_account_id FROM invitation WHERE email_normalized=:email',email=address))
    listed = client.get('/api/v1/me/invitations')
    assert {item['id'] for item in listed.json()['items']}==set(identities)
    assert all(str(row['invitee_account_id'])==rt.actor(client).user_id for row in sql(rt,
        'SELECT invitee_account_id FROM invitation WHERE email_normalized=:email',email=address))


def test_already_member_accept_does_not_consume_capacity_or_restore_removed_access(invited):
    rt = invited
    actor = rt.actor(rt.receiver)
    link = rt.service.create_share_link(rt.actor(rt.owner),rt.course.id)['link']['token']
    rt.service.join_by_link(actor,link)
    rt.settings.course_max_members=2
    identity = iid(send(rt))
    assert accept(rt.receiver,identity).json()['already_member'] is True
    assert len(sql(rt, 'SELECT * FROM membership WHERE course_id=:cid',cid=rt.course.id))==2
    assert sql(rt, 'SELECT via FROM membership WHERE course_id=:cid AND account_id=:uid',
        cid=rt.course.id,uid=actor.user_id)==[{'via':'link'}]
    rt.service.remove_member(rt.actor(rt.owner),rt.course.id,actor.user_id)
    assert accept(rt.receiver,identity).status_code==410
    assert not sql(rt,'SELECT * FROM membership WHERE course_id=:cid AND account_id=:uid',cid=rt.course.id,uid=actor.user_id)


def test_mail_failure_is_after_commit_counted_without_retry_or_secret_log(invited, monkeypatch, caplog):
    rt = invited
    def failed(*args, **kwargs):
        raise RuntimeError('synthetic recipient/token/provider secret must not be logged')
    monkeypatch.setattr(rt.mailer,'send',failed)
    response=send(rt)
    identity=iid(response)
    assert sql(rt,'SELECT status FROM invitation WHERE id=:id',id=identity)==[{'status':'pending'}]
    assert len(sql(rt,"SELECT id FROM audit_event WHERE target_id=:id AND action='invitation_sent'",id=identity))==1
    assert 'Invitation email delivery unavailable' in caplog.text
    assert 'synthetic recipient/token/provider secret' not in caplog.text


def test_invitation_dto_filters_private_fields_and_body_cannot_select_recipient(invited, monkeypatch):
    rt=invited
    identity=iid(send(rt))
    original=rt.service.list_my_invitations
    def private(actor):
        response=original(actor)
        response['token_hash']='PRIVATE-HASH'
        for item in response['items']:
            item['token']='PRIVATE-TOKEN'
        return response
    monkeypatch.setattr(rt.service,'list_my_invitations',private)
    response=rt.receiver.get('/api/v1/me/invitations')
    assert response.status_code==200 and 'PRIVATE-' not in response.text
    for action in ('accept','decline'):
        result=rt.receiver.post(f'/api/v1/invitations/{identity}/{action}',headers=headers(rt.receiver),
            json={'owner':rt.actor(rt.outsider).user_id})
        assert result.status_code==422
    assert sql(rt,'SELECT status FROM invitation WHERE id=:id',id=identity)==[{'status':'pending'}]


def test_pg_rollback_on_membership_write_failure(invited,monkeypatch):
    rt=invited
    identity=iid(send(rt))
    def fail(_):
        raise RuntimeError('synthetic membership write failure')
    monkeypatch.setattr(rt.service.store,'add_membership',fail)
    with pytest.raises(RuntimeError,match='synthetic membership write failure'):
        rt.service.accept_invitation(rt.actor(rt.receiver),identity)
    assert sql(rt,'SELECT status FROM invitation WHERE id=:id',id=identity)==[{'status':'pending'}]
    assert len(sql(rt,'SELECT * FROM membership WHERE course_id=:cid',cid=rt.course.id))==1
    assert not sql(rt,"SELECT id FROM audit_event WHERE target_id=:id AND action='invitation_accepted'",id=identity)


def record(name, response):
    label = os.environ.get('W12_EVIDENCE_RUN')
    if label:
        out = Path('report/w12-evidence') / label
        out.mkdir(parents=True, exist_ok=True)
        (out/(name+'.json')).write_text(json.dumps({'status':response.status_code,'body':response.json()},
            ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def record_data(name, data):
    label = os.environ.get('W12_EVIDENCE_RUN')
    if label:
        path = Path('report/w12-evidence')/label
        path.mkdir(parents=True,exist_ok=True)
        target=path/(name+'.json')
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(data,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')


def record_html(html):
    label = os.environ.get('W12_EVIDENCE_RUN')
    if label:
        (Path('report/w12-evidence')/label/'invitation-email.html').write_text(html,encoding='utf-8')
