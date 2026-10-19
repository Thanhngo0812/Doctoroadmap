from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import threading

import pytest

from wayfinder.application.accounts import AccountService, AuthError, AuthPolicy
from wayfinder.domain.auth import Actor, decide
from wayfinder.fakes.auth import FakeAuthStore


class FakeClock:
    def __init__(self):
        self.value = datetime(2026, 10, 19, tzinfo=timezone.utc)

    def now(self):
        return self.value

    def today(self, timezone_name: str):
        return self.value.date()

    def advance(self, delta: timedelta):
        self.value += delta


class FakeHasher:
    dummy_hash = "$argon2id$dummy"

    def __init__(self):
        self.hash_calls = []
        self.verify_calls = []

    def hash(self, password: str) -> str:
        self.hash_calls.append(password)
        return "$argon2id$" + hashlib.sha256(password.encode()).hexdigest()

    def verify(self, encoded: str, password: str) -> bool:
        self.verify_calls.append((encoded, password))
        return encoded == self.hash(password)


def service(*, store=None, clock=None, hasher=None, passwords=frozenset()):
    store = store or FakeAuthStore()
    clock = clock or FakeClock()
    hasher = hasher or FakeHasher()
    return AccountService(store, hasher, clock, AuthPolicy(), passwords), store, clock, hasher


def register(service_: AccountService, email="learner@example.vn", password="safe passphrase"):
    return service_.register(email, password, "Người học", ip="192.0.2.1", user_agent="unit-test")


def test_registration_normalizes_email_and_duplicate_does_not_replace_account_or_grant_session():
    account_service, store, _, _ = service()

    first = register(account_service, "  Learner@Example.VN  ")
    original = store.get_credentials("learner@example.vn")
    duplicate = register(account_service, "learner@example.vn", "different passphrase")

    assert first.session is not None
    assert first.session.account.email == "Learner@Example.VN"
    assert first.session.account.email_normalized == "learner@example.vn"
    assert duplicate.session is None
    assert store.get_credentials("learner@example.vn") == original
    assert len(store.accounts) == 1
    assert len(store.sessions) == 1


@pytest.mark.parametrize("password", ["short", "x" * 129, "COMMON"])
def test_registration_rejects_short_long_or_casefolded_common_password(password):
    account_service, store, _, _ = service(passwords=frozenset({"COMMON"}))

    with pytest.raises(AuthError) as error:
        register(account_service, password=password)

    assert error.value.code == "validation"
    assert store.accounts == {}


def test_password_whitespace_is_preserved_for_hashing():
    account_service, store, _, hasher = service()
    password = "  keep these spaces  "

    register(account_service, password=password)

    assert hasher.hash_calls == [password]


def test_unknown_and_wrong_password_use_same_error_and_unknown_uses_dummy_hash():
    account_service, store, _, hasher = service()
    register(account_service)
    errors = []
    for email in ("learner@example.vn", "missing@example.vn"):
        with pytest.raises(AuthError) as error:
            account_service.login(email, "wrong passphrase", ip="192.0.2.2", user_agent="unit-test")
        errors.append((error.value.code, error.value.message))

    assert errors[0] == errors[1] == ("invalid_credentials", "Email hoặc mật khẩu không đúng.")
    assert (hasher.dummy_hash, "wrong passphrase") in hasher.verify_calls
    assert [event.action for event in store.audit_events] == ["login_ok", "login_failed", "login_failed"]


def test_email_failure_limit_unlocks_after_window():
    account_service, store, clock, _ = service()
    register(account_service)
    for _ in range(5):
        with pytest.raises(AuthError) as error:
            account_service.login("learner@example.vn", "wrong passphrase", ip="192.0.2.3", user_agent="test")
        assert error.value.code == "invalid_credentials"

    with pytest.raises(AuthError) as limited:
        account_service.login("learner@example.vn", "wrong passphrase", ip="192.0.2.3", user_agent="test")
    assert limited.value.code == "rate_limited"
    assert limited.value.retry_after == 900
    assert len(store.failure_events) == 10

    clock.advance(timedelta(minutes=15))
    with pytest.raises(AuthError) as retry:
        account_service.login("learner@example.vn", "wrong passphrase", ip="192.0.2.3", user_agent="test")
    assert retry.value.code == "invalid_credentials"


def test_ip_failure_limit_is_shared_across_emails():
    account_service, _, _, _ = service()
    for index in range(20):
        with pytest.raises(AuthError) as error:
            account_service.login(f"missing{index}@example.vn", "wrong passphrase", ip="192.0.2.4", user_agent="test")
        assert error.value.code == "invalid_credentials"

    with pytest.raises(AuthError) as error:
        account_service.login("another@example.vn", "wrong passphrase", ip="192.0.2.4", user_agent="test")
    assert error.value.code == "rate_limited"


def test_concurrent_failures_cannot_bypass_limit():
    store, clock, hasher = FakeAuthStore(), FakeClock(), FakeHasher()
    account_service = AccountService(store, hasher, clock, AuthPolicy(), frozenset())
    register(account_service)
    for _ in range(4):
        with pytest.raises(AuthError):
            account_service.login("learner@example.vn", "wrong passphrase", ip="192.0.2.5", user_agent="test")

    start = threading.Barrier(2)

    def attempt():
        start.wait()
        try:
            account_service.login("learner@example.vn", "wrong passphrase", ip="192.0.2.5", user_agent="test")
        except AuthError as error:
            return error.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: attempt(), range(2)))

    assert sorted(results) == ["invalid_credentials", "rate_limited"]


def test_login_grants_random_hashed_session_and_successful_identity():
    account_service, store, clock, _ = service()
    register(account_service)
    grant = account_service.login("learner@example.vn", "safe passphrase", ip="192.0.2.6", user_agent="x" * 250)

    assert len(grant.token.encode()) >= 43
    assert grant.session.token_hash == hashlib.sha256(grant.token.encode()).digest()
    assert grant.token not in repr(store.sessions)
    assert grant.session.token_hash in store.sessions
    assert grant.session.csrf_token != grant.token
    assert len(grant.session.csrf_token) >= 43
    assert grant.session.expires_at == clock.now() + timedelta(days=30)
    assert grant.session.user_agent == "x" * 200
    assert account_service.me(grant.token).account.id == grant.account.id


@pytest.mark.parametrize("age", [timedelta(days=7), timedelta(days=30)])
def test_session_expiry_is_enforced_at_idle_and_absolute_boundaries(age):
    account_service, store, clock, _ = service()
    grant = register(account_service).session
    clock.advance(age)

    with pytest.raises(AuthError) as error:
        account_service.me(grant.token)

    assert error.value.code == "unauthenticated"
    assert grant.session.id not in store.sessions_by_id


def test_session_absolute_expiry_applies_after_recent_activity():
    account_service, store, clock, _ = service()
    grant = register(account_service).session
    clock.advance(timedelta(days=29))
    store.sessions_by_id[grant.session.id] = replace(
        store.sessions_by_id[grant.session.id], last_seen_at=clock.now()
    )
    clock.advance(timedelta(days=1))

    with pytest.raises(AuthError) as error:
        account_service.me(grant.token)
    assert error.value.code == "unauthenticated"


def test_me_touches_old_activity_only_after_five_minutes():
    account_service, store, clock, _ = service()
    grant = register(account_service).session
    clock.advance(timedelta(minutes=5))
    account_service.me(grant.token)
    assert store.sessions_by_id[grant.session.id].last_seen_at == grant.session.last_seen_at

    clock.advance(timedelta(seconds=1))
    identity = account_service.me(grant.token)
    assert identity.session.last_seen_at == clock.now()


def test_disabled_session_is_revoked_on_first_request_and_cannot_return_if_reenabled():
    account_service, store, _, _ = service()
    grant = register(account_service).session
    store.accounts[grant.account.id] = replace(grant.account, status="disabled")

    with pytest.raises(AuthError) as error:
        account_service.me(grant.token)
    assert error.value.code == "account_disabled"
    assert store.sessions == {}

    store.accounts[grant.account.id] = grant.account
    with pytest.raises(AuthError) as expired:
        account_service.me(grant.token)
    assert expired.value.code == "unauthenticated"


def test_logout_revokes_only_hashed_token_and_is_idempotent():
    account_service, store, _, _ = service()
    grant = register(account_service).session

    account_service.logout(grant.token, ip="192.0.2.7")
    account_service.logout(grant.token, ip="192.0.2.7")

    assert store.sessions == {}
    assert store.audit_events[-1].action == "logout"
    assert grant.token not in repr(store.audit_events)


def test_audit_never_contains_email_password_or_session_tokens():
    account_service, store, _, _ = service()
    grant = register(account_service, password="safe passphrase").session
    with pytest.raises(AuthError):
        account_service.login("missing@example.vn", "secret not for logs", ip="192.0.2.8", user_agent="test")

    serialized = repr(store.audit_events)
    assert "learner@example.vn" not in serialized
    assert "safe passphrase" not in serialized
    assert "secret not for logs" not in serialized
    assert grant.token not in serialized


def test_create_admin_is_trusted_and_never_returns_a_session():
    account_service, store, _, _ = service()

    account = account_service.create_admin(" Admin@Example.VN ", "safe passphrase")

    assert account.role == "admin"
    assert account.email_normalized == "admin@example.vn"
    assert account.email_verified_at is not None
    assert store.sessions == {}

    with pytest.raises(AuthError) as error:
        account_service.create_admin("admin@example.vn", "safe passphrase")
    assert error.value.code == "conflict"


def test_domain_decisions_cover_guest_unverified_and_disabled_actors():
    assert decide(None, "register", None, None).allowed
    assert decide(None, "me", None, None).code == "unauthenticated"
    unverified = Actor("u1", "user", False, "active")
    disabled = Actor("u2", "user", True, "disabled")

    assert decide(unverified, "invite_by_email", None, "owner").code == "email_unverified"
    assert decide(Actor("u3", "user", True, "active"), "invite_by_email", None, "owner").code == "forbidden"
    assert decide(disabled, "upload", None, None).code == "account_disabled"
    assert decide(unverified, "future_course_action", None, None).code == "forbidden"


def test_auth_service_guards_reject_mutants_without_editing_source(monkeypatch):
    from wayfinder.application.accounts import SessionIdentity

    def assert_dummy_hash_is_verified(account_service, hasher):
        try:
            account_service.login("missing@example.vn", "wrong passphrase", ip="192.0.2.20", user_agent="test")
        except AuthError as error:
            assert error.code == "invalid_credentials"
        else:
            raise AssertionError("unknown login must fail")
        assert (hasher.dummy_hash, "wrong passphrase") in hasher.verify_calls

    account_service, _, _, hasher = service()

    def skip_unknown_hash(self, email, password, *, ip, user_agent):
        raise AuthError("invalid_credentials", "Email hoặc mật khẩu không đúng.")

    monkeypatch.setattr(AccountService, "login", skip_unknown_hash)
    with pytest.raises(AssertionError):
        assert_dummy_hash_is_verified(account_service, hasher)
    monkeypatch.undo()

    def assert_idle_expiry(account_service, store, clock, token):
        try:
            account_service.me(token)
        except AuthError as error:
            assert error.code == "unauthenticated"
        else:
            raise AssertionError("expired session must fail")
        assert store.sessions == {}

    account_service, store, clock, _ = service()
    grant = register(account_service).session
    clock.advance(timedelta(days=7))

    def ignore_idle_expiry(self, token):
        session = self.store.get_session(self._token_hash(token))
        account = self.store.get_account(session.account_id)
        return SessionIdentity(account, session)

    monkeypatch.setattr(AccountService, "me", ignore_idle_expiry)
    with pytest.raises(AssertionError):
        assert_idle_expiry(account_service, store, clock, grant.token)
    monkeypatch.undo()

    account_service, store, _, _ = service()
    grant = register(account_service).session
    store.accounts[grant.account.id] = replace(grant.account, status="disabled")

    def skip_disabled_revocation(self, token):
        raise AuthError("account_disabled", "Tài khoản đã bị khoá.")

    monkeypatch.setattr(AccountService, "me", skip_disabled_revocation)
    with pytest.raises(AssertionError):
        try:
            account_service.me(grant.token)
        except AuthError as error:
            assert error.code == "account_disabled"
            assert store.sessions == {}
    monkeypatch.undo()

    account_service, store, _, _ = service()
    register(account_service)

    def assert_email_throttle(account_service):
        for index in range(5):
            try:
                account_service.login("learner@example.vn", "wrong passphrase",
                                      ip=f"192.0.2.{index + 30}", user_agent="test")
            except AuthError as error:
                assert error.code == "invalid_credentials"
            else:
                raise AssertionError("wrong password must fail")
        try:
            account_service.login("learner@example.vn", "wrong passphrase", ip="192.0.2.40", user_agent="test")
        except AuthError as error:
            assert error.code == "rate_limited"
        else:
            raise AssertionError("email bucket must limit after five failures")

    def ignore_email_limit(self, buckets, since, now, window):
        times = self.store.failure_times(buckets[1], since)
        if len(times) < 20:
            return None
        return 1

    monkeypatch.setattr(AccountService, "_retry_after", ignore_email_limit)
    with pytest.raises(AssertionError):
        assert_email_throttle(account_service)
