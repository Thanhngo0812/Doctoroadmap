"""W12: real HTTP/auth/PG and graph v8; fake clock/Mailer, no paid providers."""
import json, os, re, socket, subprocess, sys
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from threading import Thread
from time import monotonic, sleep
from uuid import uuid4
ROOT=Path('C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-r10-acceptance-20261028')
sys.path[:0]=[str(ROOT/'src/web/backend'),str(ROOT/'src'),str(ROOT/'scripts')]
from dotenv import dotenv_values
from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.engine import make_url
import uvicorn
from doc2roadmap.application.phase_b.retrieval import load_learning_graph
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore
from wayfinder.api.app import create_app
from wayfinder.api.auth import get_actor
from wayfinder.api.errors import WebError
from wayfinder.composition import WebServices,compose_account_service,compose_course_services,compose_sharing_service
from wayfinder.domain.auth import Actor
from wayfinder.domain.courses import Membership
from wayfinder.fakes.mail import FakeMailer
from wayfinder.infrastructure.database import create_database_engine,upgrade_database
from wayfinder.infrastructure.phase_b_store import PostgresPhaseBStore
from wayfinder.settings import WebSettings
from wayfinder.testing import FakeClock
from w14_web_runtime import _forbid_live_providers
BASE='http://127.0.0.1:8027'
RUN=os.environ.get('W12_REACT_RUN','browser-dev1');assert re.fullmatch('browser-[a-z0-9-]+',RUN)
OUT=ROOT/'report/w12-react-evidence'/RUN
PASSWORD='W12 synthetic browser passphrase!'
def save(name,value):(OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf8')
def main():
    assert not OUT.exists();OUT.mkdir(parents=True)
    url=make_url(dotenv_values(ROOT.parents[1]/'src/web/.env')['WAYFINDER_TEST_DATABASE_URL'])
    assert url.database=='wayfinder_test' and url.get_backend_name()=='postgresql'
    _forbid_live_providers();name='wayfinder_w12_react_'+uuid4().hex
    admin=create_database_engine(url).execution_options(isolation_level='AUTOCOMMIT')
    engine=audit=phase=server=thread=listener=None;created=False;mailer=FakeMailer()
    summary=dict(base=BASE,databaseName=name,temporaryDatabaseRemoved=False,externalCostUsd=0,
        sourceCommit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        dirtySourcePaths=subprocess.check_output(['git','diff','HEAD','--name-only','--','src','scripts'],cwd=ROOT,text=True).splitlines(),
        providers='FakeMailer/FakeClock; model/media/embedding unused; real auth/Argon2/PG/graph v8')
    try:
        with admin.connect() as c:c.execute(text(f'CREATE DATABASE "{name}"'))
        created=True;db=url.set(database=name);upgrade_database(db)
        engine,audit=create_database_engine(db),create_database_engine(db)
        settings=WebSettings(_env_file=None,database_url=db.render_as_string(hide_password=False),frontend_dist=ROOT/'src/web/frontend/dist',artifact_root=ROOT/'artifacts',allowed_origins=[BASE],public_base_url=BASE)
        clock=FakeClock(datetime(2026,10,27,8,tzinfo=timezone.utc))
        accounts=compose_account_service(settings,engine,mailer=mailer);accounts.clock=clock
        phase=PostgresPhaseBStore(engine)
        graph_loader=lambda doc,version:load_learning_graph(JsonArtifactStore(settings.artifact_root),doc,version)
        graph=graph_loader('doc-1',8)
        courses,gateway=compose_course_services(settings,engine,phase,clock=clock,graph_loader=graph_loader)
        sharing=compose_sharing_service(settings,engine,clock=clock,graph_loader=graph_loader,mailer=mailer)
        accounts.on_email_verified=sharing.attach_verified_invitations
        actors={}
        for label,display in [('owner','Cô Mai'),('receiver','Nguyễn An'),('other','Bình'),('unverified','Linh')]:
            grant=accounts.register(label+'-w12@example.invalid',PASSWORD,display,ip=None,user_agent=None).session
            if label!='unverified':
                raw=re.search(r'#token=([^\s]+)',mailer.messages[-1]['body']).group(1);accounts.verify_email(raw)
            account=accounts.store.get_account(grant.account.id)
            actors[label]=Actor(account.id,'user',account.email_verified_at is not None,'active')
            with accounts.store.atomic(['account:'+account.id]):accounts.store.delete_account_sessions(account.id)
        catalog={}
        for key,title in [('primary','Đại số tuyến tính'),('secondary','Ôn tập Đại số'),('full','Nhóm đã đủ 200 thành viên'),('cancel','Nhóm học cuối tuần'),('expired','Lời mời đã hết hạn')]:
            catalog[key]=courses.create_course(actors['owner'],doc_id='doc-1',title=title,graph_version=8,module_count=len(graph.modules))
        catalog['unverified']=courses.create_course(actors['unverified'],doc_id='doc-1',title='Khoá của Linh',graph_version=8,module_count=len(graph.modules))
        # Populate only this UUID database, retaining the actual 200-member production boundary.
        fixture_account=accounts.store.get_account(actors['owner'].user_id)
        encoded=accounts.store.get_credentials('owner-w12@example.invalid').password_hash
        members=[]
        with accounts.store.atomic(['fixture-full-course']):
            for index in range(199):
                uid=str(uuid4());email=f'member-{index}@w12-fixture.invalid'
                accounts.store.create_account(replace(fixture_account,id=uid,email=email,email_normalized=email,display_name=f'Thành viên tổng hợp {index+1}'),encoded);members.append(uid)
        with courses.store.atomic():
            for uid in members:courses.store.add_membership(Membership(catalog['full'].id,uid,'learner','email',clock.now(),None))
        invitation_ids={}
        for key in ['primary','secondary','full','cancel','expired']:
            invitation_ids[key]=sharing.invite_by_email(actors['owner'],catalog[key].id,['receiver-w12@example.invalid'])['items'][0]['id']
        with engine.begin() as c:c.execute(text('UPDATE invitation SET expires_at=:now WHERE id=:id'),{'now':clock.now(),'id':invitation_ids['expired']})
        app=create_app(settings,WebServices(health_check=lambda:'ok',accounts=accounts,phase_b_store=phase,courses=courses,learning=gateway,sharing=sharing))
        def observer(actor=Depends(get_actor)):
            if actor.user_id!=actors['other'].user_id:raise WebError('not_found','Không tìm thấy')
        def probe():
            with audit.connect() as c:
                rows=c.execute(text('SELECT id,course_id,email_normalized,invitee_account_id,status,created_at,expires_at,responded_at,octet_length(token_hash) AS hash_bytes FROM invitation ORDER BY created_at,id')).mappings().all()
                membership=c.execute(text('SELECT course_id,account_id,role,via FROM membership WHERE account_id NOT IN (SELECT id FROM account WHERE email_normalized LIKE :dummy)'),{'dummy':'%@w12-fixture.invalid'}).mappings().all()
                counts=c.execute(text('SELECT course_id,count(*) AS members FROM membership GROUP BY course_id')).mappings().all()
                events=c.execute(text("SELECT action,actor_id,target_id,meta FROM audit_event WHERE action LIKE 'invitation_%' ORDER BY id")).mappings().all()
            return dict(invitations=[dict(r) for r in rows],membership=[dict(r) for r in membership],courseCounts=[dict(r) for r in counts],audit=[dict(r) for r in events])
        @app.get('/api/v1/__test/w12/probe',dependencies=[Depends(observer)])
        def inspect():return probe()
        @app.get('/api/v1/__test/w12/mail',dependencies=[Depends(observer)])
        def mail(email:str):
            messages=[m for m in mailer.messages if m['to']==email]
            return {'body':messages[-1]['body'] if messages else ''}
        @app.post('/api/v1/__test/w12/fill-rate',dependencies=[Depends(observer)])
        def fill_rate():
            with audit.connect() as c:used=c.scalar(text("SELECT count(*) FROM audit_event WHERE actor_id=:id AND action='invitation_sent'"),{'id':actors['owner'].user_id})
            remaining=200-used
            for offset in range(0,remaining,50):sharing.invite_by_email(actors['owner'],catalog['secondary'].id,[f'rate-{index}@w12-fixture.invalid' for index in range(offset,min(offset+50,remaining))])
            return {'used':200}
        for _ in range(3):app.router.routes.insert(0,app.router.routes.pop())
        summary.update(courseIds={key:value.id for key,value in catalog.items()},accountIds={key:value.user_id for key,value in actors.items()},invitationIds=invitation_ids)
        with audit.connect() as c:summary['migrationHead']=c.scalar(text('SELECT version_num FROM alembic_version'))
        assert summary['migrationHead']=='w12_0008';save('runtime.json',summary)
        listener=socket.socket();listener.bind(('127.0.0.1',8027));listener.listen(128);listener.setblocking(False)
        server=uvicorn.Server(uvicorn.Config(app,log_config=None,access_log=False,log_level='warning',timeout_graceful_shutdown=5))
        thread=Thread(target=server.run,kwargs={'sockets':[listener]},daemon=True);thread.start()
        deadline=monotonic()+15
        while not server.started and monotonic()<deadline:sleep(.05)
        assert server.started
        result=subprocess.run(['node',str(Path('C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-r10-tools-20261028/w12_real_race.cjs'))],cwd=ROOT,env=dict(os.environ,W12_REACT_RUNTIME=str(OUT/'runtime.json')))
        summary['browserExitCode']=result.returncode;summary['independentSqlFinal']=probe()
        invitations=[m for m in mailer.messages if m['html_body'] and '/dang-ky#invitation=' in m['html_body']]
        if invitations:
            html=invitations[0]['html_body'];html=re.sub(r'(invitation=)[A-Za-z0-9_-]+',r'\1[REDACTED]',html)
            (OUT/'fake-invitation-redacted.html').write_text(html,encoding='utf8')
        return result.returncode
    finally:
        if server:server.should_exit=True
        if thread:
            thread.join(10)
            if thread.is_alive():server.force_exit=True;thread.join(10)
            summary['serverThreadStopped']=not thread.is_alive()
        if listener:listener.close()
        if phase:phase.close()
        if engine:engine.dispose()
        if audit:audit.dispose()
        if created:
            assert re.fullmatch('wayfinder_w12_react_[0-9a-f]{32}',name)
            with admin.connect() as c:c.execute(text(f'DROP DATABASE "{name}" WITH (FORCE)'))
            summary['temporaryDatabaseRemoved']=True
        admin.dispose();save('runtime.json',summary)
if __name__=='__main__':raise SystemExit(main())
