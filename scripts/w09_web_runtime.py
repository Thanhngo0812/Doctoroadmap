"""W09 real HTTP/Assistant3/PostgreSQL; isolated database and fake providers only."""
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

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src/web/backend'), str(ROOT / 'src'), str(ROOT / 'scripts')]
from dotenv import dotenv_values
from fastapi import Depends, Request
from sqlalchemy import text
from sqlalchemy.engine import make_url
import uvicorn
from wayfinder.api.app import create_app
from wayfinder.api.auth import get_actor
from wayfinder.api.errors import WebError
from wayfinder.composition import WebServices, compose_account_service, compose_course_services, compose_sharing_service
from wayfinder.domain.auth import Actor
from wayfinder.domain.courses import Membership
from wayfinder.fakes.assistant import ScriptedAssistantModel
from wayfinder.fakes.lecture import ScriptedLectureModel
from wayfinder.fakes.mail import FakeMailer
from wayfinder.infrastructure.database import create_database_engine, upgrade_database
from wayfinder.infrastructure.phase_b_store import PostgresPhaseBStore
from wayfinder.settings import WebSettings
from wayfinder.testing import FakeClock
from w08_web_runtime import LocalImageMedia
from w14_web_runtime import _forbid_live_providers

BASE = 'http://127.0.0.1:8019'
RUN = os.environ.get('W09_EVIDENCE_RUN', 'browser-dev1')
assert re.fullmatch(r'browser-[a-z0-9-]+', RUN)
OUT = ROOT / 'report/w09-evidence' / RUN


def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf8')


def main():
    assert not OUT.exists(), 'Choose a fresh W09_EVIDENCE_RUN; retain prior evidence'
    OUT.mkdir(parents=True)
    values = dotenv_values(ROOT.parents[1] / 'src/web/.env')
    url = make_url(values['WAYFINDER_TEST_DATABASE_URL'])
    assert url.database == 'wayfinder_test' and url.get_backend_name() == 'postgresql'
    _forbid_live_providers()
    name = 'wayfinder_w09_' + uuid4().hex
    admin = create_database_engine(url).execution_options(isolation_level='AUTOCOMMIT')
    engine = audit = phase = server = thread = listener = None
    created = False; models = []
    summary = dict(base=BASE, databaseName=name, temporaryDatabaseRemoved=False,
        externalCostUsd=0, providers='scripted model/embedding-free local search, FakeMailer, LocalImageMedia',
        sourceCommit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        dirtySourcePaths=subprocess.check_output(['git', 'diff', 'HEAD', '--name-only', '--', 'src', 'scripts'], cwd=ROOT, text=True).splitlines())
    try:
        with admin.connect() as c: c.execute(text(f'CREATE DATABASE "{name}"'))
        created = True; db = url.set(database=name); upgrade_database(db)
        engine = create_database_engine(db); audit = create_database_engine(db)
        settings = WebSettings(_env_file=None, database_url=db.render_as_string(hide_password=False),
            frontend_dist=ROOT / 'src/web/frontend/dist', artifact_root=ROOT / 'artifacts',
            allowed_origins=[BASE], public_base_url=BASE)
        accounts = compose_account_service(settings, engine, mailer=FakeMailer())
        actors = {}
        for label, display in [('owner', 'Cô Mai'), ('learner', 'Nguyễn An'), ('outsider', 'Người ngoài')]:
            grant = accounts.register(f'{label}-w09@example.invalid', 'W09 isolated browser passphrase!', display, ip=None, user_agent=None)
            actors[label] = Actor(grant.session.account.id, 'user', False, 'active')
        phase = PostgresPhaseBStore(engine); media = LocalImageMedia(); clock = FakeClock()
        lecture = ScriptedLectureModel()
        courses, learning = compose_course_services(settings, engine, phase, model=lecture, media=media)
        learning.runtime.clock = clock
        learning.runtime.spend_guard.clock = clock
        graph = learning.graph_loader('doc-1', 8)
        nid = next(node for node in graph.learnable_nodes if graph.why_here(node)['prerequisites'])
        mid = graph.nodes[nid]['module_id']
        pdf = media.upload(ROOT / 'doc-1.pdf', 'private/w09/source', 'image')
        course = courses.create_course(actors['owner'], doc_id='doc-1', title='Đại số tuyến tính', graph_version=8,
            module_count=len(graph.modules), source_public_id=pdf)
        with courses.store.atomic():
            courses.store.add_membership(Membership(course.id, actors['learner'].user_id, 'learner', 'email', clock.now(), clock.now()))
        learning.runtime.lecture(graph).make('doc-1', 8, graph, nid, owner=actors['learner'].user_id, allow_spend=True)
        assistant = ScriptedAssistantModel()
        document = ScriptedLectureModel([['Tài liệu ôn tập đã lưu. ', '$x^2$ [S1]']], pause_after_first=True)
        models.extend([assistant, document, lecture])
        learning.runtime.model_for = lambda purpose: assistant if purpose == 'assistant' else document if purpose == 'document' else None
        sharing = compose_sharing_service(settings, engine, graph_loader=learning.graph_loader)
        app = create_app(settings, WebServices(health_check=lambda: 'ok', accounts=accounts, phase_b_store=phase,
            courses=courses, learning=learning, sharing=sharing))
        control_path = '/api/v1/__test/w09/control'

        @app.post(control_path)
        async def control(request: Request, actor=Depends(get_actor)):
            nonlocal assistant
            if actor.user_id != actors['owner'].user_id:
                raise WebError('not_found', 'Không tìm thấy nội dung')
            data = await request.json(); action = data.get('action')
            if action == 'probe':
                with audit.connect() as c:
                    turns = c.scalar(text("SELECT count(*) FROM phase_b_record WHERE kind='turn'"))
                    quizzes = c.scalar(text("SELECT count(*) FROM phase_b_record WHERE kind='quiz_attempt'"))
                    documents = c.scalar(text("SELECT count(*) FROM phase_b_record WHERE kind='documents'"))
                return dict(calls=len(assistant.calls), finished=all(row.finished for row in assistant.calls), turns=turns,
                    quizzes=quizzes, documents=documents)
            if action == 'release':
                assistant.release.set(); return {'released': True}
            if action == 'release-tools':
                document.release.set(); return {'released': True}
            if action == 'advance':
                clock.advance(61); return {'advanced': True}
            if action == 'limit':
                phase.append_usage({'usage_id': uuid4().hex, 'doc_id': 'another-book', 'purpose': 'document',
                    'learner_id': actors['learner'].user_id, 'cost_usd': 1.0, 'created_at': clock.now().isoformat()})
                return {'syntheticLedgerFixture': True}
            if action == 'old-scope':
                with engine.begin() as c:
                    c.execute(text("UPDATE phase_b_record SET value=jsonb_set(value,'{scope,node_ids}','[\"retired-fixture-node\"]') WHERE kind='session' AND owner=:owner AND value->'scope'->>'kind'='module'"), {'owner': actors['learner'].user_id})
                return {'changed': True}
            if action == 'scenario' and data.get('name') in {'normal', 'tail', 'failure', 'tools'}:
                assert all(row.finished for row in assistant.calls), 'Previous fake turn still running'
                assistant = ScriptedAssistantModel(scenario=data['name'], pause=bool(data.get('pause')))
                models.append(assistant); return {'scenario': data['name']}
            raise WebError('validation', 'Kịch bản không hợp lệ')

        app.router.routes.insert(0, app.router.routes.pop())
        with audit.connect() as c: head = c.scalar(text('SELECT version_num FROM alembic_version'))
        assert head == 'w11_0007'
        summary.update(courseId=course.id, ownerId=actors['owner'].user_id, learnerId=actors['learner'].user_id,
            nodeId=nid, moduleId=mid, otherNodeId=next(n for n in graph.modules[mid]['node_ids'] if n != nid and n in graph.learnable_nodes),
            controlPath=control_path, migrationHead=head)
        save('runtime.json', summary)
        listener = socket.socket(); listener.bind(('127.0.0.1', 8019)); listener.listen(128); listener.setblocking(False)
        server = uvicorn.Server(uvicorn.Config(app, log_config=None, access_log=False, log_level='warning', timeout_graceful_shutdown=5))
        thread = Thread(target=server.run, kwargs={'sockets': [listener]}, daemon=True); thread.start()
        deadline = monotonic() + 15
        while not server.started and monotonic() < deadline: sleep(.05)
        assert server.started
        result = subprocess.run(['node', str(ROOT / 'scripts/w09_web_check.cjs')], cwd=ROOT,
            env=dict(os.environ, W09_RUNTIME=str(OUT / 'runtime.json')))
        summary['browserExitCode'] = result.returncode
        with audit.connect() as c:
            records = c.execute(text("SELECT kind,count(*) AS count FROM phase_b_record GROUP BY kind ORDER BY kind")).mappings().all()
            owners = c.execute(text("SELECT DISTINCT owner FROM phase_b_record WHERE kind IN ('session','turn','documents','quiz_attempt')")).scalars().all()
            usage = c.execute(text("SELECT purpose,count(*) AS rows,sum(cost_usd) AS usd FROM usage_ledger GROUP BY purpose")).mappings().all()
        summary['independentSql'] = dict(records=[dict(row) for row in records], owners=owners,
            usage=[{**dict(row), 'usd': float(row['usd'])} for row in usage], syntheticLimitUsd=1.0,
            sourcePages=media.pages, fakeProviderCalls=sum(len(model.calls) for model in models))
        assert all(owner in [actors['learner'].user_id, actors['owner'].user_id] for owner in owners)
        return result.returncode
    finally:
        for model in models: model.release.set()
        if server: server.should_exit = True
        if thread:
            thread.join(10)
            if thread.is_alive(): server.force_exit = True; thread.join(10)
            summary['serverThreadStopped'] = not thread.is_alive()
        if listener: listener.close()
        if phase: phase.close()
        if engine: engine.dispose()
        if audit: audit.dispose()
        if created:
            assert re.fullmatch(r'wayfinder_w09_[0-9a-f]{32}', name)
            with admin.connect() as c: c.execute(text(f'DROP DATABASE "{name}" WITH (FORCE)'))
            summary['temporaryDatabaseRemoved'] = True
        admin.dispose(); save('runtime.json', summary)
        assert not thread or not thread.is_alive()


if __name__ == '__main__': raise SystemExit(main())
