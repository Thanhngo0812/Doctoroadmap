from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from wayfinder.api.app import create_app
from wayfinder.api.auth import get_actor
from wayfinder.composition import WebServices, compose_account_service
from wayfinder.domain.auth import Actor
from wayfinder.fakes.media import MemoryMediaStore
from wayfinder.fakes.mail import FakeMailer
from wayfinder.infrastructure.database import create_database_engine
from wayfinder.infrastructure.phase_b_store import PostgresPhaseBStore
from wayfinder.testing import FakeClock, _sample_graph
from wayfinder.settings import WebSettings


pytestmark = pytest.mark.postgres
ORIGIN = "http://testserver"


@pytest.fixture
def courses(postgres_database_url, monkeypatch):
    from wayfinder.application.courses import CourseService
    from wayfinder.application.learning_gateway import LearningGateway
    from wayfinder.infrastructure.course_store import PostgresCourseStore
    from wayfinder.infrastructure.learning_runtime import WebLearningRuntime

    def forbidden(*args, **kwargs):
        raise AssertionError("W-06 must not use providers, ADC or live media")

    monkeypatch.setattr("doc2roadmap.infrastructure.llm.gemini.urlopen", forbidden)
    monkeypatch.setattr("doc2roadmap.infrastructure.embedding.gemini.urlopen", forbidden)
    monkeypatch.setattr("doc2roadmap.infrastructure.google_auth.VertexCredentials.headers", forbidden)
    engine = create_database_engine(postgres_database_url)
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE course, membership, phase_b_record, usage_ledger, phase_b_cache, phase_b_negative CASCADE"))
    settings = WebSettings(
        _env_file=None, frontend_dist=Path("missing"), allowed_origins=[ORIGIN])
    clock = FakeClock()
    accounts = compose_account_service(settings, engine, mailer=FakeMailer())
    phase_b = PostgresPhaseBStore(engine)
    store = PostgresCourseStore(engine)
    graph = _sample_graph()
    graph.doc_id, graph.graph_version = "doc-1", 8
    loaded = []

    def graph_loader(doc_id, version):
        loaded.append((doc_id, version))
        return graph

    runtime = WebLearningRuntime(phase_b, clock=clock)
    service = CourseService(store, settings=settings, clock=clock)
    gateway = LearningGateway(service, runtime, graph_loader)
    service.gateway = gateway
    services = WebServices(health_check=lambda: "ok", accounts=accounts, phase_b_store=phase_b,
                           courses=service, learning=gateway)
    app = create_app(settings, services)

    def user(role="user"):
        client = TestClient(app)
        email = uuid4().hex + "@example.vn"
        result = client.post("/api/v1/auth/register", headers={"Origin": ORIGIN},
                             json={"email": email, "password": "W06 very private passphrase!", "display_name": "Người học"})
        assert result.status_code == 200, result.text
        me = client.get("/api/v1/me").json()
        actor = Actor(me["account"]["id"], role, False, "active")
        if role == "admin":
            with engine.begin() as connection:
                connection.execute(text("UPDATE account SET role='admin' WHERE id=:id"), {"id": actor.user_id})
        return actor, client, {"Origin": ORIGIN, "X-CSRF-Token": me["csrf_token"]}

    owner, owner_client, owner_headers = user("admin")
    course = service.create_course(owner, doc_id="doc-1", title="Khoá riêng", graph_version=8, module_count=1)
    sample = service.create_course(owner, doc_id="doc-1", title="Khoá mẫu", graph_version=8,
                                   module_count=1, is_sample=True)
    yield SimpleNamespace(**locals())
    phase_b.close()


def routes_with_cid(router):
    for route in router.routes:
        included = getattr(route, "original_router", None)
        if included is not None:
            yield from routes_with_cid(included)
        elif "{cid}" in getattr(route, "path", ""):
            yield route


def assert_private_course_routes_protected(app, client, headers, cid):
    seen = set()
    for route in routes_with_cid(app):
        path = route.path.replace("{cid}", cid)
        import re
        path = re.sub(r"\{[^}]+\}", "unknown-resource", path)
        for method in route.methods - {"HEAD", "OPTIONS"}:
            response = client.request(method, path, headers=headers,
                                      json={"title": "Attack", "owner": "someone-else"} if method not in {"GET", "DELETE"} else None)
            assert response.status_code == 404, (method, path, response.text)
            assert response.json()["error"]["code"] == "not_found"
            seen.add((method, route.path))
    assert ("POST", "/api/v1/courses/{cid}/join-sample") in seen
    return seen


def test_every_cid_route_hides_private_course_from_outsiders_including_admin(courses):
    for role in ("user", "admin"):
        _, client, headers = courses.user(role)
        assert len(assert_private_course_routes_protected(courses.app, client, headers, courses.course.id)) >= 4
    assert courses.loaded == []


def test_route_inventory_catches_a_new_unguarded_route(courses):
    @courses.app.get("/api/v1/courses/{cid}/unguarded-probe")
    def unguarded(cid: str, actor=Depends(get_actor)):
        return {"leaked": cid}

    _, client, headers = courses.user()
    with pytest.raises(AssertionError, match="unguarded-probe"):
        assert_private_course_routes_protected(courses.app, client, headers, courses.course.id)


def test_logged_in_unverified_user_can_join_dev_sample_and_repeat_without_duplicates(courses):
    actor, client, headers = courses.user()
    before = client.get("/api/v1/courses").json()
    assert [c["course_id"] for c in before["samples"]] == [courses.sample.id]
    assert before["samples"][0]["progress"] is None
    assert courses.loaded == []
    assert client.get(f"/api/v1/courses/{courses.sample.id}/roadmap").status_code == 404
    for _ in range(2):
        result = client.post(f"/api/v1/courses/{courses.sample.id}/join-sample", headers=headers,
                             json={"owner": courses.owner.user_id})
        assert result.status_code == 200, result.text
        assert result.json()["role"] == "learner"
    with courses.engine.connect() as connection:
        assert connection.scalar(text("SELECT count(*) FROM membership WHERE course_id=:cid AND account_id=:uid"),
                                 {"cid": courses.sample.id, "uid": actor.user_id}) == 1
    listed = client.get("/api/v1/courses").json()
    assert listed["samples"] == [] and len(listed["joined"]) == 1
    assert listed["joined"][0]["progress"]["total"] == len(courses.graph.learnable_nodes)
    assert listed["joined"][0]["member_count"] is None
    roadmap = client.get(f"/api/v1/courses/{courses.sample.id}/roadmap")
    assert roadmap.status_code == 200
    assert roadmap.json()["course_id"] == courses.sample.id
    assert roadmap.json()["graph_version"] == 8
    assert courses.loaded == [("doc-1", 8)]


def test_guest_and_prod_cannot_join_or_discover_samples(courses):
    guest = TestClient(courses.app)
    response = guest.post(f"/api/v1/courses/{courses.sample.id}/join-sample", headers={"Origin": ORIGIN}, json={})
    assert response.status_code in {401, 403}
    actor, client, headers = courses.user()
    courses.settings.env = "prod"
    assert client.get("/api/v1/courses").json()["samples"] == []
    assert client.post(f"/api/v1/courses/{courses.sample.id}/join-sample", headers=headers, json={}).status_code == 404
    assert courses.store.get_membership(courses.sample.id, actor.user_id) is None


def test_owner_constraint_and_course_creation_rollback(courses, monkeypatch):
    actor, _, _ = courses.user()
    with pytest.raises(IntegrityError):
        with courses.engine.begin() as connection:
            connection.execute(text("INSERT INTO membership (course_id,account_id,role,via,joined_at) "
                                    "VALUES (:cid,:uid,'owner','owner',now())"),
                               {"cid": courses.course.id, "uid": actor.user_id})
    with courses.engine.connect() as connection:
        count = connection.scalar(text("SELECT count(*) FROM course"))
    def fail(*args, **kwargs):
        raise RuntimeError("owner membership failed")
    monkeypatch.setattr(courses.store, "add_membership", fail)
    with pytest.raises(RuntimeError, match="owner membership failed"):
        courses.service.create_course(courses.owner, doc_id="doc-1", title="Rollback", graph_version=8, module_count=1)
    with courses.engine.connect() as connection:
        assert connection.scalar(text("SELECT count(*) FROM course")) == count


def test_update_requires_owner_and_cannot_change_identity(courses):
    actor, client, headers = courses.user()
    client.post(f"/api/v1/courses/{courses.sample.id}/join-sample", headers=headers, json={})
    assert client.patch(f"/api/v1/courses/{courses.sample.id}", headers=headers, json={"title": "Attack"}).status_code == 403
    result = courses.owner_client.patch(f"/api/v1/courses/{courses.course.id}", headers=courses.owner_headers,
        json={"title": "Tên mới", "description": "Mô tả", "owner_id": actor.user_id, "doc_id": "other", "graph_version": 1})
    assert result.status_code == 200, result.text
    assert result.json()["title"] == "Tên mới"
    saved = courses.store.get_course(courses.course.id)
    assert saved.owner_id == courses.owner.user_id and saved.doc_id == "doc-1" and saved.published_graph_version == 8


def test_membership_activity_updates_only_after_five_minutes(courses):
    first = courses.store.get_membership(courses.course.id, courses.owner.user_id)
    courses.gateway.get_roadmap(courses.owner, courses.course.id)
    assert courses.store.get_membership(courses.course.id, courses.owner.user_id).last_active_at == first.last_active_at
    courses.clock.advance(301)
    courses.gateway.get_roadmap(courses.owner, courses.course.id)
    assert courses.store.get_membership(courses.course.id, courses.owner.user_id).last_active_at == courses.clock.now()


def test_gateway_ignores_claimed_owner_and_records_actor_in_independent_postgres_connection(courses):
    actor, client, headers = courses.user()
    client.post(f"/api/v1/courses/{courses.sample.id}/join-sample", headers=headers, json={})

    # Acceptance-only route for the gateway's bound learner context; no session
    # endpoint is published by W-06 (the HTTP session flow belongs to W-09).
    @courses.app.post("/api/v1/courses/{cid}/binding-probe")
    def binding_probe(cid: str, payload: dict, actor=Depends(get_actor)):
        learner = courses.gateway.learner(actor, cid, **payload)
        session = learner.sessions.create_session(learner.owner, learner.doc_id, {"kind": "roadmap"})
        learner.progress.set_progress(learner.owner, learner.doc_id, "a", True)
        token = learner.spend_guard.reserve("assistant", .02, learner.owner)
        learner.spend_guard.store.append_usage({"purpose": "assistant", "learner_id": learner.owner,
                                              "doc_id": learner.doc_id, "cost_usd": .01})
        return {"session_id": session["session_id"], "reservation": token}

    response = client.post(f"/api/v1/courses/{courses.sample.id}/binding-probe", headers=headers,
                           json={"owner": courses.owner.user_id, "doc_id": "other-book", "graph_version": 999})
    assert response.status_code == 200, response.text
    from wayfinder.infrastructure.database import create_database_engine
    independent = create_database_engine(courses.engine.url)
    try:
        with independent.connect() as connection:
            session = connection.execute(text("SELECT owner,doc_id,value FROM phase_b_record WHERE kind='session' AND record_id=:id"),
                                         {"id": response.json()["session_id"]}).one()
            assert session.owner == actor.user_id and session.doc_id == "doc-1"
            assert session.value["owner"] == actor.user_id
            assert connection.scalar(text("SELECT count(*) FROM phase_b_record WHERE kind='progress' AND owner=:uid"),
                                     {"uid": actor.user_id}) == 1
            reserved = connection.scalar(text("SELECT value FROM phase_b_record WHERE kind='spend_reservation' AND record_id=:id"),
                                         {"id": response.json()["reservation"]})
            assert reserved is not None, "spend guard wrote to a different store"
            assert reserved["learner_id"] == actor.user_id and reserved["cost_usd"] == .02
            assert connection.scalar(text("SELECT extra FROM usage_ledger WHERE learner_id=:uid"),
                                     {"uid": actor.user_id})["cost_usd"] == .01
    finally:
        independent.dispose()
    # The very same route inventory must include the probe as well.
    outsider, outsider_client, outsider_headers = courses.user()
    assert_private_course_routes_protected(courses.app, outsider_client, outsider_headers, courses.course.id)


def test_database_cannot_commit_course_without_matching_owner_membership(courses):
    with pytest.raises(IntegrityError):
        with courses.engine.begin() as connection:
            connection.execute(text("DELETE FROM membership WHERE course_id=:cid AND role='owner'"), {"cid": courses.course.id})
    with courses.engine.connect() as connection:
        assert connection.scalar(text("SELECT count(*) FROM membership WHERE course_id=:cid AND role='owner'"),
                                 {"cid": courses.course.id}) == 1


def test_join_concurrency_respects_course_capacity(courses):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from wayfinder.api.errors import WebError

    courses.settings.course_max_members = 2
    users = [courses.user()[0], courses.user()[0]]
    barrier = Barrier(2)
    def join(actor):
        barrier.wait(5)
        try:
            courses.service.join_sample_course(actor, courses.sample.id)
            return "joined"
        except WebError as error:
            return error.code
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(join, users)) == ["course_full", "joined"]
    assert courses.store.member_count(courses.sample.id) == 2


def test_seed_only_allows_six_development_documents_in_dev_and_uploads_once(courses, tmp_path):
    from wayfinder.application.seed_samples import SampleSeeder, SAMPLE_DOCS
    from wayfinder.api.errors import WebError
    media = MemoryMediaStore()
    seeder = SampleSeeder(courses.service, courses.gateway, media, source_root=tmp_path, folder="fake/dev")
    for doc_id, spec in SAMPLE_DOCS.items():
        (tmp_path / spec["pdf"]).write_bytes(b"%PDF-1.7 fake seed input")
    def graph_loader(doc_id, version):
        courses.loaded.append((doc_id, version))
        from copy import deepcopy
        graph = deepcopy(courses.graph)
        graph.doc_id = doc_id
        graph.graph_version = 8 if doc_id == "doc-1" else 29 if doc_id == "doc-6" else 1
        return graph
    courses.gateway.graph_loader = graph_loader
    loaded_before = list(courses.loaded)
    with pytest.raises(WebError) as outside:
        seeder.execute(courses.owner, ["heldout-looking-fake-01"])
    assert outside.value.code == "not_found"
    assert courses.loaded == loaded_before and media.files == {}
    courses.settings.env = "prod"
    with pytest.raises(WebError) as production:
        seeder.execute(courses.owner, ["doc-6"])
    assert production.value.code == "not_found"
    assert media.files == {} and courses.store.find_sample("doc-6") is None
    assert courses.loaded == loaded_before
    courses.settings.env = "dev"
    with courses.engine.begin() as connection:
        connection.execute(text("DELETE FROM course WHERE id=:cid"), {"cid": courses.sample.id})
    first = seeder.execute(courses.owner, list(SAMPLE_DOCS))
    second = seeder.execute(courses.owner, list(SAMPLE_DOCS))
    assert len(first) == len(second) == 6
    assert [row.id for row in first] == [row.id for row in second]
    assert len(media.files) == 6
    assert {row.doc_id for row in first} == set(SAMPLE_DOCS)
    assert all(courses.store.get_membership(row.id, courses.owner.user_id).role == "owner" for row in first)


def test_composition_binds_vertex_models_and_all_child_stores_to_postgres(courses, monkeypatch):
    from doc2roadmap.config import Settings
    from wayfinder.composition import compose_services
    observed = {}
    def provider(kind):
        def create(*args, **kwargs):
            observed[kind] = kwargs
            return SimpleNamespace(transport=kwargs["transport"])
        return create
    # The web composition must never construct even a temporary CLI JSON store.
    monkeypatch.setattr("doc2roadmap.infrastructure.artifacts.phase_b_store.JsonPhaseBStore",
                        lambda *_a, **_k: pytest.fail("web constructed a CLI JSON store"))
    services = compose_services(
        WebSettings(_env_file=None, database_url=courses.engine.url.render_as_string(hide_password=False)),
        core_settings=Settings(_env_file=None, llm_transport="vertex", vertex_project="fake-project"),
        auth_validator=lambda *_: None, model_factory=provider("model"), embedding_factory=provider("embedding"),
        graph_loader=courses.graph_loader, clock=courses.clock)
    try:
        assert observed["model"]["transport"] == observed["embedding"]["transport"] == "vertex"
        assert services.learning.runtime.model is services.model
        assert services.learning.runtime.embedding is services.embedding
        learner = services.learning.learner(courses.owner, courses.course.id, owner="forged")
        created = learner.sessions.create_session(learner.owner, learner.doc_id, {"kind": "roadmap"})
        token = learner.spend_guard.reserve("assistant", .03, learner.owner)
        with courses.engine.connect() as independent:
            saved = independent.scalar(text("SELECT value FROM phase_b_record WHERE kind='session' AND record_id=:id"),
                                       {"id": created["session_id"]})
            assert saved is not None, "session use case wrote to a different store"
            assert saved["owner"] == courses.owner.user_id
            held = independent.scalar(text("SELECT value FROM phase_b_record WHERE kind='spend_reservation' AND record_id=:id"),
                                      {"id": token})
            assert held is not None, "spend guard wrote to a different store"
            assert held["cost_usd"] == .03 and held["learner_id"] == courses.owner.user_id
        learner.spend_guard.release(token)
    finally:
        services.close()


def test_seed_cli_uses_admin_identity_and_media_port(courses, monkeypatch, tmp_path, capsys):
    from wayfinder import cli
    media = MemoryMediaStore()
    (tmp_path / "doc-6.pdf").write_bytes(b"%PDF-1.7 fake cli")
    monkeypatch.setenv("WAYFINDER_DATABASE_URL", courses.engine.url.render_as_string(hide_password=False))
    monkeypatch.setenv("WAYFINDER_ENV", "dev")
    monkeypatch.setattr("wayfinder.infrastructure.media.CloudinaryMediaStore", lambda: media)
    def load_graph(_store, doc_id, version=None):
        from copy import deepcopy
        graph = deepcopy(courses.graph)
        graph.doc_id = doc_id
        return graph
    monkeypatch.setattr("doc2roadmap.application.phase_b.retrieval.load_learning_graph", load_graph)
    with courses.engine.connect() as connection:
        email = connection.scalar(text("SELECT email FROM account WHERE id=:uid"), {"uid": courses.owner.user_id})
    assert cli.main(["seed-samples", "--admin-email", email, "--source-root", str(tmp_path), "--doc-id", "doc-6"]) == 0
    assert len(media.files) == 1
    assert "doc-6" in capsys.readouterr().out


def test_real_six_book_seed_join_and_roadmap_over_tcp_http(courses, monkeypatch):
    import json
    from contextlib import contextmanager
    from threading import Thread
    from time import monotonic, sleep
    import socket
    import httpx
    import uvicorn
    from doc2roadmap.application.phase_b.retrieval import load_learning_graph
    from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore
    from wayfinder.application.seed_samples import SAMPLE_DOCS
    from wayfinder import cli

    # Inputs are copied and hash-verified by copy_w06_fixtures.py before this
    # mandatory integration test; missing development input must fail, not skip.
    root = Path(__file__).absolute().parents[4]
    artifacts = JsonArtifactStore(root / "artifacts")
    courses.gateway.graph_loader = lambda doc_id, version: load_learning_graph(artifacts, doc_id, version)
    with courses.engine.begin() as connection:
        connection.execute(text("DELETE FROM course WHERE id=:cid"), {"cid": courses.sample.id})
    media = MemoryMediaStore()
    monkeypatch.setenv("WAYFINDER_DATABASE_URL", courses.engine.url.render_as_string(hide_password=False))
    monkeypatch.setenv("WAYFINDER_ENV", "dev")
    monkeypatch.setattr("wayfinder.infrastructure.media.CloudinaryMediaStore", lambda: media)
    with courses.engine.connect() as connection:
        email = connection.scalar(text("SELECT email FROM account WHERE id=:uid"), {"uid": courses.owner.user_id})
    assert cli.main(["seed-samples", "--admin-email", email, "--source-root", str(root)]) == 0
    seeded = [courses.store.find_sample(doc_id) for doc_id in SAMPLE_DOCS]
    expected = {"doc-1": (8, 35, 223), "doc-6": (29, 2, 11), "nhap-mon-ml": (50, 15, 75),
                "naive-bayes": (49, 5, 33), "xstk-ch3-1": (68, 14, 82), "doc-4": (27, 91, 495)}
    assert {row.doc_id: row.published_graph_version for row in seeded} == {key: value[0] for key, value in expected.items()}
    assert len(media.files) == 6
    assert cli.main(["seed-samples", "--admin-email", email, "--source-root", str(root)]) == 0
    assert [courses.store.find_sample(doc_id).id for doc_id in SAMPLE_DOCS] == [row.id for row in seeded]
    assert len(media.files) == 6

    @contextmanager
    def live_client():
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        origin = f"http://127.0.0.1:{listener.getsockname()[1]}"
        courses.settings.allowed_origins.append(origin)
        server = uvicorn.Server(uvicorn.Config(courses.app, log_config=None, access_log=False))
        thread = Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
        thread.start()
        try:
            deadline = monotonic() + 10
            while not server.started and thread.is_alive() and monotonic() < deadline:
                sleep(.01)
            assert server.started
            with httpx.Client(base_url=origin, trust_env=False, timeout=20) as client:
                yield client, origin
        finally:
            server.should_exit = True
            thread.join(10)
            listener.close()
            assert not thread.is_alive(), "local HTTP server did not stop"

    snapshots = []
    with live_client() as (client, origin):
        assert client.post("/api/v1/auth/register", headers={"Origin": origin}, json={
            "email": uuid4().hex + "@example.vn", "password": "W06 TCP private passphrase!",
            "display_name": "Người học HTTP"}).status_code == 200
        identity = client.get("/api/v1/me").json()
        uid = identity["account"]["id"]
        headers = {"Origin": origin, "X-CSRF-Token": identity["csrf_token"]}
        before = client.get("/api/v1/courses")
        assert before.status_code == 200 and len(before.json()["samples"]) == 6
        for item in seeded:
            joined_item = client.post(f"/api/v1/courses/{item.id}/join-sample", headers=headers, json={"owner": "forged"})
            repeated = client.post(f"/api/v1/courses/{item.id}/join-sample", headers=headers, json={})
            roadmap_item = client.get(f"/api/v1/courses/{item.id}/roadmap")
            assert joined_item.status_code == repeated.status_code == roadmap_item.status_code == 200
            version, modules, nodes = expected[item.doc_id]
            assert roadmap_item.json()["graph_version"] == version
            assert len(roadmap_item.json()["modules"]) == modules
            assert joined_item.json()["progress"] == {"learned": 0, "total": nodes}
            snapshots.append({"doc_id": item.doc_id, "course_id": item.id, "graph_version": version,
                "module_count": modules, "learnable_nodes": nodes, "join": joined_item.json(),
                "roadmap": roadmap_item.json(), "repeat_join_status": repeated.status_code})
        course = seeded[0]
        joined = snapshots[0]["join"]
        detail = client.get(f"/api/v1/courses/{course.id}")
        roadmap = client.get(f"/api/v1/courses/{course.id}/roadmap")
        after = client.get("/api/v1/courses")
        private = client.get(f"/api/v1/courses/{courses.course.id}")
        assert after.status_code == 200 and len(after.json()["joined"]) == 6 and after.json()["samples"] == []
    assert detail.status_code == roadmap.status_code == after.status_code == 200
    assert len(roadmap.json()["modules"]) == 35
    assert joined["progress"] == {"learned": 0, "total": 223}
    assert private.status_code == 404 and private.json()["error"]["code"] == "not_found"
    with courses.engine.connect() as independent:
        assert independent.scalar(text("SELECT via FROM membership WHERE course_id=:cid AND account_id=:uid"),
                                  {"cid": course.id, "uid": uid}) == "sample"
        assert independent.scalar(text("SELECT count(*) FROM course WHERE is_sample")) == 6
        assert independent.scalar(text("SELECT count(*) FROM membership m JOIN course c ON c.id=m.course_id WHERE c.is_sample")) == 12
    evidence = root / "report/w06-evidence"
    evidence.mkdir(exist_ok=True)
    (evidence / "http-doc1.json").write_text(json.dumps({
        "label": "REAL_HTTP_POSTGRES_FAKE_MODEL_MAILER_MEDIA", "model_calls": 0,
        "transport": "TCP HTTP via uvicorn on loopback", "source": "two manifest-verified development snapshot copies",
        "get_courses_before_join": before.json(), "join_sample": joined,
        "get_course": detail.json(), "get_roadmap": roadmap.json(),
        "get_courses_after_join": after.json(), "private_course_error": private.json(),
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (evidence / "http-six-books.json").write_text(json.dumps({"label": "REAL_TCP_HTTP_POSTGRES_FAKE_PROVIDERS",
        "samples": 6, "owner_memberships": 6, "learner_memberships": 6, "model_calls": 0,
        "media_uploads_to_memory_only": len(media.files), "records": snapshots}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_deferred_owner_check_protects_source_when_owner_membership_is_moved(courses):
    new_id = str(uuid4())
    with pytest.raises(IntegrityError):
        with courses.engine.begin() as connection:
            connection.execute(text("INSERT INTO course (id,owner_id,doc_id,title,status,published_graph_version,created_at,updated_at) "
                                    "SELECT :new,owner_id,doc_id,title,status,published_graph_version,created_at,updated_at FROM course WHERE id=:old"),
                               {"new": new_id, "old": courses.course.id})
            connection.execute(text("UPDATE membership SET course_id=:new WHERE course_id=:old AND role='owner'"),
                               {"new": new_id, "old": courses.course.id})


def test_cached_graph_never_bypasses_revoked_membership(courses):
    actor, client, headers = courses.user()
    client.post(f"/api/v1/courses/{courses.sample.id}/join-sample", headers=headers, json={})
    assert len(courses.loaded) == 1
    with courses.engine.begin() as connection:
        connection.execute(text("DELETE FROM membership WHERE course_id=:cid AND account_id=:uid"),
                           {"cid": courses.sample.id, "uid": actor.user_id})
    result = client.get(f"/api/v1/courses/{courses.sample.id}/roadmap")
    assert result.status_code == 404 and result.json()["error"]["code"] == "not_found"
    assert len(courses.loaded) == 1


def test_course_progress_and_resume_are_per_actor_and_resume_resolves_module_scope(courses):
    courses.graph.nodes["b"] = {**courses.graph.nodes["a"], "node_id": "b", "module_id": "m2"}
    courses.graph.learnable_nodes["b"] = courses.graph.nodes["b"]
    courses.graph.modules["m2"] = {"module_id": "m2", "index": 2, "title": "Tiếp theo", "node_ids": ["b"]}
    actor, client, headers = courses.user()
    client.post(f"/api/v1/courses/{courses.sample.id}/join-sample", headers=headers, json={})
    learner = courses.gateway.learner(actor, courses.sample.id)
    assert courses.service.get_course(actor, courses.sample.id)["resume"] == {"module_id": "m1"}
    learner.sessions.create_session(actor.user_id, "doc-1", {"kind": "module", "node_ids": ["b"],
        "module_id_at_creation": "m2", "graph_version_at_creation": 8})
    learner.progress.set_progress(actor.user_id, "doc-1", "a", True)
    summary = courses.service.get_course(actor, courses.sample.id)
    assert summary["resume"] == {"module_id": "m2"}
    assert summary["progress"] == {"learned": 1, "total": 2}
    assert courses.service.get_course(courses.owner, courses.sample.id)["progress"] == {"learned": 0, "total": 2}


def test_graph_is_pinned_to_course_version_and_cached_by_doc_version(courses):
    from copy import deepcopy
    old = courses.gateway.get_roadmap(courses.owner, courses.course.id)
    assert old["graph_version"] == 8
    courses.gateway.get_roadmap(courses.owner, courses.sample.id)
    assert courses.loaded == [("doc-1", 8)]
    with courses.engine.begin() as connection:
        connection.execute(text("UPDATE course SET published_graph_version=9 WHERE id=:cid"), {"cid": courses.sample.id})
    def newer(doc_id, version):
        courses.loaded.append((doc_id, version))
        graph = deepcopy(courses.graph)
        graph.graph_version = version
        return graph
    courses.gateway.graph_loader = newer
    assert courses.gateway.get_roadmap(courses.owner, courses.sample.id)["graph_version"] == 9
    assert courses.gateway.get_roadmap(courses.owner, courses.course.id)["graph_version"] == 8
    assert courses.loaded == [("doc-1", 8), ("doc-1", 9)]


def test_w06_migration_is_single_head_after_w03_and_empty_database_upgrades(courses):
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    from sqlalchemy import inspect
    config = Config()
    config.set_main_option("script_location", str(Path(__file__).parents[1] / "wayfinder/migrations"))
    scripts = ScriptDirectory.from_config(config)
    assert scripts.get_heads() == ["w06_0005"]
    assert scripts.get_revision("w06_0005").down_revision == "w03_0004"
    assert {"course", "membership"} <= set(inspect(courses.engine).get_table_names())
    with courses.engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "w06_0005"


def test_fixture_copy_refuses_escape_hardlink_and_dangling_reparse_point(tmp_path, monkeypatch):
    import stat
    from copy_w06_fixtures import safe_path
    with pytest.raises(ValueError, match="escapes"):
        safe_path(tmp_path, "../outside")
    missing = tmp_path / "not-created"
    original = Path.lstat
    # Simulate metadata only: this test never creates a link of any kind.
    metadata = SimpleNamespace(st_mode=stat.S_IFREG, st_nlink=2, st_file_attributes=0)
    def lstat(path, *args, **kwargs):
        return metadata if path == missing else original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "lstat", lstat)
    with pytest.raises(ValueError, match="hardlinked"):
        safe_path(tmp_path, missing.name)
    metadata.st_nlink = 1
    metadata.st_file_attributes = stat.FILE_ATTRIBUTE_REPARSE_POINT
    with pytest.raises(ValueError, match="linked path"):
        safe_path(tmp_path, missing.name)
