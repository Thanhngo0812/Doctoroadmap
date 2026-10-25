"""Prepare isolated W-15 inputs/PG/profile without credentials or provider requests."""
import argparse
from contextlib import ExitStack
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from unittest.mock import patch
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'src/web/backend')]

from dotenv import dotenv_values
from sqlalchemy import text
from sqlalchemy.engine import URL, make_url
from doc2roadmap.application.use_cases.build_document import BuildDocument
from doc2roadmap.config import Settings
from wayfinder.infrastructure.database import create_database_engine, upgrade_database
from wayfinder.infrastructure.real_build import RealBuildRuntime
from wayfinder.settings import WebSettings


def test_database_url(database=None):
    values = dotenv_values(ROOT.parents[1] / 'src/web/.env')
    configured = os.environ.get('WAYFINDER_TEST_DATABASE_URL') or values.get('WAYFINDER_TEST_DATABASE_URL')
    url = make_url(configured) if configured else URL.create('postgresql+psycopg', username='wayfinder',
        password=values['POSTGRES_TEST_PASSWORD'], host='127.0.0.1', port=5433, database='wayfinder_test')
    if url.host not in {'127.0.0.1', 'localhost'}:
        raise ValueError('W-15 operator preparation uses local db-test only')
    return url.set(database=database) if database else url


def profile(run_dir, database):
    values = dotenv_values(ROOT.parents[1] / '.env')
    project = os.environ.get('DOC2ROADMAP_VERTEX_PROJECT') or values.get('DOC2ROADMAP_VERTEX_PROJECT')
    if not project:
        raise ValueError('A real Vertex project must be configured before preparing the exact profile')
    settings = WebSettings(_env_file=None, build_runner='real', artifact_root=run_dir / 'artifacts',
        database_url=test_database_url(database).render_as_string(hide_password=False),
        allowed_origins=['http://testserver'], frontend_dist=ROOT / 'src/web/frontend/dist')
    core = Settings(_env_file=None, artifact_dir=settings.artifact_root, llm_transport='vertex',
                    vertex_project=project, vertex_location='global')
    return settings, core


def prepare(book):
    candidate = json.loads((ROOT / 'report/w15-evidence/candidate.json').read_text(encoding='utf-8'))
    relative, expected = (('doc-6.pdf', '82cb494d407c4755d29deb7c08b9a4f3794f79e241c307fd2b5dfc149cd559c7')
        if book == 'doc-6' else (candidate['staged_copy'], candidate['sha256']))
    from wayfinder.domain.file_paths import safe_path
    source = safe_path(ROOT, relative)
    assert source.stat().st_nlink == 1 and sha256(source.read_bytes()).hexdigest() == expected
    nonce = uuid4().hex[:12]
    run_dir = ROOT / 'tmp' / ('w15-operator-' + book + '-' + nonce)
    database = 'wayfinder_w15_' + nonce
    settings, core = profile(run_dir, database)
    run_dir.mkdir()
    target = run_dir / 'source.pdf'
    shutil.copyfile(source, target)
    assert target.stat().st_nlink == 1 and sha256(target.read_bytes()).hexdigest() == expected
    admin = create_database_engine(test_database_url()).execution_options(isolation_level='AUTOCOMMIT')
    try:
        with admin.connect() as connection:
            connection.execute(text('CREATE DATABASE "' + database + '"'))
    finally:
        admin.dispose()
    upgrade_database(test_database_url(database))
    engine = create_database_engine(test_database_url(database))
    runtime = RealBuildRuntime(settings, engine, core_settings=core)
    receipts = []
    def forbidden(*args, **kwargs):
        raise AssertionError('W-15 prepare must never call provider/ADC/SMTP/Cloudinary')
    try:
        with ExitStack() as guards:
            for name in ('doc2roadmap.infrastructure.llm.gemini.urlopen', 'doc2roadmap.infrastructure.embedding.gemini.urlopen',
                         'doc2roadmap.infrastructure.llm.phase_b.urlopen', 'google.auth.default',
                         'doc2roadmap.infrastructure.google_auth.VertexCredentials.headers', 'smtplib.SMTP'):
                guards.enter_context(patch(name, forbidden))
            pipeline = runtime.pipeline_factory(core, allow_spend=False, phase_b_store=runtime.phase_b_store)
            result = BuildDocument(pipeline, runtime.pipeline_version, recorder=receipts.append).execute(
                target, 'u-' + expected[:20], dry_run=True)
        assert result.status == 'dry_run' and len(receipts) == 1 and result.model_calls == result.spent_usd == 0
        plan = dict(book=book, run_dir=run_dir.relative_to(ROOT).as_posix(), database=database, file_sha256=expected,
            pipeline_version=runtime.pipeline_version, prepared_commit=subprocess.check_output(
                ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(), dry_run=result.to_dict(),
            vertex_project_configured=True, transport='vertex', location='global', approved=False,
            provider_calls=0, proposed_max_usd='1.00' if book == 'doc-6' else '3.00')
        destination = run_dir / 'plan.json'
        destination.write_bytes((json.dumps(plan, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
        print(json.dumps({'plan': str(destination), 'book': book, 'pipeline_version': runtime.pipeline_version,
                          'provider_calls': 0, 'approved': False}, ensure_ascii=False, indent=2))
        return destination
    finally:
        runtime.close()
        engine.dispose()


def execute(plan_path, approval_path):
    """Only an explicit owner-approval file can reach this branch; no automatic grant."""
    from fastapi.testclient import TestClient
    from wayfinder.api.app import create_app
    from wayfinder.composition import WebServices, compose_account_service, compose_build_service, compose_course_services
    from wayfinder.fakes.mail import FakeMailer
    from wayfinder.fakes.local_media import LocalFakeMediaStore
    from wayfinder.infrastructure.build_spend import BuildSpendApproval
    from wayfinder.infrastructure.mail import ConsoleMailer
    from wayfinder.domain.file_paths import safe_path
    from wayfinder.worker import make_real_worker

    plan = json.loads(plan_path.read_text(encoding='utf-8'))
    permission = json.loads(approval_path.read_text(encoding='utf-8'))
    if permission.get('approved') is not True or permission.get('approved_by') != 'project-owner':
        raise ValueError('A new exact-run approval from the project owner is required')
    for field in ('file_sha256', 'pipeline_version', 'database'):
        if permission.get(field) != plan[field]:
            raise ValueError('Owner approval differs from the prepared ' + field)
    run_dir = safe_path(ROOT, plan['run_dir'])
    if (run_dir.parent != ROOT / 'tmp' or not re.fullmatch(r'w15-operator-(doc-6|candidate)-[0-9a-f]{12}', run_dir.name)
            or plan['database'] != 'wayfinder_w15_' + run_dir.name.rsplit('-', 1)[1]):
        raise ValueError('Use only a W-15 operator-prepared directory/database')
    output = run_dir / 'execution.json'
    if output.exists():
        raise ValueError('This attempt already has evidence; retain it and prepare a new attempt')
    source = safe_path(run_dir, 'source.pdf')
    if source.stat().st_nlink != 1 or sha256(source.read_bytes()).hexdigest() != plan['file_sha256']:
        raise ValueError('Prepared input bytes changed')
    settings, core = profile(run_dir, plan['database'])
    engine = create_database_engine(test_database_url(plan['database']))
    runtime = RealBuildRuntime(settings, engine, core_settings=core)
    if runtime.pipeline_version != plan['pipeline_version']:
        runtime.close()
        engine.dispose()
        raise ValueError('Code/config changed since dry-run; prepare again before approving')
    grant = BuildSpendApproval(**{key: permission[key] for key in
        ('reference', 'file_sha256', 'pipeline_version', 'max_usd')}, audit_log=safe_path(run_dir,
            'requests-' + sha256(permission['reference'].encode()).hexdigest()[:12] + '.jsonl'))
    media, account_mail = LocalFakeMediaStore(run_dir / 'media'), FakeMailer()
    service = compose_build_service(settings, engine, media=media, core_settings=core)
    accounts = compose_account_service(settings, engine, mailer=account_mail)
    courses, learning = compose_course_services(settings, engine, runtime.phase_b_store)
    app = create_app(settings, WebServices(health_check=lambda: 'ok', accounts=accounts, builds=service,
                                         courses=courses, learning=learning))

    class BuildMail(ConsoleMailer):
        subjects = []
        def send(self, to, subject, body, **kwargs):
            self.subjects.append(subject)
            print('Console Mailer: ' + subject, flush=True)
            super().send(to, subject, body, **kwargs)

    mailer = BuildMail()
    worker = worker_engine = None
    result = {'book': plan['book'], 'file_sha256': plan['file_sha256'], 'pipeline_version': plan['pipeline_version']}
    try:
        with TestClient(app) as client:
            registered = client.post('/api/v1/auth/register', headers={'Origin': 'http://testserver'}, json={
                'email': 'w15-' + uuid4().hex + '@example.vn', 'password': 'W15 isolated operator passphrase!', 'display_name': 'W-15'})
            registered.raise_for_status()
            me = client.get('/api/v1/me').json()
            headers = {'Origin': 'http://testserver', 'X-CSRF-Token': me['csrf_token']}
            if plan['book'] == 'doc-6':
                runtime.spend_approval = grant
                def record_bootstrap(receipt):
                    result['bootstrap'] = receipt.to_dict()
                    runtime.phase_b_store.put_record('w15_bootstrap_receipt', grant.reference, receipt.to_dict())
                    runtime.phase_b_store.append_usage(dict(purpose='build', doc_id=receipt.doc_id,
                        learner_id=me['account']['id'], operation='w15_doc6_cache_bootstrap', approval_reference=grant.reference,
                        cost_usd=receipt.spent_usd, input_tokens=receipt.input_tokens, output_tokens=receipt.output_tokens,
                        model_calls=receipt.model_calls, usage_complete=receipt.usage_complete, failed=receipt.status != 'succeeded'))
                bootstrap = runtime.runner(record_bootstrap).execute(source, 'u-' + plan['file_sha256'][:20])
                result['bootstrap'] = bootstrap.to_dict()
                if bootstrap.status != 'succeeded':
                    raise RuntimeError('Bootstrap stopped; retain its receipt and request a new decision')
            worker, worker_engine = make_real_worker(settings, media=media, mailer=mailer, core_settings=core,
                spend_approval=grant if plan['book'] == 'candidate' else None)
            upload = client.post('/api/v1/uploads', files={'file': ('source.pdf', source.read_bytes(), 'application/pdf')},
                                 data={'rights_confirmed': 'true'}, headers=headers)
            upload.raise_for_status()
            confirmed = client.post('/api/v1/uploads/' + upload.json()['upload_id'] + '/build', json={}, headers=headers)
            confirmed.raise_for_status()
            assert confirmed.json()['status'] == 'queued'
            if plan['book'] == 'doc-6':
                with ExitStack() as guards:
                    for name in ('doc2roadmap.infrastructure.llm.gemini.urlopen', 'doc2roadmap.infrastructure.embedding.gemini.urlopen',
                                 'doc2roadmap.infrastructure.llm.phase_b.urlopen',
                                 'doc2roadmap.infrastructure.google_auth.VertexCredentials.headers', 'google.auth.default'):
                        guards.enter_context(patch(name, side_effect=AssertionError('The web cache-only attempt forbids paid calls')))
                    job = worker.run_next_job()
            else:
                job = worker.run_next_job()
            view = client.get('/api/v1/builds/' + job['id'])
            view.raise_for_status()
            result.update(build=job, http_build=view.json(), mail_subjects=mailer.subjects)
            reader_engine = create_database_engine(test_database_url(plan['database']))
            try:
                with reader_engine.connect() as reader:
                    result['attempts'] = [dict(row) for row in reader.execute(text(
                        'SELECT result FROM build_attempt WHERE build_id=:id'), {'id': job['id']}).mappings()]
                    result['courses'] = [dict(row) for row in reader.execute(text(
                        'SELECT status,doc_id,published_graph_version FROM course WHERE build_id=:id'), {'id': job['id']}).mappings()]
            finally:
                reader_engine.dispose()
            assert job['status'] == 'succeeded' and result['courses'] and all(row['status'] == 'ready' for row in result['courses'])
            assert mailer.subjects == ['Bản dựng xong']
            if plan['book'] == 'doc-6':
                assert job['spent_usd'] == job['model_calls'] == 0
            print(json.dumps({'status': job['status'], 'spent_usd': str(job['spent_usd']), 'evidence': str(output)}, indent=2))
    finally:
        output.write_bytes((json.dumps(result, ensure_ascii=False, indent=2, default=str) + '\n').encode('utf-8'))
        if worker is not None:
            worker.build_runtime.close()
            worker_engine.dispose()
        runtime.close()
        engine.dispose()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--book', choices=['doc-6', 'candidate'])
    parser.add_argument('--plan', type=Path)
    parser.add_argument('--approval', type=Path)
    args = parser.parse_args()
    if args.approval:
        if not args.plan:
            parser.error('--approval requires --plan')
        execute(args.plan, args.approval)
    elif args.book:
        prepare(args.book)
    else:
        parser.error('Use --book for a free prepare, or --plan with an explicit --approval file')
