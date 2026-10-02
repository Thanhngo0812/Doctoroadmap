import importlib.util
import json
from pathlib import Path
from urllib.error import HTTPError

import pytest
from google.auth.exceptions import RefreshError, TransportError as AuthTransportError

from doc2roadmap.application.ports.extraction import ModelTransportError


def load_driver(monkeypatch):
    scripts = Path(__file__).resolve().parents[3] / "scripts/doc-lo-trinh"
    monkeypatch.syspath_prepend(str(scripts))
    spec = importlib.util.spec_from_file_location("a8_full_v3", scripts / "chay_a8_full_v3.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def transport_error(code):
    try:
        raise HTTPError("https://vertex.example", code, "temporary", {}, None)
    except HTTPError as cause:
        raise ModelTransportError("Gemini API lỗi tạm thời sau 4 lần thử") from cause


def test_temporary_error_retries_from_saved_progress_and_logs_cause(monkeypatch, tmp_path):
    driver = load_driver(monkeypatch)
    waits = []
    monkeypatch.setattr(driver, "sleep", waits.append)
    monkeypatch.setattr(driver, "monotonic", lambda: sum(waits))
    monkeypatch.setattr(driver, "MAX_OUTAGE_SECONDS", 50)
    progress = {"completed": 0}

    def stage():
        if progress["completed"] < 2:
            progress["completed"] += 1  # Stand-in for a persisted pair checkpoint.
            transport_error(503)
        return progress["completed"]

    events = tmp_path / "transport-retries.jsonl"
    assert driver.retry_temporary(stage, stage="doc-1:secondary", event_path=events,
                                  progress=lambda: progress["completed"]) == 2
    assert waits == [30, 30]  # Progress resets the outage clock, even across a long stage.
    rows = [json.loads(line) for line in events.read_text(encoding="utf-8").splitlines()]
    assert [row["cause"] for row in rows] == ["HTTP 503", "HTTP 503"]
    assert [row["wait_seconds"] for row in rows] == waits


def test_nonretryable_error_and_budget_stop_are_not_retried(monkeypatch, tmp_path):
    driver = load_driver(monkeypatch)
    from chay_danh_tinh_v3 import BudgetStop

    monkeypatch.setattr(driver, "sleep", lambda _: pytest.fail("must not sleep"))
    events = tmp_path / "transport-retries.jsonl"
    with pytest.raises(ModelTransportError):
        driver.retry_temporary(lambda: transport_error(403), stage="doc-1:secondary",
                               event_path=events, progress=lambda: 0)

    def exhausted_budget():
        raise BudgetStop("cap")

    with pytest.raises(BudgetStop):
        driver.retry_temporary(exhausted_budget, stage="doc-1:secondary",
                               event_path=events, progress=lambda: 0)
    assert not events.exists()


def test_temporary_outage_has_finite_limit(monkeypatch, tmp_path):
    driver = load_driver(monkeypatch)
    waits = []
    monkeypatch.setattr(driver, "sleep", waits.append)
    monkeypatch.setattr(driver, "monotonic", lambda: sum(waits))
    monkeypatch.setattr(driver, "MAX_OUTAGE_SECONDS", 50)
    with pytest.raises(ModelTransportError):
        driver.retry_temporary(lambda: transport_error(429), stage="doc-1:secondary",
                               event_path=tmp_path / "events.jsonl", progress=lambda: 0)
    assert waits == [30, 20]


def test_auth_network_failure_retries_but_invalid_credentials_stop(monkeypatch, tmp_path):
    driver = load_driver(monkeypatch)
    waits = []
    monkeypatch.setattr(driver, "sleep", waits.append)
    monkeypatch.setattr(driver, "monotonic", lambda: sum(waits))
    calls = 0

    def stage():
        nonlocal calls
        calls += 1
        if calls == 1:
            raise AuthTransportError("connection reset")
        return "recovered"

    events = tmp_path / "events.jsonl"
    assert driver.retry_temporary(stage, stage="doc-1:secondary", event_path=events,
                                  progress=lambda: 0) == "recovered"
    assert waits == [30]
    assert json.loads(events.read_text(encoding="utf-8").splitlines()[0])["cause"] == "Google auth transport"

    def invalid_credentials():
        raise RefreshError("invalid grant")

    with pytest.raises(RefreshError):
        driver.retry_temporary(invalid_credentials, stage="doc-1:secondary",
                               event_path=events, progress=lambda: 0)
    assert waits == [30]
