"""Retain legacy test outputs, restore only our eight generated report edits."""
import hashlib
import json
from pathlib import Path
import subprocess

root=Path(__file__).resolve().parents[3]
out=root/'report/w12-react-evidence/r10-gate-python-final/legacy-test-output'
out.mkdir(exist_ok=False)
paths=['report/w06-evidence/http-doc1.json','report/w06-evidence/http-six-books.json']
paths+=['report/w14-evidence/'+name+'.json' for name in ['http-contract','sql-cancelled','sql-capacity','sql-failed','sql-queue-claims','sql-succeeded']]
receipt=[]
for name in paths:
    target=root/name;data=target.read_bytes()
    saved=out/target.name;saved.write_bytes(data)
    receipt.append(dict(path=name,generatedCopy=str(saved.relative_to(root)).replace('\\','/'),generatedSha256=hashlib.sha256(data).hexdigest()))
subprocess.run(['git','restore','--source=HEAD','--worktree','--',*paths],cwd=root,check=True)
for row in receipt:
    name=row['path'];raw=(root/name).read_bytes()
    blob=subprocess.check_output(['git','show','HEAD:'+name],cwd=root)
    assert raw.replace(b'\r\n',b'\n')==blob.replace(b'\r\n',b'\n')
    row.update(restoredCheckoutSha256=hashlib.sha256(raw).hexdigest(),gitBlobSha256=hashlib.sha256(blob).hexdigest(),matchesHeadAfterLineEndingNormalization=True)
subprocess.run(['git','diff','--exit-code','--',*paths],cwd=root,check=True)
(root/'report/w12-react-evidence/r10-legacy-report-restoration.json').write_text(json.dumps(dict(cause='r10- prefix bypassed legacy protection in capture wrapper; restored explicitly at packaging, source code unchanged',files=receipt),indent=2)+'\n',encoding='utf8')
print('Preserved new test JSON and restored eight historical report files to HEAD checkout.')
