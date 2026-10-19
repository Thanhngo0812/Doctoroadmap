"""W-05: shared Phase B cache, records, negative results and usage ledger."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "w05_0002"
down_revision = "w01_0001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("phase_b_cache",
        sa.Column("key", sa.Text(), primary_key=True),
        sa.Column("value", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_table("phase_b_negative",
        sa.Column("key", sa.Text(), primary_key=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("value", postgresql.JSONB()), sa.Column("error_type", sa.Text()),
        sa.Column("error_message", sa.Text()))
    op.create_index("ix_phase_b_negative_expiry", "phase_b_negative", ["expires_at"])
    op.create_table("phase_b_record",
        sa.Column("kind", sa.Text(), primary_key=True), sa.Column("record_id", sa.Text(), primary_key=True),
        sa.Column("owner", sa.Text()), sa.Column("doc_id", sa.Text()),
        sa.Column("value", postgresql.JSONB(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_index("ix_phase_b_record_scope", "phase_b_record", ["kind", "owner", "doc_id"])
    op.create_table("usage_ledger",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(timezone=True)), sa.Column("purpose", sa.Text()),
        sa.Column("model_id", sa.Text()), sa.Column("doc_id", sa.Text()), sa.Column("context_hash", sa.Text()),
        sa.Column("learner_id", sa.Text()), sa.Column("cost_usd", sa.Numeric(12, 6), nullable=False),
        sa.Column("input_tokens", sa.Integer()), sa.Column("output_tokens", sa.Integer()),
        sa.Column("elapsed_ms", sa.Integer()), sa.Column("ttft_ms", sa.Integer()),
        sa.Column("failed", sa.Boolean()), sa.Column("replayed", sa.Boolean()),
        sa.Column("extra", postgresql.JSONB(), nullable=False),
        sa.CheckConstraint("purpose NOT IN ('assistant','document') OR (learner_id IS NOT NULL AND learner_id <> '')",
                           name="ck_usage_personal_learner"))
    op.create_index("ix_usage_learner_day", "usage_ledger", ["learner_id", "created_at"],
                    postgresql_where=sa.text("purpose IN ('assistant','document')"))
    op.create_index("ix_usage_purpose_day", "usage_ledger", ["purpose", "created_at"])
    op.create_index("ix_usage_doc_day", "usage_ledger", ["doc_id", "created_at"])


def downgrade():
    for table in ("usage_ledger", "phase_b_record", "phase_b_negative", "phase_b_cache"):
        op.drop_table(table)
