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
def test_migration_from_empty_database_creates_only_alembic_version(postgres_database_url):
    engine = create_database_engine(postgres_database_url)
    try:
        upgrade_database(postgres_database_url)
        assert inspect(engine).get_table_names() == ["alembic_version"]
        with engine.connect() as connection:
            assert connection.scalar(text("select version_num from alembic_version")) == "w01_0001"
        health = DatabaseHealth(postgres_database_url)
        try:
            assert health() == "ok"
        finally:
            health.close()
    finally:
        engine.dispose()
