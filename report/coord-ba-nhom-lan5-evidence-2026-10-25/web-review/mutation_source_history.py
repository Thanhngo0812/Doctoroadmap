import hashlib
import json
import subprocess
from pathlib import Path

OUT = Path(__file__).resolve().parent
WORK = OUT.parent / 'w09-assistant'
def git(*args):
    return subprocess.check_output(['git', *args], cwd=WORK)
rows = json.loads((WORK/'report/w09-evidence/mutations2/results.json').read_text(encoding='utf-8-sig'))
commits = git('rev-list', '46d829a..da4d639').decode().splitlines()
checked = {}
for rel in {r['path'] for r in rows}:
    by_sha = {}
    for commit in commits:
        run = subprocess.run(['git', 'show', f'{commit}:{rel}'], cwd=WORK, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        if run.returncode:
            continue
        raw = run.stdout
        for form, variant in [('Git LF', raw), ('checkout CRLF', raw.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n'))]:
            by_sha.setdefault(hashlib.sha256(variant).hexdigest(), {'commit':commit, 'form':form})
    checked[rel] = by_sha
result = [{'name':r['name'], 'path':r['path'], 'sourceSha256':r['sourceSha256'],
    'historicalSource':checked[r['path']].get(r['sourceSha256'])} for r in rows]
(OUT/'mutation-source-history.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
