"""Post-port W-15: real pipeline methods and file artifacts, fake provider responses."""
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

from test_builds_w14 import builds, sql
from test_real_build_w15 import evidence
from doc2roadmap.application import stage_measurements as measurements

pytestmark = pytest.mark.postgres
SENTENCE = 'Ma trận là một bảng số được sắp xếp theo hàng và cột.'


def source_pdf():
    import ctypes
    import pypdfium2 as pdfium
    from pypdfium2 import raw
    buffer = BytesIO()
    font_bytes = Path('C:/Windows/Fonts/arial.ttf').read_bytes()
    data = (ctypes.c_ubyte * len(font_bytes)).from_buffer_copy(font_bytes)
    with pdfium.PdfDocument.new() as writer:
        page = writer.new_page(595, 842)
        font = raw.FPDFText_LoadFont(writer.raw, data, len(data), 2, True)
        assert font
        for i, line in enumerate(['Chương 1. Ma trận'] + [SENTENCE] * 10):
            obj = raw.FPDFPageObj_CreateTextObj(writer.raw, font, 12)
            text = ctypes.create_string_buffer(line.encode('utf-16-le') + b'\0\0')
            assert raw.FPDFText_SetText(obj, ctypes.cast(text, ctypes.POINTER(ctypes.c_ushort)))
            raw.FPDFPageObj_Transform(obj, 1, 0, 0, 1, 40, 790 - i * 25)
            raw.FPDFPage_InsertObject(page.raw, obj)
        assert raw.FPDFPage_GenerateContent(page.raw)
        writer.save(buffer)
        page.close()
        raw.FPDFFont_Close(font)
    return buffer.getvalue()


class Model:
    identifier = 'w15-fake-generation-v1'
    model_id = 'gemini-3.1-flash-lite'
    calls = []
    incomplete = False
    on_title = None

    def __init__(self, key, model_id, **kwargs):
        assert kwargs['transport'] == 'vertex'
        self.model_id = model_id

    def start_session(self, system):
        return Session(self)


class Session:
    def __init__(self, model):
        self.model, self.call_count, self.repair_count, self.turns = model, 0, 0, ()

    def ask_json(self, prompt, *, response_schema, **kwargs):
        from tests.unit.application.test_a4_pipeline import FakeModel
        from tests.unit.application.test_canonical_gop import AnchorModel
        self.call_count += 1
        props = response_schema['properties']
        measurements.record_model_call()
        usage = {} if Model.incomplete and not Model.calls else {'promptTokenCount': 100, 'candidatesTokenCount': 20}
        measurements.record_usage(usage)
        Model.calls.append(sorted(props))
        if 'entities' in props:
            value = {'entities': [dict(name='Ma trận', node_type='concept', description_draft=SENTENCE,
                     evidence=SENTENCE, media_evidence_id='', learnable=True, aliases=[])],
                     'edges': [], 'media_descriptions': []}
        elif 'remove_entity_ids' in props:
            value = {'remove_entity_ids': [], 'remove_edge_ids': []}
        else:
            data = json.loads(prompt.split('\nCorrect this validation error:')[0])
            if 'labels' in props:
                value = {'labels': [{'index': row['index'], 'role': 'noi_dung'} for row in data['headings']]}
            elif 'title' in props:
                if Model.on_title:
                    Model.on_title()
                nodes = data.get('nodes', [])
                value = {'title': 'Ma trận', 'description': [{'text': SENTENCE,
                         'node_ids': [nodes[0]['node_id']] if nodes else []}]}
            elif 'items' in data:
                value = AnchorModel().ask_json(prompt, response_schema=response_schema).payload
            else:
                value = FakeModel().ask_json(prompt, response_schema=response_schema).payload
        return NS(payload=value, usage=usage, raw_text='', repaired=False)


class Embedding:
    identifier = 'w15-fake-embedding-v1'
    embedding_model_id = 'gemini-embedding-001:768'
    calls = 0
    fail = False

    def __init__(self, *args, **kwargs):
        assert kwargs['transport'] == 'vertex'

    def embed(self, requests):
        Embedding.calls += 1
        measurements.record_model_call(embedding=True)
        measurements.record_usage({'promptTokenCount': 100}, embedding=True)
        if Embedding.fail:
            raise ConnectionError('fake embedding failed after reporting known usage')
        return [[1., 0.] + [0.] * 766 for _ in requests]


@pytest.fixture
def guarded_pg(builds, monkeypatch):
    from sqlalchemy import text
    with builds.engine.begin() as connection:
        connection.execute(text('TRUNCATE phase_b_cache,phase_b_record,phase_b_negative'))
    def forbidden(*args, **kwargs):
        raise AssertionError('No provider, ADC or JSON/SQLite learner store allowed')
    for target in ('google.auth.default', 'wayfinder.composition.google_auth_default',
                   'doc2roadmap.infrastructure.artifacts.phase_b_store.JsonPhaseBStore.__init__',
                   'doc2roadmap.infrastructure.artifacts.build_log.SqliteBuildLog.__init__'):
        monkeypatch.setattr(target, forbidden)
    builds.mailer.messages.clear()


@pytest.fixture
def fake_providers(guarded_pg, monkeypatch):
    monkeypatch.setattr('doc2roadmap.composition_build.GeminiEntityExtractor', Model)
    monkeypatch.setattr('doc2roadmap.composition_build.GeminiEmbedding', Embedding)
    Model.calls, Embedding.calls = [], 0
    Model.incomplete = False
    Model.on_title = None
    Embedding.fail = False


@pytest.mark.parametrize('outcome,incomplete', [('success', False), ('success', True),
                          ('cancel', False), ('error', False), ('lease', False)])
def test_postport_whole_pipeline_with_fake_providers_and_independent_pg(builds, fake_providers, outcome, incomplete):
    from doc2roadmap.composition_build import DocumentPipeline
    from doc2roadmap.config import Settings
    from doc2roadmap.application.phase_b.retrieval import load_learning_graph
    from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore
    from wayfinder.infrastructure.real_build import RealBuildRuntime
    from wayfinder.composition import compose_build_service
    from wayfinder.application.build_worker import BuildWorker
    from wayfinder.infrastructure.database import create_database_engine
    from wayfinder.infrastructure.phase_b_store import PostgresPhaseBStore
    from wayfinder.infrastructure.learning_runtime import WebLearningRuntime
    from doc2roadmap.application.phase_b.budget import DailyLimitExceeded
    from doc2roadmap.domain.phase_b_limits import BSettings
    from doc2roadmap.application.ports.build import BuildResult
    b = builds
    Model.incomplete = incomplete
    settings = b.settings.model_copy(update={'build_runner': 'real'})
    core = Settings(_env_file=None, artifact_dir=settings.artifact_root, llm_transport='vertex',
                    vertex_project='fake-only', secondary_mode='llm')
    pipelines = []
    def factory(config, *, allow_spend, phase_b_store):
        assert allow_spend is False
        # Only this test factory permits fake calls. The production adapter still prohibits spend.
        pipeline = DocumentPipeline(config, allow_spend=True, phase_b_store=phase_b_store)
        pipelines.append(pipeline)
        return pipeline
    runtime = RealBuildRuntime(settings, b.engine, core_settings=core, pipeline_factory=factory)
    service = compose_build_service(settings, b.engine, media=b.media, clock=b.clock, core_settings=core)
    content = source_pdf()
    item = service.create_upload(b.actor, 'matran.pdf', content, rights_confirmed=True)
    service.confirm_build(b.actor, item['upload_id'])
    bid = item['build']['build_id']
    leases = []
    def on_title():
        if outcome == 'cancel':
            b.service.cancel_build(b.actor, bid)
        elif outcome == 'error':
            Embedding.fail = True
        elif outcome == 'lease' and not leases:
            b.clock.advance(601)
            assert b.store.reclaim(b.clock.now(), settings) == 1
            leases.append(b.store.claim('replacement', b.clock.now(), settings))
    Model.on_title = on_title
    raw_receipts = []
    def runner(recorder):
        def record(result):
            raw_receipts.append(json.loads(json.dumps(result.to_dict())))
            recorder(result)
        return runtime.runner(record)
    try:
        consumer = BuildWorker(service, runner_factory=runner,
            graph_loader=lambda doc, version: load_learning_graph(JsonArtifactStore(settings.artifact_root), doc, version),
            mailer=b.mailer, worker_id='postport-real-pipeline')
        job = consumer.run_next_job()
        receipt = sql(b, 'SELECT result FROM build_attempt WHERE result IS NOT NULL')[0]['result']
        expected = {'success': 'succeeded', 'cancel': 'cancelled', 'error': 'failed', 'lease': 'reading'}[outcome]
        assert job['status'] == expected, json.dumps(raw_receipts, ensure_ascii=False)
        assert receipt['model_calls'] == len(Model.calls) + Embedding.calls > 0
        assert receipt['usage_complete'] == (not incomplete)
        assert job['spent_usd'] > 0
        assert len(raw_receipts) == 1
        traces = sql(b, "SELECT * FROM usage_ledger WHERE extra->>'counted_in'='build'")
        assert all(row['cost_usd'] == row['input_tokens'] == row['output_tokens'] == 0 for row in traces)
        assert sql(b, 'SELECT sum(cost_usd) AS usd FROM usage_ledger')[0]['usd'] == job['spent_usd']
        ledger = sql(b, "SELECT * FROM usage_ledger WHERE purpose='build' ORDER BY id")
        assert len([row for row in ledger if row['extra']['step'] is None]) == 1
        if outcome == 'success':
            # Reading has no provider calls: its zero checkpoint creates no charge row.
            assert {row['extra']['step'] for row in ledger if row['extra']['step'] is not None} == {
                'concepts', 'graph', 'learning_prep'}
            assert receipt['step_details']['doc_reading']['web_timing']['wall_seconds'] > 0
        reader = PostgresPhaseBStore(create_database_engine(b.postgres_database_url))
        try:
            if outcome == 'success':
                assert receipt['completed_steps'] == ['doc_reading', 'concepts', 'graph', 'learning_prep']
                assert {row['purpose'] for row in traces} == {'embedding', 'module_title'}
                assert len(reader.list_records('module_assignment', doc_id=job['doc_id'])) == 1
                keys = sql(b, 'SELECT key FROM phase_b_cache')
                assert len(keys) >= 2 and all(reader.get_cache(row['key']) for row in keys)
                from doc2roadmap.application.phase_b.concept_index import IndexConcepts
                from doc2roadmap.application.phase_b.naming import NameModulesB
                named = pipelines[0].store.load_graph(job['doc_id'], receipt['graph_version'])
                upstream = pipelines[0].store.load_graph(job['doc_id'], named.manifest['config']['upstream_version'])
                model = Model('', core.roadmap_model_id, transport='vertex')
                calls_before = len(Model.calls), Embedding.calls
                assert NameModulesB(pipelines[0].store, model, phase_b_store=reader).plan(
                    job['doc_id'], upstream=upstream).calls_estimate == 0
                assert IndexConcepts(pipelines[0].store, pipelines[0].embedding_guard, reader).execute(
                    job['doc_id'], receipt['graph_version'], allow_spend=False)['reused']
                assert calls_before == (len(Model.calls), Embedding.calls)
                graph = load_learning_graph(pipelines[0].store, job['doc_id'], receipt['graph_version'])
                learning = WebLearningRuntime(runtime.phase_b_store, clock=b.clock,
                    settings=BSettings(system_daily_max_usd=.002))
                session = learning.sessions(graph).create_session(b.actor.user_id, graph.doc_id, {'kind': 'roadmap'})
                assert reader.get_record('session', session['session_id'])['owner'] == b.actor.user_id
                runtime.phase_b_store.append_usage(dict(purpose='lecture', cost_usd=.003,
                    created_at=b.clock.now().isoformat()))
                # Admission is a learner/shared-content guard check; it is not the build cap.
                with pytest.raises(DailyLimitExceeded):
                    learning.spend_guard.reserve('lecture', .0001)
            else:
                assert all(message['subject'] != 'Bản dựng xong' for message in b.mailer.messages)
                if outcome != 'error':
                    assert not b.mailer.messages
                assert sql(b, 'SELECT published_graph_version FROM course')[0]['published_graph_version'] is None
            original = sql(b, 'SELECT * FROM build_attempt WHERE result IS NOT NULL')[0]
            before = sql(b, 'SELECT count(*) AS n FROM usage_ledger')[0]['n']
            assert not b.store.record_usage(bid, str(original['lease_id']), receipt, b.clock.now(), result=BuildResult(**receipt))
            assert sql(b, 'SELECT count(*) AS n FROM usage_ledger')[0]['n'] == before
            if outcome == 'lease':
                assert job['lease_id'] == leases[0]['lease_id'] and not job['usage_complete']
        finally:
            reader.close()
        assert job['doc_id'] == 'u-' + sha256(content).hexdigest()[:20]
        assert not list(settings.artifact_root.rglob('live.json'))
        assert not list(settings.artifact_root.rglob('*.sqlite3'))
        evidence(f'postport-{outcome}-{incomplete}', {'build': job, 'receipt': receipt, 'traces': traces, 'ledger': ledger,
                 'phase_b_records': sql(b, 'SELECT kind,owner,doc_id FROM phase_b_record ORDER BY kind'),
                 'phase_b_cache_keys': sql(b, 'SELECT key FROM phase_b_cache ORDER BY key'),
                 'generation_fake_calls': len(Model.calls), 'embedding_fake_calls': Embedding.calls,
                 'provider_calls': 0, 'synthetic_usage': True})
    finally:
        runtime.close()
