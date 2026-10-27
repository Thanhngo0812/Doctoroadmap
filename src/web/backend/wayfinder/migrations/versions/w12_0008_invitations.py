"""W12 invitations after the accepted W11 sharing schema."""
from alembic import op

revision = 'w12_0008'
down_revision = 'w11_0007'
branch_labels = depends_on = None


def upgrade():
    op.execute("""
    CREATE TABLE invitation (
      id uuid PRIMARY KEY,
      course_id uuid NOT NULL REFERENCES course ON DELETE CASCADE,
      email_normalized text NOT NULL CHECK(email_normalized=lower(btrim(email_normalized))),
      invitee_account_id uuid REFERENCES account ON DELETE CASCADE,
      invited_by uuid REFERENCES account ON DELETE SET NULL,
      token_hash bytea NOT NULL UNIQUE CHECK(octet_length(token_hash)=32),
      status text NOT NULL CHECK(status IN ('pending','accepted','declined','cancelled','expired')),
      expires_at timestamptz NOT NULL, created_at timestamptz NOT NULL, responded_at timestamptz
    );
    CREATE UNIQUE INDEX uq_invitation_pending_course_email ON invitation(course_id,email_normalized) WHERE status='pending';
    CREATE INDEX ix_invitation_invitee_status ON invitation(invitee_account_id,status,expires_at);
    CREATE INDEX ix_invitation_pending_email ON invitation(email_normalized) WHERE status='pending';
    """)


def downgrade():
    op.execute('DROP TABLE invitation')
