import hashlib,json,re,socket,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
R=Path('C:/Users/ngoco/Desktop/Doctoroadmap');W=Path('C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-r11-final-20261028');T=Path('C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-r11-tools-20261028');S=json.loads((T/'final-source.json').read_text());sha=lambda b:hashlib.sha256(b).hexdigest()
def git(*a,cwd=R):return subprocess.check_output(['git','-c','core.longpaths=true',*a],cwd=cwd,text=True).strip()
def junit(p):
 cs=list(ET.parse(p).iter('testcase'));f=[c for c in cs if c.find('failure') is not None];e=[c for c in cs if c.find('error') is not None];sk=[c for c in cs if c.find('skipped') is not None]
 return dict(tests=len(cs),passed=len(cs)-len(f)-len(e)-len(sk),failures=len(f),errors=len(e),skipped=[dict(name=c.attrib['name'],reason=c.find('skipped').attrib) for c in sk])
assert git('rev-parse','HEAD',cwd=W)==S['candidate'];assert git('rev-parse','main')==S['main'];assert git('branch','--show-current')=='main';assert not git('diff','--cached','--name-only')
gates={}
for label in ['full-final','react-received-main','build-final','browser-w12']:
 receipt=json.loads((T/f'runs/{label}-exit.json').read_text());assert receipt['native_exit_code']==0 and receipt['commit']==S['candidate'],(label,receipt);gates[label]=dict(receipt=receipt)
 p=T/f'runs/{label}.xml'
 if p.exists():
  j=junit(p);assert j['failures']==j['errors']==0;gates[label].update(j)
mutants={}
for label,failures in [('web-old',3),('web-button',3),('web-handler',2)]:
 j=junit(T/f'runs/{label}.xml');assert j['failures']==failures and j['errors']==0;mutants[label]=j
core=junit(T/'runs/core-independent.xml');assert core['failures']==1 and core['errors']==0 and core['passed']==1
for file in ['protected.json','untracked-before.json']:
 for row in json.loads((T/file).read_text()):assert sha((R/row['path']).read_bytes())==row['sha256'],row['path']
assert not git('diff','--name-only','HEAD','--','src','scripts',cwd=W)
pc=json.loads((T/'product-comparison.json').read_text());assert pc['frontendTreePinned']==pc['frontendTreeCandidate'] and pc['runtimeScriptsEqual']
rt=json.loads((W/'report/w12-react-evidence/browser-coord-r11-final/runtime.json').read_text());assert rt['temporaryDatabaseRemoved'] and rt['serverThreadStopped'] and rt['browserExitCode']==0 and not rt['dirtySourcePaths'];name=rt['databaseName'];assert re.fullmatch('wayfinder_w12_react_[0-9a-f]{32}',name)
left=subprocess.check_output(['docker','compose','--env-file','src/web/.env','-f','src/web/docker-compose.yml','exec','-T','db-test','psql','-U','wayfinder','-d','wayfinder_test','-Atc',"SELECT datname FROM pg_database WHERE datname='"+name+"';"],cwd=R,text=True).strip();assert not left
with socket.socket() as sock:sock.settimeout(1);closed=sock.connect_ex(('127.0.0.1',8027))!=0
assert closed
b=json.loads((T/'browser-summary.json').read_text());assert b['axeViolations']==b['pageErrors']==0 and not b['dirtySourcePaths'];assert all(b['proof'].values());assert all(r['sqlPending'] and r['visibleAfterReload'] and r['postCount']==1 for r in b['serializedReads'])
result=dict(source=S,gates=gates,mutations=mutants,core_independent=core,browser=b,protected_tracked=8,protected_untracked=216,owned_runtime_database_absent=name,port_8027_closed=closed,new_provider_cost_usd=0)
(T/'gate-summary.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8');print(json.dumps(dict(source=S['candidate'],python=gates['full-final']['passed'],react=gates['react-received-main']['passed'],protected_untracked=216,browser_screens=b['screens'])))
