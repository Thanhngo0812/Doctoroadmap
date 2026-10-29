import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

name=sys.argv[1]
assert name in {'r11-react-01','r11-build-01'}
command=['npm.cmd','--prefix','src/web/frontend']+(['test','--','--pool=threads','--maxWorkers=1'] if name=='r11-react-01' else ['run','build'])
root=Path.cwd()
out=root/'report/w17-r11-evidence/runs'
out.mkdir(parents=True,exist_ok=True)
head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
source={str(p.relative_to(root)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest()
    for p in (root/'src/web/frontend').rglob('*') if p.is_file() and not {'node_modules','dist'}&set(p.parts)
    and p.suffix in {'.tsx','.ts','.json','.css','.html'}}
start=time.time()
with (out/(name+'.log')).open('w',encoding='utf-8') as log:
    result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
data=dict(command=command,cwd=str(root),head=head,native_exit=result.returncode,seconds=time.time()-start,source_sha256=source)
(out/(name+'-exit.json')).write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in data.items() if k!='source_sha256'}))
raise SystemExit(result.returncode)
