"""The core contract runs unchanged against PostgreSQL too."""
import pytest
from sqlalchemy import inspect, text

from wayfinder.infrastructure.database import create_database_engine
from tests.unit.application.test_phase_b_store import (
    test_anonymize_keeps_cost_and_other_fields,
    test_single_flight_runs_one_generation_for_concurrent_callers,
    test_store_contract,
    test_store_returns_nested_values_by_copy,
    test_usage_filters_and_unknown_fields_round_trip,
    test_usage_since_requires_timezone,
)


pytestmark = pytest.mark.postgres


def test_phase_b_migration_has_tables_and_indexes(postgres_database_url):
    engine = create_database_engine(postgres_database_url)
    try:
        schema = inspect(engine)
        assert {"phase_b_cache", "phase_b_negative", "phase_b_record", "usage_ledger"} <= set(schema.get_table_names())
        assert {"ix_usage_learner_day", "ix_usage_purpose_day", "ix_usage_doc_day"} <= {
            index["name"] for index in schema.get_indexes("usage_ledger")}
        from alembic.config import Config
        from alembic.script import ScriptDirectory
        from pathlib import Path
        config = Config()
        config.set_main_option("script_location", str(Path(__file__).resolve().parents[1] / "wayfinder/migrations"))
        heads = ScriptDirectory.from_config(config).get_heads()
        assert len(heads) == 1
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT version_num FROM alembic_version")) == heads[0]
    finally:
        engine.dispose()


@pytest.fixture
def phase_b_store(postgres_database_url):
    from wayfinder.infrastructure.phase_b_store import PostgresPhaseBStore

    engine = create_database_engine(postgres_database_url)
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE phase_b_cache, phase_b_negative, phase_b_record, usage_ledger RESTART IDENTITY"))
    store = PostgresPhaseBStore(engine)
    try:
        yield store
    finally:
        store.close()
