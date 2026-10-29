import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

root = Path.cwd()
name, *args = sys.argv[1:]
out = root / 'report/w17-first-admin-evidence/runs'
out.mkdir(parents=True, exist_ok=True)
command = [sys.executable, 'scripts/w05_run_tests.py', '-o', 'addopts=', '-q', *args,
    '--basetemp=tmp/w17-' + name, '--junitxml=report/w17-first-admin-evidence/runs/' + name + '.xml']
source = {str(p.relative_to(root)).replace('\\','/'): hashlib.sha256(p.read_bytes()).hexdigest()
    for p in (root/'src/web/backend').rglob('*.py')}
env = dict(os.environ, W17_EVIDENCE_RUN=name, W17_EVIDENCE_ROOT='report/w17-first-admin-evidence', W15_EVIDENCE_RUN='w17-first-'+name, W25_EVIDENCE_RUN='w17-first-'+name)
start = time.time()
with (out/(name+'.log')).open('w', encoding='utf-8') as log:
    result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, env=env)
data = dict(command=command, cwd=str(root), head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
    native_exit=result.returncode, seconds=time.time()-start, source_sha256=source)
(out/(name+'-exit.json')).write_text(json.dumps(data,indent=2)+'\n', encoding='utf-8')
print(json.dumps({k:v for k,v in data.items() if k!='source_sha256'}))
raise SystemExit(result.returncode)
