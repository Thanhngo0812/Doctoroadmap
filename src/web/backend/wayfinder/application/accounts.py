from __future__ import annotations

import hashlib
import re
import secrets
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from math import ceil
from typing import Literal
from uuid import uuid4

from doc2roadmap.application.ports.phase_b import ClockPort

from wayfinder.application.auth_ports import AuditEvent, AuthStore, PasswordHasher
from wayfinder.domain.auth import Account, AccountRole, AuthSession


@dataclass(frozen=True, slots=True)
class AuthPolicy:
    session_idle_days: int = 7
    session_absolute_days: int = 30
    login_max_failures: int = 5
    login_failure_window_minutes: int = 15


@dataclass(frozen=True, slots=True)
class Credentials:
    account: Account
    password_hash: str


@dataclass(frozen=True, slots=True)
class SessionGrant:
    token: str
    account: Account
    session: AuthSession


@dataclass(frozen=True, slots=True)
class SessionIdentity:
    account: Account
    session: AuthSession


@dataclass(frozen=True, slots=True)
class RegistrationResult:
    session: SessionGrant | None


AuthErrorCode = Literal[
    "validation", "invalid_credentials", "rate_limited", "unauthenticated", "account_disabled", "conflict"
]


class AuthError(Exception):
    def __init__(self, code: AuthErrorCode, message: str, *, retry_after: int | None = None,
                 fields: list[dict[str, str]] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retry_after = retry_after
        self.fields = fields


_INVALID_CREDENTIALS = "Email hoặc mật khẩu không đúng."
_UNAUTHENTICATED = "Vui lòng đăng nhập để tiếp tục."
_ACCOUNT_DISABLED = "Tài khoản đã bị khoá."
_EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+\Z")


class AccountService:
    def __init__(self, store: AuthStore, hasher: PasswordHasher, clock: ClockPort, policy: AuthPolicy,
                 common_passwords: frozenset[str]) -> None:
        self.store = store
        self.hasher = hasher
        self.clock = clock
        self.policy = policy
        self.common_passwords = frozenset(password.casefold() for password in common_passwords)

    def register(self, email: str, password: str, display_name: str, *, ip: str | None,
                 user_agent: str | None) -> RegistrationResult:
        normalized, email = self._validated_identity(email, password, display_name)
        now = self.clock.now()
        account = Account(
            id=str(uuid4()), email=email, email_normalized=normalized, display_name=display_name.strip(),
            role="user", status="active", email_verified_at=None, created_at=now, updated_at=now,
            last_login_at=now,
        )
        password_hash = self.hasher.hash(password)
        session_grant = self._new_session(account, now, ip, user_agent)
        duplicate = False
        with self.store.atomic([f"account:{normalized}"]):
            if not self.store.create_account(account, password_hash):
                duplicate = True
            else:
                self.store.save_session(session_grant.session)
                self.store.append_audit(AuditEvent(now, account.id, "login_ok", "account", account.id, ip))
        return RegistrationResult(None if duplicate else session_grant)

    def login(self, email: str, password: str, *, ip: str | None, user_agent: str | None) -> SessionGrant:
        normalized = email.strip().lower() if isinstance(email, str) else ""
        email_bucket = f"login:email:{hashlib.sha256(normalized.encode()).hexdigest()}"
        ip_bucket = f"login:ip:{ip or 'unknown'}"
        window = timedelta(minutes=self.policy.login_failure_window_minutes)
        pending: AuthError | None = None
        grant: SessionGrant | None = None
        with self.store.atomic([email_bucket, ip_bucket]):
            now = self.clock.now()
            retry_after = self._retry_after((email_bucket, ip_bucket), now - window, now, window)
            if retry_after is not None:
                pending = AuthError("rate_limited", "Bạn đã thử quá nhiều lần. Vui lòng thử lại sau.",
                                    retry_after=retry_after)
            else:
                credentials = self.store.get_credentials(normalized)
                encoded = credentials.password_hash if credentials else self.hasher.dummy_hash
                valid = self.hasher.verify(encoded, password if isinstance(password, str) else "")
                if credentials is None or not valid:
                    self.store.add_failure(email_bucket, now)
                    self.store.add_failure(ip_bucket, now)
                    self.store.append_audit(AuditEvent(now, credentials.account.id if credentials else None,
                                                       "login_failed", "account" if credentials else None,
                                                       credentials.account.id if credentials else None, ip))
                    pending = AuthError("invalid_credentials", _INVALID_CREDENTIALS)
                elif credentials.account.status == "disabled":
                    self.store.append_audit(AuditEvent(now, credentials.account.id, "login_failed", "account",
                                                       credentials.account.id, ip))
                    pending = AuthError("account_disabled", _ACCOUNT_DISABLED)
                else:
                    updated_account = replace(credentials.account, last_login_at=now, updated_at=now)
                    grant = self._new_session(updated_account, now, ip, user_agent)
                    self.store.save_session(grant.session)
                    self.store.update_last_login(credentials.account.id, now)
                    self.store.append_audit(AuditEvent(now, credentials.account.id, "login_ok", "account",
                                                       credentials.account.id, ip))
        if pending is not None:
            raise pending
        assert grant is not None
        return grant

    def me(self, raw_token: str | None) -> SessionIdentity:
        if not raw_token:
            raise AuthError("unauthenticated", _UNAUTHENTICATED)
        token_hash = self._token_hash(raw_token)
        pending: AuthError | None = None
        identity: SessionIdentity | None = None
        with self.store.atomic([f"session:{token_hash.hex()}"]):
            now = self.clock.now()
            session = self.store.get_session(token_hash)
            if session is None:
                pending = AuthError("unauthenticated", _UNAUTHENTICATED)
            else:
                account = self.store.get_account(session.account_id)
                if account is None:
                    self.store.delete_session(session.id)
                    pending = AuthError("unauthenticated", _UNAUTHENTICATED)
                elif account.status == "disabled":
                    self.store.delete_account_sessions(account.id)
                    pending = AuthError("account_disabled", _ACCOUNT_DISABLED)
                elif (now >= session.expires_at or
                      now - session.last_seen_at >= timedelta(days=self.policy.session_idle_days)):
                    self.store.delete_session(session.id)
                    pending = AuthError("unauthenticated", _UNAUTHENTICATED)
                else:
                    if now - session.last_seen_at > timedelta(minutes=5):
                        self.store.touch_session(session.id, now)
                        session = replace(session, last_seen_at=now)
                    identity = SessionIdentity(account, session)
        if pending is not None:
            raise pending
        assert identity is not None
        return identity

    def logout(self, raw_token: str | None, *, ip: str | None) -> None:
        if not raw_token:
            return
        token_hash = self._token_hash(raw_token)
        now = self.clock.now()
        with self.store.atomic([f"session:{token_hash.hex()}"]):
            session = self.store.get_session(token_hash)
            if session is not None:
                self.store.delete_session(session.id)
                self.store.append_audit(AuditEvent(now, session.account_id, "logout", "account",
                                                   session.account_id, ip))

    def create_admin(self, email: str, password: str, display_name: str = "Quản trị viên") -> Account:
        normalized, email = self._validated_identity(email, password, display_name)
        now = self.clock.now()
        account = Account(
            id=str(uuid4()), email=email, email_normalized=normalized, display_name=display_name.strip(),
            role="admin", status="active", email_verified_at=now, created_at=now, updated_at=now,
        )
        password_hash = self.hasher.hash(password)
        duplicate = False
        with self.store.atomic([f"account:{normalized}"]):
            if not self.store.create_account(account, password_hash):
                duplicate = True
            else:
                self.store.append_audit(AuditEvent(now, account.id, "admin_account_created", "account", account.id))
        if duplicate:
            raise AuthError("conflict", "Tài khoản đã tồn tại.")
        return account

    def _validated_identity(self, email: str, password: str, display_name: str) -> tuple[str, str]:
        original = email.strip() if isinstance(email, str) else ""
        normalized = original.lower()
        errors: list[dict[str, str]] = []
        if len(normalized) > 254 or not _EMAIL_RE.fullmatch(normalized):
            errors.append({"loc": "email", "message": "Địa chỉ email không hợp lệ."})
        if not isinstance(password, str) or not 8 <= len(password) <= 128:
            errors.append({"loc": "password", "message": "Mật khẩu phải có từ 8 đến 128 ký tự."})
        elif password.casefold() in self.common_passwords:
            errors.append({"loc": "password", "message": "Mật khẩu nằm trong danh sách phổ biến."})
        if not isinstance(display_name, str) or not 1 <= len(display_name.strip()) <= 60:
            errors.append({"loc": "display_name", "message": "Tên hiển thị phải có từ 1 đến 60 ký tự."})
        if errors:
            raise AuthError("validation", "Thông tin đăng ký không hợp lệ.", fields=errors)
        return normalized, original

    def _new_session(self, account: Account, now: datetime, ip: str | None,
                     user_agent: str | None) -> SessionGrant:
        token = secrets.token_urlsafe(32)
        session = AuthSession(
            id=str(uuid4()), account_id=account.id, token_hash=self._token_hash(token),
            csrf_token=secrets.token_urlsafe(32), created_at=now, last_seen_at=now,
            expires_at=now + timedelta(days=self.policy.session_absolute_days), ip=ip,
            user_agent=user_agent[:200] if user_agent else None,
        )
        return SessionGrant(token, account, session)

    @staticmethod
    def _token_hash(raw_token: str) -> bytes:
        return hashlib.sha256(raw_token.encode("utf-8")).digest()

    def _retry_after(self, buckets: tuple[str, ...], since: datetime, now: datetime,
                     window: timedelta) -> int | None:
        retry_after = None
        for index, bucket in enumerate(buckets):
            times = self.store.failure_times(bucket, since)
            limit = self.policy.login_max_failures if index == 0 else 20
            if len(times) >= limit:
                remaining = ceil((times[0] + window - now).total_seconds())
                retry_after = max(retry_after or 0, remaining, 1)
        return retry_after
