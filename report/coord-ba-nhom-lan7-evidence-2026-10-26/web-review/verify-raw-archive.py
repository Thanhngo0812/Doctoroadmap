import json,hashlib,zipfile
from pathlib import Path
base=Path(r'C:/Users/ngoco/Desktop/Doctoroadmap/tmp/w10-quiz-documents/report/w10-evidence')
m=json.loads((base/'raw-text-manifest.json').read_text(encoding='utf8'))
zip_path=base/m['archive']
assert hashlib.sha256(zip_path.read_bytes()).hexdigest()==m['archiveSha256']
bad=[]
with zipfile.ZipFile(zip_path) as z:
    for e in m['files']:
        b=z.read(e['path'])
        if len(b)!=e['bytes'] or hashlib.sha256(b).hexdigest()!=e['sha256']: bad.append(e['path'])
print(json.dumps({'archive':m['archive'],'files':len(m['files']),'mismatches':bad}))
assert not bad
