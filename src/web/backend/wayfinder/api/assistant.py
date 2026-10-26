import asyncio
import json
import logging
from threading import Event
from typing import Literal

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from wayfinder.api.auth import get_actor
from wayfinder.api.lecture_models import Source, SourceDocument
from wayfinder.domain.auth import Actor


log = logging.getLogger(__name__)


class Scope(BaseModel):
    kind: Literal['roadmap', 'module']
    module_id: str | None = Field(default=None, max_length=128)
    # Deliberately ignored: graph membership is selected by the server.
    node_ids: list[str] | None = None


class NewSession(BaseModel):
    scope: Scope


class RenameSession(BaseModel):
    title: str = Field(min_length=1, max_length=60, pattern=r'\S')


class NewTurn(BaseModel):
    question: str = Field(min_length=1, max_length=4000, pattern=r'\S')
    client_turn_id: str = Field(min_length=1, max_length=128, pattern=r'^[a-zA-Z0-9_-]+$')
    focus_node_id: str | None = Field(default=None, max_length=256)


class Card(BaseModel):
    node_id: str | None = None
    name: str | None = None
    module_id: str | None = None
    module_index: int | None = None
    module_title: str | None = None
    title: str | None = None
    text: str | None = None
    label: str | None = None
    quote: str | None = None
    page: int | None = None
    learner_status: str | None = None


class Cards(BaseModel):
    scope_note: str | None = None
    module_cards: list[Card] = Field(default_factory=list)
    later_modules: list[Card] = Field(default_factory=list)
    reminders: list[Card] = Field(default_factory=list)
    roadmap: list[Card] = Field(default_factory=list)


class Artifact(BaseModel):
    kind: Literal['quiz', 'document', 'lecture']
    id: str
    title: str
    node_id: str | None = None
    module_id: str | None = None


class Failure(BaseModel):
    reason_code: str
    message: str
    retryable: bool


class Answer(BaseModel):
    contract_version: Literal['answer-3']
    answer_id: str
    course_id: str
    doc_id: str
    graph_version: int
    session_id: str
    client_turn_id: str | None
    status: Literal['answered', 'failed', 'daily_limit']
    answer_md: str
    sources: list[Source] = Field(default_factory=list)
    graph_cards: Cards
    artifacts: list[Artifact] = Field(default_factory=list)
    focus_node_id: str | None = None
    warnings: list[Literal['focus_ignored']] = Field(default_factory=list)
    failure: Failure | None = None


class Session(BaseModel):
    contract_version: Literal['session-1']
    session_id: str
    title: str
    scope: dict[str, str | None]
    created_at: str
    updated_at: str
    turn_count: int
    last_question_preview: str
    resolved_module_id: str | None = None
    module_label: str | None = None
    scope_note: str | None = None


class Sessions(BaseModel):
    course_id: str
    sessions: list[Session]
    source_document: SourceDocument | None = None


class Turn(BaseModel):
    contract_version: Literal['turn-1']
    turn_id: str
    client_turn_id: str | None
    question: str
    created_at: str
    answer: Answer


class Turns(BaseModel):
    course_id: str
    session_id: str
    turns: list[Turn]


class LibraryItem(BaseModel):
    kind: Literal['document', 'quiz_attempt']
    id: str
    title: str
    created_at: str | None = None
    origin: str | None = None
    group: str
    module_labels: list[str]
    label: str | None = None
    session_deleted: bool = False


class Library(BaseModel):
    contract_version: Literal['library-1']
    course_id: str
    doc_id: str
    scope_filter: str
    items: list[LibraryItem]


class QuizOption(BaseModel):
    option_id: str
    text: str


class QuizItem(BaseModel):
    item_id: str
    question: str
    options: list[QuizOption]


class ArtifactContent(Artifact):
    contract_version: Literal['document-3', 'quiz-3']
    markdown: str | None = None
    sources: list[Source] = Field(default_factory=list)
    items: list[QuizItem] = Field(default_factory=list)


def stream_payload(row):
    kind = row['event']
    if kind in {'final', 'failure'} and 'answer' in row:
        return {'answer': Answer.model_validate(row['answer']).model_dump(mode='json')}
    if kind == 'failure':
        return {'failure': Failure.model_validate(row['failure']).model_dump(mode='json')}
    if kind in {'progress', 'delta'}:
        return {'text': str(row.get('text', ''))}
    if kind == 'tool_call':
        from wayfinder.application.assistant_view import TOOL_LABELS
        name = row.get('name')
        return {'name': name if name in TOOL_LABELS else 'other',
            'text': TOOL_LABELS.get(name, 'Đang xử lý yêu cầu…'), 'state': 'running' if row.get('state') == 'running' else 'done'}
    if kind == 'artifact':
        return {'artifact': Artifact.model_validate(row['artifact']).model_dump(mode='json')}
    if kind == 'graph_card':
        return {'graph_cards': Cards.model_validate(row['graph_cards']).model_dump(mode='json')}
    return None


def assistant_router():
    def guard(cid: str, request: Request, actor: Actor = Depends(get_actor)):
        gateway = request.app.state.services.learning
        sid = request.path_params.get('sid')
        if sid:
            gateway._owned_session(actor, cid, sid)
        else:
            gateway.learner(actor, cid)
    router = APIRouter(prefix='/api/v1/courses/{cid}/sessions', tags=['assistant'], dependencies=[Depends(guard)])

    @router.get('', response_model=Sessions)
    def sessions(cid: str, request: Request, response: Response, filter: str = 'roadmap_page', actor: Actor = Depends(get_actor)):
        response.headers['cache-control'] = 'no-store'
        return request.app.state.services.learning.list_sessions(actor, cid, filter)

    @router.post('', response_model=Session, status_code=201)
    def create(cid: str, data: NewSession, request: Request, actor: Actor = Depends(get_actor)):
        return request.app.state.services.learning.create_session(actor, cid, data.scope.model_dump())

    @router.patch('/{sid}', response_model=Session)
    def rename(cid: str, sid: str, data: RenameSession, request: Request, actor: Actor = Depends(get_actor)):
        return request.app.state.services.learning.rename_session(actor, cid, sid, data.title)

    @router.delete('/{sid}')
    def delete(cid: str, sid: str, request: Request, actor: Actor = Depends(get_actor)):
        return request.app.state.services.learning.delete_session(actor, cid, sid)

    @router.get('/{sid}/turns', response_model=Turns)
    def turns(cid: str, sid: str, request: Request, response: Response, actor: Actor = Depends(get_actor)):
        response.headers['cache-control'] = 'no-store'
        return request.app.state.services.learning.list_turns(actor, cid, sid)

    @router.get('/{sid}/artifacts/{kind}/{aid}', response_model=ArtifactContent)
    def artifact(cid: str, sid: str, kind: str, aid: str, request: Request, response: Response, actor: Actor = Depends(get_actor)):
        response.headers['cache-control'] = 'no-store'
        return request.app.state.services.learning.get_assistant_artifact(actor, cid, sid, kind, aid)

    @router.post('/{sid}/turns')
    async def ask(cid: str, sid: str, data: NewTurn, request: Request, actor: Actor = Depends(get_actor)):
        gateway = request.app.state.services.learning
        await run_in_threadpool(gateway.prepare_turn, actor, cid, sid, data.client_turn_id, data.question, data.focus_node_id)
        loop, queue, disconnected = asyncio.get_running_loop(), asyncio.Queue(), Event()

        def emit(row):
            if not disconnected.is_set():
                loop.call_soon_threadsafe(queue.put_nowait, row)

        def produce():
            try:
                gateway.ask_stream(actor, cid, sid, data.client_turn_id, data.question, emit, data.focus_node_id)
            except Exception:
                log.exception('Assistant turn failed course=%s session=%s', cid, sid)
                emit({'event': 'failure', 'failure': {'reason_code': 'loi_mang',
                    'message': 'Kết nối bị gián đoạn. Bạn có thể mở lại phiên hoặc thử lại câu hỏi.', 'retryable': True}})
            finally:
                emit(None)

        async def stream():
            future = loop.run_in_executor(None, produce)
            try:
                while True:
                    try:
                        row = await asyncio.wait_for(queue.get(), timeout=15)
                    except TimeoutError:
                        yield ': keep-alive\n\n'
                        continue
                    if row is None:
                        break
                    payload = stream_payload(row)
                    if payload is None:
                        continue
                    yield f'event: {row["event"]}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n'
            finally:
                disconnected.set()
                future.add_done_callback(lambda done: done.exception() if not done.cancelled() else None)

        return StreamingResponse(stream(), media_type='text/event-stream', headers={'cache-control': 'no-store', 'x-accel-buffering': 'no'})

    return router


def assistant_library_router():
    # Read-only inventory is needed to prove W09 deletion keeps saved artifacts.
    # Generation, submission and the library screen remain W10.
    router = APIRouter(tags=['assistant'])

    @router.get('/api/v1/courses/{cid}/library', response_model=Library)
    def library(cid: str, request: Request, response: Response, scope: str = 'all', actor: Actor = Depends(get_actor)):
        response.headers['cache-control'] = 'no-store'
        return request.app.state.services.learning.list_library(actor, cid, scope)

    return router
