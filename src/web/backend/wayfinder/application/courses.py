from uuid import uuid4

from doc2roadmap.application.phase_b.clock import SystemClock
from wayfinder.api.errors import WebError
from wayfinder.domain.auth import decide
from wayfinder.domain.courses import Course, Membership


class CourseService:
    def __init__(self, store, *, settings, clock=None):
        self.store, self.settings = store, settings
        self.clock = clock or SystemClock()
        self.gateway = None
        self.build_service = None

    def authorize(self, actor, action, course=None, member=None):
        decision = decide(actor, action, course, member)
        if not decision.allowed:
            raise WebError(decision.code, "Không tìm thấy nội dung yêu cầu" if decision.code == "not_found" else "Không có quyền thực hiện yêu cầu")

    def require_course(self, actor, cid, *, action="read_course", for_update=False):
        self.authorize(actor, "list_courses")
        course = self.store.get_course(cid, for_update=for_update)
        member = self.store.get_membership(course.id, actor.user_id) if course else None
        self.authorize(actor, action, course, member)
        return course, member

    def create_course(self, actor, *, doc_id, title, graph_version, module_count, description="",
                      is_sample=False, source_public_id=None):
        self.authorize(actor, "seed_samples" if is_sample else "create_course")
        if is_sample:
            from wayfinder.application.seed_samples import SAMPLE_DOCS
            if self.settings.env != "dev" or doc_id not in SAMPLE_DOCS:
                raise WebError("not_found", "Không tìm thấy nội dung yêu cầu")
        now = self.clock.now()
        course = Course(str(uuid4()), actor.user_id, doc_id, title.strip(), description, "ready", graph_version,
                        is_sample, module_count, source_public_id, now, now)
        with self.store.atomic():
            self.store.add_course(course)
            self.store.add_membership(Membership(course.id, actor.user_id, "owner", "owner", now, now))
        return course

    def list_my_courses(self, actor):
        self.authorize(actor, "list_courses")
        result = {"owned": [], "joined": [], "samples": self.list_sample_courses(actor)}
        for course in self.store.list_courses(actor.user_id):
            result["owned" if course.owner_id == actor.user_id else "joined"].append(self._card(actor, course))
        return result

    def list_sample_courses(self, actor):
        self.authorize(actor, "list_courses")
        return [self._card(actor, course, preview=True) for course in self.store.list_courses(actor.user_id, samples=True)] if self.settings.env == "dev" else []

    def get_course(self, actor, cid):
        course, _ = self.require_course(actor, cid)
        return self._card(actor, course)

    def update_course(self, actor, cid, changes):
        with self.store.atomic():
            course, _ = self.require_course(actor, cid, action="update_course", for_update=True)
            title = changes.get("title", course.title).strip()
            description = changes.get("description", course.description)
            if not 1 <= len(title) <= 120 or len(description) > 1000:
                raise WebError("validation", "Tên hoặc mô tả không hợp lệ")
            self.store.update_course(cid, title, description, self.clock.now())
        return self.get_course(actor, cid)

    def join_sample_course(self, actor, cid):
        self.authorize(actor, "list_courses")
        with self.store.atomic():
            course = self.store.get_course(cid, for_update=True)
            if self.settings.env != "dev" or course is None or not course.is_sample or course.status != "ready":
                raise WebError("not_found", "Không tìm thấy nội dung yêu cầu")
            member = self.store.get_membership(cid, actor.user_id)
            self.authorize(actor, "join_sample", course, member)
            if member is None:
                if self.store.member_count(cid) >= self.settings.course_max_members:
                    raise WebError("course_full", "Khoá học đã đủ thành viên")
                now = self.clock.now()
                self.store.add_membership(Membership(cid, actor.user_id, "learner", "sample", now, now))
        return self.get_course(actor, cid)

    def _card(self, actor, course, *, preview=False):
        member = None if preview else self.store.get_membership(course.id, actor.user_id)
        summary = {"progress": None, "resume": None}
        if member is not None and course.status == "ready":
            summary = self.gateway.course_summary(actor, course.id)
        return {"course_id": course.id, "doc_id": course.doc_id, "title": course.title,
            "description": course.description, "status": course.status, "is_sample": course.is_sample,
            "published_graph_version": course.published_graph_version,
            "role": member.role if member else None,
            "owner": {"user_id": course.owner_id, "display_name": self.store.owner_name(course.owner_id)},
            "module_count": course.module_count,
            "member_count": self.store.member_count(course.id) if member and member.role == "owner" else None,
            **summary,
            "build": self.build_service.course_build(actor, course) if self.build_service and course.build_id else None}
