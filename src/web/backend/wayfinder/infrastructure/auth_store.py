from contextlib import contextmanager
from contextvars import ContextVar
from hashlib import sha256
from typing import Iterator, Sequence

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Connection, Engine

from wayfinder.application.accounts import Credentials
from wayfinder.application.auth_ports import AuditEvent, EmailPurpose, EmailToken
from wayfinder.domain.auth import Account, AuthSession
from wayfinder.infrastructure.auth_schema import auth_metadata


class PostgresAuthStore:
    def __init__(self, engine: Engine, *, schema: str | None = None) -> None:
        self.engine = engine
        self.schema = schema
        self._metadata = auth_metadata(schema)
        self._tables = self._metadata.tables
        self._connection: ContextVar[Connection | None] = ContextVar(
            f"wayfinder_auth_connection_{id(self)}", default=None
        )

    @contextmanager
    def atomic(self, keys: Sequence[str]) -> Iterator[None]:
        if self._connection.get() is not None:
            raise RuntimeError("AuthStore.atomic cannot be nested")
        with self.engine.begin() as connection:
            context_token = self._connection.set(connection)
            try:
                lock_ids = sorted({_advisory_lock_id(key) for key in keys})
                for lock_id in lock_ids:
                    connection.execute(
                        select(func.pg_advisory_xact_lock(lock_id))
                    )
                yield
            finally:
                self._connection.reset(context_token)

    def get_credentials(self, normalized_email: str) -> Credentials | None:
        account_table = self._table("account")
        with self._use_connection() as connection:
            row = connection.execute(
                select(account_table).where(account_table.c.email_normalized == normalized_email)
            ).mappings().first()
            if row is None:
                return None
            return Credentials(_account(row), row["password_hash"])

    def create_account(self, account: Account, password_hash: str) -> bool:
        table = self._table("account")
        statement = (
            pg_insert(table)
            .values(**_account_values(account), password_hash=password_hash)
            .on_conflict_do_nothing(index_elements=[table.c.email_normalized])
            .returning(table.c.id)
        )
        with self._use_connection(write=True) as connection:
            return connection.execute(statement).scalar_one_or_none() is not None

    def get_account(self, account_id: str) -> Account | None:
        table = self._table("account")
        with self._use_connection() as connection:
            row = connection.execute(
                select(table).where(table.c.id == account_id)
            ).mappings().first()
            return _account(row) if row is not None else None

    def update_last_login(self, account_id: str, at) -> None:
        table = self._table("account")
        with self._use_connection(write=True) as connection:
            connection.execute(
                update(table)
                .where(table.c.id == account_id)
                .values(last_login_at=at, updated_at=at)
            )

    def update_profile(self, account_id: str, display_name: str, at) -> Account:
        table = self._table("account")
        with self._use_connection(write=True) as connection:
            row = connection.execute(update(table).where(table.c.id == account_id).values(
                display_name=display_name, updated_at=at
            ).returning(table)).mappings().one()
            return _account(row)

    def get_session(self, token_hash: bytes) -> AuthSession | None:
        table = self._table("auth_session")
        with self._use_connection() as connection:
            row = connection.execute(
                select(table).where(table.c.token_hash == token_hash)
            ).mappings().first()
            return _session(row) if row is not None else None

    def save_session(self, session: AuthSession) -> None:
        table = self._table("auth_session")
        statement = insert(table).values(
            id=session.id,
            account_id=session.account_id,
            token_hash=session.token_hash,
            csrf_token=session.csrf_token,
            created_at=session.created_at,
            last_seen_at=session.last_seen_at,
            expires_at=session.expires_at,
            ip=session.ip,
            user_agent=session.user_agent,
        )
        with self._use_connection(write=True) as connection:
            connection.execute(statement)

    def touch_session(self, session_id: str, at) -> None:
        table = self._table("auth_session")
        with self._use_connection(write=True) as connection:
            connection.execute(
                update(table).where(table.c.id == session_id).values(last_seen_at=at)
            )

    def delete_session(self, session_id: str) -> None:
        table = self._table("auth_session")
        with self._use_connection(write=True) as connection:
            connection.execute(delete(table).where(table.c.id == session_id))

    def delete_account_sessions(self, account_id: str, *, except_session_id: str | None = None) -> None:
        table = self._table("auth_session")
        statement = delete(table).where(table.c.account_id == account_id)
        if except_session_id is not None:
            statement = statement.where(table.c.id != except_session_id)
        with self._use_connection(write=True) as connection:
            connection.execute(statement)

    def create_email_token(self, token: EmailToken) -> None:
        table = self._table("email_token")
        with self._use_connection(write=True) as connection:
            connection.execute(insert(table).values(
                id=token.id, account_id=token.account_id, purpose=token.purpose,
                token_hash=token.token_hash, email_normalized=token.email_normalized,
                expires_at=token.expires_at, used_at=token.used_at, created_at=token.created_at,
            ))

    def get_email_token(self, token_hash: bytes) -> EmailToken | None:
        table = self._table("email_token")
        with self._use_connection() as connection:
            row = connection.execute(select(table).where(table.c.token_hash == token_hash)).mappings().first()
            return _email_token(row) if row is not None else None

    def consume_email_token(self, token_id: str, at) -> bool:
        table = self._table("email_token")
        with self._use_connection(write=True) as connection:
            return connection.execute(update(table).where(
                table.c.id == token_id, table.c.used_at.is_(None)
            ).values(used_at=at).returning(table.c.id)).scalar_one_or_none() is not None

    def consume_account_email_tokens(self, account_id: str, purpose: EmailPurpose, at) -> None:
        table = self._table("email_token")
        with self._use_connection(write=True) as connection:
            connection.execute(update(table).where(
                table.c.account_id == account_id, table.c.purpose == purpose, table.c.used_at.is_(None)
            ).values(used_at=at))

    def verify_account_email(self, account_id: str, at) -> Account | None:
        table = self._table("account")
        with self._use_connection(write=True) as connection:
            row = connection.execute(update(table).where(table.c.id == account_id).values(
                email_verified_at=at, updated_at=at
            ).returning(table)).mappings().first()
            return _account(row) if row is not None else None

    def update_password(self, account_id: str, password_hash: str, at) -> None:
        table = self._table("account")
        with self._use_connection(write=True) as connection:
            connection.execute(update(table).where(table.c.id == account_id).values(
                password_hash=password_hash, updated_at=at
            ))

    def failure_times(self, bucket: str, since) -> list:
        table = self._table("rate_limit_event")
        with self._use_connection() as connection:
            return list(
                connection.scalars(
                    select(table.c.at)
                    .where(table.c.bucket == bucket, table.c.at > since)
                    .order_by(table.c.at)
                )
            )

    def add_failure(self, bucket: str, at) -> None:
        table = self._table("rate_limit_event")
        with self._use_connection(write=True) as connection:
            connection.execute(insert(table).values(bucket=bucket, at=at))

    def append_audit(self, event: AuditEvent) -> None:
        table = self._table("audit_event")
        with self._use_connection(write=True) as connection:
            connection.execute(
                insert(table).values(
                    at=event.at,
                    actor_id=event.actor_id,
                    action=event.action,
                    target_kind=event.target_kind,
                    target_id=event.target_id,
                    ip=event.ip,
                    meta=event.meta,
                )
            )

    @contextmanager
    def _use_connection(self, *, write: bool = False) -> Iterator[Connection]:
        current = self._connection.get()
        if current is not None:
            yield current
        elif write:
            with self.engine.begin() as connection:
                yield connection
        else:
            with self.engine.connect() as connection:
                yield connection

    def _table(self, name: str):
        return self._tables[f"{self.schema}.{name}" if self.schema else name]


def _advisory_lock_id(key: str) -> int:
    return int.from_bytes(sha256(key.encode("utf-8")).digest()[:8], "big", signed=True)


def _account_values(account: Account) -> dict[str, object]:
    return {
        "id": account.id,
        "email": account.email,
        "email_normalized": account.email_normalized,
        "display_name": account.display_name,
        "role": account.role,
        "status": account.status,
        "email_verified_at": account.email_verified_at,
        "build_monthly_max": account.build_monthly_max,
        "created_at": account.created_at,
        "updated_at": account.updated_at,
        "last_login_at": account.last_login_at,
    }


def _account(row) -> Account:
    return Account(
        id=str(row["id"]),
        email=row["email"],
        email_normalized=row["email_normalized"],
        display_name=row["display_name"],
        role=row["role"],
        status=row["status"],
        email_verified_at=row["email_verified_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        last_login_at=row["last_login_at"],
        build_monthly_max=row["build_monthly_max"],
    )


def _session(row) -> AuthSession:
    return AuthSession(
        id=str(row["id"]),
        account_id=str(row["account_id"]),
        token_hash=bytes(row["token_hash"]),
        csrf_token=row["csrf_token"],
        created_at=row["created_at"],
        last_seen_at=row["last_seen_at"],
        expires_at=row["expires_at"],
        ip=str(row["ip"]) if row["ip"] is not None else None,
        user_agent=row["user_agent"],
    )


def _email_token(row) -> EmailToken:
    return EmailToken(
        id=str(row["id"]), account_id=str(row["account_id"]), purpose=row["purpose"],
        token_hash=bytes(row["token_hash"]), email_normalized=row["email_normalized"],
        expires_at=row["expires_at"], used_at=row["used_at"], created_at=row["created_at"],
    )
