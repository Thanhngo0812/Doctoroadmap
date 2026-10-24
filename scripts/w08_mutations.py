"""Serial counterexamples; no browser/full gate may run until exact source restoration."""
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'report/w08-evidence' / os.environ.get('W08_MUTATION_RUN', 'mutations')
assert OUT.parent == ROOT / 'report/w08-evidence' and OUT.name.startswith('mutations')
BACK = 'src/web/backend/'
FRONT = 'src/web/frontend/src/'
CASES = (
    ('cache-only', BACK + 'wayfinder/application/learning_gateway.py',
     'test_lecture3_integration_w08.py::test_w08_real_lecture3_cache_validation_stays_private_and_status_is_per_learner',
     'owner=actor.user_id, cache_only=True', 'owner=actor.user_id, cache_only=False'),
    ('learner-status', BACK + 'wayfinder/application/lecture_view.py',
     'test_lecture3_integration_w08.py::test_w08_real_lecture3_cache_validation_stays_private_and_status_is_per_learner',
     "return progress.get(node_id, {}).get('state', 'not_learned')", "return 'not_learned'"),
    ('node-guard', BACK + 'wayfinder/application/learning_gateway.py',
     'test_lectures_w08.py::test_w08_node_must_be_in_published_learnable_graph',
     "if node_id not in graph.learnable_nodes:\n            raise WebError('not_found', 'Không tìm thấy nội dung yêu cầu')", 'if False:\n            pass'),
    ('page-range', BACK + 'wayfinder/infrastructure/learning_media.py',
     'test_lectures_w08.py::test_w08_private_source_page_headers_range_and_lazy_media_are_real_postgres',
     "or not 1 <= page <= source['page_count']", 'or False'),
    ('http-dto-privacy', BACK + 'wayfinder/api/learning.py',
     'test_lecture3_integration_w08.py::test_w08_http_dto_discards_admin_keys_even_if_a_gateway_returns_them',
     "response_model=LectureView", 'response_model=None'),
    ('sse-membership', BACK + 'wayfinder/api/learning.py',
     'test_lectures_w08.py::test_w08_private_source_page_headers_range_and_lazy_media_are_real_postgres',
     'await run_in_threadpool(gateway.lecture_context, actor, cid, node_id)', 'pass  # deliberately omit pre-SSE authorization'),
    ('early-delta', BACK + 'wayfinder/api/learning.py',
     'test_lecture3_integration_w08.py::test_w08_first_delta_precedes_model_finish_and_cache_is_completed_after_http_disconnect',
     "if not disconnected.is_set():", "if event is None or event.get('event') != 'delta':"),
    ('cross-site', BACK + 'wayfinder/api/learning.py',
     'test_lecture3_integration_w08.py::test_w08_cross_site_navigation_cannot_start_a_paid_generation',
     "if (request.headers.get('sec-fetch-site') == 'cross-site'\n                or origin and origin not in request.app.state.settings.allowed_origins):", "if False:"),
    ('rollback', FRONT + 'Learning.tsx', 'Learning.test.tsx',
     '[nodeId]: previous', "[nodeId]: { state: learned ? 'learned' : 'not_learned', source: 'learner', updated_at: null }"),
    ('late-error-keeps-text', FRONT + 'Learning.tsx', 'Learning.test.tsx',
     "\n      if (accumulated.trim() && latest) accept", "\n      if (false && accumulated.trim() && latest) accept"),
    ('always-retry', FRONT + 'Learning.tsx', 'Learning.test.tsx',
     '<button className="button button-primary" type="button" onClick={() => setAttempt(value => value + 1)}>Thử lại</button>',
     '{failure.retryable && <button className="button button-primary" type="button" onClick={() => setAttempt(value => value + 1)}>Thử lại</button>}'),
    ('safe-math', FRONT + 'LectureMarkdown.tsx', 'LectureMarkdown.test.tsx', 'trust: false', 'trust: true'),
    ('source-page-identity', FRONT + 'SourceViewer.tsx', 'SourceViewer.test.tsx',
     'image?.page === page ? <img', 'image ? <img'),
    ('live-related-progress', FRONT + 'Learning.tsx', 'Learning.review-repro.test.tsx',
     'progress={data.progress.nodes}', 'progress={{}}'),
    ('self-check-heading-grammar', FRONT + 'Learning.tsx', 'Learning.review-repro.test.tsx',
     'split(/^[ \\t]*#{2,4}[ \\t]*Tự kiểm tra[ \\t:]*$/im)', 'split(/^###\\s+Tự kiểm tra\\s*$/im)'),
)


def main():
    assert not OUT.exists(), 'Retain prior evidence; use a new output for a new mutation round'
    OUT.mkdir(parents=True)
    results = []
    for name, relative, test, old, new in CASES:
        source = ROOT / relative
        original = source.read_bytes(); content = original.decode('utf-8').replace('\r\n', '\n')
        assert content.count(old) == 1, (name, content.count(old))
        xml = OUT / (name + '.xml')
        if relative.startswith(BACK):
            command = [sys.executable, 'scripts/w05_run_tests.py', '-o', 'addopts=', '-q',
                BACK + 'tests/' + test, '--basetemp=tmp/w08-mut-' + name + '-' + uuid4().hex, '--junitxml=' + str(xml)]
        else:
            command = ['npm.cmd', '--prefix', 'src/web/frontend', 'test', '--', 'src/' + test,
                '--pool=threads', '--maxWorkers=1', '--reporter=junit', '--outputFile=' + str(xml)]
        row = {'name': name, 'source': relative, 'command': command, 'beforeSha256': sha256(original).hexdigest()}
        try:
            source.write_bytes(content.replace(old, new).encode('utf-8'))
            run = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=180)
            (OUT / (name + '.log')).write_bytes(run.stdout + run.stderr)
            suite = ET.parse(xml).getroot()
            failures = suite.findall('.//testcase/failure'); errors = suite.findall('.//testcase/error')
            row.update(nativeExit=run.returncode, failures=len(failures), errors=len(errors))
            assert run.returncode == 1 and failures and not errors, row
        finally:
            source.write_bytes(original)
            assert source.read_bytes() == original
            row['restoredSha256'] = sha256(source.read_bytes()).hexdigest()
            results.append(row)
            (OUT / 'results.json').write_bytes((json.dumps(results, indent=2) + '\n').encode())
        print(name + ': caught; restored', flush=True)
    print(str(len(results)) + ' counterexamples caught; exact source restored', flush=True)


if __name__ == '__main__': main()
