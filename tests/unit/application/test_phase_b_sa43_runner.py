import importlib.util
import json
from pathlib import Path
from urllib.request import Request

import pytest


@pytest.fixture
def runner(monkeypatch):
    root = Path(__file__).resolve().parents[3]
    monkeypatch.syspath_prepend(str(root / 'scripts/phase-b'))
    spec = importlib.util.spec_from_file_location('sa43_acceptance_runner', root / 'scripts/phase-b/sa43_acceptance.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_shared_first_attempt_is_replayed_once_and_only_repair_calls_provider(runner):
    class Delegate:
        model_id = 'gemini-3.1-flash-lite'
        calls = []
        def start_session(self, system):
            parent = self
            class Session:
                last_usage = {'input_tokens': 4}
                last_ttft_ms = 7
                last_finish_reason = 'STOP'
                def stream_json(self, prompt, **kwargs):
                    parent.calls.append((system, prompt, kwargs))
                    yield '{"same":true}'
            return Session()
    delegate, shared = Delegate(), {}
    first = runner.SharedFirstModel(delegate, shared)
    original = list(first.start_session('system').stream_json('prompt', response_schema={}, temperature=0,
                                                             transport_retries=1, timeout_seconds=30))
    second = runner.SharedFirstModel(delegate, shared, reuse=True)
    copied = list(second.start_session('system').stream_json('prompt', response_schema={}, temperature=0,
                                                            transport_retries=1, timeout_seconds=30))
    assert original == copied
    assert len(delegate.calls) == 1 and second.is_replay is True
    list(second.start_session('system').stream_json('repair', response_schema={}, temperature=1,
                                                    transport_retries=1, timeout_seconds=30))
    assert len(delegate.calls) == 2 and second.is_replay is False
    assert delegate.calls[-1][2]['temperature'] == 1


def test_comparison_rejects_changed_first_prompt_without_provider_call(runner):
    class Delegate:
        model_id = 'fake'
        def start_session(self, *_):
            pytest.fail('shared first must not call provider')
    shared = {'system_prompt': 's', 'request': {'prompt': 'p', 'schema': {}, 'temperature': 0}, 'chunks': []}
    model = runner.SharedFirstModel(Delegate(), shared, reuse=True)
    with pytest.raises(ValueError, match='exact first request'):
        list(model.start_session('s').stream_json('changed', response_schema={}, temperature=0))


def test_runner_dry_run_and_existing_output_never_start_runtime(runner, monkeypatch, tmp_path, capsys):
    plan = tmp_path / 'plan.json'
    plan.write_text('{"max_logical_estimate_usd":0.14}', encoding='utf-8')
    monkeypatch.setattr(runner, 'PLAN', plan)
    monkeypatch.setattr(runner, 'PhaseBRuntime', lambda **_: pytest.fail('must not start runtime'))
    monkeypatch.setattr('sys.argv', ['sa43_acceptance.py'])
    runner.main()
    assert json.loads(capsys.readouterr().out)['network_calls'] == 0
    paid = tmp_path / 'paid.json'
    paid.write_text('already completed', encoding='utf-8')
    monkeypatch.setattr(runner, 'STORE', paid)
    with pytest.raises(FileExistsError, match='spending twice'):
        runner.execute({})
    assert paid.read_text() == 'already completed'


def test_hard_gate_refuses_an_http_attempt_before_network(runner):
    gate = runner.BudgetGate(.000001)
    request = Request('https://example.invalid', data=json.dumps({'generationConfig': {'maxOutputTokens': 2048}}).encode())
    with pytest.raises(PermissionError, match='hard cap'):
        gate.reserve_request(request)
    assert gate.attempts == 0 and gate.reserved == 0
