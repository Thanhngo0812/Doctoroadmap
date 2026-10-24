import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from dotenv import dotenv_values

ROOT = Path('C:/Users/ngoco/Desktop/Doctoroadmap')
WT = ROOT if '--root' in sys.argv else ROOT / 'tmp/sa62-port-kho-pha-b'
OUT = WT / 'report/sa62-web-test-evidence-2026-10-23'
manifest = json.loads((OUT / 'manifest.json').read_bytes())['files']
secrets = []
for config in [ROOT / '.env', ROOT / 'src/web/.env']:
    if config.exists():
        secrets.extend(value.encode() for key, value in dotenv_values(config).items()
                       if value and len(value) >= 10 and re.search(r'(KEY|TOKEN|PASSWORD|SECRET|DATABASE_URL)$', key))
for row in manifest:
    data = (OUT / row['path']).read_bytes()
    assert len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() == row['sha256'], row['path']
    assert not any(value in data for value in secrets), ('configured value in evidence', row['path'])
prefix = ':' if '--staged' in sys.argv else 'HEAD:' if '--head' in sys.argv else None
if prefix:
    rows = manifest + [{'path': 'manifest.json', 'sha256': hashlib.sha256((OUT / 'manifest.json').read_bytes()).hexdigest()}]
    for row in rows:
        path = OUT.relative_to(WT).as_posix() + '/' + row['path']
        data = subprocess.check_output(['git', 'show', prefix + path], cwd=WT)
        assert hashlib.sha256(data).hexdigest() == row['sha256'], ('git blob', path)
print(json.dumps({'verified_files': len(manifest), 'git_blob_check': prefix}))
