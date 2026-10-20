"""Exercise protection removal in memory; never mutate product files on disk."""
from dataclasses import replace
from datetime import timedelta
import re

import pytest

from wayfinder.application.accounts import AuthError
from wayfinder.testing import build_test_application


def fixture():
    app = build_test_application()
    service = app.services.accounts
    grant = service.register("guard@example.vn", "Mật khẩu riêng W03!", "Người học", ip=None, user_agent=None).session
    return app, service, grant


def token(app):
    return re.search(r"#token=([A-Za-z0-9_-]+)", app.mailer.messages[-1]["body"]).group(1)


def assert_expiry_protects_account():
    app, service, grant = fixture()
    value = token(app)
    app.phase_b.clock.advance(24 * 3600)
    try:
        service.verify_email(value)
    except AuthError as error:
        assert error.fields[0]["type"] == "token_expired"
    assert service.store.get_account(grant.account.id).email_verified_at is None, "expired token verified the account"


def test_expiry_assertion_rejects_a_removed_expiry_check(monkeypatch):
    from wayfinder.application.accounts import AccountService

    assert_expiry_protects_account()
    original = AccountService._token_failure

    def without_expiry(self, email_token, account, purpose, now):
        if email_token is not None:
            email_token = replace(email_token, expires_at=now + timedelta(days=1))
        return original(self, email_token, account, purpose, now)

    monkeypatch.setattr(AccountService, "_token_failure", without_expiry)
    with pytest.raises(AssertionError, match="expired token verified"):
        assert_expiry_protects_account()


def assert_only_one_verification_occurs():
    app, service, _ = fixture()
    value = token(app)
    for _ in range(2):
        try:
            service.verify_email(value)
        except AuthError as error:
            assert error.fields[0]["type"] == "token_used"
    audits = [event for event in service.store.audit_events if event.action == "email_verified"]
    assert len(audits) == 1, "token reuse produced a second verification"


def test_one_use_assertion_rejects_removed_consumption(monkeypatch):
    from wayfinder.fakes.auth import FakeAuthStore

    assert_only_one_verification_occurs()
    monkeypatch.setattr(FakeAuthStore, "consume_email_token", lambda *_args: True)
    monkeypatch.setattr(FakeAuthStore, "consume_account_email_tokens", lambda *_args: None)
    with pytest.raises(AssertionError, match="second verification"):
        assert_only_one_verification_occurs()


def assert_reset_revokes_old_session():
    app, service, grant = fixture()
    service.request_password_reset("guard@example.vn")
    service.reset_password(token(app), "Mật khẩu mới riêng W03!")
    try:
        service.me(grant.token)
    except AuthError as error:
        assert error.code == "unauthenticated"
        return
    raise AssertionError("old authenticated session survived password reset")


def test_revocation_assertion_rejects_removed_session_deletion(monkeypatch):
    from wayfinder.fakes.auth import FakeAuthStore

    assert_reset_revokes_old_session()
    monkeypatch.setattr(FakeAuthStore, "delete_account_sessions", lambda *_args: None)
    with pytest.raises(AssertionError, match="survived password reset"):
        assert_reset_revokes_old_session()
