import json,hashlib,zipfile
from pathlib import Path
base=Path(r'C:/Users/ngoco/Desktop/Doctoroadmap/tmp/w10-quiz-documents/report/w10-r7-evidence')
m=json.loads((base/'raw-text-manifest.json').read_text())
b=(base/m['archive']).read_bytes()
assert hashlib.sha256(b).hexdigest()==m['sha256']
with zipfile.ZipFile(base/m['archive']) as z:
    assert len(z.namelist())==len(m['files'])
    for row in m['files']:
        payload=z.read(row['path'])
        assert len(payload)==row['bytes'] and hashlib.sha256(payload).hexdigest()==row['sha256'],row['path']
print(json.dumps({'archiveSha256':m['sha256'],'verifiedMembers':len(m['files']),'bad':[]}))
