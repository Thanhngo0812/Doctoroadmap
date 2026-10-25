import json,sys
from pathlib import Path
from decimal import Decimal
from hashlib import sha256
ROOT=Path('C:/Users/ngoco/Desktop/Doctoroadmap');WT=ROOT/'tmp/w15-real-build';OUT=ROOT/'tmp/coord-r6-tools-20261025'
sys.path[:0]=[str(WT/'src'),str(WT/'src/web/backend')]
from dotenv import dotenv_values
from sqlalchemy import create_engine,text
from sqlalchemy.engine import make_url
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore
from doc2roadmap.application.phase_b.retrieval import load_learning_graph
load=lambda p:json.loads(p.read_text(encoding='utf-8'))
record=load(WT/'report/w15-evidence/r5-20261025/doc-6-first-independent.json');rd=WT/record['plan']['run_dir'];plan=load(rd/'plan.json');approval=load(rd/'owner-approval.json');receipt=record['web_receipt']
assert plan['database']=='wayfinder_w15_722e9386b724' and plan['approved'] is False
assert sha256((rd/'source.pdf').read_bytes()).hexdigest()==plan['file_sha256'] and (rd/'source.pdf').stat().st_nlink==1
assert approval['approved'] is True and approval['file_sha256']==plan['file_sha256']
assert receipt['status']=='succeeded' and receipt['model_calls']==receipt['spent_usd']==receipt['input_tokens']==receipt['output_tokens']==0
assert all(receipt['step_details'][k]['reused'] for k in ['graph'])
assert receipt['step_details']['concepts']['label_roles']['reused'] is True
assert receipt['step_details']['concepts']['a3']['a3_reused'] is True and receipt['step_details']['concepts']['a3']['a3_prime_reused'] is True
url=make_url(dotenv_values(ROOT/'src/web/.env')['WAYFINDER_TEST_DATABASE_URL']);assert url.host in ['127.0.0.1','localhost']
engine=create_engine(url.set(database=plan['database']))
try:
 with engine.connect() as c:
  c.execute(text('SET TRANSACTION READ ONLY'))
  builds=[dict(x) for x in c.execute(text('SELECT id,status,doc_id,pipeline_version,claim_count,spent_usd FROM build')).mappings()]
  courses=[dict(x) for x in c.execute(text('SELECT id,status,published_graph_version FROM course')).mappings()]
  attempts=c.scalar(text('SELECT count(*) FROM build_attempt'))
  grant=c.execute(text("SELECT value FROM phase_b_record WHERE kind='w15_build_approval' AND record_id=:ref"),{'ref':approval['reference']}).scalar_one()
  ledger=[dict(x) for x in c.execute(text('SELECT purpose,cost_usd,input_tokens,output_tokens,extra FROM usage_ledger')).mappings()]
 assert len(builds)==len(courses)==attempts==1 and builds[0]['claim_count']==1
 assert builds[0]['status']=='succeeded' and courses[0]['status']=='ready' and courses[0]['published_graph_version']==8
 assert Decimal(str(builds[0]['spent_usd']))==0 and grant['state']=='finished'
 assert sum((x['cost_usd'] for x in ledger),Decimal(0))==Decimal('0.120403')
 assert all(x['cost_usd']==x['input_tokens']==x['output_tokens']==0 for x in ledger if x['extra'].get('counted_in')=='build')
finally:engine.dispose()
g=load_learning_graph(JsonArtifactStore(rd/'artifacts'),receipt['doc_id'],8);assert len(g.modules)==2 and len(g.learnable_nodes)==15
roundDir=WT/'report/w15-evidence/r5-20261025';accounting=[]
for label in ['doc-6-first','candidate-first','diagnostic','controlled','probe100','mixed100']:
 p=load(roundDir/label/'plan.json');local=WT/p['run_dir'];events=[]
 for audit in sorted({*local.glob('requests-*.jsonl'), *local.glob('budget-requests.jsonl')}):
  events.extend(json.loads(line) for line in audit.read_text(encoding='utf-8').splitlines())
 known=sum((Decimal(e['actual_usd']) for e in events if e['actual_usd'] is not None),Decimal(0));unknown=sum((Decimal(e['reserved_usd']) for e in events if e['actual_usd'] is None),Decimal(0))
 accounting.append(dict(label=label,calls=len(events),known=str(known),unknown=str(unknown)))
print(json.dumps({'accounting_debug':accounting}),flush=True)
assert sum(Decimal(x['known']) for x in accounting)==Decimal('1.28947575')
assert sum(Decimal(x['unknown']) for x in accounting)==Decimal('0.4139008')
result=dict(doc6_web_cache_only=dict(status='succeeded',model_calls=0,usd=0,modules=2,concepts=15,graph_version=8,independent_sql=True,sql_builds=len(builds),claims=1,attempts=1,grant_state=grant['state'],ledger_including_bootstrap='0.120403',bootstrap_known_demo_usd='0.1204034',bootstrap_quality_gate_passed=False,bootstrap_fallback='document_order'),r5_accounting=accounting,provider_calls_this_audit=0,sql_read_only=True)
(OUT/'doc6-independent.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
