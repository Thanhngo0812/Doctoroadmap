import subprocess
import os
import sys
import pytest

from wayfinder import cli


def test_check_refuses_missing_test_database(monkeypatch, capsys):
    monkeypatch.delenv("WAYFINDER_TEST_DATABASE_URL", raising=False)
    called = []
    monkeypatch.setattr(subprocess, "call", lambda args: called.append(args))
    assert cli.main(["check"]) == 2
    assert "WAYFINDER_TEST_DATABASE_URL" in capsys.readouterr().err
    assert called == []


def test_check_refuses_unreachable_test_database(monkeypatch, capsys):
    monkeypatch.setenv("WAYFINDER_TEST_DATABASE_URL", "postgresql+psycopg://unused:unused@127.0.0.1:1/unused")
    assert cli.main(["check"]) == 1
    assert "PostgreSQL" in capsys.readouterr().err


def test_check_invokes_pytest_with_mandatory_postgres(monkeypatch):
    monkeypatch.setenv("WAYFINDER_TEST_DATABASE_URL", "postgresql+psycopg://unused:unused@localhost/test")
    monkeypatch.setenv("DOC2ROADMAP_LLM_TRANSPORT", "vertex")
    monkeypatch.setenv("DOC2ROADMAP_GEMINI_API_KEY", "runtime-only-fake-secret")

    class AvailableDatabase:
        def __init__(self, url):
            pass

        def __call__(self):
            return "ok"

        def close(self):
            pass

    monkeypatch.setattr(cli, "DatabaseHealth", AvailableDatabase)
    called = []
    captured_environment = {}

    def run_tests(args, env=None):
        called.append(args)
        captured_environment.update(os.environ if env is None else env)
        return 7

    monkeypatch.setattr(subprocess, "call", run_tests)
    assert cli.main(["check"]) == 7
    assert called[0][1:] == ["-m", "pytest", "--require-postgres"]
    if any(key.startswith("DOC2ROADMAP_") for key in captured_environment):
        pytest.fail("Runtime model configuration must not contaminate isolated core tests", pytrace=False)
    assert captured_environment["WAYFINDER_TEST_DATABASE_URL"] == "postgresql+psycopg://unused:unused@localhost/test"


def test_worker_is_explicit_about_w14_scaffold(capsys):
    assert cli.main(["worker"]) == 0
    assert "W-14" in capsys.readouterr().out


def test_cli_prints_vietnamese_with_legacy_windows_output_encoding():
    environment = {**os.environ, "PYTHONIOENCODING": "cp1252"}
    result = subprocess.run(
        [sys.executable, "-m", "wayfinder.cli", "worker"],
        env=environment, capture_output=True,
    )
    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    assert "sẵn sàng" in result.stdout.decode("utf-8")
