"""Isolated fake-only probes for dispatch limits and unknown usage retention."""
from hashlib import sha256
import importlib.util
from io import BytesIO
import json
from pathlib import Path
import sys
from urllib.request import Request

sys.dont_write_bytecode = True
ROOT = Path('C:/Users/ngoco/Desktop/Doctoroadmap/tmp/w15-real-build')
source = ROOT / 'src/web/backend/wayfinder/infrastructure/build_spend.py'
spec = importlib.util.spec_from_file_location('review_spend', source)
api = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = api
spec.loader.exec_module(api)

def request():
    return Request('https://aiplatform.googleapis.com/v1/projects/fake/locations/global/publishers/google/models/gemini-3.1-flash-lite:generateContent',
                   data=json.dumps({'contents': [{'parts': [{'text': 'fake'}]}],
                                    'generationConfig': {'maxOutputTokens': 8192}}).encode())

def response(output=10):
    return BytesIO(json.dumps({'usageMetadata': {'promptTokenCount': 1000, 'candidatesTokenCount': output}}).encode())

def refused(guard):
    try:
        guard(request())
    except api.BuildSpendStopped:
        return
    raise AssertionError('A stopped guard dispatched another request')

calls = []
guard = api.BuildSpendGuard('.3606', lambda *a, **k: (calls.append(1), response())[1])
guard(request())
refused(guard)
assert len(calls) == 1 and guard.snapshot()['known_usd'] == '0.000265'

unknown_calls = []
def timeout(*args, **kwargs):
    unknown_calls.append(1)
    raise TimeoutError('in-process fake timeout')
unknown = api.BuildSpendGuard('1', timeout)
try:
    unknown(request())
except TimeoutError:
    pass
else:
    raise AssertionError('Expected synthetic timeout')
refused(unknown)
assert len(unknown_calls) == 1 and unknown.snapshot()['unknown_upper_usd'] == '0.360448'

exceeded_calls = []
exceeded = api.BuildSpendGuard('1', lambda *a, **k: (exceeded_calls.append(1), response(1_000_000))[1])
exceeded(request())
refused(exceeded)
assert len(exceeded_calls) == 1 and exceeded.stopped and exceeded.snapshot()['known_usd'] == '1.50025'

print(json.dumps({'source_sha256': sha256(source.read_bytes()).hexdigest(), 'provider_calls': 0,
                  'database_connections': 0, 'fake_dispatches': len(calls) + len(unknown_calls) + len(exceeded_calls),
                  'capacity_stop': guard.snapshot(), 'timeout': unknown.snapshot(),
                  'reported_bound_exceeded': exceeded.snapshot()}, indent=2))
