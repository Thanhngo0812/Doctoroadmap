import json, subprocess, sys, time
from pathlib import Path
root=Path(__file__).resolve().parent
label=sys.argv[1]
args=sys.argv[2:]
start=time.monotonic()
result=subprocess.run([sys.executable,'scripts/w05_run_tests.py',*args],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(root/'runs'/f'{label}.log').write_bytes(result.stdout)
meta={'command':[sys.executable,'scripts/w05_run_tests.py',*args],'cwd':str(root),'native_exit':result.returncode,'seconds':round(time.monotonic()-start,3)}
(root/'runs'/f'{label}.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(meta,ensure_ascii=False))
print(result.stdout.decode('utf8',errors='replace')[-4000:])
sys.exit(result.returncode)
