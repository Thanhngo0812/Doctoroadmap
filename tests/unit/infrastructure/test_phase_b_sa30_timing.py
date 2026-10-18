import io
import json

import pytest

from doc2roadmap.application.phase_b.common import call_json
from doc2roadmap.application.ports.phase_b import Done
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore
from doc2roadmap.infrastructure.llm import phase_b
from doc2roadmap.infrastructure.llm.phase_b import GeminiToolModel, RecordingToolModel, ReplayToolModel


def timed_http(monkeypatch, *, tool=False, invalid=False):
    from doc2roadmap.application.phase_b import common
    now = [0.0]
    monkeypatch.setattr(phase_b, 'perf_counter', lambda: now[0])
    monkeypatch.setattr(common, 'perf_counter', lambda: now[0])
    text = 'not-json' if invalid else '{"ok":true}'
    part = {'functionCall': {'name': 'lookup', 'args': {}, 'id': 'c1'}} if tool else {'text': text}
    payload = {'candidates': [{'content': {'parts': [part]}, 'finishReason': 'STOP'}],
               'usageMetadata': {'promptTokenCount': 7, 'candidatesTokenCount': 3}}

    class Response:
        def __init__(self):
            self.body = io.BytesIO(json.dumps(payload).encode())

        def read(self, size=-1):
            now[0] += .5 if self.body.tell() == 0 else 3
            return self.body.read(size)

        def __iter__(self):
            now[0] += .5
            yield b'data: ' + json.dumps(payload).encode() + b'\n'
            yield b'\n'
            now[0] += 3

        def close(self):
            pass

    def open_request(request, timeout):
        now[0] += 2  # Waiting for response headers is part of time to first content.
        return Response()

    monkeypatch.setattr(phase_b, 'urlopen', open_request)
    return GeminiToolModel('fake-key'), now


def test_json_stream_ttft_includes_request_wait(monkeypatch):
    model, _ = timed_http(monkeypatch)
    session = model.start_session('system')
    assert ''.join(session.stream_json('prompt', response_schema={})) == '{"ok":true}'
    assert session.last_ttft_ms == 2500


@pytest.mark.parametrize('tool', [False, True])
def test_conversation_ttft_includes_request_wait_for_text_or_tool(monkeypatch, tool):
    model, _ = timed_http(monkeypatch, tool=tool)
    session = model.start_session('system')
    events = list(session.stream([{'role': 'user', 'text': 'prompt'}]))
    assert next(event for event in events if isinstance(event, Done)).ttft_ms == 2500
    assert session.last_ttft_ms == 2500


def test_json_first_byte_timing_is_recorded_in_ledger_and_replayed(monkeypatch, tmp_path):
    model, _ = timed_http(monkeypatch)
    fixture = tmp_path / 'timing.json'
    recorded = RecordingToolModel(model, fixture, prompt_hash='timing')
    store = InMemoryPhaseBStore()
    result = call_json(recorded, 'prompt', response_schema={}, store=store,
                       purpose='document', doc_id='dev', context_hash='ctx', allow_spend=True, learner_id='tester')
    assert result.payload == {'ok': True}
    assert result.ttft_ms == store.usage_rows()[0]['ttft_ms'] == 2500
    assert result.elapsed_ms == store.usage_rows()[0]['elapsed_ms'] == 5500
    assert json.loads(fixture.read_text())['sessions'][0]['calls'][0]['ttft_ms'] == 2500

    def forbidden(*args, **kwargs):
        pytest.fail('replay must not call HTTP')

    monkeypatch.setattr(phase_b, 'urlopen', forbidden)
    replay = ReplayToolModel(fixture, prompt_hash='timing')
    replay_store = InMemoryPhaseBStore()
    replayed = call_json(replay, 'prompt', response_schema={}, store=replay_store,
                         purpose='document', doc_id='dev', context_hash='ctx', allow_spend=True, learner_id='tester')
    assert replayed.ttft_ms == replay_store.usage_rows()[0]['ttft_ms'] == 2500
    assert replayed.cost_usd == 0


def test_invalid_json_keeps_first_byte_timing_on_failed_usage(monkeypatch, tmp_path):
    model, _ = timed_http(monkeypatch, invalid=True)
    recorded = RecordingToolModel(model, tmp_path / 'invalid.json', prompt_hash='timing')
    store = InMemoryPhaseBStore()
    with pytest.raises(json.JSONDecodeError):
        call_json(recorded, 'prompt', response_schema={}, store=store,
                  purpose='document', doc_id='dev', context_hash='ctx', allow_spend=True, learner_id='tester')
    [row] = store.usage_rows()
    assert row['failed'] is True
    assert row['ttft_ms'] == 2500
    assert row['input_tokens'] == 7
