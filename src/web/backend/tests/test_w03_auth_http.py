from pathlib import Path
from http.cookies import SimpleCookie
import re
from urllib.parse import urlsplit

import pytest
from fastapi.testclient import TestClient

from wayfinder.api.app import create_app
from wayfinder.infrastructure.mail_dispatch import BackgroundMailer
from wayfinder.settings import WebSettings
from wayfinder.testing import build_test_application


ORIGIN = "http://testserver"
PASSWORD = "Mật khẩu riêng cho W03!"


@pytest.fixture
def runtime():
    bundle = build_test_application()
    app = create_app(WebSettings(_env_file=None, frontend_dist=Path("missing"),
                                 allowed_origins=[ORIGIN]), bundle.services)
    return bundle, TestClient(app)


def register(client, email="w03@example.vn"):
    return client.post("/api/v1/auth/register", headers={"Origin": ORIGIN}, json={
        "email": email, "password": PASSWORD, "display_name": "Người học"})


def token_from_message(message):
    link = re.search(r"https?://\S+", message["body"]).group(0)
    fragment = urlsplit(link).fragment
    assert fragment.startswith("token=")
    return fragment.removeprefix("token=")


def test_verify_email_is_public_post_origin_checked_and_one_use(runtime):
    bundle, client = runtime
    register(client)
    token = token_from_message(bundle.mailer.messages[0])

    result = client.post("/api/v1/auth/verify-email", headers={"Origin": ORIGIN}, json={"token": token})
    assert result.status_code == 200
    assert result.json() == {"message": "Email đã được xác minh."}
    assert client.get("/api/v1/me").json()["account"]["email_verified"] is True
    again = client.post("/api/v1/auth/verify-email", headers={"Origin": ORIGIN}, json={"token": token})
    assert again.status_code == 410
    assert again.json()["error"]["fields"][0]["type"] == "token_used"


@pytest.mark.parametrize("path,payload", [
    ("/api/v1/auth/verify-email", {"token": "bad"}),
    ("/api/v1/auth/password-reset/request", {"email": "unknown@example.vn"}),
    ("/api/v1/auth/password-reset/confirm", {"token": "bad", "password": "valid passphrase"}),
])
def test_public_recovery_posts_still_reject_missing_and_foreign_origin(runtime, path, payload):
    _, client = runtime
    for headers in ({}, {"Origin": "null"}, {"Origin": "https://attacker.example"}):
        response = client.post(path, headers=headers, json=payload)
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "csrf_failed"


def test_public_token_posts_check_origin_before_request_validation(runtime):
    _, client = runtime
    for path in ("/api/v1/auth/verify-email", "/api/v1/auth/password-reset/request",
                 "/api/v1/auth/password-reset/confirm"):
        for headers in ({}, {"Origin": "https://attacker.example"}):
            rejected = client.post(path, headers=headers, content="malformed-json")
            assert rejected.status_code == 403
            assert rejected.json()["error"]["code"] == "csrf_failed"
        allowed_origin = client.post(path, headers={"Origin": ORIGIN}, content="malformed-json")
        assert allowed_origin.status_code == 422


def test_public_reset_request_is_generic_but_resend_requires_session_and_csrf(runtime):
    _, client = runtime
    generic = client.post("/api/v1/auth/password-reset/request", headers={"Origin": ORIGIN},
                         json={"email": "unknown@example.vn"})
    assert generic.status_code == 200
    assert generic.json() == {"message": "Nếu email có tài khoản, bạn sẽ nhận được thư đặt lại mật khẩu."}

    denied = client.post("/api/v1/auth/resend-verification", headers={"Origin": ORIGIN}, json={})
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "csrf_failed"

    register(client)
    identity = client.get("/api/v1/me").json()
    resent = client.post("/api/v1/auth/resend-verification", headers={
        "Origin": ORIGIN, "X-CSRF-Token": identity["csrf_token"]}, json={})
    assert resent.status_code == 200
    assert resent.json() == {"message": "Nếu email chưa được xác minh, bạn sẽ nhận được thư xác minh mới."}


def test_password_reset_clears_cookie_and_old_sessions(runtime):
    bundle, client = runtime
    register(client)
    old_cookie = client.cookies.get("d2r_session")
    old_identity = client.get("/api/v1/me").json()
    reset = client.post("/api/v1/auth/password-reset/request", headers={"Origin": ORIGIN},
                        json={"email": "w03@example.vn"})
    assert reset.status_code == 200
    token = token_from_message(bundle.mailer.messages[-1])

    response = client.post("/api/v1/auth/password-reset/confirm", headers={"Origin": ORIGIN}, json={
        "token": token, "password": "new W03 passphrase"})
    assert response.status_code == 200
    assert response.json() == {"message": "Đã đặt lại mật khẩu. Hãy đăng nhập bằng mật khẩu mới."}
    assert "max-age=0" in response.headers["set-cookie"].lower()
    assert client.get("/api/v1/me").status_code == 401

    client.cookies.set("d2r_session", old_cookie)
    assert client.get("/api/v1/me").status_code == 401
    login = client.post("/api/v1/auth/login", headers={"Origin": ORIGIN}, json={
        "email": "w03@example.vn", "password": "new W03 passphrase"})
    assert login.status_code == 200


def test_production_logout_deletes_secure_cookie_and_revokes_session():
    bundle = build_test_application()
    settings = WebSettings(_env_file=None, env="prod", frontend_dist=Path("missing"),
                           allowed_origins=[ORIGIN])
    client = TestClient(create_app(settings, bundle.services))

    created = register(client, "secure-logout@example.vn")
    assert created.status_code == 200
    created_cookie = SimpleCookie()
    created_cookie.load(created.headers["set-cookie"])
    raw_session = created_cookie["d2r_session"].value
    assert created_cookie["d2r_session"]["secure"]

    cookie_header = f"d2r_session={raw_session}"
    identity = client.get("/api/v1/me", headers={"Cookie": cookie_header})
    assert identity.status_code == 200

    logged_out = client.post("/api/v1/auth/logout", headers={
        "Origin": ORIGIN,
        "Cookie": cookie_header,
        "X-CSRF-Token": identity.json()["csrf_token"],
    })
    assert logged_out.status_code == 200
    deleted_cookie = SimpleCookie()
    deleted_cookie.load(logged_out.headers["set-cookie"])
    assert deleted_cookie["d2r_session"]["max-age"] == "0"
    assert deleted_cookie["d2r_session"]["secure"]

    assert client.get("/api/v1/me", headers={"Cookie": cookie_header}).status_code == 401


def test_public_token_failure_has_stable_link_invalid_fields(runtime):
    _, client = runtime
    response = client.post("/api/v1/auth/password-reset/confirm", headers={"Origin": ORIGIN}, json={
        "token": "not-a-token", "password": "new W03 passphrase"})
    assert response.status_code == 410
    assert response.json()["error"]["code"] == "link_invalid"
    assert response.json()["error"]["fields"] == [{
        "loc": "token", "type": "token_invalid", "message": "Liên kết không hợp lệ.",
    }]


def test_queue_full_mailer_keeps_known_and_unknown_reset_responses_generic():
    from threading import Event

    bundle = build_test_application()
    started, release = Event(), Event()

    class SlowMailer:
        def send(self, *_args, **_kwargs):
            started.set()
            release.wait(5)

    mailer = BackgroundMailer(SlowMailer(), max_pending=1)
    bundle.services.accounts.mailer = mailer
    app = create_app(WebSettings(_env_file=None, frontend_dist=Path("missing"),
                                 allowed_origins=[ORIGIN]), bundle.services)
    client = TestClient(app)
    try:
        created = register(client, "queued@example.vn")
        assert created.status_code == 200
        assert started.wait(5)

        known = client.post("/api/v1/auth/password-reset/request", headers={"Origin": ORIGIN},
                            json={"email": "queued@example.vn"})
        unknown = client.post("/api/v1/auth/password-reset/request", headers={"Origin": ORIGIN},
                              json={"email": "missing@example.vn"})
        assert known.status_code == unknown.status_code == 200
        assert known.json() == unknown.json() == {
            "message": "Nếu email có tài khoản, bạn sẽ nhận được thư đặt lại mật khẩu."
        }
        assert len(bundle.services.accounts.store.email_tokens) == 2
    finally:
        release.set()
        mailer.close()
