import pytest
from sqlalchemy import inspect, text

from wayfinder.infrastructure.database import DatabaseHealth, create_database_engine, upgrade_database


def test_unreachable_database_is_down():
    health = DatabaseHealth("postgresql+psycopg://unused:unused@127.0.0.1:1/unused")
    try:
        assert health() == "down"
    finally:
        health.close()


@pytest.mark.postgres
def test_postgres_fixture_hides_password_in_failure_representation(postgres_database_url):
    from sqlalchemy.engine import URL

    if not isinstance(postgres_database_url, URL):
        pytest.fail("PostgreSQL fixture must retain a URL object with a redacted representation", pytrace=False)
    if postgres_database_url.password and postgres_database_url.password in repr(postgres_database_url):
        pytest.fail("PostgreSQL fixture representation exposes credentials", pytrace=False)


@pytest.mark.postgres
def test_migration_from_empty_database_creates_only_alembic_version(empty_postgres_database_url):
    engine = create_database_engine(empty_postgres_database_url)
    try:
        upgrade_database(empty_postgres_database_url, "w01_0001")
        assert inspect(engine).get_table_names() == ["alembic_version"]
        with engine.connect() as connection:
            assert connection.scalar(text("select version_num from alembic_version")) == "w01_0001"
        health = DatabaseHealth(empty_postgres_database_url)
        try:
            assert health() == "ok"
        finally:
            health.close()
    finally:
        engine.dispose()


@pytest.mark.postgres
def test_w02_head_migrates_from_empty_and_follows_w05(postgres_database_url):
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    from pathlib import Path

    config = Config()
    config.set_main_option("script_location", str(Path(__file__).parents[1] / "wayfinder" / "migrations"))
    scripts = ScriptDirectory.from_config(config)
    assert scripts.get_heads() == ["w02_0003"]
    assert scripts.get_revision("w02_0003").down_revision == "w05_0002"
    engine = create_database_engine(postgres_database_url)
    try:
        assert set(inspect(engine).get_table_names()) == {
            "alembic_version", "phase_b_cache", "phase_b_negative", "phase_b_record", "usage_ledger",
            "account", "auth_session", "rate_limit_event", "audit_event"}
        with engine.connect() as connection:
            assert connection.scalar(text("select version_num from alembic_version")) == "w02_0003"
        upgrade_database(postgres_database_url)
        assert len(inspect(engine).get_table_names()) == 9
    finally:
        engine.dispose()


@pytest.mark.postgres
def test_w02_migration_schema_matches_runtime_metadata(postgres_database_url):
    from wayfinder.infrastructure.auth_schema import auth_metadata
    engine = create_database_engine(postgres_database_url)
    try:
        inspector = inspect(engine)
        for name, table in auth_metadata().tables.items():
            actual = {column["name"]: column for column in inspector.get_columns(name)}
            assert set(actual) == set(table.columns.keys())
            for expected in table.columns:
                assert actual[expected.name]["nullable"] == expected.nullable
            actual_checks = {check["name"] for check in inspector.get_check_constraints(name)}
            expected_checks = {constraint.name for constraint in table.constraints
                               if constraint.__class__.__name__ == "CheckConstraint"}
            assert actual_checks == expected_checks
            actual_indexes = {tuple(index["column_names"]) for index in inspector.get_indexes(name)
                              if not index.get("duplicates_constraint")}
            assert {tuple(column.name for column in index.columns) for index in table.indexes} <= actual_indexes
    finally:
        engine.dispose()
