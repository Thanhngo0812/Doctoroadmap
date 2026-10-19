"""Each PostgreSQL test session gets its own disposable, migrated database."""
import os
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError

from wayfinder.infrastructure.database import create_database_engine, upgrade_database


def pytest_addoption(parser):
    parser.addoption("--require-postgres", action="store_true", help="Fail when db-test is not configured or unavailable")


def pytest_sessionstart(session):
    if session.config.getoption("require_postgres", default=False) and not os.environ.get("WAYFINDER_TEST_DATABASE_URL"):
        raise pytest.UsageError("PostgreSQL: missing WAYFINDER_TEST_DATABASE_URL; web check requires db-test")


@pytest.fixture(scope="session")
def postgres_database_url(request):
    configured = os.environ.get("WAYFINDER_TEST_DATABASE_URL")
    if not configured:
        pytest.skip("PostgreSQL: missing WAYFINDER_TEST_DATABASE_URL; run db-test then web check for mandatory verification")
    engine = create_database_engine(configured).execution_options(isolation_level="AUTOCOMMIT")
    database_name = "wayfinder_test_" + uuid4().hex
    created = False
    url = make_url(configured).set(database=database_name)
    try:
        try:
            with engine.connect() as connection:
                connection.execute(text(f'CREATE DATABASE "{database_name}"'))
                created = True
        except SQLAlchemyError:
            pytest.fail("PostgreSQL: db-test is configured but unavailable, or cannot create a test database", pytrace=False)
        upgrade_database(url)
        yield url
    finally:
        if created:
            with engine.connect() as connection:
                connection.execute(text(f'DROP DATABASE "{database_name}" WITH (FORCE)'))
        engine.dispose()


@pytest.fixture
def empty_postgres_database_url(postgres_database_url):
    """Keep the W-01 empty-schema assertion at its original revision."""
    name = "wayfinder_base_test_" + uuid4().hex
    engine = create_database_engine(postgres_database_url).execution_options(isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as connection:
            connection.execute(text(f'CREATE DATABASE "{name}"'))
        yield make_url(postgres_database_url).set(database=name)
    finally:
        with engine.connect() as connection:
            connection.execute(text(f'DROP DATABASE "{name}" WITH (FORCE)'))
        engine.dispose()
