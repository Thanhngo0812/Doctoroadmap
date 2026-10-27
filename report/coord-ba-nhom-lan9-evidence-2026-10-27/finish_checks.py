"""Read-only provenance and gate checks for round nine; no cleanup or providers."""
import hashlib,json,socket,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
R=Path('C:/Users/ngoco/Desktop/Doctoroadmap'); T=Path(__file__).parent
W=R/'tmp/coord-r9-acceptance-20261027'
def git(*args,cwd=R):return subprocess.check_output(['git','-c','safe.directory='+str(cwd),*args],cwd=cwd,text=True,encoding='utf-8').strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
candidate=git('rev-parse','HEAD',cwd=W)
gates={}
for label in ('full-final','react-final','build-final','browser-final','full-rebased','react-rebased','build-rebased'):
    receipt=json.loads((T/f'runs/{label}-exit.json').read_text(encoding='utf-8'))
    assert receipt['native_exit_code']==0,(label,receipt)
    if label.endswith('rebased'):assert receipt['commit']==candidate,(label,candidate)
    result=dict(receipt=receipt)
    xml=T/f'runs/{label}.xml'
    if xml.exists():
        tree=ET.parse(xml);cases=list(tree.iter('testcase'))
        failed=sum(c.find('failure') is not None for c in cases)
        errors=sum(c.find('error') is not None for c in cases)
        skipped=[c for c in cases if c.find('skipped') is not None]
        assert failed==errors==0,(label,failed,errors)
        result.update(tests=len(cases),passed=len(cases)-len(skipped),failures=failed,errors=errors,
                      skipped=[dict(name=c.attrib['name'],message=c.find('skipped').attrib) for c in skipped])
    gates[label]=result
browser=json.loads((W/'report/w16-react-evidence/browser-coord-r9-final/runtime.json').read_text(encoding='utf-8'))
dbs=[browser['databaseName'],'wayfinder_w16_ea97feb131fd4688b60ae0a216f91c6e']
sql="SELECT datname FROM pg_database WHERE datname IN ("+','.join("'"+d+"'" for d in dbs)+');'
dbresult=subprocess.check_output(['docker','compose','--env-file','src/web/.env','-f','src/web/docker-compose.yml','exec','-T','db-test','psql','-U','wayfinder','-d','wayfinder_test','-Atc',sql],cwd=R,text=True).splitlines()
assert dbs[0] not in dbresult,'Final harness UUID database is still present'
with socket.socket() as s:
    s.settimeout(1);port_closed=s.connect_ex(('127.0.0.1',8026))!=0
assert port_closed
protected=json.loads((T/'protected-resume.json').read_text(encoding='utf-8'))
protection=[dict(path=p,before=h,now=sha(R/p)) for p,h in protected['files'].items()]
assert all(p['before']==p['now'] for p in protection),'Concurrent files changed; inspect before making claims'
comp=json.loads((T/'product-comparison.json').read_text(encoding='utf-8'))
allowed={'scripts/w16_web_runtime.py','scripts/w16_web_check.cjs'}
assert {r['path'] for r in comp['files'] if not r['equal']}==allowed
fixture=json.loads((W/'report/w06-evidence/fixture-copy.json').read_text(encoding='utf-8'))
assert fixture['verified_files']==3144 and len(fixture['files'])==3144
assert not fixture['links_used'] and not fixture['learner_stores_copied']
assert all(b['all_sha256_match'] for b in fixture['bundles'])
frontend_diff=git('diff','--name-only',browser['sourceCommit'],candidate,'--','src/web','scripts/w16_web_runtime.py','scripts/w16_web_check.cjs','design',cwd=W)
assert not frontend_diff
result=dict(candidate=candidate,main_received=protected['main'],current_main=git('rev-parse','main'),gates=gates,
            browser_reused_source=browser['sourceCommit'],browser_reuse_web_tree_identical=True,
            browser_final_database_absent=True,interrupted_uuid_retained=dbs[1] in dbresult,
            interrupted_uuid=dbs[1],browser_port_closed=port_closed,protected_files=protection,
            new_external_spend_usd=0,provider_note='Scripted providers, FakeMailer and local media; ledger dollar figures are synthetic.')
(T/'gate-summary.json').write_bytes((json.dumps(result,indent=2,ensure_ascii=False)+'\n').encode())
print(json.dumps(dict(candidate=candidate,gates={k:{x:v[x] for x in ('passed','failures','errors') if x in v} for k,v in gates.items()},database_absent=True,port_closed=port_closed,protected=len(protection))))
