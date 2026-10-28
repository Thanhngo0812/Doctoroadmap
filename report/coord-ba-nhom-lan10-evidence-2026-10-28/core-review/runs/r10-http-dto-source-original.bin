from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, ConfigDict, Field, StrictInt

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

    @router.patch('/users/{uid}',response_model=AdminUserResponse)
    def update_user(uid: UUID, data: AdminUserPatch, request: Request, admin=Depends(service),actor: Actor=Depends(get_actor)):
        return admin.update_user(actor,str(uid),data.model_dump(exclude_unset=True),ip=client_ip(request))

    @router.get('/audit',response_model=AdminAuditResponse)
    def audit(request: Request, admin=Depends(service),actor: Actor=Depends(get_actor),
              actor_id: UUID | None=None, action: str | None=Query(None,min_length=1,max_length=80,pattern=r'^[a-z][a-z0-9_]*$'),
              since: datetime | None=None, until: datetime | None=None,
              limit: int=Query(50,ge=1,le=100),offset: int=Query(0,ge=0,le=100000)):
        return admin.list_audit(actor,actor_id=str(actor_id) if actor_id else None,action=action,
            since=since,until=until,limit=limit,offset=offset)

    return router
