from collections.abc import Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Literal, Protocol

from wayfinder.domain.auth import Account, AuthSession

if TYPE_CHECKING:
    from wayfinder.application.accounts import Credentials


@dataclass(frozen=True, slots=True)
class AuditEvent:
    at: datetime
    actor_id: str | None
    action: str
    target_kind: str | None = None
    target_id: str | None = None
    ip: str | None = None
    meta: dict[str, object] = field(default_factory=dict)


EmailPurpose = Literal["verify_email", "reset_password"]


@dataclass(frozen=True, slots=True)
class EmailToken:
    id: str
    account_id: str
    purpose: EmailPurpose
    token_hash: bytes
    email_normalized: str
    expires_at: datetime
    used_at: datetime | None
    created_at: datetime


class PasswordHasher(Protocol):
    @property
    def dummy_hash(self) -> str: ...

    def hash(self, password: str) -> str: ...

    def verify(self, encoded: str, password: str) -> bool: ...


class AuthStore(Protocol):
    def atomic(self, keys: Sequence[str]) -> AbstractContextManager[None]: ...

    def get_credentials(self, normalized_email: str) -> "Credentials | None": ...

    def create_account(self, account: Account, password_hash: str) -> bool: ...

    def get_account(self, account_id: str) -> Account | None: ...

    def update_last_login(self, account_id: str, at: datetime) -> None: ...

    def get_session(self, token_hash: bytes) -> AuthSession | None: ...

    def save_session(self, session: AuthSession) -> None: ...

    def touch_session(self, session_id: str, at: datetime) -> None: ...

    def delete_session(self, session_id: str) -> None: ...

    def delete_account_sessions(self, account_id: str) -> None: ...

    def create_email_token(self, token: EmailToken) -> None: ...

    def get_email_token(self, token_hash: bytes) -> EmailToken | None: ...

    def consume_email_token(self, token_id: str, at: datetime) -> bool: ...

    def consume_account_email_tokens(self, account_id: str, purpose: EmailPurpose, at: datetime) -> None: ...

    def verify_account_email(self, account_id: str, at: datetime) -> Account | None: ...

    def update_password(self, account_id: str, password_hash: str, at: datetime) -> None: ...

    def failure_times(self, bucket: str, since: datetime) -> list[datetime]: ...

    def add_failure(self, bucket: str, at: datetime) -> None: ...

    def append_audit(self, event: AuditEvent) -> None: ...
