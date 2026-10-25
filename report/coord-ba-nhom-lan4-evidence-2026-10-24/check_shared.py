import hashlib,json,subprocess
from pathlib import Path
ROOT=Path('C:/Users/ngoco/Desktop/Doctoroadmap')
OUT=Path(__file__).with_name('protected-shared-files.json')
paths=['report/ket-qua-v3-05b-09b-11b-vertex-2026-09-28.md','scripts/thu-vertex/chi_thu_credit.py',
 'scripts/thu-vertex/goi_thu_vertex.py','scripts/thu-vertex/so_embedding.py',
 'task/sau-a10/19-dac-ta-bo-cau-hoi-thu.md','task/v3-lo-trinh-doc-duoc/19-goi-mo-hinh-qua-vertex.md']
current={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
if OUT.exists():assert json.loads(OUT.read_text())==current,'Preserve other-owner changes; inspect instead of restoring'
else:OUT.write_bytes((json.dumps(current,indent=2)+'\n').encode())
print(json.dumps({'protected_files':6,'unchanged':True,'main':subprocess.check_output(['git','rev-parse','main'],cwd=ROOT,text=True).strip()}))
