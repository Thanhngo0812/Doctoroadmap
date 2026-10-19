"""Spawn separate workers so process-local locks cannot satisfy these assertions."""
import multiprocessing
import os
from datetime import datetime, timezone
from time import monotonic, sleep
from types import SimpleNamespace

import pytest
from sqlalchemy import event, text

from doc2roadmap.application.phase_b.budget import DailyLimitExceeded, DailySpendGuard
from wayfinder.infrastructure.database import create_database_engine
from wayfinder.infrastructure.phase_b_store import PostgresPhaseBStore


pytestmark = pytest.mark.postgres


def _remove_lock(engine, marker):
    def replace(connection, cursor, statement, parameters, context, executemany):
        return ("SELECT 1", parameters) if marker in statement else (statement, parameters)
    event.listen(engine, "before_cursor_execute", replace, retval=True)


def _flight_worker(url, barrier, release, count, queue, mutation=False, failure=False, key="shared", timeout=3):
    store = PostgresPhaseBStore(create_database_engine(url), lock_timeout_seconds=timeout)
    if mutation:
        _remove_lock(store._lock_engine, "pg_advisory_lock(")

    def generate():
        with count.get_lock():
            count.value += 1
        if failure:
            raise ValueError("temporary failure")
        if release is not None:
            assert release.wait(10), "parent did not release generation"
        return {"answer": 42}

    try:
        if barrier is not None:
            barrier.wait(10)
        queue.put({"value": store.single_flight(key, generate)})
    except BaseException as error:
        queue.put({"error": type(error).__name__, "message": str(error)})
    finally:
        store.close()


def _join(processes):
    for process in processes:
        process.join(12)
    for process in processes:
        if process.is_alive():
            process.terminate()
            process.join()
            pytest.fail("PostgreSQL worker did not terminate")
        assert process.exitcode == 0


def test_two_processes_generate_once(postgres_phase_b_store):
    context = multiprocessing.get_context("spawn")
    barrier, release, count, queue = context.Barrier(3), context.Event(), context.Value("i", 0), context.Queue()
    mutation = os.environ.get("W05_DISABLE_FLIGHT_LOCK") == "1"
    processes = [context.Process(target=_flight_worker, args=(
        postgres_phase_b_store.engine.url, barrier, release, count, queue, mutation)) for _ in range(2)]
    for process in processes:
        process.start()
    try:
        barrier.wait(10)
        # Do not release A until B is blocked by the DB lock, or has generated
        # as well (the mutation). Scheduling cannot turn a missing lock green.
        deadline = monotonic() + 10
        observed = False
        while monotonic() < deadline:
            with postgres_phase_b_store.engine.connect() as connection:
                waiting = connection.scalar(text("SELECT count(*) FROM pg_locks WHERE locktype='advisory' "
                    "AND NOT granted AND database=(SELECT oid FROM pg_database WHERE datname=current_database())"))
            if waiting or count.value >= 2:
                observed = True
                break
            sleep(0.01)
        assert observed, "second process never reached the lock/generator"
    finally:
        release.set()
        _join(processes)
    results = [queue.get(timeout=2) for _ in processes]
    assert results == [{"value": {"answer": 42}}] * 2
    assert count.value == 1, "duplicate generation across processes"


def test_negative_cache_shared_across_processes_then_expires(postgres_phase_b_store):
    context = multiprocessing.get_context("spawn")
    count, queue = context.Value("i", 0), context.Queue()
    for _ in range(2):
        process = context.Process(target=_flight_worker, args=(
            postgres_phase_b_store.engine.url, None, None, count, queue, False, True, "negative"))
        process.start()
        _join([process])
        assert queue.get(timeout=2) == {"error": "ValueError", "message": "temporary failure"}
    assert count.value == 1
    with postgres_phase_b_store.engine.begin() as connection:
        connection.execute(text("UPDATE phase_b_negative SET expires_at=clock_timestamp()-interval '1 second'"))
    process = context.Process(target=_flight_worker, args=(
        postgres_phase_b_store.engine.url, None, None, count, queue, False, False, "negative"))
    process.start()
    _join([process])
    assert queue.get(timeout=2) == {"value": {"answer": 42}}
    assert count.value == 2


def _budget_worker(url, start, read_barrier, finish, queue, mutation):
    class Store(PostgresPhaseBStore):
        def list_records(self, kind, *args, **kwargs):
            result = super().list_records(kind, *args, **kwargs)
            if kind == "spend_reservation":
                if mutation:
                    read_barrier.wait(10)
                else:
                    sleep(0.1)
            return result

    store = Store(create_database_engine(url))
    if mutation:
        _remove_lock(store.engine, "pg_advisory_xact_lock(")
    clock = SimpleNamespace(now=lambda: datetime(2026, 10, 18, 10, tzinfo=timezone.utc))
    guard = DailySpendGuard(store, clock=clock)
    token = None
    try:
        start.wait(10)
        try:
            token = guard.reserve("assistant", 0.08, "alice")
        except DailyLimitExceeded:
            queue.put({"admitted": False})
        else:
            queue.put({"admitted": True})
            assert finish.wait(10)
    except BaseException as error:
        queue.put({"error": type(error).__name__, "message": str(error)})
    finally:
        if token:
            guard.release(token)
        store.close()


def test_two_processes_cannot_reserve_the_last_budget_twice(postgres_phase_b_store):
    store = postgres_phase_b_store
    store.append_usage({"learner_id": "alice", "purpose": "document", "doc_id": "another-book",
                        "cost_usd": 0.1, "created_at": "2026-10-18T10:00:00Z"})
    context = multiprocessing.get_context("spawn")
    start, reads, finish, queue = context.Barrier(3), context.Barrier(2), context.Event(), context.Queue()
    mutation = os.environ.get("W05_DISABLE_ATOMIC_LOCK") == "1"
    processes = [context.Process(target=_budget_worker, args=(
        store.engine.url, start, reads, finish, queue, mutation)) for _ in range(2)]
    for process in processes:
        process.start()
    try:
        start.wait(10)
        results = [queue.get(timeout=12) for _ in processes]
        reservations = store.list_records("spend_reservation")
    finally:
        finish.set()
        _join(processes)
    assert not any("error" in row for row in results), results
    assert sum(row["admitted"] for row in results) == 1, "overspent last budget across processes"
    assert 0.1 + sum(row["cost_usd"] for row in reservations) <= 0.2
    assert store.list_records("spend_reservation") == []


def test_atomic_nested_transaction_and_rollback(postgres_phase_b_store):
    store = postgres_phase_b_store
    with pytest.raises(ValueError, match="rollback"):
        with store.atomic():
            store.put_record("progress", "p", {"owner": "alice", "status": "seen"})
            with store.atomic():
                assert store.get_record("progress", "p")["status"] == "seen"
            raise ValueError("rollback")
    assert store.get_record("progress", "p") is None
    with store.atomic():
        store.put_record("progress", "p", {"status": "learned"})
    assert store.get_record("progress", "p") == {"status": "learned"}


def test_atomic_uses_fresh_snapshots_even_when_engine_default_is_repeatable_read(postgres_phase_b_store):
    engine = create_database_engine(postgres_phase_b_store.engine.url).execution_options(
        isolation_level="REPEATABLE READ")
    store = PostgresPhaseBStore(engine)
    try:
        store.put_record("probe", "snapshot", {"value": "before"})
        with store.atomic():
            assert store.get_record("probe", "snapshot") == {"value": "before"}
            with engine.begin() as writer:
                writer.execute(text("UPDATE phase_b_record SET value='{}'::jsonb "
                                    "WHERE kind='probe' AND record_id='snapshot'"))
            assert store.get_record("probe", "snapshot") == {}
        with engine.connect() as connection:
            assert connection.scalar(text("SHOW transaction_isolation")) == "repeatable read"
    finally:
        store.close()


def test_lock_timeout_does_not_generate_or_poison_cache(postgres_phase_b_store):
    store = postgres_phase_b_store
    context = multiprocessing.get_context("spawn")
    count, queue = context.Value("i", 0), context.Queue()
    with store.engine.connect() as connection:
        connection.execute(text("SELECT pg_advisory_lock(hashtextextended('phase-b:flight:held',0))"))
        connection.commit()
        try:
            process = context.Process(target=_flight_worker, args=(
                store.engine.url, None, None, count, queue, False, False, "held", .1))
            process.start()
            _join([process])
            result = queue.get(timeout=2)
        finally:
            connection.execute(text("SELECT pg_advisory_unlock(hashtextextended('phase-b:flight:held',0))"))
            connection.commit()
    assert result["error"] == "TimeoutError"
    assert count.value == 0
    assert store.get_cache("held") is None
    with store.engine.connect() as connection:
        assert connection.scalar(text("SELECT count(*) FROM phase_b_negative")) == 0


def test_generation_uses_separate_pool_and_releases_lock(postgres_phase_b_store):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from sqlalchemy import create_engine

    engine = create_engine(postgres_phase_b_store.engine.url, pool_size=1, max_overflow=0, pool_timeout=.2)
    store = PostgresPhaseBStore(engine, lock_pool_size=1)
    entered, release = Event(), Event()

    def generate():
        entered.set()
        assert release.wait(5)
        return 42

    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(store.single_flight, "slow", generate)
            try:
                assert entered.wait(2)
                with engine.connect() as connection:
                    assert connection.scalar(text("SELECT 1")) == 1
            finally:
                release.set()
            assert future.result(2) == 42
        with store._lock_engine.connect() as connection:
            assert connection.scalar(text("SELECT count(*) FROM pg_locks WHERE locktype='advisory' "
                "AND pid=pg_backend_pid()")) == 0
    finally:
        store.close()
