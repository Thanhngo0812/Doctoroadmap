"""W16 browser runtime: isolated PostgreSQL, real core, fake providers only."""
import json
import os
from pathlib import Path
from datetime import datetime, timezone
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
from wayfinder.composition import WebServices, compose_account_service, compose_course_services, compose_sharing_service, compose_build_service
from wayfinder.domain.auth import Actor
from wayfinder.domain.courses import Membership
from wayfinder.fakes.quiz import ScriptedQuizModel
from wayfinder.fakes.assistant import ScriptedAssistantModel
from wayfinder.fakes.lecture import ScriptedLectureModel
from wayfinder.fakes.mail import FakeMailer
from wayfinder.infrastructure.database import create_database_engine, upgrade_database
from wayfinder.infrastructure.phase_b_store import PostgresPhaseBStore
from wayfinder.settings import WebSettings
from wayfinder.testing import FakeClock
from w08_web_runtime import LocalImageMedia
from w14_web_runtime import _forbid_live_providers

BASE = 'http://127.0.0.1:8026'
RUN = os.environ.get('W16_EVIDENCE_RUN', 'browser-dev1')
assert re.fullmatch(r'browser-[a-z0-9-]+', RUN)
EVIDENCE = 'w16-react-evidence'
OUT = ROOT / 'report' / EVIDENCE / RUN


def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf8')


def main():
    assert not OUT.exists(), 'Use a fresh W16_EVIDENCE_RUN; retain prior evidence'
    OUT.mkdir(parents=True)
    url = make_url(dotenv_values(ROOT.parents[1] / 'src/web/.env')['WAYFINDER_TEST_DATABASE_URL'])
    assert url.database == 'wayfinder_test' and url.get_backend_name() == 'postgresql'
    _forbid_live_providers()
    name = 'wayfinder_w16_' + uuid4().hex
    admin = create_database_engine(url).execution_options(isolation_level='AUTOCOMMIT')
    engine = audit = phase = server = thread = listener = None
    created = False
    generator, solver = ScriptedQuizModel(), None
    solver = ScriptedQuizModel(generator)
    documents = []
    summary = dict(base=BASE, databaseName=name, temporaryDatabaseRemoved=False, externalCostUsd=0,
        providers='ScriptedQuizModel/ScriptedLectureModel/FakeMailer/LocalImageMedia; no embedding',
        sourceCommit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        dirtySourcePaths=subprocess.check_output(['git', 'diff', 'HEAD', '--name-only', '--', 'src', 'scripts'], cwd=ROOT, text=True).splitlines())
    try:
        with admin.connect() as c:
            c.execute(text(f'CREATE DATABASE "{name}"'))
        created = True
        db = url.set(database=name); upgrade_database(db)
        engine, audit = create_database_engine(db), create_database_engine(db)
        settings = WebSettings(_env_file=None, database_url=db.render_as_string(hide_password=False),
            frontend_dist=ROOT / 'src/web/frontend/dist', artifact_root=ROOT / 'artifacts',
            allowed_origins=[BASE], public_base_url=BASE)
        accounts = compose_account_service(settings, engine, mailer=FakeMailer())
        actors = {}
        for label, display in [('owner', 'Cô Mai'), ('learner', 'Nguyễn An'), ('outsider', 'Người ngoài')]:
            grant = accounts.register(label + '-w16@example.invalid', 'W16 isolated browser passphrase!', display, ip=None, user_agent=None)
            actors[label] = Actor(grant.session.account.id, 'user', False, 'active')
        phase, media, clock = PostgresPhaseBStore(engine), LocalImageMedia(), FakeClock()
        document = ScriptedLectureModel([['# Ghi chú ôn tập\n\n', 'Ta có $1+1=2$. [S1]\n\nNhãn chưa biết [S999].\n\n<img src=x onerror=alert(1)>']])
        documents.append(document)
        lecture = ScriptedLectureModel()
        # Fake transport, real spend admission: replay mode intentionally skips budget checks.
        lecture.is_replay = False
        generator.is_replay = False
        solver.is_replay = False
        assistant = ScriptedAssistantModel(scenario='document')
        assistant.is_replay = False
        courses, gateway = compose_course_services(settings, engine, phase, clock=clock, model=lecture, media=media,
            model_for=lambda purpose: {'quiz_gen': generator, 'quiz_verify': solver, 'document': document, 'assistant': assistant}.get(purpose))
        graph = gateway.graph_loader('doc-1', 8)
        modules = sorted((m for m in graph.modules.values() if m['node_ids']), key=lambda m: m.get('index', 0))
        ma, mb = modules[0]['module_id'], modules[1]['module_id']
        clock.instant = datetime(2026, 10, 26, 16, 59, tzinfo=timezone.utc)
        source = media.upload(ROOT / 'doc-1.pdf', 'private/w16/source', 'image')
        course = courses.create_course(actors['owner'], doc_id='doc-1', title='Đại số tuyến tính', graph_version=8,
            module_count=len(graph.modules), source_public_id=source)
        with courses.store.atomic():
            courses.store.add_membership(Membership(course.id, actors['learner'].user_id, 'learner', 'email', clock.now(), clock.now()))
        # Crossed origin/home fixtures are generated by the real core into the private PG store.
        for home, target in [(ma, mb), (mb, ma)]:
            for origin in ['button', 'assistant']:
                made = gateway.runtime.document(graph).create('doc-1', 8, graph, 'Ôn ' + graph.modules[target]['title'],
                    {'module_ids': [target]}, owner=actors['learner'].user_id, origin=origin, allow_spend=True,
                    home_scope=gateway._content_scope(graph, home))
                assert made['status'] == 'ready'
        sharing = compose_sharing_service(settings, engine, graph_loader=gateway.graph_loader, clock=clock)
        cached_node = modules[0]['node_ids'][0]
        cold_node = modules[0]['node_ids'][1]
        gateway.stream_lecture(actors['learner'], course.id, cached_node, lambda event: None)
        assert gateway.get_lecture(actors['learner'], course.id, cached_node)['status'] == 'ready'
        cached_quiz = gateway.make_quiz(actors['learner'], course.id, {'kind': 'module', 'module_id': ma}, 1)
        build_service = compose_build_service(settings, engine, media=media, clock=clock)
        app = create_app(settings, WebServices(health_check=lambda: 'ok', accounts=accounts, phase_b_store=phase,
            courses=courses, learning=gateway, sharing=sharing, builds=build_service))

        @app.post('/api/v1/__test/w16/control')
        async def control(request: Request, actor=Depends(get_actor)):
            nonlocal document
            if actor.user_id != actors['owner'].user_id:
                raise WebError('not_found', 'Không tìm thấy nội dung')
            data = await request.json()
            action = data.get('action')
            if action == 'state':
                # Fresh synthetic day; projection and spend guards remain real.
                clock.advance(86400)
                ratio = float(data.get('ratio', 0))
                assert ratio in {0, .35, .85, 1}
                settings.build_monthly_max = None if data.get('unlimited', True) else 3
                phase.append_usage({'purpose': 'assistant', 'cost_usd': ratio, 'learner_id': actors['learner'].user_id,
                    'doc_id': 'doc-1', 'created_at': clock.now().isoformat(), 'fixture': 'synthetic W16 ratio, not external spend'})
                if data.get('shared'):
                    phase.append_usage({'purpose': 'lecture', 'cost_usd': 5, 'learner_id': actors['owner'].user_id,
                        'doc_id': 'doc-1', 'created_at': clock.now().isoformat(), 'fixture': 'synthetic W16 shared cap'})
                return {'clock': clock.now().isoformat()}
            if action == 'probe':
                with audit.connect() as c:
                    ledger = c.execute(text('SELECT learner_id,purpose,cost_usd,created_at FROM usage_ledger ORDER BY created_at')).mappings().all()
                return {'ledgerRows': len(ledger), 'lectureCalls': len(lecture.calls), 'generatorCalls': len(generator.calls),
                    'documentCalls': sum(len(row.calls) for row in documents), 'assistantCalls': len(assistant.calls)}
            raise WebError('validation', 'Kịch bản không hợp lệ')

        app.router.routes.insert(0, app.router.routes.pop())
        summary.update(courseId=course.id, moduleA=ma, moduleB=mb, learnerId=actors['learner'].user_id,
            modules=[{'id': row['module_id'], 'title': row['title']} for row in modules],
            controlPath='/api/v1/__test/w16/control', cachedNode=cached_node, coldNode=cold_node, quizId=cached_quiz['attempt_id'])
        with audit.connect() as c:
            summary['migrationHead'] = c.scalar(text('SELECT version_num FROM alembic_version'))
        assert summary['migrationHead'] == 'w12_0008'
        save('runtime.json', summary)
        listener = socket.socket(); listener.bind(('127.0.0.1', 8026)); listener.listen(128); listener.setblocking(False)
        server = uvicorn.Server(uvicorn.Config(app, log_config=None, access_log=False, log_level='warning', timeout_graceful_shutdown=5))
        thread = Thread(target=server.run, kwargs={'sockets': [listener]}, daemon=True); thread.start()
        deadline = monotonic() + 15
        while not server.started and monotonic() < deadline:
            sleep(.05)
        assert server.started
        result = subprocess.run(['node', str(ROOT / 'scripts/w16_web_check.cjs')], cwd=ROOT,
            env=dict(os.environ, W16_RUNTIME=str(OUT / 'runtime.json')))
        summary['browserExitCode'] = result.returncode
        with audit.connect() as c:
            summary['independentSql'] = {
                'records': [dict(row) for row in c.execute(text("SELECT kind,owner,count(*) AS count FROM phase_b_record WHERE kind IN ('quiz_attempt','documents','progress') GROUP BY kind,owner ORDER BY kind")).mappings()],
                'submissions': list(c.scalars(text("SELECT value->'submission' FROM phase_b_record WHERE kind='quiz_attempt' AND value ? 'submission'"))),
                'usage': [{**dict(row), 'usd': float(row['usd'])} for row in c.execute(text("SELECT purpose,count(*) AS rows,sum(cost_usd) AS usd FROM usage_ledger GROUP BY purpose")).mappings()],
            }
        return result.returncode
    finally:
        generator.release.set()
        for row in documents:
            row.release.set()
        if server:
            server.should_exit = True
        if thread:
            thread.join(10)
            if thread.is_alive():
                server.force_exit = True; thread.join(10)
            summary['serverThreadStopped'] = not thread.is_alive()
        if listener:
            listener.close()
        if phase:
            phase.close()
        if engine:
            engine.dispose()
        if audit:
            audit.dispose()
        if created:
            assert re.fullmatch(r'wayfinder_w16_[0-9a-f]{32}', name)
            with admin.connect() as c:
                c.execute(text(f'DROP DATABASE "{name}" WITH (FORCE)'))
            summary['temporaryDatabaseRemoved'] = True
        admin.dispose(); save('runtime.json', summary)
        assert not thread or not thread.is_alive()


if __name__ == '__main__':
    raise SystemExit(main())
