from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, Request, Response, UploadFile
from pydantic import BaseModel, ConfigDict, Field

from wayfinder.api.auth import get_actor
from wayfinder.domain.auth import Actor


class Confirmation(BaseModel):
    model_config=ConfigDict(extra='forbid')
    title: str | None = Field(default=None,min_length=1,max_length=120)


class BuildError(BaseModel):
    code: str
    message: str
    retryable: bool


class BuildView(BaseModel):
    contract_version: str
    build_id: str
    course_id: str
    upload_id: str | None = None
    status: str
    step: str | None
    step_index: int
    step_count: int
    started_at: datetime | None
    finished_at: datetime | None
    confirmation_expires_at: datetime
    cancel_requested: bool
    can_cancel: bool
    can_retry: bool
    error: BuildError | None


class UploadView(BaseModel):
    contract_version: str
    upload_id: str
    original_name: str
    kind: str
    size_bytes: int
    page_count: int | None
    confirmed_at: datetime | None = None
    build: BuildView


class BuildQuota(BaseModel):
    builds_used: int
    build_monthly_max: int | None
    builds_remaining: int | None


class LearnerUsage(BaseModel):
    used_ratio: float
    limited: bool
    resets_at: str


class SharedUsage(BaseModel):
    limited: bool


class MonthlyUsage(BaseModel):
    used: int
    max: int | None
    resets_at: str


class MyUsage(BuildQuota):
    contract_version: str = 'usage-1'
    learner_today: LearnerUsage
    shared_content_today: SharedUsage
    builds_this_month: MonthlyUsage


def build_router():
    router=APIRouter(prefix='/api/v1',tags=['builds'])

    @router.post('/uploads',response_model=UploadView)
    def upload(request:Request,file:UploadFile=File(),rights_confirmed:bool=Form(),actor:Actor=Depends(get_actor)):
        service=request.app.state.services.builds
        service.authorize(actor)
        try:
            content=file.file.read(service.settings.upload_max_mb*1024*1024+1)
            return service.create_upload(actor,file.filename or 'document',content,rights_confirmed=rights_confirmed)
        finally: file.file.close()

    @router.get('/uploads/{id}',response_model=UploadView)
    def get_upload(id:str,request:Request,response:Response,actor:Actor=Depends(get_actor)):
        response.headers['cache-control']='no-store'
        return request.app.state.services.builds.get_upload(actor,id)

    @router.post('/uploads/{id}/build',response_model=BuildView)
    def confirm(id:str,data:Confirmation,request:Request,actor:Actor=Depends(get_actor)):
        return request.app.state.services.builds.confirm_build(actor,id,title=data.title)

    @router.get('/builds/{id}',response_model=BuildView)
    def get_build(id:str,request:Request,response:Response,actor:Actor=Depends(get_actor),course_id:str|None=None):
        response.headers['cache-control']='no-store'
        return request.app.state.services.builds.get_build(actor,id,course_id=course_id)

    @router.post('/builds/{id}/cancel',response_model=BuildView)
    def cancel(id:str,request:Request,actor:Actor=Depends(get_actor),course_id:str|None=None):
        return request.app.state.services.builds.cancel_build(actor,id,course_id=course_id)

    @router.post('/builds/{id}/retry',response_model=BuildView)
    def retry(id:str,request:Request,actor:Actor=Depends(get_actor),course_id:str|None=None):
        return request.app.state.services.builds.retry_build(actor,id,course_id=course_id)

    @router.get('/me/usage',response_model=MyUsage)
    def quota(request:Request,response:Response,actor:Actor=Depends(get_actor)):
        response.headers['cache-control']='no-store'
        from wayfinder.infrastructure.learning_usage import my_learning_usage
        services=request.app.state.services
        learning=services.learning
        quota=services.builds.usage(actor) if services.builds else {'builds_used':0,'build_monthly_max':None,'builds_remaining':None}
        if learning is not None:
            amount=my_learning_usage(actor,learning.courses.store.engine,learning.runtime)
        else:
            from types import SimpleNamespace
            from doc2roadmap.domain.phase_b_limits import BSettings
            amount=my_learning_usage(actor,services.builds.store.engine,
                SimpleNamespace(clock=services.builds.clock,settings=BSettings()))
        return {**quota,**amount,'builds_this_month':{'used':quota['builds_used'],'max':quota['build_monthly_max'],
            'resets_at':amount.pop('build_month_resets_at')}}

    return router
