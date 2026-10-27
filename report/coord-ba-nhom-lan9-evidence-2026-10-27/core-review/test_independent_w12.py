"""Independent R9 probes of the actual W12 service; fake transaction port and SQLite SQL predicate only."""
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import replace
from datetime import datetime,timedelta,timezone
from types import SimpleNamespace
import hashlib,logging,re
from threading import RLock
import pytest
from sqlalchemy import create_engine,text
from wayfinder.application.sharing import SharingService
from wayfinder.domain.auth import Actor
from wayfinder.domain.courses import Membership
from wayfinder.api.errors import WebError
from wayfinder.infrastructure.sharing_store import PostgresSharingStore
from wayfinder.infrastructure.mail import ConsoleMailer
from wayfinder.application.email_templates import render_invitation_email

class Port:
    def __init__(self,now):
        self.lock=RLock();self.in_tx=False;self.rows={};self.audits=[];self.members={};self.calls=[];self.fail_audit=False
        self.accounts={'owner':dict(id='owner',email_normalized='owner@example.vn',email_verified_at=now,status='active'),
        'receiver':dict(id='receiver',email_normalized='receiver@example.vn',email_verified_at=now,status='active'),
        'outsider':dict(id='outsider',email_normalized='other@example.vn',email_verified_at=now,status='active')}
        self.courses={c:SimpleNamespace(id=c,owner_id='owner',title='Course <script>&',status='ready',is_sample=False) for c in ['c1','c2']}
        for c in self.courses:self.members[c,'owner']=Membership(c,'owner','owner','owner',now,now)
    @contextmanager
    def atomic(self):
        with self.lock:
            snapshot=deepcopy((self.rows,self.audits,self.members));self.in_tx=True
            try:yield
            except BaseException:
                self.rows,self.audits,self.members=snapshot;raise
            finally:self.in_tx=False
    def lock_invitation_sender(self,uid):assert self.in_tx;self.calls.append(('sender',uid))
    def get_course(self,cid,for_update=False):
        if for_update:assert self.in_tx
        return self.courses.get(cid)
    def get_membership(self,cid,uid):return self.members.get((cid,uid))
    def invitation_account(self,uid=None,email=None):
        return self.accounts.get(uid) if uid else next((a for a in self.accounts.values() if a['email_normalized']==email),None)
    def invitation_send_count(self,uid,start,end):return sum(e.actor_id==uid and e.action=='invitation_sent' and start<=e.at<end for e in self.audits)
    def pending_invitation(self,cid,email):return next((r for r in self.rows.values() if r.course_id==cid and r.email_normalized==email and r.status=='pending'),None)
    def save_invitation(self,r,existing=False):assert self.in_tx;self.rows[r.id]=r
    def append_audit(self,e):
        if self.fail_audit:raise RuntimeError('synthetic audit failure')
        self.audits.append(e)
    def get_invitation(self,iid,for_update=False):
        if for_update:assert self.in_tx
        return self.rows.get(iid)
    def member_count(self,cid):return sum(c==cid for c,u in self.members)
    def add_membership(self,m):
        assert self.in_tx
        if (m.course_id,m.account_id) in self.members:return False
        self.members[m.course_id,m.account_id]=m;return True

@pytest.fixture
def rt():
    now=datetime(2026,10,27,16,59,tzinfo=timezone.utc);clock=SimpleNamespace(instant=now)
    clock.now=lambda:clock.instant
    port=Port(now);deliveries=[]
    def send(*a,**k):assert not port.in_tx;deliveries.append((a,k))
    settings=SimpleNamespace(invite_batch_max=50,invite_emails_per_day=200,invite_ttl_days=7,course_max_members=200,public_base_url='https://example.invalid',email_logo_url=None)
    service=SharingService(port,settings,clock,mailer=SimpleNamespace(send=send))
    return SimpleNamespace(service=service,port=port,clock=clock,settings=settings,deliveries=deliveries,
        owner=Actor('owner','user',True,'active'),receiver=Actor('receiver','user',True,'active'),outsider=Actor('outsider','user',True,'active'))

def issue(rt,address='receiver@example.vn',cid='c1'):
    return rt.service.invite_by_email(rt.owner,cid,[address])['items'][0]['id']

def denied(fn,code):
    with pytest.raises(WebError) as e:fn()
    assert e.value.code==code

def test_dedup_hash_payload_escape_and_no_mail_inside_transaction(rt):
    result=rt.service.invite_by_email(rt.owner,'c1',['receiver@example.vn','  RECEIVER@example.vn  '])
    assert len(result['items'])==len(rt.port.rows)==len(rt.deliveries)==1
    raw=re.search(r'#invitation=([^\s]+)',rt.deliveries[0][0][2]).group(1)
    row=next(iter(rt.port.rows.values()))
    assert row.token_hash==hashlib.sha256(raw.encode()).digest() and len(row.token_hash)==32
    assert row.expires_at==rt.clock.now()+timedelta(days=7)
    assert raw not in str(result) and 'token' not in str(result) and rt.port.calls==[('sender','owner')]
    assert '&lt;script&gt;&amp;' in rt.deliveries[0][1]['html_body']

def test_invalid_batch_is_atomic_without_mail(rt):
    denied(lambda:rt.service.invite_by_email(rt.owner,'c1',['receiver@example.vn','invalid']),'validation')
    assert not rt.port.rows and not rt.deliveries and not rt.port.audits

def test_reinvite_retains_one_pending_and_renews_token(rt):
    identity=issue(rt);old=rt.port.rows[identity];rt.clock.instant+=timedelta(hours=1)
    assert issue(rt)==identity and len(rt.port.rows)==1
    assert rt.port.rows[identity].created_at==old.created_at and rt.port.rows[identity].expires_at>old.expires_at and rt.port.rows[identity].token_hash!=old.token_hash

def test_unverified_actor_and_db_account_cannot_accept(rt):
    identity=issue(rt)
    actor=replace(rt.receiver,email_verified=False)
    denied(lambda:rt.service.accept_invitation(actor,identity),'email_unverified')
    rt.port.accounts['receiver']['email_verified_at']=None
    denied(lambda:rt.service.accept_invitation(rt.receiver,identity),'email_unverified')
    assert rt.port.rows[identity].status=='pending' and len(rt.port.members)==2

def test_unknown_recipient_pending_cannot_be_taken_by_other_verified_email(rt):
    identity=issue(rt,'not-registered@example.vn')
    assert rt.port.rows[identity].invitee_account_id is None
    denied(lambda:rt.service.accept_invitation(rt.outsider,identity),'not_found')
    assert rt.port.rows[identity].status=='pending' and len(rt.port.members)==2

def test_expiry_exact_boundary_denies_without_membership(rt):
    identity=issue(rt);rt.clock.instant=rt.port.rows[identity].expires_at
    denied(lambda:rt.service.accept_invitation(rt.receiver,identity),'link_invalid')
    assert ('c1','receiver') not in rt.port.members and rt.port.rows[identity].status=='pending'

def test_owner_daily_limit_cross_course_and_hcm_midnight(rt):
    rt.settings.invite_emails_per_day=1;issue(rt)
    denied(lambda:issue(rt,cid='c2'),'rate_limited')
    assert len(rt.deliveries)==len(rt.port.audits)==1
    rt.clock.instant+=timedelta(minutes=1)
    assert issue(rt,cid='c2') and len(rt.deliveries)==2

def test_accepted_replay_does_not_duplicate_and_removed_member_not_restored(rt):
    identity=issue(rt);first=rt.service.accept_invitation(rt.receiver,identity);second=rt.service.accept_invitation(rt.receiver,identity)
    assert first['already_member'] is False and second['already_member'] is True
    assert sum(a.action=='invitation_accepted' for a in rt.port.audits)==1
    del rt.port.members['c1','receiver']
    denied(lambda:rt.service.accept_invitation(rt.receiver,identity),'link_invalid')
    assert ('c1','receiver') not in rt.port.members

def test_capacity_checked_without_consuming_pending(rt):
    identity=issue(rt);rt.settings.course_max_members=1
    denied(lambda:rt.service.accept_invitation(rt.receiver,identity),'course_full')
    assert rt.port.rows[identity].status=='pending' and ('c1','receiver') not in rt.port.members

def test_audit_error_rolls_back_member_status_and_no_new_mail(rt):
    identity=issue(rt);rt.port.fail_audit=True
    with pytest.raises(RuntimeError,match='synthetic audit'):
        rt.service.accept_invitation(rt.receiver,identity)
    assert rt.port.rows[identity].status=='pending' and ('c1','receiver') not in rt.port.members and len(rt.deliveries)==1
    with pytest.raises(RuntimeError):issue(rt,cid='c2')
    assert len(rt.port.rows)==len(rt.deliveries)==1

def test_console_token_redacted_and_template_origin_checked(caplog):
    token='SYNTHETIC_SECRET_FRAGMENT'
    content=render_invitation_email(course_title='<script>',action_url='https://example.invalid/dang-ky#invitation='+token,base_url='https://example.invalid')
    caplog.set_level(logging.INFO,logger='wayfinder.infrastructure.mail')
    ConsoleMailer().send('fixture@example.invalid',content.subject,content.text,html_body=content.html)
    assert token not in caplog.text and '[redacted]' in caplog.text
    with pytest.raises(ValueError):
        render_invitation_email(course_title='x',action_url='https://evil.invalid/dang-ky#invitation=x',base_url='https://example.invalid')

def test_actual_repository_binding_sql_requires_active_verified_matching_pending_unexpired():
    engine=create_engine('sqlite://')
    now=datetime(2026,10,27)
    with engine.begin() as c:
        c.execute(text('CREATE TABLE account(id TEXT,email_normalized TEXT,email_verified_at TEXT,status TEXT)'))
        c.execute(text('CREATE TABLE invitation(id TEXT,email_normalized TEXT,invitee_account_id TEXT,status TEXT,expires_at TIMESTAMP)'))
        c.execute(text('INSERT INTO account VALUES(:id,:email,:verified,:status)'),[
            {'id':'verified','email':'match@example.vn','verified':'yes','status':'active'},
            {'id':'unverified','email':'match@example.vn','verified':None,'status':'active'},
            {'id':'disabled','email':'match@example.vn','verified':'yes','status':'disabled'},
            {'id':'wrong','email':'other@example.vn','verified':'yes','status':'active'}])
        c.execute(text('INSERT INTO invitation VALUES(:id,:email,NULL,:status,:expires)'),[
            {'id':'valid','email':'match@example.vn','status':'pending','expires':now+timedelta(seconds=1)},
            {'id':'expired','email':'match@example.vn','status':'pending','expires':now},
            {'id':'cancelled','email':'match@example.vn','status':'cancelled','expires':now+timedelta(days=1)}])
    store=PostgresSharingStore(engine)
    for account in ['unverified','disabled','wrong']:
        store.bind_verified_invitations(SimpleNamespace(id=account),now)
    with engine.connect() as c:assert c.scalar(text('SELECT count(*) FROM invitation WHERE invitee_account_id IS NOT NULL'))==0
    store.bind_verified_invitations(SimpleNamespace(id='verified'),now)
    with engine.connect() as c:
        assert list(c.execute(text('SELECT id,invitee_account_id FROM invitation ORDER BY id')))==[('cancelled',None),('expired',None),('valid','verified')]
    engine.dispose()


@pytest.mark.parametrize('operation', ['invite','owner-list','cancel','mine','accept','decline'])
def test_disabled_actor_cannot_read_or_mutate_any_invitation_operation(rt,operation):
    identity=issue(rt)
    disabled_owner=replace(rt.owner,status='disabled')
    disabled_receiver=replace(rt.receiver,status='disabled')
    calls={
        'invite':lambda:rt.service.invite_by_email(disabled_owner,'c1',['receiver@example.vn']),
        'owner-list':lambda:rt.service.list_course_invitations(disabled_owner,'c1'),
        'cancel':lambda:rt.service.cancel_invitation(disabled_owner,'c1',identity),
        'mine':lambda:rt.service.list_my_invitations(disabled_receiver),
        'accept':lambda:rt.service.accept_invitation(disabled_receiver,identity),
        'decline':lambda:rt.service.decline_invitation(disabled_receiver,identity),
    }
    denied(calls[operation],'account_disabled')
    assert rt.port.rows[identity].status=='pending' and len(rt.port.audits)==len(rt.deliveries)==1
    assert ('c1','receiver') not in rt.port.members


@pytest.mark.parametrize('operation',['invite','accept','decline'])
def test_database_disabled_account_cannot_send_or_respond_even_with_stale_active_actor(rt,operation):
    identity=issue(rt)
    rt.port.accounts['owner' if operation=='invite' else 'receiver']['status']='disabled'
    calls={
        'invite':lambda:rt.service.invite_by_email(rt.owner,'c1',['receiver@example.vn']),
        'accept':lambda:rt.service.accept_invitation(rt.receiver,identity),
        'decline':lambda:rt.service.decline_invitation(rt.receiver,identity),
    }
    denied(calls[operation],'not_found')
    assert rt.port.rows[identity].status=='pending' and len(rt.port.audits)==len(rt.deliveries)==1
    assert ('c1','receiver') not in rt.port.members
