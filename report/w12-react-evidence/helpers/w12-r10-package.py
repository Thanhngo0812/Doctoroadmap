"""Package exact source/native receipts; never rewrite prior-round evidence."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'report/w12-react-evidence'

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def save(name, value): (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def git(*args): return subprocess.check_output(['git',*args],cwd=ROOT)
def read(name): return json.loads((OUT/name).read_text(encoding='utf-8-sig'))

def main():
    commit=git('rev-parse','HEAD').decode().strip()
    assert git('diff','HEAD','--name-only','--','src','scripts')==b''
    auth=(ROOT/'src/web/frontend/src/Auth.tsx').read_bytes().replace(b'\r\n',b'\n')
    base=git('show','26d43b83:src/web/frontend/src/Auth.tsx').replace(b'\r\n',b'\n')
    assert auth.split(b'export function AuthPage')[0]==base.split(b'export function AuthPage')[0]
    for path in ['src/web/frontend/src/Account.tsx','src/web/frontend/src/Account.test.tsx']:
        assert (ROOT/path).read_bytes().replace(b'\r\n',b'\n')==git('show','26d43b83:'+path).replace(b'\r\n',b'\n')
    save('r10-auth-preservation.json',dict(sourceCommit=commit,main='26d43b83ba0d3f265f28ea7d3220f924ba96a97d',providerPrefixExact=True,accountSourceAndTestsExact=True,authDiffWithMain=git('diff','26d43b83','HEAD','--','src/web/frontend/src/Auth.tsx').decode()))
    audit=read('browser-r10-final/audit.json');runtime=read('browser-r10-final/runtime.json')
    assert runtime['sourceCommit']==commit and runtime['dirtySourcePaths']==[] and runtime['temporaryDatabaseRemoved'] and runtime['serverThreadStopped']
    assert runtime['browserExitCode']==0 and not audit.get('failure') and not audit['pageErrors'] and not audit['tokenLeaks']
    assert len(audit['serializedReads'])==4 and all(r['sqlPending'] and r['visibleAfterReload'] and r['posts']==1 for r in audit['serializedReads'])
    for row in audit['serializedReads']:
        assert any(item['email_normalized']==row['email'] and item['course_id']==row['cid'] and item['status']=='pending' for item in runtime['independentSqlFinal']['invitations'])
    mutations={}
    for mode,failed in [('old',3),('button',3),('handler',2)]:
        label=f'r10-{mode}-{commit[:8]}-red'
        receipt=read(label+'-restoration.json');assert receipt['nativeExitCode']==1 and receipt['restored'] and receipt['sourceCommit']==commit
        assert receipt['beforeSha256']==receipt['restoredSha256']==sha(ROOT/'src/web/frontend/src/Invitations.tsx')
        tree=ET.parse(OUT/(label+'.xml')).getroot();suite=list(tree.findall('testsuite'))
        assert sum(int(s.get('failures',0)) for s in suite)==failed and sum(int(s.get('errors',0)) for s in suite)==0
        mutations[mode]=dict(assertionFailures=failed,setupErrors=0,nativeExitCode=1,sourceRestored=True,sha256=receipt['restoredSha256'])
    save('r10-mutation-summary.json',dict(sourceCommit=commit,mutations=mutations))
    save('r10-http-examples.json',dict(sourceCommit=commit,serializedReads=audit['serializedReads'],http=[row for row in audit['http'] if row['stage'].startswith('serialized-get')]))
    receipts=[]
    for group in ['w15','w25']:
        source=ROOT/f'report/{group}-evidence/sql/w12-react-r10-gate-python-final'
        target=OUT/f'r10-gate-python-final/{group}'
        for src in sorted(source.glob('*.json')):
            assert not src.is_symlink() and src.stat().st_nlink==1
            dst=target/src.name;target.mkdir(exist_ok=True,parents=True)
            if not dst.exists(): shutil.copyfile(src,dst)
            assert sha(src)==sha(dst)
            receipts.append(dict(source=str(src.relative_to(ROOT)).replace('\\','/'),destination=str(dst.relative_to(ROOT)).replace('\\','/'),sha256=sha(src)))
    save('r10-sql-copy-receipts.json',receipts)
    gates={}
    for label in ['r10-gate-python-final','r10-gate-react-final2','r10-gate-build-final2','r10-gate-browser-final']:
        row=read(label+'/exit.json');assert row['nativeExitCode']==0 and row['commit']==commit
        gates[label]={key:row[key] for key in ['commit','command','nativeExitCode','seconds']}
        xml=OUT/(label+'.xml')
        if xml.exists():
            root=ET.parse(xml).getroot();suites=[root] if root.tag=='testsuite' else list(root.findall('testsuite'))
            gates[label]['junit']={key:sum(int(s.get(key,0)) for s in suites) for key in ['tests','failures','errors','skipped']}
            assert gates[label]['junit']['failures']==gates[label]['junit']['errors']==0
    save('r10-gate-summary.json',dict(sourceCommit=commit,main='26d43b83ba0d3f265f28ea7d3220f924ba96a97d',gates=gates,browser=dict(configurations=len(audit['configurations']),images=len(audit['screens']),axe=len(audit['accessibility']),violations=sum(len(row['violations']) for row in audit['accessibility']),http=len(audit['http']),serializedReads=len(audit['serializedReads']),sqlStages=len(audit['sql']),liveFonts=audit['liveFonts'],pageErrors=audit['pageErrors'],tokenLeaks=audit['tokenLeaks']),externalCostUsd=0))
    tracked=[p for p in git('ls-files','src','scripts').decode().splitlines() if (ROOT/p).is_file()]
    changed=['src/web/frontend/src/Invitations.tsx','src/web/frontend/src/Invitations.test.tsx','scripts/w12_react_runtime.py','scripts/w12_react_browser.cjs','src/web/frontend/src/Auth.tsx']
    with zipfile.ZipFile(OUT/'r10-source-snapshot.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for path in changed:archive.write(ROOT/path,path)
    files=[p for p in OUT.rglob('*') if p.is_file() and (p.relative_to(OUT).parts[0].startswith('r10-') or p.relative_to(OUT).parts[0]=='browser-r10-final' or p.name.startswith('w12-r10-')) and p.name!='r10-manifest.json']
    hits=[]
    for path in files:
        if path.suffix not in {'.json','.log','.html','.xml','.md','.py'}:continue
        data=path.read_text(encoding='utf-8-sig')
        if re.search(r'(?:invitation|token)=[A-Za-z0-9_-]{16,}',data):hits.append(str(path.relative_to(ROOT)))
    assert hits==[],hits
    save('r10-privacy-scan.json',dict(rawFragmentPatternMatches=hits,filesScanned=len(files),scope='New text evidence only; synthetic SQL IDs/emails retained, token/CSRF/password values redacted by harness'))
    files.append(OUT/'r10-privacy-scan.json')
    save('r10-manifest.json',dict(sourceCommit=commit,main='26d43b83ba0d3f265f28ea7d3220f924ba96a97d',sourceSha256={p:sha(ROOT/p) for p in tracked},evidenceSha256={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in sorted(set(files))}))
    print(json.dumps(dict(sourceCommit=commit,sourceFiles=len(tracked),evidenceFiles=len(set(files)),sqlFiles=len(receipts))))

if __name__=='__main__': main()
