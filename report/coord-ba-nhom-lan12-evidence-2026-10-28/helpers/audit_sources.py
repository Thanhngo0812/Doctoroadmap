import hashlib,json,subprocess,zipfile,io
from pathlib import Path
R=Path('C:/Users/ngoco/Desktop/Doctoroadmap');T=Path('C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-r12-tools-20261028');P=json.loads((T/'pinned.json').read_text());sha=lambda b:hashlib.sha256(b).hexdigest()
def blobs(ref,paths):
 data=subprocess.check_output(['git','cat-file','--batch'],cwd=R,input=(''.join(ref+':'+p+'\n' for p in paths)).encode());out={};i=0
 for p in paths:
  end=data.index(b'\n',i);head=data[i:end].split();assert head[-1]!=b'missing',p;n=int(head[-1]);out[p]=data[end+1:end+1+n];i=end+1+n+1
 return out
def one(ref,p):return blobs(ref,[p])[p]
groups={}
for name in ['w17-first-admin-evidence','w17-r11-evidence']:
 m=json.loads(one(P['core'],'report/'+name+'/manifest.json'));b=blobs(P['core'],[r['path'] for r in m['files']]);rows=[dict(path=r['path'],matches=sha(b[r['path']])==r['sha256'],bytes_match=len(b[r['path']])==r['bytes']) for r in m['files']];groups[name]=dict(tested_source=m['tested_source_head'],files=rows)
result=dict(groups=groups,tested_to_delivered_source_diff=subprocess.check_output(['git','diff','--name-only','e7d54a1a7969715012c099cc0d7f028f48038c41',P['core'],'--','src','scripts'],cwd=R,text=True).splitlines());(T/'source-evidence-audit.json').write_text(json.dumps(result,indent=2));print(json.dumps({n:dict(files=len(v['files']),mismatches=[r['path'] for r in v['files'] if not(r['matches'] and r['bytes_match'])]) for n,v in groups.items()}));assert all(all(r['matches'] and r['bytes_match'] for r in v['files']) for v in groups.values());assert not result['tested_to_delivered_source_diff']
