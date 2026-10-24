"""Check the real upload/worker path against the frozen doc-6 copy without spending."""
from hashlib import sha256
import json
from pathlib import Path
import shutil

import pytest

from test_builds_w14 import builds, sql
from test_pipeline_postport_w15 import guarded_pg
from test_real_build_w15 import evidence

pytestmark = pytest.mark.postgres
ROOT = Path(__file__).parents[4]


def test_doc6_real_web_worker_stops_at_the_first_uncached_stage_without_spending(builds, guarded_pg, tmp_path):
    from doc2roadmap.application.phase_b.retrieval import load_learning_graph
    from doc2roadmap.config import Settings
    from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore
    from wayfinder.application.build_worker import BuildWorker
    from wayfinder.composition import compose_build_service
    from wayfinder.domain.file_paths import safe_path
    from wayfinder.infrastructure.real_build import RealBuildRuntime

    manifest = ROOT / 'report/doc1-rebuild-evidence-2026-10-20/development-fixtures.json'
    assert sha256(manifest.read_bytes()).hexdigest() == '5fc819f723f7263fe3d443ec780009a75aae66f2c35db8fe0bc3e3c50464eb84'
    entries = [row for row in json.loads(manifest.read_text(encoding='utf-8'))['files']
               if '/doc-6/' in row['path'] or row['path'] == 'doc-6.pdf']
    copied = tmp_path / 'frozen-copy'
    for row in entries:
        source = safe_path(ROOT, row['path'])
        assert source.stat().st_nlink == 1 and sha256(source.read_bytes()).hexdigest() == row['sha256']
        target = copied / row['path']
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        assert target.stat().st_nlink == 1 and sha256(target.read_bytes()).hexdigest() == row['sha256']
    content = (copied / 'doc-6.pdf').read_bytes()
    digest = sha256(content).hexdigest()
    doc_id = 'u-' + digest[:20]
    settings = builds.settings.model_copy(update={'artifact_root': copied / 'artifacts', 'build_runner': 'real'})
    core = Settings(_env_file=None, artifact_dir=settings.artifact_root, llm_transport='vertex',
                    vertex_project='cache-only-no-network', vertex_location='global')
    service = compose_build_service(settings, builds.engine, media=builds.media, clock=builds.clock, core_settings=core)
    builds.services.builds = service
    runtime = RealBuildRuntime(settings, builds.engine, core_settings=core)
    receipts = []

    def runner(recorder):
        def record(result):
            receipts.append(json.loads(json.dumps(result.to_dict())))
            recorder(result)
        return runtime.runner(record)

    try:
        uploaded = builds.client.post('/api/v1/uploads', files={'file': ('doc-6.pdf', content, 'application/pdf')},
                                       data={'rights_confirmed': 'true'}, headers=builds.headers)
        assert uploaded.status_code == 200, uploaded.text
        upload = uploaded.json()
        confirmed = builds.client.post('/api/v1/uploads/' + upload['upload_id'] + '/build',
                                        json={}, headers=builds.headers)
        assert confirmed.status_code == 200 and confirmed.json()['status'] == 'queued'
        worker = BuildWorker(service, runner_factory=runner,
            graph_loader=lambda doc, version: load_learning_graph(JsonArtifactStore(settings.artifact_root), doc, version),
            mailer=builds.mailer, worker_id='doc6-cache-only')
        job = worker.run_next_job()
        assert len(receipts) == 1
        receipt = receipts[0]
        assert job['doc_id'] == doc_id and job['status'] == 'failed'
        assert receipt['completed_steps'] == ['doc_reading']
        assert receipt['error']['stage'] == 'concepts' and receipt['error']['error_type'] == 'SpendNotAllowed'
        assert receipt['model_calls'] == receipt['spent_usd'] == 0 and receipt['usage_complete']
        courses = sql(builds, 'SELECT status,doc_id,published_graph_version FROM course')
        attempts = sql(builds, 'SELECT result FROM build_attempt')
        assert len(attempts) == 1 and attempts[0]['result']['status'] == 'failed'
        assert len(courses) == 1 and courses[0]['published_graph_version'] is None
        ledger = sql(builds, 'SELECT purpose,cost_usd,input_tokens,output_tokens,extra FROM usage_ledger')
        assert len(ledger) == 1 and ledger[0]['purpose'] == 'build'
        assert ledger[0]['cost_usd'] == ledger[0]['input_tokens'] == ledger[0]['output_tokens'] == 0
        assert ledger[0]['extra']['model_calls'] == 0 and ledger[0]['extra']['build_id'] == job['id']
        assert not any(message['subject'] == 'Bản dựng xong' for message in builds.mailer.messages)
        assert not (settings.artifact_root / 'graph' / doc_id).exists()
        assert not list(copied.rglob('live.json')) and not list(copied.rglob('*.sqlite3'))
        assert all(sha256((ROOT / row['path']).read_bytes()).hexdigest() == row['sha256'] for row in entries)
        evidence('doc6-real-web-cache-only', dict(source_sha256=digest, copied_files=len(entries),
            build=job, receipt_before_web_error_mapping=receipt, courses=courses, attempts=attempts, ledger=ledger,
            mail_subjects=[message['subject'] for message in builds.mailer.messages], provider_calls=0,
            ready_at_zero_cost_proven=False, source_manifest_sha256=sha256(manifest.read_bytes()).hexdigest(),
            test_source_sha256=sha256(Path(__file__).read_bytes()).hexdigest()))
    finally:
        runtime.close()
