import hashlib
import io
import json
import re
import subprocess
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
PIN = '60412c87df1b684c97e6148d1f88f578d5202322'
PREV = '24538ae0a658c6e7a7439a8cf3418373e53a7aa4'
MAIN = '26d43b83ba0d3f265f28ea7d3220f924ba96a97d'

def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], stderr=subprocess.PIPE)

def blob(commit, p):
    return git('show', f'{commit}:{p}')

def sha(data):
    return hashlib.sha256(data).hexdigest()

def save(rel, data):
    dest = OUT / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)

paths = git('ls-tree', '-r', '--name-only', PIN, 'report/w23-evidence').decode().splitlines()
extras = [
    'report/w23-lat1-sua-bang-chung-2026-10-28.md',
    'report/w23-doi-chieu-web-thuc-te-2026-10-27.md',
    'scripts/capture_w23_slice1.cjs',
    'scripts/capture_w23_slice1_fixed.cjs',
    'design/preview/w08_lecture_screens.html',
    'design/preview/w10_quiz_screens.html',
    'design/tokens/tokens.css',
]
for p in paths + extras:
    save('submitted/' + p, blob(PIN, p))
for p in extras:
    if p.startswith(('scripts/', 'design/')):
        # Ordinary CRLF files reproduce the declared raw input without touching a worker.
        data = blob(PIN, p)
        if p.startswith('design/'):
            data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
        save(p, data)

receipt = json.loads(blob(PIN, 'report/w23-evidence/w23-slice1-receipts.json'))
results = {'pins': {'design': PIN, 'previous': PREV, 'main': MAIN}, 'images': [], 'sources': [], 'historical': [], 'checks': []}
for p in paths:
    if not p.endswith('.png'):
        continue
    data = blob(PIN, p)
    im = Image.open(io.BytesIO(data))
    try:
        old = blob(PREV, p)
    except subprocess.CalledProcessError:
        old = None
    results['images'].append({'path': p, 'sha256': sha(data), 'bytes': len(data), 'dimensions': list(im.size), 'identicalToPrevious': old == data if old else None})

for name, row in receipt['sources'].items():
    data = blob(PIN, row['path'])
    raw = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    results['sources'].append({'key': name, 'path': row['path'], 'gitLfSha256': sha(data), 'crlfSha256': sha(raw), 'matchesDeclaredLf': sha(data) == row['gitBlobSha256'], 'matchesDeclaredRawCrlf': sha(raw) == row['rawSha256']})

hist = [
    ('b4136987668c3fb822ea374f399b947064ce7f18', 'report/w08-evidence/browser-required3-20261024/ready-1280-dark-reduced.png', 'report/w23-evidence/w08/react-w08-self-check-folded-1280-dark-reduced.png', 'report/w23-evidence/w08/react-w08-self-check-folded-crop.png', (446, 1064, 680, 164)),
    ('b4136987668c3fb822ea374f399b947064ce7f18', 'report/w08-evidence/browser-required3-20261024/self-check-open-1280-dark-reduced.png', 'report/w23-evidence/w08/react-w08-self-check-open-1280-dark-reduced.png', 'report/w23-evidence/w08/react-w08-self-check-open-crop.png', (446, 1214, 680, 206)),
    ('1fc0f553bec808241388b722fa2c10a1c6ead33d', 'report/w10-r7-evidence/browser-r7-main/library-here-390-light.png', 'report/w23-evidence/w10/react-w10-library-here-390-light.png', 'report/w23-evidence/w10/react-w10-library-here-crop.png', (12, 72, 366, 478)),
]
for commit, orig, full, crop, rect in hist:
    # The historical capture commit describes source; the artifact was committed later.
    original = blob(MAIN, orig)
    source = Image.open(io.BytesIO(original)).convert('RGBA')
    cropped = Image.open(io.BytesIO(blob(PIN, crop))).convert('RGBA')
    x, y, w, h = rect
    expected = source.crop((x, y, x+w, y+h))
    diff = ImageChops.difference(expected, cropped)
    equal = expected.tobytes() == cropped.tobytes()
    root_orig = ROOT / orig
    results['historical'].append({'captureSourceCommit': commit, 'artifactGitCommitRead': MAIN, 'original': orig, 'originalSha256': sha(original), 'submittedFullIdentical': original == blob(PIN, full), 'rootHistoricalBytesMatch': root_orig.is_file() and sha(root_orig.read_bytes()) == sha(original), 'crop': crop, 'cropRect': rect, 'cropExactPixels': equal, 'differentBounds': diff.getbbox()})
    assert equal, f'crop pixels differ: {crop}'

def image_refs(value, location='$'):
    if isinstance(value, dict):
        if isinstance(value.get('path'), str) and value['path'].endswith('.png'):
            p = value['path']
            data = blob(PIN, p)
            im = Image.open(io.BytesIO(data))
            results['checks'].append({'assertion': 'submitted image receipt matches pinned bytes and PNG dimensions', 'location': location, 'path': p, 'shaMatches': value.get('sha256') == sha(data), 'bytesMatch': value.get('bytes') == len(data), 'dimensionsInReceipt': value.get('dimensions'), 'actualDimensions': list(im.size), 'dimensionsMatch': value.get('dimensions') == list(im.size) if 'dimensions' in value else None})
        for key, val in value.items():
            image_refs(val, f'{location}.{key}')
    elif isinstance(value, list):
        for i, val in enumerate(value):
            image_refs(val, f'{location}[{i}]')
image_refs(receipt)

reuse_specs = [
    ('w10-accepted-reuse', '1fc0f553bec808241388b722fa2c10a1c6ead33d', 'aaf68eb6795c929169e5212a05093d8d817c76e3', ['src/web/frontend', 'scripts/capture_w10_browser.cjs']),
    ('w10-to-main', 'aaf68eb6795c929169e5212a05093d8d817c76e3', MAIN, ['src/web/frontend/src/ContentLibrary.tsx', 'src/web/frontend/src/content-library.css']),
    ('w08-to-main', 'b4136987668c3fb822ea374f399b947064ce7f18', MAIN, ['src/web/frontend/src/Learning.tsx', 'src/web/frontend/src/learning.css', 'src/web/frontend/src/LectureMarkdown.tsx']),
]
results['reuseDiffs'] = []
for name, old, new, files in reuse_specs:
    data = git('diff', old, new, '--', *files)
    save(name + '.diff', data)
    results['reuseDiffs'].append({'name': name, 'old': old, 'new': new, 'paths': files, 'bytes': len(data)})

for p in ['src/web/frontend/src/ContentLibrary.tsx','src/web/frontend/src/Learning.tsx','src/web/frontend/src/learning.css','src/web/frontend/src/Sharing.tsx','doc/web-chuc-nang-spec.md']:
    save('main-source/' + p, blob(MAIN, p))

save('evidence-inspection.json', (json.dumps(results, ensure_ascii=False, indent=2) + '\n').encode())
print(json.dumps({'images': len(results['images']), 'exactCrops': len(results['historical']), 'sourceHashesMatch': all(r['matchesDeclaredLf'] and r['matchesDeclaredRawCrlf'] for r in results['sources']), 'receiptDimensionMismatches': [r for r in results['checks'] if r['dimensionsMatch'] is False], 'reuseDiffs': results['reuseDiffs']}, indent=2))
