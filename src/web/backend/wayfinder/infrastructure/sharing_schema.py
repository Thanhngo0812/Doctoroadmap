from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, LargeBinary, MetaData, Table, Text
from sqlalchemy.dialects.postgresql import UUID


def sharing_metadata() -> MetaData:
    metadata = MetaData()
    # FK declarations for SQL construction; Alembic owns schema creation.
    Table("account", metadata, Column("id", UUID(as_uuid=False), primary_key=True))
    Table("course", metadata, Column("id", UUID(as_uuid=False), primary_key=True))
    links = Table(
        "share_link", metadata,
        Column("id", UUID(as_uuid=False), primary_key=True),
        Column("course_id", UUID(as_uuid=False), ForeignKey("course.id", ondelete="CASCADE"), nullable=False),
        Column("token_hash", LargeBinary(32), nullable=False, unique=True),
        Column("token_tail", Text, nullable=False),
        Column("created_by", UUID(as_uuid=False), ForeignKey("account.id", ondelete="SET NULL")),
        Column("expires_at", DateTime(timezone=True)),
        Column("max_uses", Integer),
        Column("use_count", Integer, nullable=False, server_default="0"),
        Column("revoked_at", DateTime(timezone=True)),
        Column("created_at", DateTime(timezone=True), nullable=False),
        CheckConstraint("octet_length(token_hash) = 32", name="ck_share_link_token_hash_length"),
        CheckConstraint("length(token_tail) = 6", name="ck_share_link_token_tail_length"),
        CheckConstraint("max_uses IS NULL OR max_uses > 0", name="ck_share_link_max_uses"),
        CheckConstraint("use_count >= 0", name="ck_share_link_use_count"),
        CheckConstraint("max_uses IS NULL OR use_count <= max_uses", name="ck_share_link_use_count_max"),
    )
    Index("ix_share_link_course_created", links.c.course_id, links.c.created_at)
    return metadata
