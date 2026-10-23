"""Archive only named review evidence; never copy inputs, credentials or live stores."""
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path('C:/Users/ngoco/Desktop/Doctoroadmap')
RUN = Path(__file__).parent
WT = ROOT / 'tmp/coord-w15-acceptance-20261023'
OUT = ROOT / 'report/coord-w11-w15-w24-evidence-2026-10-23'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def xml_counts(data):
    tree = ET.fromstring(data)
    cases = tree.findall('.//testcase')
    return {'tests': len(cases), 'failures': len(tree.findall('.//testcase/failure')),
            'errors': len(tree.findall('.//testcase/error')), 'skipped': len(tree.findall('.//testcase/skipped'))}


assert json.loads((RUN / 'full-exit.json').read_text(encoding='utf-8'))['native_exit_code'] == 0
planned = []
for pattern in ('*.json', '*.xml', '*.log', '*.py'):
    planned.extend((p, 'w15/' + p.name) for p in RUN.glob(pattern))
for folder, prefix in [('coord-w11-auth-repro-evidence-20261023', 'w11'), ('coord-w24-review-20261023', 'w24')]:
    planned.extend((p, prefix + '/' + p.name) for p in (ROOT / 'tmp' / folder).iterdir() if p.is_file())
planned.append((WT / 'report/w06-evidence/fixture-copy.json', 'w15/fixture-copy-manifest.json'))
for folder, prefix in [('report/w15-evidence/sql/coord-full-20261023', 'w15/sql'),
                       ('report/w25-evidence/sql/coord-w15-full-20261023', 'w15/w25-sql')]:
    planned.extend((p, prefix + '/' + p.name) for p in (WT / folder).glob('*.json'))
normalization = []
for source, relative in planned:
    raw = source.read_bytes()
    content = raw
    if source.suffix != '.png':
        text = raw.decode('utf-8')
        content = ('\n'.join(line.rstrip() for line in text.replace('\r\n', '\n').splitlines()) + '\n').encode('utf-8')
        if source.suffix == '.json':
            assert json.loads(raw) == json.loads(content), relative
        if source.suffix == '.xml':
            assert xml_counts(raw) == xml_counts(content), relative
    target = OUT / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    assert not target.exists(), target
    target.write_bytes(content)
    normalization.append({'path': relative, 'raw_sha256': sha(raw), 'archived_sha256': sha(content),
                          'changed': raw != content, 'method': 'UTF-8/LF and trailing whitespace only' if raw != content else 'unchanged'})
(OUT / '.gitattributes').write_text('* -text\n', encoding='utf-8')
(OUT / 'normalization.json').write_text(json.dumps(normalization, indent=2) + '\n', encoding='utf-8')
metadata = {'reviewed_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=WT, text=True).strip(),
            'baseline_main': '605f6a3', 'python': xml_counts((RUN / 'full.xml').read_bytes()),
            'react': xml_counts((RUN / 'react.xml').read_bytes()),
            'w11_repro': xml_counts((ROOT / 'tmp/coord-w11-auth-repro-evidence-20261023/auth-return-red.xml').read_bytes()),
            'external_spend_usd': 0, 'links_used': False, 'full_w15_complete': False,
            'w11_accepted': False, 'w24_accepted': False}
(OUT / 'summary.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
files = [{'path': p.relative_to(OUT).as_posix(), 'sha256': sha(p.read_bytes()), 'bytes': p.stat().st_size}
         for p in sorted(OUT.rglob('*')) if p.is_file()]
(OUT / 'manifest.json').write_text(json.dumps({'files': files}, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'archived_files': len(files), 'bytes': sum(p['bytes'] for p in files), **metadata}))
