"""Build W17 handoff receipts from exact native files; retain historical raw evidence."""
import hashlib,json,re,shutil,subprocess,xml.etree.ElementTree as ET,zipfile
from pathlib import Path
root=Path.cwd();out=root/'report/w17-react-evidence'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=root,text=True).strip()
def read(name):return json.loads((out/name).read_text(encoding='utf-8-sig'))
def save(name,data):(out/name).write_bytes((json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
commit=git('rev-parse','HEAD');main='647149b3977f8b58e4c086e7521d4991ffc0e693'
assert not git('diff','HEAD','--name-only','--','src','scripts')
unchanged=['src/web/frontend/src/Auth.tsx','src/web/frontend/src/Account.tsx','src/web/frontend/src/Account.test.tsx','src/web/frontend/src/Invitations.tsx','src/web/frontend/src/Invitations.test.tsx','src/web/frontend/src/W11AuthReturn.repro.test.tsx']
assert not git('diff',main,'HEAD','--',*unchanged)
assert not git('diff',main,'HEAD','--','src/web/backend')
save('preserved-source.json',dict(sourceCommit=commit,main=main,unchangedFiles={p:sha(root/p) for p in unchanged},backendDiffEmpty=True))
manual=[]
for name in ['browser-manual1','browser-manual-legacy1']:
    data=read(name+'/manual-audit.json');old=data['sourceCommit']
    assert not git('diff',old,commit,'--','src','scripts') and not data.get('failure') and data['errors']==[]
    rows=[row for state in data['states'] for row in state.get('measured',[])]
    assert rows and all(row['contrast']>=4.5 and row['unobscured'] is True for row in rows)
    manual.append(dict(run=name,measuredSourceCommit=old,currentSourceCommit=commit,sourceAndScriptsDiffEmpty=True,nodes=len(rows),minimumContrast=min(row['contrast'] for row in rows),scope='Reuse only supplementary captures at original source; code/assets byte-equivalent to integrated source, not new measurements on canonical images'))
save('manual-a11y-equivalence.json',dict(runs=manual))
mutations={}
for mode in ['role-presence','read','callback','first','focus','repeat']:
    label=f'mutation-{mode}-{commit[:8]}'
    receipt=read(label+'-restore.json');assert receipt['sourceCommit']==commit and receipt['nativeExitCode']==1 and receipt['sourceRestored']
    assert receipt['sha256Before']==receipt['sha256After']==sha(root/'src/web/frontend/src/Admin.tsx')
    suites=list(ET.parse(out/(label+'.xml')).getroot().findall('testsuite'))
    failed=sum(int(s.get('failures',0)) for s in suites);errors=sum(int(s.get('errors',0)) for s in suites)
    assert failed>0 and errors==0
    failures=[e.attrib for e in ET.parse(out/(label+'.xml')).getroot().iter('failure')]
    assert all('TypeError' not in row.get('type','') for row in failures)
    mutations[mode]=dict(assertionFailures=failed,setupErrors=errors,nativeExitCode=1,restoredSha256=receipt['sha256After'])
save('mutation-summary.json',dict(sourceCommit=commit,mutations=mutations))
browsers={}
for name in ['browser-integrated','browser-legacy-integrated']:
    audit=read(name+'/audit.json');runtime=read(name+'/runtime.json')
    assert runtime['sourceCommit']==commit and runtime['dirtySourcePaths']==[] and runtime['browserExitCode']==0
    assert runtime['temporaryDatabaseRemoved'] and runtime['serverThreadStopped'] and not audit.get('failure') and not audit['pageErrors']
    assert all(not a['violations'] for a in audit['axe'])
    assert all(any(f['familyName']=='Be Vietnam Pro' and f['isCustomFont'] for f in row['liveFonts']['fonts']) for row in audit['screens'])
    if name=='browser-integrated':
        assert len(audit['configurations'])==12 and audit['heldRealGet']['clientFailure']=='net::ERR_ABORTED'
        assert not audit['designInspection']['findings']
        sql={row['stage']:row for row in audit['sql']};uid=runtime['accountIds']['binh'];owner=runtime['accountIds']['mai']
        assert not any(s['account_id']==uid for s in sql['disabled-sessions']['sessions'])
        assert next(row for row in sql['disabled-demoted']['users'] if row['id']==uid)['role']=='user'
        assert next(row for row in sql['enabled-demoted']['users'] if row['id']==uid)['status']=='active'
        assert sql['enabled-demoted']['firstAdminIds']==[owner]
    else:assert audit['sql'][0]['firstAdminIds']==[]
    browsers[name]=dict(sourceCommit=commit,configurations=len(audit['configurations']),images=len(audit['screens']),axe=len(audit['axe']),violations=0,incomplete=sum(len(row['incomplete']) for row in audit['axe']),http=len(audit['http']),sqlStages=len(audit['sql']),pageErrors=0,dbRemoved=True,providersCostUsd=0)
    save(name+'-http.json',dict(sourceCommit=commit,responses=audit['http']))
gates={}
for label in ['gate-build-integrated','gate-react-integrated','gate-python-integrated','gate-browser-integrated','gate-browser-legacy-integrated']:
    result=read(label+'/exit.json');assert result['commit']==commit and result['nativeExitCode']==0
    assert all(sha(root/p)==value for p,value in result['sourceSha256'].items())
    gates[label]={key:result[key] for key in ['commit','command','cwd','nativeExitCode','seconds']}
    xml=out/(label+'.xml')
    if xml.exists():
        suites=list(ET.parse(xml).getroot().findall('testsuite'));counts={key:sum(int(s.get(key,0)) for s in suites) for key in ['tests','failures','errors','skipped']}
        assert counts['failures']==counts['errors']==0;gates[label]['junit']=counts
save('gate-summary.json',dict(sourceCommit=commit,main=main,gates=gates,browsers=browsers,externalCostUsd=0))
copies=[]
for group in ['w15','w25']:
    source=root/f'report/{group}-evidence/sql/w17-react-gate-python-integrated';target=out/f'gate-python-integrated/{group}'
    files=sorted(source.glob('*.json'));assert files,source
    for path in files:
        assert path.stat().st_nlink==1 and not path.is_symlink();target.mkdir(parents=True,exist_ok=True);dst=target/path.name
        if not dst.exists():shutil.copyfile(path,dst)
        assert sha(path)==sha(dst);copies.append(dict(source=str(path.relative_to(root)).replace('\\','/'),copy=str(dst.relative_to(root)).replace('\\','/'),sha256=sha(dst)))
save('legacy-sql-copy-receipts.json',copies)
historical=[]
for folder in out.iterdir():
    if folder.is_dir() and (folder.name.startswith('browser-smoke') or folder.name in ['browser-matrix1','browser-final1','browser-final2','browser-legacy-final2']):
        historical.extend(p for p in folder.rglob('*') if p.is_file() and p.suffix.lower() in ['.json','.html','.log'])
with zipfile.ZipFile(out/'historical-browser-text.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for path in historical:archive.write(path,str(path.relative_to(out)))
save('historical-browser-index.json',dict(files=[dict(path=str(p.relative_to(root)).replace('\\','/'),sha256=sha(p)) for p in historical],imagesAndVideosRetainedLocal=True,archive='historical-browser-text.zip'))
tracked=[p for p in git('ls-files','src','scripts').splitlines() if (root/p).is_file()]
changed=git('diff','--name-only',main,'HEAD','--','src','scripts').splitlines()
with zipfile.ZipFile(out/'tested-source.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for p in changed:archive.write(root/p,p)
textFiles=[p for p in out.rglob('*') if p.is_file() and not any(parent.name.startswith('browser-smoke') or parent.name in ['browser-matrix1','browser-final1','browser-final2','browser-legacy-final2'] for parent in p.parents) and p.suffix in ['.json','.log','.html','.xml','.md']]
leaks=[]
for path in textFiles:
    raw=path.read_bytes();value=raw.decode('utf16') if raw.startswith((b'\xff\xfe',b'\xfe\xff')) else raw.decode('utf-8-sig')
    if re.search(r'(?:invitation|token)=[A-Za-z0-9_-]{24,}',value):leaks.append(str(path.relative_to(root)))
assert not leaks
save('privacy-scan.json',dict(rawFragmentPatternMatches=leaks,files=len(textFiles),scope='new text evidence; synthetic emails/UUIDs retained; password/CSRF/token/cookie values scrubbed by browser recorder'))
evidence=[p for p in out.rglob('*') if p.is_file() and p.name!='manifest.json' and not any(parent.name.startswith('browser-smoke') or parent.name in ['browser-matrix1','browser-final1','browser-final2','browser-legacy-final2'] for parent in p.parents)]
evidence+=list(root.glob('report/w17-react-evidence-*.py'))+list(root.glob('report/w17-react-evidence-*.cjs'))
evidence.append(root/'report/w17-react-tich-hop-2026-10-29.md')
evidence.append(root/'report/.gitattributes')
design=['design/preview/components.html','design/tokens/tokens.css','design/tokens/tokens.json','design/Artboard 24.png','design/Artboard 28.png','doc/web-thiet-ke-giao-dien-spec.md']
save('manifest.json',dict(sourceCommit=commit,main=main,designSha256={p:sha(root/p) for p in design},sourceSha256={p:sha(root/p) for p in tracked},evidenceSha256={str(p.relative_to(root)).replace('\\','/'):sha(p) for p in sorted(evidence)}))
print(json.dumps(dict(sourceCommit=commit,sourceFiles=len(tracked),evidenceFiles=len(evidence),sqlFiles=len(copies),browsers=browsers)))
