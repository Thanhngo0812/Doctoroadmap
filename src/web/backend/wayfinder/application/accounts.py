from __future__ import annotations

import hashlib
import logging
import re
import secrets
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from math import ceil
from typing import Literal
from uuid import uuid4

from doc2roadmap.application.ports.phase_b import ClockPort

from wayfinder.application.auth_ports import AuditEvent, AuthStore, EmailPurpose, EmailToken, PasswordHasher
from wayfinder.domain.auth import Account, AccountRole, AuthSession
from wayfinder.application.ports import Mailer


@dataclass(frozen=True, slots=True)
class AuthPolicy:
    session_idle_days: int = 7
    session_absolute_days: int = 30
    login_max_failures: int = 5
    login_failure_window_minutes: int = 15
    email_verify_ttl_hours: int = 24
    resend_verification_per_hour: int = 3
    password_reset_ttl_minutes: int = 60
    public_base_url: str = "http://127.0.0.1:8000"


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
    "validation", "invalid_credentials", "rate_limited", "unauthenticated", "account_disabled", "conflict",
    "link_invalid",
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
_VERIFY_SENT = "Nếu email chưa được xác minh, bạn sẽ nhận được thư xác minh mới."
_RESET_REQUESTED = "Nếu email có tài khoản, bạn sẽ nhận được thư đặt lại mật khẩu."
_RATE_LIMITED = "Bạn đã yêu cầu quá nhiều lần. Vui lòng thử lại sau."
_TOKEN_ERRORS = {
    "token_invalid": "Liên kết không hợp lệ.",
    "token_expired": "Liên kết đã hết hạn.",
    "token_used": "Liên kết đã được sử dụng.",
}
_EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+\Z")
logger = logging.getLogger(__name__)


class AccountService:
    def __init__(self, store: AuthStore, hasher: PasswordHasher, clock: ClockPort, policy: AuthPolicy,
                 common_passwords: frozenset[str], *, mailer: Mailer | None = None) -> None:
        self.store = store
        self.hasher = hasher
        self.clock = clock
        self.policy = policy
        self.common_passwords = frozenset(password.casefold() for password in common_passwords)
        self.mailer = mailer

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
        raw_token, email_token = self._new_email_token(
            account, "verify_email", now, timedelta(hours=self.policy.email_verify_ttl_hours)
        )
        duplicate = False
        existing = None
        with self.store.atomic([f"account:{normalized}"]):
            if not self.store.create_account(account, password_hash):
                duplicate = True
                credentials = self.store.get_credentials(normalized)
                existing = credentials.account if credentials else None
            else:
                self.store.save_session(session_grant.session)
                self.store.create_email_token(email_token)
                self.store.append_audit(AuditEvent(now, account.id, "login_ok", "account", account.id, ip))
        if duplicate and existing is not None:
            self._send_account_email("existing_account", existing)
        elif not duplicate:
            self._send_account_email("verify_email", account, raw_token,
                                     valid_for=f"{self.policy.email_verify_ttl_hours} giờ")
        return RegistrationResult(None if duplicate else session_grant)

    def verify_email(self, raw_token: str, *, ip: str | None = None) -> Account:
        token_hash = self._token_hash(raw_token)
        candidate = self.store.get_email_token(token_hash)
        keys = [f"email-token:{token_hash.hex()}"]
        if candidate is not None:
            keys.append(f"account:{candidate.account_id}")
        now = self.clock.now()
        pending: AuthError | None = None
        verified: Account | None = None
        with self.store.atomic(keys):
            now = self.clock.now()
            token = self.store.get_email_token(token_hash)
            account = self.store.get_account(token.account_id) if token else None
            failure = self._token_failure(token, account, "verify_email", now)
            if failure is not None:
                pending = failure
            elif not self.store.consume_email_token(token.id, now):
                pending = self._token_error("token_used")
            else:
                self.store.consume_account_email_tokens(token.account_id, "verify_email", now)
                verified = self.store.verify_account_email(token.account_id, now)
                if verified is None:
                    pending = self._token_error("token_invalid")
                else:
                    self.store.append_audit(AuditEvent(now, verified.id, "email_verified", "account",
                                                       verified.id, ip))
        if pending is not None:
            raise pending
        assert verified is not None
        return verified

    def resend_verification(self, account_id: str, *, ip: str | None = None) -> str:
        bucket = f"verify:account:{account_id}"
        window = timedelta(hours=1)
        pending: AuthError | None = None
        account = None
        raw_token = None
        with self.store.atomic([bucket, f"account:{account_id}"]):
            now = self.clock.now()
            retry_after = self._rate_limit_retry_after(bucket, self.policy.resend_verification_per_hour,
                                                       window, now)
            if retry_after is not None:
                pending = AuthError("rate_limited", _RATE_LIMITED, retry_after=retry_after)
            else:
                self.store.add_failure(bucket, now)
                account = self.store.get_account(account_id)
                if account is None:
                    pending = AuthError("unauthenticated", _UNAUTHENTICATED)
                elif account.email_verified_at is None:
                    self.store.consume_account_email_tokens(account.id, "verify_email", now)
                    raw_token, email_token = self._new_email_token(
                        account, "verify_email", now, timedelta(hours=self.policy.email_verify_ttl_hours)
                    )
                    self.store.create_email_token(email_token)
        if pending is not None:
            raise pending
        if account is not None and raw_token is not None:
            self._send_account_email("verify_email", account, raw_token,
                                     valid_for=f"{self.policy.email_verify_ttl_hours} giờ")
        return _VERIFY_SENT

    def request_password_reset(self, email: str, *, ip: str | None = None) -> str:
        normalized = email.strip().lower() if isinstance(email, str) else ""
        bucket = f"reset:{hashlib.sha256(normalized.encode()).hexdigest()}"
        window = timedelta(hours=1)
        pending: AuthError | None = None
        account = None
        raw_token = None
        with self.store.atomic([bucket]):
            now = self.clock.now()
            retry_after = self._rate_limit_retry_after(bucket, 3, window, now)
            if retry_after is not None:
                pending = AuthError("rate_limited", _RATE_LIMITED, retry_after=retry_after)
            else:
                self.store.add_failure(bucket, now)
                credentials = self.store.get_credentials(normalized)
                account = credentials.account if credentials and credentials.account.status == "active" else None
                if account is not None:
                    raw_token, email_token = self._new_email_token(
                        account, "reset_password", now,
                        timedelta(minutes=self.policy.password_reset_ttl_minutes),
                    )
                    self.store.create_email_token(email_token)
                self.store.append_audit(AuditEvent(now, account.id if account else None,
                                                   "password_reset_requested", "account" if account else None,
                                                   account.id if account else None, ip))
        if pending is not None:
            raise pending
        if account is not None and raw_token is not None:
            self._send_account_email("reset_password", account, raw_token,
                                     valid_for=f"{self.policy.password_reset_ttl_minutes} phút")
        return _RESET_REQUESTED

    def reset_password(self, raw_token: str, password: str, *, ip: str | None = None) -> None:
        self._validate_password(password)
        token_hash = self._token_hash(raw_token)
        candidate = self.store.get_email_token(token_hash)
        now = self.clock.now()
        candidate_account = self.store.get_account(candidate.account_id) if candidate else None
        failure = self._token_failure(candidate, candidate_account, "reset_password", now)
        if failure is not None:
            raise failure
        password_hash = self.hasher.hash(password)
        keys = [f"email-token:{token_hash.hex()}"]
        if candidate is not None:
            keys.extend((f"account:{candidate.account_id}", f"account:{candidate.email_normalized}"))
        pending: AuthError | None = None
        with self.store.atomic(keys):
            now = self.clock.now()
            token = self.store.get_email_token(token_hash)
            account = self.store.get_account(token.account_id) if token else None
            failure = self._token_failure(token, account, "reset_password", now)
            if failure is not None:
                pending = failure
            elif not self.store.consume_email_token(token.id, now):
                pending = self._token_error("token_used")
            else:
                self.store.consume_account_email_tokens(token.account_id, "reset_password", now)
                self.store.update_password(token.account_id, password_hash, now)
                self.store.delete_account_sessions(token.account_id)
                self.store.append_audit(AuditEvent(now, token.account_id, "password_reset_done", "account",
                                                   token.account_id, ip))
        if pending is not None:
            raise pending

    def login(self, email: str, password: str, *, ip: str | None, user_agent: str | None) -> SessionGrant:
        normalized = email.strip().lower() if isinstance(email, str) else ""
        email_bucket = f"login:email:{hashlib.sha256(normalized.encode()).hexdigest()}"
        ip_bucket = f"login:ip:{ip or 'unknown'}"
        window = timedelta(minutes=self.policy.login_failure_window_minutes)
        pending: AuthError | None = None
        grant: SessionGrant | None = None
        with self.store.atomic([email_bucket, ip_bucket, f"account:{normalized}"]):
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
        try:
            self._validate_password(password)
        except AuthError as exc:
            errors.extend(exc.fields or [])
        if not isinstance(display_name, str) or not 1 <= len(display_name.strip()) <= 60:
            errors.append({"loc": "display_name", "message": "Tên hiển thị phải có từ 1 đến 60 ký tự."})
        if errors:
            raise AuthError("validation", "Thông tin đăng ký không hợp lệ.", fields=errors)
        return normalized, original

    def _validate_password(self, password: str) -> None:
        if not isinstance(password, str) or not 8 <= len(password) <= 128:
            raise AuthError("validation", "Mật khẩu không hợp lệ.",
                            fields=[{"loc": "password", "message": "Mật khẩu phải có từ 8 đến 128 ký tự."}])
        if password.casefold() in self.common_passwords:
            raise AuthError("validation", "Mật khẩu không hợp lệ.",
                            fields=[{"loc": "password", "message": "Mật khẩu nằm trong danh sách phổ biến."}])

    def _new_email_token(self, account: Account, purpose: EmailPurpose, now: datetime,
                         lifetime: timedelta) -> tuple[str, EmailToken]:
        raw = secrets.token_urlsafe(32)
        return raw, EmailToken(
            id=str(uuid4()), account_id=account.id, purpose=purpose,
            token_hash=self._token_hash(raw), email_normalized=account.email_normalized,
            expires_at=now + lifetime, used_at=None, created_at=now,
        )

    def _send_account_email(self, kind: str, account: Account, raw_token: str | None = None,
                            *, valid_for: str | None = None) -> None:
        if self.mailer is None:
            return
        base_url = self.policy.public_base_url.rstrip("/")
        if kind == "verify_email":
            action_url = f"{base_url}/xac-minh#token={raw_token}"
        elif kind == "reset_password":
            action_url = f"{base_url}/dat-lai-mat-khau#token={raw_token}"
        else:
            action_url = f"{base_url}/dang-nhap"
        from wayfinder.application.email_templates import render_account_email

        content = render_account_email(kind, display_name=account.display_name, action_url=action_url,
                                       base_url=base_url, valid_for=valid_for)
        try:
            self.mailer.send(account.email, content.subject, content.text, html_body=content.html)
        except Exception:
            # Delivery may fail after the account/token transaction; never expose the mailbox or token.
            logger.warning("Account email delivery unavailable")

    @staticmethod
    def _token_error(kind: str) -> AuthError:
        message = _TOKEN_ERRORS[kind]
        return AuthError("link_invalid", message,
                         fields=[{"loc": "token", "type": kind, "message": message}])

    def _token_failure(self, token: EmailToken | None, account: Account | None,
                       purpose: EmailPurpose, now: datetime) -> AuthError | None:
        if token is None or token.purpose != purpose or account is None:
            return self._token_error("token_invalid")
        if token.used_at is not None:
            return self._token_error("token_used")
        if now >= token.expires_at:
            return self._token_error("token_expired")
        if token.email_normalized != account.email_normalized:
            return self._token_error("token_invalid")
        return None

    def _rate_limit_retry_after(self, bucket: str, limit: int, window: timedelta,
                                now: datetime) -> int | None:
        times = self.store.failure_times(bucket, now - window)
        if len(times) < limit:
            return None
        return max(ceil((times[0] + window - now).total_seconds()), 1)

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
