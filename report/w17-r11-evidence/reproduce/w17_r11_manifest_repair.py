import hashlib
import json
from pathlib import Path
import subprocess

root=Path.cwd()
history=root/'report/w17-r11-evidence/history'
history.mkdir(parents=True,exist_ok=True)
manifest=root/'report/w17-first-admin-evidence/manifest.json'
old=manifest.read_bytes()
backup=history/'first-admin-manifest-before-r11.json'
assert not backup.exists()
backup.write_bytes(old)
data=json.loads(old)
changes=[]
for name in ('redactions.json','packaging-note.json'):
    path=root/'report/w17-first-admin-evidence'/name
    raw=path.read_bytes()
    blob=subprocess.check_output(['git','show','862dd805:'+path.relative_to(root).as_posix()],cwd=root)
    (history/('before-r11-'+name)).write_bytes(raw)
    content=raw.decode('utf-8').replace('\r\n','\n')
    path.write_bytes(content.encode('utf-8'))
    entry=next(row for row in data['files'] if row['path']==path.relative_to(root).as_posix())
    changes.append(dict(path=entry['path'],old_entry=dict(entry),old_worktree_bytes=len(raw),
        old_git_blob_bytes=len(blob),old_git_blob_sha256=hashlib.sha256(blob).hexdigest(),
        new_bytes=path.stat().st_size,new_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    entry.update(bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
manifest.write_bytes((json.dumps(data,indent=2)+'\n').encode('utf-8'))
assert all((root/row['path']).stat().st_size==row['bytes'] and hashlib.sha256((root/row['path']).read_bytes()).hexdigest()==row['sha256'] for row in data['files'])
(history/'manifest-repair.json').write_bytes((json.dumps(dict(prior_delivery='862dd805',rows_verified=380,changes=changes,
    cause='Two write_text outputs had CRLF byte hashes while Git stored normalized LF; normalize bytes before hashing',
    artifact_content_semantics_unchanged=True),indent=2)+'\n').encode('utf-8'))
print(json.dumps(dict(rows_verified=380,changes=changes)))
