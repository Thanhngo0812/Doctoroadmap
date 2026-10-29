"""Claude's independent W-17.2 mutations (r15). Each mutant runs the whole W-26 test file; bytes restored, SHA checked."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
B = ROOT / 'src/web/backend/wayfinder'
TEST = 'src/web/backend/tests/test_w17_builds_samples.py'
OUT = Path(sys.argv[1]).resolve()
ONLY = set(sys.argv[2:])


MUTANTS = [
    ('q-email', 'infrastructure/admin_store.py', ' OR strpos(a.email_normalized,:q)>0', ''),
    ('q-build-id', 'infrastructure/admin_store.py', ' OR CAST(b.id AS text)=:q', ''),
    ('course-count-all', 'infrastructure/admin_store.py', '(SELECT count(*) FROM course c WHERE c.build_id=b.id)', '(SELECT count(*) FROM course c)'),
    ('error-always', 'application/admin.py', "'retryable': row['retryable']} if code else None),", "'retryable': row['retryable']} if True else None),"),
    ('unset-conflict', 'application/admin.py', "if is_sample and not course['is_sample'] and self.store.other_sample_exists(",
     "if not course['is_sample'] and self.store.other_sample_exists("),
    ('unset-action-name', 'application/admin.py', "'admin_course_sample_set' if is_sample else 'admin_course_sample_unset'", "'admin_course_sample_set'"),
    ('since-before-until', 'application/admin.py', 'if since is not None and until is not None and since >= until:', 'if False:'),
    ('requester-null', 'application/admin.py', "{'user_id': row['requester_id'], 'email': row['requester_email']} if row['requester_id'] else None", 'None'),
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
                                  '--tb=line', '-p', 'no:warnings', '--basetemp=tmp/r15-mut-' + label,
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
