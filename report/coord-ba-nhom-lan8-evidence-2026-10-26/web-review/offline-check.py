import subprocess,json,sys,os,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PYTHON=Path(r'C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe')
target=ROOT/'backend/wayfinder/infrastructure/learning_runtime.py'
original=target.read_bytes()
receipts=[]
for label,source in [('baseline',original),('bypass-admission',original.replace(b'            self.document_requests.admit(owner)',b'            pass # independent mutation'))]:
    try:
        target.write_bytes(source)
        done=subprocess.run([str(PYTHON),str(ROOT/'offline-boundary.py')],cwd=ROOT,capture_output=True,env={**os.environ,'PYTHONIOENCODING':'utf-8'})
        (ROOT/('offline-'+label+'.log')).write_bytes(done.stdout+b'\n'+done.stderr)
        receipts.append({'label':label,'nativeExitCode':done.returncode,'sourceSha256':hashlib.sha256(source).hexdigest()})
    finally: target.write_bytes(original)
(ROOT/'offline-receipts.json').write_text(json.dumps({'receipts':receipts,'restored':target.read_bytes()==original},indent=2))
print(json.dumps(receipts))
