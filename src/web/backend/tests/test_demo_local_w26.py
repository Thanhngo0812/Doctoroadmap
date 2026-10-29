"""W-26: the local demo server. PostgreSQL db-test only; model, SMTP and media are all in-process fakes."""
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from io import BytesIO
import json
from types import SimpleNamespace
from urllib.request import Request
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from test_builds_w14 import builds, pdf, sql
from test_real_build_w15 import core
from wayfinder import demo_local
from wayfinder.api.app import create_app
from wayfinder.application.build_worker import BuildWorker
from wayfinder.composition import WebServices, compose_build_service, compose_course_services, compose_mailer
from wayfinder.demo_local import DemoSpendPolicy, demo_database_url, demo_settings, ensure_database, make_demo_worker
from wayfinder.fakes.mail import FakeMailer
from wayfinder.infrastructure import build_spend
from wayfinder.infrastructure.database import create_database_engine
from wayfinder.infrastructure.disk_media import DiskMediaStore
from wayfinder.infrastructure.phase_b_store import PostgresPhaseBStore
from wayfinder.infrastructure.real_build import RealBuildRuntime
from wayfinder.settings import WebSettings
from wayfinder.testing import FakeClock, _sample_graph

pytestmark = pytest.mark.postgres

PRICE_PER_CALL = Decimal('.25')


class Provider:
    """Stands in for Vertex: every request reports 1M prompt tokens, i.e. USD .25."""
    def __init__(self):
        self.calls = 0

    def __call__(self, request, *args, **kwargs):
        self.calls += 1
        value = {'candidates': [{'content': {'parts': [{'text': '{}'}]}}],
                 'usageMetadata': {'promptTokenCount': 1_000_000, 'candidatesTokenCount': 0}}
        return BytesIO(json.dumps(value).encode())


def spending_pipeline(calls):
    class SpendingPipeline:
        allow_flags = []

        def __init__(self, settings, *, allow_spend, phase_b_store):
            type(self).allow_flags.append(allow_spend)
            self.allow_spend, self.store = allow_spend, phase_b_store
            self.values = dict(spent_usd=0., model_calls=0, input_tokens=0, output_tokens=0,
                               usage_complete=True, missing_usage_calls=0)

        def read(self, path, doc):
            self.doc = doc
            return {'page_texts': ['Đây là nội dung giáo trình tiếng Việt có đầy đủ ví dụ. ' * 20]}

        def label_roles(self, doc):
            from doc2roadmap.infrastructure.llm import gemini
            if self.allow_spend:
                for _ in range(calls):
                    request = Request('https://aiplatform.googleapis.com/v1/projects/p/locations/global/publishers/google/'
                                      'models/gemini-3.1-flash-lite:generateContent',
                                      data=json.dumps({'contents': [{'parts': [{'text': 'x'}]}],
                                                       'generationConfig': {'maxOutputTokens': 100}}).encode())
                    with gemini.urlopen(request) as response:  # the approval hook, or the real urlopen
                        tokens = json.loads(response.read())['usageMetadata']['promptTokenCount']
                    self.values['spent_usd'] += tokens * .25 / 1e6
                    self.values['model_calls'] += 1
                    self.values['input_tokens'] += tokens
                    # The core wraps the store this way: a raw trace that must not be billed twice.
                    self.store.append_usage(dict(purpose='extraction', doc_id=doc, counted_in='build',
                        cost_usd=tokens * .25 / 1e6, input_tokens=tokens, output_tokens=0))
            return {}

        def a3(self, doc):
            return {}

        def canonical(self, doc, language):
            return {}

        def roadmap(self, doc):
            return {'graph_version': 8}

        def learning_prep(self, path, doc, graph_version):
            return {}

        def usage(self):
            return dict(self.values)
    return SpendingPipeline


def loader(doc, version):
    graph = _sample_graph()
    graph.doc_id, graph.graph_version = doc, 8 if version is None else version  # None: the sample's latest
    return graph


def config(b, **kwargs):
    base = WebSettings(_env_file=None, database_url=b.postgres_database_url.render_as_string(hide_password=False),
        smtp_username='demo-user', smtp_password='demo-pass', smtp_from='demo@example.vn',
        artifact_root=b.settings.artifact_root, frontend_dist=b.settings.frontend_dist,
        allowed_origins=['http://testserver'])
    demo = demo_settings(base, database='wayfinder_demo_unit', artifact_root=b.settings.artifact_root, **kwargs)
    return demo.model_copy(update={'database_url': base.database_url})  # points at the disposable test database


@pytest.fixture(autouse=True)
def isolated(builds):
    with builds.engine.begin() as connection:
        connection.execute(text('TRUNCATE phase_b_cache,phase_b_record,phase_b_negative'))


@pytest.fixture
def provider(monkeypatch):
    fake = Provider()
    monkeypatch.setattr(build_spend, 'urlopen', fake)
    return fake


class FakeSMTP:
    sent = []

    def __init__(self, host, port, timeout=None):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def ehlo(self):
        pass

    def starttls(self, context=None):
        pass

    def login(self, user, password):
        pass

    def send_message(self, message):
        type(self).sent.append(message)


@pytest.fixture(autouse=True)
def smtp(builds, monkeypatch):
    FakeSMTP.sent = []
    monkeypatch.setattr('smtplib.SMTP', FakeSMTP)
    return FakeSMTP


def demo_worker(b, calls, tmp_path, **options):
    cfg = config(b)
    media = DiskMediaStore(tmp_path / 'media')
    worker, engine = make_demo_worker(cfg, media, core_settings=core(b), pipeline_factory=spending_pipeline(calls),
                                      graph_loader=loader, **options)
    return worker, engine, cfg


def queue(worker, actor, pages):
    item = worker.service.create_upload(actor, 'book.pdf', pdf(pages), rights_confirmed=True)
    worker.service.confirm_build(actor, item['upload_id'])
    return item['build']['build_id']


def finish(worker, engine):
    close = getattr(worker.mailer, 'close', None)
    if close:
        close()
    worker.build_runtime.close()
    engine.dispose()


def clocked_worker(b, calls, clock, mailer=None):
    """Same policy class as the demo command, but with a controllable clock for day-boundary tests."""
    cfg = config(b)
    runtime = RealBuildRuntime(cfg, b.engine, core_settings=core(b), pipeline_factory=spending_pipeline(calls),
                               spend_approval=DemoSpendPolicy(clock=clock))
    service = compose_build_service(cfg, b.engine, media=DiskMediaStore(b.tmp_path / 'media'), clock=clock,
                                    core_settings=core(b))
    worker = BuildWorker(service, runner_factory=runtime.runner, graph_loader=loader,
                         mailer=mailer or FakeMailer(), worker_id='w26-' + uuid4().hex)
    worker.build_runtime = runtime
    return worker


def build_rows(b):
    return {str(row['id']): row for row in sql(b, 'SELECT id,status,requested_by,spent_usd,error_code FROM build')}


# --- Database isolation -----------------------------------------------------------------------

@pytest.mark.parametrize('name', ['wayfinder', 'wayfinder_test', 'postgres', 'wayfinder_demo_', 'Wayfinder_demo_x',
                                  'wayfinder_demo_x"; DROP DATABASE wayfinder; --', 'wayfinder_demo_' + 'a' * 41])
def test_demo_never_targets_a_database_that_is_not_dedicated(name):
    with pytest.raises(ValueError):
        demo_database_url('postgresql+psycopg://u:p@127.0.0.1:5432/wayfinder', name)


def test_demo_only_uses_a_local_postgres_and_a_dedicated_name():
    url = demo_database_url('postgresql+psycopg://u:p@127.0.0.1:5432/wayfinder', 'wayfinder_demo_20261029')
    assert url.database == 'wayfinder_demo_20261029' and url.host == '127.0.0.1'
    with pytest.raises(ValueError, match='local'):
        demo_database_url('postgresql+psycopg://u:p@db.example.com:5432/wayfinder', 'wayfinder_demo_20261029')


def test_ensure_database_refuses_the_shared_database_before_any_connection(builds, monkeypatch):
    cfg = config(builds)
    shared = cfg.model_copy(update={'database_url': cfg.database_url.rsplit('/', 1)[0] + '/wayfinder'})
    def forbidden(*args, **kwargs):
        raise AssertionError('The shared database must be refused before any connection is opened')
    monkeypatch.setattr(demo_local, 'create_database_engine', forbidden)
    monkeypatch.setattr(demo_local, 'upgrade_database', forbidden)
    with pytest.raises(ValueError, match='not a demo database'):
        ensure_database(shared)


@contextmanager
def disposable_demo_database(b):
    """A real `wayfinder_demo_*` database made by ensure_database, dropped afterwards (admins cannot be demoted)."""
    name = 'wayfinder_demo_t' + uuid4().hex[:12]
    cfg = config(b).model_copy(update={'database_url': demo_database_url(
        b.postgres_database_url.render_as_string(hide_password=False), name).render_as_string(hide_password=False)})
    admin = create_database_engine(b.postgres_database_url.set(database='postgres')).execution_options(isolation_level='AUTOCOMMIT')
    try:
        yield cfg, name
    finally:
        with admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
        admin.dispose()


def test_ensure_database_creates_a_migrated_database_and_first_admin_once(builds, monkeypatch):
    with disposable_demo_database(builds) as (cfg, name):
        ensure_database(cfg)
        ensure_database(cfg)  # idempotent
        engine = create_database_engine(cfg.database_url)
        try:
            assert engine.url.database == name
            with engine.connect() as connection:
                assert connection.scalar(text("SELECT count(*) FROM information_schema.tables WHERE table_name='build'")) == 1
            assert demo_local.ensure_admin(cfg, engine, 'quan-tri@example.vn', password=lambda: 'W26 demo admin passphrase!')
            assert not demo_local.ensure_admin(cfg, engine, 'khac@example.vn', password=lambda: 'unused')
            with engine.connect() as connection:
                rows = connection.execute(text('SELECT role,email FROM account')).all()
            assert [tuple(row) for row in rows] == [('admin', 'quan-tri@example.vn')]
            from wayfinder.infrastructure.auth_store import PostgresAuthStore
            assert PostgresAuthStore(engine).first_admin_id() is not None
        finally:
            engine.dispose()


# --- Media on disk, no Cloudinary -------------------------------------------------------------

def test_demo_media_is_the_disk_store_and_never_cloudinary(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('Cloudinary must not be created by the demo server')
    monkeypatch.setattr('wayfinder.infrastructure.media.CloudinaryMediaStore', forbidden)
    store = demo_local.demo_media(tmp_path / 'media')
    assert type(store) is DiskMediaStore and store.root == tmp_path / 'media'


def test_page_and_formula_images_are_real_images_served_through_the_learning_media_port(builds, tmp_path):
    from PIL import Image
    b, cfg = builds, config(builds)
    media = DiskMediaStore(tmp_path / 'media')
    source = tmp_path / 'book.pdf'
    source.write_bytes(pdf(3))
    public = media.upload(source, 'wayfinder/dev/uploads', 'image')
    cfg.artifact_root.joinpath('phase_b/formula_images/u-x/parse-v1').mkdir(parents=True)
    Image.new('RGB', (30, 10), (200, 10, 10)).save(cfg.artifact_root / 'phase_b/formula_images/u-x/parse-v1/f1.png')
    courses, gateway = compose_course_services(cfg, b.engine, PostgresPhaseBStore(b.engine), media=media)
    course = SimpleNamespace(id=str(uuid4()), doc_id='u-x', source_public_id=public)
    graph = SimpleNamespace(doc_id='u-x', parse_version=1, formula_images={'o1': {'image_ref': 'f1.png'}},
                            learnable_nodes=[], tree=SimpleNamespace(parse_stats={'page_count': 3}))
    image, count = gateway.media.open_source_page(course, graph, 2)
    assert count == 3 and image[:4] == b'RIFF' and image[8:12] == b'WEBP'
    page = Image.open(BytesIO(image))
    assert page.format == 'WEBP' and abs(page.width - cfg.page_image_width) <= 1 and page.height == page.width  # square 72 x 72 pt page
    formula = Image.open(BytesIO(gateway.media.get_media(course, graph, 'parse-v1/f1.png')))
    assert formula.format == 'WEBP' and formula.size == (30, 10)
    assert sql(b, "SELECT count(*) AS n FROM media_asset WHERE doc_id='u-x'")[0]['n'] == 1


def test_disk_store_rejects_paths_outside_its_root(tmp_path):
    media = DiskMediaStore(tmp_path / 'media')
    for hostile in ('../escape.pdf', '/etc/passwd', 'a\\b.pdf'):
        with pytest.raises(ValueError):
            media.delete(hostile)
    docx = tmp_path / 'x.pdf'
    docx.write_bytes(b'x')
    with pytest.raises(ValueError):
        media.upload(docx, 'f', 'raw')  # raw is DOCX only, like Cloudinary


def test_source_download_is_a_short_signed_server_link_not_a_file_path(builds, tmp_path):
    b = builds
    dist = tmp_path / 'dist'
    dist.mkdir()
    (dist / 'index.html').write_text('<html>spa</html>', encoding='utf-8')
    media, clock = DiskMediaStore(tmp_path / 'media'), FakeClock(datetime.now(timezone.utc))
    source = tmp_path / 'book.pdf'
    source.write_bytes(pdf(1))
    public = media.upload(source, 'wayfinder/dev/uploads', 'image')
    cfg = config(b).model_copy(update={'frontend_dist': dist})
    app = create_app(cfg, WebServices(health_check=lambda: 'ok'))
    demo_local.install_download_route(app, media, clock)
    client = TestClient(app)
    url = media.temporary_download_url(public, clock.now() + timedelta(seconds=300))
    assert url.startswith('/api/v1/demo-files/') and str(tmp_path) not in url and public not in url
    ok = client.get(url)
    assert ok.status_code == 200 and ok.content == source.read_bytes() and 'attachment' in ok.headers['content-disposition']
    assert client.get(url[:-4] + 'AAAA').status_code == 404          # tampered token
    assert client.get('/api/v1/demo-files/not-a-token').status_code == 404
    clock.advance(301)
    assert client.get(url).status_code == 404                         # expired
    assert client.get('/some/spa/page').text == '<html>spa</html>'    # the SPA fallback still works


# --- Dựng thật cho mọi tài khoản, trần cuốn và trần ngày --------------------------------------------

def test_two_accounts_both_get_a_grant_and_spend(builds, provider, tmp_path):
    b = builds
    actor_two, _, _ = b.user()
    worker, engine, cfg = demo_worker(b, 2, tmp_path)
    try:
        first, second = queue(worker, b.actor, 1), queue(worker, actor_two, 2)
        assert worker.run_next_job()['status'] == 'succeeded' and worker.run_next_job()['status'] == 'succeeded'
        rows = build_rows(b)
        assert {str(rows[first]['requested_by']), str(rows[second]['requested_by'])} == {b.actor.user_id, actor_two.user_id}
        assert [float(rows[key]['spent_usd']) for key in (first, second)] == [.5, .5] and provider.calls == 4
        grants = [row['value'] for row in sql(b, "SELECT value FROM phase_b_record WHERE kind='w15_build_approval'")]
        assert len(grants) == 2 and {g['state'] for g in grants} == {'finished'} and {Decimal(g['max_usd']) for g in grants} == {3}
        assert len({g['file_sha256'] for g in grants}) == 2 and all(g['budget']['http_calls'] == 2 for g in grants)
    finally:
        finish(worker, engine)


def test_without_the_demo_command_no_build_may_spend(builds, provider, tmp_path):
    from wayfinder.worker import make_real_worker
    b = builds
    pipeline = spending_pipeline(2)
    cfg = config(b)
    worker, engine = make_real_worker(cfg, media=DiskMediaStore(tmp_path / 'media'), core_settings=core(b),
                                      pipeline_factory=pipeline, graph_loader=loader)
    try:
        assert worker.build_runtime.spend_approval is None
        actor_two, _, _ = b.user()
        queue(worker, b.actor, 1)
        queue(worker, actor_two, 2)
        assert worker.run_next_job()['status'] == 'succeeded' and worker.run_next_job()['status'] == 'succeeded'
        assert pipeline.allow_flags == [False, False] and provider.calls == 0
        assert sql(b, "SELECT count(*) AS n FROM phase_b_record WHERE kind='w15_build_approval'")[0]['n'] == 0
        assert sql(b, "SELECT coalesce(sum(cost_usd),0) AS total FROM usage_ledger")[0]['total'] == 0
    finally:
        finish(worker, engine)


def test_the_shared_worker_command_does_not_pass_a_grant(builds, monkeypatch):
    from wayfinder import worker as worker_module
    seen = {}
    def capture(settings, **kwargs):
        seen.update(kwargs)
        raise ValueError('stop')
    monkeypatch.setattr(worker_module, 'make_real_worker', capture)
    with pytest.raises(ValueError):
        worker_module.make_worker(config(builds))
    assert seen.get('spend_approval') is None


def test_book_cap_stops_a_build_that_would_exceed_three_usd(builds, provider, tmp_path):
    b = builds
    worker, engine, cfg = demo_worker(b, 20, tmp_path)  # would spend USD 5 if nothing stopped it
    try:
        build = queue(worker, b.actor, 1)
        assert worker.run_next_job()['status'] == 'failed'
        # 11 requests fit under USD 3 with the 0.36 reservation; the 12th is refused before the provider.
        assert provider.calls == 11
        assert build_rows(b)[build]['spent_usd'] == Decimal('2.75') and Decimal('2.75') <= Decimal('3')
        grant = sql(b, "SELECT value FROM phase_b_record WHERE kind='w15_build_approval'")[0]['value']
        assert Decimal(grant['max_usd']) == 3 and grant['budget']['stopped'] is True
    finally:
        finish(worker, engine)


def test_daily_cap_leaves_only_the_remainder_to_the_next_build(builds, provider, tmp_path):
    b = builds
    store = PostgresPhaseBStore(b.engine)
    store.append_usage(dict(purpose='build', doc_id='earlier', cost_usd=9.0, created_at=datetime.now(timezone.utc).isoformat()))
    store.close()
    worker, engine, cfg = demo_worker(b, 20, tmp_path)
    try:
        build = queue(worker, b.actor, 1)
        assert worker.run_next_job()['status'] == 'failed'
        assert provider.calls == 3  # USD 1 left: three requests (0.75 + 0.36 reserve) fit, the fourth does not
        grant = sql(b, "SELECT value FROM phase_b_record WHERE kind='w15_build_approval'")[0]['value']
        assert Decimal(grant['max_usd']) == 1
        total = sql(b, "SELECT sum(cost_usd) AS total FROM usage_ledger WHERE purpose='build'")[0]['total']
        assert total == Decimal('9.75') and total <= Decimal('10')
    finally:
        finish(worker, engine)


def test_a_full_day_queues_builds_until_vietnam_midnight(builds, provider, tmp_path):
    b = builds
    clock = FakeClock(datetime(2026, 1, 1, 16, 30, tzinfo=timezone.utc))  # 23:30 on 1 Jan in Vietnam
    PostgresPhaseBStore(b.engine).append_usage(dict(purpose='build', doc_id='earlier', cost_usd=10.0,
                                                    created_at=clock.now().isoformat()))
    worker = clocked_worker(b, 2, clock)
    try:
        build = queue(worker, b.actor, 1)
        clock.advance(15 * 60)  # 23:45 Vietnam time, 16:45 UTC
        assert worker.run_next_job() is None and build_rows(b)[build]['status'] == 'queued'
        reason = demo_local.waiting_reason(worker.store, worker.settings, clock.now())
        assert '10 USD' in reason and '1 bản dựng' in reason and '00:00' in reason
        clock.advance(20 * 60)  # 00:05 on 2 Jan in Vietnam but still 1 Jan in UTC
        assert clock.now().date().isoformat() == '2026-01-01'
        assert worker.run_next_job()['status'] == 'succeeded' and provider.calls == 2
        assert demo_local.waiting_reason(worker.store, worker.settings, clock.now()) is None
    finally:
        worker.build_runtime.close()


def test_demo_defaults_are_the_ones_the_owner_asked_for(builds):
    cfg = config(builds)
    assert cfg.system_daily_build_max_usd == 10 and cfg.learner_daily_max_usd == 3
    assert DemoSpendPolicy().book_max_usd == Decimal('3') and DemoSpendPolicy().daily_max_usd == Decimal('10')
    assert WebSettings(_env_file=None).system_daily_build_max_usd is None and WebSettings(_env_file=None).learner_daily_max_usd == 1


# --- Receipt ----------------------------------------------------------------------------------

def test_build_receipt_is_added_to_the_ledger_exactly_once(builds, provider, tmp_path):
    b = builds
    worker, engine, cfg = demo_worker(b, 2, tmp_path)
    try:
        build = queue(worker, b.actor, 1)
        assert worker.run_next_job()['status'] == 'succeeded'
        assert build_rows(b)[build]['spent_usd'] == Decimal('.5')
        # Independent SQL: two raw traces (cost zeroed in their column) and the build receipt rows.
        assert sql(b, "SELECT count(*) AS n FROM usage_ledger WHERE extra->>'counted_in'='build'")[0]['n'] == 2
        assert sql(b, "SELECT coalesce(sum(cost_usd),0) AS total FROM usage_ledger WHERE extra->>'counted_in'='build'")[0]['total'] == 0
        assert sql(b, "SELECT sum(cost_usd) AS total FROM usage_ledger WHERE purpose='build'")[0]['total'] == Decimal('.5')
        assert sql(b, "SELECT sum(cost_usd) AS total FROM usage_ledger")[0]['total'] == Decimal('.5')
        from wayfinder.infrastructure.build_store import PostgresBuildStore
        assert PostgresBuildStore(b.engine).spent_today(datetime.now(timezone.utc)) == Decimal('.5')
    finally:
        finish(worker, engine)


# --- Trần người học ---------------------------------------------------------------------------

def usage_ratio(b, cfg):
    store = PostgresPhaseBStore(b.engine)
    courses, gateway = compose_course_services(cfg, b.engine, store)
    app = create_app(cfg, WebServices(health_check=lambda: 'ok', accounts=b.accounts, builds=b.service, courses=courses,
                                      learning=gateway))
    client = TestClient(app)
    client.cookies.update(b.client.cookies)
    response = client.get('/api/v1/me/usage')
    assert response.status_code == 200, response.text
    return response.json()['learner_today']


def test_learner_cap_is_three_usd_on_the_demo_server_and_one_elsewhere(builds):
    b = builds
    store = PostgresPhaseBStore(b.engine)
    store.append_usage(dict(purpose='assistant', doc_id='d', learner_id=b.actor.user_id, cost_usd=1.5))
    store.close()
    normal = WebSettings(_env_file=None, artifact_root=b.settings.artifact_root, allowed_origins=['http://testserver'],
                         frontend_dist=b.settings.frontend_dist)
    elsewhere = usage_ratio(b, normal)
    assert elsewhere['used_ratio'] == pytest.approx(1.0) and elsewhere['limited'] is True
    demo = usage_ratio(b, config(b))
    assert demo['used_ratio'] == pytest.approx(.5) and demo['limited'] is False


# --- Mail thật (SMTP) --------------------------------------------------------------------------

def test_demo_mailer_is_smtp_and_account_mail_reaches_the_smtp_server(builds, smtp):
    from wayfinder.infrastructure.mail_dispatch import BackgroundMailer
    b, cfg = builds, config(builds)
    mailer = compose_mailer(cfg)
    assert isinstance(mailer, BackgroundMailer) and mailer.mailer.host == 'smtp.gmail.com'
    from wayfinder.composition import compose_account_service
    accounts = compose_account_service(cfg, b.engine)
    client = TestClient(create_app(cfg, WebServices(health_check=lambda: 'ok', accounts=accounts)))
    email = uuid4().hex + '@example.vn'
    response = client.post('/api/v1/auth/register', headers={'Origin': cfg.public_base_url},
        json={'email': email, 'password': 'W26 safe test passphrase!', 'display_name': 'Người xem demo'})
    assert response.status_code == 200, response.text
    accounts.mailer.close()
    assert [message['To'] for message in smtp.sent] == [email] and cfg.public_base_url in smtp.sent[0].get_body().get_content()


def test_demo_needs_smtp_credentials(builds):
    base = WebSettings(_env_file=None, database_url=builds.postgres_database_url.render_as_string(hide_password=False))
    with pytest.raises(ValueError, match='SMTP'):
        demo_settings(base, database='wayfinder_demo_unit', artifact_root=builds.settings.artifact_root)


def test_build_finished_notice_goes_through_smtp_in_the_demo_worker(builds, provider, smtp, tmp_path):
    b = builds
    worker, engine, cfg = demo_worker(b, 1, tmp_path)
    try:
        queue(worker, b.actor, 1)
        assert worker.run_next_job()['status'] == 'succeeded'
        worker.mailer.close()
        owner = sql(b, 'SELECT email FROM account WHERE id=:id', {'id': b.actor.user_id})[0]['email']
        assert [(m['To'], m['Subject']) for m in smtp.sent] == [(owner, 'Bản dựng xong')]
    finally:
        finish(worker, engine)


# --- Sáu khoá mẫu --------------------------------------------------------------------------------

def test_six_sample_courses_load_from_disk_without_network(builds, tmp_path, monkeypatch):
    import socket
    from wayfinder.application.seed_samples import SAMPLE_DOCS
    def no_network(*args, **kwargs):
        raise AssertionError('Sample seeding must not open a network connection')
    sources = tmp_path / 'sources'
    sources.mkdir()
    payload = pdf(1)
    for doc in SAMPLE_DOCS.values():
        (sources / doc['pdf']).write_bytes(payload)
    with disposable_demo_database(builds) as (cfg, name):
        ensure_database(cfg)
        engine = create_database_engine(cfg.database_url)
        try:
            demo_local.ensure_admin(cfg, engine, 'quan-tri@example.vn', password=lambda: 'W26 demo admin passphrase!')
            media = DiskMediaStore(tmp_path / 'media')
            monkeypatch.setattr(socket.socket, 'connect', no_network)
            rows = demo_local.seed_samples(cfg, engine, 'quan-tri@example.vn', media, source_root=sources, graph_loader=loader)
            assert sorted(course.doc_id for course in rows) == sorted(SAMPLE_DOCS)
            with engine.connect() as connection:
                stored = connection.execute(text('SELECT doc_id,source_public_id FROM course WHERE is_sample')).mappings().all()
            assert len(stored) == 6
            for row in stored:
                assert (media.root / row['source_public_id']).read_bytes() == payload
            assert len(demo_local.seed_samples(cfg, engine, 'quan-tri@example.vn', media, source_root=sources,
                                               graph_loader=loader)) == 6
            with engine.connect() as connection:
                assert connection.scalar(text('SELECT count(*) FROM course WHERE is_sample')) == 6  # idempotent
        finally:
            engine.dispose()


# --- Lệnh: worker là tiến trình riêng, mặc định tắt chi ngoài lệnh demo --------------------------------

def test_demo_worker_composition_uses_policy_smtp_and_disk_media(builds, tmp_path):
    from wayfinder.infrastructure.mail_dispatch import BackgroundMailer
    worker, engine, cfg = demo_worker(builds, 1, tmp_path)
    try:
        assert isinstance(worker.build_runtime.spend_approval, DemoSpendPolicy)
        assert isinstance(worker.mailer, BackgroundMailer) and type(worker.service.media) is DiskMediaStore
    finally:
        finish(worker, engine)


def run_args(role, artifact_root):
    return SimpleNamespace(database='wayfinder_demo_unit', artifact_root=artifact_root, admin_email='a@example.vn',
                           role=role, host='127.0.0.1', port=8000)


def test_role_all_runs_the_builder_as_a_separate_process_and_stops_it(builds, tmp_path, monkeypatch):
    import uvicorn
    started, events = [], []
    class FakeProcess:
        def __init__(self, command):
            started.append(command)
        def terminate(self):
            events.append('terminate')
        def wait(self, timeout=None):
            events.append('wait')
    cfg = config(builds)
    dist = tmp_path / 'dist'
    dist.mkdir()
    base = cfg.model_copy(update={'frontend_dist': dist, 'artifact_root': tmp_path / 'artifacts', 'database_url':
                                  cfg.database_url.rsplit('/', 1)[0] + '/wayfinder'})
    captured = {}
    monkeypatch.setattr(demo_local.subprocess, 'Popen', FakeProcess)
    monkeypatch.setattr(demo_local, 'ensure_database', lambda settings: captured.setdefault('database', settings.database_url))
    monkeypatch.setattr(demo_local, 'ensure_admin', lambda *a, **k: False)
    monkeypatch.setattr(demo_local, 'seed_samples', lambda *a, **k: [])
    monkeypatch.setattr('wayfinder.composition.compose_services',
                        lambda settings, **kwargs: captured.update(kwargs) or WebServices(health_check=lambda: 'ok'))
    monkeypatch.setattr(uvicorn, 'run', lambda app, host, port: captured.update(app=app, host=host, port=port))
    assert demo_local.run_demo_local(run_args('all', tmp_path / 'artifacts'), base, env_file=tmp_path / '.env') == 0
    # The shared database in the environment is replaced, never used.
    assert captured['database'].endswith('/wayfinder_demo_unit') and not captured['database'].endswith('/wayfinder')
    assert type(captured['build_media']) is DiskMediaStore and captured['build_media'].root.is_relative_to((tmp_path / 'artifacts').resolve())
    assert captured['app'].router.routes[0].path.startswith('/api/v1/demo-files/')
    command = started[0]
    assert command[1:3] == ['-m', 'wayfinder.cli'] and command[command.index('--role') + 1] == 'worker'
    assert '--env-file' in command and events == ['terminate', 'wait']


SMTP_ENV = {'WAYFINDER_SMTP_USERNAME': 'u', 'WAYFINDER_SMTP_PASSWORD': 'p', 'WAYFINDER_SMTP_FROM': 'a@example.vn'}


def test_cli_demo_local_refuses_to_start_without_smtp(monkeypatch, capsys):
    from wayfinder import cli
    monkeypatch.setenv('WAYFINDER_DATABASE_URL', 'postgresql+psycopg://u:p@127.0.0.1:5432/wayfinder')
    for key in SMTP_ENV:
        monkeypatch.delenv(key, raising=False)
    assert cli.main(['demo-local', '--admin-email', 'a@example.vn']) == 2
    assert 'SMTP' in capsys.readouterr().err


def test_cli_demo_local_worker_role_gets_the_dedicated_database_and_disk_media(monkeypatch, tmp_path):
    from wayfinder import cli
    monkeypatch.setenv('WAYFINDER_DATABASE_URL', 'postgresql+psycopg://u:p@127.0.0.1:5432/wayfinder')
    for key, value in SMTP_ENV.items():
        monkeypatch.setenv(key, value)
    seen = {}
    runtime = SimpleNamespace(close=lambda: seen.setdefault('runtime_closed', True))
    engine = SimpleNamespace(dispose=lambda: seen.setdefault('engine_disposed', True))
    def fake_worker(settings, media, **kwargs):
        seen.update(settings=settings, media=media)
        return SimpleNamespace(build_runtime=runtime), engine
    monkeypatch.setattr(demo_local, 'make_demo_worker', fake_worker)
    monkeypatch.setattr(demo_local, 'run_demo_worker', lambda worker, **kwargs: 0)
    assert cli.main(['demo-local', '--role', 'worker', '--database', 'wayfinder_demo_cli', '--artifact-root', str(tmp_path)]) == 0
    settings = seen['settings']
    assert settings.database_url.endswith('/wayfinder_demo_cli') and settings.build_runner == 'real' and settings.env == 'dev'
    assert settings.cloudinary_url is None and settings.mailer == 'smtp'
    assert type(seen['media']) is DiskMediaStore
    assert seen['media'].root == tmp_path.resolve() / 'demo-local' / 'wayfinder_demo_cli' / 'media'
    assert seen['runtime_closed'] and seen['engine_disposed']


def test_cli_demo_local_reports_a_missing_sample_roadmap_without_a_traceback(monkeypatch, capsys):
    from wayfinder import cli
    from wayfinder.api.errors import WebError
    monkeypatch.setenv('WAYFINDER_DATABASE_URL', 'postgresql+psycopg://u:p@127.0.0.1:5432/wayfinder')
    def missing(*args, **kwargs):
        raise WebError('conflict', 'Chưa có lộ trình hoàn tất')
    monkeypatch.setattr(demo_local, 'run_demo_local', missing)
    assert cli.main(['demo-local', '--admin-email', 'a@example.vn']) == 1
    assert 'Chưa có lộ trình hoàn tất' in capsys.readouterr().err
