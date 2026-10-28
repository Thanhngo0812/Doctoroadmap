"""Read-only R10 acceptance checks; only W04 is eligible after the owner decision."""
import hashlib,json,socket,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
R=Path('C:/Users/ngoco/Desktop/Doctoroadmap');T=Path(__file__).parent
W=R/'tmp/coord-r10-web-final-20261028'
def git(*args,cwd=R):return subprocess.check_output(['git','-c','safe.directory='+str(cwd),*args],cwd=cwd,text=True,encoding='utf-8').strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
candidate=git('rev-parse','HEAD',cwd=W);source=json.loads((T/'integration-source.json').read_text(encoding='utf-8'))
assert candidate==source['candidate']
gates={}
for label in ['full-web-final','react-web-final','build-web-final','browser-w04-web-final']:
    receipt=json.loads((T/f'runs/{label}-exit.json').read_text(encoding='utf-8'))
    assert receipt['native_exit_code']==0 and receipt['commit']==candidate,(label,receipt)
    result={'receipt':receipt};xml=T/f'runs/{label}.xml'
    if xml.exists():
        cases=list(ET.parse(xml).iter('testcase'));failed=sum(c.find('failure') is not None for c in cases);errors=sum(c.find('error') is not None for c in cases)
        skipped=[c for c in cases if c.find('skipped') is not None];assert failed==errors==0
        result.update(tests=len(cases),passed=len(cases)-len(skipped),failures=failed,errors=errors,
            skipped=[dict(name=c.attrib['name'],message=c.find('skipped').attrib) for c in skipped])
    gates[label]=result
for name in ['protected.json','untracked-protected.json']:
    for p,h in json.loads((T/name).read_text()).items():assert sha(R/p)==h,(name,p)
pins=json.loads((T/'pinned.json').read_text());base=git('merge-base',pins['main'],pins['web04'])
paths=git('diff','--name-only',base,pins['web04'],'--','src','scripts').splitlines();comparison=[]
for p in paths:
    original=subprocess.check_output(['git','show',pins['web04']+':'+p],cwd=R)
    integrated=subprocess.check_output(['git','show',candidate+':'+p],cwd=R)
    assert original==integrated,p
    comparison.append(dict(path=p,worker_sha256=hashlib.sha256(original).hexdigest(),candidate_sha256=hashlib.sha256(integrated).hexdigest()))
(T/'product-comparison.json').write_bytes((json.dumps(dict(candidate=candidate,files=comparison,differences=[]),indent=2)+'\n').encode())
fx=json.loads((W/'report/w06-evidence/fixture-copy.json').read_text());assert fx['verified_files']==3144 and not fx['links_used'] and not fx['learner_stores_copied']
runtime=json.loads((W/'report/w04-react-evidence/browser-coord-r10-web-final/runtime.json').read_text(encoding='utf-8'))
audit=json.loads((W/'report/w04-react-evidence/browser-coord-r10-web-final/audit.json').read_text(encoding='utf-8'))
assert runtime['sourceCommit']==candidate and not runtime['dirtySourcePaths'] and runtime['externalCostUsd']==0
assert runtime['temporaryDatabaseRemoved'] and runtime['serverThreadStopped']
assert all(audit['sessionProof'].values()) and audit['secretStorageClean'] and not audit['pageErrors']
assert sum(len(a['violations']) for a in audit['accessibility'])==0
browser=dict(source=candidate,configurations=len(audit['configurations']),screens=len(audit['screens']),axeRuns=len(audit['accessibility']),http=len(audit['http']),sqlSnapshots=len(audit['sql']),consoleErrors=len(audit['console']),pageErrors=len(audit['pageErrors']),sessionProof=audit['sessionProof'],secretStorageClean=audit['secretStorageClean'],designFindings=audit['designInspection']['findings'])
(T/'browser-summary.json').write_bytes((json.dumps(browser,indent=2,ensure_ascii=False)+'\n').encode())
runtime_paths=[W/'report/w04-react-evidence/browser-coord-r10-web-final/runtime.json',R/'tmp/coord-r10-final-20261028/report/w04-react-evidence/browser-coord-r10-final/runtime.json',*[R/f'tmp/coord-r10-acceptance-20261028/report/w12-react-evidence/browser-coord-r10-race{s}/runtime.json' for s in ('','2')]]
dbs=[json.loads(p.read_text(encoding='utf-8'))['databaseName'] for p in runtime_paths]
sql='SELECT datname FROM pg_database WHERE datname IN ('+','.join("'"+d+"'" for d in dbs)+');'
remaining=subprocess.check_output(['docker','compose','--env-file','src/web/.env','-f','src/web/docker-compose.yml','exec','-T','db-test','psql','-U','wayfinder','-d','wayfinder_test','-Atc',sql],cwd=R,text=True).splitlines();assert not remaining,remaining
ports={}
for port in [8024,8027]:
    with socket.socket() as s:s.settimeout(1);ports[port]=s.connect_ex(('127.0.0.1',port))!=0
assert all(ports.values())
proof=json.loads((R/'tmp/coord-r10-acceptance-20261028/report/w12-react-evidence/browser-coord-r10-race2/race-proof.json').read_text(encoding='utf-8'))
assert proof['postStatus']==200 and not proof['visibleAfterOldGet']
assert all(any(r['email_normalized']==proof['email'] and r['status']=='pending' for r in proof[key]['invitations']) for key in ['sqlBeforeRelease','sqlAfterRelease'])
result=dict(candidate=candidate,main_received=source['main'],current_main=git('rev-parse','main'),gates=gates,protected_tracked_files=8,protected_untracked_w23_files=8,
    browser=browser,owned_runtime_databases_absent=dbs,ports_closed=ports,w12_real_http_pg_regression_confirmed=True,new_provider_spend_usd=0,
    included=[pins['web04']],held=[pins['web12'],pins['core'],pins['design']],owner_decision=json.loads((T/'owner-decision.json').read_text(encoding='utf-8')))
(T/'gate-summary.json').write_bytes((json.dumps(result,indent=2,ensure_ascii=False)+'\n').encode())
print(json.dumps(dict(candidate=candidate,python=gates['full-web-final']['passed'],react=gates['react-web-final']['passed'],browser=browser,owned_databases_absent=len(dbs),protected_tracked=8,protected_untracked=8)))
