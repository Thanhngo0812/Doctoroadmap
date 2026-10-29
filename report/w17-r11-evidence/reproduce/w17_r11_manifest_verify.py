import hashlib
import json
from pathlib import Path
import subprocess

root=Path.cwd()
manifest=json.loads((root/'report/w17-first-admin-evidence/manifest.json').read_text(encoding='utf-8'))
files=manifest['files']
batch=b''.join(('HEAD:'+row['path']+'\n').encode('utf-8') for row in files)
result=subprocess.run(['git','-c','core.longpaths=true','cat-file','--batch'],input=batch,capture_output=True,check=True,cwd=root)
cursor=0
for row in files:
    end=result.stdout.index(b'\n',cursor)
    header=result.stdout[cursor:end].split()
    assert header[1]==b'blob',(row['path'],header)
    size=int(header[2]); cursor=end+1
    blob=result.stdout[cursor:cursor+size]; cursor+=size+1
    actual=(root/row['path']).read_bytes()
    assert size==row['bytes']==len(actual),row['path']
    assert hashlib.sha256(blob).hexdigest()==row['sha256']==hashlib.sha256(actual).hexdigest(),row['path']
out=root/'report/w17-r11-evidence/history/manifest-verification.json'
out.write_bytes((json.dumps(dict(head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
    worktree_rows_verified=len(files),committed_git_blob_rows_verified=len(files),
    scoped_lf_attributes=True,global_git_configuration_changed=False),indent=2)+'\n').encode('utf-8'))
print(out.read_text(encoding='utf-8'))
