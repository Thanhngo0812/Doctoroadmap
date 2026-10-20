"""W-02: accounts, server-side cookie sessions, throttling and audit.

Frozen schema; do not import mutable runtime metadata into old migrations.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

revision = "w02_0003"
down_revision = "w05_0002"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("account",
        sa.Column("id", pg.UUID(as_uuid=False), primary_key=True),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("email_normalized", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False, server_default="user"),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        sa.Column("email_verified_at", sa.DateTime(timezone=True)),
        sa.Column("build_monthly_max", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("email_normalized", name="uq_account_email_normalized"),
        sa.CheckConstraint("role IN ('user', 'admin')", name="ck_account_role"),
        sa.CheckConstraint("status IN ('active', 'disabled')", name="ck_account_status"),
        sa.CheckConstraint("length(display_name) BETWEEN 1 AND 60", name="ck_account_display_name"))
    op.create_table("auth_session",
        sa.Column("id", pg.UUID(as_uuid=False), primary_key=True),
        sa.Column("account_id", pg.UUID(as_uuid=False), sa.ForeignKey("account.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.LargeBinary(), nullable=False, unique=True),
        sa.Column("csrf_token", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ip", pg.INET()),
        sa.Column("user_agent", sa.Text()),
        sa.CheckConstraint("octet_length(token_hash) = 32", name="ck_auth_session_token_hash_length"),
        sa.CheckConstraint("user_agent IS NULL OR length(user_agent) <= 200", name="ck_auth_session_user_agent_length"))
    op.create_index("ix_auth_session_account_id", "auth_session", ["account_id"])
    op.create_index("ix_auth_session_expires_at", "auth_session", ["expires_at"])
    op.create_table("rate_limit_event",
        sa.Column("bucket", sa.Text(), nullable=False),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_rate_limit_event_bucket_at", "rate_limit_event", ["bucket", "at"])
    op.create_table("audit_event",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor_id", pg.UUID(as_uuid=False)),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("target_kind", sa.Text()),
        sa.Column("target_id", sa.Text()),
        sa.Column("ip", pg.INET()),
        sa.Column("meta", pg.JSONB()))
    op.create_index("ix_audit_event_at", "audit_event", ["at"])
    op.create_index("ix_audit_event_actor_at", "audit_event", ["actor_id", "at"])
    op.create_index("ix_audit_event_action_at", "audit_event", ["action", "at"])


def downgrade():
    for table in ("audit_event", "rate_limit_event", "auth_session", "account"):
        op.drop_table(table)
