"""Run only mocked React regression tests in the isolated existing review worktree."""
from pathlib import Path
import json
import subprocess
import xml.etree.ElementTree as ET

OUT = Path(__file__).resolve().parent
REVIEW = Path('C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-w11-auth-repro-20261023')
command = ['cmd.exe','/d','/c','npm.cmd','--prefix','src/web/frontend','test','--',
    'src/W11AuthReturn.repro.test.tsx','src/W11AuthReturn.worker-recheck.test.tsx',
    '--pool=threads','--maxWorkers=1','--reporter=default','--reporter=junit',
    '--outputFile='+str(OUT/'auth-return-independent-green.xml')]
with (OUT/'auth-return-independent-green.log').open('w',encoding='utf-8') as log:
    run = subprocess.run(command,cwd=REVIEW,stdout=log,stderr=subprocess.STDOUT,timeout=180)
(OUT/'native-exit.txt').write_text(str(run.returncode)+'\n',encoding='utf-8')
tree = ET.parse(OUT/'auth-return-independent-green.xml')
cases = list(tree.iter('testcase'))
failures = list(tree.iter('failure'))
errors = list(tree.iter('error'))
skips = list(tree.iter('skipped'))
results = dict(command=command,cwd=str(REVIEW),worker_input_commit='253874bbd83e4224477542928b4a3ef9344db93a',
    native_exit=run.returncode,tests=len(cases),passed=len(cases)-len(failures)-len(errors)-len(skips),
    failures=len(failures),errors=len(errors),skipped=len(skips),postgres_calls=0,provider_calls=0,
    scope='Original independent ten-case reproduction plus worker expanded twenty-two-case test, mocked HTTP/auth only')
(OUT/'focused-result.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
print(json.dumps(results,indent=2),flush=True)
