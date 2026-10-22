from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Lock

import pytest

from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore, JsonPhaseBStore
import doc2roadmap.infrastructure.artifacts.phase_b_store as store_module


@pytest.fixture(params=["memory", "json"])
def phase_b_store(request, tmp_path):
    return InMemoryPhaseBStore() if request.param == "memory" else JsonPhaseBStore(tmp_path / "phase-b.json")


def test_store_contract(phase_b_store):
    store = phase_b_store
    store.put_cache("k", {"ready": True})
    store.put_record("documents", "d1", {"owner": "learner-1", "markdown": "text"})
    store.put_record("documents", "d2", {"owner": "learner-2", "markdown": "other"})
    store.append_usage({"doc_id": "d1", "cost_usd": 0.2, "created_at": "2026-10-18T00:00:00+00:00"})
    assert store.get_cache("k") == {"ready": True}
    assert store.get_record("documents", "d1")["markdown"] == "text"
    assert [row["owner"] for row in store.list_records("documents", owner="learner-1")] == ["learner-1"]
    assert store.usage_rows(doc_id="d1") == [{"doc_id": "d1", "cost_usd": 0.2, "created_at": "2026-10-18T00:00:00+00:00"}]


def test_single_flight_runs_one_generation_for_concurrent_callers(phase_b_store):
    store = phase_b_store
    barrier = Barrier(12)
    lock = Lock()
    calls = 0

    def generate():
        nonlocal calls
        with lock:
            calls += 1
        return {"answer": 42}

    def run():
        barrier.wait()
        return store.single_flight("same", generate)

    with ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(lambda _: run(), range(12)))
    assert calls == 1
    assert results == [{"answer": 42}] * 12


def test_single_flight_negative_cache_expires_and_does_not_cache_failure(monkeypatch):
    now = [10.0]
    monkeypatch.setattr(store_module, "monotonic", lambda: now[0])
    store = InMemoryPhaseBStore(negative_ttl_seconds=60)
    calls = []

    def fail():
        calls.append("called")
        raise ValueError("temporary")

    with pytest.raises(ValueError):
        store.single_flight("k", fail)
    with pytest.raises(ValueError):
        store.single_flight("k", fail)
    assert calls == ["called"]
    assert store.get_cache("k") is None
    now[0] += 60.01
    assert store.single_flight("k", lambda: "recovered") == "recovered"
    assert store.get_cache("k") == "recovered"


def test_store_returns_nested_values_by_copy(phase_b_store):
    store = phase_b_store
    original = {"nested": {"rows": [1]}}
    store.put_cache("k", original)
    original["nested"]["rows"].append(2)
    value = store.get_cache("k")
    value["nested"]["rows"].append(3)
    assert store.get_cache("k") == {"nested": {"rows": [1]}}

    store.put_record("documents", "d", {"nested": {"rows": [1]}})
    record = store.get_record("documents", "d")
    record["nested"]["rows"].append(2)
    assert store.get_record("documents", "d") == {"nested": {"rows": [1]}}


def test_usage_filters_and_unknown_fields_round_trip(phase_b_store):
    from datetime import datetime, timezone

    rows = [
        {"doc_id": "a", "learner_id": "alice", "purpose": "assistant", "cost_usd": 0.0000009,
         "created_at": "2026-10-18T00:00:00Z", "custom": {"nested": [False, None, 1]}},
        {"doc_id": "b", "learner_id": "alice", "purpose": "document", "cost_usd": 0.02,
         "created_at": "2026-10-18T07:00:00+07:00", "failed": False, "ttft_ms": None},
        {"doc_id": "a", "learner_id": "bob", "purpose": "assistant", "cost_usd": 0.01,
         "created_at": "2026-10-18T01:00:00+00:00"},
        {"doc_id": "a", "purpose": "lecture", "cost_usd": 0.03,
         "created_at": "2026-10-18T01:00:00+00:00"},
        {"doc_id": "a", "learner_id": "alice", "purpose": "assistant", "cost_usd": 0.04,
         "created_at": "2026-10-17T23:59:59+00:00"},
    ]
    for row in rows:
        phase_b_store.append_usage(row)
    assert phase_b_store.usage_rows() == rows
    since = datetime(2026, 10, 18, tzinfo=timezone.utc)
    assert phase_b_store.usage_rows(learner_id="alice", since=since,
                                  purposes={"assistant", "document"}) == rows[:2]
    assert phase_b_store.usage_rows("a", learner_id="alice", since=since,
                                  purposes={"assistant", "document"}) == rows[:1]
    assert phase_b_store.usage_rows(purposes=set()) == []


def test_usage_since_requires_timezone(phase_b_store):
    from datetime import datetime

    with pytest.raises(ValueError, match="timezone"):
        phase_b_store.usage_rows(since=datetime(2026, 10, 18))


def test_anonymize_keeps_cost_and_other_fields(phase_b_store):
    rows = [
        {"learner_id": owner, "purpose": "assistant", "cost_usd": cost,
         "created_at": "2026-10-18T00:00:00Z", "unknown": {"a": [1, 2]}}
        for owner, cost in [("alice", 0.123456789), ("bob", 0.04), ("alice", 0.01)]
    ]
    for row in rows:
        phase_b_store.append_usage(row)
    phase_b_store.anonymize_learner_usage("alice")
    expected = [{**row, "learner_id": "deleted" if row["learner_id"] == "alice" else "bob"}
                for row in rows]
    assert phase_b_store.usage_rows() == expected
    assert phase_b_store.usage_rows(learner_id="alice") == []
    assert sum(r["cost_usd"] for r in phase_b_store.usage_rows()) == sum(r["cost_usd"] for r in rows)
    if isinstance(phase_b_store, JsonPhaseBStore):
        assert JsonPhaseBStore(phase_b_store.path).usage_rows() == expected


def test_budget_queries_filtered_usage_and_keeps_reservations():
    from datetime import datetime, timezone
    from doc2roadmap.application.phase_b.budget import DailySpendGuard

    class Observed(InMemoryPhaseBStore):
        def usage_rows(self, doc_id=None, **filters):
            self.last_filters = filters
            return super().usage_rows(doc_id, **filters)

    store = Observed()
    guard = DailySpendGuard(store)
    at = datetime(2026, 10, 18, 10, tzinfo=timezone.utc)
    store.put_record("spend_reservation", "in-flight", {
        "purpose": "assistant", "learner_id": "alice", "cost_usd": 0.15,
        "created_at": at.isoformat()})
    assert guard.check("document", 0.06, "alice", at=at) is False
    assert store.last_filters == {
        "learner_id": "alice", "since": datetime(2026, 10, 17, 17, tzinfo=timezone.utc),
        "purposes": {"assistant", "document"}}
