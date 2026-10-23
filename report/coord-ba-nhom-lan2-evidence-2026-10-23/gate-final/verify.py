import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from dotenv import dotenv_values

root = Path('C:/Users/ngoco/Desktop/Doctoroadmap')
package = root / 'report/coord-ba-nhom-lan2-evidence-2026-10-23'
manifest = json.loads((package / 'manifest.json').read_bytes())['files']
secrets = []
for source in [root / '.env', root / 'src/web/.env']:
    if source.exists():
        secrets.extend(value.encode() for key, value in dotenv_values(source).items()
                       if value and len(value) >= 10 and re.search(r'(KEY|TOKEN|PASSWORD|SECRET|DATABASE_URL)$', key))
for row in manifest:
    data = (package / row['path']).read_bytes()
    assert len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() == row['sha256'], row['path']
    if not row['path'].endswith(('.png', '.webm')):
        assert not any(value in data for value in secrets), ('configured value', row['path'])
prefix = ':' if '--staged' in sys.argv else 'HEAD:' if '--head' in sys.argv else None
if prefix:
    rows = manifest + [{'path': 'manifest.json', 'sha256': hashlib.sha256((package / 'manifest.json').read_bytes()).hexdigest()}]
    for row in rows:
        relative = package.relative_to(root).as_posix() + '/' + row['path']
        data = subprocess.check_output(['git', 'show', prefix + relative], cwd=root)
        assert hashlib.sha256(data).hexdigest() == row['sha256'], ('git blob', relative)
links = []
docs = ['report/dieu-phoi-nghiem-thu-ba-nhom-lan2-2026-10-23.md', 'report/lenh-giao-viec-ba-nhom-lan2-2026-10-23.md',
        'task/web/00-ke-hoach.md', 'task/web/W-08-trang-hoc-bai-giang-doc-trang.md', 'task/web/W-10-quiz-tai-lieu-thu-vien.md',
        'task/web/W-11-chia-se-link-thanh-vien.md', 'task/web/W-15-noi-bo-dung-that-do-usd-cuon.md',
        'task/web/W-17-quan-tri.md', 'task/web/W-24-bo-sung-va-sua-ban-giao-w22.md']
for relative in docs:
    path = root / relative
    for target in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
        if '://' not in target and not target.startswith('#'):
            assert (path.parent / target.split('#')[0]).exists(), (relative, target)
            links.append(target)
print(json.dumps({'files_verified': len(manifest), 'links_verified': len(links), 'git_blob_check': prefix}))
