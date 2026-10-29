"""Sequential W-17.2 mutations; each must fail an assertion (not a setup error) and the bytes are restored.

Usage: python w17_2_mutations.py <batch-name> [label ...]
"""
import hashlib
import json
import os
import subprocess
import sys
from uuid import uuid4
import xml.etree.ElementTree as ET

from w14_mutations import PACKAGE, ROOT

TEST = 'src/web/backend/tests/test_w17_builds_samples.py'
SERVICE = 'application/admin.py'
STORE = 'infrastructure/admin_store.py'
API = 'api/admin.py'
LIST = "limit=50, offset=0):\n        self.authorize(actor)\n        self._page(limit, offset)\n        if not isinstance(q"
FLAG = "def set_sample_course(self, actor, cid, is_sample, *, ip=None):\n        self.authorize(actor)\n"
INNER = "with self.store.atomic(['admin:samples']):\n            self.authorize(actor)\n"
# (label, [(file, old, new), ...]); every `old` must occur exactly once in its file.
CASES = [
    ('list-no-admin-service', [(SERVICE, LIST, LIST.replace('        self.authorize(actor)\n', '', 1))]),
    ('list-no-admin-anywhere', [(SERVICE, LIST, LIST.replace('        self.authorize(actor)\n', '', 1)),
        (API, "def builds(request: Request, admin=Depends(service), actor", "def builds(request: Request, admin=Depends(lambda request: request.app.state.services.admin), actor")]),
    ('flag-no-admin-service', [(SERVICE, FLAG, FLAG.replace('        self.authorize(actor)\n', '', 1)),
        (SERVICE, INNER, INNER.replace('            self.authorize(actor)\n', '', 1))]),
    ('flag-no-first-admin-check', [(SERVICE, FLAG, FLAG.replace('        self.authorize(actor)\n', '', 1))]),
    ('flag-no-recheck-in-lock', [(SERVICE, INNER, INNER.replace('            self.authorize(actor)\n', '', 1))]),
    ('no-allowlist', [(SERVICE, "if course['doc_id'] not in SAMPLE_DOCS:", 'if False:')]),
    ('no-env-check', [(SERVICE, "if self.settings.env != 'dev':", 'if False:')]),
    ('no-duplicate-guard', [(SERVICE, "if is_sample and not course['is_sample'] and self.store.other_sample_exists(",
        "if False and self.store.other_sample_exists(")]),
    ('no-advisory-lock', [(SERVICE, "with self.store.atomic(['admin:samples']):", 'with self.store.atomic([]):')]),
    ('no-row-lock', [(STORE, "'FROM course WHERE id=:cid FOR UPDATE'", "'FROM course WHERE id=:cid'")]),
    ('audit-always', [(SERVICE, "if course['is_sample'] != is_sample:", 'if True:')]),
    ('audit-outside-transaction', [
        (STORE, "'FROM course WHERE id=:cid FOR UPDATE'), dict(cid=cid))", "'FROM course WHERE id=:cid'), dict(cid=cid))"),
        (STORE, "def set_course_sample(self, cid, is_sample, at):\n        with self._use_connection(write=True) as conn:",
         "def set_course_sample(self, cid, is_sample, at):\n        with self.engine.begin() as conn:")]),
    ('flag-not-strict-bool', [(API, "is_sample: StrictBool", 'is_sample: bool')]),
    ('dto-error-message-raw', [
        (STORE, "b.error_code,b.retryable,", "b.error_code,b.error_message,b.retryable,"),
        (SERVICE, "'message': BUILD_ERROR_MESSAGES.get(code, 'Mã lỗi không nhận diện được'),", "'message': row['error_message'],")]),
    ('dto-unknown-code-passthrough', [(SERVICE, "'code': code if code in BUILD_ERROR_MESSAGES else 'khong_ro',", "'code': code,")]),
    ('dto-no-response-model', [(API, "@router.get('/builds',response_model=AdminBuildsResponse)", "@router.get('/builds')")]),
    ('until-inclusive', [(STORE, "b.created_at<:until", "b.created_at<=:until")]),
    ('since-exclusive', [(STORE, "b.created_at>=:since", "b.created_at>:since")]),
    ('search-like-wildcard', [(STORE, "strpos(lower(b.doc_id),:q)>0", "lower(b.doc_id) LIKE '%'||:q||'%'")]),
    ('search-case-sensitive', [(SERVICE, "q=q.strip().lower()", "q=q.strip()")]),
    ('total-ignores-filters', [(STORE, "text('SELECT count(*)' + join + where)", "text('SELECT count(*)' + join.replace(' WHERE ', ' WHERE true OR '))")]),
    ('order-ascending', [(STORE, "ORDER BY b.created_at DESC,b.id LIMIT", "ORDER BY b.created_at,b.id LIMIT")]),
    ('offset-ignored', [(STORE, "ORDER BY b.created_at DESC,b.id LIMIT :limit OFFSET :offset", "ORDER BY b.created_at DESC,b.id LIMIT :limit")]),
    ('status-filter-ignored', [(STORE, "b.status=:status)'", "true)'")]),
    ('usage-filter-ignored', [(STORE, "b.usage_complete=:usage_complete)'", "true)'")]),
    ('naive-since-allowed', [(SERVICE, "        for field, value in (('since', since), ('until', until)):\n            if value is not None and (value.tzinfo is None or value.utcoffset() is None):\n                self._invalid(field)\n        if since is not None and until is not None and since >= until:\n            self._invalid('until')\n        page = self.store.list_builds(",
        "        page = self.store.list_builds(")]),
]


def main():
    batch = sys.argv[1] if len(sys.argv) > 1 else 'run'
    output = ROOT / 'report/w17-2-evidence/mutations' / batch
    output.mkdir(parents=True, exist_ok=True)
    only = set(sys.argv[2:])
    records = []
    run_id = uuid4().hex[:8]
    for label, edits in CASES:
        if only and label not in only:
            continue
        originals = {}
        xml = output / (label + '.xml')
        try:
            for relative, old, new in edits:
                path = PACKAGE / relative
                originals.setdefault(path, path.read_bytes())
            for relative, old, new in edits:
                path = PACKAGE / relative
                source = path.read_bytes().decode('utf-8')
                crlf = '\r\n' in source
                source = source.replace('\r\n', '\n')
                assert source.count(old) == 1, (label, relative, 'mutation target must occur exactly once', source.count(old))
                source = source.replace(old, new)
                path.write_bytes((source.replace('\n', '\r\n') if crlf else source).encode('utf-8'))
            command = [sys.executable, str(ROOT / 'scripts/w05_run_tests.py'), TEST, '-o', 'addopts=', '-q',
                       '--tb=short', '-p', 'no:warnings', '--basetemp=tmp/w172-mut-' + run_id + '-' + label,
                       '--junitxml=' + str(xml)]
            process = subprocess.run(command, cwd=ROOT, capture_output=True, encoding='utf-8', errors='replace',
                                     env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
            (output / (label + '.log')).write_bytes((process.stdout + process.stderr).encode('utf-8'))
            tree = ET.parse(xml)
            failures, errors = tree.findall('.//testcase/failure'), tree.findall('.//testcase/error')
            names = sorted({case.get('name') for case in tree.findall('.//testcase') if case.find('failure') is not None})
            assertions = sum(any(word in (f.text or '') for word in ('AssertionError', 'assert ', 'DID NOT RAISE', 'Failed:'))
                             for f in failures)
            record = {'label': label, 'exit_code': process.returncode, 'failures': len(failures), 'caught_by': names,
                      'assertion_failures': assertions, 'setup_errors': len(errors),
                      'original_sha256': {p.name: hashlib.sha256(b).hexdigest() for p, b in originals.items()}}
            record['caught'] = process.returncode == 1 and assertions > 0 and not errors
        finally:
            for path, original in originals.items():
                path.write_bytes(original)
                assert path.read_bytes() == original
        record['source_restored'] = True
        records.append(record)
        (output / 'mutations.json').write_bytes((json.dumps(records, indent=2) + '\n').encode())
        print(label + (': caught by ' if record['caught'] else ': NOT CLEAN (survived or setup error) ') + ', '.join(names), flush=True)


if __name__ == '__main__':
    main()
