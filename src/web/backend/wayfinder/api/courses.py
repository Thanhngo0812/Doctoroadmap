from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from typing import Any, Literal

from wayfinder.api.auth import get_actor
from wayfinder.api.builds import BuildView
from wayfinder.domain.auth import Actor


class CourseChanges(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=1000)


class OwnerSummary(BaseModel):
    user_id: str
    display_name: str


class ProgressSummary(BaseModel):
    learned: int
    total: int


class Resume(BaseModel):
    module_id: str


class CourseCard(BaseModel):
    course_id: str
    doc_id: str
    title: str
    description: str
    status: str
    is_sample: bool
    published_graph_version: int | None
    role: str | None
    owner: OwnerSummary
    module_count: int
    member_count: int | None
    progress: ProgressSummary | None
    resume: Resume | None
    build: BuildView | None = None


class CourseList(BaseModel):
    owned: list[CourseCard]
    joined: list[CourseCard]
    samples: list[CourseCard]


class Concept(BaseModel):
    node_id: str
    name: str


class RoadmapModule(BaseModel):
    module_id: str
    index: int
    title: str
    description: str | list[dict[str, Any]]
    concepts: list[Concept]
    progress: ProgressSummary


class ProgressNode(BaseModel):
    state: Literal["learned", "not_learned"]
    source: Literal["learner", "quiz"] | None
    updated_at: str | None


class ProgressModule(BaseModel):
    module_id: str
    learned: int
    total: int


class CourseProgress(BaseModel):
    course_id: str
    contract_version: Literal["progress-1"]
    doc_id: str
    nodes: dict[str, ProgressNode]
    modules: list[ProgressModule]


class SetProgressRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    learned: bool = Field(strict=True)


class Roadmap(BaseModel):
    course_id: str
    doc_id: str
    graph_version: int
    progress: ProgressSummary
    modules: list[RoadmapModule]


def course_router():
    router = APIRouter(prefix="/api/v1/courses", tags=["courses"])

    @router.get("", response_model=CourseList)
    def courses(request: Request, response: Response, actor: Actor = Depends(get_actor)):
        response.headers["cache-control"] = "no-store"
        return request.app.state.services.courses.list_my_courses(actor)

    @router.get("/{cid}", response_model=CourseCard)
    def detail(cid: str, request: Request, response: Response, actor: Actor = Depends(get_actor)):
        response.headers["cache-control"] = "no-store"
        return request.app.state.services.courses.get_course(actor, cid)

    @router.patch("/{cid}", response_model=CourseCard)
    def update(cid: str, data: CourseChanges, request: Request, actor: Actor = Depends(get_actor)):
        return request.app.state.services.courses.update_course(actor, cid, data.model_dump(exclude_none=True))

    @router.post("/{cid}/join-sample", response_model=CourseCard)
    def join(cid: str, request: Request, actor: Actor = Depends(get_actor)):
        return request.app.state.services.courses.join_sample_course(actor, cid)

    @router.get("/{cid}/roadmap", response_model=Roadmap)
    def roadmap(cid: str, request: Request, response: Response, actor: Actor = Depends(get_actor)):
        response.headers["cache-control"] = "no-store"
        return request.app.state.services.learning.get_roadmap(actor, cid)

    @router.get("/{cid}/progress", response_model=CourseProgress)
    def progress(cid: str, request: Request, response: Response, actor: Actor = Depends(get_actor)):
        response.headers["cache-control"] = "no-store"
        return request.app.state.services.learning.get_progress(actor, cid)

    @router.put("/{cid}/progress/{node_id}", response_model=CourseProgress)
    def set_progress(cid: str, node_id: str, data: SetProgressRequest, request: Request,
                     response: Response, actor: Actor = Depends(get_actor)):
        response.headers["cache-control"] = "no-store"
        return request.app.state.services.learning.set_progress(actor, cid, node_id, data.learned)

    return router
