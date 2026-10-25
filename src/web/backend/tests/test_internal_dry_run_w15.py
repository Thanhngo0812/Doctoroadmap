"""Real internal dry-runs use isolated verified copies, web PG and a collector, never queue."""
from hashlib import sha256
import json
from pathlib import Path
import shutil
from time import perf_counter

import pytest

from test_builds_w14 import builds, sql
from test_pipeline_postport_w15 import guarded_pg
from test_real_build_w15 import evidence

pytestmark = pytest.mark.postgres
ROOT = Path(__file__).parents[4]


@pytest.mark.parametrize('book', ['doc-6', 'candidate'])
def test_real_internal_dry_run_has_no_queue_receipt_or_provider_cost(builds, guarded_pg, tmp_path, book):
    from doc2roadmap.application.use_cases.build_document import BuildDocument
    from doc2roadmap.config import Settings
    from wayfinder.domain.file_paths import safe_path
    from wayfinder.infrastructure.real_build import RealBuildRuntime
    copied = tmp_path / 'dry-run-copy'
    candidate = json.loads((ROOT / 'report/w15-evidence/candidate.json').read_text(encoding='utf-8'))
    entries = []
    if book == 'doc-6':
        manifest_path = ROOT / 'report/doc1-rebuild-evidence-2026-10-20/development-fixtures.json'
        assert sha256(manifest_path.read_bytes()).hexdigest() == '5fc819f723f7263fe3d443ec780009a75aae66f2c35db8fe0bc3e3c50464eb84'
        entries = [row for row in json.loads(manifest_path.read_text(encoding='utf-8'))['files']
                   if '/doc-6/' in row['path'] or row['path'] == 'doc-6.pdf']
        source_relative = 'doc-6.pdf'
    else:
        source_relative = candidate['staged_copy']
        entries = [dict(path=source_relative, sha256=candidate['sha256'])]
    for entry in entries:
        source = safe_path(ROOT, entry['path'])
        assert source.stat().st_nlink == 1 and not source.is_symlink()
        assert sha256(source.read_bytes()).hexdigest() == entry['sha256']
        destination = copied / entry['path']
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        assert destination.stat().st_nlink == 1 and sha256(destination.read_bytes()).hexdigest() == entry['sha256']
    input_path = copied / source_relative
    source_sha = sha256(input_path.read_bytes()).hexdigest()
    doc = 'u-' + source_sha[:20]
    settings = builds.settings.model_copy(update={'build_runner': 'real', 'artifact_root': copied / 'artifacts'})
    core = Settings(_env_file=None, artifact_dir=settings.artifact_root, llm_transport='vertex',
                    vertex_project='dry-run-no-network', vertex_location='global')
    runtime = RealBuildRuntime(settings, builds.engine, core_settings=core)
    receipts, events, started, timings = [], [], {}, {}
    def progress(step, details):
        events.append({'step': step, 'status': details['status']})
        if details['status'] == 'started':
            started[step] = perf_counter()
        elif details['status'] == 'completed':
            timings[step] = perf_counter() - started.pop(step)
    try:
        pipeline = runtime.pipeline_factory(runtime.settings, allow_spend=False, phase_b_store=runtime.phase_b_store)
        result = BuildDocument(pipeline, runtime.pipeline_version, recorder=receipts.append).execute(
            input_path, doc, dry_run=True, progress=progress)
        from doc2roadmap.application.use_cases.label_chunk_roles import LabelChunkRoles
        role_plan = LabelChunkRoles(pipeline.store, pipeline._extractor(core.roadmap_model_id,
            temperature=0., max_output_tokens=16384), allow_spend=False).plan(doc).to_dict()
        reading = result.step_details['doc_reading']
        parsed = pipeline.store.load_parse(doc, reading['parse_version'])
        proof = {'book': book, 'source_sha256': source_sha, 'source_pages': 25 if book == 'doc-6' else candidate['page_count'],
                 'input_copy': str(input_path.relative_to(ROOT)), 'artifact_copy': str(settings.artifact_root.relative_to(ROOT)),
                 'copied_input_manifest': entries, 'web_doc_id': doc, 'result': result.to_dict(),
                 'collector_receipts': len(receipts), 'events': events, 'wall_seconds_by_completed_step': timings,
                 'label_roles_plan': role_plan, 'reader_config': parsed.manifest['config']['parser'],
                 'embedding_wait_seconds': None, 'embedding_wait_measured': False,
                 'model_calls_for_future_steps': 'unknown', 'future_usd_minutes_cap': 'unknown',
                 'provider_calls': 0, 'real_read_and_inspect': True, 'queued': False,
                 'sql_counts': {table: sql(builds, 'SELECT count(*) AS n FROM ' + table)[0]['n']
                                for table in ('build', 'build_attempt', 'course', 'usage_ledger', 'phase_b_cache')}}
        evidence('real-dry-run-' + book, proof)
        assert result.status == 'dry_run', result.to_dict()
        assert receipts == [result] and result.completed_steps == ['doc_reading']
        assert result.graph_version is None and result.model_calls == result.spent_usd == 0
        assert reading['page_count'] == proof['source_pages']
        assert all(value == 0 for value in proof['sql_counts'].values())
        assert result.step_details['dry_run']['cache_validated'] is False
        assert len([event for event in events if event['status'] == 'planned']) == 3
        assert all(sha256((copied / row['path']).read_bytes()).hexdigest() == row['sha256']
                   and sha256((ROOT / row['path']).read_bytes()).hexdigest() == row['sha256'] for row in entries)
        assert not list(copied.rglob('*.sqlite3')) and not list(copied.rglob('live.json'))
    finally:
        runtime.close()
