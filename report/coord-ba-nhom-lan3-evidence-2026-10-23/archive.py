"""Ordinary file copies, normalized text receipts and an independent SHA ledger."""
import hashlib, json, shutil, stat, subprocess
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path('C:/Users/ngoco/Desktop/Doctoroadmap')
SCRATCH=Path(__file__).parent
WT=ROOT/'tmp/coord-r3-acceptance-20261023'
OUT=ROOT/'report/coord-ba-nhom-lan3-evidence-2026-10-23'

def sha(data): return hashlib.sha256(data).hexdigest()
def safe(p):
    p=p.absolute()
    assert p.is_relative_to(ROOT),p
    for q in [p,*p.parents]:
        if not q.exists(): continue
        s=q.lstat()
        assert not (stat.S_ISLNK(s.st_mode) or getattr(s,'st_file_attributes',0)&stat.FILE_ATTRIBUTE_REPARSE_POINT),q
        if stat.S_ISREG(s.st_mode): assert s.st_nlink==1,q

normal=[]
def copy(source,relative):
    safe(source)
    raw=source.read_bytes();data=raw
    if source.suffix.lower() in {'.json','.log','.xml','.md','.py','.cjs','.txt'}:
        try:
            text=raw.decode('utf-8-sig').replace('\r\n','\n').replace('\r','\n')
            data=('\n'.join(line.rstrip() for line in text.splitlines()).rstrip()+'\n').encode()
            if source.suffix=='.json': assert json.loads(raw)==json.loads(data)
            if source.suffix=='.xml':
                def counts(v):
                    return [(r.tag,r.attrib) for r in ET.fromstring(v).iter() if r.tag in {'testsuite','testsuites'}]
                assert counts(raw)==counts(data)
        except UnicodeError: data=raw
    target=OUT/relative;safe(target);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(data)
    normal.append({'path':relative,'source':str(source.relative_to(ROOT)).replace('\\','/'),
        'raw_sha256':sha(raw),'archive_sha256':sha(data),'bytes':len(data)})

def write(relative,obj):
    p=OUT/relative;safe(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_bytes((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())

def main():
    assert not OUT.exists(),'Retain an existing archive, do not overwrite it'
    OUT.mkdir()
    (OUT/'.gitattributes').write_bytes(b'* -text\n')
    for p in sorted((SCRATCH/'runs').glob('*')):
        if p.is_file(): copy(p,'runs/'+p.name)
    for name in ['cloud-read.json','protected-shared-files.json','check_shared.py','design-browser.cjs','run_mutations.py','prepare_repro.py','finish_repro.py','finish_checks.py','acceptance-summary.json','repro-input.json','repro-finish.json','runtime-cleanup.json','executed-Learning.review-repro.test.tsx.txt']:
        p=SCRATCH/name
        if p.is_file():copy(p,name)
    for p in sorted((SCRATCH/'design-browser').glob('*')):
        if p.is_file():copy(p,'design-browser/'+p.name)
    for folder, dest in [('coord-w08-focused-review-20261023','web-review'),('coord-w24-review-f292f18','design-review'),('coord-r3-w15-review-20261023','core-review')]:
        source=ROOT/'tmp'/folder
        for p in sorted(source.iterdir()):
            if p.is_file() and p.suffix in {'.json','.md','.log','.xml','.cjs','.py','.tsx'}:
                copy(p,dest+'/'+p.name)
    copy(WT/'report/w06-evidence/fixture-copy.json','fixture-copy.json')
    for p in sorted((WT/'report/w08-evidence/mutations-coord-r3').glob('*')):
        if p.is_file():copy(p,'mutations/'+p.name)
    browser=WT/'report/w08-evidence/browser-coord-r3'
    for name in ['audit.json','runtime.json','learner.webm','owner.webm',
        'ready-1280-light.png','ready-390-dark-reduced.png','failure-390-light.png','source-768-light.png']:
        p=browser/name
        if p.is_file():copy(p,'browser/'+name)
    # Full browser run is retained locally; hashes make the unarchived images reviewable.
    write('browser-local-files.json',{'files':[{'path':str(p.relative_to(ROOT)).replace('\\','/'),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}
        for p in sorted(browser.rglob('*')) if p.is_file()]})
    # Only exported synthetic SQL rows, never development learner cache or artifacts.
    for rel in ['report/w15-evidence/sql/latest','report/w25-evidence/sql/latest']:
        folder=WT/rel
        if folder.exists():
            for p in sorted(folder.glob('*.json')):copy(p,'sql/'+folder.parents[1].name+'/'+p.name)
    protected=json.loads((SCRATCH/'protected-shared-files.json').read_text())
    assert all(sha((ROOT/p).read_bytes())==h for p,h in protected.items())
    copy(SCRATCH/'archive.py','archive.py')
    write('normalization.json',{'method':'UTF-8/LF, trailing whitespace trimmed; JSON semantic values and JUnit suite counts preserved','files':normal})
    files=[{'path':str(p.relative_to(OUT)).replace('\\','/'),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}
        for p in sorted(OUT.rglob('*')) if p.is_file()]
    write('manifest.json',{'files':files,'links_used':False,'new_provider_cost_usd':0})
    print(json.dumps({'archive':str(OUT),'files':len(files),'bytes':sum(f['bytes'] for f in files)}))

if __name__=='__main__':main()
