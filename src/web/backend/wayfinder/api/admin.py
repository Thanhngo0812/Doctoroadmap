from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt

from wayfinder.api.auth import client_ip, get_actor
from wayfinder.api.errors import WebError
from wayfinder.domain.auth import Actor


class AdminUserPatch(BaseModel):
    model_config = ConfigDict(extra='forbid')
    status: Literal['active','disabled'] | None = None
    role: Literal['user','admin'] | None = None
    build_monthly_max: Annotated[StrictInt, Field(ge=1, le=2147483647)] | None = None


class AdminMonthlyBuilds(BaseModel):
    used: int
    max: int | None
    resets_at: datetime


class AdminUserResponse(BaseModel):
    id: str
    email: str
    display_name: str
    role: Literal['user','admin']
    status: Literal['active','disabled']
    email_verified_at: datetime | None
    created_at: datetime
    last_login_at: datetime | None
    owned_courses: int
    build_monthly_max: int | None
    builds_this_month: AdminMonthlyBuilds
    is_first_admin: bool | None


class AdminUsersResponse(BaseModel):
    items: list[AdminUserResponse]
    total: int
    limit: int
    offset: int


class AdminAuditItem(BaseModel):
    id: int
    at: datetime
    actor_id: str | None
    action: str
    target_kind: str | None
    target_id: str | None
    ip: str | None


class AdminAuditResponse(BaseModel):
    items: list[AdminAuditItem]
    total: int
    limit: int
    offset: int


BuildStatus = Literal['awaiting_confirmation','queued','reading','running','rejected','succeeded','failed','cancelled']


class AdminBuildRequester(BaseModel):
    user_id: str
    email: str


class AdminBuildUpload(BaseModel):
    kind: Literal['pdf','docx']
    page_count: int | None
    size_bytes: int


class AdminBuildError(BaseModel):
    code: Literal['ban_quet','chu_loi','ngon_ngu_khong_ho_tro','loi_mang','het_tran_he_thong','loi_noi_bo','confirmation_expired','khong_ro']
    message: str
    retryable: bool


class AdminBuildUsage(BaseModel):
    spent_usd: float
    model_calls: int
    input_tokens: int
    output_tokens: int
    usage_complete: bool
    elapsed_seconds: float


class AdminBuildItem(BaseModel):
    build_id: str
    doc_id: str
    status: BuildStatus
    step: Literal['doc_reading','concepts','graph','learning_prep'] | None
    pipeline_version: str
    requested_by: AdminBuildRequester | None
    upload: AdminBuildUpload | None
    course_count: int
    counts_quota: bool
    cancel_requested: bool
    claim_count: int
    created_at: datetime
    queued_at: datetime | None
    started_at: datetime | None
    finished_at: datetime | None
    error: AdminBuildError | None
    usage: AdminBuildUsage
    graph_version: int | None
    module_count: int


class AdminBuildsResponse(BaseModel):
    items: list[AdminBuildItem]
    total: int
    limit: int
    offset: int


class AdminCoursePatch(BaseModel):
    model_config = ConfigDict(extra='forbid')
    is_sample: StrictBool


class AdminCourseResponse(BaseModel):
    course_id: str
    doc_id: str
    title: str
    status: Literal['building','ready','failed']
    is_sample: bool
    published_graph_version: int | None
    module_count: int
    updated_at: datetime


class AdminPolicyField(BaseModel):
    loc: str
    message: str


class AdminPolicyError(BaseModel):
    code: Literal['protected_admin','bootstrap_required','conflict']
    message: str
    retry_after: int | None = None
    ref: str | None = None
    fields: list[AdminPolicyField] | None = None


class AdminPolicyErrorResponse(BaseModel):
    error: AdminPolicyError


def admin_router():
    router = APIRouter(prefix='/api/v1/admin', tags=['admin'])

    def service(request: Request, actor: Actor = Depends(get_actor)):
        admin = request.app.state.services.admin
        if admin is None:
            raise WebError('internal_error','Dịch vụ quản trị chưa sẵn sàng.')
        admin.authorize(actor)
        return admin

    @router.get('/users',response_model=AdminUsersResponse)
    def users(request: Request, admin=Depends(service), actor: Actor=Depends(get_actor),
              email: str=Query('',max_length=254), role: Literal['user','admin'] | None=None,
              status: Literal['active','disabled'] | None=None, limit: int=Query(50,ge=1,le=100),
              offset: int=Query(0,ge=0,le=100000)):
        return admin.list_users(actor,email=email,role=role,status=status,limit=limit,offset=offset)

    @router.patch('/users/{uid}',response_model=AdminUserResponse,responses={409:{'model':AdminPolicyErrorResponse}})
    def update_user(uid: UUID, data: AdminUserPatch, request: Request, admin=Depends(service),actor: Actor=Depends(get_actor)):
        return admin.update_user(actor,str(uid),data.model_dump(exclude_unset=True),ip=client_ip(request))

    @router.get('/audit',response_model=AdminAuditResponse)
    def audit(request: Request, admin=Depends(service),actor: Actor=Depends(get_actor),
              actor_id: UUID | None=None, action: str | None=Query(None,min_length=1,max_length=80,pattern=r'^[a-z][a-z0-9_]*$'),
              since: datetime | None=None, until: datetime | None=None,
              limit: int=Query(50,ge=1,le=100),offset: int=Query(0,ge=0,le=100000)):
        return admin.list_audit(actor,actor_id=str(actor_id) if actor_id else None,action=action,
            since=since,until=until,limit=limit,offset=offset)

    @router.get('/builds',response_model=AdminBuildsResponse)
    def builds(request: Request, admin=Depends(service), actor: Actor=Depends(get_actor),
               q: str=Query('',max_length=254), status: BuildStatus | None=None, usage_complete: bool | None=None,
               since: datetime | None=None, until: datetime | None=None,
               limit: int=Query(50,ge=1,le=100),offset: int=Query(0,ge=0,le=100000)):
        return admin.list_builds(actor,q=q,status=status,usage_complete=usage_complete,since=since,until=until,
            limit=limit,offset=offset)

    @router.patch('/courses/{cid}',response_model=AdminCourseResponse,responses={409:{'model':AdminPolicyErrorResponse}})
    def set_sample(cid: UUID, data: AdminCoursePatch, request: Request, admin=Depends(service),actor: Actor=Depends(get_actor)):
        return admin.set_sample_course(actor,str(cid),data.is_sample,ip=client_ip(request))

    return router
