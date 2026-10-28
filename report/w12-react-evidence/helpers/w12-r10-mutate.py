"""Sequential W12 guard checks; restore exact bytes before any full gate/server."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
TARGET = ROOT / 'src/web/frontend/src/Invitations.tsx'
OUT = ROOT / 'report/w12-react-evidence'

def sha(value): return hashlib.sha256(value).hexdigest()

def main():
    mode = sys.argv[1]
    assert mode in {'old', 'button', 'handler'}
    original = TARGET.read_bytes()
    if mode == 'old':
        mutated = subprocess.check_output(['git','show','af2993a5:src/web/frontend/src/Invitations.tsx'],cwd=ROOT)
        # Restore checkout line endings for an exact old component, not a rewritten analogue.
        mutated = mutated.replace(b'\r\n',b'\n')
        if b'\r\n' in original: mutated = mutated.replace(b'\n',b'\r\n')
    elif mode == 'button':
        mutated = original.replace(b'disabled={loading||Boolean(busy)}',b'disabled={Boolean(busy)}')
    else:
        mutated = original.replace(b'if(loading||active.current)return',b'if(active.current)return')
    assert mutated != original
    label = 'r10-' + mode + '-' + subprocess.check_output(['git','rev-parse','--short=8','HEAD'],cwd=ROOT,text=True).strip() + '-red'
    result = {}
    try:
        TARGET.write_bytes(mutated)
        result['nativeExitCode'] = subprocess.call([sys.executable,'scripts/w12_react_capture.py',label,'npm.cmd','--prefix','src/web/frontend','test','--','--pool=threads','--maxWorkers=1','src/Invitations.test.tsx','--reporter=default','--reporter=junit','--outputFile=../../../report/w12-react-evidence/'+label+'.xml'],cwd=ROOT)
    finally:
        TARGET.write_bytes(original)
        result.update(mode=mode,sourceCommit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),mutantSha256=sha(mutated),beforeSha256=sha(original),restoredSha256=sha(TARGET.read_bytes()),restored=TARGET.read_bytes()==original)
        (OUT/(label+'-restoration.json')).write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result))
    assert result['nativeExitCode']==1 and result['restored']

if __name__ == '__main__': main()
