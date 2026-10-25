"""Sequential counterexamples; always restore exact bytes before integration checks."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / 'mutations'
OUT.mkdir(exist_ok=True)
ui = ROOT / 'src/web/frontend/src/useAssistant.ts'
backend = ROOT / 'src/web/backend/wayfinder/infrastructure/learning_runtime.py'
source_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
originals = {p: p.read_bytes() for p in (ui, backend)}
cases = [
    ('terminal-lock', ui, 'if (active.current && !active.current.terminal) return;', 'if (active.current) return;'),
    ('old-usage', ui, 'if (!controller.signal.aborted && active.current === request) setUsage(amount);',
     'if (!controller.signal.aborted) setUsage(amount);'),
    ('old-finally', ui,
     'if (active.current === request) {\n        active.current = null;\n        if (!controller.signal.aborted) setLive(value => value && ({ ...value, busy: false }));\n      }',
     'if (active.current === request) active.current = null;\n      if (!controller.signal.aborted) setLive(value => value && ({ ...value, busy: false }));'),
    ('forced-cache', backend,
     "owner=kwargs.get('owner'), cache_only=kwargs.get('cache_only', False),\n                allow_spend=kwargs.get('allow_spend', False))",
     "owner=kwargs.get('owner'), cache_only=True)"),
]
receipts = []
for name, path, old, new in cases:
    raw = originals[path]
    source = raw.decode('utf8').replace('\r\n', '\n')
    assert source.count(old) == 1, name
    changed = source.replace(old, new).encode('utf8')
    path.write_bytes(changed)
    xml = OUT / (name + '.xml')
    if path == ui:
        command = [shutil.which('node'), str(ROOT / 'src/web/frontend/node_modules/vitest/vitest.mjs'),
            'run', '--pool=threads', '--maxWorkers=1', 'src/Assistant.final-usage-race.test.tsx',
            '--reporter=junit', '--outputFile=' + str(xml)]
        cwd = ROOT / 'src/web/frontend'
    else:
        command = [sys.executable, str(ROOT / 'scripts/w05_run_tests.py'), '-o', 'addopts=', '-q',
            'src/web/backend/tests/test_assistant_lecture_forwarding_w09.py',
            '--basetemp=tmp/cong-w09-mut-' + name + '-20261025', '--junitxml=' + str(xml)]
        cwd = ROOT
    try:
        with (OUT / (name + '.log')).open('wb') as log:
            result = subprocess.run(command, cwd=cwd, stdout=log, stderr=subprocess.STDOUT)
    finally:
        path.write_bytes(raw)
        assert path.read_bytes() == raw
    suite = ET.parse(xml).getroot()
    failures = sum(int(s.attrib.get('failures', 0)) for s in suite.findall('testsuite'))
    errors = sum(int(s.attrib.get('errors', 0)) for s in suite.findall('testsuite'))
    row = dict(name=name, sourceCommit=source_commit, path=path.relative_to(ROOT).as_posix(), command=command,
        nativeExit=result.returncode, failures=failures, errors=errors,
        originalSha256=hashlib.sha256(raw).hexdigest(), mutatedSha256=hashlib.sha256(changed).hexdigest(),
        restoredSha256=hashlib.sha256(path.read_bytes()).hexdigest())
    receipts.append(row)
    (OUT / 'receipts.json').write_text(json.dumps(receipts, indent=2) + '\n', encoding='utf8')
    assert result.returncode != 0 and failures > 0 and errors == 0, row
    print(name, 'caught:', failures, 'assertion failures; source restored', flush=True)
assert all(p.read_bytes() == value for p, value in originals.items())
