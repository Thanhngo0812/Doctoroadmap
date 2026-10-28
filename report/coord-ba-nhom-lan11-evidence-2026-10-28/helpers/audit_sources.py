import hashlib,json,subprocess,zipfile,io
from pathlib import Path
R=Path('C:/Users/ngoco/Desktop/Doctoroadmap');T=Path('C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-r11-tools-20261028');P=json.loads((T/'pinned.json').read_text());sha=lambda b:hashlib.sha256(b).hexdigest()
def blobs(ref,paths):
 data=subprocess.check_output(['git','cat-file','--batch'],cwd=R,input=(''.join(ref+':'+p+'\n' for p in paths)).encode());out={};i=0
 for p in paths:
  end=data.index(b'\n',i);head=data[i:end].split();assert head[-1]!=b'missing',p;n=int(head[-1]);out[p]=data[end+1:end+1+n];i=end+1+n+1
 return out
def one(ref,p):return blobs(ref,[p])[p]
wm=json.loads(one(P['web'],'report/w12-react-evidence/r10-manifest.json'));z=zipfile.ZipFile(io.BytesIO(one(P['web'],'report/w12-react-evidence/r10-source-snapshot.zip')));sb=blobs(P['web'],list(wm['sourceSha256']));s=[]
for p,h in wm['sourceSha256'].items():
 b=sb[p];variants=[b];snapshot=p in z.namelist()
 try:
  b.decode('utf8');variants.append(b.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n'))
 except UnicodeDecodeError:pass
 if snapshot:
  raw=z.read(p);assert raw.replace(b'\r\n',b'\n')==b.replace(b'\r\n',b'\n'),p;variants.append(raw)
 s.append(dict(path=p,raw_receipt_explained=any(sha(v)==h for v in variants),snapshot_available=snapshot))
eb=blobs(P['web'],list(wm['evidenceSha256']));es=[dict(path=p,matches=sha(eb[p])==h) for p,h in wm['evidenceSha256'].items()]
cm=json.loads(one(P['core'],'report/w17-first-admin-evidence/manifest.json'));cb=blobs(P['core'],[r['path'] for r in cm['files']]);cs=[dict(path=r['path'],matches=sha(cb[r['path']])==r['sha256'],bytes_match=len(cb[r['path']])==r['bytes']) for r in cm['files']]
result=dict(web_source=s,web_evidence=es,core_evidence=cs,web_tested_source=wm['sourceCommit'],core_tested_source=cm['tested_source_head']);(T/'source-evidence-audit.json').write_text(json.dumps(result,indent=2));print(json.dumps(dict(web_source=len(s),web_source_unexplained=[r['path'] for r in s if not r['raw_receipt_explained']],web_evidence=len(es),web_bad_evidence=[r['path'] for r in es if not r['matches']],core_evidence=len(cs),core_bad_evidence=[r['path'] for r in cs if not(r['matches'] and r['bytes_match'])])))
