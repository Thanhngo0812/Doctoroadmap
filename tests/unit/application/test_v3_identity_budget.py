import importlib.util
import json
from pathlib import Path

import pytest


def runner():
    path = Path(__file__).resolve().parents[3] / "scripts/doc-lo-trinh/chay_danh_tinh_v3.py"
    spec = importlib.util.spec_from_file_location("identity_v3_run", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_evaluation_budget_refuses_before_the_network_and_accounts_for_real_usage(monkeypatch, tmp_path):
    module = runner()
    calls = []

    def complete(self, *args):
        calls.append(args)
        assert self._max_output_tokens == 1024 and self._max_retries == 0 and self._temperature == 0
        return "{}", {"promptTokenCount": 100, "candidatesTokenCount": 10, "thoughtsTokenCount": 5}

    monkeypatch.setattr(module.GeminiEntityExtractor, "_complete", complete)
    ledger = tmp_path / "spend.json"
    model = module.MeteredGemini("test-key", max_usd=0.00001, ledger_path=ledger)
    with pytest.raises(module.BudgetStop):
        model._complete("system", [], {})
    assert not calls and not ledger.exists()
    model.limit = 1.50
    model._complete("system", [], {})
    assert len(calls) == 1
    value = json.loads(ledger.read_text())
    assert value[0]["usd"] == pytest.approx((100 * .25 + 15 * 1.5) / 1e6)
    assert not value[0]["reserved"]
    assert module.MeteredGemini("test-key", max_usd=1.50, ledger_path=ledger).ledger == value


def test_failed_completion_keeps_reservation_instead_of_claiming_zero_cost(monkeypatch, tmp_path):
    module = runner()

    def fail(*args):
        raise OSError("network interrupted")

    monkeypatch.setattr(module.GeminiEntityExtractor, "_complete", fail)
    ledger = tmp_path / "spend.json"
    model = module.MeteredGemini("test-key", max_usd=1.50, ledger_path=ledger)
    with pytest.raises(OSError):
        model._complete("system", [], {})
    rows = json.loads(ledger.read_text())
    assert len(rows) == 1 and rows[0]["reserved"] and rows[0]["usd"] > 0
