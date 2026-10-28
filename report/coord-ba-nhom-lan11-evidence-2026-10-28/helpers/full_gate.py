import json,subprocess,sys,hashlib
from pathlib import Path
R=Path('C:/Users/ngoco/Desktop/Doctoroadmap');W=Path('C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-r11-final-20261028');T=Path('C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-r11-tools-20261028');paths=["report/w06-evidence/http-doc1.json","report/w06-evidence/http-six-books.json","report/w14-evidence/http-contract.json","report/w14-evidence/sql-cancelled.json","report/w14-evidence/sql-capacity.json","report/w14-evidence/sql-failed.json","report/w14-evidence/sql-queue-claims.json","report/w14-evidence/sql-succeeded.json"]
assert subprocess.check_output(['git','rev-parse','main'],cwd=R,text=True).strip()=='b64b88478e72cc36991815006923d9b3ae0beb93'
try:
 r=subprocess.run([sys.executable,str(R/'tmp/coord-review-20261021/run_check.py'),str(W),str(T/'runs'),'full-final',sys.executable,'scripts/w05_run_tests.py','-o','addopts=','-q','--basetemp=tmp/coord-r11-full-final','--junitxml='+str(T/'runs/full-final.xml')],cwd=R)
finally:
 out=T/'legacy-test-output';out.mkdir(exist_ok=True);records=[]
 for p in paths:
  target=W/p;new=target.read_bytes();saved=out/target.name;saved.write_bytes(new);old=(T/'history-before'/target.name).read_bytes();target.write_bytes(old);assert target.read_bytes()==old;records.append(dict(path=p,generated_sha256=hashlib.sha256(new).hexdigest(),restored_sha256=hashlib.sha256(old).hexdigest()))
 (T/'legacy-report-restoration.json').write_text(json.dumps(records,indent=2))
raise SystemExit(r.returncode)
