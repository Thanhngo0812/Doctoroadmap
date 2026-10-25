from pathlib import Path
from hashlib import sha256
from decimal import Decimal
from collections import Counter,defaultdict
from datetime import datetime
import json,os,sys,subprocess
from unittest.mock import patch
from contextlib import ExitStack
ROOT=Path(r'C:/Users/ngoco/Desktop/Doctoroadmap')
WT=ROOT/'tmp/w15-real-build'
OUT=ROOT/'tmp/coord-r6-core-review-20261025'
sys.path[:0]=[str(WT/'src'),str(WT/'src/web/backend')]
from dotenv import dotenv_values
from sqlalchemy import create_engine,text
from sqlalchemy.engine import URL,make_url
from PIL import Image
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore
from doc2roadmap.application.phase_b.retrieval import load_learning_graph,assert_retrieval_compatible
from doc2roadmap.domain.global_validation import strongly_connected_components

def load(p):return json.loads(p.read_text(encoding='utf-8'))
def dump(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2,default=str)+chr(10),encoding='utf-8')
def digest(p):return sha256(p.read_bytes()).hexdigest()
def local(p,base=WT):
 p=p.resolve()
 assert p.is_relative_to(base.resolve()),p
 cur=p
 while cur!=base.resolve():
  assert not cur.is_symlink(),cur
  if cur.exists():assert not (getattr(cur.lstat(),'st_file_attributes',0)&0x400),cur
  cur=cur.parent
 return p

ev=WT/'report/w15-evidence'
checks=[]
for round in ['r5-20261025','r6-20261025']:
 manifest=load(ev/round/'manifest.json');good=[]
 for e in manifest['files']:
  p=local(ev/e['path'])
  assert digest(p)==e['sha256'],str(p)
  if 'bytes' in e:assert p.stat().st_size==e['bytes'],str(p)
  good.append(e['path'])
 checks.append(dict(round=round,manifest_entries=len(good)))
 prov=load(ev/round/'provenance.json');rows=[]
 for e in prov['files']:
  p=local(WT/e['source']);assert digest(p)==e['source_sha256'],e['source']
  rows.append(e['source'])
 checks[-1]['source_provenance_entries']=len(rows)

r6=load(ev/'r6-20261025/final-audit.json');loc=r6['location'];rd=local(WT/loc['run_dir']);plan=load(rd/'plan.json');permission=load(rd/'owner-core-retry-approval.json');execution=load(rd/'execution.json')
assert digest(rd/'plan.json')==loc['plan_sha256']
assert digest(rd/'owner-core-retry-approval.json')==loc['approval_sha256']
assert plan['approved'] is False and permission['approved'] is True and permission['approved_by']=='project-owner'
assert permission['retry_unknown_within_cap'] is True
assert permission['embedding_billing_verified'] is False
assert permission['reference']==loc['reference']
for k in ['file_sha256','database','pipeline_version','embedding_price_profile']:assert permission[k]==plan[k],k
assert plan['pipeline_version'].split(':')[1]==loc['head']==plan['prepared_commit']
assert (rd/'source.pdf').stat().st_nlink==1 and digest(rd/'source.pdf')==plan['file_sha256']
receipt=execution['attempts'][0]['result'];budget=receipt['step_details']['operator_budget']
assert receipt['status']=='succeeded' and receipt['error'] is None
assert receipt['usage_complete'] is False
assert execution['mail_subjects']==['Bản dựng xong']
assert receipt['pipeline_version']==plan['pipeline_version']
assert receipt['doc_id']=='u-'+plan['file_sha256'][:20]
events=[]
for p in rd.glob('requests-*.jsonl'):events.extend(json.loads(l) for l in p.read_text(encoding='utf-8').splitlines())
traces=[json.loads(l) for l in (rd/'transport-trace.jsonl').read_text(encoding='utf-8').splitlines()]
known=sum((Decimal(e['actual_usd']) for e in events if e['actual_usd'] is not None),Decimal(0))
unknown=sum((Decimal(e['reserved_usd']) for e in events if e['actual_usd'] is None),Decimal(0))
assert str(known)==r6['new_known_demo_usd'] and unknown==Decimal(r6['new_unknown_upper_usd'])
assert len(events)==len(traces)==1637 and budget['held_usd']=='0'
for e in events:
 b=e['budget'];assert Decimal(b['known_usd'])+Decimal(b['unknown_upper_usd'])+Decimal(b['held_usd'])<=Decimal(b['limit_usd'])
assert known+unknown<=Decimal(budget['limit_usd'])==Decimal('2.25')
counts=Counter(r['operation'] for r in traces);statuses=Counter(str(r.get('http_status')) for r in traces)
assert counts=={'generateContent':715,'predict':922} and statuses=={'200':1635,'429':2}
errors=[r for r in traces if r.get('error_type')]
assert all(r['http_status']==429 and r['operation']=='generateContent' for r in errors) and len(errors)==2
assert len({r['request_sha256'] for r in errors})==1
assert any(r['request_sha256']==errors[0]['request_sha256'] and r['sequence']>max(e['sequence'] for e in errors) and r['http_status']==200 for r in traces)
peaks={}
for stage in sorted({r['stage'] for r in traces}):
 points=[]
 for r in traces:
  if r['stage']!=stage:continue
  start=datetime.fromisoformat(r['started_at']).timestamp();points.extend([(start,1),(start+r['wall_seconds'],-1)])
 active=peak=0
 for _,d in sorted(points):active+=d;peak=max(peak,active)
 peaks[stage]=peak
assert peaks==r6['stage_peaks']

values=dotenv_values(ROOT/'src/web/.env')
configured=os.environ.get('WAYFINDER_TEST_DATABASE_URL') or values.get('WAYFINDER_TEST_DATABASE_URL')
url=make_url(configured) if configured else URL.create('postgresql+psycopg',username='wayfinder',password=values['POSTGRES_TEST_PASSWORD'],host='127.0.0.1',port=5433,database='wayfinder_test')
assert url.host in ('127.0.0.1','localhost') and loc['database']=='wayfinder_w15_b5f1aa6534ce'
engine=create_engine(url.set(database=loc['database']))
try:
 with engine.connect() as c:
  c.execute(text('SET TRANSACTION READ ONLY'))
  approval=c.execute(text("SELECT value FROM phase_b_record WHERE kind='w15_build_approval' AND record_id=:ref"),{'ref':loc['reference']}).scalar_one()
  builds=[dict(r) for r in c.execute(text('SELECT id,status,doc_id,pipeline_version,spent_usd,model_calls,usage_complete,claim_count FROM build')).mappings()]
  courses=[dict(r) for r in c.execute(text('SELECT id,status,doc_id,published_graph_version FROM course')).mappings()]
  ledger=[dict(r) for r in c.execute(text('SELECT purpose,cost_usd,input_tokens,output_tokens,extra FROM usage_ledger ORDER BY id')).mappings()]
  attempt_count=c.execute(text('SELECT count(*) FROM build_attempt')).scalar_one()
 assert approval['state']=='finished' and approval['retry_unknown_within_cap'] is True and approval['budget']==budget
 assert approval['events']==events
 assert len(builds)==len(courses)==attempt_count==1 and builds[0]['claim_count']==1
 assert builds[0]['status']=='succeeded' and courses[0]['status']=='ready'
 assert sum((r['cost_usd'] for r in ledger),Decimal(0))==Decimal(str(receipt['spent_usd']))==Decimal('0.679336')
 assert all(r['cost_usd']==r['input_tokens']==r['output_tokens']==0 for r in ledger if r['extra'].get('counted_in')=='build')
finally:engine.dispose()

store=JsonArtifactStore(rd/'artifacts');graph=store.load_graph(receipt['doc_id'],receipt['graph_version']);lg=load_learning_graph(store,receipt['doc_id'],graph.version);ids=set(lg.learnable_nodes)
assert courses[0]['published_graph_version']==graph.version==8
members=[n for m in graph.payload['modules'] for n in m['node_ids']]
assert sorted(members)==sorted(ids) and sorted(graph.payload['sequence'])==sorted(ids)
hard=[e for e in [*graph.payload['requires_edges'],*graph.payload.get('bypassed_edges',[])] if not e.get('soft') and e['source'] in ids and e['target'] in ids]
assert all(len(p)==1 for p in strongly_connected_components(ids,hard))
ranks={n:i for i,n in enumerate(graph.payload['sequence'])};assert all(ranks[e['source']]<ranks[e['target']] for e in hard)
assert len(graph.payload['modules'])==16 and len(ids)==104 and len(lg.formula_images)==14
chunks=store.load_chunks(receipt['doc_id'],graph.manifest['config']['chunks_version']);fp=assert_retrieval_compatible(store.load_latest_retrieval(receipt['doc_id']).payload,chunks.result.chunks)
images=[]
for e in r6['artifact_images']:
 p=local(rd/e['path'],rd)
 assert digest(p)==e['sha256']
 with Image.open(p) as im:im.verify()
 with Image.open(p) as im:assert list(im.size)==e['size']
 images.append({'path':e['path'],'sha256':e['sha256']})
assert len(images)==33
r5=load(ev/'r5-20261025/summary.json');total=Decimal(r5['total_upper_usd'])+known+unknown;assert total==Decimal('2.38271210')<4
result=dict(source_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=WT,text=True).strip(),manifest_checks=checks,source_pdf_verified=True,plan_sha_verified=True,approval_sha_verified=True,sql_read_only=True,
 sql=dict(build_count=len(builds),course_count=len(courses),attempt_count=attempt_count,claim_count=builds[0]['claim_count'],course_status=courses[0]['status'],approval_state=approval['state'],ledger_total=str(sum((r['cost_usd'] for r in ledger),Decimal(0))),trace_rows_zero=True),
 graph=dict(version=graph.version,modules=len(graph.payload['modules']),learnable=len(ids),mentioned=len(graph.payload.get('mentioned_nodes',[])),nonlearnable=len(graph.payload.get('non_learnable_nodes',[])),formula_refs=len(lg.formula_images),module_and_sequence_coverage=True,hard_dag=True,topological=True,retrieval_compatible=True,quality_gate=graph.payload.get('quality_gate')),images_verified=len(images),requests=len(traces),operations=dict(counts),statuses=dict(statuses),two_429_recovered_same_payload=True,stage_peaks=peaks,known_demo_usd=str(known),unknown_upper_usd=str(unknown),combined_upper_usd=str(total),billing_verified=False,usage_complete=receipt['usage_complete'],provider_calls_this_review=0)
dump(OUT/'independent-audit.json',result);print(json.dumps(result,ensure_ascii=False,default=str))
