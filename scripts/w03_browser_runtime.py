"""Run browser acceptance with real auth/Argon2/PostgreSQL and an in-memory Mailer.

All fixtures, test-only mail endpoint and database belong to this isolated process.
No SMTP, Cloudinary, ADC or model calls are needed.
"""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from threading import Thread
import time
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src/web/backend"), str(ROOT / "src")]

from dotenv import dotenv_values
from sqlalchemy import text
from sqlalchemy.engine import make_url
import uvicorn

from wayfinder.api.app import create_app
from wayfinder.composition import WebServices, compose_account_service
from wayfinder.fakes.mail import FakeMailer
from wayfinder.infrastructure.database import create_database_engine, upgrade_database
from wayfinder.settings import WebSettings
from wayfinder.testing import FakeClock


def main() -> int:
    values = dotenv_values(ROOT / "src/web/.env")
    configured = os.environ.get("WAYFINDER_TEST_DATABASE_URL") or values.get("WAYFINDER_TEST_DATABASE_URL")
    if not configured:
        raise RuntimeError("PostgreSQL db-test configuration is required")
    admin = create_database_engine(configured).execution_options(isolation_level="AUTOCOMMIT")
    name = "wayfinder_w03_" + uuid4().hex
    url = make_url(configured).set(database=name)
    output = ROOT / "report/w03-evidence"
    output.mkdir(parents=True, exist_ok=True)
    created, server, thread, engine = False, None, None, None
    summary = {"realPostgres": True, "realArgon2": True, "mailer": "fake", "modelCalls": 0, "modelCostUsd": 0}
    try:
        with admin.connect() as connection:
            connection.execute(text(f'CREATE DATABASE "{name}"'))
            created = True
        upgrade_database(url)
        engine = create_database_engine(url)
        settings = WebSettings(_env_file=None, public_base_url="http://127.0.0.1:8003",
                               allowed_origins=["http://127.0.0.1:8003"],
                               frontend_dist=ROOT / "src/web/frontend/dist", mailer="console")
        mailer, clock = FakeMailer(), FakeClock()
        accounts = compose_account_service(settings, engine, mailer=mailer)
        accounts.clock = clock
        password = "Riêng tư cho kiểm thử W03!"

        def register(label):
            return accounts.register(label + "@example.vn", password, "Người học", ip=None, user_agent=None)

        def token():
            return re.search(r"[#?]token=([A-Za-z0-9_-]+)", mailer.messages[-1]["body"]).group(1)

        fixtures = {}
        register("expired-verify")
        fixtures["expiredVerify"] = token()
        clock.advance(24 * 3600)
        register("used-verify")
        fixtures["usedVerify"] = token()
        accounts.verify_email(fixtures["usedVerify"])
        register("expired-reset")
        accounts.request_password_reset("expired-reset@example.vn")
        fixtures["expiredReset"] = token()
        clock.advance(3600)
        register("used-reset")
        accounts.request_password_reset("used-reset@example.vn")
        fixtures["usedReset"] = token()
        accounts.reset_password(fixtures["usedReset"], "Mật khẩu đã được thay W03!")
        register("preview")
        fixtures["previewVerify"] = token()
        accounts.request_password_reset("preview@example.vn")
        fixtures["previewReset"] = token()

        services = WebServices(health_check=lambda: "ok", close=engine.dispose, accounts=accounts)
        app = create_app(settings, services)

        @app.get("/__test__/mail", include_in_schema=False)
        def test_mail(email: str):
            return [message for message in mailer.messages if message["to"].lower() == email.lower()]

        @app.get("/__test__/fixtures", include_in_schema=False)
        def test_fixtures():
            return fixtures

        # Put the test-only routes before the SPA catch-all; they are never installed in production.
        test_routes = [route for route in app.router.routes if getattr(route, "path", "").startswith("/__test__/")]
        app.router.routes[:] = test_routes + [route for route in app.router.routes if route not in test_routes]

        # These routes exist only on the disposable loopback server in this script.
        server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=8003,
                                               log_level="warning", access_log=False))
        thread = Thread(target=server.run, daemon=True)
        thread.start()
        deadline = time.monotonic() + 15
        while not server.started and thread.is_alive() and time.monotonic() < deadline:
            time.sleep(0.05)
        if not server.started:
            raise RuntimeError("Isolated W-03 server did not start")
        environment = dict(os.environ, W03_BASE_URL=settings.public_base_url)
        result = subprocess.run(["node", str(ROOT / "scripts/w03_browser_check.cjs")], cwd=ROOT, env=environment)
        inspector = ROOT.parents[1] / ".agents/skills/design-taste-frontend/scripts/inspect.mjs"
        inspect_code = 0
        if result.returncode == 0 and inspector.is_file():
            profile_root = (ROOT / "tmp/w03-taste-profiles").resolve()
            if not profile_root.is_relative_to(ROOT.resolve()):
                raise RuntimeError("Unexpected taste inspector profile directory")
            profile_root.mkdir(parents=True, exist_ok=True)
            inspector_env = dict(environment, TASTE_SKILL_TMP=str(profile_root))
            with (output / "taste-inspect.log").open("w", encoding="utf-8") as log:
                inspected = subprocess.run(["node", str(inspector), "--app", settings.public_base_url + "/quen-mat-khau",
                                            "--widths", "1280,768,390", "--out", str(output / "taste-inspect")],
                                           cwd=ROOT, env=inspector_env, stdout=log, stderr=subprocess.STDOUT)
            inspect_code = inspected.returncode
            summary["tasteInspectorExitCode"] = inspect_code

        with engine.connect() as connection:
            summary["migrationHead"] = connection.scalar(text("SELECT version_num FROM alembic_version"))
            summary["verifiedAccounts"] = connection.scalar(text("SELECT count(*) FROM account WHERE email_verified_at IS NOT NULL"))
            summary["consumedTokens"] = connection.scalar(text("SELECT count(*) FROM email_token WHERE used_at IS NOT NULL"))
            tokens = list(connection.scalars(text("SELECT token_hash FROM email_token")))
            summary["onlySha256TokenHashes"] = bool(tokens) and all(len(value) == 32 for value in tokens)
        if result.returncode == 0:
            assert summary["migrationHead"] == "w03_0004"
            assert summary["onlySha256TokenHashes"] is True
            with engine.connect() as connection:
                assert connection.scalar(text("SELECT email_verified_at IS NOT NULL FROM account WHERE email_normalized='w03-browser@example.vn'")) is True
        summary["browserExitCode"] = result.returncode
        return result.returncode or inspect_code
    finally:
        if server is not None:
            server.should_exit = True
        if thread is not None:
            thread.join(15)
            if thread.is_alive():
                raise RuntimeError("Isolated W-03 server did not stop")
        if engine is not None:
            engine.dispose()
        if created:
            if not re.fullmatch(r"wayfinder_w03_[0-9a-f]{32}", name):
                raise RuntimeError("Refusing to drop an unexpected database")
            with admin.connect() as connection:
                connection.execute(text(f'DROP DATABASE "{name}" WITH (FORCE)'))
            summary["temporaryDatabaseRemoved"] = True
        admin.dispose()
        (output / "isolated-runtime.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
