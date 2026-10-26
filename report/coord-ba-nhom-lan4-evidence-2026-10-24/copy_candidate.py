import hashlib, json, shutil
from pathlib import Path

ROOT = Path('C:/Users/ngoco/Desktop/Doctoroadmap')
worker = ROOT / 'tmp/w15-real-build'
target = ROOT / 'tmp/coord-r4-acceptance-20261024'
record = json.loads((worker / 'report/w15-evidence/candidate.json').read_text(encoding='utf-8'))
relative = record['staged_copy']
assert relative == 'tmp/w15-candidate/input.pdf'
source, destination = worker / relative, target / relative
for parent in (source, *source.parents):
    if parent == ROOT.parent:
        break
    assert not parent.is_symlink() and not parent.is_junction(), str(parent)
assert source.stat().st_nlink == 1
assert hashlib.sha256(source.read_bytes()).hexdigest() == record['sha256']
assert not destination.exists()
destination.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile(source, destination)
assert destination.stat().st_nlink == 1 and not destination.is_symlink()
assert hashlib.sha256(destination.read_bytes()).hexdigest() == record['sha256']
proof = {'source': str(source), 'destination': str(destination), 'sha256': record['sha256'],
         'bytes': destination.stat().st_size, 'ordinary_copy': True, 'links_used': False}
(Path(__file__).parent / 'candidate-copy.json').write_text(json.dumps(proof, indent=2)+'\n', encoding='utf-8')
print(json.dumps(proof))
