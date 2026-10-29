import hashlib,json,subprocess,sys
from pathlib import Path
R=Path('C:/Users/ngoco/Desktop/Doctoroadmap');W=Path('C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-r11-final-20261028');T=Path('C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-r11-tools-20261028');p=W/'src/web/frontend/src/Invitations.tsx';original=p.read_bytes();s=original.decode();records=[]
old=subprocess.check_output(['git','show','af2993a57ae4d9c023e0b77a5d6b699399753427:src/web/frontend/src/Invitations.tsx'],cwd=R)
variants=[('web-old',old),('web-button',s.replace('disabled={loading||Boolean(busy)}','disabled={Boolean(busy)}',1).encode()),('web-handler',s.replace('if(loading||active.current)return','if(active.current)return',1).encode())]
for label,data in variants:
 assert data!=original
 try:
  p.write_bytes(data);cmd=[sys.executable,str(R/'tmp/coord-review-20261021/run_check.py'),str(W),str(T/'runs'),label,'npm.cmd','--prefix','src/web/frontend','test','--','src/Invitations.test.tsx','--pool=threads','--maxWorkers=1','--reporter=default','--reporter=junit','--outputFile='+str(T/'runs'/f'{label}.xml')];result=subprocess.run(cmd,cwd=R);records.append(dict(label=label,native_exit_code=result.returncode,original_sha256=hashlib.sha256(original).hexdigest(),mutant_sha256=hashlib.sha256(data).hexdigest()))
 finally:p.write_bytes(original);assert p.read_bytes()==original
(T/'web-mutations.json').write_text(json.dumps(records,indent=2))
assert all(r['native_exit_code']==1 for r in records)
