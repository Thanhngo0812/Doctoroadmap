import hashlib
import json
from pathlib import Path
import re
import subprocess
from dotenv import dotenv_values

root = Path('C:/Users/ngoco/Desktop/Doctoroadmap')
package = root / 'report/coord-w11-w15-w24-evidence-2026-10-23'
manifest = json.loads((package / 'manifest.json').read_text(encoding='utf-8'))
for row in manifest['files']:
    data = (package / row['path']).read_bytes()
    assert len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() == row['sha256'], row['path']
secrets = set()
for configured in (root / '.env', root / 'src/web/.env'):
    if configured.is_file():
        for key, value in dotenv_values(configured).items():
            if value and len(value) >= 10 and re.search(r'(KEY|TOKEN|PASSWORD|SECRET|DATABASE_URL)$', key):
                secrets.add(value.encode('utf-8'))
for path in package.rglob('*'):
    if path.is_file() and path.suffix != '.png':
        content = path.read_bytes()
        assert not any(value in content for value in secrets), ('configured value in evidence', path.relative_to(package).as_posix())
docs = ['report/dieu-phoi-nghiem-thu-w11-w15-w24-va-ke-hoach-2026-10-23.md',
        'report/lenh-giao-viec-sau-w11-2026-10-23.md',
        'task/web/00-ke-hoach.md', 'task/web/W-08-trang-hoc-bai-giang-doc-trang.md',
        'task/web/W-09-tro-ly-va-phien.md', 'task/web/W-11-chia-se-link-thanh-vien.md',
        'task/web/W-15-noi-bo-dung-that-do-usd-cuon.md', 'task/web/W-24-bo-sung-va-sua-ban-giao-w22.md']
links = []
for relative in docs:
    path = root / relative
    for target in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
        if '://' in target or target.startswith('#'):
            continue
        actual = path.parent / target.split('#', 1)[0]
        assert actual.exists(), (relative, target)
        links.append([relative, target])
if '--staged' in __import__('sys').argv:
    for row in manifest['files'] + [{'path': 'manifest.json', 'sha256': hashlib.sha256((package / 'manifest.json').read_bytes()).hexdigest()}]:
        relative = package.relative_to(root).as_posix() + '/' + row['path']
        data = subprocess.check_output(['git', 'show', ':' + relative], cwd=root)
        assert hashlib.sha256(data).hexdigest() == row['sha256'], ('staged', relative)
print(json.dumps({'manifest_files_checked': len(manifest['files']), 'local_links_checked': len(links),
                  'staged_checked': '--staged' in __import__('sys').argv}))
