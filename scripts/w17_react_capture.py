"""Run a scoped check with exact source/native receipts and retained legacy exports."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from time import monotonic

ROOT=Path(__file__).resolve().parents[1]

def main():
    label,*command=sys.argv[1:]
    assert label.replace('-','').isalnum()
    folder=ROOT/'report/w17-react-evidence'/label
    assert not folder.exists()
    folder.mkdir(parents=True)
    protected=[]
    if any('w05_run_tests.py' in part for part in command):
        protected=['report/w06-evidence/http-doc1.json','report/w06-evidence/http-six-books.json']
        protected+=['report/w14-evidence/'+p+'.json' for p in ['http-contract','sql-cancelled','sql-capacity','sql-failed','sql-queue-claims','sql-succeeded']]
    originals={p:(ROOT/p).read_bytes() for p in protected}
    files=subprocess.check_output(['git','ls-files','src','scripts'],cwd=ROOT,text=True).splitlines()
    hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files if (ROOT/p).is_file()}
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    start=monotonic()
    try:
        with (folder/'output.log').open('wb') as log:
            native=subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,env={**os.environ,'W15_EVIDENCE_RUN':'w17-react-'+label,'W25_EVIDENCE_RUN':'w17-react-'+label}).returncode
    finally:
        for p,data in originals.items():
            target=ROOT/p
            if target.read_bytes()!=data:
                saved=folder/'legacy-test-output'/target.name;saved.parent.mkdir(exist_ok=True);saved.write_bytes(target.read_bytes())
                target.write_bytes(data)
            assert target.read_bytes()==data
    result=dict(commit=commit,cwd=str(ROOT),command=command,nativeExitCode=native,seconds=round(monotonic()-start,2),sourceSha256=hashes,restoredHistoricalFiles=list(originals))
    (folder/'exit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in result.items() if k!='sourceSha256'}),flush=True)
    return native

if __name__=='__main__':raise SystemExit(main())
