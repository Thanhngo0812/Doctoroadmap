from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import re
from contextlib import contextmanager
from threading import Event, Lock
from urllib.parse import urlsplit

import pytest

from wayfinder.application.accounts import AccountService, AuthError, AuthPolicy
from wayfinder.fakes.auth import FakeAuthStore
from wayfinder.fakes.mail import FakeMailer


class Clock:
    def __init__(self):
        self.value = datetime(2026, 10, 20, tzinfo=timezone.utc)

    def now(self):
        return self.value

    def today(self, timezone_name):
        return self.value.date()

    def advance(self, *, hours=0, minutes=0):
        self.value += timedelta(hours=hours, minutes=minutes)


class Hasher:
    dummy_hash = "dummy"

    def hash(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def verify(self, encoded, password):
        return encoded == self.hash(password)


def make_service(*, mailer=None, policy=None):
    store, clock, mailer = FakeAuthStore(), Clock(), mailer or FakeMailer()
    service = AccountService(store, Hasher(), clock, policy or AuthPolicy(), frozenset(), mailer=mailer)
    return service, store, clock, mailer


def register(service, email="learner@example.vn", password="old secure pass"):
    return service.register(email, password, "Người học", ip="192.0.2.2", user_agent="test")


def mailed_token(message):
    url = re.search(r"https?://\S+", message["body"]).group(0)
    fragment = urlsplit(url).fragment
    assert fragment.startswith("token=")
    return fragment.removeprefix("token=")


def test_register_sends_one_hashed_token_and_verification_is_one_use():
    service, store, clock, mailer = make_service()
    grant = register(service).session

    assert grant is not None
    assert len(mailer.messages) == 1
    token = mailed_token(mailer.messages[0])
    saved = next(iter(store.email_tokens.values()))
    assert saved.token_hash == hashlib.sha256(token.encode()).digest()
    assert token not in repr(saved)
    assert saved.purpose == "verify_email"
    assert saved.expires_at == clock.value + timedelta(hours=24)

    service.verify_email(token, ip="192.0.2.2")
    assert store.accounts[grant.account.id].email_verified_at == clock.value
    assert store.audit_events[-1].action == "email_verified"
    with pytest.raises(AuthError) as error:
        service.verify_email(token)
    assert error.value.code == "link_invalid"
    assert error.value.fields[0]["type"] == "token_used"


def test_duplicate_registration_sends_existing_account_notice_without_takeover():
    service, store, _, mailer = make_service()
    original = register(service, password="original secret pass").session
    original_account = store.accounts[original.account.id]
    original_credential = store.credentials_by_email[original_account.email_normalized]
    original_sessions = dict(store.sessions)
    original_tokens = dict(store.email_tokens)
    mailer.messages.clear()

    duplicate = service.register(" LEARNER@example.vn ", "attacker secret pass", "Attacker",
                                 ip="192.0.2.9", user_agent="duplicate-test")

    assert duplicate.session is None
    assert len(mailer.messages) == 1
    assert "đã tồn tại" in mailer.messages[0]["subject"].lower() or "tài khoản" in mailer.messages[0]["body"].lower()
    assert store.accounts[original.account.id] == original_account
    assert store.credentials_by_email[original_account.email_normalized] == original_credential
    assert store.sessions == original_sessions
    assert store.email_tokens == original_tokens


def test_verification_expiration_and_changed_email_are_rejected():
    service, store, clock, mailer = make_service()
    grant = register(service).session
    expired_token = mailed_token(mailer.messages[0])
    clock.advance(hours=24)
    with pytest.raises(AuthError) as expired:
        service.verify_email(expired_token)
    assert expired.value.fields[0]["type"] == "token_expired"

    service, store, _, mailer = make_service()
    grant = register(service).session
    token = mailed_token(mailer.messages[0])
    account = store.accounts[grant.account.id]
    credentials = store.credentials_by_email.pop(account.email_normalized)
    changed = replace(account, email_normalized="new@example.vn")
    store.accounts[account.id] = changed
    store.credentials_by_email[changed.email_normalized] = replace(credentials, account=changed)
    with pytest.raises(AuthError) as invalid:
        service.verify_email(token)
    assert invalid.value.fields[0]["type"] == "token_invalid"


def test_resend_is_limited_by_shared_store_and_sends_three_per_hour():
    service, _, _, mailer = make_service()
    grant = register(service).session
    mailer.messages.clear()

    for _ in range(3):
        service.resend_verification(grant.account.id, ip="192.0.2.2")
    assert len(mailer.messages) == 3
    with pytest.raises(AuthError) as limited:
        service.resend_verification(grant.account.id, ip="192.0.2.2")
    assert limited.value.code == "rate_limited"
    assert limited.value.retry_after == 3600


def test_password_reset_request_is_generic_and_throttles_known_and_unknown_emails():
    service, _, _, mailer = make_service()
    register(service)
    mailer.messages.clear()

    known = service.request_password_reset("learner@example.vn")
    unknown = service.request_password_reset("missing@example.vn")
    assert known == unknown == "Nếu email có tài khoản, bạn sẽ nhận được thư đặt lại mật khẩu."
    assert [message["to"] for message in mailer.messages] == ["learner@example.vn"]
    assert service.request_password_reset("missing@example.vn") == known
    assert service.request_password_reset("missing@example.vn") == known
    with pytest.raises(AuthError) as unknown_limited:
        service.request_password_reset("missing@example.vn")
    for _ in range(2):
        service.request_password_reset("learner@example.vn")
    with pytest.raises(AuthError) as known_limited:
        service.request_password_reset("learner@example.vn")
    assert unknown_limited.value.code == known_limited.value.code == "rate_limited"
    assert unknown_limited.value.retry_after == known_limited.value.retry_after == 3600


def test_password_reset_is_single_use_revokes_all_sessions_and_other_reset_tokens():
    service, store, _, mailer = make_service()
    grant = register(service).session
    assert grant is not None
    service.request_password_reset("learner@example.vn")
    first = mailed_token(mailer.messages[-1])
    service.request_password_reset("learner@example.vn")
    second = mailed_token(mailer.messages[-1])

    service.reset_password(first, "new secure pass", ip="192.0.2.2")
    assert store.sessions == {}
    assert store.audit_events[-1].action == "password_reset_done"
    with pytest.raises(AuthError) as old_session:
        service.me(grant.token)
    assert old_session.value.code == "unauthenticated"
    with pytest.raises(AuthError) as old_password:
        service.login("learner@example.vn", "old secure pass", ip=None, user_agent=None)
    assert old_password.value.code == "invalid_credentials"
    assert service.login("learner@example.vn", "new secure pass", ip=None, user_agent=None)
    with pytest.raises(AuthError) as old_reset:
        service.reset_password(second, "another secure pass")
    assert old_reset.value.fields[0]["type"] == "token_used"
    with pytest.raises(AuthError):
        service.reset_password(first, "third secure pass")


def test_password_reset_token_expires_after_sixty_minutes():
    service, _, clock, mailer = make_service()
    register(service)
    service.request_password_reset("learner@example.vn")
    token = mailed_token(mailer.messages[-1])
    clock.advance(minutes=60)
    with pytest.raises(AuthError) as expired:
        service.reset_password(token, "new secure pass")
    assert expired.value.fields[0]["type"] == "token_expired"


def test_concurrent_verification_consumes_token_once():
    service, _, _, mailer = make_service()
    register(service)
    token = mailed_token(mailer.messages[0])

    def verify():
        try:
            service.verify_email(token)
            return "ok"
        except AuthError:
            return "rejected"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: verify(), range(2)))
    assert sorted(outcomes) == ["ok", "rejected"]


def test_mailer_failure_does_not_rollback_registration_or_generic_reset_result():
    class BrokenMailer:
        def send(self, *_args, **_kwargs):
            raise RuntimeError("SMTP failure")

    service, store, _, _ = make_service(mailer=BrokenMailer())
    grant = register(service).session
    assert grant is not None and grant.account.id in store.accounts
    assert len(store.email_tokens) == 1
    result = service.request_password_reset("learner@example.vn")
    assert result == "Nếu email có tài khoản, bạn sẽ nhận được thư đặt lại mật khẩu."
    assert len(store.email_tokens) == 2


def test_invalid_expired_and_used_reset_tokens_are_rejected_before_password_hash():
    class CountingHasher(Hasher):
        def __init__(self):
            self.hash_calls = []

        def hash(self, password):
            self.hash_calls.append(password)
            return super().hash(password)

    store, clock, mailer, hasher = FakeAuthStore(), Clock(), FakeMailer(), CountingHasher()
    service = AccountService(store, hasher, clock, AuthPolicy(), frozenset(), mailer=mailer)
    register(service)
    service.request_password_reset("learner@example.vn")
    token = mailed_token(mailer.messages[-1])
    calls = len(hasher.hash_calls)

    for bad_token, advance in (("not-a-token", 0), (token, 60)):
        if advance:
            clock.advance(minutes=advance)
        with pytest.raises(AuthError):
            service.reset_password(bad_token, "replacement passphrase")
        assert len(hasher.hash_calls) == calls

    clock.value = datetime(2026, 10, 20, tzinfo=timezone.utc)
    service.request_password_reset("learner@example.vn")
    used = mailed_token(mailer.messages[-1])
    service.reset_password(used, "replacement passphrase")
    calls = len(hasher.hash_calls)
    with pytest.raises(AuthError):
        service.reset_password(used, "another replacement")
    assert len(hasher.hash_calls) == calls


def test_login_started_before_reset_cannot_leave_a_live_old_password_session():
    login_in_verify = Event()
    allow_login = Event()
    reset_lock_attempted = Event()

    class BlockingHasher(Hasher):
        def verify(self, encoded, password):
            login_in_verify.set()
            assert allow_login.wait(5)
            return super().verify(encoded, password)

    class ObservedStore(FakeAuthStore):
        def __init__(self):
            super().__init__()
            self._key_locks_guard = Lock()
            self._key_locks = {}
            self.login_keys = set()
            self.reset_keys = set()

        @contextmanager
        def atomic(self, keys):
            locks = []
            with self._key_locks_guard:
                for key in sorted(set(keys)):
                    locks.append(self._key_locks.setdefault(key, Lock()))
            is_reset = any(key.startswith("email-token:") for key in keys)
            if is_reset:
                self.reset_keys = set(keys)
                reset_lock_attempted.set()
            elif any(key.startswith("login:email:") for key in keys):
                self.login_keys = set(keys)
            for lock in locks:
                lock.acquire()
            try:
                yield
            finally:
                for lock in reversed(locks):
                    lock.release()

    store, clock, mailer = ObservedStore(), Clock(), FakeMailer()
    hasher = BlockingHasher()
    service = AccountService(store, hasher, clock, AuthPolicy(), frozenset(), mailer=mailer)
    old_session = register(service).session
    service.request_password_reset("learner@example.vn")
    reset_token = mailed_token(mailer.messages[-1])

    with ThreadPoolExecutor(max_workers=2) as pool:
        login_future = pool.submit(service.login, "learner@example.vn", "old secure pass",
                                   ip=None, user_agent=None)
        assert login_in_verify.wait(5)
        reset_future = pool.submit(service.reset_password, reset_token, "new secure pass")
        assert reset_lock_attempted.wait(5)
        allow_login.set()
        login_grant = login_future.result(timeout=5)
        reset_future.result(timeout=5)

    assert "account:learner@example.vn" in store.login_keys & store.reset_keys

    with pytest.raises(AuthError) as login_revoked:
        service.me(login_grant.token)
    assert login_revoked.value.code == "unauthenticated"
    with pytest.raises(AuthError) as original_revoked:
        service.me(old_session.token)
    assert original_revoked.value.code == "unauthenticated"
