import hashlib,json,re,subprocess,sys
from pathlib import Path
from dotenv import dotenv_values
ROOT=Path('C:/Users/ngoco/Desktop/Doctoroadmap')
TOOLS=ROOT/'tmp/coord-r8-tools-20261026'
OUT=ROOT/'report/coord-ba-nhom-lan8-evidence-2026-10-26'
docs=json.loads((TOOLS/'docs-paths.json').read_text())
manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
for row in manifest['files']:
    b=(OUT/row['path']).read_bytes();assert len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'],row['path']
for p,sha in json.loads((TOOLS/'protected.json').read_text()).items():
    assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==sha,p
links=0
for rel in docs:
    text=(ROOT/rel).read_text(encoding='utf-8');assert not re.search(r'MERGE_HASH|PY_PASS',text),rel
    clean=re.sub(r'```[\s\S]*?```','',text)
    clean=re.sub(r'`[^`]*`','',clean)
    for m in re.finditer(r'(?<!!)\[[^\]]*\]\(([^)]+)\)',clean):
        target=m.group(1).strip('<>').split('#')[0]
        if not target or re.match('^(https?:|mailto:)',target):continue
        assert (ROOT/rel).parent.joinpath(target).resolve().exists(),(rel,target)
        links+=1
paths=[*docs,*['report/coord-ba-nhom-lan8-evidence-2026-10-26/'+r['path'] for r in manifest['files']],'report/coord-ba-nhom-lan8-evidence-2026-10-26/manifest.json']
assert len(paths)==len(set(paths))
values=dotenv_values(ROOT/'src/web/.env')
secrets=[str(v).encode() for k,v in values.items() if v and re.search(r'PASSWORD|SECRET|TOKEN|API_KEY|GEMINI_KEY',k) and len(str(v))>=12]
for p in paths:
    assert not p.startswith(('tmp/','artifacts/','document-data/')) and '.env' not in p
    b=(ROOT/p).read_bytes()
    assert not any(secret in b for secret in secrets),'configured secret value found in scoped files'
assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()=='main'
subprocess.run(['git','diff','--exit-code','ee5a75fe571d62803387429677c2b87201baf654','HEAD','--','src','scripts','tests','design'],cwd=ROOT,check=True,stdout=subprocess.PIPE)
(TOOLS/'commit-paths.txt').write_text('\n'.join(paths)+'\n',encoding='utf-8')
proof={'manifest_entries':len(manifest['files']),'scoped_commit_paths':len(paths),'local_document_links_verified':links,'protected_files_unchanged':True,'no_configured_secret_values_found':True,'committed_product_tree_matches_tested_candidate':True}
(TOOLS/'final-validation.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps(proof))

if '--head' in sys.argv:
    for row in manifest['files']:
        p='report/coord-ba-nhom-lan8-evidence-2026-10-26/'+row['path']
        b=subprocess.check_output(['git','show','HEAD:'+p],cwd=ROOT)
        assert hashlib.sha256(b).hexdigest()==row['sha256'],p
    for p in docs:
        expected=(ROOT/p).read_text(encoding='utf-8').replace('\r\n','\n')
        committed=subprocess.check_output(['git','show','HEAD:'+p],cwd=ROOT).decode('utf-8').replace('\r\n','\n')
        assert expected==committed,p
    print(json.dumps({'head_evidence_blobs_verified':True,'head_docs_verified':True}))
