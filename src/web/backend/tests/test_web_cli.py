import subprocess
import os
import sys
import getpass
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


def test_create_admin_reads_password_hidden_and_closes_database(monkeypatch, capsys):
    from wayfinder import composition

    monkeypatch.setenv("WAYFINDER_DATABASE_URL", "postgresql+psycopg://user:secret@localhost/wayfinder")
    monkeypatch.setattr(getpass, "getpass", lambda prompt: "hidden password")
    health_state = {"closed": False}

    class Health:
        engine = object()

        def __init__(self, url):
            assert "secret" in url

        def close(self):
            health_state["closed"] = True

    calls = []

    class Service:
        def create_admin(self, email, password):
            calls.append((email, password))
            return object()

    monkeypatch.setattr(cli, "DatabaseHealth", Health)
    monkeypatch.setattr(composition, "compose_account_service", lambda settings, engine: Service(), raising=False)

    assert cli.main(["create-admin", "--email", "admin@example.vn"]) == 0
    captured = capsys.readouterr()
    assert calls == [("admin@example.vn", "hidden password")]
    assert "hidden password" not in captured.out + captured.err
    assert health_state["closed"]


def test_create_admin_does_not_accept_password_as_command_argument(capsys):
    with pytest.raises(SystemExit) as error:
        cli.main(["create-admin", "--email", "admin@example.vn", "--password", "must-not-appear"])

    assert error.value.code == 2
    assert "--password" in capsys.readouterr().err


def test_create_admin_reports_auth_conflict_without_database_details(monkeypatch, capsys):
    from wayfinder import composition
    from wayfinder.application.accounts import AuthError

    monkeypatch.setenv("WAYFINDER_DATABASE_URL", "postgresql+psycopg://user:secret@localhost/wayfinder")
    monkeypatch.setattr(getpass, "getpass", lambda prompt: "hidden password")

    class Health:
        engine = object()

        def __init__(self, url):
            pass

        def close(self):
            pass

    class Service:
        def create_admin(self, email, password):
            raise AuthError("conflict", "Tài khoản đã tồn tại.")

    monkeypatch.setattr(cli, "DatabaseHealth", Health)
    monkeypatch.setattr(composition, "compose_account_service", lambda settings, engine: Service(), raising=False)

    assert cli.main(["create-admin", "--email", "admin@example.vn"]) == 1
    captured = capsys.readouterr()
    assert "Tài khoản đã tồn tại." in captured.err
    assert "secret" not in captured.out + captured.err
    assert "hidden password" not in captured.out + captured.err


def test_create_admin_sanitizes_database_failure_and_closes_engine(monkeypatch, capsys):
    from sqlalchemy.exc import SQLAlchemyError
    from wayfinder import composition

    monkeypatch.setenv("WAYFINDER_DATABASE_URL", "postgresql+psycopg://user:secret@localhost/wayfinder")
    engine_state = {"closed": False}

    class Health:
        engine = object()

        def __init__(self, url):
            pass

        def close(self):
            engine_state["closed"] = True

    def failed_composition(settings, engine):
        raise SQLAlchemyError("dsn secret detail")

    monkeypatch.setattr(cli, "DatabaseHealth", Health)
    monkeypatch.setattr(composition, "compose_account_service", failed_composition, raising=False)

    assert cli.main(["create-admin", "--email", "admin@example.vn"]) == 1
    captured = capsys.readouterr()
    assert "dsn secret detail" not in captured.out + captured.err
    assert "secret" not in captured.out + captured.err
    assert engine_state["closed"]


@pytest.mark.postgres
def test_create_admin_bootstraps_real_postgres_without_vertex(monkeypatch, capsys, postgres_database_url):
    from uuid import uuid4
    from sqlalchemy import text
    from wayfinder.infrastructure.database import create_database_engine

    email = "bootstrap-" + uuid4().hex + "@example.vn"
    password = "Mật khẩu bootstrap riêng tư!"
    monkeypatch.setenv("WAYFINDER_DATABASE_URL", postgres_database_url.render_as_string(hide_password=False))
    monkeypatch.setenv("DOC2ROADMAP_LLM_TRANSPORT", "developer_api")
    monkeypatch.setattr(cli.getpass, "getpass", lambda _prompt: password)
    assert cli.main(["create-admin", "--email", email]) == 0
    output = capsys.readouterr()
    hidden = password not in output.out + output.err
    assert hidden is True
    engine = create_database_engine(postgres_database_url)
    try:
        with engine.connect() as connection:
            account = connection.execute(text("SELECT id, role, email_verified_at, password_hash FROM account WHERE email_normalized=:email"), {"email": email}).mappings().one()
            assert account["role"] == "admin"
            assert account["email_verified_at"] is not None
            assert account["password_hash"].startswith("$argon2id$")
            assert connection.scalar(text("SELECT count(*) FROM auth_session WHERE account_id=:id"), {"id": account["id"]}) == 0
    finally:
        engine.dispose()
