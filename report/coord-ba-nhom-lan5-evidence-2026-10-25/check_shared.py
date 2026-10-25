import hashlib,json,subprocess
from pathlib import Path
ROOT=Path('C:/Users/ngoco/Desktop/Doctoroadmap')
HERE=Path(__file__).parent
protected=json.loads((HERE/'protected-shared-files.json').read_text())
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in protected.items())
print(json.dumps({'protected_files':len(protected),'unchanged':True,
    'main':subprocess.check_output(['git','rev-parse','main'],cwd=ROOT,text=True).strip()}))
