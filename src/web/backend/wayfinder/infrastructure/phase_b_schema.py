"""Indexed columns serve queries; JSON preserves the PhaseBStore payload contract."""
from sqlalchemy import (BigInteger, Boolean, CheckConstraint, Column, DateTime, Index,
                        Integer, MetaData, Numeric, Table, Text, func, text)
from sqlalchemy.dialects.postgresql import JSONB


metadata = MetaData()
cache = Table("phase_b_cache", metadata,
    Column("key", Text, primary_key=True), Column("value", JSONB, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()))
negative = Table("phase_b_negative", metadata,
    Column("key", Text, primary_key=True), Column("expires_at", DateTime(timezone=True), nullable=False),
    Column("value", JSONB), Column("error_type", Text), Column("error_message", Text))
Index("ix_phase_b_negative_expiry", negative.c.expires_at)
record = Table("phase_b_record", metadata,
    Column("kind", Text, primary_key=True), Column("record_id", Text, primary_key=True),
    Column("owner", Text), Column("doc_id", Text), Column("value", JSONB, nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()))
Index("ix_phase_b_record_scope", record.c.kind, record.c.owner, record.c.doc_id)
usage = Table("usage_ledger", metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column("created_at", DateTime(timezone=True)), Column("purpose", Text),
    Column("model_id", Text), Column("doc_id", Text), Column("context_hash", Text),
    Column("learner_id", Text), Column("cost_usd", Numeric(12, 6), nullable=False),
    Column("input_tokens", Integer), Column("output_tokens", Integer),
    Column("elapsed_ms", Integer), Column("ttft_ms", Integer),
    Column("failed", Boolean), Column("replayed", Boolean), Column("extra", JSONB, nullable=False),
    CheckConstraint("purpose NOT IN ('assistant','document') OR (learner_id IS NOT NULL AND learner_id <> '')",
                    name="ck_usage_personal_learner"))
Index("ix_usage_learner_day", usage.c.learner_id, usage.c.created_at,
      postgresql_where=text("purpose IN ('assistant','document')"))
Index("ix_usage_purpose_day", usage.c.purpose, usage.c.created_at)
Index("ix_usage_doc_day", usage.c.doc_id, usage.c.created_at)
