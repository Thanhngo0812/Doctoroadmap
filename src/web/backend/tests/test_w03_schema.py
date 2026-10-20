from wayfinder.migrations.versions import w03_0004_email_tokens
from wayfinder.infrastructure.auth_schema import auth_metadata
from wayfinder.infrastructure.database import create_database_engine, upgrade_database


def test_metadata_describes_private_single_use_tokens():
    assert w03_0004_email_tokens.revision == "w03_0004"
    assert w03_0004_email_tokens.down_revision == "w02_0003"
    assert "email_token" in auth_metadata().tables

    table = auth_metadata().tables["email_token"]
    assert set(table.columns.keys()) == {
        "id", "account_id", "purpose", "token_hash", "email_normalized",
        "expires_at", "used_at", "created_at",
    }
    assert table.c.token_hash.unique
    assert table.c.token_hash.type.length == 32
    assert table.c.account_id.foreign_keys.pop().ondelete == "CASCADE"
    assert {index.name: tuple(column.name for column in index.columns) for index in table.indexes} == {
        "ix_email_token_account_purpose_created": ("account_id", "purpose", "created_at"),
        "ix_email_token_expires_at": ("expires_at",),
    }


def test_postgres_upgrade_from_w02_adds_email_token_schema(empty_postgres_database_url):
    upgrade_database(empty_postgres_database_url, "w02_0003")
    engine = create_database_engine(empty_postgres_database_url)
    try:
        from sqlalchemy import inspect

        assert "email_token" not in inspect(engine).get_table_names()
        upgrade_database(empty_postgres_database_url, "w03_0004")
        inspector = inspect(engine)
        assert "email_token" in inspector.get_table_names()
        assert {index["name"] for index in inspector.get_indexes("email_token")} >= {
            "ix_email_token_account_purpose_created", "ix_email_token_expires_at",
        }
        assert {tuple(constraint["column_names"]) for constraint in inspector.get_unique_constraints("email_token")} == {
            ("token_hash",),
        }
        assert inspector.get_foreign_keys("email_token")[0]["options"]["ondelete"] == "CASCADE"
    finally:
        engine.dispose()
