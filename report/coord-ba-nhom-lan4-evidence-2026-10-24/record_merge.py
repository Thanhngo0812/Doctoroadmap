import json,subprocess
from pathlib import Path

ROOT=Path('C:/Users/ngoco/Desktop/Doctoroadmap')
HERE=Path(__file__).parent
provenance=json.loads((HERE/'provenance.json').read_text())
def output(*args):
    return subprocess.check_output(args,cwd=ROOT,text=True,encoding='utf-8',timeout=60).strip()
merged=output('git','rev-parse','HEAD')
assert merged=='bad8e45f392ee8a463efbb944669b27d6c20f390'
assert output('git','rev-parse','HEAD^1')==provenance['received_main']
assert output('git','rev-parse','HEAD^2')==provenance['candidate_sha']
assert not output('git','diff','--name-only',provenance['candidate_sha'],merged,'--','src','tests','scripts','design')
remote=output('git','rev-parse','refs/remotes/origin/main')
result={'received_main':provenance['received_main'],'candidate_sha':provenance['candidate_sha'],'merge_sha':merged,
        'pushed':False,'last_known_remote_main_sha':remote,'whole_w15_accepted':False,'operator_package_merged':False,
        'design_branch_merged':False,'new_provider_cost_usd':0,
        'owner_decision_date':'2026-10-24','synchronization':'local commits only; main push deferred by owner',
        'owner_message':'tạm thời k cần push lên main, commit đồng bộ mới nhất ở đây là đc, viết vô điều phối giao tiep đây là quyết định của tôi'}
(HERE/'merge-result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
