"""Keep W-14 mutations and falsify W-25 guards sequentially, restoring exact bytes."""
import hashlib
import json
import os
import subprocess
import sys
from uuid import uuid4
import xml.etree.ElementTree as ET

from w14_mutations import CASES, PACKAGE, ROOT, TEST

NEW_TEST = 'src/web/backend/tests/test_build_cancellation_w25.py'
CASES = [(label, path, old, new, selection, TEST) for label, path, old, new, selection in CASES] + [
    ('confirm-cancel', 'application/builds.py',
     "WHERE id=:id AND status='awaiting_confirmation' AND NOT cancel_requested RETURNING id",
     'WHERE id=:id RETURNING id', 'before_confirmation_queue', NEW_TEST),
    ('terminal-cancel', 'infrastructure/build_store.py',
     "if result and active and job['cancel_requested']:", 'if False:', 'preserves_receipt', NEW_TEST),
    ('media-cancel', 'application/build_worker.py',
     "if current['cancel_requested']:", 'if False:', 'preserves_receipt', NEW_TEST),
    ('receipt-once', 'infrastructure/build_store.py',
     "if attempt is None or attempt['result'] is not None: return False",
     'if attempt is None: return False', 'preserves_receipt', NEW_TEST),
    ('cancel-mail', 'application/build_worker.py',
     "if accepted and result.status in {'succeeded','failed','rejected'}:",
     'if accepted:', 'preserves_receipt', NEW_TEST),
]


def main():
    output = ROOT / 'report/w25-evidence/mutations'
    output.mkdir(parents=True, exist_ok=True)
    records = []
    run_id = uuid4().hex[:8]
    for label, relative, old, new, selection, test in CASES:
        path = PACKAGE / relative
        original = path.read_bytes()
        source = original.decode('utf-8')
        assert old in source, (label, 'mutation target missing')
        xml = output / (label + '.xml')
        command = [sys.executable, str(ROOT / 'scripts/w05_run_tests.py'), test, '-k', selection,
                   '-o', 'addopts=', '-q', '--tb=short', '--basetemp=tmp/w25-mut-' + run_id + '-' + label,
                   '--junitxml=' + str(xml)]
        try:
            path.write_bytes(source.replace(old, new).encode('utf-8'))
            process = subprocess.run(command, cwd=ROOT, capture_output=True, encoding='utf-8', errors='replace',
                                     env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'W25_EVIDENCE_RUN': 'mutation-' + label})
            (output / (label + '.log')).write_text(process.stdout + process.stderr, encoding='utf-8')
            tree = ET.parse(xml)
            failures, errors = tree.findall('.//testcase/failure'), tree.findall('.//testcase/error')
            record = {'label': label, 'exit_code': process.returncode, 'failures': len(failures),
                      'assertion_failures': sum('AssertionError' in (failure.text or '') or 'assert ' in (failure.text or '')
                                               or 'Failed: confirmation must reject' in (failure.text or '') for failure in failures),
                      'setup_errors': len(errors), 'command': command[2:],
                      'original_sha256': hashlib.sha256(original).hexdigest()}
            assert process.returncode == 1 and record['assertion_failures'] and not errors, record
        finally:
            path.write_bytes(original)
            assert path.read_bytes() == original
        record['source_restored'] = True
        records.append(record)
        (output / 'mutations.json').write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
        print(label + ': caught and restored', flush=True)


if __name__ == '__main__':
    main()
