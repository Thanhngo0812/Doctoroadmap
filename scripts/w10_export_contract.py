"""Export the API contract without starting services or constructing provider clients."""
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(root / 'src/web/backend'), str(root / 'src')]
from wayfinder.api.app import create_app
from wayfinder.composition import WebServices
from wayfinder.settings import WebSettings

app = create_app(WebSettings(_env_file=None, frontend_dist='C:/missing-wayfinder-dist'), WebServices(health_check=lambda: 'ok'))
(root / 'src/web/openapi.json').write_text(json.dumps(app.openapi(), ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print('Exported W10 API contract without external calls.')
