import importlib.util
import json
from pathlib import Path

import pytest


def runner():
    path = Path(__file__).resolve().parents[3] / "scripts/doc-lo-trinh/evaluation_runtime.py"
    spec = importlib.util.spec_from_file_location("identity_v3_run", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_evaluation_budget_refuses_before_the_network_and_accounts_for_real_usage(monkeypatch, tmp_path):
    module = runner()
    calls = []

    def complete(self, *args):
        calls.append(args)
        assert self._max_output_tokens == 1024 and self._max_retries == 8 and self._temperature == 0
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


def test_windows_ledger_replace_conflict_retries_before_network(monkeypatch, tmp_path):
    module = runner()
    original = module.JsonArtifactStore._write
    attempts = []

    def flaky(path, payload):
        attempts.append(path)
        if len(attempts) == 1:
            raise PermissionError("file briefly open")
        return original(path, payload)

    monkeypatch.setattr(module.JsonArtifactStore, "_write", staticmethod(flaky))
    monkeypatch.setattr(module, "sleep", lambda seconds: None)
    monkeypatch.setattr(module.GeminiEntityExtractor, "_complete",
                        lambda self, *args: ("{}", {"promptTokenCount": 1, "candidatesTokenCount": 1}))
    ledger = tmp_path / "spend.json"
    module.MeteredGemini("key", max_usd=1, ledger_path=ledger)._complete("system", [], {})
    assert len(attempts) == 3  # reserve retried once; final actual usage written once
    assert json.loads(ledger.read_text())[0]["reserved"] is False


def test_jsonl_ledger_appends_and_recovers_latest_event(monkeypatch, tmp_path):
    module = runner()
    monkeypatch.setattr(module.GeminiEntityExtractor, "_complete",
                        lambda self, *args: ("{}", {"promptTokenCount": 10, "candidatesTokenCount": 2}))
    legacy = tmp_path / "spend.json"
    legacy.write_text(json.dumps([{"usd": .25, "reserved": False, "transport": "vertex"}]), encoding="utf-8")
    ledger = tmp_path / "spend.jsonl"
    model = module.MeteredGemini("key", max_usd=1, ledger_path=ledger)
    model._complete("system", [], {})

    events = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()]
    assert len(events) == 3  # migrated legacy + reserve + completion; no full-file rewrite.
    assert events[-2]["call_id"] == events[-1]["call_id"] and events[-2]["reserved"] and not events[-1]["reserved"]
    recovered = module.MeteredGemini("key", max_usd=1, ledger_path=ledger)
    assert len(recovered.ledger) == 2
    assert sum(row["usd"] for row in recovered.ledger) == pytest.approx(.25 + events[-1]["usd"])
