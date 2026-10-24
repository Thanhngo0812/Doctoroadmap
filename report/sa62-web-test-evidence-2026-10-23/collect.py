import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path('C:/Users/ngoco/Desktop/Doctoroadmap')
RUN = Path(__file__).parent
WT = ROOT / 'tmp/sa62-port-kho-pha-b'
OUT = WT / 'report/sa62-web-test-evidence-2026-10-23'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def counts(data):
    tree = ET.fromstring(data)
    return {name: len(tree.findall(query)) for name, query in
            [('tests', './/testcase'), ('failures', './/testcase/failure'), ('errors', './/testcase/error'), ('skipped', './/testcase/skipped')]}


for label in ['full', 'react', 'build', 'full-postmerge', 'react-postmerge', 'build-postmerge']:
    assert json.loads((RUN / (label + '-exit.json')).read_bytes())['native_exit_code'] == 0
planned = [(path, path.name) for path in RUN.iterdir() if path.is_file() and path.suffix in {'.json', '.xml', '.log', '.py'}]
planned.append((WT / 'report/w06-evidence/fixture-copy.json', 'fixture-copy-manifest.json'))
sql = WT / 'report/w15-evidence/sql/sa62-web-full-20261023'
for name in ['single-build-charge.json', 'trace-build.json', 'children.json']:
    planned.append((sql / name, 'sql/' + name))
    planned.append((WT / 'report/w15-evidence/sql/sa62-postmerge-20261023' / name, 'sql-postmerge/' + name))
OUT.mkdir(parents=True, exist_ok=True)
normalization = []
for path, relative in planned:
    raw = path.read_bytes()
    data = ('\n'.join(line.rstrip() for line in raw.decode('utf-8').replace('\r\n', '\n').splitlines()).rstrip('\n') + '\n').encode('utf-8')
    if path.suffix == '.json':
        assert json.loads(raw) == json.loads(data), relative
    if path.suffix == '.xml':
        assert counts(raw) == counts(data), relative
    target = OUT / relative
    assert not target.exists(), target
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    normalization.append({'path': relative, 'raw_sha256': digest(raw), 'archived_sha256': digest(data), 'changed': raw != data})
commit = 'ce5f581a685754f2c8bcc93664047dd159ad5eb7'
paths = ['src/web/backend/tests/test_real_build_w15.py', 'src/web/backend/wayfinder/infrastructure/real_build.py',
         'src/web/backend/wayfinder/infrastructure/phase_b_store.py', 'src/doc2roadmap/composition_build.py',
         'src/doc2roadmap/composition_phase_b.py']
hashes = {path: digest(subprocess.check_output(['git', 'show', commit + ':' + path], cwd=WT)) for path in paths}
postmerge = '14110c0e5a49aa2395b5f3be5555ca7c002315a0'
postmerge_hashes = {path: digest(subprocess.check_output(['git', 'show', postmerge + ':' + path], cwd=WT)) for path in paths}
summary = {'tested_commit': commit, 'received_main': 'ecd98c25b2038a853252b7fe123317699b0a9014',
           'source_blob_sha256': hashes, 'python': counts((RUN / 'full.xml').read_bytes()),
           'react': counts((RUN / 'react.xml').read_bytes()), 'focused': counts((RUN / 'focused-green.xml').read_bytes()),
           'injection_red': counts((RUN / 'injection-red.xml').read_bytes()),
           'postmerge_verified_commit': postmerge, 'postmerge_source_blob_sha256': postmerge_hashes,
           'postmerge_python': counts((RUN / 'full-postmerge.xml').read_bytes()),
           'postmerge_react': counts((RUN / 'react-postmerge.xml').read_bytes()),
           'merge_commit': '9ac2a852d59a1495d1da624ea69eec87f1e0c4ec',
           'external_spend_usd': 0, 'full_w15_complete': False, 'sa62_merged_by_codex': True, 'links_used': False}
for name, value in [('summary.json', summary), ('normalization.json', normalization)]:
    (OUT / name).write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
(OUT / '.gitattributes').write_bytes(b'* -text\n')
files = [{'path': path.relative_to(OUT).as_posix(), 'sha256': digest(path.read_bytes()), 'bytes': path.stat().st_size}
         for path in sorted(OUT.rglob('*')) if path.is_file()]
(OUT / 'manifest.json').write_bytes((json.dumps({'files': files}, indent=2) + '\n').encode('utf-8'))
print(json.dumps({'files': len(files), 'bytes': sum(row['bytes'] for row in files), 'summary': summary}))
