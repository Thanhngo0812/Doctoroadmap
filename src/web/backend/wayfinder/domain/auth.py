from dataclasses import dataclass
from datetime import datetime
from typing import Literal


AccountRole = Literal["user", "admin"]
AccountStatus = Literal["active", "disabled"]


@dataclass(frozen=True, slots=True)
class Account:
    id: str
    email: str
    email_normalized: str
    display_name: str
    role: AccountRole
    status: AccountStatus
    email_verified_at: datetime | None
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None = None
    build_monthly_max: int | None = None


@dataclass(frozen=True, slots=True)
class Actor:
    user_id: str | None
    role: AccountRole | None
    email_verified: bool
    status: AccountStatus | Literal["guest"]


@dataclass(frozen=True, slots=True)
class AuthSession:
    id: str
    account_id: str
    token_hash: bytes
    csrf_token: str
    created_at: datetime
    last_seen_at: datetime
    expires_at: datetime
    ip: str | None = None
    user_agent: str | None = None


@dataclass(frozen=True, slots=True)
class Decision:
    allowed: bool
    code: str | None = None


def decide(actor: Actor | None, action: str, course: object | None, membership: object | None) -> Decision:
    if actor is None or actor.status == "guest":
        return Decision(True) if action in {"register", "login"} else Decision(False, "unauthenticated")
    if actor.status == "disabled":
        return Decision(False, "account_disabled")
    if action == "invite_by_email" and not actor.email_verified:
        return Decision(False, "email_unverified")
    if action in {"me", "logout"}:
        return Decision(True)
    if action == "list_courses":
        return Decision(True)
    if action == "seed_samples":
        return Decision(actor.role == "admin", None if actor.role == "admin" else "forbidden")
    if action == "create_course":
        return Decision(True)
    if action in {"read_course", "learn", "update_course", "join_sample"}:
        if course is None:
            return Decision(False, "not_found")
        if action == "join_sample" and course.is_sample:
            return Decision(True)
        if membership is None:
            return Decision(False, "not_found")
        if action == "join_sample":
            return Decision(False, "not_found")
        if action == "update_course" and (membership.role != "owner" or course.owner_id != actor.user_id):
            return Decision(False, "forbidden")
        return Decision(True)
    return Decision(False, "forbidden")
