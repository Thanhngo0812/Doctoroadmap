"""Merge only the passed, reviewed candidate if main still equals the received baseline."""
import json, subprocess
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path('C:/Users/ngoco/Desktop/Doctoroadmap')
HERE = Path(__file__).parent
WT = ROOT/'tmp/coord-r4-acceptance-20261024'
provenance = json.loads((HERE/'provenance.json').read_text())
candidate, expected_main = provenance['candidate_sha'], provenance['received_main']

def output(*args,cwd=ROOT):
    return subprocess.check_output(args,cwd=cwd,text=True,encoding='utf-8').strip()

assert output('git','branch','--show-current') == 'main'
assert output('git','rev-parse','HEAD',cwd=WT) == candidate
assert not output('git','diff','--name-only','HEAD','--','src','tests','scripts','design',cwd=WT)
assert not output('git','diff','--cached','--name-only'), 'Do not include any other staged work'
for name in ['full-current','react-current','build-current','browser-current-retry']:
    record = json.loads((HERE/f'runs/{name}-exit.json').read_text())
    assert record['native_exit_code'] == 0 and record['commit'] == candidate,name
for name in ['full-current','react-current']:
    cases = list(ET.parse(HERE/f'runs/{name}.xml').getroot().iter('testcase'))
    assert cases and not any(c.find('failure') is not None or c.find('error') is not None for c in cases)
for ancestor in [expected_main, 'c8c687b', 'bf761fe']:
    subprocess.run(['git','merge-base','--is-ancestor',ancestor,candidate],cwd=ROOT,check=True)
assert subprocess.run(['git','merge-base','--is-ancestor','5ed9ca1',candidate],cwd=ROOT).returncode == 1
protected = subprocess.run([str(ROOT/'.venv/Scripts/python.exe'),str(HERE/'check_shared.py')],cwd=ROOT)
assert protected.returncode == 0
# Keep the comparison and mutation in this same conditional operation.
if output('git','rev-parse','main') != expected_main:
    raise SystemExit('STOP: main changed after current gates; receive it and rerun before merge')
subprocess.run(['git','merge','--no-ff',candidate,'-m',
    'merge(W-08,W-15): accept lecture UI and zero-cost pipeline milestone; round four gates passed; review report/dieu-phoi-nghiem-thu-ba-nhom-lan4-2026-10-24.md'],cwd=ROOT,check=True)
merged = output('git','rev-parse','HEAD')
assert output('git','rev-parse','HEAD^1') == expected_main
assert output('git','rev-parse','HEAD^2') == candidate
assert not output('git','diff','--name-only',candidate,merged,'--','src','tests','scripts','design')
subprocess.run(['git','push','origin','main'],cwd=ROOT,check=True)
result = {'received_main':expected_main,'candidate_sha':candidate,'merge_sha':merged,'pushed':True,
          'whole_w15_accepted':False,'operator_package_merged':False,'design_branch_merged':False,'new_provider_cost_usd':0}
(HERE/'merge-result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
