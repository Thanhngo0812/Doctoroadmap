from pathlib import Path
import hashlib,json,shutil
root=Path(r'C:/Users/ngoco/Desktop/Doctoroadmap');target=Path.cwd()
result=[]
for bundle in json.loads((target/'report/w06-fixtures-evidence-2026-10-20/bundles.json').read_text())['bundles']:
 manifest=root/bundle['manifest']; assert hashlib.sha256(manifest.read_bytes()).hexdigest()==bundle['manifest_sha256']
 source=root/bundle['snapshot']
 for item in json.loads(manifest.read_text())['files']:
  src=source/item['path']; dst=target/item['path']
  assert src.resolve().is_relative_to(source.resolve()) and dst.resolve().is_relative_to(target.resolve())
  assert not any(p.is_symlink() or p.is_junction() for p in [src,*src.parents] if p.is_relative_to(source))
  assert hashlib.sha256(src.read_bytes()).hexdigest()==item['sha256']
  if dst.exists(): assert hashlib.sha256(dst.read_bytes()).hexdigest()==item['sha256'],str(dst)
  else: dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
  assert hashlib.sha256(dst.read_bytes()).hexdigest()==item['sha256']
  result.append(dict(path=item['path'],source_sha256=item['sha256'],destination_sha256=item['sha256']))
(target/'report/w12-react-evidence/fixture-copy.json').write_text(json.dumps(dict(files=result,linked=False),indent=2)+'\n')
print('verified ordinary copies',len(result))

meta=json.loads((target/'report/w15-evidence/candidate.json').read_text())
src=root/meta['candidate'];dst=target/meta['staged_copy']
assert src.resolve().is_relative_to((root/'document-data/train').resolve())
assert hashlib.sha256(src.read_bytes()).hexdigest()==meta['sha256'] and src.stat().st_nlink==1 and not src.is_symlink()
if dst.exists(): assert hashlib.sha256(dst.read_bytes()).hexdigest()==meta['sha256']
else: dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
assert dst.stat().st_nlink==1 and hashlib.sha256(dst.read_bytes()).hexdigest()==meta['sha256']
(target/'report/w12-react-evidence/candidate-copy.json').write_text(json.dumps(dict(source=meta['candidate'],destination=meta['staged_copy'],source_sha256=meta['sha256'],destination_sha256=hashlib.sha256(dst.read_bytes()).hexdigest(),linked=False),indent=2)+'\n')
print('Verified train candidate copy')
