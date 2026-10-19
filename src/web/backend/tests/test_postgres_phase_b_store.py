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
def phase_b_store(postgres_phase_b_store):
    return postgres_phase_b_store


def test_composition_uses_postgres_and_configures_separate_lock_pool(postgres_database_url):
    from doc2roadmap.config import Settings
    from doc2roadmap.domain.phase_b_limits import BSettings
    from wayfinder.composition import compose_services
    from wayfinder.settings import WebSettings
    from wayfinder.infrastructure.phase_b_store import PostgresPhaseBStore

    services = compose_services(
        WebSettings(_env_file=None, database_url=postgres_database_url.render_as_string(hide_password=False),
                    phase_b_lock_pool_size=2),
        core_settings=Settings(_env_file=None, llm_transport="vertex", vertex_project="offline-project"),
        auth_validator=lambda *_: None, model_factory=lambda *_a, **_k: object(),
        embedding_factory=lambda *_a, **_k: object())
    try:
        assert isinstance(services.phase_b_store, PostgresPhaseBStore)
        assert services.phase_b_store._lock_engine.pool.size() == 2
        assert services.phase_b_store.lock_timeout_seconds == BSettings().lecture_click_timeout_seconds
        services.phase_b_store.put_record("session", "wired", {"owner": "alice", "doc_id": "book"})
        assert services.phase_b_store.get_record("session", "wired") == {"owner": "alice", "doc_id": "book"}
        assert services.health_check() == "ok"
    finally:
        services.close()


def test_usage_query_uses_personal_day_index_without_forcing_planner(postgres_phase_b_store):
    from datetime import datetime, timezone
    import json
    from pathlib import Path

    store = postgres_phase_b_store
    with store.engine.begin() as connection:
        connection.execute(text("""
            INSERT INTO usage_ledger (created_at,purpose,learner_id,cost_usd,extra)
            SELECT timestamptz '2026-10-18 10:00:00+00',
                   CASE WHEN g%2=0 THEN 'assistant' ELSE 'lecture' END,
                   'learner-'||(g%1000)::text,0.01,'{}'::jsonb
            FROM generate_series(1,20000) AS g
        """))
    store.append_usage({"purpose": "assistant", "learner_id": "needle", "cost_usd": .01,
                        "created_at": "2026-10-18T10:00:00Z"})
    statement = store._usage_query(learner_id="needle", since=datetime(2026, 10, 18, tzinfo=timezone.utc),
                                   purposes={"assistant", "document"})
    sql = str(statement.compile(store.engine, compile_kwargs={"literal_binds": True}))
    with store.engine.begin() as connection:
        connection.execute(text("ANALYZE usage_ledger"))
        plan = connection.scalar(text("EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + sql))

    def nodes(node):
        yield node
        for child in node.get("Plans", []):
            yield from nodes(child)

    steps = list(nodes(plan[0]["Plan"]))
    assert any(row.get("Index Name") == "ix_usage_learner_day" for row in steps), plan
    assert not any(row.get("Node Type") == "Seq Scan" and row.get("Relation Name") == "usage_ledger"
                   for row in steps), plan
    evidence = Path("tmp/w05-explain.json")
    evidence.parent.mkdir(exist_ok=True)
    evidence.write_text(json.dumps({"query": sql, "plan": plan}, indent=2), encoding="utf-8")


def test_record_projection_updates_without_changing_payload(postgres_phase_b_store):
    store = postgres_phase_b_store
    first = {"owner": "alice", "doc_id": "book", "extra": [None, False, 1]}
    store.put_record("custom-kind", "r", first)
    assert store.list_records("custom-kind", "alice", "book") == [first]
    second = {"unscoped": True}
    store.put_record("custom-kind", "r", second)
    assert store.get_record("custom-kind", "r") == second
    assert store.list_records("custom-kind", "alice") == []
    with store.engine.connect() as connection:
        assert connection.execute(text("SELECT owner,doc_id FROM phase_b_record WHERE kind='custom-kind'")).one() == (None, None)
    store.delete_record("custom-kind", "r")
    assert store.get_record("custom-kind", "r") is None


def test_negative_values_are_shared_and_cache_write_clears_them(postgres_phase_b_store):
    from wayfinder.infrastructure.phase_b_store import PostgresPhaseBStore

    store = postgres_phase_b_store
    other = PostgresPhaseBStore(create_database_engine(store.engine.url))
    calls = []

    def generate():
        calls.append(True)
        return {"ready": False}

    try:
        for backend in (store, other):
            assert backend.single_flight("not-ready", generate, cache_if=lambda v: v["ready"]) == {"ready": False}
        assert len(calls) == 1
        other.put_cache("not-ready", {"ready": True})
        assert store.single_flight("not-ready", generate) == {"ready": True}
        assert len(calls) == 1
        with store.engine.connect() as connection:
            assert connection.scalar(text("SELECT count(*) FROM phase_b_negative")) == 0
        store.put_cache("null", None)
        assert other.single_flight("null", lambda: pytest.fail("cached JSON null must not regenerate")) is None
    finally:
        other.close()


def test_negative_errors_only_rehydrate_registered_types(postgres_phase_b_store):
    from wayfinder.infrastructure.phase_b_store import PostgresPhaseBStore

    class CustomFailure(ValueError):
        pass

    def generate():
        raise CustomFailure("shared failure")

    store = postgres_phase_b_store
    with pytest.raises(CustomFailure, match="shared failure"):
        store.single_flight("custom-error", generate)
    with pytest.raises(RuntimeError, match="CustomFailure: shared failure"):
        store.single_flight("custom-error", lambda: pytest.fail("negative error must be reused"))
    registered = PostgresPhaseBStore(create_database_engine(store.engine.url),
                                     error_types={"CustomFailure": CustomFailure})
    try:
        with pytest.raises(CustomFailure, match="shared failure"):
            registered.single_flight("custom-error", lambda: pytest.fail("must not regenerate"))
    finally:
        registered.close()
