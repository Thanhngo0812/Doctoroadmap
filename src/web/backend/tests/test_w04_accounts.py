"""W-04: identical service and HTTP assertions against fake and PostgreSQL auth stores."""
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import select

from test_auth_store import auth_database
from test_w03_auth_http import token_from_message
from wayfinder.api.app import create_app
from wayfinder.application.accounts import AuthError
from wayfinder.settings import WebSettings
from wayfinder.testing import build_test_application


ORIGIN = "https://testserver"
PASSWORD = "W04 synthetic original passphrase!"
NEW_PASSWORD = "W04 synthetic replacement passphrase!"


@pytest.fixture(params=["fake", "postgres"])
def runtime(request, monkeypatch):
    bundle = build_test_application()
    service = bundle.services.accounts
    if request.param == "postgres":
        service.store = request.getfixturevalue("auth_database")[0]
    forbidden_calls = []

    def forbidden(*args, **kwargs):
        forbidden_calls.append(True)
        raise AssertionError("W-04 forbids external provider/ADC/SMTP/media calls")

    for target in (
        "doc2roadmap.infrastructure.llm.gemini.urlopen",
        "doc2roadmap.infrastructure.embedding.gemini.urlopen",
        "doc2roadmap.infrastructure.google_auth.VertexCredentials.headers",
        "smtplib.SMTP", "cloudinary.uploader.upload",
    ):
        monkeypatch.setattr(target, forbidden)
    app = create_app(WebSettings(_env_file=None, frontend_dist=Path("missing"),
                                allowed_origins=[ORIGIN]), bundle.services)
    with TestClient(app, base_url=ORIGIN) as a, TestClient(app, base_url=ORIGIN) as b, \
            TestClient(app, base_url=ORIGIN) as other:
        register(a, "w04@example.vn")
        assert login(b).status_code == 200
        register(other, "other-w04@example.vn")
        assert a.cookies.get("d2r_session") != b.cookies.get("d2r_session")
        yield service, a, b, other, bundle
    assert forbidden_calls == []
    assert bundle.phase_b.model.json_calls == bundle.phase_b.model.tool_calls == []
    assert bundle.phase_b.embedding.requests == []
    assert len(bundle.mailer.messages) >= 2  # Fake registration mail, never SMTP.


def register(client, email):
    result = client.post("/api/v1/auth/register", headers={"Origin": ORIGIN}, json={
        "email": email, "password": PASSWORD, "display_name": "Người học"})
    assert result.status_code == 200


def login(client, password=PASSWORD):
    return client.post("/api/v1/auth/login", headers={"Origin": ORIGIN},
                       json={"email": "w04@example.vn", "password": password})


def headers(client):
    return {"Origin": ORIGIN, "X-CSRF-Token": client.get("/api/v1/me").json()["csrf_token"]}


def change(client, **extra):
    return client.post("/api/v1/me/password", headers=headers(client), json={
        "current_password": PASSWORD, "new_password": NEW_PASSWORD, **extra})


def audit(service):
    store = service.store
    if hasattr(store, "audit_events"):
        return [vars_event(event) for event in store.audit_events]
    with store.engine.connect() as connection:
        return [dict(row) for row in connection.execute(select(store._table("audit_event"))).mappings()]


def vars_event(event):
    return {name: getattr(event, name) for name in ("actor_id", "action", "target_kind", "target_id", "ip", "meta")}


def snapshot(service):
    credentials = service.store.get_credentials("w04@example.vn")
    return credentials.password_hash, credentials.account.updated_at, audit(service)


def assert_unauthenticated(client):
    response = client.get("/api/v1/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"


def test_profile_trim_boundaries_persist_and_preserve_identity(runtime):
    service, a, b, other, _ = runtime
    before = a.get("/api/v1/me").json()
    original = service.store.get_credentials("w04@example.vn")
    for name in ("  An  ", "  " + "Đ" * 60 + "  ", " x "):
        result = a.patch("/api/v1/me", headers=headers(a), json={"display_name": name})
        assert result.status_code == 200
        expected = {**before, "account": {**before["account"], "display_name": name.strip()}}
        assert result.json() == expected
        assert b.get("/api/v1/me").json()["account"] == expected["account"]
        stored = service.store.get_credentials("w04@example.vn")
        assert stored.account.display_name == name.strip()
        assert stored.password_hash == original.password_hash
        assert stored.account.role == original.account.role == "user"
        assert stored.account.email == original.account.email
        assert other.get("/api/v1/me").json()["account"]["display_name"] == "Người học"
        assert result.headers["cache-control"] == "no-store"
    record("profile", result)


@pytest.mark.parametrize("name", ["", "   ", "x" * 61])
def test_profile_validation_fields_without_mutation(runtime, name):
    service, a, b, _, _ = runtime
    previous = a.get("/api/v1/me").json()
    response = a.patch("/api/v1/me", headers=headers(a), json={"display_name": name})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation"
    assert response.json()["error"]["fields"][0]["loc"] == "body.display_name"
    assert a.get("/api/v1/me").json() == previous
    assert b.get("/api/v1/me").status_code == 200
    record("profile-validation", response)


@pytest.mark.parametrize("extra", [{"role": "admin"}, {"email": "other-w04@example.vn"},
                                   {"owner": "other-account"}, {"account_id": "other-account"}])
def test_profile_rejects_mass_assignment(runtime, extra):
    _, a, _, other, _ = runtime
    before = a.get("/api/v1/me").json()
    other_before = other.get("/api/v1/me").json()
    result = a.patch("/api/v1/me", headers=headers(a), json={"display_name": "Attacker", **extra})
    assert result.status_code == 422
    assert result.json()["error"]["code"] == "validation"
    assert a.get("/api/v1/me").json() == before
    assert other.get("/api/v1/me").json() == other_before


def test_wrong_current_password_leaves_hash_sessions_and_audit_unchanged(runtime):
    service, a, b, _, _ = runtime
    before = snapshot(service)
    result = change(a, current_password="incorrect synthetic password")
    assert result.status_code == 401
    assert result.json()["error"]["code"] == "invalid_credentials"
    assert snapshot(service) == before
    assert a.get("/api/v1/me").status_code == b.get("/api/v1/me").status_code == 200
    assert service.hasher.verify(before[0], PASSWORD)
    assert not service.hasher.verify(before[0], NEW_PASSWORD)
    record("wrong-current-password", result)


@pytest.mark.parametrize("password", ["short", "x" * 129, "password"])
def test_new_password_uses_w02_policy_without_mutation(runtime, password):
    service, a, b, _, _ = runtime
    before = snapshot(service)
    response = change(a, new_password=password)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation"
    expected_location = "new_password" if password == "password" else "body.new_password"
    assert response.json()["error"]["fields"][0]["loc"] == expected_location
    assert snapshot(service) == before
    assert b.get("/api/v1/me").status_code == 200
    record("new-password-validation", response)


def test_change_keeps_a_revokes_b_checks_hash_login_and_audit(runtime):
    service, a, b, other, _ = runtime
    raw_a, raw_b = a.cookies.get("d2r_session"), b.cookies.get("d2r_session")
    before = snapshot(service)
    result = change(a)
    assert result.status_code == 200
    assert result.headers["cache-control"] == "no-store"
    assert a.cookies.get("d2r_session") == raw_a
    assert a.get("/api/v1/me").status_code == other.get("/api/v1/me").status_code == 200
    assert_unauthenticated(b)
    # Replaying B's original cookie cannot bypass revocation.
    assert b.get("/api/v1/me", headers={"Cookie": f"d2r_session={raw_b}"}).status_code == 401
    credentials = service.store.get_credentials("w04@example.vn")
    assert credentials.password_hash.startswith("$argon2id$")
    assert credentials.password_hash != before[0]
    assert service.hasher.verify(credentials.password_hash, NEW_PASSWORD)
    assert not service.hasher.verify(credentials.password_hash, PASSWORD)
    assert login(b).status_code == 401
    assert login(b, NEW_PASSWORD).status_code == 200
    events = [event for event in audit(service) if event["action"] == "password_changed"]
    assert len(events) == 1
    owner = credentials.account.id
    assert events[0]["actor_id"] == events[0]["target_id"] == owner
    assert events[0]["target_kind"] == "account" and events[0]["meta"] == {}
    assert PASSWORD not in json.dumps(events, default=str) and NEW_PASSWORD not in json.dumps(events, default=str)
    record("password-changed", result)
    record_audit(events)


@pytest.mark.parametrize("path,payload", [("/me/password", {"current_password": PASSWORD, "new_password": NEW_PASSWORD}),
                                          ("/auth/logout-all", {})])
def test_session_owner_body_forgery_rejected(runtime, path, payload):
    service, a, b, other, _ = runtime
    raw_b = b.cookies.get("d2r_session")
    session_b = service.store.get_session(hashlib.sha256(raw_b.encode()).digest())
    owner = other.get("/api/v1/me").json()["account"]["id"]
    before = snapshot(service)
    result = a.post("/api/v1" + path, headers=headers(a), json={**payload, "session_id": session_b.id, "owner": owner})
    assert result.status_code == 422
    assert result.json()["error"]["code"] == "validation"
    assert snapshot(service) == before
    for client in (a, b, other):
        assert client.get("/api/v1/me").status_code == 200


def test_logout_all_revokes_a_b_preserves_other_and_cookie_security(runtime):
    service, a, b, other, _ = runtime
    old_cookies = [client.cookies.get("d2r_session") for client in (a, b)]
    old_headers = [headers(client) for client in (a, b)]
    owner = a.get("/api/v1/me").json()["account"]["id"]
    result = a.post("/api/v1/auth/logout-all", headers=headers(a))
    assert result.status_code == 200
    cookie = result.headers["set-cookie"].lower()
    assert all(part in cookie for part in ("max-age=0", "path=/", "httponly", "secure", "samesite=lax"))
    assert "domain=" not in cookie and "d2r_session" not in a.cookies
    for client, cookie, csrf in zip((a, b), old_cookies, old_headers):
        assert_unauthenticated(client)
        assert client.get("/api/v1/me", headers={"Cookie": f"d2r_session={cookie}"}).status_code == 401
        replay = client.patch("/api/v1/me", headers={**csrf, "Cookie": f"d2r_session={cookie}"},
                              json={"display_name": "Revoked session"})
        assert replay.status_code == 401 and replay.json()["error"]["code"] == "unauthenticated"
    assert other.get("/api/v1/me").status_code == 200
    events = [event for event in audit(service) if event["action"] == "logout_all"]
    assert len(events) == 1 and events[0]["actor_id"] == events[0]["target_id"] == owner
    assert events[0]["target_kind"] == "account" and events[0]["meta"] == {}
    record("logout-all", result)
    record_audit(events)


@pytest.mark.parametrize("method,path,payload", [("PATCH", "/me", {"display_name": "Changed"}),
    ("POST", "/me/password", {"current_password": PASSWORD, "new_password": NEW_PASSWORD}),
    ("POST", "/auth/logout-all", {})])
def test_csrf_origin_guest_disabled_and_cross_session_guards(runtime, method, path, payload):
    service, a, b, other, _ = runtime
    before = snapshot(service)
    valid = headers(a)
    for bad in ({}, {"Origin": ORIGIN}, {**valid, "Origin": "null"},
                {**valid, "Origin": "https://attacker.example"},
                {**valid, "X-CSRF-Token": headers(b)["X-CSRF-Token"]}):
        response = a.request(method, "/api/v1" + path, headers=bad, json=payload)
        assert response.status_code == 403 and response.json()["error"]["code"] == "csrf_failed"
    assert snapshot(service) == before
    raw = a.cookies.get("d2r_session")
    a.cookies.clear()
    assert a.request(method, "/api/v1" + path, headers=valid, json=payload).status_code == 403
    a.cookies.set("d2r_session", raw, domain="testserver.local", path="/")
    account = service.store.get_credentials("w04@example.vn").account
    if hasattr(service.store, "accounts"):
        service.store.accounts[account.id] = replace(account, status="disabled")
    else:
        with service.store.engine.begin() as connection:
            table = service.store._table("account")
            connection.execute(table.update().where(table.c.id == account.id).values(status="disabled"))
    response = a.request(method, "/api/v1" + path, headers=valid, json=payload)
    assert response.status_code == 403 and response.json()["error"]["code"] == "account_disabled"
    assert service.store.get_credentials("w04@example.vn").password_hash == before[0]
    assert service.store.get_account(account.id).display_name == account.display_name
    assert service.store.get_session(hashlib.sha256(raw.encode()).digest()) is None
    assert other.get("/api/v1/me").status_code == 200


@pytest.mark.parametrize("action", ["profile", "password", "logout"])
def test_service_methods_validate_without_http_and_reject_stale_session(runtime, monkeypatch, action):
    service, a, b, _, _ = runtime
    raw = a.cookies.get("d2r_session")
    before = snapshot(service)
    with pytest.raises(AuthError) as failure:
        service.update_profile(raw, " " * 3)
    assert failure.value.code == "validation"
    with pytest.raises(AuthError) as failure:
        service.change_password(raw, "wrong", NEW_PASSWORD, ip=None)
    assert failure.value.code == "invalid_credentials"
    assert snapshot(service) == before
    original_me = service.me

    def revoked_after_authentication(token):
        identity = original_me(token)
        service.store.delete_session(identity.session.id)
        return identity

    monkeypatch.setattr(service, "me", revoked_after_authentication)
    with pytest.raises(AuthError) as failure:
        if action == "profile":
            service.update_profile(raw, "Changed")
        elif action == "password":
            service.change_password(raw, PASSWORD, NEW_PASSWORD, ip=None)
        else:
            service.logout_all(raw, ip=None)
    assert failure.value.code == "unauthenticated"
    assert snapshot(service) == before
    assert b.get("/api/v1/me").status_code == 200


def test_profile_uses_public_response_dto(runtime, monkeypatch):
    from wayfinder.api import auth
    _, a, _, _, _ = runtime
    original = auth._identity_response

    def private_fields(identity):
        body = original(identity)
        body["password_hash"] = "fixture-private-hash"
        body["account"]["session_token"] = "fixture-private-token"
        return body

    monkeypatch.setattr(auth, "_identity_response", private_fields)
    response = a.patch("/api/v1/me", headers=headers(a), json={"display_name": "An"})
    assert response.status_code == 200
    assert set(response.json()) == {"account", "csrf_token"}
    assert set(response.json()["account"]) == {"id", "email", "display_name", "role", "email_verified"}
    assert "fixture-private" not in response.text


def test_pg_password_hash_revocation_and_audit_commit_atomically(auth_database, monkeypatch):
    service = build_test_application().services.accounts
    service.store = auth_database[0]
    a = service.register("w04@example.vn", PASSWORD, "An", ip=None, user_agent=None).session
    b = service.login("w04@example.vn", PASSWORD, ip=None, user_agent=None)
    before = snapshot(service)

    def fail_audit(event):
        raise RuntimeError("synthetic audit storage failure")

    monkeypatch.setattr(service.store, "append_audit", fail_audit)
    with pytest.raises(RuntimeError, match="synthetic audit storage failure"):
        service.change_password(a.token, PASSWORD, NEW_PASSWORD, ip=None)
    assert snapshot(service) == before
    assert service.me(a.token).account.id == a.account.id
    assert service.me(b.token).account.id == b.account.id


def test_w03_reset_still_revokes_all_including_a(runtime):
    service, a, b, other, bundle = runtime
    result = a.post("/api/v1/auth/password-reset/request", headers={"Origin": ORIGIN}, json={"email": "w04@example.vn"})
    assert result.status_code == 200
    token = token_from_message(bundle.mailer.messages[-1])
    result = a.post("/api/v1/auth/password-reset/confirm", headers={"Origin": ORIGIN},
                    json={"token": token, "password": NEW_PASSWORD})
    assert result.status_code == 200
    assert_unauthenticated(a)
    assert_unauthenticated(b)
    assert other.get("/api/v1/me").status_code == 200
    assert login(b).status_code == 401
    assert login(b, NEW_PASSWORD).status_code == 200


def record(name, response):
    label = os.environ.get("W04_EVIDENCE_RUN")
    if not label:
        return
    path = Path("report/w04-evidence") / label
    path.mkdir(parents=True, exist_ok=True)
    body = response.json()
    if "csrf_token" in body:
        body["csrf_token"] = "<ephemeral fixture CSRF omitted>"
    (path / (name + ".json")).write_text(json.dumps({"status": response.status_code, "body": body},
        ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def record_audit(events):
    label = os.environ.get("W04_EVIDENCE_RUN")
    if label:
        path = Path("report/w04-evidence") / label / (events[0]["action"] + "-audit.json")
        path.write_text(json.dumps(events, default=str, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
