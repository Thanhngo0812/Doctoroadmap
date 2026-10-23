import base64
import hashlib
import re
import secrets
from datetime import timedelta
from uuid import uuid4

from doc2roadmap.application.phase_b.clock import SystemClock

from wayfinder.api.errors import WebError
from wayfinder.application.auth_ports import AuditEvent
from wayfinder.domain.auth import decide
from wayfinder.domain.courses import Membership
from wayfinder.domain.sharing import ShareLink


_DEFAULT_EXPIRY = object()
_TOKEN = re.compile(r"[A-Za-z0-9_-]{43}\Z")


class SharingService:
    def __init__(self, store, settings, clock=None, *, graph_loader=None):
        self.store = store
        self.settings = settings
        self.clock = clock or SystemClock()
        self.graph_loader = graph_loader

    def create_share_link(self, actor, cid, *, expires_in_days=_DEFAULT_EXPIRY, max_uses=None, ip=None):
        course, _ = self._require_course(actor, cid, "manage_sharing")
        if expires_in_days is _DEFAULT_EXPIRY:
            expires_in_days = self.settings.share_link_default_days
        if expires_in_days is not None and (type(expires_in_days) is not int or expires_in_days <= 0):
            raise self._validation("expires_in_days")
        if max_uses is not None and (type(max_uses) is not int or not 1 <= max_uses <= 2_147_483_647):
            raise self._validation("max_uses")
        now = self.clock.now()
        raw_token = secrets.token_bytes(32)
        token = base64.urlsafe_b64encode(raw_token).rstrip(b"=").decode("ascii")
        try:
            expires_at = now + timedelta(days=expires_in_days) if expires_in_days is not None else None
        except OverflowError:
            raise self._validation("expires_in_days") from None
        link = ShareLink(
            str(uuid4()), course.id, hashlib.sha256(raw_token).digest(), token[-6:], actor.user_id,
            expires_at,
            max_uses, 0, None, now,
        )
        with self.store.atomic():
            self.store.add_link(link)
            self.store.append_audit(AuditEvent(now, actor.user_id, "share_link_created", "share_link", link.id, ip))
        return {"link": {**self._link_json(link, now), "token": token,
                          "url": f"{self.settings.public_base_url}/join/{token}"}}

    def list_share_links(self, actor, cid):
        self._require_course(actor, cid, "manage_sharing")
        now = self.clock.now()
        return {"items": [self._link_json(link, now) for link in self.store.list_links(cid)]}

    def revoke_share_link(self, actor, cid, link_id, *, ip=None):
        self._require_course(actor, cid, "manage_sharing")
        now = self.clock.now()
        with self.store.atomic():
            link = self.store.get_link(cid, link_id, for_update=True)
            if link is None:
                raise self._not_found()
            if link.revoked_at is None:
                self.store.revoke_link(link.id, now)
                self.store.append_audit(AuditEvent(now, actor.user_id, "share_link_revoked", "share_link", link.id, ip))
        return {"message": "Đã thu hồi link chia sẻ."}

    def preview_share_link(self, token):
        now = self.clock.now()
        link = self.store.get_link_by_hash(self._token_hash(token))
        if not self._valid(link, now, check_uses=True):
            raise self._invalid_link()
        course = self.store.get_course(link.course_id)
        if course is None:
            raise self._invalid_link()
        if course.status != "ready" or course.published_graph_version is None:
            concepts = 0
        elif self.graph_loader:
            concepts = len(self.graph_loader(course.doc_id, course.published_graph_version).learnable_nodes)
        else:
            concepts = self.store.concept_count(course.id)
        return {"course_id": course.id, "title": course.title,
                "owner": {"display_name": self.store.owner_summary(course.owner_id)["display_name"]},
                "module_count": course.module_count, "concept_count": concepts}

    def join_by_link(self, actor, token, *, ip=None):
        self._authorize(actor, "list_courses")
        token_hash = self._token_hash(token)
        with self.store.atomic():
            link = self.store.get_link_by_hash(token_hash, for_update=True)
            now = self.clock.now()
            if not self._valid(link, now):
                raise self._invalid_link()
            course = self.store.get_course(link.course_id, for_update=True)
            if course is None:
                raise self._invalid_link()
            member = self.store.get_membership(course.id, actor.user_id)
            if member is not None:
                return self._join_json(course.id, member.role, member.joined_at, True)
            if link.max_uses is not None and link.use_count >= link.max_uses:
                raise self._invalid_link()
            decision = decide(actor, "join_link", course, None)
            if not decision.allowed:
                raise WebError(decision.code, "Không có quyền thực hiện yêu cầu")
            if self.store.member_count(course.id) >= self.settings.course_max_members:
                raise WebError("course_full", "Khoá học đã đủ thành viên")
            member = Membership(course.id, actor.user_id, "learner", "link", now, now)
            if not self.store.add_membership(member):
                # The course lock serializes real PostgreSQL joins; this protects alternate stores.
                member = self.store.get_membership(course.id, actor.user_id)
                return self._join_json(course.id, member.role, member.joined_at, True)
            if not self.store.increment_use_count(link.id, link.max_uses):
                raise self._invalid_link()
            self.store.append_audit(AuditEvent(now, actor.user_id, "member_joined", "course", course.id, ip,
                                               {"via": "link"}))
            return self._join_json(course.id, member.role, member.joined_at, False)

    def list_members(self, actor, cid):
        course, member = self._require_course(actor, cid, "list_members")
        count = self.store.member_count(cid)
        result = {"role": member.role, "owner": self.store.owner_summary(course.owner_id), "member_count": count}
        if member.role == "owner":
            result["members"] = [{"user_id": item.user_id, "display_name": item.display_name,
                                  "joined_at": item.joined_at.isoformat(),
                                  "last_active_at": item.last_active_at.isoformat() if item.last_active_at else None,
                                  "via": item.via}
                                 for item in self.store.list_members(cid)]
        return result

    def remove_member(self, actor, cid, user_id, *, ip=None):
        course, _ = self._require_course(actor, cid, "manage_sharing")
        now = self.clock.now()
        with self.store.atomic():
            course, _ = self._require_course(actor, cid, "manage_sharing", for_update=True)
            member = self.store.get_membership(cid, user_id)
            if member is None:
                raise self._not_found()
            if member.role == "owner":
                raise WebError("forbidden", "Chủ khoá không thể tự xoá mình khỏi khoá học.")
            self.store.remove_membership(cid, user_id)
            self.store.append_audit(AuditEvent(now, actor.user_id, "member_removed", "course", cid, ip,
                                               {"member_id": user_id}))
        return {"message": "Đã xoá thành viên."}

    def leave_course(self, actor, cid, *, ip=None):
        course, member = self._require_course(actor, cid, "leave_course")
        if member.role == "owner":
            raise WebError("forbidden", "Chủ khoá không thể rời khoá học.")
        now = self.clock.now()
        with self.store.atomic():
            course, member = self._require_course(actor, cid, "leave_course", for_update=True)
            if member.role == "owner":
                raise WebError("forbidden", "Chủ khoá không thể rời khoá học.")
            self.store.remove_membership(cid, actor.user_id)
            self.store.append_audit(AuditEvent(now, actor.user_id, "member_left", "course", cid, ip))
        return {"message": "Đã rời khoá học."}

    def _require_course(self, actor, cid, action, *, for_update=False):
        self._authorize(actor, "list_courses")
        course = self.store.get_course(cid, for_update=for_update)
        member = self.store.get_membership(cid, actor.user_id) if course else None
        decision = decide(actor, action, course, member)
        if not decision.allowed:
            message = "Không tìm thấy nội dung yêu cầu" if decision.code == "not_found" else "Không có quyền thực hiện yêu cầu"
            raise WebError(decision.code, message)
        return course, member

    @staticmethod
    def _authorize(actor, action):
        decision = decide(actor, action, None, None)
        if not decision.allowed:
            raise WebError(decision.code, "Không có quyền thực hiện yêu cầu")

    @staticmethod
    def _token_hash(token):
        if not isinstance(token, str) or not _TOKEN.fullmatch(token):
            raise SharingService._invalid_link()
        try:
            raw = base64.b64decode(token + "=", altchars=b"-_", validate=True)
        except (ValueError, base64.binascii.Error):
            raise SharingService._invalid_link() from None
        if len(raw) != 32:
            raise SharingService._invalid_link()
        if base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii") != token:
            raise SharingService._invalid_link()
        return hashlib.sha256(raw).digest()

    @staticmethod
    def _valid(link, now, *, check_uses=False):
        return bool(link and link.revoked_at is None and
                    (link.expires_at is None or link.expires_at > now) and
                    (not check_uses or link.max_uses is None or link.use_count < link.max_uses))

    @staticmethod
    def _invalid_link():
        return WebError("link_invalid", "Link tham gia không hợp lệ hoặc đã hết hạn.")

    @staticmethod
    def _not_found():
        return WebError("not_found", "Không tìm thấy nội dung yêu cầu")

    @staticmethod
    def _validation(field):
        return WebError("validation", "Dữ liệu yêu cầu không hợp lệ", fields=[
            {"loc": field, "type": "value_error", "message": "Giá trị không hợp lệ"}])

    @staticmethod
    def _join_json(course_id, role, joined_at, already_member):
        return {"course_id": course_id, "role": role, "joined_at": joined_at.isoformat(),
                "already_member": already_member}

    @staticmethod
    def _link_json(link, now):
        if link.revoked_at is not None:
            status = "revoked"
        elif link.expires_at is not None and link.expires_at <= now:
            status = "expired"
        elif link.max_uses is not None and link.use_count >= link.max_uses:
            status = "exhausted"
        else:
            status = "active"
        return {"id": link.id, "token_tail": link.token_tail, "created_at": link.created_at.isoformat(),
                "expires_at": link.expires_at.isoformat() if link.expires_at else None,
                "max_uses": link.max_uses, "use_count": link.use_count,
                "revoked_at": link.revoked_at.isoformat() if link.revoked_at else None, "status": status}
