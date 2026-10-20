from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import threading
from uuid import uuid4

import pytest
from sqlalchemy import event, inspect, text
from sqlalchemy.exc import IntegrityError

from wayfinder.application.accounts import AccountService, AuthError, AuthPolicy
from wayfinder.application.auth_ports import AuditEvent
from wayfinder.domain.auth import Account, AuthSession
from wayfinder.infrastructure.auth_schema import create_auth_schema
from wayfinder.infrastructure.auth_store import PostgresAuthStore, _advisory_lock_id
from wayfinder.infrastructure.database import create_database_engine


class FixedClock:
    def __init__(self):
        self.value = datetime(2026, 10, 19, tzinfo=timezone.utc)

    def now(self):
        return self.value

    def today(self, timezone_name: str):
        return self.value.date()


class CheapHasher:
    dummy_hash = "$argon2id$dummy"

    def hash(self, password: str) -> str:
        return "$argon2id$" + hashlib.sha256(password.encode()).hexdigest()

    def verify(self, encoded: str, password: str) -> bool:
        return False


@pytest.fixture
def auth_database(postgres_database_url):
    schema = "auth_test_" + uuid4().hex
    admin_engine = create_database_engine(postgres_database_url)
    with admin_engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))

    engine = create_database_engine(postgres_database_url)

    @event.listens_for(engine, "connect")
    def use_test_schema(dbapi_connection, _):
        with dbapi_connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO "{schema}"')

    try:
        create_auth_schema(engine, schema=schema)
        yield PostgresAuthStore(engine, schema=schema), engine, schema
    finally:
        engine.dispose()
        with admin_engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin_engine.dispose()


def _account(email="learner@example.vn", now=None):
    now = now or datetime(2026, 10, 19, tzinfo=timezone.utc)
    return Account(
        id=str(uuid4()),
        email=email,
        email_normalized=email.strip().lower(),
        display_name="Người học",
        role="user",
        status="active",
        email_verified_at=None,
        created_at=now,
        updated_at=now,
    )


def _session(account, token="raw-session-token", now=None):
    now = now or datetime(2026, 10, 19, tzinfo=timezone.utc)
    return AuthSession(
        id=str(uuid4()),
        account_id=account.id,
        token_hash=hashlib.sha256(token.encode()).digest(),
        csrf_token="distinct-csrf-token",
        created_at=now,
        last_seen_at=now,
        expires_at=now + timedelta(days=30),
        ip="192.0.2.10",
        user_agent="integration-test",
    )


def test_auth_schema_has_required_tables_constraints_and_indexes(auth_database):
    _, engine, schema = auth_database
    inspector = inspect(engine)

    assert set(inspector.get_table_names(schema=schema)) == {
        "account",
        "auth_session",
        "rate_limit_event",
        "audit_event",
        "email_token",
    }
    assert inspector.get_unique_constraints("account", schema=schema)
    assert inspector.get_unique_constraints("auth_session", schema=schema)
    checks = {
        check["name"]
        for check in inspector.get_check_constraints("auth_session", schema=schema)
    }
    assert {"ck_auth_session_token_hash_length", "ck_auth_session_user_agent_length"} <= checks
    assert {index["name"] for index in inspector.get_indexes("rate_limit_event", schema=schema)}
    assert {index["name"] for index in inspector.get_indexes("audit_event", schema=schema)}
    assert inspector.get_foreign_keys("auth_session", schema=schema)[0]["options"]["ondelete"] == "CASCADE"


def test_account_session_and_audit_round_trip_store_no_raw_session_token(auth_database):
    store, engine, schema = auth_database
    now = datetime(2026, 10, 19, tzinfo=timezone.utc)
    account = _account(now=now)
    raw_token = "known-raw-session-token"
    session = _session(account, token=raw_token, now=now)

    with store.atomic([f"account:{account.email_normalized}"]):
        assert store.create_account(account, "$argon2id$encoded-password-hash")
        store.save_session(session)
        store.append_audit(
            AuditEvent(now, account.id, "login_ok", "account", account.id, "192.0.2.10", {"method": "password"})
        )

    credentials = store.get_credentials(account.email_normalized)
    assert credentials.account == account
    assert credentials.password_hash == "$argon2id$encoded-password-hash"
    assert store.get_account(account.id) == account
    assert store.get_session(session.token_hash) == session
    assert store.get_session(hashlib.sha256(b"unknown-token").digest()) is None

    with engine.connect() as connection:
        stored_hash = connection.execute(
            text(f'SELECT token_hash FROM "{schema}".auth_session WHERE id = :id'),
            {"id": session.id},
        ).scalar_one()
        audit = connection.execute(
            text(
                f'SELECT actor_id, action, target_kind, target_id, ip, meta '
                f'FROM "{schema}".audit_event'
            )
        ).mappings().one()
        assert bytes(stored_hash) == hashlib.sha256(raw_token.encode()).digest()
        assert raw_token.encode() not in bytes(stored_hash)
        assert str(audit["actor_id"]) == account.id
        assert audit["action"] == "login_ok"
        assert audit["meta"] == {"method": "password"}
        assert raw_token not in repr(dict(audit))
        assert account.email not in repr(dict(audit))

    store.update_last_login(account.id, now + timedelta(minutes=1))
    assert store.get_account(account.id).last_login_at == now + timedelta(minutes=1)
    store.touch_session(session.id, now + timedelta(minutes=2))
    assert store.get_session(session.token_hash).last_seen_at == now + timedelta(minutes=2)
    store.delete_session(session.id)
    assert store.get_session(session.token_hash) is None

    second_session = _session(account, token="second-session-token", now=now)
    with store.atomic([f"account:{account.email_normalized}"]):
        store.save_session(second_session)
        store.delete_account_sessions(account.id)
    assert store.get_session(second_session.token_hash) is None


def test_advisory_lock_id_is_stable_sha256_signed_int64():
    key = "login:email:abc123"
    expected = int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], "big", signed=True)

    assert _advisory_lock_id(key) == expected
    assert -(2**63) <= expected < 2**63


def test_email_unique_conflict_does_not_replace_existing_credentials(auth_database):
    store, _, _ = auth_database
    original = _account("Learner@example.vn")
    replacement = _account("learner@example.vn")

    with store.atomic(["account:learner@example.vn"]):
        assert store.create_account(original, "$argon2id$original")
    with store.atomic(["account:learner@example.vn"]):
        assert not store.create_account(replacement, "$argon2id$replacement")

    credentials = store.get_credentials("learner@example.vn")
    assert credentials.account.id == original.id
    assert credentials.password_hash == "$argon2id$original"


def test_session_token_hash_must_be_sha256_length(auth_database):
    store, _, _ = auth_database
    account = _account()
    invalid_session = replace(_session(account), token_hash=b"too-short")
    with store.atomic([f"account:{account.email_normalized}"]):
        store.create_account(account, "$argon2id$hash")
        with pytest.raises(IntegrityError):
            store.save_session(invalid_session)


def test_failed_login_auth_error_commits_rate_events_and_audit(auth_database):
    store, _, _ = auth_database
    service = AccountService(store, CheapHasher(), FixedClock(), AuthPolicy(), frozenset())
    normalized = "missing@example.vn"
    email_bucket = "login:email:" + hashlib.sha256(normalized.encode()).hexdigest()
    ip_bucket = "login:ip:192.0.2.20"

    with pytest.raises(AuthError) as error:
        service.login(normalized, "wrong passphrase", ip="192.0.2.20", user_agent="test")

    assert error.value.code == "invalid_credentials"
    since = FixedClock().now() - timedelta(minutes=15)
    assert store.failure_times(email_bucket, since) == [FixedClock().now()]
    assert store.failure_times(ip_bucket, since) == [FixedClock().now()]


def test_atomic_context_rolls_back_work_when_caller_raises(auth_database):
    store, _, _ = auth_database
    now = FixedClock().now()

    with pytest.raises(RuntimeError, match="abort"):
        with store.atomic(["login:email:test"]):
            store.add_failure("login:email:test", now)
            raise RuntimeError("abort")

    assert store.failure_times("login:email:test", now - timedelta(seconds=1)) == []


def _login_service(store):
    return AccountService(store, CheapHasher(), FixedClock(), AuthPolicy(), frozenset())


def _attempt(service, email, ip, start):
    start.wait()
    try:
        service.login(email, "wrong passphrase", ip=ip, user_agent="parallel-test")
    except AuthError as error:
        return error.code
    raise AssertionError("wrong password unexpectedly succeeded")


def test_shared_email_limit_holds_across_store_instances_and_connections(auth_database):
    store, engine, schema = auth_database
    other_store = PostgresAuthStore(engine, schema=schema)
    services = [_login_service(store), _login_service(other_store)]
    email = "many-requests@example.vn"
    bucket = "login:email:" + hashlib.sha256(email.encode()).hexdigest()
    count = 12
    start = threading.Barrier(count)

    with ThreadPoolExecutor(max_workers=count) as pool:
        results = list(
            pool.map(
                lambda index: _attempt(
                    services[index % 2], email, f"192.0.2.{index + 1}", start
                ),
                range(count),
            )
        )

    assert results.count("invalid_credentials") == 5
    assert results.count("rate_limited") == count - 5
    assert len(store.failure_times(bucket, FixedClock().now() - timedelta(minutes=15))) == 5


def test_shared_ip_limit_holds_across_many_connections(auth_database):
    store, engine, schema = auth_database
    other_store = PostgresAuthStore(engine, schema=schema)
    services = [_login_service(store), _login_service(other_store)]
    ip = "192.0.2.55"
    ip_bucket = f"login:ip:{ip}"
    count = 24
    start = threading.Barrier(count)

    with ThreadPoolExecutor(max_workers=count) as pool:
        results = list(
            pool.map(
                lambda index: _attempt(
                    services[index % 2], f"missing{index}@example.vn", ip, start
                ),
                range(count),
            )
        )

    assert results.count("invalid_credentials") == 20
    assert results.count("rate_limited") == count - 20
    assert len(store.failure_times(ip_bucket, FixedClock().now() - timedelta(minutes=15))) == 20
