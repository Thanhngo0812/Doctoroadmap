import hashlib,json,shutil
from pathlib import Path
ROOT=Path('C:/Users/ngoco/Desktop/Doctoroadmap')
OUT=Path(__file__).parent
source=ROOT/'tmp/coord-w08-focused-review-20261023/Learning.review-repro.test.tsx'
target=ROOT/'tmp/coord-r3-acceptance-20261023/src/web/frontend/src/Learning.review-repro.test.tsx'
assert not target.exists()
assert hashlib.sha256(source.read_bytes()).hexdigest()=='d5d4f470765b513bd60e643745aa7c1a4a400c64e87049ccf4e1aa231edf92cf'
shutil.copyfile(source,target)
data={'source':str(source),'executedTestPath':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
    'productCodeChanged':False,'originalControlsRetained':10,'newCases':7,'purpose':'Independent counterexamples after unchanged full gate; not a worker source edit'}
(OUT/'repro-input.json').write_bytes((json.dumps(data,indent=2)+'\n').encode())
print(json.dumps(data))
