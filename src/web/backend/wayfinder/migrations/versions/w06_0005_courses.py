"""W-06 courses and memberships after W-03 email recovery."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "w06_0005"
down_revision = "w03_0004"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("course",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("owner_id", UUID(as_uuid=False), sa.ForeignKey("account.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("doc_id", sa.Text(), nullable=False),
        # W-14 adds the FK when its build table exists.
        sa.Column("build_id", UUID(as_uuid=False)),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("published_graph_version", sa.Integer()),
        sa.Column("is_sample", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("module_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source_public_id", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("length(btrim(title)) BETWEEN 1 AND 120", name="ck_course_title"),
        sa.CheckConstraint("length(description) <= 1000", name="ck_course_description"),
        sa.CheckConstraint("status IN ('building','ready','failed')", name="ck_course_status"),
        sa.CheckConstraint("status <> 'ready' OR published_graph_version > 0 AND published_graph_version IS NOT NULL", name="ck_course_ready_graph"),
        sa.CheckConstraint("module_count >= 0", name="ck_course_module_count"))
    op.create_index("ix_course_owner", "course", ["owner_id"])
    op.create_index("ix_course_doc", "course", ["doc_id"])
    op.create_index("ix_course_sample", "course", ["is_sample"], postgresql_where=sa.text("is_sample"))
    op.create_table("membership",
        sa.Column("course_id", UUID(as_uuid=False), sa.ForeignKey("course.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("account_id", UUID(as_uuid=False), sa.ForeignKey("account.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role", sa.Text(), nullable=False), sa.Column("via", sa.Text(), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_active_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("role IN ('owner','learner')", name="ck_membership_role"),
        sa.CheckConstraint("via IN ('owner','link','email','sample')", name="ck_membership_via"))
    op.create_index("ix_membership_account", "membership", ["account_id"])
    op.create_index("uq_membership_owner", "membership", ["course_id"], unique=True,
                    postgresql_where=sa.text("role='owner'"))
    # Defer the matching-owner check until both rows have been inserted.
    op.execute("""CREATE FUNCTION check_course_owner() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE ids uuid[]; cid uuid;
    BEGIN
      IF TG_TABLE_NAME = 'course' THEN ids := ARRAY[NEW.id, OLD.id];
      ELSE ids := ARRAY[NEW.course_id, OLD.course_id]; END IF;
      FOREACH cid IN ARRAY ids LOOP
      IF EXISTS (SELECT 1 FROM course c WHERE c.id=cid AND NOT EXISTS
         (SELECT 1 FROM membership m WHERE m.course_id=c.id AND m.account_id=c.owner_id AND m.role='owner'))
      THEN RAISE EXCEPTION 'course requires its owner membership' USING ERRCODE='23514'; END IF;
      END LOOP;
      RETURN NULL;
    END $$""")
    for table in ("course", "membership"):
        op.execute(f"CREATE CONSTRAINT TRIGGER ck_{table}_owner AFTER INSERT OR UPDATE OR DELETE ON {table} "
                   "DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION check_course_owner()")


def downgrade():
    op.drop_table("membership")
    op.drop_table("course")
    op.execute("DROP FUNCTION check_course_owner()")
