import json
from pathlib import Path
import sys

root = Path.cwd()
sys.path[:0] = [str(root/'src'),str(root/'src/web/backend')]
from wayfinder.api.app import create_app
from wayfinder.composition import WebServices
from wayfinder.settings import WebSettings
path = root/'src/web/openapi.json'
old = json.loads(path.read_text(encoding='utf-8'))
new = create_app(WebSettings(_env_file=None,frontend_dist='C:/missing-wayfinder-dist'),WebServices(health_check=lambda:'ok')).openapi()
old_ops = {(p,m) for p,v in old['paths'].items() for m in v}
new_ops = {(p,m) for p,v in new['paths'].items() for m in v}
assert old_ops <= new_ops
path.write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print({'operations':len(new_ops),'added':sorted(new_ops-old_ops)})
