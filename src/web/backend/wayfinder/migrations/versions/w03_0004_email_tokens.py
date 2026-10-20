"""W-03: one-use email verification and password reset tokens."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "w03_0004"
down_revision = "w02_0003"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "email_token",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("account_id", postgresql.UUID(as_uuid=False),
                  sa.ForeignKey("account.id", ondelete="CASCADE"), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column("token_hash", sa.LargeBinary(32), nullable=False, unique=True),
        sa.Column("email_normalized", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("purpose IN ('verify_email', 'reset_password')", name="ck_email_token_purpose"),
        sa.CheckConstraint("octet_length(token_hash) = 32", name="ck_email_token_hash_length"),
    )
    op.create_index("ix_email_token_account_purpose_created", "email_token",
                    ["account_id", "purpose", "created_at"])
    op.create_index("ix_email_token_expires_at", "email_token", ["expires_at"])


def downgrade():
    op.drop_table("email_token")
