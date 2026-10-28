import hashlib,json,shutil
from pathlib import Path
R=Path('C:/Users/ngoco/Desktop/Doctoroadmap');W=Path('C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-r11-final-20261028');T=Path('C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-r11-tools-20261028')
records={}
for bundle in json.loads((W/'report/w06-fixtures-evidence-2026-10-20/bundles.json').read_text())['bundles']:
 m=R/bundle['manifest'];assert hashlib.sha256(m.read_bytes()).hexdigest()==bundle['manifest_sha256'];S=R/bundle['snapshot']
 for f in json.loads(m.read_text())['files']:
  s=S/f['path'];d=W/f['path'];assert s.resolve().is_relative_to(S.resolve()) and d.resolve().is_relative_to(W.resolve())
  assert not any(p.is_symlink() or p.is_junction() for p in [s,*s.parents] if p.is_relative_to(R));assert s.stat().st_nlink==1
  assert hashlib.sha256(s.read_bytes()).hexdigest()==f['sha256']
  if not d.exists():d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(s,d)
  assert d.stat().st_nlink==1 and hashlib.sha256(d.read_bytes()).hexdigest()==f['sha256'];records[f['path']]=f['sha256']
(T/'fixture-copy.json').write_text(json.dumps(dict(verified_files=len(records),files=records,links_used=False,learner_stores_copied=False),indent=2))
meta=json.loads((R/'tmp/w15-real-build/report/w15-evidence/candidate.json').read_text());s=R/'tmp/w15-real-build'/meta['staged_copy'];d=W/meta['staged_copy'];assert s.stat().st_nlink==1 and hashlib.sha256(s.read_bytes()).hexdigest()==meta['sha256'];assert not d.exists();d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(s,d);assert d.stat().st_nlink==1 and hashlib.sha256(d.read_bytes()).hexdigest()==meta['sha256']
(T/'candidate-copy.json').write_text(json.dumps(dict(path=meta['staged_copy'],sha256=meta['sha256'],bytes=d.stat().st_size,links_used=False)))
print('Unique fixture files',len(records),'PDF bytes',d.stat().st_size)
