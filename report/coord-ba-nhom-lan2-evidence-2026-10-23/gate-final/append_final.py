"""Append post-merge verification evidence; preserve the first gate and archive."""
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

root = Path('C:/Users/ngoco/Desktop/Doctoroadmap')
run = Path(__file__).parent
wt = root / 'tmp/coord-r2-acceptance-20261023'
out = root / 'report/coord-ba-nhom-lan2-evidence-2026-10-23'


def counts(data):
    tree = ET.fromstring(data)
    return {key: len(tree.findall(query)) for key, query in
            [('tests', './/testcase'), ('failures', './/testcase/failure'), ('errors', './/testcase/error'), ('skipped', './/testcase/skipped')]}


for label in ['full-final', 'react-final', 'build-final']:
    assert json.loads((run / (label + '-exit.json')).read_bytes())['native_exit_code'] == 0
planned = [(p, 'gate-final/' + p.name) for p in run.iterdir() if p.is_file() and p.suffix in {'.json', '.xml', '.log', '.py'}]
for folder, label in [('report/w15-evidence/sql/coord-r2-final-20261023', 'w15-sql-final'),
                      ('report/w25-evidence/sql/coord-r2-final-20261023', 'w25-sql-final')]:
    planned.extend((p, label + '/' + p.name) for p in (wt / folder).glob('*.json'))
norm = []
for path, relative in planned:
    raw = path.read_bytes()
    data = ('\n'.join(line.rstrip() for line in raw.decode('utf-8').replace('\r\n', '\n').splitlines()) + '\n').encode('utf-8')
    if path.suffix == '.json':
        assert json.loads(raw) == json.loads(data)
    if path.suffix == '.xml':
        assert counts(raw) == counts(data)
    target = out / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    assert not target.exists(), target
    target.write_bytes(data)
    norm.append({'path': relative, 'raw_sha256': hashlib.sha256(raw).hexdigest(),
                 'archived_sha256': hashlib.sha256(data).hexdigest(), 'changed': raw != data})
source_paths = ['src', 'tests', 'scripts', 'design']
assert not subprocess.check_output(['git', 'diff', '--name-only', 'b625752', '817f487', '--', *source_paths], cwd=root)
assert not subprocess.check_output(['git', 'diff', '--name-only', '817f487', 'main', '--', *source_paths], cwd=root)
summary = {'initial_review': 'b625752d929efd1a94f0975586a9c80296966aa7',
           'merge_commit': 'e85427ad5c7ecb65a18ab581af9f790a54d53da0',
           'post_merge_verified_commit': '817f487639880e2ca052fbe28ad2d8423c615ace',
           'main_at_finalization': subprocess.check_output(['git', 'rev-parse', 'main'], cwd=root, text=True).strip(),
           'python': counts((run / 'full-final.xml').read_bytes()), 'react': counts((run / 'react-final.xml').read_bytes()),
           'production_test_script_design_diff_empty': True, 'external_spend_usd': 0,
           'w11_accepted': True, 'w15_trace_milestone_accepted': True, 'full_w15_complete': False,
           'w24_accepted': False}
for name, value in [('normalization-final.json', norm), ('summary-final.json', summary)]:
    (out / name).write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode())
files = [{'path': p.relative_to(out).as_posix(), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'bytes': p.stat().st_size}
         for p in sorted(out.rglob('*')) if p.is_file() and p.name != 'manifest.json']
(out / 'manifest.json').write_bytes((json.dumps({'files': files}, indent=2) + '\n').encode())
print(json.dumps({'files': len(files), 'bytes': sum(row['bytes'] for row in files), **summary}))
