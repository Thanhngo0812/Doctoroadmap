"""W08 browser: actual Lecture3UseCase/HTTP/PostgreSQL, local fake providers only."""
import io
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
from threading import Lock, Thread
from time import monotonic, sleep
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src/web/backend'), str(ROOT / 'src'), str(ROOT / 'scripts')]
from dotenv import dotenv_values
from fastapi import Depends, Request
from PIL import Image
import pypdfium2
from sqlalchemy import text
from sqlalchemy.engine import make_url
import uvicorn

from wayfinder.api.app import create_app
from wayfinder.api.auth import get_actor
from wayfinder.api.errors import WebError
from wayfinder.composition import WebServices, compose_account_service, compose_course_services, compose_sharing_service
from wayfinder.domain.auth import Actor
from wayfinder.domain.courses import Membership
from wayfinder.fakes.lecture import BODY, ScriptedLectureModel
from wayfinder.fakes.mail import FakeMailer
from wayfinder.fakes.media import MemoryMediaStore
from wayfinder.infrastructure.database import create_database_engine, upgrade_database
from wayfinder.infrastructure.phase_b_store import PostgresPhaseBStore
from wayfinder.settings import WebSettings
from w14_web_runtime import _forbid_live_providers

BASE = 'http://127.0.0.1:8018'
RUN = os.environ.get('W08_EVIDENCE_RUN', 'browser-dev1')
assert re.fullmatch(r'browser-[a-z0-9-]+', RUN)
OUT = ROOT / 'report/w08-evidence' / RUN


class LocalImageMedia(MemoryMediaStore):
    """Render the manifest-copied PDF locally to model a private Cloudinary response."""
    def __init__(self):
        super().__init__()
        self.pages = []
        self.render_lock = Lock()

    def fetch_page_image(self, public_id, page, width):
        raw = self._get(public_id)
        self.pages.append(page)
        with self.render_lock, pypdfium2.PdfDocument(raw) as document:
            source = document[page - 1]
            try:
                bitmap = source.render(scale=width / source.get_width())
                try:
                    image = bitmap.to_pil()
                    output = io.BytesIO(); image.save(output, 'WEBP')
                    image.close()
                    return output.getvalue()
                finally:
                    bitmap.close()
            finally:
                source.close()

    def fetch_image(self, public_id):
        with Image.open(io.BytesIO(self._get(public_id))) as image:
            output = io.BytesIO(); image.save(output, 'WEBP')
            return output.getvalue()


def save(name, value):
    (OUT / name).write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode())


def main():
    assert not OUT.exists(), 'Use a fresh W08_EVIDENCE_RUN; previous evidence must be retained'
    OUT.mkdir(parents=True)
    values = dotenv_values(ROOT.parents[1] / 'src/web/.env')
    url = make_url(values['WAYFINDER_TEST_DATABASE_URL'])
    assert url.database == 'wayfinder_test' and url.get_backend_name() == 'postgresql'
    _forbid_live_providers()
    name = 'wayfinder_w08_' + uuid4().hex
    admin = create_database_engine(url).execution_options(isolation_level='AUTOCOMMIT')
    engine = audit = phase = server = thread = listener = None
    models = []
    summary = dict(base=BASE, databaseName=name, temporaryDatabaseRemoved=False, modelCalls=0,
        externalCostUsd=0, mailer='FakeMailer', media='LocalImageMedia: copied PDF rendered locally',
        core='Lecture3UseCase received through reviewed SA64 and SA70 merge 5188908',
        sourceCommit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        dirtySourcePaths=subprocess.check_output(['git', 'diff', 'HEAD', '--name-only', '--', 'src', 'scripts'], cwd=ROOT, text=True).splitlines())
    created = False
    try:
        with admin.connect() as c: c.execute(text(f'CREATE DATABASE "{name}"'))
        created = True
        db = url.set(database=name); upgrade_database(db)
        engine = create_database_engine(db); audit = create_database_engine(db)
        settings = WebSettings(_env_file=None, database_url=db.render_as_string(hide_password=False),
            frontend_dist=ROOT / 'src/web/frontend/dist', artifact_root=ROOT / 'artifacts',
            allowed_origins=[BASE], public_base_url=BASE)
        accounts = compose_account_service(settings, engine, mailer=FakeMailer())
        identities = {}
        for label in ['owner', 'learner', 'outsider']:
            grant = accounts.register(f'{label}-w08@example.invalid', 'W08 isolated browser passphrase!',
                {'owner': 'Cô Mai', 'learner': 'Nguyễn An', 'outsider': 'Người ngoài'}[label], ip=None, user_agent=None)
            identities[label] = Actor(grant.session.account.id, 'user', False, 'active')
        phase = PostgresPhaseBStore(engine)
        media = LocalImageMedia()
        courses, learning = compose_course_services(settings, engine, phase, model=ScriptedLectureModel(), media=media)
        graph = learning.graph_loader('doc-1', 8)
        node_id = next(nid for nid in graph.learnable_nodes if graph.why_here(nid)['prerequisites'])
        module_id = graph.nodes[node_id]['module_id']
        pdf_id = media.upload(ROOT / 'doc-1.pdf', 'private/w08/source', 'image')
        course = courses.create_course(identities['owner'], doc_id='doc-1', title='Đại số tuyến tính', graph_version=8,
            module_count=len(graph.modules), source_public_id=pdf_id)
        with courses.store.atomic():
            now = learning.runtime.clock.now()
            courses.store.add_membership(Membership(course.id, identities['learner'].user_id, 'learner', 'email', now, now))
        sharing = compose_sharing_service(settings, engine, graph_loader=learning.graph_loader)
        app = create_app(settings, WebServices(health_check=lambda: 'ok', accounts=accounts,
            phase_b_store=phase, courses=courses, learning=learning, sharing=sharing))
        control_path = '/api/v1/__test/w08/control'

        @app.post(control_path)
        async def control(request: Request, actor=Depends(get_actor)):
            # Fixture control exists only in this script, protected by the real auth/CSRF middleware.
            if actor.user_id != identities['owner'].user_id:
                raise WebError('not_found', 'Không tìm thấy nội dung yêu cầu')
            data = await request.json(); action = data.get('action')
            model = learning.runtime.model
            if action == 'probe':
                return {'calls': len(model.calls), 'finished': all(row.finished for row in model.calls)}
            if action == 'release':
                model.release.set()
                return {'released': True}
            if action == 'progress-probe':
                node = data.get('node_id')
                if node not in graph.learnable_nodes:
                    raise WebError('not_found', 'Không tìm thấy bài học')
                # Read through the independent engine, not a gateway response or React state.
                with audit.connect() as c:
                    row = c.scalar(text("SELECT value FROM phase_b_record WHERE kind='progress' AND owner=:owner AND doc_id='doc-1' AND value->>'node_id'=:node"),
                        {'owner': identities['learner'].user_id, 'node': node})
                return {'node_id': node, 'record': row}
            if action in {'progress-fail', 'progress-ok'}:
                with engine.begin() as c:
                    c.execute(text('DROP TRIGGER IF EXISTS w08_progress_failure ON phase_b_record'))
                    if action == 'progress-fail':
                        c.execute(text("CREATE OR REPLACE FUNCTION w08_fail_progress() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'W08 deliberate private-DB save failure'; END $$"))
                        c.execute(text("CREATE TRIGGER w08_progress_failure BEFORE INSERT OR UPDATE ON phase_b_record FOR EACH ROW WHEN (NEW.kind='progress') EXECUTE FUNCTION w08_fail_progress()"))
                return {'enabled': action == 'progress-fail'}
            headings = {'heading-two': '## Tự kiểm tra', 'heading-four': '#### Tự kiểm tra',
                'heading-indent': '  ### Tự kiểm tra', 'heading-colon': '### Tự kiểm tra:',
                'heading-tab': '\t##TỰ KIỂM TRA ::'}
            if action != 'scenario' or data.get('name') not in {'normal', 'tail', 'empty', 'no-self-check', 'unsafe', 'unsplit', *headings}:
                raise WebError('validation', 'Kịch bản kiểm không hợp lệ')
            if any(not row.finished for row in model.calls):
                raise WebError('conflict', 'Lần sinh trước chưa hoàn tất')
            scripts = {
                'normal': [[BODY[:100], BODY[100:210], BODY[210:]]],
                'tail': [['Phần đã gửi được giữ lại. $x^2$ [S1]', RuntimeError('W08 scripted tail error')]],
                'empty': [[RuntimeError('W08 scripted empty failure')]],
                'no-self-check': [['Bài này không có câu hỏi tự kiểm tra riêng. [S1]']],
                'unsafe': [['Nội dung an toàn. <script>window.__w08pwned=true</script>\n\n![bad](https://evil.example/image)\n\n[bad](javascript:alert%281%29)\n\n$\\htmlClass{w08-injected}{bad}$']],
                'unsplit': [['Phần chính nguyên vẹn.\n\n## Tự kiểm tra\n\nĐoạn cuối thiếu khuôn hỏi đáp vẫn phải được giữ ở final.']],
            }
            scripts.update({name: [[f'Phần chính hiện ngay.\n\n{heading}\n\n**Câu hỏi:** Câu hỏi kiểm riêng.\n\n**Đáp án:** Đáp án riêng phải gập.', '\n']]
                for name, heading in headings.items()})
            model = ScriptedLectureModel(scripts[data['name']], delay_seconds=3 if data['name'] == 'normal' or data['name'] in headings else 0)
            models.append(model); learning.runtime.model = model
            with engine.begin() as c:
                c.execute(text("DELETE FROM phase_b_cache WHERE value->>'doc_id'='doc-1'"))
                c.execute(text("DELETE FROM phase_b_record WHERE kind='lecture_failure'"))
            return {'scenario': data['name']}

        # Insert the local fixture route ahead of the SPA catch-all; production create_app has no such route.
        app.router.routes.insert(0, app.router.routes.pop())
        summary.update(courseId=course.id, ownerId=identities['owner'].user_id,
            learnerId=identities['learner'].user_id, nodeId=node_id, moduleId=module_id,
            controlPath=control_path, sourcePageCount=graph.tree.parse_stats['page_count'])
        with audit.connect() as c: summary['migrationHead'] = c.scalar(text('SELECT version_num FROM alembic_version'))
        assert summary['migrationHead'] == 'w11_0007'
        save('runtime.json', summary)
        listener = socket.socket(); listener.bind(('127.0.0.1', 8018)); listener.listen(128); listener.setblocking(False)
        server = uvicorn.Server(uvicorn.Config(app, log_config=None, access_log=False, log_level='warning', timeout_graceful_shutdown=5))
        thread = Thread(target=server.run, kwargs={'sockets': [listener]}, daemon=True); thread.start()
        deadline = monotonic() + 15
        while not server.started and monotonic() < deadline: sleep(.05)
        assert server.started
        result = subprocess.run(['node', str(ROOT / 'scripts/w08_web_check.cjs')], cwd=ROOT,
            env=dict(os.environ, W08_RUNTIME=str(OUT / 'runtime.json')))
        summary['browserExitCode'] = result.returncode
        summary['fakeModelCalls'] = sum(len(model.calls) for model in models)
        summary['sourcePagesFetched'] = media.pages
        if result.returncode == 0:
            with audit.connect() as c:
                cached = c.execute(text("SELECT key,value FROM phase_b_cache WHERE value->>'doc_id'='doc-1'" )).mappings().all()
                usage = c.execute(text("SELECT count(*) AS calls,coalesce(sum(cost_usd),0) AS usd,coalesce(sum(input_tokens),0) AS input_tokens FROM usage_ledger WHERE purpose='lecture'" )).mappings().one()
                members = c.scalar(text('SELECT count(*) FROM membership WHERE course_id=:cid'), {'cid': course.id})
                progress = c.execute(text("SELECT owner,value FROM phase_b_record WHERE kind='progress' AND doc_id='doc-1'" )).mappings().all()
            assert usage['calls'] > 0 and usage['usd'] == 0 and usage['input_tokens'] > 0
            assert members == 1 and cached and all('validation' in row['value'] for row in cached)
            summary['independentSql'] = {'cachedLessons': len(cached), 'adminValidationInCache': True,
                'usageRows': usage['calls'], 'fakeLedgerUsd': float(usage['usd']), 'fakeInputTokens': usage['input_tokens'],
                'memberCountAfterRemoval': members, 'progressOwners': sorted(set(row['owner'] for row in progress))}
        return result.returncode
    finally:
        for model in models: model.release.set()
        if server: server.should_exit = True
        if thread:
            thread.join(10)
            if thread.is_alive():
                server.force_exit = True
                thread.join(10)
            summary['serverThreadStopped'] = not thread.is_alive()
        if listener: listener.close()
        if phase: phase.close()
        if engine: engine.dispose()
        if audit: audit.dispose()
        if created:
            assert re.fullmatch(r'wayfinder_w08_[0-9a-f]{32}', name)
            with admin.connect() as c: c.execute(text(f'DROP DATABASE "{name}" WITH (FORCE)'))
            summary['temporaryDatabaseRemoved'] = True
        admin.dispose(); save('runtime.json', summary)
        assert not thread or not thread.is_alive(), 'Harness server must stop after database cleanup'


if __name__ == '__main__': raise SystemExit(main())
