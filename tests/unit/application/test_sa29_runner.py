import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace as NS
from urllib.request import Request

import pytest


RUNNER_PATH = Path(__file__).resolve().parents[3] / "scripts" / "phase-b" / "sa29_acceptance.py"
spec = importlib.util.spec_from_file_location("sa29_acceptance_runner", RUNNER_PATH)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def test_preflight_is_read_only_and_bounds_160_requests_under_cap(monkeypatch, tmp_path):
    counts = {"doc-1": 33, "nhap-mon-ml": 15, "naive-bayes": 5,
              "doc-6": 2, "xstk-ch3-1": 14, "doc-4": 91}

    class FakeArtifacts:
        def load_graph(self, doc_id, version):
            count = counts[doc_id]
            payload = {"stage": "stages", "modules": [{"module_id": f"m{i}",
                                                          "description_source": "llm"}
                                                         for i in range(count)]}
            return NS(version=version, payload=payload)

    class FakeNameModules:
        def __init__(self, *args, **kwargs):
            pass

        def plan(self, doc_id, *, upstream):
            return NS(calls_estimate=len(upstream.payload["modules"]))

        def _prepare(self, doc_id, upstream):
            rows = [(None, None, {"module": index}) for index in range(len(upstream.payload["modules"]))]
            return NS(result=NS(chunks=[])), rows

        def _prompt(self):
            return "fake prompt"

    monkeypatch.setattr(runner, "JsonArtifactStore", lambda _path: FakeArtifacts())
    monkeypatch.setattr(runner, "NameModulesB", FakeNameModules)
    monkeypatch.setattr(runner, "STORE_PATH", tmp_path / "ledger.json")
    monkeypatch.setattr(runner, "RECORD_DIR", tmp_path / "recordings")
    monkeypatch.setattr(runner, "RESULT_PATH", tmp_path / "result.json")
    monkeypatch.setattr(runner, "Settings", lambda: NS(artifact_dir=tmp_path))
    before = sorted(path.name for path in tmp_path.iterdir())
    monkeypatch.setattr(runner.phase_b_transport, "urlopen",
                        lambda *args, **kwargs: pytest.fail("preflight called transport"))

    result = runner.preflight()

    assert result["mode"] == "preflight_no_calls_no_writes"
    assert result["planned_calls"] == 160
    assert result["request_bytes_total"] == sum(doc["request_bytes_total"] for doc in result["docs"])
    assert result["estimated_usd_upper"] <= runner.CAP_USD
    assert not runner.STORE_PATH.exists()
    assert not runner.RECORD_DIR.exists()
    assert not runner.RESULT_PATH.exists()
    assert sorted(path.name for path in tmp_path.iterdir()) == before


def test_installed_sa29_budget_gate_blocks_before_second_transport_attempt(monkeypatch):
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
    assert gate.attempts == 1
    assert gate.bytes == len(request.data)
    assert gate.reserved == one_attempt
