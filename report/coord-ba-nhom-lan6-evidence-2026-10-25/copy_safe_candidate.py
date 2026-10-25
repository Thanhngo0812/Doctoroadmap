import hashlib,json,shutil
from pathlib import Path
ROOT=Path('C:/Users/ngoco/Desktop/Doctoroadmap')
WT=ROOT/'tmp/coord-r6-web-core-20261025'
worker=ROOT/'tmp/w15-real-build'
record=json.loads((worker/'report/w15-evidence/candidate.json').read_text(encoding='utf-8'))
relative=record['staged_copy']
assert relative=='tmp/w15-candidate/input.pdf'
source,target=worker/relative,WT/relative
for part in [source,*source.parents]:
    assert not part.is_symlink() and not part.is_junction()
assert source.stat().st_nlink==1 and hashlib.sha256(source.read_bytes()).hexdigest()==record['sha256']
assert not target.exists()
target.parent.mkdir(parents=True,exist_ok=True)
shutil.copyfile(source,target)
assert target.stat().st_nlink==1 and hashlib.sha256(target.read_bytes()).hexdigest()==record['sha256']
proof={'path':relative,'sha256':record['sha256'],'bytes':target.stat().st_size,'ordinary_copy':True,'links_used':False}
(Path(__file__).parent/'safe-candidate-copy.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(proof))
