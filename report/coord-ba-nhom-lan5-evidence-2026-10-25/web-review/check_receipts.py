"""Selected, read-only W09 receipt checks. No application import or external service."""
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

OUT = Path(__file__).resolve().parent
WORK = OUT.parent / 'w09-assistant'
OLD = WORK / 'report/w09-evidence'
UI = WORK / 'report/w09-session-ui-2026-10-25'
PIN = 'da4d6399965f5a67accaacc6ea34af8ce56f0dd5'
FUNCTIONAL = '56acc16914eb2a20f1cb60eafa139cd04d74a4bc'
BROWSER = 'c048b724a78513375600507acf6aa7b6d8a1e06f'


def j(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def git(*args):
    return subprocess.check_output(['git', *args], cwd=WORK)


def cases(path):
    rows = list(ET.parse(path).getroot().iter('testcase'))
    failed = [r.get('name') for r in rows if r.find('failure') is not None]
    errors = [r.get('name') for r in rows if r.find('error') is not None]
    skipped = [r for r in rows if r.find('skipped') is not None]
    xfailed = [r for r in skipped if r.find('skipped').get('type') == 'pytest.xfail']
    return {'tests': len(rows), 'passed': len(rows) - len(failed) - len(errors) - len(skipped),
        'failures': len(failed), 'errors': len(errors), 'skipped': len(skipped)-len(xfailed),
        'xfailed': len(xfailed), 'failedNames': failed}


result = {'head': git('rev-parse', 'HEAD').decode().strip(), 'errors': [], 'limits':
    'Selected source/receipt verification only; app gates not rerun. Original full Python gate is functional-source evidence, not a new UI gate.'}
errors = result['errors']
assert result['head'] == PIN
result['productChangesAfterBrowser'] = git('diff', '--name-only', BROWSER, PIN, '--', 'src', 'scripts', 'tests').decode().splitlines()
result['backendChangesAfterFullGate'] = git('diff', '--name-only', FUNCTIONAL, PIN, '--', 'src/web/backend', 'src/doc2roadmap').decode().splitlines()
if result['productChangesAfterBrowser'] or result['backendChangesAfterFullGate']:
    errors.append('Source changed after the stated browser or backend gate')

checked = []
for manifest in [j(OLD/'browser-final-manifest.json')['files'], j(UI/'evidence-sha256.json')]:
    for r in manifest:
        rel = r['path'].replace('\\', '/')
        assert rel.startswith(('report/w09-evidence/', 'report/w09-session-ui-2026-10-25/'))
        raw = (WORK / rel).read_bytes()
        if sha(raw) != r['sha256'] or len(raw) != r['bytes']:
            errors.append({'receiptHashMismatch': rel})
        checked.append(rel)
result['receiptHashesChecked'] = len(checked)

source = []
for r in j(UI/'source-manifest.json')['files']:
    raw, rel = (WORK/r['path']).read_bytes(), r['path']
    blob, ui_blob = git('show', f'{BROWSER}:{rel}'), git('show', f'acba665:{rel}')
    ok = (sha(raw) == r['localSha256'] and sha(blob) == r['gitSha256']
        and sha(raw.replace(b'\r\n', b'\n')) == r['localLfNormalizedSha256']
        and (blob == ui_blob) == r['sameAsUiTestCommit'] and blob == git('show', f'{PIN}:{rel}'))
    source.append({'path': rel, 'passed': ok})
    if not ok:
        errors.append({'uiSourceMismatch': rel})
old_manifest = {r['path']: r for r in j(OLD/'source-manifest-final.json')['files']}
backend_paths = git('diff', '--name-only', '46d829a', PIN, '--', 'src/web/backend').decode().splitlines()
for rel in backend_paths:
    if rel.endswith('.md'):
        continue
    raw, blob = (WORK/rel).read_bytes(), git('show', f'{FUNCTIONAL}:{rel}')
    ok = sha(raw) == old_manifest[rel]['sha256'] and raw.replace(b'\r\n', b'\n') == blob.replace(b'\r\n', b'\n')
    source.append({'path': rel, 'passed': ok})
    if not ok:
        errors.append({'backendSourceMismatch': rel})
result['sourceChecks'] = source

selected = [
    (OLD,'gate-final4'), (OLD,'react-final5'), (OLD,'library-green2'),
    (OLD,'lecture-config-red'), (OLD,'config-green2'), (OLD,'library-red'),
    (OLD,'history-race-red'), (OLD,'history-race-green'), (OLD,'preview-race-red'), (OLD,'preview-race-green'),
    (OLD,'tool-state-red2'), (OLD,'regression-green2'),
    (UI,'red'), (UI,'green3'), (UI,'metadata-red'), (UI,'metadata-green'), (UI,'react'),
]
result['junit'] = {}
for directory, name in selected:
    result['junit'][str((directory/name).relative_to(WORK))] = cases(directory/f'{name}.xml')
for prefix in ['red','green3','metadata-red','metadata-green','react','build-final','browser-final4']:
    actual = int((UI/f'{prefix}.exit').read_text().strip())
    if actual != j(UI/'verification.json')['nativeExits'][prefix]:
        errors.append({'nativeMismatch': prefix})
result['nativeUiExitsMatch'] = True
result['mutations'] = []
for row in j(OLD/'mutations2/results.json'):
    proof = cases(OLD/'mutations2'/f"{row['name']}.xml")
    good = row['nativeExitCode'] == 1 and row['errors'] == proof['errors'] == 0 and set(proof['failedNames']) == set(row['failedAssertions']) and proof['failures'] > 0
    exact_source = sha((WORK/row['path']).read_bytes()) == row['sourceSha256']
    result['mutations'].append({'name': row['name'], 'receiptValid': good, 'sameCurrentSourceBytes': exact_source, 'failures': proof['failures']})
    if not good:
        errors.append({'mutantMismatch': row['name']})

audit = j(OLD/'browser-session-ui-final4/audit.json')
wire = []
for row in audit['http']:
    if row.get('capture') != 'tee of actual fetch response':
        continue
    frames = []
    for raw in re.split(r'\r?\n\r?\n', row['body']):
        lines = raw.splitlines()
        kind = next((line[6:].strip() for line in lines if line.startswith('event:')), None)
        data = '\n'.join(line[5:].lstrip() for line in lines if line.startswith('data:'))
        if kind and data:
            frames.append((kind, json.loads(data)))
    private = re.search(r'"validation"|"args"|"public_id"|"tool_calls"|res\.cloudinary\.com', row['body'])
    terminals = [data.get('answer') for kind,data in frames if kind in {'final','failure'} and data.get('answer')]
    good = not private and len(terminals) == 1 and terminals[0]['contract_version'] == 'answer-3'
    wire.append({'stage': row['stage'], 'passed': good, 'events': [k for k,_ in frames]})
    if not good:
        errors.append({'wireMismatch': row['stage']})
result['wireChecks'] = wire
result['browserCounts'] = {'configurations':len(audit['configurations']), 'screens':len(audit['screens']),
    'accessibility':len(audit['accessibility']), 'http':len(audit['http']), 'pageErrors':audit['pageErrors']}
result['ok'] = not errors
(OUT/'receipt-check.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'ok':result['ok'], 'errors':errors, 'receiptHashesChecked':len(checked),
    'sourceFiles':len(source), 'mutants':len(result['mutations']), 'changedMutantSources':[r['name'] for r in result['mutations'] if not r['sameCurrentSourceBytes']],
    'wireTraces':len(wire), 'browserCounts':result['browserCounts']}, ensure_ascii=False, indent=2))
