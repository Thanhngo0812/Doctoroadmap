import hashlib
import json
from pathlib import Path
import subprocess
import sys

root = Path('C:/Users/ngoco/Desktop/Doctoroadmap')
paths = ['report/ket-qua-v3-05b-09b-11b-vertex-2026-09-28.md',
         'scripts/thu-vertex/chi_thu_credit.py', 'scripts/thu-vertex/goi_thu_vertex.py',
         'scripts/thu-vertex/so_embedding.py', 'task/sau-a10/19-dac-ta-bo-cau-hoi-thu.md',
         'task/v3-lo-trinh-doc-duoc/19-goi-mo-hinh-qua-vertex.md']
hashes = {path: hashlib.sha256((root / path).read_bytes()).hexdigest() for path in paths}
out = Path(__file__).with_name('protected-shared-files.json')
if out.exists():
    assert json.loads(out.read_text(encoding='utf-8')) == hashes, 'Another session changed a protected file; preserve it and review.'
else:
    out.write_text(json.dumps(hashes, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'protected_files': len(hashes), 'all_unchanged': True,
                  'main': subprocess.check_output(['git', 'rev-parse', 'main'], cwd=root, text=True).strip()}))
