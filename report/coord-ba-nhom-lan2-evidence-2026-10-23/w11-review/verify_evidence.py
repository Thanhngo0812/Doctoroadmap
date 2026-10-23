"""Read-only verification of the pinned W11 worker evidence."""
from pathlib import Path
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path('C:/Users/ngoco/Desktop/Doctoroadmap/tmp/w11-share-links')
OUT = Path(__file__).resolve().parent
EVIDENCE = ROOT / 'report/w11-evidence/auth-return-2026-10-23'


def xml_counts(path):
    tree = ET.parse(path)
    cases = list(tree.iter('testcase'))
    failures = list(tree.iter('failure'))
    errors = list(tree.iter('error'))
    skips = list(tree.iter('skipped'))
    return dict(tests=len(cases), passed=len(cases)-len(failures)-len(errors)-len(skips),
                failures=len(failures), errors=len(errors), skipped=len(skips))


results = dict(worker_commit='253874bbd83e4224477542928b4a3ef9344db93a',
               mode='read-only manifests, JUnit and saved browser audit; no test/browser/PG runtime here')
manifest_results = {}
for name, base in [('source-manifest.json', ROOT), ('latest-source-manifest.json', ROOT),
                   ('sha256-manifest.json', EVIDENCE)]:
    manifest = json.loads((EVIDENCE/name).read_text(encoding='utf-8-sig'))
    mismatches = []
    for row in manifest['files']:
        payload = (base/row['path']).read_bytes()
        if hashlib.sha256(payload).hexdigest() != row['sha256']:
            mismatches.append(row['path'])
    manifest_results[name] = dict(files=len(manifest['files']), mismatches=mismatches)
results['manifests'] = manifest_results
results['junit'] = {name: xml_counts(EVIDENCE/name) for name in (
    'auth-return-red.xml', 'auth-return-green.xml', 'final-python.xml', 'latest-python.xml',
    'final-react.xml', 'latest-react.xml', 'unsafe-next-final-mutation.xml')}
results['exits'] = {path.name: path.read_text(encoding='utf-8-sig').strip()
                    for path in EVIDENCE.glob('*-exit.txt')}
mutations = json.loads((EVIDENCE/'mutations/results.json').read_text(encoding='utf-8-sig'))
results['mutations'] = []
for mutation in mutations:
    name = mutation['name']
    source = ROOT/'src/web/backend/wayfinder'/(
        'infrastructure/sharing_store.py' if name == 'atomic-join' else 'application/sharing.py')
    current_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    results['mutations'].append(dict(name=name, native_exit=mutation['native_exit_code'],
        counts=xml_counts(EVIDENCE/'mutations'/(name+'.xml')),
        restored=mutation['original_sha256']==mutation['restored_sha256']==current_hash))
unsafe = json.loads((EVIDENCE/'unsafe-next-final-mutation.json').read_text(encoding='utf-8-sig'))
results['unsafe_mutation_source_restored'] = (
    unsafe['beforeSha256'] == unsafe['restoredSha256'] == hashlib.sha256(
        (ROOT/'src/web/frontend/src/Auth.tsx').read_bytes()).hexdigest())
audit = json.loads((EVIDENCE/'browser-final/audit.json').read_text(encoding='utf-8-sig'))
results['browser'] = dict(screens=len(audit['screens']), axe=len(audit['accessibility']),
    http=len(audit['http']), auth_returns=audit['authReturns'],
    violations=sum(len(row['violations']) for row in audit['accessibility']),
    incomplete=sum(len(row['incomplete']) for row in audit['accessibility']),
    console_errors=len(audit['errors']), page_errors=len(audit['pageErrors']),
    failed_requests=len(audit['failedRequests']),
    axe_scope=[{key: row[key] for key in ['state', 'theme', 'width']} for row in audit['accessibility']])
results['browser_runtime'] = json.loads((EVIDENCE/'browser-final/runtime.json').read_text(encoding='utf-8-sig'))
results['delta_after_tested_source'] = subprocess.check_output([
    'git','diff','--name-only','33f9c25','253874bb','--','src','scripts','tests','design'], cwd=ROOT, text=True).splitlines()
results['delta_between_tested_sources'] = subprocess.check_output([
    'git','diff','--name-only','2c5166b','33f9c25','--','src','scripts','tests','design'], cwd=ROOT, text=True).splitlines()
results['ancestors'] = {sha: subprocess.run(['git','merge-base','--is-ancestor',sha,'253874bb'],
    cwd=ROOT,capture_output=True).returncode==0 for sha in ['865974a','1d193735','33f9c25']}
(OUT/'evidence-verification.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(results,ensure_ascii=False,indent=2))
