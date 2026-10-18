import importlib.util
import json
from pathlib import Path
from urllib.request import Request

import pytest


RUNNER_PATH = Path(__file__).resolve().parents[3] / "scripts" / "phase-b" / "sa28_acceptance.py"
spec = importlib.util.spec_from_file_location("sa28_live_runner", RUNNER_PATH)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def test_budget_gate_accounts_for_every_attempt_and_rejects_before_network():
    body = {"generationConfig": {"maxOutputTokens": 512}}
    request = Request("https://example.invalid", data=json.dumps(body).encode())
    one_attempt = runner.estimate_cost(runner.MODEL_ID, len(request.data), 512)
    gate = runner.BudgetGate(one_attempt * 1.5)

    assert gate.reserve_request(request) == one_attempt
    with pytest.raises(PermissionError, match="hard cap"):
        gate.reserve_request(request)
    assert gate.reserved == one_attempt


def test_installed_budget_gate_blocks_second_transport_attempt(monkeypatch):
    body = {"generationConfig": {"maxOutputTokens": 512}}
    request = Request("https://example.invalid", data=json.dumps(body).encode())
    one_attempt = runner.estimate_cost(runner.MODEL_ID, len(request.data), 512)
    gate = runner.BudgetGate(one_attempt * 1.5)
    forwarded = []
    original = lambda request, timeout=None: forwarded.append(request) or object()
    monkeypatch.setattr(runner.phase_b_transport, "urlopen", original)

    saved = runner.install_budget_gate(gate)
    try:
        runner.phase_b_transport.urlopen(request, timeout=1)
        with pytest.raises(PermissionError, match="hard cap"):
            runner.phase_b_transport.urlopen(request, timeout=1)
    finally:
        runner.phase_b_transport.urlopen = saved

    assert forwarded == [request]
    assert gate.reserved == one_attempt
