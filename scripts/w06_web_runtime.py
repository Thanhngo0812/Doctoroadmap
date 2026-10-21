"""Run the W-06 browser check against a disposable PostgreSQL database."""
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


BASE_URL = "http://127.0.0.1:8006"
DATABASE_PREFIX = "wayfinder_w06_"


def main() -> int:
    shared_root = ROOT.parents[1]
    local_env = ROOT / "src/web/.env"
    env_path = local_env if local_env.is_file() else shared_root / "src/web/.env"
    values = dotenv_values(env_path)
    configured = os.environ.get("WAYFINDER_TEST_DATABASE_URL") or values.get("WAYFINDER_TEST_DATABASE_URL")
    if not configured:
        raise RuntimeError("PostgreSQL test database configuration is required")

    admin = create_database_engine(configured).execution_options(isolation_level="AUTOCOMMIT")
    database_name = DATABASE_PREFIX + uuid4().hex
    database_url = make_url(configured).set(database=database_name)
    output = ROOT / "report/w06-web-evidence"
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
    }
    created = False
    engine = phase_b = None
    server = thread = None
    listener = None
    try:
        _forbid_live_providers()
        with admin.connect() as connection:
            connection.execute(text(f'CREATE DATABASE "{database_name}"'))
            created = True
        upgrade_database(database_url)
        engine = create_database_engine(database_url)
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
        admin_account = accounts.create_admin(
            "w06-seed-admin@example.invalid", "W06 disposable seed admin passphrase!", "W06 Seed Admin"
        )
        seed_actor = Actor(admin_account.id, "admin", True, "active")

        phase_b = PostgresPhaseBStore(engine, lock_pool_size=settings.phase_b_lock_pool_size)
        graph_store = JsonArtifactStore(settings.artifact_root)

        def graph_loader(doc_id: str, version: int | None):
            return load_learning_graph(graph_store, doc_id, version)

        courses, learning = compose_course_services(
            settings, engine, phase_b, graph_loader=graph_loader
        )
        media = MemoryMediaStore()
        seeded = SampleSeeder(
            courses, learning, media, source_root=ROOT, folder="w06-browser/fake-media"
        ).execute(seed_actor)
        private_course = courses.create_course(
            seed_actor,
            doc_id="doc-1",
            title="Private W-06 outsider fixture",
            description="Owned by the disposable seed administrator.",
            graph_version=8,
            module_count=len(graph_loader("doc-1", 8).modules),
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
            "privateCourseId": private_course.id,
            "seedOwnerId": admin_account.id,
            "samples": [
                {
                    "courseId": course.id,
                    "docId": course.doc_id,
                    "graphVersion": course.published_graph_version,
                }
                for course in seeded
            ],
            "memoryMediaUploads": len(media.files),
        }
        summary["migrationHead"] = _read_migration_head(engine)
        if summary["migrationHead"] != "w06_0005":
            raise RuntimeError("Disposable database did not reach W-06 migration head")
        _write_summary(output, summary)

        listener = socket.socket()
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(("127.0.0.1", 8006))
        listener.listen(128)
        listener.setblocking(False)
        server = uvicorn.Server(uvicorn.Config(app, log_config=None, access_log=False, log_level="warning"))
        thread = Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
        thread.start()
        deadline = monotonic() + 15
        while not server.started and thread.is_alive() and monotonic() < deadline:
            sleep(0.05)
        if not server.started:
            raise RuntimeError("Isolated W-06 server did not start on port 8006")

        environment = dict(os.environ, W06_BASE_URL=BASE_URL, W06_RUNTIME_JSON=str(output / "runtime.json"))
        checker = ROOT / "scripts/w06_web_check.cjs"
        if not checker.is_file():
            raise RuntimeError("scripts/w06_web_check.cjs is not available yet")
        result = subprocess.run(["node", str(checker)], cwd=ROOT, env=environment)
        summary["browserExitCode"] = result.returncode
        if result.returncode == 0:
            summary.update(_database_evidence(
                engine, output, private_course.id, admin_account.id, seeded
            ))
            summary["acceptanceAssertionsPassed"] = True
        _write_summary(output, summary)
        return result.returncode
    finally:
        if server is not None:
            server.should_exit = True
        if thread is not None:
            thread.join(15)
            if thread.is_alive():
                raise RuntimeError("Isolated W-06 server did not stop")
        if listener is not None:
            listener.close()
        if phase_b is not None:
            phase_b.close()
        if engine is not None:
            engine.dispose()
        if created:
            if not re.fullmatch(r"wayfinder_w06_[0-9a-f]{32}", database_name):
                raise RuntimeError("Refusing to drop an unexpected database")
            with admin.connect() as connection:
                connection.execute(text(f'DROP DATABASE "{database_name}" WITH (FORCE)'))
            summary["temporaryDatabaseRemoved"] = True
        admin.dispose()
        _write_summary(output, summary)


def _forbid_live_providers() -> None:
    def forbidden(*_args, **_kwargs):
        raise AssertionError("W-06 browser runtime attempted a live provider request")

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


def _database_evidence(engine, output: Path, private_course_id: str, seed_owner_id: str, seeded) -> dict:
    learner_state_path = output / "learner-state.json"
    if not learner_state_path.is_file():
        raise AssertionError("browser checker did not write learner-state.json")
    learner_state = json.loads(learner_state_path.read_text(encoding="utf-8"))
    sample_ids = {course.id for course in seeded}
    by_doc = {course.doc_id: course.id for course in seeded}
    expected_joined = {by_doc["doc-1"], by_doc["doc-6"]}
    if set(learner_state.get("joinedCourseIds", [])) != expected_joined:
        raise AssertionError("browser learner state does not match the expected sample joins")
    if learner_state.get("privateCourseId") != private_course_id:
        raise AssertionError("browser learner state does not match the private-course fixture")
    if learner_state.get("duplicateJoinStatus") != 200:
        raise AssertionError("browser checker did not confirm a successful duplicate join")
    if any("token" in key.lower() or "cookie" in key.lower() for key in learner_state):
        raise AssertionError("learner-state.json must not contain tokens or cookies")
    learner_id = learner_state.get("accountId")
    if not learner_id:
        raise AssertionError("browser learner state omitted the registered account ID")
    with engine.connect() as connection:
        account = connection.execute(text("SELECT role,status FROM account WHERE id=:uid"),
                                     {"uid": learner_id}).one_or_none()
        if account is None or account.role != "user" or account.status != "active":
            raise AssertionError("browser learner account is missing or has the wrong identity")
        sample_owner_memberships = connection.scalar(
            text("SELECT count(*) FROM membership m JOIN course c ON c.id=m.course_id "
                 "WHERE c.is_sample AND m.role='owner'")
        )
        sample_learner_memberships = connection.scalar(
            text("SELECT count(*) FROM membership m JOIN course c ON c.id=m.course_id "
                 "WHERE c.is_sample AND m.role='learner' AND m.via='sample'")
        )
        private_memberships = connection.scalar(
            text("SELECT count(*) FROM membership WHERE course_id=:cid"), {"cid": private_course_id}
        )
        private_owner = connection.execute(
            text("SELECT account_id,role FROM membership WHERE course_id=:cid"), {"cid": private_course_id}
        ).one_or_none()
        actual_learner_memberships = connection.execute(
            text("SELECT course_id,role,via FROM membership WHERE account_id=:uid AND course_id IN (:doc1,:doc6)"),
            {"uid": learner_id, "doc1": by_doc["doc-1"], "doc6": by_doc["doc-6"]},
        ).mappings().all()
        if sample_owner_memberships != 6:
            raise AssertionError(f"expected six sample owners, found {sample_owner_memberships}")
        if sample_learner_memberships != 2:
            raise AssertionError(f"expected two persisted sample learners, found {sample_learner_memberships}")
        if (private_memberships != 1 or private_owner is None or str(private_owner.account_id) != seed_owner_id
                or private_owner.role != "owner"):
            raise AssertionError("private course does not have exactly its seed administrator as owner")
        actual_courses = {str(row["course_id"]) for row in actual_learner_memberships}
        if (actual_courses != expected_joined or len(actual_learner_memberships) != 2
                or any(row["role"] != "learner" or row["via"] != "sample" for row in actual_learner_memberships)):
            raise AssertionError("PostgreSQL memberships do not match the two browser joins")
        return {
            "sampleCourseCount": len(sample_ids),
            "sampleOwnerMemberships": sample_owner_memberships,
            "sampleLearnerMemberships": sample_learner_memberships,
            "privateCourseMemberships": private_memberships,
            "learnerAccountId": learner_id,
            "learnerCourseIds": sorted(actual_courses),
            "duplicateJoinStatus": learner_state["duplicateJoinStatus"],
            "duplicateJoinIsIdempotent": len(actual_learner_memberships) == 2,
            "phaseBRecords": connection.scalar(text("SELECT count(*) FROM phase_b_record")),
        }


def _write_summary(output: Path, summary: dict) -> None:
    (output / "runtime.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    raise SystemExit(main())
