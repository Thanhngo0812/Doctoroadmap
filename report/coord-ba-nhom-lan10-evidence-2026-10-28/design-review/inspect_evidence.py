import hashlib
import json
import pathlib
import struct
import subprocess
from collections import Counter
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = pathlib.Path(__file__).resolve().parent
PIN = '24538ae0a658c6e7a7439a8cf3418373e53a7aa4'
MAIN = '776f1f00b13726fcdc95f12bfd18a2b937bbd153'

def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])

rows = []
originals = {
    'w08/react-w08-self-check-folded-1280-dark-reduced.png': 'report/w08-evidence/browser-required3-20261024/ready-1280-dark-reduced.png',
    'w08/react-w08-self-check-open-1280-dark-reduced.png': 'report/w08-evidence/browser-required3-20261024/self-check-open-1280-dark-reduced.png',
    'w10/react-w10-library-here-390-light.png': 'report/w10-r7-evidence/browser-r7-main/library-here-390-light.png',
}
for p in sorted((ROOT / 'tmp/w23-paired-web-evidence/report/w23-evidence').rglob('*.png')):
    rel = p.relative_to(ROOT / 'tmp/w23-paired-web-evidence').as_posix()
    data = p.read_bytes()
    row = dict(path=rel, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), dimensions=struct.unpack('>II', data[16:24]),
               equals_pinned_blob=data == git('show', PIN + ':' + rel), equals_root_copy=data == (ROOT / rel).read_bytes())
    name = p.relative_to(ROOT / 'tmp/w23-paired-web-evidence/report/w23-evidence').as_posix()
    if name in originals:
        original = ROOT / originals[name]
        row.update(original=originals[name], original_sha256=hashlib.sha256(original.read_bytes()).hexdigest(), equals_original=data == original.read_bytes())
    rows.append(row)
source_rows = []
for rel in ['design/preview/w08_lecture_screens.html', 'design/preview/w10_quiz_screens.html', 'design/tokens/tokens.css', 'scripts/capture_w23_slice1.cjs', 'report/w23-doi-chieu-web-thuc-te-2026-10-27.md']:
    data = git('show', PIN + ':' + rel)
    raw = (ROOT/'tmp/w23-paired-web-evidence'/rel).read_bytes()
    source_rows.append(dict(path=rel, git_blob_sha256=hashlib.sha256(data).hexdigest(), worker_raw_sha256=hashlib.sha256(raw).hexdigest(), git_blob=git('rev-parse', PIN + ':' + rel).decode().strip(), equals_worker_bytes=data == raw, equals_worker_after_crlf_normalization=data == raw.replace(b'\r\n', b'\n')))
diffs = []
for before, after, paths in [
    ('1fc0f553bec808241388b722fa2c10a1c6ead33d', 'aaf68eb6795c929169e5212a05093d8d817c76e3', ['src/web/frontend','scripts/w10_web_check.cjs','scripts/w10_web_runtime.py']),
    ('b4136987668c3fb822ea374f399b947064ce7f18', MAIN, ['src/web/frontend/src/Learning.tsx', 'src/web/frontend/src/LectureMarkdown.tsx', 'src/web/frontend/src/learning.css', 'src/web/frontend/src/styles.css', 'src/web/frontend/src/tokens.css']),
]:
    diff = git('diff', before, after, '--', *paths)
    output = OUT / ('reuse-' + before[:8] + '.diff')
    output.write_bytes(diff)
    diffs.append(dict(before=before, after=after, paths=paths, diff_bytes=len(diff), saved=output.name))
origins = []
for folder, names in [
    ('report/w08-evidence/browser-required3-20261024', ['ready-1280-dark-reduced.png', 'self-check-open-1280-dark-reduced.png']),
    ('report/w10-r7-evidence/browser-r7-main', ['library-here-390-light.png']),
]:
    runtime = json.loads((ROOT/folder/'runtime.json').read_text(encoding='utf-8'))
    audit = json.loads((ROOT/folder/'audit.json').read_text(encoding='utf-8'))
    origins.append(dict(folder=folder, sourceCommit=runtime['sourceCommit'], base=runtime['base'], dirtySourcePaths=runtime['dirtySourcePaths'],
                        externalCostUsd=runtime['externalCostUsd'], screens=[x for x in audit['screens'] if x['file'] in names],
                        providers=runtime.get('providers',runtime.get('mailer')), browserVersion=audit.get('browserVersion')))
im = Image.open(ROOT/'report/w23-evidence/w08/html-w08-self-check-folded-1280-dark-reduced.png').convert('RGB')
pixels = Counter(im.get_flattened_data())
pixel_receipt = dict(path='report/w23-evidence/w08/html-w08-self-check-folded-1280-dark-reduced.png',
                     background_rgb=[22,27,34],background_pixel_count=pixels[(22,27,34)],primary_rgb=[41,169,255],primary_pixel_count=pixels[(41,169,255)],
                     dominant_colors=pixels.most_common(8),note='Source colors independently observed in the submitted PNG; no image modification')
result = dict(main_pin=MAIN, design_pin=PIN, images=rows, sources=source_rows, reuse=diffs, historical_origins=origins, submitted_pixel_receipt=pixel_receipt,
              visual_inspection=dict(all_six_submitted_pngs_viewed=True, all_three_reviewer_offline_pngs_viewed=True,
                  w08='HTML summary contains cardiology question/triangle/bulb. React full pages contain algebra question outside details, Xem đáp án summary with no triangle; open adds Bằng 1. Open original also has prerequisite panel open, unlike folded original.',
                  w10='HTML three wrapping catalog tabs/two cardiology cards with view+download actions. React two module tabs/two algebra rows plus module controls, no third tab. Both here groups contain button and assistant origins.',
                  authenticity='Three React images exactly reuse full original runtime files; no recropping. Original harness captures live authenticated pages, while later cloned DOM/style embedding is only for distinct taste inspection snapshots.'))
(OUT / 'evidence-inspection.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
print(json.dumps(result, indent=2, ensure_ascii=False))
