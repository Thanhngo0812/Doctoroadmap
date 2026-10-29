"""W-26 operator composition for the local demo server (real builds, real mail, media on disk).

Everything here is opt-in through the `demo-local` command. The shared server and worker keep
`allow_spend=False`; no HTTP endpoint or setting creates a spend grant. Owner instruction of
2026-10-29 relaxes W-15's "no setting creates a grant" for this one command only.
"""
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
import getpass
import re
import subprocess
import sys
from threading import Event
from uuid import uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import text
from sqlalchemy.engine import make_url

from doc2roadmap.application.phase_b.clock import SystemClock
from wayfinder.infrastructure.build_spend import (
    BuildSpendApproval, BuildSpendStopped, DEMO_EMBEDDING_PRICE_PROFILE)
from wayfinder.infrastructure.build_store import PostgresBuildStore
from wayfinder.infrastructure.database import create_database_engine, upgrade_database

DEMO_BOOK_MAX_USD = Decimal('3')
DEMO_DAILY_BUILD_MAX_USD = 10.0
DEMO_LEARNER_DAILY_MAX_USD = 3.0
DATABASE_NAME = re.compile(r'wayfinder_demo_[a-z0-9_]{1,40}')


def default_database_name(now=None):
    return 'wayfinder_demo_' + (now or datetime.now(ZoneInfo('Asia/Ho_Chi_Minh'))).strftime('%Y%m%d')


def demo_database_url(base_url, name):
    """The demo database must be a dedicated local one; never the shared `wayfinder` database."""
    if not DATABASE_NAME.fullmatch(name):
        raise ValueError('Demo database name must look like wayfinder_demo_<suffix>')
    if not base_url:
        raise ValueError('WAYFINDER_DATABASE_URL is required to find the local PostgreSQL server')
    url = make_url(base_url)
    if url.host not in {'127.0.0.1', 'localhost'}:
        raise ValueError('The demo server only uses a local PostgreSQL container')
    return url.set(drivername='postgresql+psycopg', database=name)


def demo_settings(base, *, database, artifact_root, host='127.0.0.1', port=8000):
    if not all((base.smtp_username, base.smtp_password, base.smtp_from)):
        raise ValueError('The demo server sends real mail: SMTP username, password and from address are required')
    origin = f'http://{host}:{port}'
    origins = [origin] + ([f'http://localhost:{port}'] if host == '127.0.0.1' else [])
    return base.model_copy(update=dict(
        database_url=demo_database_url(base.database_url, database).render_as_string(hide_password=False),
        test_database_url=None, env='dev', build_runner='real', mailer='smtp', cloudinary_url=None,
        artifact_root=artifact_root, public_base_url=origin, allowed_origins=origins,
        system_daily_build_max_usd=DEMO_DAILY_BUILD_MAX_USD, learner_daily_max_usd=DEMO_LEARNER_DAILY_MAX_USD))


def demo_media(root):
    from wayfinder.infrastructure.disk_media import DiskMediaStore
    return DiskMediaStore(root)


def ensure_database(settings):
    """Create the dedicated database when missing and migrate it; never touches another database."""
    url = make_url(settings.database_url)
    if not DATABASE_NAME.fullmatch(url.database or ''):
        raise ValueError('Refusing to prepare a database that is not a demo database')
    admin = create_database_engine(url.set(database='postgres')).execution_options(isolation_level='AUTOCOMMIT')
    try:
        with admin.connect() as connection:
            if not connection.scalar(text('SELECT 1 FROM pg_database WHERE datname=:name'), {'name': url.database}):
                connection.execute(text('CREATE DATABASE "' + url.database + '"'))
    finally:
        admin.dispose()
    upgrade_database(url)


class DemoSpendPolicy:
    """Grants one exact-file spend approval per build: min(book cap, what is left of today's cap)."""

    def __init__(self, *, book_max_usd=DEMO_BOOK_MAX_USD, daily_max_usd=DEMO_DAILY_BUILD_MAX_USD,
                 clock=None, audit_dir=None, retry_unknown_within_cap=True):
        self.book_max_usd, self.daily_max_usd = Decimal(str(book_max_usd)), Decimal(str(daily_max_usd))
        self.clock, self.audit_dir = clock or SystemClock(), audit_dir
        self.retry_unknown_within_cap = retry_unknown_within_cap

    @contextmanager
    def activate(self, path, doc_id, runtime):
        spent = PostgresBuildStore(runtime.phase_b_store.engine).spent_today(self.clock.now())
        limit = min(self.book_max_usd, self.daily_max_usd - spent)
        if limit <= 0:
            raise BuildSpendStopped('Daily build cap is exhausted; the build must wait for the next Vietnam day')
        reference = 'demo-' + uuid4().hex
        audit = None
        if self.audit_dir is not None:
            self.audit_dir.mkdir(parents=True, exist_ok=True)
            audit = self.audit_dir / (reference + '.jsonl')
        grant = BuildSpendApproval(
            reference=reference, file_sha256=sha256(path.read_bytes()).hexdigest(),
            pipeline_version=runtime.pipeline_version, max_usd=format(limit, 'f'), audit_log=audit,
            embedding_price_profile=DEMO_EMBEDDING_PRICE_PROFILE,
            retry_unknown_within_cap=self.retry_unknown_within_cap)
        with grant.activate(path, doc_id, runtime) as guard:
            yield guard


def waiting_reason(store, settings, now):
    """Why queued builds are not being claimed; None when nothing is waiting for the daily cap."""
    maximum = settings.system_daily_build_max_usd
    queued = store.one("SELECT count(*) AS n FROM build WHERE status='queued' AND NOT cancel_requested")['n']
    if queued and store.cap_reached(now, maximum):
        return (f'Đã chạm trần dựng {maximum:g} USD hôm nay (giờ Việt Nam); {queued} bản dựng xếp hàng '
                'và sẽ chạy sau 00:00 ngày kế tiếp.')
    return None


def demo_worker_step(worker, log=print, last_reason=None):
    job = worker.run_next_job()
    reason = None
    if job is None:
        reason = waiting_reason(worker.store, worker.settings, worker.clock.now())
        if reason and reason != last_reason:
            log(reason)
    return job, reason


def run_demo_worker(worker, *, log=print, stop=None):
    stop, reason = stop or Event(), None
    while not stop.is_set():
        job, reason = demo_worker_step(worker, log, reason)
        if job is None:
            stop.wait(3)
    return 0


def make_demo_worker(settings, media, *, audit_dir=None, **options):
    # `options` only lets tests inject a fake pipeline and graph loader.
    from wayfinder.composition import compose_mailer
    from wayfinder.worker import make_real_worker
    return make_real_worker(settings, media=media, mailer=compose_mailer(settings),
                            spend_approval=DemoSpendPolicy(audit_dir=audit_dir), **options)


def ensure_admin(settings, engine, email, *, password=lambda: getpass.getpass('Mật khẩu quản trị demo: ')):
    from wayfinder.composition import compose_account_service
    from wayfinder.infrastructure.auth_store import PostgresAuthStore
    from wayfinder.infrastructure.mail import ConsoleMailer
    if PostgresAuthStore(engine).has_admins():
        return False
    compose_account_service(settings, engine, mailer=ConsoleMailer()).create_admin(email, password())
    return True


def seed_samples(settings, engine, admin_email, media, *, source_root=None, graph_loader=None, doc_ids=None):
    """Six development books from disk; same use case as `seed-samples`, no Cloudinary."""
    from wayfinder.api.errors import WebError
    from wayfinder.application.seed_samples import SampleSeeder
    from wayfinder.composition import compose_course_services
    from wayfinder.domain.auth import Actor
    from wayfinder.infrastructure.auth_store import PostgresAuthStore
    from wayfinder.infrastructure.phase_b_store import PostgresPhaseBStore

    credentials = PostgresAuthStore(engine).get_credentials(admin_email.strip().lower())
    if credentials is None or credentials.account.role != 'admin' or credentials.account.status != 'active':
        raise WebError('forbidden', 'Cần tài khoản quản trị đang hoạt động')
    account = credentials.account
    actor = Actor(account.id, account.role, account.email_verified_at is not None, account.status)
    store = PostgresPhaseBStore(engine, lock_pool_size=settings.phase_b_lock_pool_size)
    try:
        courses, gateway = compose_course_services(settings, engine, store, graph_loader=graph_loader, media=media)
        seeder = SampleSeeder(courses, gateway, media, source_root=source_root or settings.artifact_root.parent,
                              folder=settings.cloudinary_folder + '/samples')
        return seeder.execute(actor, doc_ids)
    finally:
        store.close()


def install_download_route(app, media, clock=None):
    """Signed, short-lived source-file links; the token is the only capability."""
    from fastapi import HTTPException
    from fastapi.responses import FileResponse
    from fastapi.routing import APIRoute
    from wayfinder.infrastructure.disk_media import DOWNLOAD_ROUTE
    clock = clock or SystemClock()

    def download(token: str):
        path = media.resolve_download(token, clock.now())
        if path is None:
            raise HTTPException(status_code=404, detail='not found')
        return FileResponse(path, filename='tai-lieu' + path.suffix, headers={'cache-control': 'no-store'})

    # The SPA fallback is a catch-all registered earlier; this route must match first.
    app.router.routes.insert(0, APIRoute(DOWNLOAD_ROUTE + '{token}', download, include_in_schema=False))


def run_demo_local(args, settings, env_file=None):
    """Entry point of `wayfinder.cli demo-local`; returns a process exit code."""
    from pathlib import Path
    artifact_root = Path(args.artifact_root).resolve()
    demo = demo_settings(settings, database=args.database, artifact_root=artifact_root, host=args.host, port=args.port)
    media_root = artifact_root / 'demo-local' / args.database / 'media'
    media = demo_media(media_root)
    if args.role == 'worker':
        worker, engine = make_demo_worker(demo, media, audit_dir=media_root.parent / 'spend-audit')
        print(f'Worker dựng sách: {args.database}, trần {DEMO_BOOK_MAX_USD}/cuốn, {DEMO_DAILY_BUILD_MAX_USD:g} USD/ngày.', flush=True)
        try:
            return run_demo_worker(worker)
        except KeyboardInterrupt:
            return 0
        finally:
            worker.build_runtime.close()
            engine.dispose()
    if not demo.frontend_dist.is_dir():
        print('Chưa có bản build React: chạy npm.cmd --prefix src/web/frontend run build trước.', file=sys.stderr)
        return 2
    if not args.admin_email:
        print('Cần --admin-email để tạo admin đầu tiên và nạp khoá mẫu.', file=sys.stderr)
        return 2
    ensure_database(demo)
    engine = create_database_engine(demo.database_url)
    try:
        if ensure_admin(demo, engine, args.admin_email):
            print('Đã tạo admin đầu tiên.', flush=True)
        for course in seed_samples(demo, engine, args.admin_email, media):
            print(f'Khoá mẫu {course.doc_id}: {course.id}', flush=True)
    finally:
        engine.dispose()
    child = None
    if args.role == 'all':
        # The spend hook patches urlopen process-wide: keep it away from the server's learner traffic.
        command = [sys.executable, '-m', 'wayfinder.cli'] + (['--env-file', str(env_file)] if env_file else []) + [
            'demo-local', '--role', 'worker', '--database', args.database, '--artifact-root', str(artifact_root),
            '--host', args.host, '--port', str(args.port)]
        child = subprocess.Popen(command)
    try:
        import uvicorn
        from wayfinder.api import create_app
        from wayfinder.composition import compose_services
        from wayfinder.infrastructure.database import DatabaseHealth
        health = DatabaseHealth(demo.database_url)
        services = compose_services(demo, health_check=health, close=health.close, build_media=media)
        app = create_app(demo, services)
        install_download_route(app, media)
        print(f'Máy chủ demo: {demo.public_base_url}', flush=True)
        uvicorn.run(app, host=args.host, port=args.port)
        return 0
    finally:
        if child is not None:
            child.terminate()
            child.wait(timeout=30)
