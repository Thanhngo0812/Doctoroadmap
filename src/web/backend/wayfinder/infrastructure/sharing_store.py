from contextlib import contextmanager
from contextvars import ContextVar
from uuid import UUID

from sqlalchemy import insert, select, text, update

from wayfinder.application.auth_ports import AuditEvent
from wayfinder.domain.courses import Course, Membership
from wayfinder.domain.sharing import ShareLink, ShareMember
from wayfinder.infrastructure.sharing_schema import sharing_metadata


class PostgresSharingStore:
    def __init__(self, engine):
        self.engine = engine
        self._metadata = sharing_metadata()
        self._tables = self._metadata.tables
        self._connection = ContextVar(f"wayfinder_sharing_connection_{id(self)}", default=None)

    @contextmanager
    def atomic(self):
        if self._connection.get() is not None:
            raise RuntimeError("SharingStore.atomic cannot be nested")
        with self.engine.begin() as connection:
            token = self._connection.set(connection)
            try:
                yield
            finally:
                self._connection.reset(token)

    def get_course(self, cid, *, for_update=False):
        try:
            cid = str(UUID(cid))
        except (ValueError, TypeError, AttributeError):
            return None
        suffix = " FOR UPDATE" if for_update else ""
        with self._use_connection() as connection:
            row = connection.execute(text("SELECT * FROM course WHERE id=:cid" + suffix), {"cid": cid}).mappings().first()
        if row is None:
            return None
        return Course(**{key: str(value) if isinstance(value, UUID) else value for key, value in row.items()})

    def get_membership(self, cid, uid):
        try:
            cid, uid = str(UUID(cid)), str(UUID(uid))
        except (ValueError, TypeError, AttributeError):
            return None
        with self._use_connection() as connection:
            row = connection.execute(text("SELECT * FROM membership WHERE course_id=:cid AND account_id=:uid"),
                                     {"cid": cid, "uid": uid}).mappings().first()
        return Membership(**{key: str(value) if isinstance(value, UUID) else value for key, value in row.items()}) if row else None

    def get_link_by_hash(self, token_hash, *, for_update=False):
        table = self._table("share_link")
        statement = select(table).where(table.c.token_hash == token_hash)
        if for_update:
            statement = statement.with_for_update()
        with self._use_connection() as connection:
            row = connection.execute(statement).mappings().first()
        return _link(row) if row else None

    def get_link(self, cid, lid, *, for_update=False):
        try:
            cid, lid = str(UUID(cid)), str(UUID(lid))
        except (ValueError, TypeError, AttributeError):
            return None
        table = self._table("share_link")
        statement = select(table).where(table.c.course_id == cid, table.c.id == lid)
        if for_update:
            statement = statement.with_for_update()
        with self._use_connection() as connection:
            row = connection.execute(statement).mappings().first()
        return _link(row) if row else None

    def list_links(self, cid):
        table = self._table("share_link")
        with self._use_connection() as connection:
            rows = connection.execute(select(table).where(table.c.course_id == cid).order_by(
                table.c.created_at.desc(), table.c.id)).mappings()
            return [_link(row) for row in rows]

    def add_link(self, link):
        table = self._table("share_link")
        with self._use_connection(write=True) as connection:
            connection.execute(insert(table).values(**_link_values(link)))

    def revoke_link(self, link_id, at):
        table = self._table("share_link")
        with self._use_connection(write=True) as connection:
            connection.execute(update(table).where(table.c.id == link_id, table.c.revoked_at.is_(None)).values(revoked_at=at))

    def member_count(self, cid):
        with self._use_connection() as connection:
            return connection.scalar(text("SELECT count(*) FROM membership WHERE course_id=:cid"), {"cid": cid})

    def owner_summary(self, uid):
        with self._use_connection() as connection:
            row = connection.execute(text("SELECT id,display_name FROM account WHERE id=:uid"), {"uid": uid}).mappings().first()
        return {"user_id": str(row["id"]), "display_name": row["display_name"]} if row else None

    def concept_count(self, cid):
        raise NotImplementedError("concept count requires the published graph loader")

    def list_members(self, cid):
        with self._use_connection() as connection:
            rows = connection.execute(text("SELECT m.account_id,m.role,m.joined_at,m.last_active_at,m.via,a.display_name "
                "FROM membership m JOIN account a ON a.id=m.account_id WHERE m.course_id=:cid ORDER BY m.joined_at,m.account_id"),
                {"cid": cid}).mappings()
        return [ShareMember(str(row["account_id"]), row["display_name"], row["role"], row["joined_at"],
                            row["last_active_at"], row["via"]) for row in rows]

    def add_membership(self, member):
        # Membership is part of the W-06 schema, so issue a parameterized insert into the existing table.
        with self._use_connection(write=True) as connection:
            result = connection.execute(text("INSERT INTO membership (course_id,account_id,role,via,joined_at,last_active_at) "
                "VALUES (:cid,:uid,:role,:via,:joined,:active) ON CONFLICT (course_id,account_id) DO NOTHING RETURNING account_id"),
                {"cid": member.course_id, "uid": member.account_id, "role": member.role, "via": member.via,
                 "joined": member.joined_at, "active": member.last_active_at})
            return result.scalar_one_or_none() is not None

    def remove_membership(self, cid, uid):
        with self._use_connection(write=True) as connection:
            result = connection.execute(text("DELETE FROM membership WHERE course_id=:cid AND account_id=:uid RETURNING account_id"),
                                        {"cid": cid, "uid": uid})
            return result.scalar_one_or_none() is not None

    def increment_use_count(self, link_id, max_uses):
        table = self._table("share_link")
        condition = [table.c.id == link_id]
        if max_uses is not None:
            condition.append(table.c.use_count < max_uses)
        with self._use_connection(write=True) as connection:
            return connection.execute(update(table).where(*condition).values(use_count=table.c.use_count + 1)
                                      .returning(table.c.id)).scalar_one_or_none() is not None

    def append_audit(self, event: AuditEvent):
        with self._use_connection(write=True) as connection:
            connection.execute(text("INSERT INTO audit_event (at,actor_id,action,target_kind,target_id,ip,meta) "
                "VALUES (:at,:actor,:action,:kind,:target,:ip,CAST(:meta AS jsonb))"), {
                    "at": event.at, "actor": event.actor_id, "action": event.action, "kind": event.target_kind,
                    "target": event.target_id, "ip": event.ip,
                    "meta": __import__("json").dumps(event.meta, ensure_ascii=False),
                })

    @contextmanager
    def _use_connection(self, *, write=False):
        current = self._connection.get()
        if current is not None:
            yield current
        elif write:
            with self.engine.begin() as connection:
                yield connection
        else:
            with self.engine.connect() as connection:
                yield connection

    def _table(self, name):
        return self._tables[name]


def _link(row):
    return ShareLink(id=str(row["id"]), course_id=str(row["course_id"]), token_hash=bytes(row["token_hash"]),
        token_tail=row["token_tail"], created_by=str(row["created_by"]) if row["created_by"] else None,
        expires_at=row["expires_at"], max_uses=row["max_uses"], use_count=row["use_count"],
        revoked_at=row["revoked_at"], created_at=row["created_at"])


def _link_values(link):
    return {"id": link.id, "course_id": link.course_id, "token_hash": link.token_hash,
        "token_tail": link.token_tail, "created_by": link.created_by, "expires_at": link.expires_at,
        "max_uses": link.max_uses, "use_count": link.use_count, "revoked_at": link.revoked_at,
        "created_at": link.created_at}
