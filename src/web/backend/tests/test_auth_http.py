from pathlib import Path

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient

from wayfinder.api.app import create_app
from wayfinder.api.auth import get_actor
from wayfinder.settings import WebSettings
from wayfinder.testing import build_test_application


ORIGIN = "http://testserver"
PASSWORD = "Mật khẩu riêng cho W02!"


@pytest.fixture
def runtime():
    bundle = build_test_application()
    app = create_app(WebSettings(_env_file=None, frontend_dist=Path("missing"),
                                allowed_origins=[ORIGIN, "https://testserver"]), bundle.services)
    return bundle, app, TestClient(app)


def register(client, email="A@example.vn"):
    return client.post("/api/v1/auth/register", headers={"Origin": ORIGIN}, json={
        "email": email, "password": PASSWORD, "display_name": "Người học"})


def test_registration_duplicate_same_body_no_account_takeover(runtime):
    _, _, client = runtime
    first = register(client)
    cookie = client.cookies.get("d2r_session")
    first_account = client.get("/api/v1/me").json()["account"]
    client.cookies.clear()
    second = register(client, " a@EXAMPLE.vn ")
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert "set-cookie" not in second.headers
    assert client.get("/api/v1/me").status_code == 401
    client.cookies.set("d2r_session", cookie)
    assert client.get("/api/v1/me").json()["account"] == first_account
    assert first_account["role"] == "user" and first_account["email_verified"] is False
    assert set(first_account) == {"id", "email", "display_name", "role", "email_verified"}


@pytest.mark.parametrize("scheme", ["http", "https"])
def test_cookie_security_and_logout_revokes_old_cookie(runtime, scheme):
    _, app, _ = runtime
    client = TestClient(app, base_url=f"{scheme}://testserver")
    response = client.post("/api/v1/auth/register", headers={"Origin": f"{scheme}://testserver"},
                           json={"email": "cookie@example.vn", "password": PASSWORD, "display_name": "An"})
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=lax" in cookie and "path=/" in cookie
    assert ("; secure" in cookie) == (scheme == "https")
    assert "domain=" not in cookie
    old = client.cookies.get("d2r_session")
    identity = client.get("/api/v1/me").json()
    result = client.post("/api/v1/auth/logout", headers={"Origin": f"{scheme}://testserver",
                                                        "X-CSRF-Token": identity["csrf_token"]})
    assert result.status_code == 200
    assert "max-age=0" in result.headers["set-cookie"].lower()
    client.cookies.set("d2r_session", old)
    assert client.get("/api/v1/me").status_code == 401


def test_known_unknown_login_errors_match_and_sixth_failure_is_throttled(runtime):
    _, _, client = runtime
    register(client)
    known = client.post("/api/v1/auth/login", headers={"Origin": ORIGIN},
                        json={"email": "a@example.vn", "password": "wrong"})
    unknown = client.post("/api/v1/auth/login", headers={"Origin": ORIGIN},
                          json={"email": "unknown@example.vn", "password": "wrong"})
    assert known.status_code == unknown.status_code == 401
    assert known.json() == unknown.json()
    for _ in range(4):
        assert client.post("/api/v1/auth/login", headers={"Origin": ORIGIN},
                           json={"email": "a@example.vn", "password": "wrong"}).status_code == 401
    blocked = client.post("/api/v1/auth/login", headers={"Origin": ORIGIN},
                          json={"email": "a@example.vn", "password": PASSWORD})
    assert blocked.status_code == 429
    assert blocked.json()["error"]["retry_after"] == 900
    assert blocked.headers["retry-after"] == "900"


def test_all_unsafe_routes_fail_closed_including_new_future_route(runtime):
    _, app, client = runtime
    mutations = []

    @app.api_route("/api/v1/future", methods=["POST", "PUT", "PATCH", "DELETE"])
    def future(actor=Depends(get_actor)):
        mutations.append(actor.user_id)
        return {"done": True}

    register(client)
    csrf = client.get("/api/v1/me").json()["csrf_token"]
    tested = set()
    def routes_in(router):
        for route in router.routes:
            included = getattr(route, "original_router", None)
            if included is not None:
                yield from routes_in(included)
            else:
                yield route

    for route in routes_in(app):
        for method in getattr(route, "methods", set()) - {"GET", "HEAD", "OPTIONS"}:
            path = route.path
            tested.add((method, path))
            preauth = path in {"/api/v1/auth/login", "/api/v1/auth/register"}
            for headers in ({}, {"Origin": "https://evil.example", "X-CSRF-Token": csrf}):
                response = client.request(method, path, headers=headers, content="invalid-json")
                assert response.status_code == 403, (method, path, response.text)
                assert response.json()["error"]["code"] == "csrf_failed"
            if not preauth:
                response = client.request(method, path, headers={"Origin": ORIGIN}, content="invalid-json")
                assert response.status_code == 403
                assert response.json()["error"]["code"] == "csrf_failed"
    assert ("POST", "/api/v1/auth/logout") in tested
    assert len([pair for pair in tested if pair[1] == "/api/v1/future"]) == 4
    assert mutations == []
    assert client.post("/api/v1/future", headers={"Origin": ORIGIN, "X-CSRF-Token": csrf}).status_code == 200
    assert len(mutations) == 1


def test_csrf_is_bound_to_session(runtime):
    _, app, client = runtime
    register(client)
    first_csrf = client.get("/api/v1/me").json()["csrf_token"]
    other = TestClient(app)
    register(other, "other@example.vn")
    response = other.post("/api/v1/auth/logout", headers={"Origin": ORIGIN, "X-CSRF-Token": first_csrf})
    assert response.status_code == 403
    assert other.get("/api/v1/me").status_code == 200


def test_public_registration_cannot_set_admin_role_or_echo_password(runtime):
    _, _, client = runtime
    result = client.post("/api/v1/auth/register", headers={"Origin": ORIGIN}, json={
        "email": "evil@example.vn", "password": PASSWORD, "display_name": "Evil", "role": "admin"})
    assert result.status_code == 422
    assert PASSWORD not in result.text
    assert client.get("/api/v1/me").status_code == 401


def test_configured_origin_is_exact_and_origin_mismatch_precedes_body_validation():
    bundle = build_test_application()
    app = create_app(WebSettings(_env_file=None, frontend_dist=Path("missing"),
                                allowed_origins=["https://learn.example.vn"]), bundle.services)
    client = TestClient(app)
    for origin in (None, "null", "https://learn.example.vn.evil.example", "https://learn.example.vn/", ORIGIN):
        headers = {} if origin is None else {"Origin": origin}
        result = client.post("/api/v1/auth/register", headers=headers, content="malformed")
        assert result.status_code == 403
        assert result.json()["error"]["code"] == "csrf_failed"
    result = client.post("/api/v1/auth/register", headers={"Origin": "https://learn.example.vn"},
                         json={"email": "origin@example.vn", "password": PASSWORD, "display_name": "An"})
    assert result.status_code == 200


def test_me_never_caches_csrf_and_global_guard_detects_removed_enforcement(runtime, monkeypatch):
    import importlib
    app_module = importlib.import_module("wayfinder.api.app")
    _, _, client = runtime
    register(client)
    response = client.get("/api/v1/me")
    assert response.headers["cache-control"] == "no-store"

    def assert_logout_protected():
        result = client.post("/api/v1/auth/logout", headers={"Origin": ORIGIN})
        assert result.status_code == 403
        assert client.get("/api/v1/me").status_code == 200

    assert_logout_protected()

    async def removed_guard(_request):
        pass

    monkeypatch.setattr(app_module, "enforce_csrf", removed_guard)
    with pytest.raises(AssertionError):
        assert_logout_protected()


def test_empty_origin_config_only_trusts_local_development_hosts():
    bundle = build_test_application()
    app = create_app(WebSettings(_env_file=None, frontend_dist=Path("missing")), bundle.services)
    attacker = TestClient(app, base_url="http://attacker.example")
    result = attacker.post("/api/v1/auth/register", headers={"Origin": "http://attacker.example"},
                           json={"email": "host@example.vn", "password": PASSWORD, "display_name": "An"})
    assert result.status_code == 403
    assert result.json()["error"]["code"] == "csrf_failed"
    local = TestClient(app, base_url="http://localhost:8000")
    result = local.post("/api/v1/auth/register", headers={"Origin": "http://localhost:8000"},
                        json={"email": "host@example.vn", "password": PASSWORD, "display_name": "An"})
    assert result.status_code == 200


def test_production_cookie_is_secure_even_behind_http_upstream():
    bundle = build_test_application()
    app = create_app(WebSettings(_env_file=None, env="prod", frontend_dist=Path("missing"),
                                allowed_origins=["https://learn.example.vn"]), bundle.services)
    client = TestClient(app, base_url="http://upstream.internal")
    result = client.post("/api/v1/auth/register", headers={"Origin": "https://learn.example.vn"},
                         json={"email": "secure@example.vn", "password": PASSWORD, "display_name": "An"})
    assert result.status_code == 200
    secure = "; secure" in result.headers["set-cookie"].lower()
    assert secure is True
