"""W-14 upload, durable queue and attempt usage after accepted W-06."""
from alembic import op

revision = 'w14_0006'
down_revision = 'w06_0005'
branch_labels = depends_on = None


def upgrade():
    op.execute("""
    CREATE TABLE upload (
      id uuid PRIMARY KEY, account_id uuid REFERENCES account ON DELETE SET NULL,
      course_id uuid NOT NULL UNIQUE REFERENCES course DEFERRABLE INITIALLY DEFERRED,
      sha256 bytea NOT NULL CHECK (octet_length(sha256)=32),
      original_name text NOT NULL CHECK(length(original_name) BETWEEN 1 AND 255),
      kind text NOT NULL CHECK(kind IN ('pdf','docx')), size_bytes bigint NOT NULL CHECK(size_bytes>0),
      page_count integer, public_id text NOT NULL UNIQUE,
      resource_type text NOT NULL CHECK(resource_type IN ('image','raw')),
      rights_confirmed_at timestamptz NOT NULL, created_at timestamptz NOT NULL,
      confirmed_at timestamptz
    );
    CREATE INDEX ix_upload_sha ON upload(sha256);
    CREATE INDEX ix_upload_account ON upload(account_id);
    CREATE TABLE build (
      id uuid PRIMARY KEY, doc_id text NOT NULL, upload_id uuid NOT NULL REFERENCES upload,
      requested_by uuid REFERENCES account ON DELETE SET NULL,
      status text NOT NULL CHECK(status IN ('awaiting_confirmation','queued','reading','running','rejected','succeeded','failed','cancelled')),
      step text CHECK(step IN ('doc_reading','concepts','graph','learning_prep')),
      pipeline_version text NOT NULL, counts_quota boolean NOT NULL DEFAULT false,
      cancel_requested boolean NOT NULL DEFAULT false,
      claim_count integer NOT NULL DEFAULT 0 CHECK(claim_count BETWEEN 0 AND 2),
      claimed_by text, lease_id uuid, heartbeat_at timestamptz,
      confirmation_expires_at timestamptz NOT NULL, queued_at timestamptz,
      started_at timestamptz, finished_at timestamptz, created_at timestamptz NOT NULL,
      error_code text, error_message text, retryable boolean NOT NULL DEFAULT false,
      spent_usd numeric(12,6) NOT NULL DEFAULT 0 CHECK(spent_usd>=0),
      model_calls integer NOT NULL DEFAULT 0, input_tokens bigint NOT NULL DEFAULT 0,
      output_tokens bigint NOT NULL DEFAULT 0, usage_complete boolean NOT NULL DEFAULT true,
      elapsed_seconds double precision NOT NULL DEFAULT 0,
      graph_version integer, module_count integer NOT NULL DEFAULT 0
    );
    CREATE UNIQUE INDEX uq_build_active ON build(doc_id,pipeline_version)
      WHERE status IN ('awaiting_confirmation','queued','reading','running');
    CREATE INDEX ix_build_queue ON build(queued_at) WHERE status='queued';
    CREATE INDEX ix_build_reuse ON build(doc_id,pipeline_version) WHERE status='succeeded';
    CREATE INDEX ix_build_quota ON build(requested_by,queued_at) WHERE counts_quota;
    ALTER TABLE course ADD CONSTRAINT fk_course_build FOREIGN KEY(build_id) REFERENCES build;
    CREATE TABLE media_asset (
      doc_id text NOT NULL, asset_key text NOT NULL, public_id text NOT NULL UNIQUE,
      kind text NOT NULL CHECK(kind IN ('formula','media')), width integer, height integer,
      bytes bigint NOT NULL, created_at timestamptz NOT NULL, PRIMARY KEY(doc_id,asset_key)
    );
    CREATE TABLE build_attempt (
      build_id uuid NOT NULL REFERENCES build ON DELETE CASCADE, lease_id uuid NOT NULL, claim_count integer NOT NULL,
      spent_usd numeric(12,6) NOT NULL DEFAULT 0, model_calls integer NOT NULL DEFAULT 0,
      input_tokens bigint NOT NULL DEFAULT 0, output_tokens bigint NOT NULL DEFAULT 0,
      usage_complete boolean NOT NULL DEFAULT true, result jsonb,
      PRIMARY KEY(build_id,lease_id)
    );
    """)


def downgrade():
    op.execute("""DROP TABLE build_attempt; DROP TABLE media_asset;
      ALTER TABLE course DROP CONSTRAINT fk_course_build;
      DROP TABLE build; DROP TABLE upload;""")
