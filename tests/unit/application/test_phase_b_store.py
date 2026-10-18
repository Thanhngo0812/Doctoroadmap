from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Lock

import pytest

from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore, JsonPhaseBStore
import doc2roadmap.infrastructure.artifacts.phase_b_store as store_module


@pytest.mark.parametrize("store_kind", ["memory", "json"])
def test_store_contract(store_kind, tmp_path):
    store = InMemoryPhaseBStore() if store_kind == "memory" else JsonPhaseBStore(tmp_path / "phase-b.json")
    store.put_cache("k", {"ready": True})
    store.put_record("documents", "d1", {"owner": "learner-1", "markdown": "text"})
    store.put_record("documents", "d2", {"owner": "learner-2", "markdown": "other"})
    store.append_usage({"doc_id": "d1", "cost_usd": 0.2})
    assert store.get_cache("k") == {"ready": True}
    assert store.get_record("documents", "d1")["markdown"] == "text"
    assert [row["owner"] for row in store.list_records("documents", owner="learner-1")] == ["learner-1"]
    assert store.usage_rows(doc_id="d1") == [{"doc_id": "d1", "cost_usd": 0.2}]


def test_single_flight_runs_one_generation_for_concurrent_callers():
    store = InMemoryPhaseBStore()
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


def test_store_returns_nested_values_by_copy():
    store = InMemoryPhaseBStore()
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
