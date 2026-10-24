"""Operator-run W-15 budget reservations; every provider here is an in-process fake."""
import importlib
import importlib.util
from io import BytesIO
import json
from concurrent.futures import ThreadPoolExecutor
from threading import Event, Lock
from urllib.error import HTTPError
from urllib.request import Request

import pytest


def module():
    name = 'wayfinder.infrastructure.build_spend'
    assert importlib.util.find_spec(name), 'The approved-run reservation guard is missing'
    return importlib.import_module(name)


def request(model='gemini-3.1-flash-lite', operation='generateContent', **extra):
    payload = {'contents': [{'parts': [{'text': 'abc'}]}], 'generationConfig': {'maxOutputTokens': 8192}, **extra}
    return Request(f'https://aiplatform.googleapis.com/v1/projects/fake/locations/global/publishers/google/models/{model}:{operation}',
                   data=json.dumps(payload).encode())


def response(**usage):
    return BytesIO(json.dumps({'usageMetadata': dict(promptTokenCount=1000, candidatesTokenCount=10, **usage)}).encode())


def test_next_request_is_rejected_before_the_provider_when_capacity_is_exhausted():
    api = module()
    calls = []
    guard = api.BuildSpendGuard('.3606', lambda *a, **k: (calls.append(1), response())[1])
    guard(request())
    with pytest.raises(api.BuildSpendStopped):
        guard(request())
    assert len(calls) == 1 and guard.snapshot()['known_usd'] == '0.000265'
    assert guard.snapshot()['held_usd'] == '0'


def test_unknown_usage_preserves_the_reservation_and_blocks_later_dispatch():
    api = module()
    calls = []
    guard = api.BuildSpendGuard('1', lambda *a, **k: (calls.append(1), BytesIO(b'{}'))[1])
    assert guard(request()).read() == b'{}'
    with pytest.raises(api.BuildSpendStopped):
        guard(request())
    assert len(calls) == 1 and guard.snapshot()['unknown_upper_usd'] == '0.360448'


def test_a_timeout_retains_its_upper_bound_and_is_not_treated_as_zero_spend():
    api = module()
    calls = []
    def timeout(*args, **kwargs):
        calls.append(1)
        raise TimeoutError('fake timeout')
    guard = api.BuildSpendGuard('1', timeout)
    with pytest.raises(TimeoutError):
        guard(request())
    with pytest.raises(api.BuildSpendStopped):
        guard(request())
    assert len(calls) == 1 and guard.snapshot()['unknown_upper_usd'] == '0.360448'


def test_non_200_http_errors_do_not_consume_the_approved_budget():
    api = module()
    def error(*args, **kwargs):
        raise HTTPError('https://example.invalid', 429, 'fake quota', {}, None)
    guard = api.BuildSpendGuard('1', error)
    with pytest.raises(HTTPError):
        guard(request())
    assert guard.snapshot()['known_usd'] == guard.snapshot()['unknown_upper_usd'] == '0'


def test_inline_images_use_the_full_documented_model_window_bound():
    api = module()
    guard = api.BuildSpendGuard('1', lambda *a, **k: response())
    image = request(contents=[{'parts': [{'inlineData': {'mimeType': 'image/png', 'data': 'ZmFrZQ=='}}]}])
    assert guard.bound(image) == guard.bound(request())


@pytest.mark.parametrize('bad', [request('another-model'), request(tools=[{'googleSearch': {}}]),
    request(serviceTier='PRIORITY'),
    request(contents=[{'parts': [{'inlineData': {'mimeType': 'audio/wav', 'data': 'ZmFrZQ=='}}]}]),
    request(contents=[{'parts': [{'fileData': {'mimeType': 'video/mp4', 'fileUri': 'gs://fake/input'}}]}]),
    Request('https://generativelanguage.googleapis.com/model', data=b'{}')])
def test_unpriced_models_extra_services_and_wrong_transport_never_reach_the_provider(bad):
    api = module()
    calls = []
    guard = api.BuildSpendGuard('1', lambda *a, **k: (calls.append(1), response())[1])
    with pytest.raises(api.BuildSpendStopped):
        guard(bad)
    assert calls == []


def test_missing_output_usage_keeps_known_cost_of_other_responses():
    api = module()
    replies = iter([response(), BytesIO(b'{"usageMetadata":{"promptTokenCount":50}}')])
    guard = api.BuildSpendGuard('1', lambda *a, **k: next(replies))
    guard(request())
    guard(request())
    with pytest.raises(api.BuildSpendStopped):
        guard(request())
    assert guard.snapshot()['known_usd'] == '0.000265'
    assert guard.snapshot()['unknown_upper_usd'] == '0.360448'


def test_stop_exception_is_not_swallowed_as_a_model_repair_error():
    assert not issubclass(module().BuildSpendStopped, RuntimeError)


def test_parallel_requests_reserve_capacity_until_their_responses_arrive(monkeypatch):
    api = module()
    first_pair, release, waiting = Event(), Event(), Event()
    lock = Lock()
    counts = {'calls': 0, 'active': 0, 'peak': 0}
    def provider(*args, **kwargs):
        with lock:
            counts['calls'] += 1
            turn = counts['calls']
            counts['active'] += 1
            counts['peak'] = max(counts['peak'], counts['active'])
            if turn == 2:
                first_pair.set()
        assert release.wait(5)
        with lock:
            counts['active'] -= 1
        return response()
    guard = api.BuildSpendGuard('.721', provider)
    original_wait = guard.condition.wait
    def observed_wait(*args, **kwargs):
        waiting.set()
        return original_wait(*args, **kwargs)
    monkeypatch.setattr(guard.condition, 'wait', observed_wait)
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(lambda: guard(request()).read()) for _ in range(3)]
        try:
            assert first_pair.wait(5) and waiting.wait(5)
            assert counts['calls'] == 2
        finally:
            release.set()
        replies = [future.result() for future in futures]
    assert len(replies) == counts['calls'] == 3 and counts['peak'] == 2
    assert guard.snapshot()['known_usd'] == '0.000795' and guard.snapshot()['held_usd'] == '0'


def test_embedding_usage_and_unknown_embedding_usage_are_kept_separate():
    api = module()
    replies = iter([BytesIO(b'{"predictions":[{"embeddings":{"statistics":{"token_count":100}}}]}'),
                    BytesIO(b'{"predictions":[{"embeddings":{"statistics":{}}}]}')])
    guard = api.BuildSpendGuard('1', lambda *a, **k: next(replies))
    embedding = request('gemini-embedding-001', 'predict', instances=[{'content': 'abc'}])
    guard(embedding)
    guard(embedding)
    with pytest.raises(api.BuildSpendStopped):
        guard(embedding)
    assert guard.snapshot()['known_usd'] == '0.000015' and guard.snapshot()['unknown_upper_usd'] == '0.0003072'


def test_overlapping_embedding_intervals_are_not_counted_twice():
    guard = module().BuildSpendGuard('1', lambda *a, **k: response())
    guard.embedding_spans = [('concepts', 1, 4), ('concepts', 2, 3), ('concepts', 6, 7), ('graph', 2, 9)]
    assert guard.embedding_wait('concepts') == 4 and guard.embedding_wait('graph') == 7
    assert guard.embedding_wait('doc_reading') == 0


def test_request_audit_retains_unknown_cost_after_a_timeout(tmp_path):
    api = module()
    def timeout(*args, **kwargs):
        raise TimeoutError('fake timeout')
    log = tmp_path / 'requests.jsonl'
    guard = api.BuildSpendGuard('1', timeout, log=log)
    with pytest.raises(TimeoutError):
        guard(request())
    rows = [json.loads(line) for line in log.read_text(encoding='utf-8').splitlines()]
    assert len(rows) == 1 and rows[0]['actual_usd'] is None
    assert rows[0]['budget']['unknown_upper_usd'] == '0.360448'


def test_an_unwritable_audit_stops_further_dispatch_without_discarding_known_cost(tmp_path):
    api = module()
    calls = []
    guard = api.BuildSpendGuard('1', lambda *a, **k: (calls.append(1), response())[1], log=tmp_path)
    assert guard(request()).read()
    with pytest.raises(api.BuildSpendStopped):
        guard(request())
    assert len(calls) == 1 and guard.snapshot()['known_usd'] == '0.000265' and guard.snapshot()['audit_failed']
