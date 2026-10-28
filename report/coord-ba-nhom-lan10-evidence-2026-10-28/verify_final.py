"""Validate scoped documentation/evidence; never read held-out or learner cache."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
from dotenv import dotenv_values
R=Path('C:/Users/ngoco/Desktop/Doctoroadmap'); T=Path(__file__).parent
O=R/'report/coord-ba-nhom-lan10-evidence-2026-10-28'
docs=json.loads((T/'docs-paths.json').read_text())
manifest=json.loads((O/'manifest.json').read_text(encoding='utf-8'))
for row in manifest['files']:
    b=(O/row['path']).read_bytes();assert len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'],row['path']
protected=json.loads((T/'protected.json').read_text())
for p,h in protected.items():assert hashlib.sha256((R/p).read_bytes()).hexdigest()==h,p
foreign=json.loads((T/'untracked-protected.json').read_text())
for p,h in foreign.items():assert hashlib.sha256((R/p).read_bytes()).hexdigest()==h,p
links=0
for rel in docs:
    text=(R/rel).read_text(encoding='utf-8');assert not re.search(r'MERGE_HASH|PY_PASS|REACT_PASS|FINAL_CANDIDATE|FINAL_MAIN|SKIP_DETAIL',text),rel
    clean=re.sub(r'```[\s\S]*?```','',text);clean=re.sub(r'`[^`]*`','',clean)
    for m in re.finditer(r'(?<!!)\[[^\]]*\]\(([^)]+)\)',clean):
        target=m.group(1).strip('<>').split('#')[0]
        if not target or re.match('^(https?:|mailto:)',target):continue
        assert (R/rel).parent.joinpath(target).resolve().exists(),(rel,target)
        links+=1
paths=[*docs,*['report/coord-ba-nhom-lan10-evidence-2026-10-28/'+r['path'] for r in manifest['files']],'report/coord-ba-nhom-lan10-evidence-2026-10-28/manifest.json']
assert len(paths)==len(set(paths))
values=dotenv_values(R/'src/web/.env')
secrets=[str(v).encode() for k,v in values.items() if v and re.search(r'PASSWORD|SECRET|TOKEN|API_KEY|GEMINI_KEY',k) and len(str(v))>=12]
for p in paths:
    assert p.startswith(('report/','task/web/','doc/')) and '.env' not in p
    b=(R/p).read_bytes();assert not any(s in b for s in secrets),'Configured secret value found'
assert subprocess.check_output(['git','branch','--show-current'],cwd=R,text=True).strip()=='main'
candidate=json.loads((T/'gate-summary.json').read_text())['candidate']
subprocess.run(['git','diff','--exit-code',candidate,'HEAD','--','src','scripts','tests','design','evaluation','.env.example'],cwd=R,check=True,stdout=subprocess.PIPE)
(T/'commit-paths.txt').write_bytes(('\n'.join(paths)+'\n').encode())
proof=dict(manifest_entries=len(manifest['files']),scoped_commit_paths=len(paths),local_document_links_verified=links,protected_tracked_files_unchanged=len(protected),protected_untracked_files_unchanged=len(foreign),no_configured_secret_values_found=True,committed_product_tree_matches_tested_candidate=True)
(T/'final-validation.json').write_bytes((json.dumps(proof,indent=2)+'\n').encode());print(json.dumps(proof))
if '--head' in sys.argv:
    for row in manifest['files']:
        b=subprocess.check_output(['git','show','HEAD:report/coord-ba-nhom-lan10-evidence-2026-10-28/'+row['path']],cwd=R)
        assert hashlib.sha256(b).hexdigest()==row['sha256'],row['path']
    for p in docs:
        actual=subprocess.check_output(['git','show','HEAD:'+p],cwd=R).decode().replace('\r\n','\n')
        assert actual==(R/p).read_text(encoding='utf-8').replace('\r\n','\n'),p
    print(json.dumps(dict(head_evidence_blobs_verified=True,head_docs_verified=True)))
