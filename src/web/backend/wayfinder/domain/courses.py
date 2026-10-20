from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Course:
    id: str
    owner_id: str
    doc_id: str
    title: str
    description: str
    status: str
    published_graph_version: int | None
    is_sample: bool
    module_count: int
    source_public_id: str | None
    created_at: datetime
    updated_at: datetime
    build_id: str | None = None


@dataclass(frozen=True, slots=True)
class Membership:
    course_id: str
    account_id: str
    role: str
    via: str
    joined_at: datetime
    last_active_at: datetime | None
