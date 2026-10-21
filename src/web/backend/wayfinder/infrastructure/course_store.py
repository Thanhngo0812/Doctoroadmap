from contextlib import contextmanager
from contextvars import ContextVar
from uuid import UUID

from sqlalchemy import text

from wayfinder.domain.courses import Course, Membership


def _course(row):
    return Course(**{key: str(value) if isinstance(value, UUID) else value for key, value in row.items()})


class PostgresCourseStore:
    def __init__(self, engine):
        self.engine = engine
        self._current = ContextVar(f"course_connection_{id(self)}", default=None)

    @contextmanager
    def atomic(self):
        with self.engine.begin() as connection:
            token = self._current.set(connection)
            try:
                yield
            finally:
                self._current.reset(token)

    @contextmanager
    def _connection(self):
        connection = self._current.get()
        if connection is not None:
            yield connection
        else:
            with self.engine.begin() as connection:
                yield connection

    def get_course(self, cid, *, for_update=False):
        try:
            cid = str(UUID(cid))
        except (ValueError, TypeError, AttributeError):
            return None
        with self._connection() as connection:
            row = connection.execute(text("SELECT * FROM course WHERE id=:cid" + (" FOR UPDATE" if for_update else "")),
                                     {"cid": cid}).mappings().first()
        return _course(row) if row else None

    def get_membership(self, cid, uid):
        with self._connection() as connection:
            row = connection.execute(text("SELECT * FROM membership WHERE course_id=:cid AND account_id=:uid"),
                                     {"cid": cid, "uid": uid}).mappings().first()
        return Membership(**{key: str(value) if isinstance(value, UUID) else value for key, value in row.items()}) if row else None

    def add_course(self, course):
        from dataclasses import asdict
        values = asdict(course)
        with self._connection() as connection:
            connection.execute(text("INSERT INTO course (" + ",".join(values) + ") VALUES (" +
                                    ",".join(":" + key for key in values) + ")"), values)

    def add_membership(self, member):
        from dataclasses import asdict
        values = asdict(member)
        with self._connection() as connection:
            connection.execute(text("INSERT INTO membership (" + ",".join(values) + ") VALUES (" +
                                    ",".join(":" + key for key in values) + ") ON CONFLICT DO NOTHING"), values)

    def list_courses(self, uid, *, samples=False):
        with self._connection() as connection:
            rows = connection.execute(text("SELECT c.* FROM course c LEFT JOIN membership m "
                "ON m.course_id=c.id AND m.account_id=:uid WHERE " +
                ("c.is_sample AND c.status='ready' AND m.account_id IS NULL" if samples else "m.account_id IS NOT NULL") +
                " ORDER BY c.created_at,c.id"), {"uid": uid}).mappings()
            return [_course(row) for row in rows]

    def find_sample(self, doc_id):
        with self._connection() as connection:
            row = connection.execute(text("SELECT * FROM course WHERE is_sample AND doc_id=:doc ORDER BY created_at,id LIMIT 1"),
                                     {"doc": doc_id}).mappings().first()
        return _course(row) if row else None

    def update_course(self, cid, title, description, now):
        with self._connection() as connection:
            connection.execute(text("UPDATE course SET title=:title,description=:description,updated_at=:now WHERE id=:cid"),
                               {"cid": cid, "title": title, "description": description, "now": now})

    def member_count(self, cid):
        with self._connection() as connection:
            return connection.scalar(text("SELECT count(*) FROM membership WHERE course_id=:cid"), {"cid": cid})

    def owner_name(self, uid):
        with self._connection() as connection:
            return connection.scalar(text("SELECT display_name FROM account WHERE id=:uid"), {"uid": uid})

    def touch(self, cid, uid, now):
        from datetime import timedelta
        with self._connection() as connection:
            connection.execute(text("UPDATE membership SET last_active_at=:now WHERE course_id=:cid AND account_id=:uid "
                "AND (last_active_at IS NULL OR last_active_at < :cutoff)"),
                {"cid": cid, "uid": uid, "now": now, "cutoff": now - timedelta(minutes=5)})
