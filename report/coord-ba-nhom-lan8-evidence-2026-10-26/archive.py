"""Archive only coordinator evidence; raw originals are retained at their source paths."""
import hashlib,json,stat
from pathlib import Path
ROOT=Path('C:/Users/ngoco/Desktop/Doctoroadmap')
TOOLS=ROOT/'tmp/coord-r8-tools-20261026'
WT=ROOT/'tmp/coord-r8-acceptance-20261026'
OUT=ROOT/'report/coord-ba-nhom-lan8-evidence-2026-10-26'
TEXT={'.md','.py','.cjs','.js','.tsx','.ts','.json','.xml','.log','.txt','.gitattributes'}
entries=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def safe(p):
    p.absolute().relative_to(ROOT)
    for a in (p,*p.parents):
        if not a.exists():continue
        m=a.lstat()
        assert not stat.S_ISLNK(m.st_mode) and not getattr(m,'st_file_attributes',0)&stat.FILE_ATTRIBUTE_REPARSE_POINT,a
        if stat.S_ISREG(m.st_mode):assert m.st_nlink==1,a

def copy(src,rel):
    safe(src);dst=OUT/rel;safe(dst)
    raw=src.read_bytes();data=raw
    if src.suffix in TEXT or src.name=='.gitattributes':
        normalized=raw.decode('utf-8-sig').replace('\r\n','\n').replace('\r','\n')
        content='\n'.join(line.rstrip(' \t') for line in normalized.split('\n')).rstrip('\n')
        data=(content+('\n' if content else '')).encode('utf-8')
    dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(data);safe(dst)
    entries.append(dict(path=rel,sha256=sha(data),bytes=len(data),raw_source=str(src.relative_to(ROOT)).replace('\\','/'),raw_sha256=sha(raw),raw_bytes=len(raw),text_normalized=data!=raw))

OUT.mkdir(exist_ok=True)
for f in sorted((TOOLS/'runs').iterdir()):
    if f.is_file():copy(f,'runs/'+f.name)
for name in ['pinned.json','protected.json','reservation.json','integration-source.json','product-comparison.json','openapi-operations.json','candidate-copy.json','environment-failure.json','merge-result.json','gate-summary.json','browser-summary.json','browser-invocation.json','finish_checks.py','copy_candidate.py','verify_final.py','archive.py']:
    copy(TOOLS/name,name)
copy(WT/'report/w06-evidence/fixture-copy.json','fixture-copy.json')
for group in ['web','core','design']:
    base=ROOT/f'tmp/coord-r8-{group}-review-20261026'
    for f in sorted(base.iterdir()):
        if f.is_file() and f.suffix in TEXT:copy(f,group+'-review/'+f.name)
    if (base/'runs').exists():
        for f in sorted((base/'runs').iterdir()):
            if f.is_file():copy(f,group+'-review/runs/'+f.name)
copy(ROOT/'tmp/coord-r8-core-review-20261026/src/web/backend/tests/test_coord_w04_concurrency.py','core-review/test_coord_w04_concurrency.py')
browser=WT/'report/w10-r7-evidence/browser-coord-r8-ready'
for name in ['audit.json','runtime.json','taste-inspect/report.json']:
    copy(browser/name,'browser/'+name)
for name in ['quiz-ready-1280-light.png','document-view-390-light.png','assistant-hour-limit-390-dark-reduced.png','document-create-768-light.png']:
    copy(browser/name,'browser/'+name)
local=[]
for f in sorted(browser.rglob('*')):
    if f.is_file():
        safe(f);raw=f.read_bytes();local.append(dict(path=str(f.relative_to(ROOT)).replace('\\','/'),sha256=sha(raw),bytes=len(raw)))
localfile=TOOLS/'browser-local-files.json';localfile.write_text(json.dumps(dict(files=local,ordinary_files=True,raw_retained=True),indent=2)+'\n',encoding='utf-8')
copy(localfile,'browser-local-files.json')
attributes=OUT/'.gitattributes';attributes.write_bytes(b'* -text\n')
entries.append(dict(path='.gitattributes',sha256=sha(attributes.read_bytes()),bytes=attributes.stat().st_size,generated=True))
manifest=dict(files=entries,normalization='QA text copies: UTF-8/LF, remove trailing physical space/tab and terminal blank lines; raw originals unchanged with before/after SHA-256.',files_count=len(entries),raw_browser_location=str(browser.relative_to(ROOT)).replace('\\','/'),new_provider_spend_usd=0)
(OUT/'manifest.json').write_bytes((json.dumps(manifest,indent=2,ensure_ascii=False)+'\n').encode('utf-8'))
for row in entries:
    assert sha((OUT/row['path']).read_bytes())==row['sha256']
print(json.dumps(dict(files=len(entries),bytes=sum(x['bytes'] for x in entries),raw_browser_files=len(local))))
