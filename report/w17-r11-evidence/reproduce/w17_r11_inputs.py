import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

root=Path.cwd()
result=subprocess.run([sys.executable,'src/web/backend/tests/copy_w06_fixtures.py'],capture_output=True,text=True,encoding='utf-8')
out=root/'report/w17-r11-evidence/inputs'
out.mkdir(parents=True,exist_ok=True)
(out/'fixture-copy.log').write_text(result.stdout+result.stderr,encoding='utf-8')
assert result.returncode==0
source=root.parents[1]/'document-data/train/nong-nghiep/rau-thuy-canh.pdf'
target=root/'tmp/w15-candidate/input.pdf'
expected='1f019766e74a747d293c15ad5bc86b2ea90420b49a8437cf27c1f6805656a627'
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert digest(source)==expected
assert not source.is_symlink() and source.stat().st_nlink==1
target.parent.mkdir(parents=True,exist_ok=True)
if target.exists():
    assert digest(target)==expected
else:
    shutil.copyfile(source,target)
assert digest(target)==expected and not target.is_symlink() and target.stat().st_nlink==1
(out/'fixture-copy.json').write_bytes((root/'report/w06-evidence/fixture-copy.json').read_bytes())
(out/'candidate.json').write_text(json.dumps(dict(source=str(source),target='tmp/w15-candidate/input.pdf',sha256=expected,
    bytes=target.stat().st_size,ordinary_copy=True,purpose='Existing whole-suite fixture only; no W15 operator/paid run'),indent=2)+'\n',encoding='utf-8')
print('Development fixtures verified, candidate ordinary copy independently SHA-verified')
