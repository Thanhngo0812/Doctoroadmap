"""Independent fake-store/HTTP probes; no PostgreSQL or live transport."""
from contextlib import nullcontext
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from types import SimpleNamespace as NS
import sys
from urllib.request import Request

sys.dont_write_bytecode = True
ROOT = Path('C:/Users/ngoco/Desktop/Doctoroadmap/tmp/w15-real-build')
sys.path[:0] = [str(ROOT / 'src/web/backend'), str(ROOT / 'src')]
from wayfinder.infrastructure.build_spend import BuildSpendApproval, BuildSpendGuard, BuildSpendStopped, DEMO_EMBEDDING_PRICE_PROFILE as DEMO
from wayfinder.infrastructure.real_build import RealBuildAdapter
from doc2roadmap.application.ports.build import BuildRejected

source = Path(__file__).parent / 'offline-grant-input.pdf'
source.write_bytes(b'Independent synthetic grant input')
digest = sha256(source.read_bytes()).hexdigest()
doc = 'u-' + digest[:20]
class Store:
    def __init__(self):
        self.records, self.operations = {}, []
    def atomic(self):
        return nullcontext()
    def get_record(self, kind, ref):
        self.operations.append('get')
        return self.records.get((kind, ref))
    def put_record(self, kind, ref, record):
        self.operations.append('put')
        self.records[kind, ref] = record
class Pipeline:
    def usage(self):
        return dict(spent_usd=0, model_calls=0, input_tokens=0, output_tokens=0, usage_complete=True)
    def read(self, *a):
        raise BuildRejected('chu_loi', 'Offline stop before any provider')
def runtime():
    calls = []
    def factory(*a, allow_spend, phase_b_store):
        calls.append(allow_spend)
        return Pipeline()
    settings = NS(vertex_location='global', embedding_model_id='gemini-embedding-001',
                  extraction_model_id='gemini-3.1-flash-lite', merge_model_id='gemini-3.1-flash-lite',
                  description_model_id='gemini-3.1-flash-lite', roadmap_model_id='gemini-3.1-flash-lite')
    return NS(settings=settings, pipeline_factory=factory, pipeline_version='offline-reviewed-profile',
              phase_b_store=Store(), spend_approval=None, monotonic=lambda: 0.), calls

normal, calls = runtime()
receipts = []
assert RealBuildAdapter(normal, receipts.append).execute(source, doc).status == 'rejected'
assert calls == [False] and len(receipts) == 1 and not normal.phase_b_store.operations

for price in [None, 'another-price-profile']:
    denied, calls = runtime()
    denied.spend_approval = BuildSpendApproval('fake-denied', digest, denied.pipeline_version, '1', embedding_price_profile=price)
    receipts = []
    try:
        RealBuildAdapter(denied, receipts.append).execute(source, doc)
    except BuildSpendStopped:
        pass
    else:
        raise AssertionError('A missing/wrong profile activated spend')
    assert calls == receipts == denied.phase_b_store.operations == []

allowed, calls = runtime()
allowed.spend_approval = BuildSpendApproval('fake-once', digest, allowed.pipeline_version, '1', embedding_price_profile=DEMO)
receipts = []
RealBuildAdapter(allowed, receipts.append).execute(source, doc)
record = allowed.phase_b_store.records['w15_build_approval', 'fake-once']
assert calls == [True] and len(receipts) == 1 and record['state'] == 'finished'
assert record['embedding_billing_verified'] is record['budget']['embedding_billing_verified'] is False
try:
    RealBuildAdapter(allowed, receipts.append).execute(source, doc)
except ValueError as error:
    assert 'consumed' in str(error)
else:
    raise AssertionError('Same reference activated twice')
assert calls == [True] and len(receipts) == 1

def embedding():
    return Request('https://aiplatform.googleapis.com/v1/projects/fake/locations/global/publishers/google/models/gemini-embedding-001:predict',
                   data=b'{"instances":[{"content":"fake input"}]}')
denied_calls = []
guard = BuildSpendGuard('1', lambda *a, **k: denied_calls.append(1))
try:
    guard(embedding())
except BuildSpendStopped:
    pass
else:
    raise AssertionError('Default embedding guard dispatched')
assert denied_calls == [] and guard.snapshot()['http_calls'] == 0
replies = iter([b'{"predictions":[{"embeddings":{"statistics":{"token_count":100}}}],"metadata":{"billableCharacterCount":9999}}',
                b'{"predictions":[{"embeddings":{"statistics":{}}}],"metadata":{"billableCharacterCount":112}}'])
fake_calls = []
def provider(*a, **k):
    fake_calls.append(1)
    return BytesIO(next(replies))
demo = BuildSpendGuard('1', provider, embedding_price_profile=DEMO)
demo(embedding())
demo(embedding())
try:
    demo(embedding())
except BuildSpendStopped:
    pass
else:
    raise AssertionError('Missing tokens did not block following dispatch')
assert len(fake_calls) == 2 and demo.snapshot()['known_usd'] == '0.000015'
assert demo.snapshot()['unknown_upper_usd'] == '0.0003072' and demo.snapshot()['embedding_billing_verified'] is False
generation = Request('https://aiplatform.googleapis.com/v1/projects/fake/locations/global/publishers/google/models/gemini-3.1-flash-lite:generateContent',
                     data=b'{"contents":[{"parts":[{"text":"fake"}]}],"generationConfig":{"maxOutputTokens":8192}}')
timeout_calls = []
def after_known_timeout(*a, **k):
    timeout_calls.append(1)
    if len(timeout_calls) == 1:
        return BytesIO(b'{"usageMetadata":{"promptTokenCount":1000,"candidatesTokenCount":10}}')
    raise TimeoutError('offline timeout after earlier known usage')
timeout = BuildSpendGuard('1', after_known_timeout)
timeout(generation)
try:
    timeout(generation)
except TimeoutError:
    pass
else:
    raise AssertionError('Expected fake timeout')
try:
    timeout(generation)
except BuildSpendStopped:
    pass
else:
    raise AssertionError('Unknown timeout allowed another dispatch')
assert len(timeout_calls) == 2 and timeout.snapshot()['known_usd'] == '0.000265'
assert timeout.snapshot()['unknown_upper_usd'] == '0.360448'
print(json.dumps({'provider_calls': 0, 'database_connections': 0, 'default_adapter_allow_spend_false': True,
                  'missing_or_wrong_grant_profile_denied_before_store': True, 'grant_consumed_once_in_fake_store': True,
                  'default_embedding_dispatch_denied': True, 'demo_token_arithmetic': demo.snapshot(),
                  'character_only_usage_not_treated_complete': True, 'timeout_retains_earlier_known_cost': timeout.snapshot()}, indent=2))
