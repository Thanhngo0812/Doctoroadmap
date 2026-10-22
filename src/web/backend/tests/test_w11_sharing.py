from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4
from types import SimpleNamespace
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
import base64
import hashlib
from sqlalchemy import text
from fastapi.testclient import TestClient

from wayfinder.api.app import create_app
from wayfinder.api.auth import get_actor
from wayfinder.composition import WebServices
from wayfinder.application.sharing import SharingService
from wayfinder.domain.auth import Actor
from wayfinder.domain.courses import Course, Membership
from wayfinder.domain.sharing import ShareMember
from wayfinder.api.errors import WebError


class Clock:
    def __init__(self):
        self.value = datetime(2026, 10, 21, tzinfo=timezone.utc)

    def now(self):
        return self.value


class MemoryStore:
    def __init__(self, owner_id, learner_id=None):
        self.course_id = str(uuid4())
        self.owner_id = owner_id
        self.course = Course(self.course_id, owner_id, "doc-demo", "Khoá thử", "", "ready", 1,
                             False, 2, None, datetime(2026, 10, 1, tzinfo=timezone.utc),
                             datetime(2026, 10, 1, tzinfo=timezone.utc))
        self.members = {owner_id: Membership(self.course_id, owner_id, "owner", "owner",
            datetime(2026, 10, 1, tzinfo=timezone.utc), None)}
        if learner_id:
            self.members[learner_id] = Membership(self.course_id, learner_id, "learner", "link",
                datetime(2026, 10, 2, tzinfo=timezone.utc), None)
        self.links = {}
        self.audits = []

    class _Atomic:
        def __enter__(self): return self
        def __exit__(self, *_): return False

    def atomic(self): return self._Atomic()
    def get_course(self, cid, *, for_update=False): return self.course if cid == self.course_id else None
    def get_membership(self, cid, uid): return self.members.get(uid) if cid == self.course_id else None
    def get_link_by_hash(self, token_hash, *, for_update=False):
        return next((link for link in self.links.values() if link.token_hash == token_hash), None)
    def get_link(self, cid, lid, *, for_update=False):
        link = self.links.get(lid)
        return link if link and link.course_id == cid else None
    def list_links(self, cid): return [link for link in self.links.values() if link.course_id == cid]
    def add_link(self, link): self.links[link.id] = link
    def revoke_link(self, lid, at):
        from dataclasses import replace
        self.links[lid] = replace(self.links[lid], revoked_at=at)
    def member_count(self, cid): return len(self.members) if cid == self.course_id else 0
    def owner_summary(self, uid): return {"user_id": uid, "display_name": "Chủ khoá"}
    def list_members(self, cid):
        return [ShareMember(member.account_id, "Chủ khoá" if member.role == "owner" else "Người học",
                            member.role, member.joined_at, member.last_active_at, member.via)
                for member in self.members.values()] if cid == self.course_id else []
    def add_membership(self, member):
        if member.account_id in self.members: return False
        self.members[member.account_id] = member
        return True
    def remove_membership(self, cid, uid): return self.members.pop(uid, None) is not None
    def increment_use_count(self, lid, max_uses):
        from dataclasses import replace
        link = self.links[lid]
        if max_uses is not None and link.use_count >= max_uses: return False
        self.links[lid] = replace(link, use_count=link.use_count + 1)
        return True
    def append_audit(self, event): self.audits.append(event)
    def concept_count(self, cid): return 4 if cid == self.course_id else 0


def owner_actor(user_id): return Actor(user_id, "user", False, "active")
def learner_actor(user_id): return Actor(user_id, "user", False, "active")


def test_share_link_token_is_one_time_and_never_returned_by_list():
    owner_id = str(uuid4())
    store, clock = MemoryStore(owner_id), Clock()
    service = SharingService(store, settings=type("Settings", (), {
        "share_link_default_days": 7, "course_max_members": 200,
        "public_base_url": "https://learn.example.vn"})(), clock=clock)

    result = service.create_share_link(owner_actor(owner_id), store.course_id)

    token = result["link"]["token"]
    assert len(__import__("base64").urlsafe_b64decode(token + "=")) == 32
    assert result["link"]["url"] == f"https://learn.example.vn/join/{token}"
    assert result["link"]["expires_at"] == (clock.now() + timedelta(days=7)).isoformat()
    assert store.links[result["link"]["id"]].token_hash != token.encode()
    listed = service.list_share_links(owner_actor(owner_id), store.course_id)
    assert token not in repr(listed)
    assert listed["items"][0]["token_tail"] == token[-6:]


def test_one_use_link_allows_existing_member_repeat_but_preview_and_new_member_are_invalid():
    owner_id, learner_id, outsider_id = (str(uuid4()) for _ in range(3))
    store, clock = MemoryStore(owner_id), Clock()
    service = SharingService(store, settings=type("Settings", (), {
        "share_link_default_days": 7, "course_max_members": 200,
        "public_base_url": "https://learn.example.vn"})(), clock=clock)
    token = service.create_share_link(owner_actor(owner_id), store.course_id, max_uses=1)["link"]["token"]

    first = service.join_by_link(learner_actor(learner_id), token)
    repeated = service.join_by_link(learner_actor(learner_id), token)

    assert first["already_member"] is False
    assert repeated["already_member"] is True
    assert repeated["role"] == "learner"
    assert store.links[next(iter(store.links))].use_count == 1
    owner_repeat = service.join_by_link(owner_actor(owner_id), token)
    assert owner_repeat["already_member"] is True
    assert owner_repeat["role"] == "owner"
    for invalid in (
        lambda: service.preview_share_link(token),
        lambda: service.join_by_link(learner_actor(outsider_id), token),
    ):
        with pytest.raises(WebError) as error:
            invalid()
        assert (error.value.code, error.value.status_code, error.value.message) == (
            "link_invalid", 410, "Link tham gia không hợp lệ hoặc đã hết hạn.")


def test_revoked_or_expired_link_is_invalid_even_for_an_existing_member():
    owner_id, learner_id = str(uuid4()), str(uuid4())
    store, clock = MemoryStore(owner_id, learner_id), Clock()
    service = SharingService(store, settings=type("Settings", (), {
        "share_link_default_days": 7, "course_max_members": 200,
        "public_base_url": "https://learn.example.vn"})(), clock=clock)
    revoked = service.create_share_link(owner_actor(owner_id), store.course_id)["link"]["token"]
    revoked_id = next(iter(store.links))
    service.revoke_share_link(owner_actor(owner_id), store.course_id, revoked_id)
    expired = service.create_share_link(owner_actor(owner_id), store.course_id, expires_in_days=1)["link"]["token"]
    clock.value += timedelta(days=1)
    for token in (revoked, expired):
        with pytest.raises(WebError) as error:
            service.join_by_link(learner_actor(learner_id), token)
        assert error.value.code == "link_invalid"


def test_all_invalid_preview_reasons_have_the_same_error_envelope_fields():
    owner_id, learner_id = str(uuid4()), str(uuid4())
    store, clock = MemoryStore(owner_id), Clock()
    service = SharingService(store, settings=type("Settings", (), {
        "share_link_default_days": 7, "course_max_members": 200,
        "public_base_url": "https://learn.example.vn"})(), clock=clock)
    exhausted = service.create_share_link(owner_actor(owner_id), store.course_id, max_uses=1)["link"]["token"]
    service.join_by_link(learner_actor(learner_id), exhausted)
    expired = service.create_share_link(owner_actor(owner_id), store.course_id, expires_in_days=1)["link"]["token"]
    revoked = service.create_share_link(owner_actor(owner_id), store.course_id)["link"]["token"]
    revoked_id = next(link.id for link in store.links.values() if link.token_tail == revoked[-6:])
    service.revoke_share_link(owner_actor(owner_id), store.course_id, revoked_id)
    clock.value += timedelta(days=1)
    invalid_tokens = [exhausted, expired, revoked, "x" * 43]
    envelopes = []
    for token in invalid_tokens:
        with pytest.raises(WebError) as error:
            service.preview_share_link(token)
        envelopes.append((error.value.code, error.value.status_code, error.value.message, error.value.fields))
    assert len(set(envelopes)) == 1


def test_course_capacity_rejects_new_member_without_consuming_link_use():
    owner_id = str(uuid4())
    store, clock = MemoryStore(owner_id), Clock()
    for _ in range(199):
        uid = str(uuid4())
        store.members[uid] = Membership(store.course_id, uid, "learner", "link", clock.now(), clock.now())
    service = SharingService(store, settings=type("Settings", (), {
        "share_link_default_days": 7, "course_max_members": 200,
        "public_base_url": "https://learn.example.vn"})(), clock=clock)
    token = service.create_share_link(owner_actor(owner_id), store.course_id)["link"]["token"]
    with pytest.raises(WebError) as error:
        service.join_by_link(learner_actor(str(uuid4())), token)
    assert (error.value.code, error.value.status_code) == ("course_full", 409)
    assert store.links[next(iter(store.links))].use_count == 0


def test_preview_has_only_public_course_summary_and_member_views_are_role_limited():
    owner_id, learner_id = str(uuid4()), str(uuid4())
    store, clock = MemoryStore(owner_id, learner_id), Clock()
    service = SharingService(store, settings=type("Settings", (), {
        "share_link_default_days": 7, "course_max_members": 200,
        "public_base_url": "https://learn.example.vn"})(), clock=clock)
    token = service.create_share_link(owner_actor(owner_id), store.course_id)["link"]["token"]

    assert service.preview_share_link(token) == {
        "course_id": store.course_id, "title": "Khoá thử", "owner": {"display_name": "Chủ khoá"},
        "module_count": 2, "concept_count": 4,
    }
    owner_view = service.list_members(owner_actor(owner_id), store.course_id)
    learner_view = service.list_members(learner_actor(learner_id), store.course_id)
    assert owner_view["owner"] == learner_view["owner"] == {"user_id": owner_id, "display_name": "Chủ khoá"}
    assert owner_view["member_count"] == learner_view["member_count"] == 2
    assert len(owner_view["members"]) == 2
    assert "members" not in learner_view
    with pytest.raises(WebError) as error:
        service.leave_course(owner_actor(owner_id), store.course_id)
    assert error.value.code == "forbidden"


@pytest.mark.parametrize("expires,max_uses", [(0, None), (10**12, None), (None, 0), (None, 2**31)])
def test_link_limits_reject_invalid_values_as_validation(expires, max_uses):
    owner_id = str(uuid4())
    store, clock = MemoryStore(owner_id), Clock()
    service = SharingService(store, settings=type("Settings", (), {
        "share_link_default_days": 7, "course_max_members": 200,
        "public_base_url": "https://learn.example.vn"})(), clock=clock)
    kwargs = {"expires_in_days": expires, "max_uses": max_uses}
    with pytest.raises(WebError) as error:
        service.create_share_link(owner_actor(owner_id), store.course_id, **kwargs)
    assert error.value.code == "validation"


def test_http_contract_csrf_private_access_and_token_privacy():
    from wayfinder.settings import WebSettings

    owner_id, learner_id, outsider_id = (str(uuid4()) for _ in range(3))
    store, clock = MemoryStore(owner_id), Clock()
    settings = WebSettings(_env_file=None, frontend_dist=Path("missing"), allowed_origins=["http://testserver"],
                           public_base_url="http://testserver")
    sharing = SharingService(store, settings, clock)

    class Accounts:
        def me(self, _token):
            return SimpleNamespace(account=SimpleNamespace(id=owner_id),
                                   session=SimpleNamespace(csrf_token="test-csrf"))

    def client_for(actor):
        app = create_app(settings, WebServices(health_check=lambda: "ok", accounts=Accounts(), sharing=sharing))
        app.dependency_overrides[get_actor] = lambda: actor
        client = TestClient(app)
        client.cookies.set("d2r_session", "test-session")
        return client

    owner = client_for(owner_actor(owner_id))
    created = owner.post(f"/api/v1/courses/{store.course_id}/share-links", headers={
        "Origin": "http://testserver", "X-CSRF-Token": "test-csrf"}, json={"max_uses": 2})
    assert created.status_code == 200, created.text
    token = created.json()["link"]["token"]
    assert created.json()["link"]["url"].endswith("/join/" + token)
    assert created.headers["cache-control"] == "no-store"
    assert created.headers["referrer-policy"] == "no-referrer"

    preview = owner.get(f"/api/v1/join/{token}")
    assert preview.status_code == 200
    assert preview.headers["cache-control"] == "no-store"
    assert preview.headers["referrer-policy"] == "no-referrer"
    assert "user_id" not in preview.json()["owner"]
    listed = owner.get(f"/api/v1/courses/{store.course_id}/share-links").json()
    assert token not in repr(listed)

    no_csrf = owner.post(f"/api/v1/join/{token}", headers={"Origin": "http://testserver"})
    assert no_csrf.status_code == 403 and no_csrf.json()["error"]["code"] == "csrf_failed"
    learner = client_for(learner_actor(learner_id))
    joined = learner.post(f"/api/v1/join/{token}", headers={
        "Origin": "http://testserver", "X-CSRF-Token": "test-csrf"})
    assert joined.status_code == 200 and joined.json()["already_member"] is False
    member_view = learner.get(f"/api/v1/courses/{store.course_id}/members").json()
    assert member_view["owner"]["user_id"] == owner_id
    assert member_view["member_count"] == 2
    assert "members" not in member_view
    owner_members = owner.get(f"/api/v1/courses/{store.course_id}/members").json()
    assert len(owner_members["members"]) == 2
    removed = owner.delete(f"/api/v1/courses/{store.course_id}/members/{learner_id}", headers={
        "Origin": "http://testserver", "X-CSRF-Token": "test-csrf"})
    assert removed.status_code == 200
    inaccessible = learner.get(f"/api/v1/courses/{store.course_id}/members")
    assert inaccessible.status_code == 404 and inaccessible.json()["error"]["code"] == "not_found"
    rejoined = learner.post(f"/api/v1/join/{token}", headers={
        "Origin": "http://testserver", "X-CSRF-Token": "test-csrf"})
    assert rejoined.status_code == 200
    left = learner.post(f"/api/v1/courses/{store.course_id}/leave", headers={
        "Origin": "http://testserver", "X-CSRF-Token": "test-csrf"})
    assert left.status_code == 200
    assert store.member_count(store.course_id) == 1

    revocable = owner.post(f"/api/v1/courses/{store.course_id}/share-links", headers={
        "Origin": "http://testserver", "X-CSRF-Token": "test-csrf"}, json={})
    revocable_link = revocable.json()["link"]
    revoked = owner.delete(f"/api/v1/courses/{store.course_id}/share-links/{revocable_link['id']}", headers={
        "Origin": "http://testserver", "X-CSRF-Token": "test-csrf"})
    assert revoked.status_code == 200
    invalid_preview = owner.get(f"/api/v1/join/{revocable_link['token']}")
    assert invalid_preview.status_code == 410 and invalid_preview.json()["error"]["code"] == "link_invalid"

    outsider = client_for(owner_actor(outsider_id))
    private = outsider.get(f"/api/v1/courses/{store.course_id}/members")
    assert private.status_code == 404 and private.json()["error"]["code"] == "not_found"


@pytest.fixture
def sharing_pg(postgres_database_url):
    from sqlalchemy import text
    from wayfinder.application.courses import CourseService
    from wayfinder.infrastructure.course_store import PostgresCourseStore
    from wayfinder.infrastructure.database import create_database_engine
    from wayfinder.infrastructure.sharing_store import PostgresSharingStore
    from wayfinder.settings import WebSettings

    engine = create_database_engine(postgres_database_url)
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == 'w11_0007'
        assert connection.scalar(text("SELECT to_regclass('public.share_link')")) == 'share_link'
    settings = WebSettings(_env_file=None, frontend_dist=Path("missing"), public_base_url="https://learn.example.vn")
    clock = Clock()

    def user(name):
        account_id = str(uuid4())
        now = clock.now()
        with engine.begin() as connection:
            connection.execute(text("INSERT INTO account (id,email,email_normalized,password_hash,display_name,"
                "created_at,updated_at) VALUES (:id,:email,:norm,'test-hash',:name,:at,:at)"),
                {"id": account_id, "email": account_id + "@example.vn", "norm": account_id + "@example.vn",
                 "name": name, "at": now})
        return Actor(account_id, "user", False, "active")

    owner = user("Chủ khoá")
    courses = CourseService(PostgresCourseStore(engine), settings=settings, clock=clock)
    course = courses.create_course(owner, doc_id="doc-w11", title="Khoá chia sẻ", graph_version=1, module_count=2)
    yield SimpleNamespace(engine=engine, settings=settings, clock=clock, owner=owner, course=course,
                          user=user, store=PostgresSharingStore(engine))
    engine.dispose()


@pytest.mark.postgres
def test_postgres_one_use_join_race_counts_exactly_one_member_and_use(sharing_pg):
    from wayfinder.application.sharing import SharingService

    service = SharingService(sharing_pg.store, sharing_pg.settings, sharing_pg.clock,
                             graph_loader=lambda *_: SimpleNamespace(learnable_nodes={}))
    token = service.create_share_link(sharing_pg.owner, sharing_pg.course.id, max_uses=1)["link"]["token"]
    users = [sharing_pg.user("Người học 1"), sharing_pg.user("Người học 2")]
    gate = Barrier(2)

    def join(actor):
        local_service = SharingService(type(sharing_pg.store)(sharing_pg.engine), sharing_pg.settings, sharing_pg.clock)
        gate.wait(timeout=5)
        try:
            return local_service.join_by_link(actor, token)
        except WebError as error:
            return error.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(join, users))

    assert sum(isinstance(item, dict) and not item["already_member"] for item in results) == 1
    assert results.count("link_invalid") == 1
    with sharing_pg.engine.connect() as connection:
        members = connection.scalar(text("SELECT count(*) FROM membership WHERE course_id=:cid AND role='learner'"),
                                    {"cid": sharing_pg.course.id})
        uses = connection.scalar(text("SELECT use_count FROM share_link WHERE token_hash=:hash"),
                                 {"hash": hashlib.sha256(base64.urlsafe_b64decode(token + "=")).digest()})
        joined_audits = connection.scalar(text("SELECT count(*) FROM audit_event WHERE action='member_joined' "
            "AND target_id=:cid"), {"cid": sharing_pg.course.id})
    assert (members, uses, joined_audits) == (1, 1, 1)


@pytest.mark.postgres
def test_postgres_create_and_join_rollback_when_audit_write_fails(sharing_pg, monkeypatch):
    from wayfinder.application.sharing import SharingService

    service = SharingService(sharing_pg.store, sharing_pg.settings, sharing_pg.clock,
                             graph_loader=lambda *_: SimpleNamespace(learnable_nodes={}))
    original_append = sharing_pg.store.append_audit

    def fail_audit(_event):
        raise RuntimeError("audit unavailable")

    monkeypatch.setattr(sharing_pg.store, "append_audit", fail_audit)
    with pytest.raises(RuntimeError, match="audit unavailable"):
        service.create_share_link(sharing_pg.owner, sharing_pg.course.id, max_uses=1)
    with sharing_pg.engine.connect() as connection:
        assert connection.scalar(text("SELECT count(*) FROM share_link WHERE course_id=:cid"),
                                 {"cid": sharing_pg.course.id}) == 0

    monkeypatch.setattr(sharing_pg.store, "append_audit", original_append)
    token = service.create_share_link(sharing_pg.owner, sharing_pg.course.id, max_uses=1)["link"]["token"]
    learner = sharing_pg.user("Người học")
    monkeypatch.setattr(sharing_pg.store, "append_audit", fail_audit)
    with pytest.raises(RuntimeError, match="audit unavailable"):
        service.join_by_link(learner, token)
    with sharing_pg.engine.connect() as connection:
        assert connection.scalar(text("SELECT count(*) FROM membership WHERE course_id=:cid AND account_id=:uid"),
                                 {"cid": sharing_pg.course.id, "uid": learner.user_id}) == 0
        assert connection.scalar(text("SELECT use_count FROM share_link WHERE token_hash=:hash"),
                                 {"hash": hashlib.sha256(base64.urlsafe_b64decode(token + "=")).digest()}) == 0


@pytest.mark.postgres
def test_postgres_remove_and_rejoin_preserve_phase_b_progress_and_revoke_keeps_members(sharing_pg):
    from sqlalchemy import text
    from wayfinder.application.sharing import SharingService

    service = SharingService(sharing_pg.store, sharing_pg.settings, sharing_pg.clock,
                             graph_loader=lambda *_: SimpleNamespace(learnable_nodes={}))
    learner = sharing_pg.user("Người học")
    token = service.create_share_link(sharing_pg.owner, sharing_pg.course.id)["link"]["token"]
    service.join_by_link(learner, token)
    with sharing_pg.engine.begin() as connection:
        connection.execute(text("INSERT INTO phase_b_record (kind,record_id,owner,doc_id,value,updated_at) "
            "VALUES ('progress',:record,:owner,'doc-w11',CAST(:value AS jsonb),:at)"), {
                "record": "w11:" + learner.user_id, "owner": learner.user_id,
                "value": '{"node_id":"n1","state":"learned"}', "at": sharing_pg.clock.now()})
    link_id = service.list_share_links(sharing_pg.owner, sharing_pg.course.id)["items"][0]["id"]
    service.revoke_share_link(sharing_pg.owner, sharing_pg.course.id, link_id)
    assert service.list_members(sharing_pg.owner, sharing_pg.course.id)["member_count"] == 2
    service.remove_member(sharing_pg.owner, sharing_pg.course.id, learner.user_id)
    with pytest.raises(WebError) as removed:
        service.list_members(learner, sharing_pg.course.id)
    assert removed.value.code == 'not_found'
    with sharing_pg.engine.connect() as connection:
        retained = connection.scalar(text("SELECT count(*) FROM phase_b_record WHERE owner=:owner AND doc_id='doc-w11'"),
                                     {"owner": learner.user_id})
    assert retained == 1
    replacement = service.create_share_link(sharing_pg.owner, sharing_pg.course.id)["link"]["token"]
    service.join_by_link(learner, replacement)
    with sharing_pg.engine.connect() as connection:
        restored = connection.scalar(text("SELECT count(*) FROM phase_b_record WHERE owner=:owner AND doc_id='doc-w11'"),
                                     {"owner": learner.user_id})
    assert restored == retained


@pytest.mark.postgres
def test_postgres_migration_has_no_raw_token_and_enforces_digest_length(sharing_pg):
    from sqlalchemy import inspect
    from sqlalchemy.exc import IntegrityError
    b = sharing_pg
    columns = {column['name'] for column in inspect(b.engine).get_columns('share_link')}
    assert 'token' not in columns and 'url' not in columns
    assert {'token_hash', 'token_tail'} <= columns
    with pytest.raises(IntegrityError):
        with b.engine.begin() as c:
            c.execute(text('INSERT INTO share_link(id,course_id,token_hash,token_tail,created_at) '
                'VALUES (:id,:cid,:hash,:tail,:at)'),
                dict(id=str(uuid4()),cid=b.course.id,hash=b'short',tail='123456',at=b.clock.now()))


@pytest.mark.postgres
@pytest.mark.parametrize('action', ['remove', 'leave'])
def test_postgres_rejoin_retains_exact_private_session_and_progress(sharing_pg, action):
    from wayfinder.infrastructure.phase_b_store import PostgresPhaseBStore
    b=sharing_pg
    learner=b.user('Returning learner')
    service=SharingService(b.store,b.settings,b.clock)
    token=service.create_share_link(b.owner,b.course.id)['link']['token']
    service.join_by_link(learner,token)
    phase=PostgresPhaseBStore(b.engine)
    records={
        'session': {'owner':learner.user_id,'doc_id':'doc-w11','session_id':str(uuid4()),'title':'Private study session'},
        'progress': {'owner':learner.user_id,'doc_id':'doc-w11','node_id':'n1','state':'learned'},
    }
    try:
        for kind,value in records.items(): phase.put_record(kind,learner.user_id+':'+kind,value)
        if action=='remove': service.remove_member(b.owner,b.course.id,learner.user_id)
        else: service.leave_course(learner,b.course.id)
        with pytest.raises(WebError) as denied: service.list_members(learner,b.course.id)
        assert denied.value.code=='not_found'
        service.join_by_link(learner,token)
        for kind,value in records.items():
            assert phase.get_record(kind,learner.user_id+':'+kind)==value
        with b.engine.connect() as c:
            assert c.scalar(text('SELECT use_count FROM share_link WHERE course_id=:cid'),{'cid':b.course.id})==2
    finally: phase.close()


@pytest.mark.postgres
def test_postgres_capacity_race_across_two_links_stops_at_200(sharing_pg):
    b = sharing_pg
    # 198 learners plus the owner leave exactly one free place.
    with b.engine.begin() as c:
        for _ in range(198):
            uid=str(uuid4())
            c.execute(text("INSERT INTO account(id,email,email_normalized,password_hash,display_name,created_at,updated_at) "
                "VALUES (:id,:email,:email,'test','Fixture',:at,:at)"),
                dict(id=uid,email=uid+'@example.invalid',at=b.clock.now()))
            c.execute(text("INSERT INTO membership(course_id,account_id,role,via,joined_at) "
                "VALUES (:cid,:uid,'learner','link',:at)"),dict(cid=b.course.id,uid=uid,at=b.clock.now()))
    service=SharingService(b.store,b.settings,b.clock)
    tokens=[service.create_share_link(b.owner,b.course.id)['link']['token'] for _ in range(2)]
    users=[b.user('Contender') for _ in range(2)]
    barrier=Barrier(2)
    def join(pair):
        actor,token=pair
        local=SharingService(type(b.store)(b.engine),b.settings,b.clock)
        barrier.wait(timeout=5)
        try: return local.join_by_link(actor,token)
        except WebError as e: return e.code
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(join,zip(users,tokens)))
    assert results.count('course_full')==1
    assert sum(isinstance(x,dict) for x in results)==1
    with b.engine.connect() as c:
        assert c.scalar(text('SELECT count(*) FROM membership WHERE course_id=:cid'),{'cid':b.course.id})==200
        assert c.scalar(text('SELECT sum(use_count) FROM share_link WHERE course_id=:cid'),{'cid':b.course.id})==1

