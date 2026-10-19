from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime
from threading import RLock

from wayfinder.application.accounts import Credentials
from wayfinder.application.auth_ports import AuditEvent
from wayfinder.domain.auth import Account, AuthSession


class FakeAuthStore:
    """Thread-safe auth store for service tests; values remain inspectable by tests."""

    def __init__(self) -> None:
        self.accounts: dict[str, Account] = {}
        self.credentials_by_email: dict[str, Credentials] = {}
        self.sessions: dict[bytes, AuthSession] = {}
        self.sessions_by_id: dict[str, AuthSession] = {}
        self.failure_events: list[tuple[str, datetime]] = []
        self.audit_events: list[AuditEvent] = []
        self._lock = RLock()

    @contextmanager
    def atomic(self, keys):
        # A global lock makes overlapping multi-bucket attempts serializable in tests.
        with self._lock:
            yield

    def get_credentials(self, normalized_email: str) -> Credentials | None:
        return self.credentials_by_email.get(normalized_email)

    def create_account(self, account: Account, password_hash: str) -> bool:
        if account.email_normalized in self.credentials_by_email:
            return False
        credentials = Credentials(account, password_hash)
        self.accounts[account.id] = account
        self.credentials_by_email[account.email_normalized] = credentials
        return True

    def get_account(self, account_id: str) -> Account | None:
        return self.accounts.get(account_id)

    def update_last_login(self, account_id: str, at: datetime) -> None:
        account = self.accounts[account_id]
        updated = replace(account, last_login_at=at, updated_at=at)
        self.accounts[account_id] = updated
        self.credentials_by_email[updated.email_normalized] = replace(
            self.credentials_by_email[updated.email_normalized], account=updated
        )

    def get_session(self, token_hash: bytes) -> AuthSession | None:
        return self.sessions.get(token_hash)

    def save_session(self, session: AuthSession) -> None:
        self.sessions[session.token_hash] = session
        self.sessions_by_id[session.id] = session

    def touch_session(self, session_id: str, at: datetime) -> None:
        previous = self.sessions_by_id[session_id]
        updated = replace(previous, last_seen_at=at)
        self.sessions_by_id[session_id] = updated
        self.sessions[updated.token_hash] = updated

    def delete_session(self, session_id: str) -> None:
        session = self.sessions_by_id.pop(session_id, None)
        if session is not None:
            self.sessions.pop(session.token_hash, None)

    def delete_account_sessions(self, account_id: str) -> None:
        for session in list(self.sessions_by_id.values()):
            if session.account_id == account_id:
                self.delete_session(session.id)

    def failure_times(self, bucket: str, since: datetime) -> list[datetime]:
        return sorted(at for event_bucket, at in self.failure_events if event_bucket == bucket and at > since)

    def add_failure(self, bucket: str, at: datetime) -> None:
        self.failure_events.append((bucket, at))

    def append_audit(self, event: AuditEvent) -> None:
        self.audit_events.append(event)
