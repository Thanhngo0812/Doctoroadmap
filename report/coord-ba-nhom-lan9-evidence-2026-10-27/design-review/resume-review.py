"""Resume reviewer probes without changing worker/main or earlier evidence."""
from pathlib import Path
import hashlib
import json
import subprocess
import time
import xml.etree.ElementTree as ET

ROOT = Path('C:/Users/ngoco/Desktop/Doctoroadmap')
BASE = Path(__file__).parent
PIN = 'bda1366b8d033ce0dcf4660651959293c178f7c8'
PYTHON = str(ROOT / '.venv/Scripts/python.exe')
HTML = BASE / 'design/preview/w10_quiz_screens.html'
WORKER = ROOT / 'tmp/w24-figma-evidence'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
paths = ['scripts/test_w10_library_filter_vm.cjs', 'tests/unit/presentation/test_tokens_and_wcag.py', 'design/preview/w10_quiz_screens.html']
sources = []
for relative in paths:
    blob = subprocess.check_output(['git', 'show', f'{PIN}:{relative}'], cwd=ROOT)
    copy = (BASE / relative).read_bytes()
    worker = (WORKER / relative).read_bytes()
    assert blob.replace(b'\r\n', b'\n') == copy.replace(b'\r\n', b'\n') == worker.replace(b'\r\n', b'\n')
    sources.append({'path': relative, 'pinned_blob_sha256': sha(blob), 'scratch_sha256': sha(copy), 'worker_sha256': sha(worker), 'equal_normalized_LF': True})

def run(label, test):
    xml = BASE / 'runs' / (label + '.xml')
    log = BASE / 'runs' / (label + '.log')
    assert not xml.exists() and not log.exists()
    args = [PYTHON, 'scripts/w05_run_tests.py', '-o', 'addopts=', '-q', test, '--junitxml=' + str(xml)]
    start = time.monotonic()
    with log.open('w', encoding='utf-8') as stream:
        proc = subprocess.run(args, cwd=BASE, stdout=stream, stderr=stream)
    cases = list(ET.parse(xml).getroot().iter('testcase'))
    failures = [c for c in cases if c.find('failure') is not None]
    errors = [c for c in cases if c.find('error') is not None]
    record = {'label': label, 'source_commit': PIN, 'command': args, 'cwd': str(BASE), 'native_exit_code': proc.returncode, 'tests': len(cases), 'failures': len(failures), 'errors': len(errors), 'elapsed_seconds': round(time.monotonic() - start, 2)}
    (BASE / 'runs' / (label + '-exit.json')).write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(record), flush=True)
    return record, failures

baseline, _ = run('resume-baseline', 'tests/unit/presentation/test_tokens_and_wcag.py')
assert baseline['native_exit_code'] == 0 and baseline['tests'] == 64
raw = HTML.read_bytes()
worker_raw = (WORKER / 'design/preview/w10_quiz_screens.html').read_bytes()
mutant = raw
for old, new in [(b"filterLibrary('here', this)", b"filterLibrary('button', this)"), (b"filterLibrary('elsewhere', this)", b"filterLibrary('assistant', this)")]:
    assert mutant.count(old) == 1
    mutant = mutant.replace(old, new, 1)
try:
    HTML.write_bytes(mutant)
    red, failures = run('resume-actual-onclick-mutant', 'tests/unit/presentation/test_tokens_and_wcag.py::test_w10_library_filters_by_group_independent_of_origin')
    assert red['native_exit_code'] == 1 and red['failures'] == 1 and red['errors'] == 0
    assert 'AssertionError' in failures[0].find('failure').text
finally:
    HTML.write_bytes(raw)
    assert sha(HTML.read_bytes()) == sha(raw)
    assert (WORKER / 'design/preview/w10_quiz_screens.html').read_bytes() == worker_raw
restored, _ = run('resume-restored', 'tests/unit/presentation/test_tokens_and_wcag.py')
assert restored['native_exit_code'] == 0 and restored['tests'] == 64
proof = {'source_commit': PIN, 'sources': sources, 'baseline': baseline, 'mutation': red, 'restored': restored, 'scratch_html_original_sha256': sha(raw), 'scratch_html_mutant_sha256': sha(mutant), 'scratch_html_restored_sha256': sha(HTML.read_bytes()), 'worker_html_unchanged': True, 'external_spend_usd': 0, 'postgres_runs': 0}
(BASE / 'resume-verification.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
