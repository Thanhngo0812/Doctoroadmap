import base64
import hashlib
import re
import secrets
import logging
from dataclasses import replace
from datetime import datetime, time, timedelta
from types import SimpleNamespace
from zoneinfo import ZoneInfo
from uuid import uuid4

from doc2roadmap.application.phase_b.clock import SystemClock

from wayfinder.api.errors import WebError
from wayfinder.application.auth_ports import AuditEvent
from wayfinder.application.accounts import AuthError, normalize_email
from wayfinder.domain.auth import decide
from wayfinder.domain.courses import Membership
from wayfinder.domain.sharing import Invitation, ShareLink


_DEFAULT_EXPIRY = object()
_TOKEN = re.compile(r"[A-Za-z0-9_-]{43}\Z")


class SharingService:
    def __init__(self, store, settings, clock=None, *, graph_loader=None, mailer=None):
        self.store = store
        self.settings = settings
        self.clock = clock or SystemClock()
        self.graph_loader = graph_loader
        self.mailer = mailer

    def invite_by_email(self, actor, cid, emails, *, ip=None):
        self._require_course(actor, cid, "manage_sharing")
        if not isinstance(emails, list) or not 1 <= len(emails) <= self.settings.invite_batch_max:
            raise self._validation("emails")
        recipients = []
        for index, email in enumerate(emails):
            try:
                recipients.append(normalize_email(email))
            except AuthError:
                raise self._validation(f"emails.{index}") from None
        recipients = list(dict.fromkeys(recipients))
        pending, deliveries = [], []
        with self.store.atomic():
            self.store.lock_invitation_sender(actor.user_id)
            course, _ = self._require_course(actor, cid, "manage_sharing", for_update=True)
            self._invitation_account(actor)
            now = self.clock.now()
            local = now.astimezone(ZoneInfo('Asia/Ho_Chi_Minh'))
            start = datetime.combine(local.date(), time.min, tzinfo=local.tzinfo)
            end = start + timedelta(days=1)
            if self.store.invitation_send_count(actor.user_id, start, end) + len(recipients) > self.settings.invite_emails_per_day:
                raise WebError('rate_limited', 'Bạn đã đạt giới hạn gửi lời mời hôm nay.',
                               retry_after=max(1, int((end-now).total_seconds())))
            for email in recipients:
                previous = self.store.pending_invitation(cid, email)
                account = self.store.invitation_account(email=email)
                recipient_id = str(account['id']) if account and account['email_verified_at'] is not None else None
                raw = secrets.token_urlsafe(32)
                invitation = Invitation(previous.id if previous else str(uuid4()), cid, email, recipient_id,
                    actor.user_id, hashlib.sha256(raw.encode()).digest(), 'pending',
                    now + timedelta(days=self.settings.invite_ttl_days), previous.created_at if previous else now)
                self.store.save_invitation(invitation, existing=previous is not None)
                self.store.append_audit(AuditEvent(now, actor.user_id, 'invitation_sent', 'invitation', invitation.id, ip))
                pending.append({**self._invitation_json(invitation, now), 'course_title': course.title})
                deliveries.append((email, raw))
        # Reuse the configured W03 Mailer, after commit; no mail on a rolled back invitation.
        from wayfinder.application.email_templates import render_invitation_email
        for email, raw in deliveries:
            content = render_invitation_email(course_title=course.title,
                action_url=f'{self.settings.public_base_url.rstrip("/")}/dang-ky#invitation={raw}',
                base_url=self.settings.public_base_url, valid_days=self.settings.invite_ttl_days,
                logo_url=self.settings.email_logo_url)
            if self.mailer is not None:
                try:
                    self.mailer.send(email, content.subject, content.text, html_body=content.html)
                except Exception:
                    logging.getLogger(__name__).warning('Invitation email delivery unavailable')
        return {'items': pending}

    def attach_verified_invitations(self, account):
        self.store.bind_verified_invitations(account, self.clock.now())

    def list_course_invitations(self, actor, cid):
        self._require_course(actor, cid, 'manage_sharing')
        now = self.clock.now()
        return {'items': [{**self._invitation_json(item, now), 'course_title': title}
                          for item,title in self.store.list_invitations(cid=cid)]}

    def list_my_invitations(self, actor):
        self._authorize(actor, 'list_courses')
        account = self.store.invitation_account(uid=actor.user_id)
        if not account or account['email_verified_at'] is None:
            return {'items': []}
        # Idempotent repair if verification committed before the post-commit hook could run.
        self.attach_verified_invitations(SimpleNamespace(id=actor.user_id))
        return {'items': [{**self._invitation_json(item, self.clock.now()), 'course_title': title}
                          for item,title in self.store.list_invitations(
            uid=actor.user_id, email=account['email_normalized'], now=self.clock.now())]}

    def cancel_invitation(self, actor, cid, iid, *, ip=None):
        with self.store.atomic():
            self._require_course(actor, cid, 'manage_sharing', for_update=True)
            invitation = self.store.get_invitation(iid, for_update=True)
            if invitation is None or invitation.course_id != cid:
                raise self._not_found()
            if invitation.status == 'cancelled':
                return {'message': 'Đã huỷ lời mời.'}
            self._pending_invitation(invitation)
            self._respond_invitation(actor, invitation, 'cancelled', ip)
        return {'message': 'Đã huỷ lời mời.'}

    def accept_invitation(self, actor, iid, *, ip=None):
        return self._respond_to_invitation(actor, iid, accept=True, ip=ip)

    def decline_invitation(self, actor, iid, *, ip=None):
        return self._respond_to_invitation(actor, iid, accept=False, ip=ip)

    def _respond_to_invitation(self, actor, iid, *, accept, ip):
        account = self._invitation_account(actor)
        candidate = self.store.get_invitation(iid)
        if candidate is None or candidate.email_normalized != account['email_normalized']:
            raise self._not_found()
        with self.store.atomic():
            # All invitation mutations lock course before invitation; shares W11 capacity lock.
            course = self.store.get_course(candidate.course_id, for_update=True)
            invitation = self.store.get_invitation(iid, for_update=True)
            account = self._invitation_account(actor)
            if course is None or invitation is None or invitation.email_normalized != account['email_normalized'] or (
                    invitation.invitee_account_id is not None and invitation.invitee_account_id != actor.user_id):
                raise self._not_found()
            member = self.store.get_membership(course.id, actor.user_id)
            if accept and invitation.status == 'accepted' and member is not None:
                return self._join_json(course.id, member.role, member.joined_at, True)
            if not accept and invitation.status == 'declined':
                return {'message': 'Đã từ chối lời mời.'}
            self._pending_invitation(invitation)
            now = self.clock.now()
            if accept:
                already = member is not None
                if member is None:
                    if self.store.member_count(course.id) >= self.settings.course_max_members:
                        raise WebError('course_full', 'Khoá học đã đủ thành viên')
                    member = Membership(course.id, actor.user_id, 'learner', 'email', now, now)
                    self.store.add_membership(member)
                result = self._join_json(course.id, member.role, member.joined_at, already)
            else:
                result = {'message': 'Đã từ chối lời mời.'}
            invitation = replace(invitation, invitee_account_id=actor.user_id)
            self._respond_invitation(actor, invitation, 'accepted' if accept else 'declined', ip)
        return result

    def _invitation_account(self, actor):
        self._authorize(actor, 'list_courses')
        account = self.store.invitation_account(uid=actor.user_id)
        if not account or account['status'] != 'active':
            raise self._not_found()
        if not actor.email_verified or account['email_verified_at'] is None:
            raise WebError('email_unverified', 'Vui lòng xác minh email trước khi dùng lời mời.')
        return account

    def _pending_invitation(self, invitation):
        if invitation.status != 'pending' or self.clock.now() >= invitation.expires_at:
            raise self._invalid_link()

    def _respond_invitation(self, actor, invitation, status, ip):
        now = self.clock.now()
        self.store.save_invitation(replace(invitation, status=status, responded_at=now), existing=True)
        self.store.append_audit(AuditEvent(now, actor.user_id, 'invitation_'+status, 'invitation', invitation.id, ip))

    @staticmethod
    def _invitation_json(invitation, now):
        return {key: value.isoformat() if isinstance(value, datetime) else value for key,value in {
            'id': invitation.id, 'course_id': invitation.course_id, 'email': invitation.email_normalized,
            'status': 'expired' if invitation.status=='pending' and now>=invitation.expires_at else invitation.status,
            'expires_at': invitation.expires_at, 'created_at': invitation.created_at,
            'responded_at': invitation.responded_at}.items()}

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
