"""Copy only R9 coordinator evidence; preserve every raw original and failed run."""
import hashlib,json,stat
from pathlib import Path
R=Path('C:/Users/ngoco/Desktop/Doctoroadmap'); T=Path(__file__).parent
W=R/'tmp/coord-r9-acceptance-20261027'; O=R/'report/coord-ba-nhom-lan9-evidence-2026-10-27'
TEXT={'.md','.py','.cjs','.js','.tsx','.ts','.json','.xml','.log','.txt','.html'}
entries=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def safe(p):
    p.absolute().relative_to(R)
    for a in (p,*p.parents):
        if not a.exists():continue
        m=a.lstat()
        assert not stat.S_ISLNK(m.st_mode) and not getattr(m,'st_file_attributes',0)&stat.FILE_ATTRIBUTE_REPARSE_POINT,a
        if stat.S_ISREG(m.st_mode):assert m.st_nlink==1,a
def copy(src,rel):
    safe(src);dst=O/rel;safe(dst);raw=src.read_bytes();data=raw
    if src.suffix in TEXT:
        encoding='utf-16' if raw.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig'
        content='\n'.join(x.rstrip(' \t') for x in raw.decode(encoding).replace('\r\n','\n').replace('\r','\n').split('\n')).rstrip('\n')
        data=(content+('\n' if content else '')).encode()
    dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(data);safe(dst)
    entries.append(dict(path=rel,sha256=sha(data),bytes=len(data),raw_source=src.relative_to(R).as_posix(),raw_sha256=sha(raw),raw_bytes=len(raw),text_normalized=data!=raw))
O.mkdir(exist_ok=True)
for f in sorted((T/'runs').iterdir()):
    if f.is_file():copy(f,'runs/'+f.name)
metadata=['pinned.json','protected.json','protected-resume.json','reservation.json','integration-source.json','product-comparison.json','candidate-copy.json','harness-integration.json','json-capture-fix.json','interrupted-runs.json','queue-setup-note.json','merge-result.json','gate-summary.json','browser-summary.json','openapi-operations.json','finish_checks.py','copy_candidate.py','archive.py','verify_final.py','queue_full_rebased.py','recheck_frontend.py']
for name in metadata:copy(T/name,name)
for f in sorted(T.glob('queue-*.json')):copy(f,'queue/'+f.name)
for f in sorted(T.glob('queue-*.log')):copy(f,'queue/'+f.name)
copy(W/'report/w06-evidence/fixture-copy.json','fixture-copy.json')
for group in ['web','core','design']:
    base=R/f'tmp/coord-r9-{group}-review-20261027'
    for f in sorted(base.iterdir()):
        if f.is_file() and (f.suffix in TEXT or f.suffix=='.png'):copy(f,group+'-review/'+f.name)
    if (base/'runs').exists():
        for f in sorted((base/'runs').iterdir()):
            if f.is_file():copy(f,group+'-review/runs/'+f.name)
copy(R/'tmp/coord-r9-core-review-20261027/tests/test_independent_w12.py','core-review/test_independent_w12.py')
copy(R/'tmp/coord-r9-design-review-20261027/tests/unit/presentation/test_tokens_and_wcag.py','design-review/test_tokens_and_wcag.py')
copy(W/'scripts/test_w10_library_filter_vm.cjs','design-review/test_w10_library_filter_vm.cjs')
browser=W/'report/w16-react-evidence/browser-coord-r9-final'
for name in ['audit.json','runtime.json','taste-inspect/report.json']:
    copy(browser/name,'browser/'+name)
for name in ['usage-35-1280-light.png','usage-100-1280-light.png','usage-85-390-dark.png','chat-limit-390-dark-reduced.png']:
    copy(browser/name,'browser/'+name)
local=[]
for f in sorted(browser.rglob('*')):
    if f.is_file():
        safe(f);raw=f.read_bytes();local.append(dict(path=f.relative_to(R).as_posix(),sha256=sha(raw),bytes=len(raw)))
localfile=T/'browser-local-files.json';localfile.write_bytes((json.dumps(dict(files=local,ordinary_files=True,raw_retained=True),indent=2)+'\n').encode())
copy(localfile,'browser-local-files.json')
attr=O/'.gitattributes';attr.write_bytes(b'* -text\n');entries.append(dict(path='.gitattributes',sha256=sha(attr.read_bytes()),bytes=attr.stat().st_size,generated=True))
assert len(entries)==len({r['path'] for r in entries})
manifest=dict(files=entries,files_count=len(entries),normalization='QA text copies: UTF-8/LF; remove physical trailing spaces/tabs and terminal blank lines; raw unchanged, both SHA-256 recorded.',raw_browser_location=browser.relative_to(R).as_posix(),new_provider_spend_usd=0)
(O/'manifest.json').write_bytes((json.dumps(manifest,indent=2,ensure_ascii=False)+'\n').encode())
for row in entries:assert sha((O/row['path']).read_bytes())==row['sha256']
print(json.dumps(dict(files=len(entries),bytes=sum(x['bytes'] for x in entries),raw_browser_files=len(local))))
