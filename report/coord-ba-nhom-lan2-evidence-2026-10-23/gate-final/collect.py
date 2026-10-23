import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path('C:/Users/ngoco/Desktop/Doctoroadmap')
RUN = Path(__file__).parent
WT = ROOT / 'tmp/coord-r2-acceptance-20261023'
OUT = ROOT / 'report/coord-ba-nhom-lan2-evidence-2026-10-23'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def counts(data):
    tree = ET.fromstring(data)
    return {key: len(tree.findall(query)) for key, query in
            [('tests', './/testcase'), ('failures', './/testcase/failure'), ('errors', './/testcase/error'), ('skipped', './/testcase/skipped')]}


assert json.loads((RUN / 'full-exit.json').read_bytes())['native_exit_code'] == 0
assert json.loads((RUN / 'browser-exit.json').read_bytes())['native_exit_code'] == 0
planned = [(p, 'gate/' + p.name) for p in RUN.iterdir() if p.is_file() and p.suffix in {'.json', '.log', '.xml', '.py'}]
for folder, label in [('coord-r2-20261023-w11-review', 'w11-review'), ('coord-r2-20261023-w15-review', 'w15-review'),
                      ('coord-r2-20261023-w24-review', 'w24-review')]:
    base = ROOT / 'tmp' / folder
    planned.extend((p, label + '/' + p.relative_to(base).as_posix()) for p in base.rglob('*')
                   if p.is_file() and 'inputs' not in p.parts and p.suffix in {'.json', '.log', '.xml', '.md', '.txt', '.py', '.cjs', '.png'})
planned.append((WT / 'report/w06-evidence/fixture-copy.json', 'gate/fixture-copy-manifest.json'))
for folder, label in [('report/w15-evidence/sql/coord-r2-full-20261023', 'w15-sql'),
                      ('report/w25-evidence/sql/coord-r2-full-20261023', 'w25-sql')]:
    planned.extend((p, label + '/' + p.name) for p in (WT / folder).glob('*.json'))
browser = WT / 'report/w11-evidence/auth-return-2026-10-23/browser-coord-r2'
for name in ['audit.json', 'runtime.json', 'state.json', 'auth-register-390-dark.png', 'auth-login-1280-light.png', 'auth-return.webm']:
    planned.append((browser / name, 'browser/' + name))
OUT.mkdir(parents=True, exist_ok=True)
normalization = []
for source, relative in planned:
    raw = source.read_bytes()
    data = raw
    if source.suffix not in {'.png', '.webm'}:
        data = ('\n'.join(line.rstrip() for line in raw.decode('utf-8').replace('\r\n', '\n').splitlines()) + '\n').encode('utf-8')
        if source.suffix == '.json':
            assert json.loads(raw) == json.loads(data), relative
        if source.suffix == '.xml':
            assert counts(raw) == counts(data), relative
    target = OUT / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    assert not target.exists(), target
    target.write_bytes(data)
    normalization.append({'path': relative, 'raw_sha256': digest(raw), 'archived_sha256': digest(data),
                          'changed': raw != data})
summary = {'commit': json.loads((RUN / 'full-exit.json').read_bytes())['commit'],
           'python': counts((RUN / 'full.xml').read_bytes()), 'react': counts((RUN / 'react.xml').read_bytes()),
           'full_w15_complete': False, 'w24_accepted': False, 'external_spend_usd': 0,
           'links_used': False, 'browser_runtime': json.loads((browser / 'runtime.json').read_bytes())}
for name, value in [('normalization.json', normalization), ('summary.json', summary)]:
    (OUT / name).write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
(OUT / '.gitattributes').write_bytes(b'* -text\n')
files = [{'path': p.relative_to(OUT).as_posix(), 'sha256': digest(p.read_bytes()), 'bytes': p.stat().st_size}
         for p in sorted(OUT.rglob('*')) if p.is_file()]
(OUT / 'manifest.json').write_bytes((json.dumps({'files': files}, indent=2) + '\n').encode('utf-8'))
print(json.dumps({'files': len(files), 'bytes': sum(row['bytes'] for row in files),
                  'python': summary['python'], 'react': summary['react']}))
