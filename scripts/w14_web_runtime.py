"""Run W-14 React acceptance against real HTTP and an isolated PostgreSQL database."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import socket
import subprocess
import sys
from tempfile import TemporaryDirectory
from threading import Event, Lock, Thread
from time import monotonic, sleep
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src/web/backend"), str(ROOT / "src")]

from dotenv import dotenv_values
from fastapi import Header, HTTPException
from sqlalchemy import text
from sqlalchemy.engine import make_url
import uvicorn

from doc2roadmap.application.phase_b.retrieval import load_learning_graph
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore
from wayfinder.api.app import create_app
from wayfinder.application.build_worker import BuildWorker
from wayfinder.composition import WebServices, compose_account_service, compose_build_service, compose_course_services
from wayfinder.fakes.build import ScriptedBuildRunner
from wayfinder.fakes.mail import FakeMailer
from wayfinder.fakes.media import MemoryMediaStore
from wayfinder.infrastructure.database import create_database_engine, upgrade_database
from wayfinder.infrastructure.fake_build import ManifestFakeBuildRunner
from wayfinder.infrastructure.phase_b_store import PostgresPhaseBStore
from wayfinder.settings import WebSettings


BASE_URL = "http://127.0.0.1:8014"
DATABASE_PREFIX = "wayfinder_w14_react_"
MANIFEST = ROOT / "report/doc1-rebuild-evidence-2026-10-20/development-fixtures.json"
MANIFEST_SHA256 = "5fc819f723f7263fe3d443ec780009a75aae66f2c35db8fe0bc3e3c50464eb84"
SOURCE_DOC = "doc-1"


class WorkerControl:
    """Out-of-band local control for the real BuildWorker used by this browser harness."""

    def __init__(self, worker: BuildWorker):
        self.worker = worker
        self.lock = Lock()
        self.release_gate: Event | None = None
        self.paused_stage: str | None = None
        self.pause_stages: set[str] = set()
        self.mode: str | None = None
        self.thread: Thread | None = None
        self.stopping = Event()
        self.runs = 0
        self.last_exception: str | None = None
        self.last_job_status: str | None = None

    def start(self, mode: str, pause_stages: list[str]) -> None:
        if mode not in {"success", "retryable", "rejected"}:
            raise HTTPException(422, "unsupported test worker mode")
        if not set(pause_stages) <= {"doc_reading", "concepts", "graph", "learning_prep"}:
            raise HTTPException(422, "unsupported test worker pause stage")
        with self.lock:
            if self.thread is not None and self.thread.is_alive():
                raise HTTPException(409, "test worker is already running")
            self.stopping.clear()
            self.mode = mode
            self.pause_stages = set(pause_stages)
            self.paused_stage = None
            self.release_gate = None
            self.last_exception = None
            self.last_job_status = None
            self.runs += 1
            self.thread = Thread(target=self._run, daemon=True, name="w14-react-test-worker")
            self.thread.start()

    def _run(self) -> None:
        try:
            job = self.worker.run_next_job()
            with self.lock:
                self.last_job_status = job.get("status") if job else None
        except Exception as exc:  # Report class only; don't serialize request or provider details.
            with self.lock:
                self.last_exception = type(exc).__name__

    def pause(self, stage: str) -> None:
        with self.lock:
            should_pause = stage in self.pause_stages
            if not should_pause:
                return
            gate = Event()
            self.release_gate = gate
            self.paused_stage = stage
        if not gate.wait(timeout=240):
            with self.lock:
                self.paused_stage = None
                self.release_gate = None
            raise TimeoutError("browser harness did not release the paused fake worker")
        with self.lock:
            if self.release_gate is gate:
                self.paused_stage = None
                self.release_gate = None

    def advance(self) -> None:
        with self.lock:
            gate = self.release_gate
        if gate is None:
            raise HTTPException(409, "test worker is not paused")
        gate.set()

    def state(self) -> dict:
        with self.lock:
            return {
                "running": bool(self.thread and self.thread.is_alive()),
                "pausedStage": self.paused_stage,
                "runs": self.runs,
                "lastException": self.last_exception,
                "lastJobStatus": self.last_job_status,
                "mode": self.mode,
            }

    def stop(self) -> None:
        with self.lock:
            self.stopping.set()
            self.pause_stages.clear()
            gate = self.release_gate
            thread = self.thread
        if gate is not None:
            gate.set()
        if thread is not None:
            thread.join(timeout=260)
            if thread.is_alive():
                raise RuntimeError("W-14 fake worker did not stop")


class ControlledManifestRunner:
    def __init__(self, runner: ManifestFakeBuildRunner, control: WorkerControl):
        self.runner, self.control = runner, control

    def execute(self, file_path, doc_id, *, language="vi", progress=None, cancelled=None, dry_run=False):
        def stop_requested():
            return self.control.stopping.is_set() or (cancelled is not None and cancelled())

        def report(step, data):
            if progress:
                progress(step, data)
            if data.get("status") == "started":
                self.control.pause(step)

        return self.runner.execute(file_path, doc_id, language=language, progress=report,
                                   cancelled=stop_requested, dry_run=dry_run)


class ControlledScriptedRunner:
    def __init__(self, recorder, pipeline_version: str, control: WorkerControl, mode: str):
        code = "loi_mang" if mode == "retryable" else "ban_quet"
        self.runner = ScriptedBuildRunner(
            recorder=recorder,
            pipeline_version=pipeline_version,
            error={"code": code, "message": "synthetic W-14 browser harness result", "stage": "concepts"},
        )
        self.control = control

    def execute(self, file_path, doc_id, *, language="vi", progress=None, cancelled=None, dry_run=False):
        def stop_requested():
            return self.control.stopping.is_set() or (cancelled is not None and cancelled())

        def report(step, data):
            if progress:
                progress(step, data)
            if data.get("status") == "started":
                self.control.pause(step)

        return self.runner.execute(file_path, doc_id, language=language, progress=report,
                                   cancelled=stop_requested, dry_run=dry_run)


def main() -> int:
    local_env = ROOT / "src/web/.env"
    fallback_env = ROOT.parents[1] / "src/web/.env"
    env_path = local_env if local_env.is_file() else fallback_env
    values = dotenv_values(env_path)
    configured = os.environ.get("WAYFINDER_TEST_DATABASE_URL") or values.get("WAYFINDER_TEST_DATABASE_URL")
    if not configured:
        raise RuntimeError("A dedicated WAYFINDER_TEST_DATABASE_URL is required")
    base_url = make_url(configured)
    if base_url.get_backend_name() != "postgresql" or base_url.database != "wayfinder_test":
        raise RuntimeError("W-14 browser runtime accepts only the dedicated wayfinder_test database configuration")
    if MANIFEST_SHA256 != hashlib.sha256(MANIFEST.read_bytes()).hexdigest():
        raise RuntimeError("W-14 fake-build manifest does not match the approved digest")

    admin_engine = create_database_engine(configured).execution_options(isolation_level="AUTOCOMMIT")
    database_name = DATABASE_PREFIX + uuid4().hex
    database_url = base_url.set(database=database_name)
    output = ROOT / "report/w14-react-evidence/final-main-2026-10-22"
    output.mkdir(parents=True, exist_ok=True)
    fixture_names = _write_browser_fixtures(output / "fixtures")
    summary = {
        "baseUrl": BASE_URL,
        "databaseName": database_name,
        "database": "uuid-disposable-postgresql",
        "migrationHead": None,
        "media": "MemoryMediaStore",
        "mailer": "FakeMailer",
        "runner": "ManifestFakeBuildRunner plus deterministic scripted retry/reject",
        "modelCalls": 0,
        "modelCostUsd": 0,
        "fixture": {"sourceDoc": SOURCE_DOC, "manifestSha256Verified": True},
        "fixtureNames": fixture_names,
        "browserExitCode": None,
        "temporaryDatabaseRemoved": False,
    }
    created = False
    engine = audit_engine = phase_b = None
    server = server_thread = None
    listener = None
    artifact_temp = None
    control = None
    try:
        _forbid_live_providers()
        with admin_engine.connect() as connection:
            connection.execute(text(f'CREATE DATABASE "{database_name}"'))
            created = True
        upgrade_database(database_url)
        engine = create_database_engine(database_url)
        audit_engine = create_database_engine(database_url)

        artifact_temp = TemporaryDirectory(prefix="w14-react-artifacts-")
        artifact_root = Path(artifact_temp.name) / "artifacts"
        settings = WebSettings(
            _env_file=None,
            database_url=database_url.render_as_string(hide_password=False),
            frontend_dist=ROOT / "src/web/frontend/dist",
            artifact_root=artifact_root,
            allowed_origins=[BASE_URL],
            public_base_url=BASE_URL,
            env="dev",
            mailer="console",
            build_monthly_max=None,
            system_daily_build_max_usd=None,
        )
        phase_b = PostgresPhaseBStore(engine, lock_pool_size=settings.phase_b_lock_pool_size)
        mailer = FakeMailer()
        media = MemoryMediaStore()
        accounts = compose_account_service(settings, engine, mailer=mailer)
        courses, learning = compose_course_services(settings, engine, phase_b)
        builds = compose_build_service(settings, engine, media=media)
        courses.build_service = builds
        graph_store = JsonArtifactStore(artifact_root)

        def graph_loader(doc_id: str, version: int | None):
            return load_learning_graph(graph_store, doc_id, version)

        control: WorkerControl

        def runner_factory(recorder):
            mode = control.mode
            if mode in {"retryable", "rejected"}:
                return ControlledScriptedRunner(recorder, builds.pipeline_version, control, mode)
            return ControlledManifestRunner(
                ManifestFakeBuildRunner(
                    ROOT, artifact_root, SOURCE_DOC,
                    manifest=MANIFEST, manifest_sha256=MANIFEST_SHA256,
                    recorder=recorder, pipeline_version=builds.pipeline_version,
                ),
                control,
            )

        worker = BuildWorker(builds, runner_factory=runner_factory, graph_loader=graph_loader,
                             mailer=mailer, worker_id=f"w14-react-{uuid4().hex}")
        control = WorkerControl(worker)
        services = WebServices(
            health_check=lambda: "ok", close=lambda: None, accounts=accounts,
            phase_b_store=phase_b, courses=courses, learning=learning, builds=builds,
        )
        app = create_app(settings, services)
        control_token = secrets.token_urlsafe(32)

        def require_control(value: str | None) -> None:
            if not value or not hmac.compare_digest(value, control_token):
                raise HTTPException(404, "not found")

        @app.post("/__test__/worker/start")
        def start_worker(payload: dict, x_w14_control: str | None = Header(default=None)):
            require_control(x_w14_control)
            control.start(payload.get("mode"), payload.get("pause_stages", []))
            return {"started": True}

        @app.post("/__test__/worker/advance")
        def advance_worker(x_w14_control: str | None = Header(default=None)):
            require_control(x_w14_control)
            control.advance()
            return {"advanced": True}

        @app.get("/__test__/worker/state")
        def worker_state(x_w14_control: str | None = Header(default=None)):
            require_control(x_w14_control)
            return control.state()

        # The SPA fallback is registered by create_app before these harness-only routes.
        # Put the authenticated, random-token-gated controls ahead of that fallback so
        # they resolve as JSON instead of returning index.html.
        test_routes = [route for route in app.router.routes
                       if getattr(route, "path", "").startswith("/__test__/worker/")]
        app.router.routes[:] = [route for route in app.router.routes if route not in test_routes]
        spa_index = next((index for index, route in enumerate(app.router.routes)
                          if getattr(route, "path", None) == "/{path:path}"), len(app.router.routes))
        app.router.routes[spa_index:spa_index] = test_routes

        summary["migrationHead"] = _migration_head(engine)
        if summary["migrationHead"] != "w14_0006":
            raise RuntimeError(f"Unexpected W-14 migration head: {summary['migrationHead']}")
        _write_summary(output, summary)

        listener = socket.socket()
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(("127.0.0.1", 8014))
        listener.listen(128)
        listener.setblocking(False)
        server = uvicorn.Server(uvicorn.Config(app, log_config=None, access_log=False, log_level="warning"))
        server_thread = Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
        server_thread.start()
        deadline = monotonic() + 20
        while not server.started and server_thread.is_alive() and monotonic() < deadline:
            sleep(0.05)
        if not server.started:
            raise RuntimeError("W-14 browser runtime failed to start on 127.0.0.1:8014")

        environment = dict(os.environ, W14_BASE_URL=BASE_URL,
                           W14_RUNTIME_JSON=str(output / "runtime.json"),
                           W14_CONTROL_TOKEN=control_token)
        checker = ROOT / "scripts/w14_web_check.cjs"
        if not checker.is_file():
            raise RuntimeError("scripts/w14_web_check.cjs is not available")
        result = subprocess.run(["node", str(checker)], cwd=ROOT, env=environment)
        summary["browserExitCode"] = result.returncode
        if result.returncode == 0:
            summary.update(_database_evidence(audit_engine, output))
            summary["localIntegrationEvidence"] = True
        return result.returncode
    finally:
        original_error = sys.exc_info()[1]
        cleanup_errors: list[str] = []

        def attempt_cleanup(action) -> None:
            try:
                action()
            except Exception as exc:
                cleanup_errors.append(type(exc).__name__)

        if control is not None:
            attempt_cleanup(control.stop)
        if server is not None:
            server.should_exit = True
        if server_thread is not None:
            server_thread.join(20)
            if server_thread.is_alive():
                cleanup_errors.append("ServerShutdownTimeout")
        if listener is not None:
            attempt_cleanup(listener.close)
        for service in (builds if "builds" in locals() else None,
                        courses if "courses" in locals() else None,
                        accounts if "accounts" in locals() else None):
            close = getattr(service, "close", None)
            if close:
                attempt_cleanup(close)
        if phase_b is not None:
            attempt_cleanup(phase_b.close)
        if engine is not None:
            attempt_cleanup(engine.dispose)
        if audit_engine is not None:
            attempt_cleanup(audit_engine.dispose)
        if artifact_temp is not None:
            attempt_cleanup(artifact_temp.cleanup)
        if created:
            if not re.fullmatch(r"wayfinder_w14_react_[0-9a-f]{32}", database_name):
                cleanup_errors.append("UnexpectedDatabaseName")
            else:
                def drop_database() -> None:
                    with admin_engine.connect() as connection:
                        connection.execute(text(f'DROP DATABASE "{database_name}" WITH (FORCE)'))
                    summary["temporaryDatabaseRemoved"] = True
                attempt_cleanup(drop_database)
        attempt_cleanup(admin_engine.dispose)
        if cleanup_errors:
            summary["cleanupErrorTypes"] = cleanup_errors
        attempt_cleanup(lambda: _write_summary(output, summary))
        if cleanup_errors and original_error is None:
            raise RuntimeError(f"W-14 runtime cleanup failed: {', '.join(cleanup_errors)}")


def _forbid_live_providers() -> None:
    def forbidden(*_args, **_kwargs):
        raise AssertionError("W-14 browser runtime attempted an external provider call")

    from doc2roadmap.infrastructure.embedding import gemini as embedding
    from doc2roadmap.infrastructure.google_auth import VertexCredentials
    from doc2roadmap.infrastructure.llm import gemini as llm
    import google.auth
    from wayfinder import composition
    from wayfinder.infrastructure import mail, media

    llm.urlopen = forbidden
    embedding.urlopen = forbidden
    VertexCredentials.headers = forbidden
    google.auth.default = forbidden
    composition.google_auth_default = forbidden
    mail.smtplib.SMTP = forbidden
    mail.smtplib.SMTP_SSL = forbidden
    media.CloudinaryMediaStore.__init__ = forbidden


def _migration_head(engine) -> str | None:
    with engine.connect() as connection:
        return connection.scalar(text("SELECT version_num FROM alembic_version"))


def _database_evidence(engine, output: Path) -> dict:
    state_path = output / "browser-state.json"
    if not state_path.is_file():
        raise AssertionError("browser-state.json is required for independent PostgreSQL verification")
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if any("token" in key.lower() or "password" in key.lower() or "cookie" in key.lower()
           for key in state):
        raise AssertionError("browser-state.json must not contain credentials")
    account_id = state.get("accountId")
    course_ids = state.get("courseIds", [])
    build_ids = state.get("buildIds", [])
    if not account_id or len(course_ids) < 1 or not build_ids:
        raise AssertionError("browser did not record the real actor, course, and build IDs")
    with engine.connect() as connection:
        account = connection.execute(text("SELECT id,role,status FROM account WHERE id=:id"),
                                     {"id": account_id}).mappings().first()
        if account is None or account["role"] != "user" or account["status"] != "active":
            raise AssertionError("browser account is not persisted as an active user in PostgreSQL")
        course_rows = connection.execute(text(
            "SELECT id,owner_id,title,status,build_id FROM course "
            "WHERE id::text = ANY(CAST(:ids AS text[])) ORDER BY id"),
            {"ids": course_ids}).mappings().all()
        if len(course_rows) != len(set(course_ids)):
            raise AssertionError("browser-owned courses are missing from PostgreSQL")
        if any(str(row["owner_id"]) != account_id for row in course_rows):
            raise AssertionError("browser course ownership differs from the authenticated actor")
        build_rows = connection.execute(text(
            "SELECT id,status,error_code,requested_by,counts_quota FROM build "
            "WHERE id::text = ANY(CAST(:ids AS text[])) ORDER BY id"),
            {"ids": build_ids}).mappings().all()
        if len(build_rows) != len(set(build_ids)):
            raise AssertionError("browser builds are missing from PostgreSQL")
        reuse = state.get("reuse")
        if not reuse or reuse.get("sameBuild") is not True:
            raise AssertionError("browser did not report the explicit same-file reuse scenario")
        courses_by_id = {str(row["id"]): row for row in course_rows}
        original = courses_by_id.get(reuse.get("originalCourseId"))
        reused = courses_by_id.get(reuse.get("reusedCourseId"))
        if (original is None or reused is None or original["id"] == reused["id"]
                or str(original["build_id"]) != reuse.get("buildId")
                or str(reused["build_id"]) != reuse.get("buildId")
                or original["title"] != reuse.get("originalTitle")
                or reused["title"] != reuse.get("reusedTitle")):
            raise AssertionError("independent PostgreSQL rows do not confirm two titled courses share one build")
        usage = connection.execute(text(
            "SELECT count(*) AS rows, coalesce(sum(cost_usd),0) AS cost_usd "
            "FROM usage_ledger WHERE purpose='build' "
            "AND extra->>'build_id' = ANY(CAST(:ids AS text[]))"),
            {"ids": build_ids}).mappings().one()
        if usage["rows"] < 1 or float(usage["cost_usd"]) <= 0:
            raise AssertionError("fake worker did not persist nonzero synthetic build usage")
        return {
            "accountRole": account["role"],
            "ownedCourseCount": len(course_rows),
            "courseStatuses": sorted(row["status"] for row in course_rows),
            "buildStatuses": sorted(row["status"] for row in build_rows),
            "allBuildRowsPersisted": True,
            "sameFileReuseVerifiedByIndependentPostgres": True,
            "syntheticBuildUsageRows": usage["rows"],
            "syntheticBuildUsageUsd": float(usage["cost_usd"]),
            "verifiedByIndependentPostgresConnection": True,
        }


def _write_summary(output: Path, summary: dict) -> None:
    (output / "runtime.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_browser_fixtures(directory: Path) -> dict[str, str]:
    directory.mkdir(parents=True, exist_ok=True)
    names = {
        "success": "w14-success.pdf",
        "reuse": "w14-reuse.pdf",
        "cancel": "w14-cancel.docx",
        "retry": "w14-retry.pdf",
        "reject": "w14-reject.pdf",
    }
    source = ROOT / "doc-1.pdf"
    if not source.is_file():
        raise RuntimeError("The approved doc-1 PDF fixture is missing")
    for key, filename in names.items():
        path = directory / filename
        if key in {"success", "reuse"}:
            path.write_bytes(source.read_bytes())
        elif filename.endswith(".pdf"):
            path.write_bytes(_tiny_pdf(f"WayFinder W14 {key}"))
        else:
            _tiny_docx(path, f"WayFinder W14 {key}")
    return names


def _tiny_pdf(label: str) -> bytes:
    text = label.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    data = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, body in enumerate(objects, 1):
        offsets.append(len(data))
        data.extend(f"{number} 0 obj\n".encode("ascii"))
        data.extend(body + b"\nendobj\n")
    xref = len(data)
    data.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("ascii"))
    for offset in offsets[1:]:
        data.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    data.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("ascii"))
    return bytes(data)


def _tiny_docx(path: Path, title: str) -> None:
    escaped = (title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>""")
        archive.writestr("_rels/.rels", """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>""")
        archive.writestr("word/document.xml", f"""<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>
<w:p><w:r><w:t>{escaped}</w:t></w:r></w:p><w:sectPr/></w:body></w:document>""")


if __name__ == "__main__":
    raise SystemExit(main())
