"""Keep raw browser videos locally with hashes; commit compact review receipts."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path('C:/Users/ngoco/Desktop/Doctoroadmap')
OUT=ROOT/'report/coord-ba-nhom-lan3-evidence-2026-10-23'
SCRATCH=Path(__file__).parent
prior=SCRATCH/'archive-manifest-before-video-tiers.json'
assert not prior.exists()
shutil.copyfile(OUT/'manifest.json',prior)
(OUT/'.gitignore').write_bytes(b'/browser/learner.webm\n/browser/owner.webm\n')
shutil.copyfile(Path(__file__),OUT/'finalize_archive.py')
def entry(p):return {'path':str(p.relative_to(OUT)).replace('\\','/'),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
files=[entry(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='manifest.json' and p.suffix!='.webm']
local=[entry(p) for p in sorted((OUT/'browser').glob('*.webm'))]
data={'files':files,'local_untracked_videos':local,'video_originals':'tmp/coord-r3-acceptance-20261023/report/w08-evidence/browser-coord-r3',
    'links_used':False,'new_provider_cost_usd':0,'note':'Raw videos are retained in both local locations, excluded from Git; no files deleted. All other evidence is committed.'}
(OUT/'manifest.json').write_bytes((json.dumps(data,indent=2)+'\n').encode())
print(json.dumps({'tracked_manifest_entries':len(files),'tracked_bytes':sum(f['bytes'] for f in files),'local_videos':len(local),'video_bytes':sum(f['bytes'] for f in local)}))
