import hashlib,json,subprocess,sys,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path('C:/Users/ngoco/Desktop/Doctoroadmap')
BASE=ROOT/'tmp/coord-r9-design-review-20261027'
HTML=BASE/'design/preview/w10_quiz_screens.html'
WORKER=ROOT/'tmp/w24-figma-evidence/design/preview/w10_quiz_screens.html'
raw=HTML.read_bytes();worker=WORKER.read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest()
assert raw==worker
py=str(ROOT/'.venv/Scripts/python.exe')
capture=str(BASE/'capture.py')
rows=[]
mutations=[('wiring-origin',[(b"filterLibrary('here', this)",b"filterLibrary('button', this)"),(b"filterLibrary('elsewhere', this)",b"filterLibrary('assistant', this)")]),('inverted-group',[(b'cardGroup === group',b'cardGroup !== group')]),('scope-off-by-one',[(b'checked > 5',b'checked >= 5')])]
for label,changes in mutations:
    changed=raw
    for old,new in changes:
        assert changed.count(old)==1,(label,old,changed.count(old))
        changed=changed.replace(old,new,1)
    try:
        HTML.write_bytes(changed)
        args=[py,capture,str(BASE),str(BASE/'runs'),label,py,'scripts/w05_run_tests.py','-o','addopts=','-q','tests/unit/presentation/test_tokens_and_wcag.py::test_w10_library_filters_by_group_independent_of_origin','--junitxml=runs/'+label+'.xml']
        result=subprocess.run(args,cwd=BASE)
        cases=list(ET.parse(BASE/'runs'/f'{label}.xml').getroot().iter('testcase'))
        failures=sum(c.find('failure') is not None for c in cases);errors=sum(c.find('error') is not None for c in cases)
        assert result.returncode==1 and failures==1 and errors==0,(label,result.returncode,failures,errors)
        rows.append(dict(name=label,native=1,failures=failures,errors=errors,original_sha256=sha(raw),mutated_sha256=sha(changed)))
    finally:
        HTML.write_bytes(raw)
        assert HTML.read_bytes()==raw and WORKER.read_bytes()==worker
args=[py,capture,str(BASE),str(BASE/'runs'),'restored-green',py,'scripts/w05_run_tests.py','-o','addopts=','-q','tests/unit/presentation/test_tokens_and_wcag.py','--junitxml=runs/restored-green.xml']
result=subprocess.run(args,cwd=BASE);assert result.returncode==0
proof=dict(mutants=rows,source_restored=True,worker_unchanged=True,sha256=sha(raw),external_spend_usd=0)
(BASE/'mutations.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof))
