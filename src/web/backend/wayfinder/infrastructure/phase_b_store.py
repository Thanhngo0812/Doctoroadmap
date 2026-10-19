"""PostgreSQL PhaseBStore with shared cache, failures and short atomic updates."""
from collections.abc import Collection
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from threading import RLock, local

from sqlalchemy import create_engine, delete, func, select, text, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import DBAPIError, TimeoutError as PoolTimeout

from doc2roadmap.application.ports.extraction import ModelTransportError
from doc2roadmap.infrastructure.artifacts.phase_b_store import _Flight
from wayfinder.infrastructure import phase_b_schema as tables


class PostgresPhaseBStore:
    def __init__(self, engine, *, lock_timeout_seconds=30.0, lock_pool_size=8,
                 negative_ttl_seconds=60.0, error_types=None):
        if lock_timeout_seconds <= 0 or lock_pool_size <= 0 or negative_ttl_seconds < 0:
            raise ValueError("invalid Phase B lock/TTL settings")
        self.engine = engine
        self.lock_timeout_seconds = lock_timeout_seconds
        self._negative_ttl = negative_ttl_seconds
        self._lock_engine = create_engine(engine.url, pool_size=lock_pool_size, max_overflow=0,
                                         pool_timeout=lock_timeout_seconds, pool_pre_ping=True)
        self._local = local()
        self._lock = RLock()
        self._flights = {}
        self._errors = {cls.__name__: cls for cls in (
            ValueError, RuntimeError, TimeoutError, PermissionError, ConnectionError, OSError, ModelTransportError)}
        self._errors.update(error_types or {})

    def close(self):
        self._lock_engine.dispose()
        self.engine.dispose()

    @contextmanager
    def _connection(self):
        current = getattr(self._local, "connection", None)
        if current is not None:
            yield current
        else:
            with self.engine.begin() as connection:
                yield connection

    @contextmanager
    def atomic(self):
        if getattr(self._local, "connection", None) is not None:
            yield
            return
        with self.engine.begin() as connection:
            # ponytail: one DB lock for short updates; the port has no per-owner lock scope.
            connection.execute(text("SELECT pg_advisory_xact_lock(hashtextextended('phase-b:atomic',0))"))
            self._local.connection = connection
            try:
                yield
            finally:
                del self._local.connection

    def get_cache(self, key):
        with self._connection() as connection:
            row = connection.execute(select(tables.cache.c.value).where(tables.cache.c.key == key)).first()
        return deepcopy(row[0]) if row is not None else None

    def put_cache(self, key, value):
        with self._connection() as connection:
            statement = insert(tables.cache).values(key=key, value=deepcopy(value))
            connection.execute(statement.on_conflict_do_update(index_elements=["key"],
                set_={"value": statement.excluded.value, "created_at": func.now()}))
            connection.execute(delete(tables.negative).where(tables.negative.c.key == key))

    def get_record(self, kind, record_id):
        with self._connection() as connection:
            value = connection.scalar(select(tables.record.c.value).where(
                tables.record.c.kind == kind, tables.record.c.record_id == record_id))
        return deepcopy(value)

    def put_record(self, kind, record_id, value):
        value = deepcopy(dict(value))
        statement = insert(tables.record).values(kind=kind, record_id=record_id,
            owner=value.get("owner"), doc_id=value.get("doc_id"), value=value)
        with self._connection() as connection:
            connection.execute(statement.on_conflict_do_update(index_elements=["kind", "record_id"],
                set_={"owner": statement.excluded.owner, "doc_id": statement.excluded.doc_id,
                      "value": statement.excluded.value, "updated_at": func.now()}))

    def list_records(self, kind, owner=None, doc_id=None):
        statement = select(tables.record.c.value).where(tables.record.c.kind == kind)
        if owner is not None:
            statement = statement.where(tables.record.c.owner == owner)
        if doc_id is not None:
            statement = statement.where(tables.record.c.doc_id == doc_id)
        with self._connection() as connection:
            return deepcopy(list(connection.scalars(statement.order_by(tables.record.c.record_id))))

    def delete_record(self, kind, record_id):
        with self._connection() as connection:
            connection.execute(delete(tables.record).where(tables.record.c.kind == kind,
                                                            tables.record.c.record_id == record_id))

    def append_usage(self, row):
        if row.get("purpose") in {"assistant", "document"} and not row.get("learner_id"):
            raise ValueError("assistant/document usage requires learner_id")
        value = deepcopy(dict(row))
        value.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        columns = {name: value.get(name) for name in tables.usage.c.keys()
                   if name not in {"id", "extra", "created_at", "cost_usd"}}
        stamp = value.get("created_at")
        columns["created_at"] = datetime.fromisoformat(stamp.replace("Z", "+00:00")) if stamp else None
        columns["cost_usd"] = value.get("cost_usd") or 0
        # Keep the original dict: numeric(12,6) and typed nullable columns cannot
        # preserve every float, timestamp spelling and absent-vs-null distinction.
        columns["extra"] = value
        with self._connection() as connection:
            connection.execute(insert(tables.usage).values(**columns))

    def _usage_query(self, doc_id=None, *, learner_id=None, since=None,
                     purposes: Collection[str] | None = None):
        if since is not None and since.utcoffset() is None:
            raise ValueError("usage since must include timezone")
        statement = select(tables.usage.c.extra)
        if doc_id is not None:
            statement = statement.where(tables.usage.c.doc_id == doc_id)
        if learner_id is not None:
            statement = statement.where(tables.usage.c.learner_id == learner_id)
        if since is not None:
            statement = statement.where(tables.usage.c.created_at >= since)
        if purposes is not None:
            if set(purposes) <= {"assistant", "document"}:
                # A literal predicate also permits the partial index in generic plans.
                statement = statement.where(text("purpose IN ('assistant','document')"))
            statement = statement.where(tables.usage.c.purpose.in_(purposes))
        return statement.order_by(tables.usage.c.id)

    def usage_rows(self, doc_id=None, *, learner_id=None, since=None, purposes=None):
        statement = self._usage_query(doc_id, learner_id=learner_id, since=since, purposes=purposes)
        with self._connection() as connection:
            return deepcopy(list(connection.scalars(statement)))

    def anonymize_learner_usage(self, learner_id):
        with self._connection() as connection:
            connection.execute(update(tables.usage).where(tables.usage.c.learner_id == learner_id).values(
                learner_id="deleted", extra=text("jsonb_set(extra, '{learner_id}', '\"deleted\"'::jsonb)")))

    @contextmanager
    def _generation_lock(self, key):
        try:
            with self._lock_engine.connect() as connection:
                with connection.begin():
                    connection.execute(text("SELECT set_config('lock_timeout', :timeout, true)"),
                                       {"timeout": f"{max(1, int(self.lock_timeout_seconds * 1000))}ms"})
                    connection.execute(text("SELECT pg_advisory_lock(hashtextextended(:key,0))"),
                                       {"key": "phase-b:flight:" + key})
                try:
                    yield
                finally:
                    try:
                        connection.execute(text("SELECT pg_advisory_unlock(hashtextextended(:key,0))"),
                                           {"key": "phase-b:flight:" + key})
                        connection.commit()
                    except BaseException:
                        connection.invalidate()  # A pooled session must never retain a lock.
                        raise
        except (DBAPIError, PoolTimeout) as error:
            if isinstance(error, PoolTimeout) or getattr(error.orig, "sqlstate", None) == "55P03":
                raise TimeoutError("Phase B generation lock timed out") from error
            raise

    def _shared_flight(self, key, generate, cache_if, ttl):
        with self._generation_lock(key):
            with self._connection() as connection:
                cached = connection.execute(select(tables.cache.c.value).where(tables.cache.c.key == key)).first()
                if cached is not None:
                    if cache_if is None or cache_if(cached[0]):
                        return deepcopy(cached[0])
                    connection.execute(delete(tables.cache).where(tables.cache.c.key == key))
                failed = connection.execute(select(tables.negative).where(
                    tables.negative.c.key == key, tables.negative.c.expires_at > func.clock_timestamp())).mappings().first()
            if failed is not None:
                if failed["error_type"]:
                    error_type = self._errors.get(failed["error_type"])
                    if error_type is not None:
                        raise error_type(failed["error_message"])
                    raise RuntimeError(f"{failed['error_type']}: {failed['error_message']}")
                return deepcopy(failed["value"])
            try:
                value = generate()
            except Exception as error:
                if ttl:
                    self._save_negative(key, ttl, error_type=type(error).__name__, error_message=str(error))
                raise
            if cache_if is None or cache_if(value):
                self.put_cache(key, value)
            elif ttl:
                self._save_negative(key, ttl, value=value)
            return deepcopy(value)

    def _save_negative(self, key, ttl, *, value=None, error_type=None, error_message=None):
        statement = insert(tables.negative).values(key=key, expires_at=func.clock_timestamp() + timedelta(seconds=ttl),
            value=deepcopy(value), error_type=error_type, error_message=error_message)
        with self._connection() as connection:
            connection.execute(statement.on_conflict_do_update(index_elements=["key"], set_={
                name: getattr(statement.excluded, name) for name in ("expires_at", "value", "error_type", "error_message")}))

    def single_flight(self, key, generate, *, cache_if=None, negative_ttl_seconds=None):
        ttl = self._negative_ttl if negative_ttl_seconds is None else float(negative_ttl_seconds)
        if ttl < 0:
            raise ValueError("negative_ttl_seconds must be non-negative")
        with self._lock:
            flight = self._flights.get(key)
            leader = flight is None
            if leader:
                flight = _Flight()
                self._flights[key] = flight
        if not leader:
            flight.done.wait()
            if flight.error is not None:
                raise flight.error
            return deepcopy(flight.value)
        try:
            flight.value = self._shared_flight(key, generate, cache_if, ttl)
            return deepcopy(flight.value)
        except BaseException as error:
            flight.error = error
            raise
        finally:
            with self._lock:
                self._flights.pop(key, None)
                flight.done.set()
