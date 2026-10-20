from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import re
from threading import Event
from time import monotonic
from urllib.parse import urlsplit

import pytest
from sqlalchemy import event, text

from wayfinder.application.accounts import AccountService, AuthError, AuthPolicy
from wayfinder.fakes.mail import FakeMailer
from wayfinder.infrastructure.auth_store import PostgresAuthStore
from wayfinder.infrastructure.database import create_database_engine


PASSWORD = "old secure password"


class Clock:
    def __init__(self):
        self.value = datetime(2026, 10, 20, tzinfo=timezone.utc)

    def now(self):
        return self.value

    def today(self, timezone_name):
        return self.value.date()


class Hasher:
    dummy_hash = "dummy"

    def hash(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def verify(self, encoded, password):
        return encoded == self.hash(password)


class BlockingHasher(Hasher):
    def __init__(self, entered, release):
        self.entered, self.release = entered, release

    def verify(self, encoded, password):
        self.entered.set()
        assert self.release.wait(10)
        return super().verify(encoded, password)


@pytest.fixture
def postgres_runtime(postgres_database_url):
    engine = create_database_engine(postgres_database_url)
    try:
        with engine.begin() as connection:
            connection.execute(text(
                "TRUNCATE email_token, auth_session, rate_limit_event, audit_event, account "
                "RESTART IDENTITY CASCADE"
            ))
        yield engine, postgres_database_url
    finally:
        engine.dispose()


def make_service(engine, clock, mailer, *, hasher=None, store_class=PostgresAuthStore):
    return AccountService(store_class(engine), hasher or Hasher(), clock, AuthPolicy(), frozenset(), mailer=mailer)


def register(service, email="learner@example.vn"):
    return service.register(email, PASSWORD, "Người học", ip="192.0.2.3", user_agent="pg-test")


def mailed_token(message):
    link = re.search(r"https?://\S+", message["body"]).group(0)
    fragment = urlsplit(link).fragment
    assert fragment.startswith("token=")
    return fragment.removeprefix("token=")


def test_postgres_persists_only_token_hash_and_reset_revokes_every_session(postgres_runtime):
    engine, _ = postgres_runtime
    clock, mailer = Clock(), FakeMailer()
    service = make_service(engine, clock, mailer)
    grant = register(service).session
    assert grant is not None
    verification_token = mailed_token(mailer.messages[0])
    with engine.connect() as connection:
        row = connection.execute(text(
            "SELECT token_hash, purpose FROM email_token WHERE account_id=:id"
        ), {"id": grant.account.id}).one()
    assert bytes(row.token_hash) == hashlib.sha256(verification_token.encode()).digest()
    assert verification_token.encode() not in bytes(row.token_hash)
    assert row.purpose == "verify_email"

    service.verify_email(verification_token)
    service.request_password_reset("learner@example.vn")
    reset_token = mailed_token(mailer.messages[-1])
    service.reset_password(reset_token, "new secure password")
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT count(*) FROM auth_session WHERE account_id=:id"),
                                 {"id": grant.account.id}) == 0
        assert connection.scalar(text(
            "SELECT count(*) FROM audit_event WHERE actor_id=:id AND action='password_reset_done'"
        ), {"id": grant.account.id}) == 1
    with pytest.raises(AuthError, match="đăng nhập"):
        service.me(grant.token)
    assert service.login("learner@example.vn", "new secure password", ip=None, user_agent=None)


def test_postgres_one_use_token_is_serialized_across_independent_stores(postgres_runtime):
    engine, url = postgres_runtime
    clock, mailer = Clock(), FakeMailer()
    service_one = make_service(engine, clock, mailer)
    register(service_one)
    token = mailed_token(mailer.messages[0])
    second_engine = create_database_engine(url)
    try:
        service_two = make_service(second_engine, clock, mailer)

        def verify(service):
            try:
                service.verify_email(token)
                return "ok"
            except AuthError:
                return "rejected"

        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(verify, (service_one, service_two)))
        assert sorted(outcomes) == ["ok", "rejected"]
        with engine.connect() as connection:
            assert connection.scalar(text(
                "SELECT count(*) FROM audit_event WHERE action='email_verified'"
            )) == 1
    finally:
        second_engine.dispose()


def test_postgres_password_reset_transaction_rolls_back_token_and_session_on_store_failure(postgres_runtime):
    engine, _ = postgres_runtime
    clock, mailer = Clock(), FakeMailer()
    service = make_service(engine, clock, mailer)
    grant = register(service).session
    service.request_password_reset("learner@example.vn")
    token = mailed_token(mailer.messages[-1])

    class FailingStore(PostgresAuthStore):
        def update_password(self, *_args):
            raise RuntimeError("injected failure")

    failing_service = make_service(engine, clock, mailer, store_class=FailingStore)
    with pytest.raises(RuntimeError, match="injected failure"):
        failing_service.reset_password(token, "new secure password")
    persisted = PostgresAuthStore(engine).get_email_token(hashlib.sha256(token.encode()).digest())
    assert persisted.used_at is None
    assert service.me(grant.token).account.id == grant.account.id
    with engine.connect() as connection:
        assert connection.scalar(text(
            "SELECT count(*) FROM audit_event WHERE action='password_reset_done'"
        )) == 0


def test_postgres_reset_throttle_is_shared_across_store_instances_and_knownness(postgres_runtime):
    engine, url = postgres_runtime
    clock, mailer = Clock(), FakeMailer()
    service_one = make_service(engine, clock, mailer)
    register(service_one)
    second_engine = create_database_engine(url)
    try:
        service_two = make_service(second_engine, clock, mailer)
        expected = "Nếu email có tài khoản, bạn sẽ nhận được thư đặt lại mật khẩu."
        for service in (service_one, service_two, service_one):
            assert service.request_password_reset("learner@example.vn") == expected
        for service in (service_two, service_one, service_two):
            assert service.request_password_reset("missing@example.vn") == expected
        with pytest.raises(AuthError) as known:
            service_two.request_password_reset("learner@example.vn")
        with pytest.raises(AuthError) as unknown:
            service_one.request_password_reset("missing@example.vn")
        assert known.value.code == unknown.value.code == "rate_limited"
        assert known.value.retry_after == unknown.value.retry_after == 3600
    finally:
        second_engine.dispose()


def _wait_for_postgres_lock_or_completion(engine, backend_pid, future):
    deadline = monotonic() + 10
    while monotonic() < deadline:
        if future.done():
            return "completed"
        with engine.connect() as connection:
            wait_type = connection.scalar(text(
                "SELECT wait_event_type FROM pg_stat_activity WHERE pid=:pid"
            ), {"pid": backend_pid})
        if wait_type == "Lock":
            return "blocked_on_lock"
        Event().wait(0.01)
    raise AssertionError("reset transaction neither waited on a PostgreSQL lock nor completed")


def _session_is_revoked(service, token):
    try:
        service.me(token)
        return False
    except AuthError:
        return True


def _run_postgres_login_reset_race(engine, url, email, *, drop_login_email_alias=False):
    clock, mailer = Clock(), FakeMailer()
    bootstrap = make_service(engine, clock, mailer)
    old_session = register(bootstrap, email).session
    bootstrap.request_password_reset(email)
    token = mailed_token(mailer.messages[-1])

    login_entered, release_login, reset_attempted = Event(), Event(), Event()

    class BlockingStore(PostgresAuthStore):
        @contextmanager
        def atomic(self, keys):
            keys = list(keys)
            if drop_login_email_alias and any(key.startswith("login:email:") for key in keys):
                keys = [key for key in keys if key != f"account:{email}"]
            with super().atomic(keys):
                yield

    class BlockingHasher(Hasher):
        def verify(self, encoded, password):
            login_entered.set()
            assert release_login.wait(10)
            return super().verify(encoded, password)

    login_engine = create_database_engine(url)
    reset_engine = create_database_engine(url)
    reset_pid = []

    def before_lock(connection, cursor, statement, _parameters, _context, _executemany):
        if "pg_advisory_xact_lock" in statement:
            reset_pid.append(cursor.connection.info.backend_pid)
            reset_attempted.set()

    event.listen(reset_engine, "before_cursor_execute", before_lock)
    try:
        login_service = make_service(login_engine, clock, mailer,
                                     hasher=BlockingHasher(), store_class=BlockingStore)
        reset_service = make_service(reset_engine, clock, mailer, store_class=PostgresAuthStore)
        with ThreadPoolExecutor(max_workers=2) as pool:
            login_future = pool.submit(login_service.login, email, PASSWORD, ip=None, user_agent=None)
            assert login_entered.wait(5)
            reset_future = pool.submit(reset_service.reset_password, token, "new secure password")
            assert reset_attempted.wait(5)
            state = _wait_for_postgres_lock_or_completion(engine, reset_pid[0], reset_future)
            release_login.set()
            login_grant = login_future.result(timeout=10)
            reset_future.result(timeout=10)
        return state, bootstrap, old_session, login_grant
    finally:
        release_login.set()
        event.remove(reset_engine, "before_cursor_execute", before_lock)
        login_engine.dispose()
        reset_engine.dispose()


def test_postgres_login_reset_race_waits_on_shared_email_lock_and_revokes_sessions(postgres_runtime):
    engine, url = postgres_runtime
    state, bootstrap, old_session, login_grant = _run_postgres_login_reset_race(
        engine, url, "learner@example.vn"
    )
    assert state == "blocked_on_lock"
    assert _session_is_revoked(bootstrap, login_grant.token)
    assert _session_is_revoked(bootstrap, old_session.token)


def test_postgres_login_reset_guard_detects_dropped_login_email_lock(postgres_runtime):
    engine, url = postgres_runtime
    state, bootstrap, _, login_grant = _run_postgres_login_reset_race(
        engine, url, "mutant@example.vn", drop_login_email_alias=True
    )
    assert state == "completed"
    assert not _session_is_revoked(bootstrap, login_grant.token)


def _run_postgres_reset_request_race(engine, url, *, drop_request_email_alias=False):
    clock, mailer = Clock(), FakeMailer()
    bootstrap = make_service(engine, clock, mailer)
    registered = register(bootstrap)
    bootstrap.request_password_reset("learner@example.vn")
    reset_token = mailed_token(mailer.messages[-1])
    reset_paused, release_reset, request_attempted = Event(), Event(), Event()

    class PausingResetStore(PostgresAuthStore):
        def consume_account_email_tokens(self, account_id, purpose, at):
            super().consume_account_email_tokens(account_id, purpose, at)
            if purpose == "reset_password":
                reset_paused.set()
                assert release_reset.wait(10)

    reset_engine, request_engine = create_database_engine(url), create_database_engine(url)
    request_pid = []
    reset_committed = Event()
    request_token_created_after_reset = []

    class RequestStore(PostgresAuthStore):
        def create_email_token(self, token):
            if token.purpose == "reset_password":
                request_token_created_after_reset.append(reset_committed.is_set())
            return super().create_email_token(token)

        @contextmanager
        def atomic(self, keys):
            keys = list(keys)
            if drop_request_email_alias:
                keys = [key for key in keys if key != "account:learner@example.vn"]
            with super().atomic(keys):
                yield

    def after_reset_commit(_connection):
        reset_committed.set()

    event.listen(reset_engine, "commit", after_reset_commit)

    def before_lock(connection, cursor, statement, _parameters, _context, _executemany):
        if "pg_advisory_xact_lock" in statement:
            request_pid.append(cursor.connection.info.backend_pid)
            request_attempted.set()

    event.listen(request_engine, "before_cursor_execute", before_lock)
    try:
        reset_service = make_service(reset_engine, clock, mailer, store_class=PausingResetStore)
        request_service = make_service(request_engine, clock, mailer, store_class=RequestStore)
        with ThreadPoolExecutor(max_workers=2) as pool:
            reset_future = pool.submit(reset_service.reset_password, reset_token, "new secure password")
            assert reset_paused.wait(5)
            request_count = len(mailer.messages)
            request_future = pool.submit(request_service.request_password_reset, "learner@example.vn")
            assert request_attempted.wait(5)
            state = _wait_for_postgres_lock_or_completion(engine, request_pid[0], request_future)
            release_reset.set()
            reset_future.result(timeout=10)
            request_result = request_future.result(timeout=10)
        assert request_result == _RESET_REQUESTED_FOR_TEST
        new_token = mailed_token(mailer.messages[request_count])
        return state, bootstrap, registered.session, new_token, request_token_created_after_reset
    finally:
        release_reset.set()
        event.remove(request_engine, "before_cursor_execute", before_lock)
        event.remove(reset_engine, "commit", after_reset_commit)
        reset_engine.dispose()
        request_engine.dispose()


_RESET_REQUESTED_FOR_TEST = "Nếu email có tài khoản, bạn sẽ nhận được thư đặt lại mật khẩu."


def test_postgres_reset_serializes_new_request_after_bulk_token_consumption(postgres_runtime):
    engine, url = postgres_runtime
    state, service, old_session, new_token, created_after_reset = _run_postgres_reset_request_race(engine, url)
    assert state == "blocked_on_lock"
    assert created_after_reset == [True]
    assert _session_is_revoked(service, old_session.token)
    service.reset_password(new_token, "third secure password")


def test_postgres_reset_request_guard_detects_dropped_email_alias(postgres_runtime):
    engine, url = postgres_runtime
    state, service, _, new_token, created_after_reset = _run_postgres_reset_request_race(
        engine, url, drop_request_email_alias=True
    )
    assert state == "completed"
    assert created_after_reset == [False]
    service.reset_password(new_token, "third secure password")
