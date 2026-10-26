"""Standalone offline observations against exact compiled worker source; no DB/provider/ADC."""
from pathlib import Path
from types import ModuleType,SimpleNamespace as NS
import sys,json,hashlib
from io import BytesIO
from urllib.request import Request
from concurrent.futures import ThreadPoolExecutor
from threading import Event,Lock
ROOT=Path(r'C:/Users/ngoco/Desktop/Doctoroadmap')
WT=ROOT/'tmp/w15-real-build';OUT=Path(__file__).parent
sys.path[:0]=[str(WT/'src'),str(WT/'src/web/backend')]
variant=sys.argv[1] if len(sys.argv)>1 else 'baseline'
guard_source=(WT/'src/web/backend/wayfinder/infrastructure/build_spend.py').read_text(encoding='utf-8')
adapter_source=(WT/'src/web/backend/wayfinder/infrastructure/real_build.py').read_text(encoding='utf-8')
if variant=='drop-unknown':
 assert guard_source.count('self.known + self.unknown + self.held + value <= self.limit')==1
 guard_source=guard_source.replace('self.known + self.unknown + self.held + value <= self.limit','self.known + self.held + value <= self.limit')
elif variant=='disable-opt-in':
 assert guard_source.count('self.stopped or (self.unknown and not self.retry_unknown_within_cap)')==1
 guard_source=guard_source.replace('self.stopped or (self.unknown and not self.retry_unknown_within_cap)','self.stopped or self.unknown')
elif variant=='override-result':
 assert adapter_source.count('spend_guard.stopped or (spend_guard.unknown and not spend_guard.retry_unknown_within_cap)')==1
 adapter_source=adapter_source.replace('spend_guard.stopped or (spend_guard.unknown and not spend_guard.retry_unknown_within_cap)','spend_guard.stopped or spend_guard.unknown')

def module(name,source):
 m=ModuleType(name);sys.modules[name]=m;exec(compile(source,'<review-'+name+'>','exec'),m.__dict__);return m
api=module('review_build_spend',guard_source);adapter=module('review_real_build',adapter_source)

def request(embedding=False):
 model='gemini-embedding-001:predict' if embedding else 'gemini-3.1-flash-lite:generateContent'
 data={'instances':[{'content':'synthetic'}]} if embedding else {'contents':[{'parts':[{'text':'synthetic'}]}],'generationConfig':{'maxOutputTokens':8192}}
 return Request('https://aiplatform.googleapis.com/v1/projects/fake/locations/global/publishers/google/models/'+model,data=json.dumps(data).encode())
def response(embedding=False):
 data={'predictions':[{'embeddings':{'statistics':{'token_count':100}}}]} if embedding else {'usageMetadata':{'promptTokenCount':1000,'candidatesTokenCount':10}}
 return BytesIO(json.dumps(data).encode())

def expected_error(kind,fn):
 try:fn()
 except kind:return
 raise AssertionError('Expected '+kind.__name__+' did not occur')

def legacy_unknown_denies_dispatch():
 calls=[]
 def fake(*args,**kwargs):calls.append(1);raise TimeoutError('fake')
 g=api.BuildSpendGuard('1',fake)
 expected_error(TimeoutError,lambda:g(request()))
 expected_error(api.BuildSpendStopped,lambda:g(request()))
 assert len(calls)==1 and g.unknown==api.Decimal('.360448')

def approved_retry_preserves_unknown_and_cap():
 calls=[]
 def fake(*args,**kwargs):
  calls.append(1)
  if len(calls)==1:raise TimeoutError('synthetic')
  return response()
 g=api.BuildSpendGuard('.721',fake,retry_unknown_within_cap=True)
 expected_error(TimeoutError,lambda:g(request()))
 assert g(request()).read()
 expected_error(api.BuildSpendStopped,lambda:g(request()))
 assert len(calls)==2 and g.unknown==api.Decimal('.360448') and g.known==api.Decimal('.000265') and g.held==0

def strict_boolean():
 for val in [None,1,'true',[],{}]:expected_error(ValueError,lambda:api.BuildSpendGuard('1',lambda *a,**k:response(),retry_unknown_within_cap=val))

def parallel_reservations_keep_retained_unknown():
 calls=[];lock=Lock();both=Event();release=Event()
 def fake(*args,**kwargs):
  with lock:
   calls.append(1);seq=len(calls)
   if seq==2:both.set()
  assert both.wait(5)
  if seq==1:raise TimeoutError('synthetic timeout in concurrent batch')
  assert release.wait(5)
  return response(True)
 g=api.BuildSpendGuard('.00062',fake,embedding_price_profile=api.DEMO_EMBEDDING_PRICE_PROFILE,retry_unknown_within_cap=True)
 def attempt():
  try:g(request(True));return 'ok'
  except TimeoutError:return 'timeout'
  except api.BuildSpendStopped:return 'stopped'
 with ThreadPoolExecutor(max_workers=3) as pool:
  a,b=pool.submit(attempt),pool.submit(attempt)
  assert both.wait(5)
  c=pool.submit(attempt);release.set()
  results=[x.result(timeout=5) for x in [a,b,c]]
 assert sorted(results)==['ok','stopped','timeout'] and len(calls)==2
 assert g.unknown==api.Decimal('.0003072') and g.known==api.Decimal('.000015') and g.held==0

def ready_wrapper_keeps_result_but_reports_unknown():
 guard=api.BuildSpendGuard('1',lambda *a,**k:response(),retry_unknown_within_cap=True)
 guard.unknown=api.Decimal('.0003072')
 class P:
  def usage(self):return dict(spent_usd=0,model_calls=0,input_tokens=0,output_tokens=0,usage_complete=True)
  def read(self,*a):return {'page_texts':['Đây là giáo trình tiếng Việt có đầy đủ ví dụ. '*30]}
  def label_roles(self,*a):return {}
  def a3(self,*a):return {}
  def canonical(self,*a):return {}
  def roadmap(self,*a):return {'graph_version':8}
  def learning_prep(self,*a):return {}
 runtime=NS(settings=NS(),pipeline_factory=lambda *a,**k:P(),phase_b_store=NS(),pipeline_version='synthetic-reviewed',monotonic=lambda:0)
 rows=[];r=adapter.RealBuildAdapter(runtime,rows.append)._execute(OUT/'synthetic.pdf','u-offline','vi',None,None,allow_spend=True,spend_guard=guard)
 assert r.status=='succeeded' and r.graph_version==8 and r.usage_complete is False and rows==[r]
 guard.stopped=True;rows=[]
 r=adapter.RealBuildAdapter(runtime,rows.append)._execute(OUT/'synthetic.pdf','u-offline','vi',None,None,allow_spend=True,spend_guard=guard)
 assert r.status=='failed' and r.usage_complete is False and rows==[r]

checks=[]
for fn in [legacy_unknown_denies_dispatch,strict_boolean,approved_retry_preserves_unknown_and_cap,parallel_reservations_keep_retained_unknown,ready_wrapper_keeps_result_but_reports_unknown]:
 try:fn();checks.append({'name':fn.__name__,'passed':True})
 except Exception as e:
  checks.append({'name':fn.__name__,'passed':False,'error_type':type(e).__name__,'message':str(e)})
value={'variant':variant,'checks':checks,'provider_calls':0,'database_connections':0,'guard_compiled_sha256':hashlib.sha256(guard_source.encode()).hexdigest(),'adapter_compiled_sha256':hashlib.sha256(adapter_source.encode()).hexdigest()}
(OUT/(variant+'-probe.json')).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8');print(json.dumps(value));raise SystemExit(0 if all(r['passed'] for r in checks) else 1)
