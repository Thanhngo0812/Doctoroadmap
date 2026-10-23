from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ShareLink:
    id: str
    course_id: str
    token_hash: bytes
    token_tail: str
    created_by: str | None
    expires_at: datetime | None
    max_uses: int | None
    use_count: int
    revoked_at: datetime | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class ShareMember:
    user_id: str
    display_name: str
    role: str
    joined_at: datetime
    last_active_at: datetime | None
    via: str
