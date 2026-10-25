import json,subprocess
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path('C:/Users/ngoco/Desktop/Doctoroadmap')
HERE=Path(__file__).parent
WT=ROOT/'tmp/coord-r5-core-design-20261025'
expected='d8d5659a01fba40a005846a288120d2f1aaf931e'
candidate='8bb746fd39b3bdef490ea6cc67d0f4758fb40891'
def output(*args,cwd=ROOT):return subprocess.check_output(args,cwd=cwd,text=True,encoding='utf-8').strip()
assert output('git','branch','--show-current')=='main'
assert not output('git','diff','--cached','--name-only')
assert output('git','rev-parse','HEAD',cwd=WT)==candidate
assert not output('git','diff','--name-only','HEAD','--','src','tests','scripts','design',cwd=WT)
for name in ['safe-full','safe-react','safe-build']:
    record=json.loads((HERE/f'runs/{name}-exit.json').read_text())
    assert record['native_exit_code']==0 and record['commit']==candidate,name
for name in ['safe-full','safe-react']:
    cases=list(ET.parse(HERE/f'runs/{name}.xml').getroot().iter('testcase'))
    assert cases and not any(c.find('failure') is not None or c.find('error') is not None for c in cases)
for ref in [expected,'fb0c769','aa387f3']:
    subprocess.run(['git','merge-base','--is-ancestor',ref,candidate],cwd=ROOT,check=True)
assert subprocess.run(['git','merge-base','--is-ancestor','da4d639',candidate],cwd=ROOT).returncode==1
subprocess.run([str(ROOT/'.venv/Scripts/python.exe'),str(HERE/'check_shared.py')],cwd=ROOT,check=True)
if output('git','rev-parse','main')!=expected:
    raise SystemExit('STOP: main changed; receive latest main and rerun gate before merge')
subprocess.run(['git','merge','--quiet','--no-ff',candidate,'-m',
    'merge(W-15,W-24): accept operator fixes and accessible math; review report/dieu-phoi-nghiem-thu-ba-nhom-lan5-2026-10-25.md; local only'],cwd=ROOT,check=True)
merged=output('git','rev-parse','HEAD')
assert output('git','rev-parse','HEAD^1')==expected and output('git','rev-parse','HEAD^2')==candidate
assert not output('git','diff','--name-only',candidate,merged,'--','src','tests','scripts','design')
result={'received_main':expected,'candidate_sha':candidate,'merge_sha':merged,'pushed':False,
        'web_w09_accepted':False,'whole_w15_complete':False,'new_provider_cost_usd':0,
        'accepted_core':'fb0c769','accepted_design':'aa387f3','owner_sync_decision':'local commits only'}
(HERE/'merge-result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
