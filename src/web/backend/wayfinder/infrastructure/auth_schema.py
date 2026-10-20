from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    MetaData,
    Table,
    Text,
    UniqueConstraint,
    Engine,
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID


def auth_metadata(schema: str | None = None) -> MetaData:
    metadata = MetaData()
    Table(
        "account",
        metadata,
        Column("id", UUID(as_uuid=False), primary_key=True),
        Column("email", Text, nullable=False),
        Column("email_normalized", Text, nullable=False),
        Column("password_hash", Text, nullable=False),
        Column("display_name", Text, nullable=False),
        Column("role", Text, nullable=False, server_default="user"),
        Column("status", Text, nullable=False, server_default="active"),
        Column("email_verified_at", DateTime(timezone=True)),
        Column("build_monthly_max", Integer),
        Column("created_at", DateTime(timezone=True), nullable=False),
        Column("updated_at", DateTime(timezone=True), nullable=False),
        Column("last_login_at", DateTime(timezone=True)),
        UniqueConstraint("email_normalized", name="uq_account_email_normalized"),
        CheckConstraint("role IN ('user', 'admin')", name="ck_account_role"),
        CheckConstraint("status IN ('active', 'disabled')", name="ck_account_status"),
        CheckConstraint("length(display_name) BETWEEN 1 AND 60", name="ck_account_display_name"),
        schema=schema,
    )
    Table(
        "auth_session",
        metadata,
        Column("id", UUID(as_uuid=False), primary_key=True),
        Column(
            "account_id",
            UUID(as_uuid=False),
            ForeignKey(f"{schema + '.' if schema else ''}account.id", ondelete="CASCADE"),
            nullable=False,
        ),
        Column("token_hash", LargeBinary, nullable=False, unique=True),
        Column("csrf_token", Text, nullable=False),
        Column("created_at", DateTime(timezone=True), nullable=False),
        Column("last_seen_at", DateTime(timezone=True), nullable=False),
        Column("expires_at", DateTime(timezone=True), nullable=False),
        Column("ip", INET),
        Column("user_agent", Text),
        CheckConstraint("octet_length(token_hash) = 32", name="ck_auth_session_token_hash_length"),
        CheckConstraint(
            "user_agent IS NULL OR length(user_agent) <= 200",
            name="ck_auth_session_user_agent_length",
        ),
        schema=schema,
    )
    Index(
        "ix_auth_session_account_id",
        metadata.tables[f"{schema + '.' if schema else ''}auth_session"].c.account_id,
    )
    Index(
        "ix_auth_session_expires_at",
        metadata.tables[f"{schema + '.' if schema else ''}auth_session"].c.expires_at,
    )
    Table(
        "email_token",
        metadata,
        Column("id", UUID(as_uuid=False), primary_key=True),
        Column(
            "account_id",
            UUID(as_uuid=False),
            ForeignKey(f"{schema + '.' if schema else ''}account.id", ondelete="CASCADE"),
            nullable=False,
        ),
        Column("purpose", Text, nullable=False),
        Column("token_hash", LargeBinary(32), nullable=False, unique=True),
        Column("email_normalized", Text, nullable=False),
        Column("expires_at", DateTime(timezone=True), nullable=False),
        Column("used_at", DateTime(timezone=True)),
        Column("created_at", DateTime(timezone=True), nullable=False),
        CheckConstraint("purpose IN ('verify_email', 'reset_password')", name="ck_email_token_purpose"),
        CheckConstraint("octet_length(token_hash) = 32", name="ck_email_token_hash_length"),
        schema=schema,
    )
    email_tokens = metadata.tables[f"{schema + '.' if schema else ''}email_token"]
    Index("ix_email_token_account_purpose_created", email_tokens.c.account_id,
          email_tokens.c.purpose, email_tokens.c.created_at)
    Index("ix_email_token_expires_at", email_tokens.c.expires_at)
    Table(
        "rate_limit_event",
        metadata,
        Column("bucket", Text, nullable=False),
        Column("at", DateTime(timezone=True), nullable=False),
        schema=schema,
    )
    Index(
        "ix_rate_limit_event_bucket_at",
        metadata.tables[f"{schema + '.' if schema else ''}rate_limit_event"].c.bucket,
        metadata.tables[f"{schema + '.' if schema else ''}rate_limit_event"].c.at,
    )
    Table(
        "audit_event",
        metadata,
        Column("id", BigInteger, primary_key=True, autoincrement=True),
        Column("at", DateTime(timezone=True), nullable=False),
        Column("actor_id", UUID(as_uuid=False)),
        Column("action", Text, nullable=False),
        Column("target_kind", Text),
        Column("target_id", Text),
        Column("ip", INET),
        Column("meta", JSONB),
        schema=schema,
    )
    audit = metadata.tables[f"{schema + '.' if schema else ''}audit_event"]
    Index("ix_audit_event_at", audit.c.at)
    Index("ix_audit_event_actor_at", audit.c.actor_id, audit.c.at)
    Index("ix_audit_event_action_at", audit.c.action, audit.c.at)
    return metadata


def create_auth_schema(engine: Engine, *, schema: str | None = None) -> MetaData:
    metadata = auth_metadata(schema)
    metadata.create_all(engine)
    return metadata
