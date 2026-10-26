"""Scoped ordinary copies of review receipts, with source and normalized SHA ledgers."""
import hashlib,json,stat
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path('C:/Users/ngoco/Desktop/Doctoroadmap')
HERE=Path(__file__).parent
WT=ROOT/'tmp/coord-r5-acceptance-20261025'
SAFE=ROOT/'tmp/coord-r5-core-design-20261025'
OUT=ROOT/'report/coord-ba-nhom-lan5-evidence-2026-10-25'
normal=[]
def sha(data):return hashlib.sha256(data).hexdigest()
def safe(path):
    path=path.absolute();assert path.is_relative_to(ROOT)
    for part in [path,*path.parents]:
        if not part.exists():continue
        record=part.lstat()
        assert not (stat.S_ISLNK(record.st_mode) or getattr(record,'st_file_attributes',0)&stat.FILE_ATTRIBUTE_REPARSE_POINT),str(part)
        if stat.S_ISREG(record.st_mode):assert record.st_nlink==1,str(part)
def copy(source,relative):
    safe(source);raw=source.read_bytes();data=raw
    if source.suffix.lower() in {'.json','.log','.xml','.md','.py','.mjs','.cjs','.tsx','.txt','.ini'}:
        try:
            text=raw.decode('utf-8-sig').replace('\r\n','\n').replace('\r','\n')
            data=('\n'.join(line.rstrip() for line in text.splitlines()).rstrip()+'\n').encode()
            if source.suffix=='.json':assert json.loads(raw)==json.loads(data)
            if source.suffix=='.xml':
                def metadata(value):return [(r.tag,r.attrib) for r in ET.fromstring(value).iter() if r.tag in {'testsuite','testsuites','testcase'}]
                assert metadata(raw)==metadata(data)
        except UnicodeError:data=raw
    target=OUT/relative;safe(target);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    normal.append({'path':relative,'source':source.relative_to(ROOT).as_posix(),'raw_sha256':sha(raw),
                   'archive_sha256':sha(data),'bytes':len(data)})
def write(relative,data):
    target=OUT/relative;safe(target);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes((json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode())

assert not OUT.exists(),'Preserve existing review archives'
OUT.mkdir();(OUT/'.gitattributes').write_bytes(b'* -text\n')
for path in sorted((HERE/'runs').iterdir()):
    if path.is_file():copy(path,'runs/'+path.name)
for name in ['archive.py','prepare.py','worker-heads.json','protected-shared-files.json','check_shared.py',
             'candidate-copy.json','safe-candidate-copy.json','copy_candidate.py','copy_safe_candidate.py',
             'finish_checks.py','acceptance-summary.json','runtime-cleanup.json','design-browser.cjs',
             'run_mutations.py','merge-result.json','merge_safe.py','provenance.json',
             'inspect_browser.py','browser-independent.json']:
    copy(HERE/name,name)
for source,dest in [('coord-r5-web-review-20261025','web-review'),('coord-r5-core-review-20261025','core-review'),
                    ('coord-r5-design-review-20261025','design-review')]:
    for path in sorted((ROOT/'tmp'/source).iterdir()):
        if path.is_file() and path.suffix in {'.json','.log','.xml','.md','.py','.mjs','.cjs','.tsx','.txt','.ini','.zip'}:
            copy(path,dest+'/'+path.name)
for path in sorted((HERE/'design-browser').iterdir()):
    if path.is_file():copy(path,'design-browser/'+path.name)
copy(SAFE/'report/w06-evidence/fixture-copy.json','fixture-copy.json')
for path in sorted((WT/'report/w09-evidence/mutations-coord-r5').iterdir()):
    if path.is_file():copy(path,'mutations/'+path.name)
browser=WT/'report/w09-evidence/browser-coord-r5'
for name in ['audit.json','runtime.json','answered-1280-light.png','answered-390-dark-reduced.png',
             'artifact-preview-1280-dark-reduced.png','options-390-light.png']:
    path=browser/name
    if path.exists():copy(path,'browser/'+name)
write('browser-local-files.json',{'files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}
     for p in sorted(browser.rglob('*')) if p.is_file()],
     'note':'All raw screenshots/videos remain at local paths, no deletion or worktree cleanup.'})
for relative in ['report/w15-evidence/sql/latest','report/w25-evidence/sql/latest']:
    folder=SAFE/relative
    if folder.exists():
        for path in sorted(folder.glob('*.json')):copy(path,'sql/'+folder.parents[1].name+'/'+path.name)
protected=json.loads((HERE/'protected-shared-files.json').read_text())
assert all(sha((ROOT/p).read_bytes())==h for p,h in protected.items())
write('normalization.json',{'method':'UTF-8/LF; trailing whitespace trimmed, JSON values/JUnit test attributes unchanged','files':normal})
files=[{'path':p.relative_to(OUT).as_posix(),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size} for p in sorted(OUT.rglob('*')) if p.is_file()]
write('manifest.json',{'files':files,'links_used':False,'new_provider_cost_usd':0,'pushed':False})
print(json.dumps({'files':len(files),'bytes':sum(r['bytes'] for r in files)}))
