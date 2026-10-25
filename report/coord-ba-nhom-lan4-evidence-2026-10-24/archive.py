"""Archive review receipts through ordinary files; retain raw browser evidence locally."""
import hashlib, json, stat
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path('C:/Users/ngoco/Desktop/Doctoroadmap')
SCRATCH = Path(__file__).parent
WT = ROOT/'tmp/coord-r4-acceptance-20261024'
OUT = ROOT/'report/coord-ba-nhom-lan4-evidence-2026-10-24'
normal = []

def sha(data):
    return hashlib.sha256(data).hexdigest()

def safe(path):
    path = path.absolute()
    assert path.is_relative_to(ROOT)
    for part in (path, *path.parents):
        if not part.exists():
            continue
        record = part.lstat()
        assert not (stat.S_ISLNK(record.st_mode) or getattr(record,'st_file_attributes',0)&stat.FILE_ATTRIBUTE_REPARSE_POINT), str(part)
        if stat.S_ISREG(record.st_mode):
            assert record.st_nlink == 1, str(part)

def copy(source, relative):
    safe(source)
    raw = source.read_bytes()
    data = raw
    if source.suffix.lower() in {'.json','.log','.xml','.md','.py','.cjs','.txt','.ini'}:
        try:
            text = raw.decode('utf-8-sig').replace('\r\n','\n').replace('\r','\n')
            data = ('\n'.join(line.rstrip() for line in text.splitlines()).rstrip()+'\n').encode()
            if source.suffix == '.json':
                assert json.loads(raw) == json.loads(data)
            if source.suffix == '.xml':
                def suites(value):
                    return [(row.tag,row.attrib) for row in ET.fromstring(value).iter() if row.tag in {'testsuite','testsuites'}]
                assert suites(raw) == suites(data)
        except UnicodeError:
            data = raw
    target = OUT/relative
    safe(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    normal.append({'path':relative, 'source':source.relative_to(ROOT).as_posix(),
                   'raw_sha256':sha(raw), 'archive_sha256':sha(data), 'bytes':len(data)})

def write(relative, data):
    target = OUT/relative
    safe(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes((json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode())

def entry(path):
    return {'path':path.relative_to(OUT).as_posix(), 'sha256':sha(path.read_bytes()), 'bytes':path.stat().st_size}

def main():
    assert not OUT.exists(), 'Preserve an existing archive'
    OUT.mkdir()
    (OUT/'.gitattributes').write_bytes(b'* -text\n')
    for path in sorted((SCRATCH/'runs').iterdir()):
        if path.is_file():
            copy(path,'runs/'+path.name)
    for name in ['archive.py','finish_checks.py','copy_candidate.py','candidate-copy.json','runtime-cleanup.json',
                 'acceptance-summary.json','browser-independent.json','provenance.json','design-browser.cjs',
                 'run_mutations.py','verify_browser.py','check_shared.py','protected-shared-files.json',
                 'merge_current.py','merge-result.json','record_merge.py','render_docs.py','transfer-stats.json',
                 'runtime-cleanup-initial.json','runtime-cleanup-failed-browser.json']:
        copy(SCRATCH/name,name)
    for folder,destination in [('coord-r4-web-review-20261024','web-review'),
                               ('coord-r4-core-review-20261024','core-review'),
                               ('coord-r4-design-review-20261024','design-review')]:
        for path in sorted((ROOT/'tmp'/folder).iterdir()):
            if path.is_file() and path.suffix in {'.json','.md','.log','.xml','.cjs','.py','.ini'}:
                copy(path,destination+'/'+path.name)
    for path in sorted((SCRATCH/'design-browser').iterdir()):
        if path.is_file():
            copy(path,'design-browser/'+path.name)
    copy(WT/'report/w06-evidence/fixture-copy.json','fixture-copy.json')
    for path in sorted((WT/'report/w08-evidence/mutations-coord-r4').iterdir()):
        if path.is_file():
            copy(path,'mutations/'+path.name)
    browser = WT/'report/w08-evidence/browser-coord-r4-current-retry'
    for name in ['audit.json','runtime.json','ready-1280-light.png','ready-390-dark-reduced.png',
                 'failure-390-light.png','source-768-light.png','related-saved-1280-dark-reduced.png']:
        copy(browser/name,'browser/'+name)
    write('browser-local-files.json', {'files':[
        {'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path.read_bytes()),'bytes':path.stat().st_size}
        for path in sorted(browser.rglob('*')) if path.is_file()],
        'note':'Full raw browser output, including videos, remains at these local paths; no files removed.'})
    for name in ['audit.json','runtime.json']:
        copy(WT/'report/w08-evidence/browser-coord-r4'/name,'browser-initial/'+name)
        copy(WT/'report/w08-evidence/browser-coord-r4-current'/name,'browser-font-failure/'+name)
    for relative in ['report/w15-evidence/sql/latest','report/w25-evidence/sql/latest']:
        folder = WT/relative
        if folder.exists():
            for path in sorted(folder.glob('*.json')):
                copy(path,'sql/'+folder.parents[1].name+'/'+path.name)
    protected = json.loads((SCRATCH/'protected-shared-files.json').read_text())
    assert all(sha((ROOT/path).read_bytes()) == digest for path,digest in protected.items())
    write('normalization.json', {'method':'UTF-8/LF and trailing whitespace trimmed; JSON values and JUnit suite metadata unchanged', 'files':normal})
    files = [entry(path) for path in sorted(OUT.rglob('*')) if path.is_file()]
    write('manifest.json', {'files':files, 'links_used':False, 'new_provider_cost_usd':0})
    print(json.dumps({'files':len(files), 'bytes':sum(row['bytes'] for row in files)}))

if __name__ == '__main__':
    main()
