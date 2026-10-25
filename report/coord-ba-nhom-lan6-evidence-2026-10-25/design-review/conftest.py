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


@pytest.fixture
def postgres_phase_b_store(postgres_database_url):
    from wayfinder.infrastructure.phase_b_store import PostgresPhaseBStore

    engine = create_database_engine(postgres_database_url)
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE phase_b_cache, phase_b_negative, phase_b_record, usage_ledger RESTART IDENTITY"))
    store = PostgresPhaseBStore(engine)
    try:
        yield store
    finally:
        store.close()


@pytest.fixture(autouse=True)
def forbid_model_network_in_w05(request, monkeypatch):
    if not request.node.path.name.startswith("test_postgres_phase_b"):
        return
    from pathlib import Path
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[4] / "tests/unit/application"))

    def forbidden(*args, **kwargs):
        raise AssertionError("W-05 acceptance must not call model providers or refresh ADC")

    monkeypatch.setattr("doc2roadmap.infrastructure.llm.gemini.urlopen", forbidden)
    monkeypatch.setattr("doc2roadmap.infrastructure.embedding.gemini.urlopen", forbidden)
    monkeypatch.setattr("doc2roadmap.infrastructure.google_auth.VertexCredentials.headers", forbidden)
