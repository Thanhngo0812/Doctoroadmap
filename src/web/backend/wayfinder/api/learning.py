import asyncio
import json
import logging
from threading import Event

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse, StreamingResponse
from starlette.concurrency import run_in_threadpool

from wayfinder.api.auth import get_actor
from wayfinder.api.errors import WebError
from wayfinder.api.lecture_models import LectureView
from wayfinder.domain.auth import Actor


logger = logging.getLogger(__name__)


def learning_router():
    router = APIRouter(prefix='/api/v1/courses', tags=['learning'])

    @router.get('/{cid}/concepts/{node_id}/lecture', response_model=LectureView)
    def lecture(cid: str, node_id: str, request: Request, response: Response, actor: Actor = Depends(get_actor)):
        response.headers['cache-control'] = 'no-store'
        return request.app.state.services.learning.get_lecture(actor, cid, node_id)

    @router.get('/{cid}/concepts/{node_id}/lecture/stream')
    async def stream(cid: str, node_id: str, request: Request, actor: Actor = Depends(get_actor)):
        gateway = request.app.state.services.learning
        # Authorize before committing HTTP 200/SSE headers, including for malformed node IDs.
        await run_in_threadpool(gateway.lecture_context, actor, cid, node_id)
        origin = request.headers.get('origin')
        if (request.headers.get('sec-fetch-site') == 'cross-site'
                or origin and origin not in request.app.state.settings.allowed_origins):
            raise WebError('csrf_failed', 'Yêu cầu không hợp lệ')
        loop = asyncio.get_running_loop()
        queue = asyncio.Queue()
        disconnected = Event()
        seen = {'lecture': None, 'body': ''}

        def emit(event):
            if event and event.get('lecture'):
                seen['lecture'] = event['lecture']
            if event and event.get('event') == 'delta':
                seen['body'] += event['text']
            if not disconnected.is_set():
                loop.call_soon_threadsafe(queue.put_nowait, event)

        def produce():
            try:
                gateway.stream_lecture(actor, cid, node_id, emit)
            except Exception:
                logger.exception('Lecture stream failed course=%s node=%s', cid, node_id)
                if seen['body'].strip() and seen['lecture']:
                    emit({'event': 'final', 'lecture': {**seen['lecture'], 'status': 'ready',
                        'body_md': seen['body'], 'failure': None,
                        'warnings': list(dict.fromkeys([*seen['lecture'].get('warnings', []), 'cat_ngan']))}})
                else:
                    emit({'event': 'failure', 'failure': {'reason_code': 'loi_mang',
                        'message': 'Chưa thể soạn bài. Hãy kiểm tra kết nối rồi thử lại.', 'retryable': True}})
            finally:
                emit(None)

        async def events():
            # Executor work deliberately outlives an SSE disconnect and completes the shared cache.
            future = loop.run_in_executor(None, produce)
            try:
                while True:
                    try:
                        event = await asyncio.wait_for(queue.get(), timeout=15)
                    except TimeoutError:
                        yield ': keep-alive\n\n'
                        continue
                    if event is None:
                        break
                    payload = {key: value for key, value in event.items() if key != 'event'}
                    if payload.get('lecture'):
                        payload['lecture'] = LectureView.model_validate(payload['lecture']).model_dump(mode='json')
                    yield f'event: {event["event"]}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n'
            finally:
                disconnected.set()
                # Retrieving an exception does not cancel a producer that still owns cache generation.
                future.add_done_callback(lambda done: done.exception() if not done.cancelled() else None)

        return StreamingResponse(events(), media_type='text/event-stream',
            headers={'cache-control': 'no-store', 'x-accel-buffering': 'no'})

    @router.get('/{cid}/source/pages/{page}')
    def source_page(cid: str, page: str, request: Request, actor: Actor = Depends(get_actor)):
        content, count = request.app.state.services.learning.open_source_page(actor, cid, page)
        return Response(content, media_type='image/webp',
            headers={'cache-control': 'private, max-age=300', 'x-page-count': str(count)})

    @router.get('/{cid}/source')
    def source(cid: str, request: Request, actor: Actor = Depends(get_actor)):
        url = request.app.state.services.learning.open_source_file(actor, cid)
        return RedirectResponse(url, status_code=302, headers={'cache-control': 'no-store', 'referrer-policy': 'no-referrer'})

    @router.get('/{cid}/media/{asset_key:path}')
    def media(cid: str, asset_key: str, request: Request, actor: Actor = Depends(get_actor)):
        content = request.app.state.services.learning.get_media(actor, cid, asset_key)
        return Response(content, media_type='image/webp', headers={'cache-control': 'private, max-age=300'})

    return router
