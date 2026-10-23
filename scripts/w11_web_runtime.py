"""W11 real HTTP/PG acceptance, isolated UUID database and fake providers."""
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
from threading import Thread
from time import monotonic, sleep
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src/web/backend'),str(ROOT/'src'),str(ROOT/'scripts')]
from dotenv import dotenv_values
from sqlalchemy import text
from sqlalchemy.engine import make_url
import uvicorn
from fastapi import Response
from doc2roadmap.application.phase_b.retrieval import load_learning_graph
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore
from wayfinder.api.app import create_app
from wayfinder.composition import WebServices, compose_account_service, compose_course_services, compose_sharing_service
from wayfinder.domain.auth import Actor
from wayfinder.fakes.mail import FakeMailer
from wayfinder.infrastructure.database import create_database_engine, upgrade_database
from wayfinder.infrastructure.phase_b_store import PostgresPhaseBStore
from wayfinder.settings import WebSettings
from w14_web_runtime import _forbid_live_providers

RUN=os.environ.get('W11_EVIDENCE_RUN','browser-final')
assert re.fullmatch(r'browser-[a-z0-9-]+',RUN)
OUT=ROOT/'report/w11-evidence/auth-return-2026-10-23'/RUN
BASE='http://127.0.0.1:8011'


def main():
    values=dotenv_values(ROOT.parents[1]/'src/web/.env')
    url=make_url(values['WAYFINDER_TEST_DATABASE_URL'])
    assert url.database=='wayfinder_test' and url.get_backend_name()=='postgresql'
    _forbid_live_providers()
    name='wayfinder_w11_'+uuid4().hex
    admin=create_database_engine(url).execution_options(isolation_level='AUTOCOMMIT')
    OUT.mkdir(parents=True,exist_ok=True)
    summary=dict(base=BASE,database='UUID PostgreSQL',databaseName=name,modelCalls=0,externalCostUsd=0,
                 mailer='FakeMailer',media='unused; no media calls',temporaryDatabaseRemoved=False)
    engine=audit=phase=server=thread=listener=None
    created=False
    try:
        with admin.connect() as c: c.execute(text(f'CREATE DATABASE "{name}"'))
        created=True; db=url.set(database=name); upgrade_database(db)
        engine=create_database_engine(db); audit=create_database_engine(db)
        settings=WebSettings(_env_file=None,database_url=db.render_as_string(hide_password=False),
            frontend_dist=ROOT/'src/web/frontend/dist',artifact_root=ROOT/'artifacts',
            allowed_origins=[BASE],public_base_url=BASE,env='dev',mailer='console')
        accounts=compose_account_service(settings,engine,mailer=FakeMailer())
        grant=accounts.register('owner-w11@example.invalid','W11 browser acceptance passphrase!','Cô Mai',ip=None,user_agent=None)
        owner=Actor(grant.session.account.id,'user',False,'active')
        phase=PostgresPhaseBStore(engine)
        def graph_loader(doc,version): return load_learning_graph(JsonArtifactStore(settings.artifact_root),doc,version)
        graph=graph_loader('doc-1',8)
        courses,learning=compose_course_services(settings,engine,phase,graph_loader=graph_loader)
        course=courses.create_course(owner,doc_id='doc-1',title='Đại số tuyến tính',graph_version=8,module_count=len(graph.modules))
        sharing=compose_sharing_service(settings,engine,graph_loader=graph_loader)
        expired=sharing.create_share_link(owner,course.id)['link']
        with engine.begin() as c:
            c.execute(text("UPDATE share_link SET expires_at=now()-interval '1 day' WHERE id=:id"),{'id':expired['id']})
        services=WebServices(health_check=lambda:'ok',accounts=accounts,phase_b_store=phase,courses=courses,learning=learning,sharing=sharing)
        app=create_app(settings,services)
        @app.get('/__test__/redact.css')
        def redact_css():
            return Response('.sharing-once code { -webkit-text-security: disc; }',media_type='text/css')
        redaction=app.router.routes.pop()
        app.router.routes.insert(0,redaction)
        summary.update(courseId=course.id,ownerId=owner.user_id,nodeId=next(iter(graph.learnable_nodes)))
        with audit.connect() as c: summary['migrationHead']=c.scalar(text('SELECT version_num FROM alembic_version'))
        assert summary['migrationHead']=='w11_0007'
        (OUT/'runtime.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
        listener=socket.socket(); listener.bind(('127.0.0.1',8011)); listener.listen(128); listener.setblocking(False)
        server=uvicorn.Server(uvicorn.Config(app,log_config=None,access_log=False,log_level='warning'))
        thread=Thread(target=server.run,kwargs={'sockets':[listener]},daemon=True); thread.start()
        deadline=monotonic()+15
        while not server.started and monotonic()<deadline: sleep(.05)
        assert server.started
        env=dict(os.environ,W11_RUNTIME=str(OUT/'runtime.json'),W11_EXPIRED_TOKEN=expired['token'])
        run=subprocess.run(['node',str(ROOT/'scripts/w11_web_check.cjs')],cwd=ROOT,env=env)
        summary['browserExitCode']=run.returncode
        if run.returncode==0:
            state=json.loads((OUT/'state.json').read_text(encoding='utf-8'))
            with audit.connect() as c:
                members=c.scalar(text('SELECT count(*) FROM membership WHERE course_id=:cid'),{'cid':course.id})
                use=c.scalar(text('SELECT use_count FROM share_link WHERE id=:id'),{'id':state['primaryLinkId']})
                switched_use=c.scalar(text('SELECT use_count FROM share_link WHERE id=:id'),{'id':state['authReturnLinkId']})
                columns=list(c.scalars(text("SELECT column_name FROM information_schema.columns WHERE table_name='share_link'")))
                learned=c.scalar(text("SELECT count(*) FROM phase_b_record WHERE owner=:uid AND doc_id='doc-1'"),{'uid':state['learnerId']})
                events=list(c.scalars(text("SELECT action FROM audit_event WHERE action IN ('share_link_created','share_link_revoked','member_joined','member_removed','member_left')")))
            assert members==1 and use==1 and learned>0
            assert switched_use==8 and len(set(state['authReturnLearnerIds']))==8
            assert 'token' not in columns and 'token_hash' in columns
            assert set(events)=={'share_link_created','share_link_revoked','member_joined','member_removed','member_left'}
            summary['independentSql']=dict(memberCount=members,primaryUseCount=use,authReturnUseCount=switched_use,retainedPhaseBRows=learned,tokenColumns=columns,auditActions=sorted(set(events)))
        return run.returncode
    finally:
        if server: server.should_exit=True
        if thread:
            thread.join(20); assert not thread.is_alive()
        if listener: listener.close()
        if phase: phase.close()
        if engine: engine.dispose()
        if audit: audit.dispose()
        if created:
            assert re.fullmatch(r'wayfinder_w11_[0-9a-f]{32}',name)
            with admin.connect() as c: c.execute(text(f'DROP DATABASE "{name}" WITH (FORCE)'))
            summary['temporaryDatabaseRemoved']=True
        admin.dispose()
        (OUT/'runtime.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__': raise SystemExit(main())
