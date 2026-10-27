from pathlib import Path
import hashlib
import json
import re
import subprocess
from PIL import Image

ROOT = Path('C:/Users/ngoco/Desktop/Doctoroadmap')
BASE = Path(__file__).parent
WORKER = ROOT / 'tmp/w24-figma-evidence'
PIN = 'bda1366b8d033ce0dcf4660651959293c178f7c8'
REPORT = 'report/w24-w10-w23-phoihop-2026-10-25.md'
text = subprocess.check_output(['git', 'show', f'{PIN}:{REPORT}'], cwd=ROOT).decode('utf-8')
rows = []
for relative in sorted(set(re.findall(r'report/[\w/.-]+\.(?:png|webm)', text))):
    root_raw = (ROOT / relative).read_bytes()
    worker_raw = (WORKER / relative).read_bytes()
    record = {'path': relative, 'bytes': len(root_raw), 'sha256': hashlib.sha256(root_raw).hexdigest(), 'worker_bytes_identical': root_raw == worker_raw}
    if relative.endswith('.png'):
        with Image.open(ROOT / relative) as image:
            record['image_size'] = list(image.size)
    rows.append(record)
anchors = []
for line in text.splitlines():
    if not line.startswith('| **W-'):
        continue
    html = re.search(r'design/preview/[\w_]+\.html', line)
    anchor = re.search(r'#([\w-]+)', line)
    if html and anchor:
        blob = subprocess.check_output(['git', 'show', f'{PIN}:{html[0]}'], cwd=ROOT).decode('utf-8')
        anchors.append({'html': html[0], 'anchor': anchor[1], 'exists': f'id="{anchor[1]}"' in blob})
origins = []
for relative in ['report/w08-evidence/browser-required3-20261024/runtime.json', 'report/w09-evidence/browser-required-final1/runtime.json', 'report/w10-r7-evidence/browser-r7-main/runtime.json']:
    runtime = json.loads((ROOT / relative).read_text(encoding='utf-8'))
    origins.append({'runtime': relative, 'sourceCommit': runtime['sourceCommit'], 'base': runtime['base'], 'externalCostUsd': runtime['externalCostUsd'], 'dirtySourcePaths': runtime['dirtySourcePaths']})
reuse = subprocess.check_output(['git', 'diff', '--name-only', '1fc0f553bec808241388b722fa2c10a1c6ead33d', 'aaf68eb6795c929169e5212a05093d8d817c76e3', '--', 'src/web/frontend', 'scripts/w10_web_check.cjs', 'scripts/w10_web_runtime.py'], cwd=ROOT, text=True)
proof = {'reviewed_commit': PIN, 'report_sha256': hashlib.sha256(text.encode()).hexdigest(), 'references': rows, 'anchors': anchors, 'runtime_origins': origins, 'w10_frontend_browser_harness_changed_paths_1fc_to_aaf': reuse.splitlines(), 'png_visually_inspected': 10, 'video_content_inspection': 'Nine metadata/frame samples retained by earlier interrupted reviewer; resume visually inspected eight nonblank samples, not every frame or interval.', 'w23_paired_capture_manifest_added_by_candidate': False}
(BASE / 'evidence-inspection.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
for n, line in enumerate(text.splitlines(), 1):
    if 35 <= n <= 80:
        print(f'{n}: {line}')
print(json.dumps({'references': len(rows), 'all_worker_identical': all(r['worker_bytes_identical'] for r in rows), 'all_anchors_exist': all(r['exists'] for r in anchors), 'origins': origins, 'w10_reuse_diff_empty': not reuse}, indent=2))
