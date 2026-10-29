"""Claude's independent W-26 mutations (r14). Each mutant runs the whole W-26 test file; bytes restored, SHA checked."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
B = ROOT / 'src/web/backend/wayfinder'
TEST = 'src/web/backend/tests/test_demo_local_w26.py'
OUT = Path(sys.argv[1]).resolve()
ONLY = set(sys.argv[2:])

MUTANTS = [
    ('base-url', 'demo_local.py', 'artifact_root=artifact_root, public_base_url=origin, allowed_origins=origins,',
     'artifact_root=artifact_root, allowed_origins=origins,'),
    ('admin-once', 'demo_local.py', '    if PostgresAuthStore(engine).has_admins():\n        return False',
     '    if False:\n        return False'),
    ('limit-zero', 'demo_local.py', 'if limit <= 0:', 'if limit < 0:'),
    ('upload-raw-any', 'infrastructure/disk_media.py',
     "if resource_type not in {'image', 'raw'} or resource_type == 'raw' and extension != '.docx':",
     "if resource_type not in {'image', 'raw'}:"),
    ('no-localhost-origin', 'demo_local.py',
     "origins = [origin] + ([f'http://localhost:{port}'] if host == '127.0.0.1' else [])", 'origins = [origin]'),
    ('learner-default-3', 'settings.py', 'learner_daily_max_usd: float = Field(default=1.0, gt=0)',
     'learner_daily_max_usd: float = Field(default=3.0, gt=0)'),
    ('child-not-stopped', 'demo_local.py', '            child.terminate()\n', ''),
]

OUT.mkdir(parents=True, exist_ok=True)
records = []
for label, rel, old, new in MUTANTS:
    if ONLY and label not in ONLY:
        continue
    path = B / rel
    original = path.read_bytes()
    digest = sha256(original).hexdigest()
    text = original.decode('utf-8').replace('\r\n', '\n')
    assert text.count(old) == 1, (label, text.count(old))
    xml = OUT / (label + '.xml')
    try:
        path.write_bytes(text.replace(old, new).replace('\n', '\r\n').encode('utf-8'))
        process = subprocess.run([sys.executable, str(ROOT / 'scripts/w05_run_tests.py'), TEST, '-o', 'addopts=', '-q',
                                  '--tb=line', '-p', 'no:warnings', '--basetemp=tmp/r14-mut-' + label,
                                  '--junitxml=' + str(xml)], cwd=ROOT, capture_output=True, encoding='utf-8',
                                 errors='replace', timeout=1800)
    finally:
        path.write_bytes(original)
    assert sha256(path.read_bytes()).hexdigest() == digest, label
    (OUT / (label + '.log')).write_bytes((process.stdout + process.stderr).encode('utf-8'))
    tail = (process.stdout.strip().splitlines() or [''])[-1]
    records.append({'mutant': label, 'file': rel, 'exit': process.returncode, 'killed': process.returncode != 0,
                    'summary': tail})
    print(label, 'KILLED' if process.returncode else 'SURVIVED', tail, flush=True)
(OUT / 'mutations.json').write_bytes((json.dumps(records, indent=2, ensure_ascii=False) + '\n').encode('utf-8'))
