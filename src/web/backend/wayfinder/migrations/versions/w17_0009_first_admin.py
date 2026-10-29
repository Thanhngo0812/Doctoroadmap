"""Persist bootstrap identity without guessing an existing installation's first admin."""
from alembic import op

revision = 'w17_0009'
down_revision = 'w12_0008'
branch_labels = depends_on = None


def upgrade():
    op.execute("""
    CREATE TABLE bootstrap_admin (
      singleton boolean PRIMARY KEY CHECK(singleton),
      account_id uuid NOT NULL UNIQUE REFERENCES account ON DELETE RESTRICT,
      established_at timestamptz NOT NULL
    );
    CREATE FUNCTION guard_bootstrap_admin_registry() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
      IF TG_OP <> 'INSERT' THEN
        RAISE EXCEPTION 'protected_admin' USING ERRCODE='23514';
      END IF;
      PERFORM id FROM account WHERE id=NEW.account_id AND role='admin' AND status='active' FOR UPDATE;
      IF NOT FOUND THEN
        RAISE EXCEPTION 'bootstrap_admin_requires_active_admin' USING ERRCODE='23514';
      END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER bootstrap_admin_immutable BEFORE INSERT OR UPDATE OR DELETE ON bootstrap_admin
      FOR EACH ROW EXECUTE FUNCTION guard_bootstrap_admin_registry();
    CREATE FUNCTION guard_bootstrap_admin_account() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE protected_id uuid;
    BEGIN
      IF TG_OP='UPDATE' AND NEW.id=OLD.id AND NEW.role=OLD.role AND NEW.status=OLD.status THEN
        RETURN NEW;
      END IF;
      SELECT account_id INTO protected_id FROM bootstrap_admin WHERE singleton;
      IF OLD.id=protected_id THEN
        IF TG_OP='DELETE' THEN
          RAISE EXCEPTION 'protected_admin' USING ERRCODE='23514';
        END IF;
        IF NEW.id<>OLD.id OR NEW.role<>'admin' OR NEW.status<>'active' THEN
          RAISE EXCEPTION 'protected_admin' USING ERRCODE='23514';
        END IF;
      ELSIF protected_id IS NULL THEN
        IF TG_OP='DELETE' THEN
          RAISE EXCEPTION 'bootstrap_required' USING ERRCODE='23514';
        END IF;
        IF OLD.role='admin' AND (NEW.role<>'admin' OR NEW.status='disabled') THEN
          RAISE EXCEPTION 'bootstrap_required' USING ERRCODE='23514';
        END IF;
      END IF;
      IF TG_OP='DELETE' THEN RETURN OLD; END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER account_bootstrap_admin_protected BEFORE UPDATE OR DELETE ON account
      FOR EACH ROW EXECUTE FUNCTION guard_bootstrap_admin_account();
    """)


def downgrade():
    op.execute("""DROP TRIGGER account_bootstrap_admin_protected ON account;
      DROP FUNCTION guard_bootstrap_admin_account();
      DROP TABLE bootstrap_admin; DROP FUNCTION guard_bootstrap_admin_registry();""")
