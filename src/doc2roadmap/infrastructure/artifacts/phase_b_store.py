from __future__ import annotations

import json
import os
from collections.abc import Collection
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from threading import Event, RLock
from time import monotonic, sleep
from typing import Any, Callable, Mapping, TypeVar

T = TypeVar("T")


class _Flight:
    def __init__(self) -> None:
        self.done = Event()
        self.value: Any = None
        self.error: BaseException | None = None


class _PhaseBStore:
    def __init__(self, *, negative_ttl_seconds: float = 60.0) -> None:
        if negative_ttl_seconds < 0:
            raise ValueError("negative_ttl_seconds must be non-negative")
        self._lock = RLock()
        self._negative_ttl = negative_ttl_seconds
        self._negative: dict[str, tuple[float, Any, BaseException | None]] = {}
        self._flights: dict[str, _Flight] = {}
        self._cache: dict[str, Any] = {}
        self._records: dict[str, dict[str, dict[str, Any]]] = {}
        self._usage: list[dict[str, Any]] = []

    @contextmanager
    def atomic(self):
        """Serialize a short read/modify/write operation across use case instances."""
        with self._lock:
            yield

    def get_cache(self, key: str) -> Any | None:
        with self._lock:
            return deepcopy(self._cache.get(key))

    def put_cache(self, key: str, value: Any) -> None:
        with self._lock:
            self._cache[key] = deepcopy(value)
            self._negative.pop(key, None)
            self._persist()

    def get_record(self, kind: str, record_id: str) -> dict[str, Any] | None:
        with self._lock:
            value = self._records.get(kind, {}).get(record_id)
            return deepcopy(value) if value is not None else None

    def put_record(self, kind: str, record_id: str, value: Mapping[str, Any]) -> None:
        with self._lock:
            self._records.setdefault(kind, {})[record_id] = deepcopy(dict(value))
            self._persist()

    def list_records(self, kind: str, owner: str | None = None, doc_id: str | None = None) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._records.get(kind, {}).values()
            return [deepcopy(row) for row in rows
                    if (owner is None or row.get("owner") == owner)
                    and (doc_id is None or row.get("doc_id") == doc_id)]

    def delete_record(self, kind: str, record_id: str) -> None:
        with self._lock:
            self._records.get(kind, {}).pop(record_id, None)
            self._persist()

    def append_usage(self, row: Mapping[str, Any]) -> None:
        if row.get("purpose") in {"assistant", "document"} and not row.get("learner_id"):
            raise ValueError("assistant/document usage requires learner_id")
        with self._lock:
            value = deepcopy(dict(row))
            value.setdefault("created_at", datetime.now(timezone.utc).isoformat())
            self._usage.append(value)
            self._persist()

    def usage_rows(self, doc_id: str | None = None, *, learner_id: str | None = None,
                   since: datetime | None = None,
                   purposes: Collection[str] | None = None) -> list[dict[str, Any]]:
        if since is not None and since.utcoffset() is None:
            raise ValueError("usage since must include timezone")
        with self._lock:
            result = []
            for row in self._usage:
                if ((doc_id is not None and row.get("doc_id") != doc_id)
                    or (learner_id is not None and row.get("learner_id") != learner_id)
                    or (purposes is not None and row.get("purpose") not in purposes)):
                    continue
                if since is not None:
                    if not row.get("created_at"):
                        continue
                    stamp = datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
                    if stamp.utcoffset() is None:
                        raise ValueError("usage created_at must include timezone")
                    if stamp < since:
                        continue
                result.append(deepcopy(row))
            return result

    def anonymize_learner_usage(self, learner_id: str) -> None:
        with self._lock:
            for row in self._usage:
                if row.get("learner_id") == learner_id:
                    row["learner_id"] = "deleted"
            self._persist()

    def single_flight(
        self, key: str, generate: Callable[[], T], *,
        cache_if: Callable[[T], bool] | None = None,
        negative_ttl_seconds: float | None = None,
    ) -> T:
        ttl = self._negative_ttl if negative_ttl_seconds is None else float(negative_ttl_seconds)
        if ttl < 0:
            raise ValueError("negative_ttl_seconds must be non-negative")
        with self._lock:
            if key in self._cache:
                cached = self._cache[key]
                if cache_if is None or cache_if(cached):
                    return deepcopy(cached)
                self._cache.pop(key, None)
                self._persist()
            failed = self._negative.get(key)
            if failed is not None:
                if failed[0] > monotonic():
                    if failed[2] is not None:
                        raise failed[2]
                    return deepcopy(failed[1])
                self._negative.pop(key, None)
            flight = self._flights.get(key)
            leader = flight is None
            if leader:
                flight = _Flight()
                self._flights[key] = flight

        assert flight is not None
        if not leader:
            flight.done.wait()
            if flight.error is not None:
                raise flight.error
            return deepcopy(flight.value)

        try:
            value = generate()
            cache_value = cache_if is None or cache_if(value)
            with self._lock:
                if cache_value:
                    self._cache[key] = deepcopy(value)
                    self._negative.pop(key, None)
                    self._persist()
                elif ttl:
                    self._negative[key] = (monotonic() + ttl, deepcopy(value), None)
                flight.value = deepcopy(value)
            return deepcopy(value)
        except BaseException as error:
            with self._lock:
                if ttl:
                    self._negative[key] = (monotonic() + ttl, None, error)
                flight.error = error
            raise
        finally:
            with self._lock:
                self._flights.pop(key, None)
                flight.done.set()

    def _persist(self) -> None:
        """Overridden by the JSON implementation; called with the lock held."""


class InMemoryPhaseBStore(_PhaseBStore):
    pass


class JsonPhaseBStore(_PhaseBStore):
    def __init__(self, path: Path | str, *, negative_ttl_seconds: float = 60.0) -> None:
        super().__init__(negative_ttl_seconds=negative_ttl_seconds)
        self.path = Path(path)
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"cannot read Phase B store: {self.path}") from error
        if value.get("version") != 1:
            raise ValueError("unsupported Phase B store version")
        self._cache = value.get("cache", {})
        self._records = value.get("records", {})
        self._usage = value.get("usage", [])

    def _persist(self) -> None:
        value = {
            "version": 1,
            "cache": self._cache,
            "records": self._records,
            "usage": self._usage,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        for attempt in range(5):
            try:
                os.replace(temporary, self.path)
                break
            except PermissionError:
                if attempt == 4:
                    raise
                sleep(0.1 * (attempt + 1))
