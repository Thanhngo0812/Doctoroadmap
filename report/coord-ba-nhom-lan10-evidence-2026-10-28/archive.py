"""Archive R10 evidence without deleting or modifying its original source."""
import hashlib,json,stat
from pathlib import Path
R=Path('C:/Users/ngoco/Desktop/Doctoroadmap');T=Path(__file__).parent
W=R/'tmp/coord-r10-web-final-20261028';O=R/'report/coord-ba-nhom-lan10-evidence-2026-10-28'
TEXT={'.md','.py','.cjs','.js','.tsx','.ts','.json','.xml','.log','.txt','.html','.ps1','.diff','.toml'}
entries=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def safe(p):
    p.absolute().relative_to(R)
    for a in (p,*p.parents):
        if not a.exists():continue
        s=a.lstat();assert not stat.S_ISLNK(s.st_mode) and not getattr(s,'st_file_attributes',0)&stat.FILE_ATTRIBUTE_REPARSE_POINT,a
        if stat.S_ISREG(s.st_mode):assert s.st_nlink==1,a
def copy(src,rel):
    safe(src);dst=O/rel;safe(dst);raw=src.read_bytes();data=raw
    if src.suffix in TEXT:
        enc='utf-16' if raw.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig'
        content='\n'.join(x.rstrip(' \t') for x in raw.decode(enc).replace('\r\n','\n').replace('\r','\n').split('\n')).rstrip('\n')
        data=(content+('\n' if content else '')).encode()
    dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(data);safe(dst)
    entries.append(dict(path=rel,bytes=len(data),sha256=sha(data),raw_source=src.relative_to(R).as_posix(),raw_bytes=len(raw),raw_sha256=sha(raw),text_normalized=data!=raw))
O.mkdir(exist_ok=True)
for f in sorted((T/'runs').iterdir()):
    if f.is_file():copy(f,'runs/'+f.name)
metadata=['pinned.json','protected.json','untracked-before.json','untracked-protected.json','owner-decision.json','integration-source.json','product-comparison.json','candidate-copy.json','candidate-copy-final.json','candidate-copy-web-final.json','race-source.json','queue-cancelled-policy.json','worker-reports.json','gate-summary.json','browser-summary.json','merge-result.json','finish_checks.py','archive.py','verify_final.py','w12_real_race.cjs','w12_real_race_runtime.py','queue_full_web_final.py','run_frontend_web_final.py']
for n in metadata:copy(T/n,n)
for f in sorted(T.glob('queue-*.json')):
    if f.name!='queue-cancelled-policy.json':copy(f,'queue/'+f.name)
copy(W/'report/w06-evidence/fixture-copy.json','fixture-copy.json')
for group in ['web','core','design']:
    base=R/f'tmp/coord-r10-{group}-review-20261028'
    for f in sorted(base.iterdir()):
        if f.is_file() and (f.suffix in TEXT or f.suffix=='.png'):copy(f,group+'-review/'+f.name)
    if (base/'runs').exists():
        for f in sorted((base/'runs').iterdir()):
            if f.is_file():copy(f,group+'-review/runs/'+f.name)
for ticket in ['W04','W12']:
    parent='w04-account-react' if ticket=='W04' else 'w12-invitations-react'
    copy(R/f'tmp/coord-r10-web-review-20261028/{parent}/src/Review{ticket}.test.tsx',f'web-review/Review{ticket}.test.tsx')
for src,dst in [('author-w04-report.md','web-review/author-w04-report.md'),('author-w12-report.md','web-review/author-w12-report.md'),('author-core-report.md','core-review/author-report.md'),('author-design-report.md','design-review/author-report.md')]:copy(T/'worker-reports'/src,dst)
browser=W/'report/w04-react-evidence/browser-coord-r10-web-final'
for name in ['audit.json','runtime.json','taste-inspect/report.json','profile-1280-light.png','profile-390-dark.png','logout-confirm-390-dark.png','password-invalid-1280-light.png']:copy(browser/name,'browser-w04/'+name)
race=R/'tmp/coord-r10-acceptance-20261028/report/w12-react-evidence/browser-coord-r10-race2'
for n in ['race-proof.json','runtime.json','before-old-get.png','after-old-get.png']:copy(race/n,'w12-race/'+n)
local=[]
for base in [browser,race]:
    for f in sorted(base.rglob('*')):
        if f.is_file():safe(f);b=f.read_bytes();local.append(dict(path=f.relative_to(R).as_posix(),sha256=sha(b),bytes=len(b)))
localfile=T/'browser-local-files.json';localfile.write_bytes((json.dumps(dict(files=local,ordinary_files=True,raw_retained=True),indent=2)+'\n').encode());copy(localfile,'browser-local-files.json')
attr=O/'.gitattributes';attr.write_bytes(b'* -text\n');entries.append(dict(path='.gitattributes',bytes=attr.stat().st_size,sha256=sha(attr.read_bytes()),generated=True))
assert len(entries)==len({r['path'] for r in entries})
manifest=dict(files=entries,files_count=len(entries),normalization='Evidence text copies: BOM-aware UTF-8/LF, strip physical trailing space/tab and terminal blank lines; raw originals unchanged and both SHA256 retained.',new_provider_spend_usd=0,raw_browser_locations=[browser.relative_to(R).as_posix(),race.relative_to(R).as_posix()])
(O/'manifest.json').write_bytes((json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode())
for row in entries:assert sha((O/row['path']).read_bytes())==row['sha256']
print(json.dumps(dict(files=len(entries),bytes=sum(x['bytes'] for x in entries),raw_browser_files=len(local))))
