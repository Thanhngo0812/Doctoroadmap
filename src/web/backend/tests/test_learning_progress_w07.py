from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event, text

from wayfinder.api.app import create_app
from wayfinder.composition import WebServices, compose_account_service, compose_course_services
from wayfinder.domain.auth import Actor
from wayfinder.domain.courses import Membership
from wayfinder.fakes.mail import FakeMailer
from wayfinder.infrastructure.database import create_database_engine
from wayfinder.infrastructure.phase_b_store import PostgresPhaseBStore
from wayfinder.settings import WebSettings
from wayfinder.testing import FakeClock, _sample_graph


pytestmark = pytest.mark.postgres
ORIGIN = "http://testserver"


@pytest.fixture
def w07(postgres_database_url):
    from wayfinder.application.courses import CourseService
    from wayfinder.application.learning_gateway import LearningGateway
    from wayfinder.infrastructure.course_store import PostgresCourseStore
    from wayfinder.infrastructure.learning_runtime import WebLearningRuntime

    engine = create_database_engine(postgres_database_url)
    with engine.begin() as connection:
        connection.execute(text(
            "TRUNCATE course,membership,phase_b_record,usage_ledger,phase_b_cache,phase_b_negative,account "
            "CASCADE"
        ))
    settings = WebSettings(_env_file=None, frontend_dist=Path("missing"), allowed_origins=[ORIGIN])
    clock = FakeClock()
    accounts = compose_account_service(settings, engine, mailer=FakeMailer())
    phase_b = PostgresPhaseBStore(engine)
    graph = _sample_graph()
    graph.doc_id, graph.graph_version = "doc-1", 8
    graph.nodes["b"] = {**graph.nodes["a"], "node_id": "b", "module_id": "m1", "display_name": "B"}
    graph.learnable_nodes["b"] = graph.nodes["b"]
    graph.modules["m1"]["node_ids"].append("b")
    graph.nodes["hidden"] = {**graph.nodes["a"], "node_id": "hidden", "learnable": False}
    graph.modules["m1"]["node_ids"].append("hidden")

    store = PostgresCourseStore(engine)
    runtime = WebLearningRuntime(phase_b, clock=clock)
    courses = CourseService(store, settings=settings, clock=clock)
    gateway = LearningGateway(courses, runtime, lambda doc_id, version: graph)
    courses.gateway = gateway
    app = create_app(settings, WebServices(
        health_check=lambda: "ok", accounts=accounts, phase_b_store=phase_b,
        courses=courses, learning=gateway,
    ))

    def make_user(label):
        client = TestClient(app)
        email = f"{label.lower().replace(' ', '-')}-{uuid4().hex}@example.vn"
        result = client.post("/api/v1/auth/register", headers={"Origin": ORIGIN}, json={
            "email": email, "password": "W07 isolated private passphrase!", "display_name": label,
        })
        assert result.status_code == 200, result.text
        identity = client.get("/api/v1/me").json()
        account = accounts.me(client.cookies.get("d2r_session")).account
        actor = Actor(account.id, account.role, account.email_verified_at is not None, account.status)
        return SimpleNamespace(client=client, actor=actor,
                               headers={"Origin": ORIGIN, "X-CSRF-Token": identity["csrf_token"]})

    a, b = make_user("Learner A"), make_user("Learner B")
    course = courses.create_course(a.actor, doc_id="doc-1", title="Progress course",
                                   graph_version=8, module_count=1)
    with store.atomic():
        store.add_membership(Membership(course.id, b.actor.user_id, "learner", "email",
                                        clock.now(), clock.now()))
    independent_engine = create_database_engine(postgres_database_url)
    independent_store = PostgresPhaseBStore(independent_engine)
    other_courses, other_gateway = compose_course_services(
        settings, independent_engine, independent_store,
        graph_loader=lambda doc_id, version: graph, clock=clock,
    )
    yield SimpleNamespace(engine=engine, independent_engine=independent_engine,
        independent_store=independent_store, phase_b=phase_b, graph=graph, clock=clock,
        accounts=accounts, courses=courses, gateway=gateway, other_gateway=other_gateway,
        course=course, a=a, b=b, app=app)
    independent_store.close()
    phase_b.close()


def test_progress_is_isolated_between_members_using_independent_postgres_runtimes(w07):
    w07.gateway.set_progress(w07.a.actor, w07.course.id, "a", True)
    assert w07.other_gateway.get_progress(w07.b.actor, w07.course.id)["nodes"]["a"]["state"] == "not_learned"

    w07.other_gateway.set_progress(w07.b.actor, w07.course.id, "a", True)
    w07.other_gateway.set_progress(w07.b.actor, w07.course.id, "a", False)

    assert w07.gateway.get_progress(w07.a.actor, w07.course.id)["nodes"]["a"]["state"] == "learned"
    assert w07.other_gateway.get_progress(w07.b.actor, w07.course.id)["nodes"]["a"]["state"] == "not_learned"
    with w07.independent_engine.connect() as connection:
        records = connection.execute(text(
            "SELECT owner,value FROM phase_b_record WHERE kind='progress' AND doc_id='doc-1'"
        )).mappings().all()
    assert {row["owner"] for row in records} == {w07.a.actor.user_id, w07.b.actor.user_id}
    assert {row["owner"]: row["value"]["state"] for row in records} == {
        w07.a.actor.user_id: "learned", w07.b.actor.user_id: "not_learned"
    }


def test_unmark_then_correct_quiz_keeps_learner_choice_through_gateway(w07):
    w07.gateway.set_progress(w07.a.actor, w07.course.id, "a", False)
    learner = w07.gateway.learner(w07.a.actor, w07.course.id)
    learner.progress.mark_quiz_correct(learner.owner, learner.doc_id, ["a"])

    progress = w07.gateway.get_progress(w07.a.actor, w07.course.id)
    assert progress["nodes"]["a"]["state"] == "not_learned"
    assert progress["nodes"]["a"]["source"] == "learner"


def test_quiz_read_then_concurrent_learner_unmark_is_serialized_by_postgres(w07):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from time import monotonic, sleep

    quiz_store = w07.independent_store
    original_get = quiz_store.get_record
    quiz_read = Event()
    release_quiz = Event()

    def paused_get(kind, record_id):
        result = original_get(kind, record_id)
        if kind == "progress":
            quiz_read.set()
            assert release_quiz.wait(10), "quiz test did not release its transaction"
        return result

    quiz_store.get_record = paused_get
    lock_request, backend_pid = Event(), {}

    def observe_lock(connection, cursor, statement, parameters, context, executemany):
        if "pg_advisory_xact_lock" in statement:
            backend_pid["value"] = connection.connection.driver_connection.info.backend_pid
            lock_request.set()

    event.listen(w07.engine, "before_cursor_execute", observe_lock)

    def quiz_correct():
        learner = w07.other_gateway.learner(w07.a.actor, w07.course.id)
        learner.progress.mark_quiz_correct(learner.owner, learner.doc_id, ["a"])

    def wait_until_pg_lock_wait_or_learner_finishes(learner_future, timeout=5):
        deadline = monotonic() + timeout
        while monotonic() < deadline:
            if learner_future.done():
                return
            with w07.engine.connect() as connection:
                waiting = connection.scalar(text(
                    "SELECT wait_event_type='Lock' FROM pg_stat_activity WHERE pid=:pid"
                ), {"pid": backend_pid.get("value")})
            if waiting:
                return
            sleep(0.01)
        raise AssertionError("learner transaction neither waited on PostgreSQL nor completed")

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            quiz = pool.submit(quiz_correct)
            assert quiz_read.wait(5), "quiz did not read progress"
            learner = pool.submit(w07.gateway.set_progress, w07.a.actor, w07.course.id, "a", False)
            assert lock_request.wait(5), "learner did not begin its PostgreSQL transaction"
            wait_until_pg_lock_wait_or_learner_finishes(learner)
            release_quiz.set()
            quiz.result(timeout=10)
            learner.result(timeout=10)
    finally:
        release_quiz.set()
        event.remove(w07.engine, "before_cursor_execute", observe_lock)
        quiz_store.get_record = original_get

    result = w07.other_gateway.get_progress(w07.a.actor, w07.course.id)["nodes"]["a"]
    assert result["state"] == "not_learned" and result["source"] == "learner"
    with w07.independent_engine.connect() as connection:
        saved = connection.execute(text(
            "SELECT value FROM phase_b_record WHERE kind='progress' AND owner=:uid AND doc_id='doc-1'"
        ), {"uid": w07.a.actor.user_id}).scalar_one()
    assert saved["state"] == "not_learned" and saved["source"] == "learner"


def test_learner_unmark_transaction_then_concurrent_quiz_respects_learner_source(w07):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from time import monotonic, sleep

    original_put = w07.phase_b.put_record
    learner_write, release_learner = Event(), Event()

    def paused_put(kind, record_id, value):
        result = original_put(kind, record_id, value)
        if kind == "progress" and value.get("owner") == w07.a.actor.user_id:
            learner_write.set()
            assert release_learner.wait(10), "learner test did not release its transaction"
        return result

    w07.phase_b.put_record = paused_put
    lock_request, backend_pid = Event(), {}

    def observe_lock(connection, cursor, statement, parameters, context, executemany):
        if "pg_advisory_xact_lock" in statement:
            backend_pid["value"] = connection.connection.driver_connection.info.backend_pid
            lock_request.set()

    event.listen(w07.independent_engine, "before_cursor_execute", observe_lock)

    def quiz_correct():
        learner = w07.other_gateway.learner(w07.a.actor, w07.course.id)
        learner.progress.mark_quiz_correct(learner.owner, learner.doc_id, ["a"])

    def wait_until_pg_lock_wait(timeout=5):
        deadline = monotonic() + timeout
        while monotonic() < deadline:
            with w07.independent_engine.connect() as connection:
                waiting = connection.scalar(text(
                    "SELECT wait_event_type='Lock' FROM pg_stat_activity WHERE pid=:pid"
                ), {"pid": backend_pid.get("value")})
            if waiting:
                return
            sleep(0.01)
        raise AssertionError("quiz did not wait for the learner's PostgreSQL lock")

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            learner_write_future = pool.submit(w07.gateway.set_progress, w07.a.actor,
                                               w07.course.id, "a", False)
            assert learner_write.wait(5), "learner did not write inside its transaction"
            quiz = pool.submit(quiz_correct)
            assert lock_request.wait(5), "quiz did not begin its PostgreSQL transaction"
            wait_until_pg_lock_wait()
            release_learner.set()
            learner_write_future.result(timeout=10)
            quiz.result(timeout=10)
    finally:
        release_learner.set()
        event.remove(w07.independent_engine, "before_cursor_execute", observe_lock)
        w07.phase_b.put_record = original_put

    result = w07.gateway.get_progress(w07.a.actor, w07.course.id)["nodes"]["a"]
    assert result["state"] == "not_learned" and result["source"] == "learner"
    with w07.independent_engine.connect() as connection:
        saved = connection.execute(text(
            "SELECT value FROM phase_b_record WHERE kind='progress' AND owner=:uid AND doc_id='doc-1'"
        ), {"uid": w07.a.actor.user_id}).scalar_one()
    assert saved["state"] == "not_learned" and saved["source"] == "learner"


def test_progress_http_validates_node_and_boolean_and_hides_private_course(w07):
    base = f"/api/v1/courses/{w07.course.id}/progress"
    read = w07.a.client.get(base)
    assert read.status_code == 200
    assert read.json()["contract_version"] == "progress-1"
    assert read.json()["course_id"] == w07.course.id
    assert read.json()["nodes"]["a"]["state"] == "not_learned"
    assert "hidden" not in read.json()["nodes"]

    updated = w07.a.client.put(f"{base}/a", headers=w07.a.headers, json={"learned": True})
    assert updated.status_code == 200, updated.text
    assert updated.json()["nodes"]["a"]["state"] == "learned"
    assert updated.json()["nodes"]["a"]["source"] == "learner"
    assert w07.a.client.put(f"{base}/a", headers=w07.a.headers,
                            json={"learned": 1}).status_code == 422
    assert w07.a.client.put(f"{base}/a", headers=w07.a.headers,
                            json={"learned": False, "owner": w07.b.actor.user_id}).status_code == 422

    for node_id in ("missing", "hidden"):
        result = w07.a.client.put(f"{base}/{node_id}", headers=w07.a.headers, json={"learned": True})
        assert result.status_code == 404
        assert result.json()["error"]["code"] == "not_found"

    guest = TestClient(w07.app)
    assert guest.get(base).status_code == 401
    csrf = w07.a.client.put(f"{base}/a", json={"learned": False})
    assert csrf.status_code == 403
    assert csrf.json()["error"]["code"] == "csrf_failed"

    outsider_course = w07.courses.create_course(w07.a.actor, doc_id="doc-1", title="Private",
        graph_version=8, module_count=1)
    hidden = w07.b.client.get(f"/api/v1/courses/{outsider_course.id}/progress")
    assert hidden.status_code == 404
    assert hidden.json()["error"]["code"] == "not_found"
    hidden_write = w07.b.client.put(f"/api/v1/courses/{outsider_course.id}/progress/a",
        headers=w07.b.headers, json={"learned": True})
    assert hidden_write.status_code == 404
    assert hidden_write.json()["error"]["code"] == "not_found"


def test_concurrent_member_writes_on_independent_connections_keep_actor_scopes(w07):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    barrier = Barrier(2)

    def write(gateway, actor, learned):
        barrier.wait(timeout=5)
        gateway.set_progress(actor, w07.course.id, "a", learned)

    with ThreadPoolExecutor(max_workers=2) as pool:
        left = pool.submit(write, w07.gateway, w07.a.actor, True)
        right = pool.submit(write, w07.other_gateway, w07.b.actor, False)
        left.result(timeout=10)
        right.result(timeout=10)

    assert w07.gateway.get_progress(w07.a.actor, w07.course.id)["nodes"]["a"]["state"] == "learned"
    assert w07.other_gateway.get_progress(w07.b.actor, w07.course.id)["nodes"]["a"]["state"] == "not_learned"
    with w07.independent_engine.connect() as connection:
        rows = connection.execute(text(
            "SELECT owner,value->>'state' AS state FROM phase_b_record WHERE kind='progress' AND doc_id='doc-1'"
        )).all()
    assert {owner: state for owner, state in rows} == {
        w07.a.actor.user_id: "learned", w07.b.actor.user_id: "not_learned"
    }


def test_roadmap_summaries_match_progress_and_preserve_published_node_order(w07):
    w07.gateway.set_progress(w07.a.actor, w07.course.id, "b", True)
    roadmap = w07.gateway.get_roadmap(w07.a.actor, w07.course.id)
    progress = w07.gateway.get_progress(w07.a.actor, w07.course.id)

    assert roadmap["progress"] == {"learned": 1, "total": 2}
    assert roadmap["modules"][0]["progress"] == {"learned": 1, "total": 2}
    assert [concept["node_id"] for concept in roadmap["modules"][0]["concepts"]] == ["a", "b"]
    assert progress["modules"] == [{"module_id": "m1", "learned": 1, "total": 2}]
