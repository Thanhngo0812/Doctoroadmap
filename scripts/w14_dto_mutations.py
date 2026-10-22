"""Exercise the two W14 DTO guards serially and restore exact source bytes."""
from hashlib import sha256
import json
from pathlib import Path
import socket
import subprocess
import sys
from uuid import uuid4
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'report/w14-react-evidence/final-main-2026-10-22/dto-mutations'
CASES = (
    ('upload-context', "'upload_id':upload.get('id')", "'upload_id':job['upload_id']",
     'test_build_cards_expose_only_the_viewers_upload_for_the_course'),
    ('confirmation', "'confirmed_at':upload['confirmed_at']", "'confirmed_at':None",
     'test_reused_queued_upload_has_its_own_confirmation_and_title'),
)


def main():
    with socket.socket() as probe:
        if probe.connect_ex(('127.0.0.1', 8014)) == 0:
            raise RuntimeError('Stop W14 server before mutation')
    OUTPUT.mkdir(parents=True, exist_ok=True)
    source = ROOT / 'src/web/backend/wayfinder/application/builds.py'
    results = []
    for name, old, new, test in CASES:
        original = source.read_bytes()
        content = original.decode('utf-8')
        assert content.count(old) == 1
        junit = OUTPUT / f'{name}.xml'
        command = [sys.executable, 'scripts/w05_run_tests.py', '-o', 'addopts=', '-q',
                   f'src/web/backend/tests/test_builds_w14.py::{test}',
                   f'--basetemp=tmp/w14-dto-{name}-{uuid4().hex}', f'--junitxml={junit}']
        try:
            source.write_bytes(content.replace(old, new).encode('utf-8'))
            run = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=180)
            (OUTPUT / f'{name}.log').write_bytes(run.stdout + run.stderr)
            suites = ET.parse(junit).getroot()
            failures = suites.findall('.//testcase/failure')
            errors = suites.findall('.//testcase/error')
            assert run.returncode == 1 and failures and not errors, name
            results.append(dict(name=name, command=command, native_exit_code=run.returncode,
                                assertion_failures=len(failures), errors=len(errors),
                                original_sha256=sha256(original).hexdigest()))
        finally:
            source.write_bytes(original)
            assert source.read_bytes() == original
        results[-1]['restored_sha256'] = sha256(source.read_bytes()).hexdigest()
    (OUTPUT / 'results.json').write_text(json.dumps(results, indent=2)+'\n', encoding='utf-8')
    print('2 DTO mutations caught; source restored byte-for-byte')


if __name__ == '__main__':
    main()
