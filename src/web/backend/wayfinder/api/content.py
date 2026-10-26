"""W10 HTTP and SSE: permission checks precede headers and provider work."""
import asyncio
import json
import logging
from threading import Event
from typing import Literal

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import PlainTextResponse, StreamingResponse
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from wayfinder.api.auth import get_actor
from wayfinder.api.assistant import Failure, Scope
from wayfinder.api.lecture_models import Source, SourceDocument
from wayfinder.domain.auth import Actor


log = logging.getLogger(__name__)


class NewQuiz(BaseModel):
    scope: Scope
    n: int | None = Field(default=None, ge=1, le=10)


class SubmitQuiz(BaseModel):
    answers: dict[str, str] = Field(default_factory=dict, max_length=1000)


class NewDocument(BaseModel):
    request: str = Field(default='', max_length=4000)
    module_ids: list[str] = Field(min_length=1, max_length=100)
    home_module_id: str | None = Field(default=None, max_length=128)


class Option(BaseModel):
    option_id: str
    text: str


class Item(BaseModel):
    item_id: str
    concept_id: str
    module_id: str | None = None
    generator: Literal['llm', 'cloze']
    bloom: str | None = None
    stem: str
    options: list[Option]


class Quiz(BaseModel):
    contract_version: Literal['quiz-3']
    course_id: str
    attempt_id: str
    status: Literal['ready', 'failed']
    created_at: str
    module_id: str | None = None
    ready_count: int
    total_concepts: int
    items: list[Item]
    submitted: bool = False
    source_document: SourceDocument | None = None


class CorrectOption(BaseModel):
    text: str


class GradedItem(BaseModel):
    item_id: str
    concept_id: str
    stem: str
    selected_option_id: str | None = None
    is_correct: bool
    correct_option: CorrectOption
    explanation: str
    why_wrong: str | None = None
    evidence: list[Source] = Field(default_factory=list)


class Result(BaseModel):
    contract_version: Literal['quiz-3']
    attempt_id: str
    correct_count: int
    question_count: int
    submitted_at: str
    results: list[GradedItem]


class Document(BaseModel):
    contract_version: Literal['document-3']
    course_id: str
    document_id: str
    title: str
    request: str
    markdown: str
    status: Literal['ready', 'failed']
    created_at: str
    sources: list[Source] = Field(default_factory=list)
    warnings: list[Literal['cat_ngan']] = Field(default_factory=list)
    failure: Failure | None = None
    source_document: SourceDocument | None = None


def public_event(row):
    kind = row['event']
    if kind in {'final', 'failure'}:
        if 'quiz' in row:
            return {'quiz': Quiz.model_validate(row['quiz']).model_dump(mode='json')}
        if 'document' in row:
            return {'document': Document.model_validate(row['document']).model_dump(mode='json')}
        return {'failure': Failure.model_validate(row['failure']).model_dump(mode='json')}
    if kind == 'item_ready':
        return {'attempt_id': str(row['attempt_id']), 'item': Item.model_validate(row['item']).model_dump(mode='json')}
    if kind == 'delta':
        return {'text': str(row['text'])}
    if kind == 'skeleton':
        return {'document_id': str(row['document_id']), 'title': None}
    return None


def stream_content(producer):
    loop, queue, disconnected = asyncio.get_running_loop(), asyncio.Queue(), Event()

    def emit(row):
        if not disconnected.is_set():
            loop.call_soon_threadsafe(queue.put_nowait, row)

    def produce():
        try:
            producer(emit)
        except Exception:
            log.exception('Content stream failed')
            emit({'event': 'failure', 'failure': {'reason_code': 'loi_mang',
                'message': 'Chưa thể hoàn tất nội dung. Hãy thử lại.', 'retryable': True}})
        finally:
            emit(None)

    async def events():
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
                payload = public_event(row)
                if payload is not None:
                    yield f'event: {row["event"]}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n'
        finally:
            disconnected.set()
            future.add_done_callback(lambda done: done.exception() if not done.cancelled() else None)
    return StreamingResponse(events(), media_type='text/event-stream',
        headers={'cache-control': 'no-store', 'x-accel-buffering': 'no'})


def content_router():
    def guard(cid: str, request: Request, actor: Actor = Depends(get_actor)):
        request.app.state.services.learning.learner(actor, cid)
    router = APIRouter(prefix='/api/v1/courses/{cid}', tags=['content'], dependencies=[Depends(guard)])

    @router.post('/quizzes', response_model=Quiz, status_code=201)
    async def make_quiz(cid: str, data: NewQuiz, request: Request, response: Response, actor: Actor = Depends(get_actor)):
        gateway = request.app.state.services.learning
        scope = data.scope.model_dump()
        await run_in_threadpool(gateway.prepare_quiz, actor, cid, scope)
        if 'text/event-stream' in request.headers.get('accept', ''):
            return stream_content(lambda emit: gateway.make_quiz(actor, cid, scope, data.n, emit))
        response.headers['cache-control'] = 'no-store'
        return await run_in_threadpool(gateway.make_quiz, actor, cid, scope, data.n)

    @router.get('/quizzes/{aid}', response_model=Quiz)
    def quiz(cid: str, aid: str, request: Request, response: Response, actor: Actor = Depends(get_actor)):
        response.headers['cache-control'] = 'no-store'
        return request.app.state.services.learning.get_quiz(actor, cid, aid)

    @router.post('/quizzes/{aid}/submit', response_model=Result)
    def submit(cid: str, aid: str, data: SubmitQuiz, request: Request, response: Response, actor: Actor = Depends(get_actor)):
        response.headers['cache-control'] = 'no-store'
        return request.app.state.services.learning.submit_quiz(actor, cid, aid, data.answers)

    @router.get('/quizzes/{aid}/result', response_model=Result)
    def result(cid: str, aid: str, request: Request, response: Response, actor: Actor = Depends(get_actor)):
        response.headers['cache-control'] = 'no-store'
        return request.app.state.services.learning.get_quiz_result(actor, cid, aid)

    @router.post('/documents', response_model=Document, status_code=201)
    async def make_document(cid: str, data: NewDocument, request: Request, response: Response, actor: Actor = Depends(get_actor)):
        gateway = request.app.state.services.learning
        await run_in_threadpool(gateway.prepare_document, actor, cid, data.module_ids, data.home_module_id)
        # Admission must fail before HTTP 200/SSE headers, even for the eleventh request.
        await run_in_threadpool(gateway.admit_document, actor)
        if 'text/event-stream' in request.headers.get('accept', ''):
            return stream_content(lambda emit: gateway.make_document(actor, cid, data.request, data.module_ids, data.home_module_id, emit))
        response.headers['cache-control'] = 'no-store'
        return await run_in_threadpool(gateway.make_document, actor, cid, data.request, data.module_ids, data.home_module_id)

    @router.get('/documents/{did}', response_model=Document)
    def document(cid: str, did: str, request: Request, response: Response, actor: Actor = Depends(get_actor)):
        response.headers['cache-control'] = 'no-store'
        return request.app.state.services.learning.get_document(actor, cid, did)

    @router.get('/documents/{did}/markdown')
    def markdown(cid: str, did: str, request: Request, actor: Actor = Depends(get_actor)):
        return PlainTextResponse(request.app.state.services.learning.export_document(actor, cid, did),
            media_type='text/markdown', headers={'cache-control': 'no-store',
                'content-disposition': 'attachment; filename="wayfinder-document.md"'})
    return router
