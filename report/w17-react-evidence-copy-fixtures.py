"""Copy only fixed development manifests, verify source/destination, never overwrite conflicts."""
from pathlib import Path
import hashlib,json,shutil

target=Path.cwd();root=target.parents[1];out=target/'report/w17-react-evidence';out.mkdir(exist_ok=True)
files=[]
for bundle in json.loads((target/'report/w06-fixtures-evidence-2026-10-20/bundles.json').read_text(encoding='utf-8-sig'))['bundles']:
    manifest=root/bundle['manifest'];assert hashlib.sha256(manifest.read_bytes()).hexdigest()==bundle['manifest_sha256'];snapshot=root/bundle['snapshot']
    for item in json.loads(manifest.read_text(encoding='utf-8-sig'))['files']:
        src=snapshot/item['path'];dst=target/item['path']
        assert src.resolve().is_relative_to(snapshot.resolve()) and dst.resolve().is_relative_to(target.resolve())
        assert not any(p.is_symlink() or p.is_junction() for p in [src,*src.parents] if p.is_relative_to(snapshot)) and src.stat().st_nlink==1
        assert hashlib.sha256(src.read_bytes()).hexdigest()==item['sha256']
        if dst.exists():assert hashlib.sha256(dst.read_bytes()).hexdigest()==item['sha256'],str(dst)
        else:dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
        assert dst.stat().st_nlink==1 and not dst.is_symlink() and hashlib.sha256(dst.read_bytes()).hexdigest()==item['sha256']
        files.append(dict(path=item['path'],sourceSha256=item['sha256'],destinationSha256=item['sha256']))
meta=json.loads((target/'report/w15-evidence/candidate.json').read_text(encoding='utf-8-sig'));src=root/meta['candidate'];dst=target/meta['staged_copy']
assert src.resolve().is_relative_to((root/'document-data/train').resolve()) and hashlib.sha256(src.read_bytes()).hexdigest()==meta['sha256']
if dst.exists():assert hashlib.sha256(dst.read_bytes()).hexdigest()==meta['sha256']
else:dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
assert src.stat().st_nlink==dst.stat().st_nlink==1 and hashlib.sha256(dst.read_bytes()).hexdigest()==meta['sha256']
(out/'fixture-copy.json').write_text(json.dumps(dict(files=files,candidate=meta,linked=False),indent=2)+'\n',encoding='utf8')
print('Verified ordinary copies:',len(files),'and allowed train candidate')
