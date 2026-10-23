"""W-11 share links after the accepted W-14 build queue."""
from alembic import op

revision = 'w11_0007'
down_revision = 'w14_0006'
branch_labels = depends_on = None


def upgrade():
    op.execute("""
    CREATE TABLE share_link (
      id uuid PRIMARY KEY,
      course_id uuid NOT NULL REFERENCES course ON DELETE CASCADE,
      token_hash bytea NOT NULL UNIQUE CHECK(octet_length(token_hash)=32),
      token_tail text NOT NULL CHECK(length(token_tail)=6),
      created_by uuid REFERENCES account ON DELETE SET NULL,
      expires_at timestamptz,
      max_uses integer CHECK(max_uses IS NULL OR max_uses>0),
      use_count integer NOT NULL DEFAULT 0 CHECK(use_count>=0),
      revoked_at timestamptz, created_at timestamptz NOT NULL,
      CHECK(max_uses IS NULL OR use_count<=max_uses)
    );
    CREATE INDEX ix_share_link_course_created ON share_link(course_id,created_at);
    """)


def downgrade():
    op.execute('DROP TABLE share_link')
