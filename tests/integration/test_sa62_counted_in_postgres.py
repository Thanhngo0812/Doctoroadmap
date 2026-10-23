"""SA-62: the web's PostgreSQL Phase B store keeps `counted_in` through a whole fake build.

Needs `WAYFINDER_TEST_DATABASE_URL` (set by scripts/w05_run_tests.py); skipped otherwise.
"""
import os
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url

from tests.unit.application.test_sa62_pipeline_phase_b_store import (
    make_pipeline, patch_a12_inputs, run_titles,
)

pytestmark = pytest.mark.postgres


@pytest.fixture
def postgres_store():
    configured = os.environ.get("WAYFINDER_TEST_DATABASE_URL")
    if not configured:
        pytest.skip("PostgreSQL: missing WAYFINDER_TEST_DATABASE_URL")
    from wayfinder.infrastructure.database import create_database_engine, upgrade_database
    from wayfinder.infrastructure.phase_b_store import PostgresPhaseBStore

    admin = create_database_engine(configured).execution_options(isolation_level="AUTOCOMMIT")
    name = "wayfinder_sa62_" + uuid4().hex
    url = make_url(configured).set(database=name)
    created = False
    engine = store = None
    try:
        with admin.connect() as connection:
            connection.execute(text(f'CREATE DATABASE "{name}"'))
            created = True
        upgrade_database(url)
        engine = create_database_engine(url)
        store = PostgresPhaseBStore(engine)
        yield store
    finally:
        if store is not None:
            store.close()
        if created:
            with admin.connect() as connection:
                connection.execute(text(f'DROP DATABASE "{name}" WITH (FORCE)'))
        admin.dispose()


def test_build_rows_keep_counted_in_after_a_postgres_round_trip(tmp_path, monkeypatch, postgres_store):
    patch_a12_inputs(monkeypatch)
    pipeline, model, embedding = make_pipeline(tmp_path, monkeypatch, phase_b_store=postgres_store)

    run_titles(pipeline, monkeypatch)
    pipeline.learning_prep(tmp_path / "book.docx", "book", 8)

    rows = postgres_store.usage_rows()
    assert sorted(row["purpose"] for row in rows) == ["embedding"] + ["module_title"] * 3
    assert all(row.get("counted_in") == "build" for row in rows)
    assert sum(row.get("cost_usd", 0) for row in rows if row.get("counted_in") != "build") == 0
    assert len(postgres_store.list_records("module_assignment")) == 1
    assert not (tmp_path / "artifacts" / "phase_b").exists()
