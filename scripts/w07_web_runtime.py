"""Run the W-07 browser check against an isolated PostgreSQL database."""
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
from threading import Thread
from time import monotonic, sleep
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src/web/backend"), str(ROOT / "src")]

from dotenv import dotenv_values
from sqlalchemy import text
from sqlalchemy.engine import make_url
import uvicorn

from doc2roadmap.application.phase_b.retrieval import load_learning_graph
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore
from wayfinder.api.app import create_app
from wayfinder.application.seed_samples import SampleSeeder
from wayfinder.composition import WebServices, compose_account_service, compose_course_services
from wayfinder.domain.auth import Actor
from wayfinder.fakes.mail import FakeMailer
from wayfinder.fakes.media import MemoryMediaStore
from wayfinder.infrastructure.database import create_database_engine, upgrade_database
from wayfinder.infrastructure.phase_b_store import PostgresPhaseBStore
from wayfinder.settings import WebSettings


BASE_URL = "http://127.0.0.1:8007"
DATABASE_PREFIX = "wayfinder_w07_"


def main() -> int:
    local_env = ROOT / "src/web/.env"
    shared_root = ROOT.parents[1]
    env_path = local_env if local_env.is_file() else shared_root / "src/web/.env"
    values = dotenv_values(env_path)
    configured = os.environ.get("WAYFINDER_TEST_DATABASE_URL") or values.get("WAYFINDER_TEST_DATABASE_URL")
    if not configured:
        raise RuntimeError("PostgreSQL test database configuration is required")
    base_url = make_url(configured)
    if base_url.get_backend_name() != "postgresql" or base_url.database != "wayfinder_test":
        raise RuntimeError("W-07 runtime requires the dedicated wayfinder_test database configuration")

    _verify_doc1_fixture()
    admin = create_database_engine(configured).execution_options(isolation_level="AUTOCOMMIT")
    database_name = DATABASE_PREFIX + uuid4().hex
    database_url = base_url.set(database=database_name)
    output = ROOT / "report/w07-evidence"
    output.mkdir(parents=True, exist_ok=True)
    summary = {
        "baseUrl": BASE_URL,
        "database": "disposable-postgresql",
        "realArgon2": True,
        "phaseBStore": "postgresql",
        "media": "memory-only",
        "mailer": "fake",
        "modelCalls": 0,
        "modelCostUsd": 0,
        "fixture": {"docId": "doc-1", "expectedGraphVersion": 8, "sourceSha256Verified": True},
    }
    created = False
    engine = audit_engine = phase_b = None
    server = thread = None
    listener = None
    try:
        _forbid_live_providers()
        with admin.connect() as connection:
            connection.execute(text(f'CREATE DATABASE "{database_name}"'))
            created = True
        upgrade_database(database_url)
        engine = create_database_engine(database_url)
        audit_engine = create_database_engine(database_url)
        settings = WebSettings(
            _env_file=None,
            database_url=database_url.render_as_string(hide_password=False),
            frontend_dist=ROOT / "src/web/frontend/dist",
            artifact_root=ROOT / "artifacts",
            allowed_origins=[BASE_URL],
            public_base_url=BASE_URL,
            env="dev",
            mailer="console",
        )
        mailer = FakeMailer()
        accounts = compose_account_service(settings, engine, mailer=mailer)
        fixture_admin = accounts.create_admin(
            "w07-seed-admin@example.invalid", "W07 disposable fixture admin passphrase!", "W07 Fixture Admin"
        )
        fixture_actor = Actor(fixture_admin.id, "admin", True, "active")
        phase_b = PostgresPhaseBStore(engine, lock_pool_size=settings.phase_b_lock_pool_size)
        graph_store = JsonArtifactStore(settings.artifact_root)

        def graph_loader(doc_id: str, version: int | None):
            return load_learning_graph(graph_store, doc_id, version)

        courses, learning = compose_course_services(settings, engine, phase_b, graph_loader=graph_loader)
        media = MemoryMediaStore()
        seeded = SampleSeeder(
            courses, learning, media, source_root=ROOT, folder="w07-browser/fake-media"
        ).execute(fixture_actor, doc_ids=["doc-1"])
        if len(seeded) != 1 or seeded[0].doc_id != "doc-1" or seeded[0].published_graph_version != 8:
            raise RuntimeError("W-07 sample fixture is not doc-1 graph version 8")
        graph = graph_loader("doc-1", 8)
        private_course = courses.create_course(
            fixture_actor,
            doc_id="doc-1",
            title="Private W-07 outsider fixture",
            description="Owned by the disposable fixture administrator.",
            graph_version=8,
            module_count=len(graph.modules),
        )

        services = WebServices(
            health_check=lambda: "ok",
            close=lambda: None,
            accounts=accounts,
            phase_b_store=phase_b,
            courses=courses,
            learning=learning,
        )
        app = create_app(settings, services)
        summary["fixtureState"] = {
            "courseId": seeded[0].id,
            "privateCourseId": private_course.id,
            "docId": seeded[0].doc_id,
            "graphVersion": seeded[0].published_graph_version,
            "moduleCount": len(graph.modules),
            "learnableNodeCount": len(graph.learnable_nodes),
            "mediaUploads": len(media.files),
            "fixtureAdminId": fixture_admin.id,
        }
        summary["migrationHead"] = _read_migration_head(engine)
        if summary["migrationHead"] != "w06_0005":
            raise RuntimeError("Disposable W-07 database did not reach the W-06 migration head")
        _write_summary(output, summary)

        listener = socket.socket()
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(("127.0.0.1", 8007))
        listener.listen(128)
        listener.setblocking(False)
        server = uvicorn.Server(uvicorn.Config(app, log_config=None, access_log=False, log_level="warning"))
        thread = Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
        thread.start()
        deadline = monotonic() + 15
        while not server.started and thread.is_alive() and monotonic() < deadline:
            sleep(0.05)
        if not server.started:
            raise RuntimeError("Isolated W-07 server did not start on port 8007")

        environment = dict(os.environ, W07_BASE_URL=BASE_URL, W07_RUNTIME_JSON=str(output / "runtime.json"))
        checker = ROOT / "scripts/w07_web_check.cjs"
        if not checker.is_file():
            raise RuntimeError("scripts/w07_web_check.cjs is not available yet")
        result = subprocess.run(["node", str(checker)], cwd=ROOT, env=environment)
        summary["browserExitCode"] = result.returncode
        if result.returncode == 0:
            summary.update(_progress_database_evidence(audit_engine, output, seeded[0].id, graph))
            summary["acceptanceAssertionsPassed"] = True
        _write_summary(output, summary)
        return result.returncode
    finally:
        if server is not None:
            server.should_exit = True
        if thread is not None:
            thread.join(15)
            if thread.is_alive():
                raise RuntimeError("Isolated W-07 server did not stop")
        if listener is not None:
            listener.close()
        if phase_b is not None:
            phase_b.close()
        if engine is not None:
            engine.dispose()
        if audit_engine is not None:
            audit_engine.dispose()
        if created:
            if not re.fullmatch(r"wayfinder_w07_[0-9a-f]{32}", database_name):
                raise RuntimeError("Refusing to drop an unexpected W-07 database")
            with admin.connect() as connection:
                connection.execute(text(f'DROP DATABASE "{database_name}" WITH (FORCE)'))
            summary["temporaryDatabaseRemoved"] = True
        admin.dispose()
        _write_summary(output, summary)


def _verify_doc1_fixture() -> None:
    manifest_path = ROOT / "report/doc1-rebuild-evidence-2026-10-20/development-fixtures.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = next((row for row in manifest["files"] if row["path"] == "doc-1.pdf"), None)
    if expected is None:
        raise RuntimeError("doc-1.pdf is absent from the approved fixture manifest")
    source = ROOT / "doc-1.pdf"
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != expected["sha256"]:
        raise RuntimeError("doc-1.pdf does not match the approved development fixture manifest")


def _forbid_live_providers() -> None:
    def forbidden(*_args, **_kwargs):
        raise AssertionError("W-07 runtime attempted a live provider request")

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


def _read_migration_head(engine) -> str | None:
    with engine.connect() as connection:
        return connection.scalar(text("SELECT version_num FROM alembic_version"))


def _progress_database_evidence(engine, output: Path, course_id: str, graph) -> dict:
    path = output / "learner-state.json"
    if not path.is_file():
        raise AssertionError("browser checker did not write learner-state.json")
    state = json.loads(path.read_text(encoding="utf-8"))
    if any("token" in key.lower() or "cookie" in key.lower() for key in state):
        raise AssertionError("learner-state.json must not contain tokens or cookies")
    learner_a, learner_b = state.get("learnerAId"), state.get("learnerBId")
    learned_node, unmarked_node = state.get("learnedNodeId"), state.get("unmarkedNodeId")
    if not learner_a or not learner_b or learner_a == learner_b:
        raise AssertionError("browser must register two distinct learner accounts")
    if not learned_node or not unmarked_node or learned_node == unmarked_node:
        raise AssertionError("browser must record separate learned and unmarked concepts")
    if state.get("courseId") != course_id:
        raise AssertionError("browser learner state does not match the doc-1 course fixture")
    if learned_node not in graph.learnable_nodes or unmarked_node not in graph.learnable_nodes:
        raise AssertionError("browser recorded progress nodes outside the published doc-1 graph")

    with engine.connect() as connection:
        accounts = connection.execute(
            text("SELECT id,role,status FROM account WHERE id IN (:a,:b)"), {"a": learner_a, "b": learner_b}
        ).mappings().all()
        if len(accounts) != 2 or any(row["role"] != "user" or row["status"] != "active" for row in accounts):
            raise AssertionError("browser learner accounts are missing or do not have user role")
        rows = connection.execute(text(
            "SELECT owner, doc_id, value->>'node_id' AS node_id, value->>'state' AS state, "
            "value->>'source' AS source FROM phase_b_record WHERE kind='progress' "
            "AND doc_id=:doc_id AND owner IN (:a,:b) ORDER BY owner,node_id"
        ), {"doc_id": "doc-1", "a": learner_a, "b": learner_b}).mappings().all()
        by_owner_node = {(str(row["owner"]), row["node_id"]): row for row in rows}
        learned_row = by_owner_node.get((learner_a, learned_node))
        unmarked_row = by_owner_node.get((learner_a, unmarked_node))
        if not learned_row or learned_row["state"] != "learned" or learned_row["source"] != "learner":
            raise AssertionError("independent PostgreSQL read did not find learner A's learned progress")
        if not unmarked_row or unmarked_row["state"] != "not_learned" or unmarked_row["source"] != "learner":
            raise AssertionError("independent PostgreSQL read did not find learner A's explicit unmark")
        if (learner_b, learned_node) in by_owner_node or (learner_b, unmarked_node) in by_owner_node:
            raise AssertionError("learner A's progress leaked to learner B in PostgreSQL")
        if any(str(row["owner"]) == learner_b for row in rows):
            raise AssertionError("new learner B unexpectedly has persisted progress rows")
        if len(rows) != 2:
            raise AssertionError(f"expected exactly two successful learner A progress rows, found {len(rows)}")
        if state.get("rollbackNodeId"):
            rollback_row = by_owner_node.get((learner_a, state["rollbackNodeId"]))
            if rollback_row and (rollback_row["state"] == "learned" or rollback_row["source"] == "learner"):
                raise AssertionError("failed mock PUT unexpectedly persisted rollback progress")
        return {
            "learnerAccounts": 2,
            "progressRowsForLearners": len(rows),
            "learnerAProgress": [
                {"nodeId": row["node_id"], "state": row["state"], "source": row["source"]}
                for row in rows if str(row["owner"]) == learner_a
            ],
            "learnerBProgressRows": sum(str(row["owner"]) == learner_b for row in rows),
            "learnerIsolationVerifiedByIndependentPostgresConnection": True,
            "failedWritePersisted": False,
            "phaseBRecords": connection.scalar(text("SELECT count(*) FROM phase_b_record")),
        }


def _write_summary(output: Path, summary: dict) -> None:
    (output / "runtime.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
