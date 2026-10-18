import importlib.util
from pathlib import Path

import pytest


RUNNER_PATH = Path(__file__).resolve().parents[3] / "scripts" / "phase-b" / "run_sa27_quiz_acceptance.py"
spec = importlib.util.spec_from_file_location("sa27_quiz_acceptance_runner", RUNNER_PATH)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def test_paid_run_refuses_existing_result_before_runtime(monkeypatch, tmp_path):
    result_path = tmp_path / "paid-result.json"
    plan_path = tmp_path / "plan.json"
    original = b"completed paid result"
    result_path.write_bytes(original)
    plan_path.write_text('{"results": [], "combined_estimated_usd": 0}', encoding="utf-8")
    monkeypatch.setattr(runner, "RESULT_PATH", result_path)
    monkeypatch.setattr(runner, "PLAN_PATH", plan_path)
    monkeypatch.setattr(runner, "PhaseBRuntime", lambda **kwargs: pytest.fail("runtime must not start"))
    monkeypatch.setattr("sys.argv", [str(RUNNER_PATH), "--allow-spend"])

    with pytest.raises(SystemExit, match="replay_sa27_quiz.py"):
        runner.main()

    assert result_path.read_bytes() == original


def test_dry_run_is_still_allowed_when_paid_result_exists(monkeypatch, tmp_path, capsys):
    result_path = tmp_path / "paid-result.json"
    original = b"completed paid result"
    result_path.write_bytes(original)
    plan_path = tmp_path / "plan.json"
    plan_path.write_text('{"results": [], "combined_estimated_usd": 0}', encoding="utf-8")
    monkeypatch.setattr(runner, "RESULT_PATH", result_path)
    monkeypatch.setattr(runner, "PLAN_PATH", plan_path)
    monkeypatch.setattr(runner, "PhaseBRuntime", lambda **kwargs: pytest.fail("dry run must not start runtime"))
    monkeypatch.setattr("sys.argv", [str(RUNNER_PATH)])

    runner.main()

    assert result_path.read_bytes() == original
    assert result_path.with_name("phaseb-sa27-live-dry-run-v2.json").exists()
    assert '"network_calls": 0' in capsys.readouterr().out
