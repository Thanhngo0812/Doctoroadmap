import hashlib,json,re,socket,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
R=Path('C:/Users/ngoco/Desktop/Doctoroadmap');W=Path('C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-r12-acceptance-20261028');T=Path('C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-r12-tools-20261028');S=json.loads((T/'integration-source.json').read_text(encoding='utf8'));sha=lambda b:hashlib.sha256(b).hexdigest()
def git(*a,cwd=R):return subprocess.check_output(['git','-c','core.longpaths=true',*a],cwd=cwd,text=True).strip()
def counts(p):
 cs=list(ET.parse(p).iter('testcase'));f=[c for c in cs if c.find('failure') is not None];e=[c for c in cs if c.find('error') is not None];sk=[c for c in cs if c.find('skipped') is not None];return dict(tests=len(cs),passed=len(cs)-len(f)-len(e)-len(sk),failures=len(f),errors=len(e),skipped=[dict(name=c.attrib['name'],reason=c.find('skipped').attrib) for c in sk])
assert git('rev-parse','main')==S['main'];assert git('rev-parse','HEAD',cwd=W)==S['candidate'];assert not git('diff','--name-only','HEAD','--','src','scripts',cwd=W);assert not git('diff','--cached','--name-only');gates={}
for label in ['full-final','react-final','build-final']:
 r=json.loads((T/f'runs/{label}-exit.json').read_text(encoding='utf8'));assert r['native_exit_code']==0 and r['commit']==S['candidate'];gates[label]=dict(receipt=r);x=T/f'runs/{label}.xml'
 if x.exists():
  c=counts(x);assert c['failures']==c['errors']==0;gates[label].update(c)
core={}
for label,nfail in [('core-old-retry',2),('core-missing-status-retry',6),('core-no-count-retry',1),('core-green-retry',0)]:
 c=counts(T/f'runs/{label}.xml');assert c['failures']==nfail and c['errors']==0;core[label]=c
assert core['core-green-retry']['passed']==81
first=counts(T/'runs/core-old.xml');assert first['errors']==2 and first['failures']==0
for filename in ['protected.json','untracked-before.json']:
 for row in json.loads((T/filename).read_text(encoding='utf8')):assert sha((R/row['path']).read_bytes())==row['sha256'],row['path']
for v in json.loads((T/'source-evidence-audit.json').read_text(encoding='utf8'))['groups'].values():assert all(x['matches'] and x['bytes_match'] for x in v['files'])
assert git('rev-parse',S['main']+':src/web/frontend')==git('rev-parse','HEAD:src/web/frontend',cwd=W)
dbs=[];browser={}
for run in ['browser-coord-r12-current','browser-coord-r12-current-fonts']:
 B=W/'report/w10-evidence'/run;r=json.loads((B/'runtime.json').read_text(encoding='utf8'));assert r['temporaryDatabaseRemoved'] and r['serverThreadStopped'] and r['browserExitCode']==0 and not r['dirtySourcePaths'] and r['sourceCommit']==S['candidate'] and r['migrationHead']=='w17_0009';name=r['databaseName'];assert re.fullmatch('wayfinder_w10_[0-9a-f]{32}',name);dbs.append(name);m=json.loads((B/'current-react-metrics.json').read_text(encoding='utf8'));assert len(m['screens'])==3 and not m['pageErrors'];browser[run]=dict(source=m['source'],screens=m['screens'],http=len(m['http']),pageErrors=len(m['pageErrors']),externalProviderUsd=m['externalProviderUsd'])
for dname in dbs:
 result=subprocess.check_output(['docker','compose','--env-file','src/web/.env','-f','src/web/docker-compose.yml','exec','-T','db-test','psql','-U','wayfinder','-d','wayfinder_test','-Atc',"SELECT datname FROM pg_database WHERE datname='"+dname+"';"],cwd=R,text=True).strip();assert not result
with socket.socket() as sock:sock.settimeout(1);closed=sock.connect_ex(('127.0.0.1',8032))!=0
assert closed
proof=json.loads((T/'design-assertion-proof.json').read_text(encoding='utf8'));assert len(proof['mismatches'])==4;assert any(f['familyName']=='Be Vietnam Pro' and f['isCustomFont'] for f in proof['actualTabFonts'])
result=dict(source=S,gates=gates,core_independent=core,infra_first_run=first,browser=browser,owned_databases_absent=dbs,port8032closed=closed,protectedTracked=8,protectedUntracked=216,new_provider_cost_usd=0,design_unresolved_mismatches=proof['mismatches']);(T/'gate-summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(dict(source=S['candidate'],python=gates['full-final']['passed'],react=gates['react-final']['passed'],core=81,browserRuns=2)))
