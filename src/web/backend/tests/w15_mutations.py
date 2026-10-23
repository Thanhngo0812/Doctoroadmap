"""Sequential W-15 and W-25 mutations; assertions must fail and bytes be restored."""
import hashlib
import json
import os
import subprocess
import sys
from uuid import uuid4
import xml.etree.ElementTree as ET

from w25_mutations import CASES as W25_CASES, PACKAGE, ROOT

TEST = 'src/web/backend/tests/test_real_build_w15.py'
W25_LABELS = {'confirm-cancel', 'terminal-cancel', 'media-cancel', 'receipt-once', 'cancel-mail', 'terminal-row-lock'}
CASES = [case for case in W25_CASES if case[0] in W25_LABELS] + [
    ('real-transport', 'infrastructure/real_build.py',
     "if core.llm_transport != 'vertex' or not core.vertex_project or not core.vertex_location:",
     'if False:', 'transport_validation', TEST),
    ('required-core-port', 'infrastructure/real_build.py',
     "if 'phase_b_store' not in signature(factory).parameters:", 'if False:', 'default_requires_core_port', TEST),
    ('same-postgres', 'infrastructure/real_build.py',
     "if settings.database_url and make_url(settings.database_url).set(drivername='postgresql+psycopg') != engine.url:",
     'if False:', 'different_database_engine', TEST),
    ('usage-baseline', 'infrastructure/real_build.py',
     'BuildDocument._set_usage_delta(snapshot, before, pipeline.usage())',
     'BuildDocument._set_usage_delta(snapshot, {key: 0 for key in before}, pipeline.usage())', 'cumulative_usage', TEST),
    ('usage-precision', 'infrastructure/real_build.py',
     'result.spent_usd = round(result.spent_usd, 6)', 'result.spent_usd = result.spent_usd', 'cumulative_usage', TEST),
    ('step-clock', 'infrastructure/real_build.py',
     "'wall_seconds': max(0., runtime.monotonic() - started.pop(step))", "'wall_seconds': 0.", 'cumulative_usage', TEST),
    ('no-queued-dry-run', 'infrastructure/real_build.py', 'if dry_run:', 'if False:', 'rejects_dry_run', TEST),
    ('api-version', 'composition.py', "version = real_pipeline_version(settings, core_settings)",
     "version = 'web-fake-v1'", 'cumulative_usage', TEST),
    ('trace-not-billed', 'infrastructure/phase_b_store.py',
     'if value.get("counted_in") == "build":', 'if False:', 'trace_keeps_raw_usage or only_build_charge', TEST),
]


def main():
    batch = sys.argv[1] if len(sys.argv) > 1 else ''
    output = ROOT / 'report/w15-evidence/mutations' / batch
    output.mkdir(parents=True, exist_ok=True)
    records = []
    run_id = uuid4().hex[:8]
    for label, relative, old, new, selection, test in CASES:
        path = PACKAGE / relative
        original = path.read_bytes()
        source = original.decode('utf-8')
        assert old in source, (label, 'missing mutation target')
        xml = output / (label + '.xml')
        command = [sys.executable, str(ROOT / 'scripts/w05_run_tests.py'), test, '-k', selection,
                   '-o', 'addopts=', '-q', '--tb=short', '--basetemp=tmp/w15-mut-' + run_id + '-' + label,
                   '--junitxml=' + str(xml)]
        try:
            path.write_bytes(source.replace(old, new).encode('utf-8'))
            process = subprocess.run(command, cwd=ROOT, capture_output=True, encoding='utf-8', errors='replace',
                                     env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1',
                                          'W25_EVIDENCE_RUN': 'w15-mutation-' + (batch + '-' if batch else '') + label,
                                          'W15_EVIDENCE_RUN': 'mutation-' + (batch + '-' if batch else '') + label})
            (output / (label + '.log')).write_bytes((process.stdout + process.stderr).encode('utf-8'))
            tree = ET.parse(xml)
            failures, errors = tree.findall('.//testcase/failure'), tree.findall('.//testcase/error')
            assertions = sum(any(word in (f.text or '') for word in ('AssertionError', 'assert ', 'DID NOT RAISE', 'Failed: confirmation must reject')) for f in failures)
            record = {'label': label, 'exit_code': process.returncode, 'failures': len(failures),
                      'assertion_failures': assertions, 'setup_errors': len(errors), 'command': command[2:],
                      'original_sha256': hashlib.sha256(original).hexdigest()}
            assert process.returncode == 1 and assertions and not errors, record
        finally:
            path.write_bytes(original)
            assert path.read_bytes() == original
        record['source_restored'] = True
        records.append(record)
        (output / 'mutations.json').write_bytes((json.dumps(records, indent=2) + '\n').encode())
        print(label + ': caught and restored', flush=True)


if __name__ == '__main__':
    main()
