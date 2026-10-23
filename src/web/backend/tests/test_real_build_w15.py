"""W-15 adapter tests: PostgreSQL and core orchestrator, fake pipeline/providers."""
from copy import deepcopy
from decimal import Decimal
import importlib
import importlib.util
import json
import os
from pathlib import Path

import pytest

from doc2roadmap.config import Settings
from test_builds_w14 import builds, sql, upload
from wayfinder.settings import WebSettings

pytestmark = pytest.mark.postgres


def module():
    name = 'wayfinder.infrastructure.real_build'
    assert importlib.util.find_spec(name), 'W-15 web adapter is missing'
    return importlib.import_module(name)


def core(b):
    return Settings(_env_file=None, artifact_dir=b.settings.artifact_root,
                    llm_transport='vertex', vertex_project='fake-project', vertex_location='global')


@pytest.fixture(autouse=True)
def no_fallbacks(builds, monkeypatch):
    from sqlalchemy import text
    with builds.engine.begin() as connection:
        connection.execute(text('TRUNCATE phase_b_cache,phase_b_record,phase_b_negative'))
    def forbidden(*args, **kwargs):
        raise AssertionError('W-15 may not use CLI stores, providers, ADC, SMTP or Cloudinary')
    for target in ('google.auth.default', 'wayfinder.composition.google_auth_default',
                   'doc2roadmap.infrastructure.artifacts.phase_b_store.JsonPhaseBStore.__init__',
                   'doc2roadmap.infrastructure.artifacts.build_log.SqliteBuildLog.__init__',
                   'doc2roadmap.composition_phase_b.PhaseBRuntime.__init__'):
        monkeypatch.setattr(target, forbidden)
    builds.mailer.messages.clear()


def evidence(name, value):
    folder = Path(__file__).parents[4] / 'report/w15-evidence/sql' / os.environ.get('W15_EVIDENCE_RUN', 'latest')
    folder.mkdir(parents=True, exist_ok=True)
    (folder / (name + '.json')).write_bytes((json.dumps(value, ensure_ascii=False, indent=2, default=str) + '\n').encode())


class FakePipeline:
    instances = []
    hook = None
    incomplete = False
    fail = False

    def __init__(self, settings, *, allow_spend, phase_b_store):
        assert settings.llm_transport == 'vertex' and not allow_spend
        self.settings, self.phase_b_store = settings, phase_b_store
        # Nonzero lifetime history must never be billed to this attempt.
        self.values = dict(spent_usd=9., model_calls=90, input_tokens=9000,
                           output_tokens=900, usage_complete=True, missing_usage_calls=0)
        self.instances.append(self)

    def read(self, path, doc):
        self.doc = doc
        return {'page_texts': ['Đây là nội dung giáo trình tiếng Việt có đầy đủ ví dụ. ' * 20]}

    def label_roles(self, doc):
        self.calls = ['label-roles']
        self.phase_b_store.put_cache('w15:roles:' + doc, {'labelled': True})
        return {'reused': False}

    def a3(self, doc):
        assert self.calls == ['label-roles']
        self.calls.append('a3')
        return {'a3_prime': True}

    def canonical(self, doc, language):
        assert language == 'vi'
        self.add()
        return {}

    def roadmap(self, doc):
        self.add()
        self.phase_b_store.put_record('module_name', doc, {'doc_id': doc, 'title': 'Tên giả'})
        if self.fail:
            raise ConnectionError('synthetic pipeline failure')
        return {'graph_version': 8}

    def learning_prep(self, path, doc, graph_version):
        self.add()
        self.phase_b_store.put_record('module_assignment', doc, {'doc_id': doc, 'graph_version': graph_version})
        if self.hook:
            self.hook(self)
        return {}

    def add(self):
        self.values['spent_usd'] += .001
        self.values['model_calls'] += 1
        self.values['input_tokens'] += 100
        self.values['output_tokens'] += 20
        if self.incomplete:
            self.values['usage_complete'] = False
            self.values['missing_usage_calls'] += 1

    def usage(self):
        return deepcopy(self.values)


class PipelineWithoutStorePort:
    def __init__(self, settings, *, allow_spend):
        raise AssertionError('An unported pipeline must not be constructed')


def test_dev_default_stays_fake_and_real_setting_is_explicit(builds):
    settings = WebSettings(_env_file=None)
    assert getattr(settings, 'build_runner', None) == 'fake', 'dev needs an explicit fake default'
    assert WebSettings(_env_file=None, build_runner='real').build_runner == 'real'


def test_real_default_requires_core_port_before_claim_or_provider(builds, monkeypatch):
    monkeypatch.setattr('doc2roadmap.composition_build.DocumentPipeline', PipelineWithoutStorePort)
    b = builds
    adapter = module()
    settings = b.settings.model_copy(update={'build_runner': 'real'})
    item = upload(b)
    b.service.confirm_build(b.actor, item['upload_id'])
    with pytest.raises(adapter.CoreBuildPortUnavailable, match='phase_b_store'):
        adapter.RealBuildRuntime(settings, b.engine, core_settings=core(b))
    assert sql(b, 'SELECT status FROM build')[0]['status'] == 'queued'
    assert not sql(b, 'SELECT * FROM build_attempt')


@pytest.mark.parametrize('transport,project', [('developer_api', 'p'), ('vertex', None)])
def test_real_transport_validation_precedes_pipeline_construction(builds, transport, project):
    b = builds
    settings = core(b).model_copy(update={'llm_transport': transport, 'vertex_project': project})
    with pytest.raises(ValueError, match='Vertex'):
        module().RealBuildRuntime(b.settings, b.engine, core_settings=settings,
                                 pipeline_factory=FakePipeline)


def test_real_default_factory_injects_web_postgres_before_provider(builds, monkeypatch):
    from doc2roadmap.composition_build import DocumentPipeline
    from doc2roadmap.application.ports.build import BuildRejected
    from wayfinder.infrastructure.database import create_database_engine
    from wayfinder.infrastructure.phase_b_store import PostgresPhaseBStore
    from wayfinder.worker import make_real_worker
    b = builds
    settings = b.settings.model_copy(update={'build_runner': 'real',
        'database_url': b.postgres_database_url.render_as_string(hide_password=False)})
    consumer, engine = make_real_worker(settings, core_settings=core(b))
    runtime = consumer.build_runtime
    reader = PostgresPhaseBStore(create_database_engine(b.postgres_database_url))
    receipts, injections = [], []

    def stop_after_store_write(pipeline, file_path, doc_id):
        assert not pipeline.allow_spend
        injected = pipeline._injected_phase_b_store
        assert isinstance(injected, PostgresPhaseBStore)
        injections.append(injected)
        pipeline._phase_b_store().put_cache('sa62:web:' + doc_id, {'written_by': 'default-pipeline'})
        raise BuildRejected('chu_loi', 'Synthetic stop before any provider or later build step')

    monkeypatch.setattr(DocumentPipeline, 'read', stop_after_store_write)
    try:
        assert runtime.pipeline_factory is DocumentPipeline
        assert consumer.service.pipeline_version == runtime.pipeline_version
        assert consumer.run_next_job() is None
        result = runtime.runner(receipts.append).execute(Path('unused.pdf'), 'sa62-web-port')
        assert result.status == 'rejected' and result.error['code'] == 'chu_loi'
        assert injections == [runtime.phase_b_store]
        assert reader.get_cache('sa62:web:sa62-web-port') == {'written_by': 'default-pipeline'}
        assert receipts == [result] and result.model_calls == 0 and result.spent_usd == 0
        assert not sql(b, 'SELECT * FROM build_attempt')
        assert not sql(b, 'SELECT * FROM usage_ledger')
    finally:
        reader.close()
        runtime.close()
        engine.dispose()


@pytest.mark.parametrize('complete', [True, False])
@pytest.mark.parametrize('outcome', ['success', 'failure', 'cancel'])
def test_real_adapter_cumulative_usage_and_pg_recorder(builds, monkeypatch, complete, outcome):
    from wayfinder.application.build_worker import BuildWorker
    from wayfinder.composition import compose_build_service
    from wayfinder.testing import _sample_graph
    b = builds
    adapter = module()
    monkeypatch.setattr(FakePipeline, 'incomplete', not complete)
    monkeypatch.setattr(FakePipeline, 'fail', outcome == 'failure')
    settings = b.settings.model_copy(update={'build_runner': 'real'})
    runtime = adapter.RealBuildRuntime(settings, b.engine, core_settings=core(b), pipeline_factory=FakePipeline)
    service = compose_build_service(settings, b.engine, media=b.media, clock=b.clock, core_settings=core(b))
    assert service.pipeline_version == runtime.pipeline_version and service.pipeline_version != 'web-fake-v1'
    item = service.create_upload(b.actor, 'book.pdf', __import__('test_builds_w14').pdf(), rights_confirmed=True)
    bid = item['build']['build_id']
    service.confirm_build(b.actor, item['upload_id'])
    def hook(pipeline):
        if outcome == 'cancel':
            b.service.cancel_build(b.actor, bid)
    monkeypatch.setattr(FakePipeline, 'hook', staticmethod(hook))
    def graph(doc, version):
        result = _sample_graph()
        result.doc_id, result.graph_version = doc, version
        return result
    ticks = iter(range(100))
    runtime.monotonic = lambda: next(ticks)
    consumer = BuildWorker(service, runner_factory=runtime.runner, graph_loader=graph,
                           mailer=b.mailer, worker_id='real-adapter-fake-pipeline')
    try:
        result = consumer.run_next_job()
        expected = {'success': 'succeeded', 'failure': 'failed', 'cancel': 'cancelled'}[outcome]
        assert result['status'] == expected
        amount = Decimal('.002') if outcome == 'failure' else Decimal('.003')
        assert result['spent_usd'] == amount
        assert result['usage_complete'] == complete
        rows = sql(b, "SELECT * FROM usage_ledger WHERE purpose='build' ORDER BY id")
        assert sum(row['cost_usd'] for row in rows) == amount
        attempt = sql(b, 'SELECT * FROM build_attempt')[0]
        assert attempt['result']['spent_usd'] < .004 and attempt['result']['model_calls'] in (2, 3)
        final = [row for row in rows if row['extra']['step'] is None]
        assert len(final) == 1
        assert final[0]['cost_usd'] == (Decimal('.001') if outcome == 'failure' else 0)
        assert not final[0]['extra']['attribution_complete']
        if not complete:
            assert all(not row['extra']['usage_complete'] for row in rows)
        details = attempt['result']['step_details']
        assert details['concepts']['web_timing']['wall_seconds'] == 1
        assert details['concepts']['web_timing']['embedding_wait_seconds'] is None
        assert details['graph']['web_timing']['wall_seconds'] == 1
        if outcome == 'cancel': assert not b.mailer.messages
        assert sql(b, "SELECT count(*) AS n FROM phase_b_cache WHERE key LIKE 'w15:roles:%'")[0]['n'] == 1
        assert sql(b, "SELECT count(*) AS n FROM phase_b_record WHERE kind='module_name'")[0]['n'] == 1
        receipt = deepcopy(attempt['result'])
        from doc2roadmap.application.ports.build import BuildResult
        duplicate = BuildResult(**receipt)
        assert not b.store.record_usage(bid, str(attempt['lease_id']), receipt, b.clock.now(), result=duplicate)
        assert len(sql(b, "SELECT * FROM usage_ledger WHERE purpose='build'")) == len(rows)
        evidence(f'{outcome}-{complete}', {'build': result, 'receipt': receipt, 'ledger': rows,
                 'transport': 'vertex', 'new_provider_calls': 0, 'synthetic_usage': True})
    finally:
        runtime.close()
    assert not list(b.settings.artifact_root.rglob('live.json'))
    assert not list(b.settings.artifact_root.rglob('*.sqlite3'))


def test_real_adapter_rejects_dry_run_before_factory_or_recorder(builds):
    adapter = module()
    called = []
    runtime = adapter.RealBuildRuntime(builds.settings, builds.engine, core_settings=core(builds), pipeline_factory=FakePipeline)
    try:
        runner = runtime.runner(called.append)
        with pytest.raises(ValueError, match='dry.run'):
            runner.execute(Path('never-open.pdf'), 'doc', dry_run=True)
        assert not called
        assert not sql(builds, 'SELECT * FROM build_attempt')
    finally:
        runtime.close()


def test_real_children_persist_sessions_names_cache_and_reservations_in_pg(builds, monkeypatch):
    from wayfinder.infrastructure.learning_runtime import WebLearningRuntime
    from wayfinder.infrastructure.database import create_database_engine
    from wayfinder.testing import _sample_graph
    from doc2roadmap.application.phase_b.naming import NameModulesB
    from doc2roadmap.application.phase_b.concept_index import IndexConcepts
    from types import SimpleNamespace
    b = builds
    root = Path(__file__).parents[4]
    monkeypatch.syspath_prepend(str(root / 'tests/unit/application'))
    from test_phase_b_naming import Store, Model, upstream, valid_outputs
    runtime = module().RealBuildRuntime(b.settings, b.engine, core_settings=core(b), pipeline_factory=FakePipeline)
    independent_engine = create_database_engine(b.postgres_database_url)
    from wayfinder.infrastructure.phase_b_store import PostgresPhaseBStore
    reader = PostgresPhaseBStore(independent_engine)
    try:
        learning = WebLearningRuntime(runtime.phase_b_store, clock=b.clock)
        graph = _sample_graph()
        session = learning.sessions(graph).create_session(b.actor.user_id, graph.doc_id, {'kind': 'roadmap'})
        assert reader.get_record('session', session['session_id'])['owner'] == b.actor.user_id
        token = learning.spend_guard.reserve('assistant', .001, b.actor.user_id)
        assert reader.get_record('spend_reservation', token)['learner_id'] == b.actor.user_id
        learning.spend_guard.release(token)
        assert reader.get_record('spend_reservation', token) is None
        model = Model(valid_outputs())
        naming = NameModulesB(Store(), model, phase_b_store=runtime.phase_b_store, allow_spend=True)
        first, _ = naming.execute('book', upstream=upstream())
        # A second independent use case must use the committed PostgreSQL cache.
        cached_model = Model([])
        second, _ = NameModulesB(Store(), cached_model, phase_b_store=reader, allow_spend=False).execute('book', upstream=upstream())
        assert not cached_model.calls and len(model.calls) == 3
        assert first.payload['modules'] == second.payload['modules']
        class Embedding:
            embedding_model_id = 'gemini-embedding-001'
            def __init__(self): self.calls = 0
            def embed(self, requests):
                self.calls += 1
                return [[1.] * 768 for _ in requests]
        embedding = Embedding()
        artifacts = SimpleNamespace(load_graph=lambda doc, version: SimpleNamespace(payload=graph.payload))
        first_index = IndexConcepts(artifacts, embedding, runtime.phase_b_store).execute(graph.doc_id, graph.graph_version, allow_spend=True)
        cached_index = IndexConcepts(artifacts, embedding, reader).execute(graph.doc_id, graph.graph_version, allow_spend=False)
        assert cached_index['reused'] and not first_index['reused'] and embedding.calls == 1
        assert reader.get_cache(next(row['key'] for row in sql(b, "SELECT key FROM phase_b_cache WHERE key LIKE 'concept-index:%'")))
        evidence('children', {'sessions': sql(b, "SELECT kind,owner,doc_id FROM phase_b_record WHERE kind='session'"),
                 'cache': sql(b, 'SELECT key FROM phase_b_cache'), 'usage': sql(b, 'SELECT purpose,cost_usd FROM usage_ledger'),
                 'provider_calls': 0, 'fake_naming_calls': len(model.calls), 'fake_embedding_calls': embedding.calls})
    finally:
        reader.close()
        runtime.close()


def test_real_worker_composition_uses_pg_version_and_never_claims_without_port(builds, monkeypatch):
    from wayfinder.worker import make_worker, make_real_worker
    b = builds
    adapter = module()
    monkeypatch.setenv('DOC2ROADMAP_LLM_TRANSPORT', 'vertex')
    monkeypatch.setenv('DOC2ROADMAP_VERTEX_PROJECT', 'fake-project')
    settings = b.settings.model_copy(update={'build_runner': 'real', 'database_url': b.postgres_database_url.render_as_string(hide_password=False)})
    # make_worker dispatches real without requiring fake-source or manifest.
    monkeypatch.setattr('doc2roadmap.composition_build.DocumentPipeline', PipelineWithoutStorePort)
    with pytest.raises(adapter.CoreBuildPortUnavailable):
        make_worker(settings)
    consumer, engine = make_real_worker(settings, core_settings=core(b), pipeline_factory=FakePipeline)
    try:
        assert consumer.service.pipeline_version == consumer.build_runtime.pipeline_version
        assert consumer.store.engine.url == consumer.build_runtime.phase_b_store.engine.url
        assert consumer.run_next_job() is None
    finally:
        consumer.build_runtime.close()
        engine.dispose()


def test_real_adapter_cancel_during_publication_with_independent_connection(builds):
    from wayfinder.application.build_worker import BuildWorker
    from wayfinder.application.builds import BuildService
    from wayfinder.composition import compose_build_service
    from wayfinder.infrastructure.build_store import PostgresBuildStore
    from wayfinder.infrastructure.database import create_database_engine
    from wayfinder.testing import _sample_graph
    b = builds
    settings = b.settings.model_copy(update={'build_runner': 'real'})
    runtime = module().RealBuildRuntime(settings, b.engine, core_settings=core(b), pipeline_factory=FakePipeline)
    service = compose_build_service(settings, b.engine, media=b.media, clock=b.clock, core_settings=core(b))
    item = service.create_upload(b.actor, 'book.pdf', __import__('test_builds_w14').pdf(), rights_confirmed=True)
    bid = item['build']['build_id']
    service.confirm_build(b.actor, item['upload_id'])
    other_engine = create_database_engine(b.postgres_database_url)
    cancel = BuildService(PostgresBuildStore(other_engine), settings=settings, media=b.media, clock=b.clock)
    def publication(doc, version):
        assert cancel.cancel_build(b.actor, bid)['cancel_requested']
        assert sql(b, 'SELECT cancel_requested FROM build WHERE id=:id', {'id': bid})[0]['cancel_requested']
        graph = _sample_graph()
        graph.doc_id, graph.graph_version = doc, version
        return graph
    try:
        consumer = BuildWorker(service, runner_factory=runtime.runner, graph_loader=publication,
                               mailer=b.mailer, worker_id='real-publication-race')
        assert consumer.run_next_job()['status'] == 'cancelled'
        proof = {'build': sql(b, 'SELECT status,spent_usd,usage_complete FROM build')[0],
                 'course': sql(b, 'SELECT status,published_graph_version FROM course')[0],
                 'mail': b.mailer.messages, 'usage': sql(b, 'SELECT cost_usd FROM usage_ledger')}
        assert proof['course']['status'] == 'failed' and proof['course']['published_graph_version'] is None
        assert not b.mailer.messages and proof['build']['spent_usd'] == Decimal('.003')
        assert sum(row['cost_usd'] for row in proof['usage']) == Decimal('.003')
        evidence('publication-cancel', proof)
    finally:
        runtime.close()
        other_engine.dispose()


def test_real_runtime_rejects_a_different_database_engine(builds):
    settings = builds.settings.model_copy(update={'database_url': 'postgresql+psycopg://unused:unused@127.0.0.1/not_the_web_database'})
    with pytest.raises(ValueError, match='same PostgreSQL'):
        module().RealBuildRuntime(settings, builds.engine, core_settings=core(builds), pipeline_factory=FakePipeline)


def test_manifest_doc6_graph_does_not_prove_web_identity_or_real_cache(builds):
    from hashlib import sha256
    from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore
    from doc2roadmap.application.phase_b.retrieval import load_learning_graph
    from wayfinder.composition import compose_build_service
    b = builds
    root = Path(__file__).parents[4]
    manifest_path = root / 'report/doc1-rebuild-evidence-2026-10-20/development-fixtures.json'
    assert sha256(manifest_path.read_bytes()).hexdigest() == '5fc819f723f7263fe3d443ec780009a75aae66f2c35db8fe0bc3e3c50464eb84'
    entries = json.loads(manifest_path.read_text(encoding='utf-8'))['files']
    relevant = [entry for entry in entries if '/doc-6/' in entry['path'] or entry['path'] == 'doc-6.pdf']
    assert relevant
    for entry in relevant:
        path = root / entry['path']
        assert path.stat().st_nlink == 1 and not path.is_symlink()
        assert sha256(path.read_bytes()).hexdigest() == entry['sha256']
    graph = load_learning_graph(JsonArtifactStore(root / 'artifacts'), 'doc-6', 29)
    assert graph.graph_version == 29
    content = (root / 'doc-6.pdf').read_bytes()
    settings = b.settings.model_copy(update={'build_runner': 'real'})
    service = compose_build_service(settings, b.engine, media=b.media, clock=b.clock, core_settings=core(b))
    first = service.create_upload(b.actor, 'doc-6.pdf', content, rights_confirmed=True)
    doc = b.store.get_job(first['build']['build_id'])['doc_id']
    assert doc == 'u-' + sha256(content).hexdigest()[:20] and doc != 'doc-6'
    assert first['build']['status'] == 'awaiting_confirmation'
    assert b.store.reusable(doc, 'web-fake-v1') is None
    second = service.create_upload(b.actor, 'same.pdf', content, rights_confirmed=True)
    assert second['build']['build_id'] == first['build']['build_id']
    assert not sql(b, 'SELECT * FROM build_attempt')
    assert not sql(b, 'SELECT * FROM usage_ledger')
    evidence('doc6-identity', {'manifest_sha256': sha256(manifest_path.read_bytes()).hexdigest(),
             'verified_doc6_files': len(relevant), 'source_graph_version': 29, 'source_doc_id': 'doc-6',
             'web_doc_id': doc, 'web_pipeline_version': service.pipeline_version,
             'reuse_same_identity': True, 'real_cache_validated': False,
             'model_calls_required': 'unknown', 'new_provider_calls': 0, 'historical_usage_imported': False})


def test_real_adapter_late_old_lease_records_known_usage_without_publication(builds, monkeypatch):
    from wayfinder.application.build_worker import BuildWorker
    from wayfinder.composition import compose_build_service
    from doc2roadmap.application.ports.build import BuildResult
    b = builds
    settings = b.settings.model_copy(update={'build_runner': 'real'})
    runtime = module().RealBuildRuntime(settings, b.engine, core_settings=core(b), pipeline_factory=FakePipeline)
    service = compose_build_service(settings, b.engine, media=b.media, clock=b.clock, core_settings=core(b))
    item = service.create_upload(b.actor, 'book.pdf', __import__('test_builds_w14').pdf(), rights_confirmed=True)
    bid = item['build']['build_id']
    service.confirm_build(b.actor, item['upload_id'])
    leases = []
    def reclaim(pipeline):
        b.clock.advance(601)
        assert b.store.reclaim(b.clock.now(), settings) == 1
        leases.append(b.store.claim('new-lease', b.clock.now(), settings))
    monkeypatch.setattr(FakePipeline, 'hook', staticmethod(reclaim))
    def no_graph(*args):
        raise AssertionError('late failed lease must not read/publish a graph')
    try:
        consumer = BuildWorker(service, runner_factory=runtime.runner, graph_loader=no_graph,
                               mailer=b.mailer, worker_id='old-lease')
        job = consumer.run_next_job()
        assert job['status'] == 'reading' and job['lease_id'] == leases[0]['lease_id']
        assert job['spent_usd'] == Decimal('.003') and not job['usage_complete']
        old = sql(b, 'SELECT * FROM build_attempt WHERE result IS NOT NULL')[0]
        duplicate = BuildResult(**old['result'])
        assert not b.store.record_usage(bid, str(old['lease_id']), duplicate.to_dict(), b.clock.now(), result=duplicate)
        assert b.store.get_job(bid)['status'] == 'reading'
        assert not b.mailer.messages
        b.service.cancel_build(b.actor, bid)
        result = BuildResult(job['doc_id'], 'succeeded', runtime.pipeline_version, graph_version=8, spent_usd=.001)
        assert b.store.record_usage(bid, job['lease_id'], result.to_dict(), b.clock.now(), result=result)
        proof = {'build': sql(b, 'SELECT status,spent_usd,usage_complete FROM build')[0],
                 'course': sql(b, 'SELECT status,published_graph_version FROM course')[0],
                 'attempts': sql(b, 'SELECT lease_id,result FROM build_attempt'),
                 'ledger': sql(b, "SELECT cost_usd,extra FROM usage_ledger WHERE purpose='build'")}
        assert proof['build']['status'] == 'cancelled' and proof['build']['spent_usd'] == Decimal('.004')
        assert proof['course']['published_graph_version'] is None and proof['course']['status'] == 'failed'
        assert sum(row['cost_usd'] for row in proof['ledger']) == Decimal('.004')
        evidence('old-lease', proof)
    finally:
        runtime.close()


@pytest.mark.parametrize('counted_in', ['build', None, 'other'])
def test_build_trace_keeps_raw_usage_but_is_not_billed_twice(builds, counted_in):
    from wayfinder.infrastructure.phase_b_store import PostgresPhaseBStore
    from wayfinder.infrastructure.database import create_database_engine
    from doc2roadmap.application.phase_b.budget import DailySpendGuard, DailyLimitExceeded
    from doc2roadmap.domain.phase_b_limits import BSettings
    b = builds
    store = PostgresPhaseBStore(b.engine)
    independent = PostgresPhaseBStore(create_database_engine(b.postgres_database_url))
    # The shared-purpose row makes the guard's actual admission decision observable.
    row = dict(purpose='lecture', doc_id='w15-trace', cost_usd=.003,
               input_tokens=300, output_tokens=60, created_at=b.clock.now().isoformat())
    if counted_in is not None:
        row['counted_in'] = counted_in
    try:
        store.append_usage(row)
        assert independent.usage_rows(doc_id='w15-trace') == [row]
        totals = sql(b, 'SELECT sum(cost_usd) AS usd, sum(input_tokens) AS input, sum(output_tokens) AS output FROM usage_ledger')[0]
        trace = counted_in == 'build'
        assert totals['usd'] == (0 if trace else Decimal('.003'))
        assert totals['input'] == (0 if trace else 300)
        assert totals['output'] == (0 if trace else 60)
        guard = DailySpendGuard(independent, settings=BSettings(system_daily_max_usd=.002), clock=b.clock)
        with pytest.raises(DailyLimitExceeded):
            guard.reserve('lecture', .0001)
        assert not sql(b, "SELECT * FROM phase_b_record WHERE kind='spend_reservation'")
        evidence('trace-' + str(counted_in), {'raw': independent.usage_rows(), 'billable': totals,
                 'shared_guard_admission': 'refused', 'provider_calls': 0})
    finally:
        independent.close()
        store.close()


def test_real_adapter_meter_is_the_only_build_charge_with_child_traces(builds):
    from wayfinder.application.build_worker import BuildWorker
    from wayfinder.composition import compose_build_service
    from wayfinder.testing import _sample_graph
    b = builds
    class TracedPipeline(FakePipeline):
        def roadmap(self, doc):
            result = super().roadmap(doc)
            self.phase_b_store.append_usage(dict(purpose='module_title', doc_id=doc,
                counted_in='build', cost_usd=.001, input_tokens=100, output_tokens=20))
            return result
        def learning_prep(self, path, doc, graph_version):
            result = super().learning_prep(path, doc, graph_version)
            self.phase_b_store.append_usage(dict(purpose='embedding', doc_id=doc,
                counted_in='build', cost_usd=.001, input_tokens=100, output_tokens=20))
            return result
    settings = b.settings.model_copy(update={'build_runner': 'real'})
    runtime = module().RealBuildRuntime(settings, b.engine, core_settings=core(b), pipeline_factory=TracedPipeline)
    service = compose_build_service(settings, b.engine, media=b.media, clock=b.clock, core_settings=core(b))
    item = service.create_upload(b.actor, 'book.pdf', __import__('test_builds_w14').pdf(), rights_confirmed=True)
    service.confirm_build(b.actor, item['upload_id'])
    def graph(doc, version):
        result = _sample_graph()
        result.doc_id, result.graph_version = doc, version
        return result
    try:
        consumer = BuildWorker(service, runner_factory=runtime.runner, graph_loader=graph,
                               mailer=b.mailer, worker_id='w15-trace-accounting')
        job = consumer.run_next_job()
        totals = sql(b, 'SELECT sum(cost_usd) AS usd, sum(input_tokens) AS input, sum(output_tokens) AS output FROM usage_ledger')[0]
        traces = sql(b, "SELECT * FROM usage_ledger WHERE extra->>'counted_in'='build'")
        assert job['status'] == 'succeeded' and job['spent_usd'] == Decimal('.003')
        assert totals == {'usd': Decimal('.003'), 'input': 300, 'output': 60}
        assert len(traces) == 2 and sum(row['extra']['cost_usd'] for row in traces) == .002
        assert all(row['cost_usd'] == 0 for row in traces)
        receipt = sql(b, 'SELECT result FROM build_attempt')[0]['result']
        assert receipt['model_calls'] == 3 and receipt['usage_complete']
        evidence('single-build-charge', {'build': job, 'totals': totals, 'traces': traces,
                 'receipt': receipt, 'provider_calls': 0, 'synthetic_usage': True})
    finally:
        runtime.close()
