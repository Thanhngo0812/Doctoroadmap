from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from fastapi.responses import FileResponse, JSONResponse
from starlette.exceptions import HTTPException

from wayfinder import __version__
from wayfinder.api.auth import auth_router, enforce_csrf
from wayfinder.application.accounts import AuthError
from wayfinder.api.errors import ERROR_STATUS, ErrorCode, WebError
from wayfinder.composition import WebServices
from wayfinder.settings import WebSettings


logger = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    version: str
    db: Literal["ok", "down"]


def _error(code: str, message: str, *, retry_after: int | None = None,
           ref: str | None = None, fields: Any = None) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message, "retry_after": retry_after, "ref": ref}
    if fields is not None:
        error["fields"] = fields
    return {"error": error}


def create_app(settings: WebSettings, services: WebServices) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI):
        try:
            yield
        finally:
            services.close()

    app = FastAPI(title="WayFinder API", version=settings.version or __version__, lifespan=lifespan,
                  docs_url=None, redoc_url=None)

    app.state.services = services
    app.state.settings = settings
    app.include_router(auth_router())

    @app.exception_handler(AuthError)
    async def account_error(_: Request, exc: AuthError) -> JSONResponse:
        headers = {"cache-control": "no-store"}
        if exc.retry_after is not None:
            headers["retry-after"] = str(exc.retry_after)
        return JSONResponse(_error(exc.code, exc.message, retry_after=exc.retry_after, fields=exc.fields),
                            status_code=ERROR_STATUS[exc.code], headers=headers)

    @app.exception_handler(HTTPException)
    async def http_error(_: Request, exc: HTTPException) -> JSONResponse:
        codes: dict[int, ErrorCode] = {
            400: "validation", 401: "unauthenticated", 403: "forbidden", 404: "not_found",
            405: "validation", 409: "conflict", 410: "link_invalid", 413: "file_too_large",
            422: "validation", 429: "rate_limited",
        }
        code = codes.get(exc.status_code, "internal_error")
        message = "Không tìm thấy nội dung yêu cầu" if code == "not_found" else "Yêu cầu không thể thực hiện"
        ref = uuid4().hex if code == "internal_error" else None
        return JSONResponse(_error(code, message, ref=ref), status_code=exc.status_code, headers=exc.headers)

    @app.exception_handler(WebError)
    async def web_error(_: Request, exc: WebError) -> JSONResponse:
        ref = exc.ref or (uuid4().hex if exc.code == "internal_error" else None)
        return JSONResponse(_error(exc.code, exc.message, retry_after=exc.retry_after,
                                   ref=ref, fields=exc.fields), status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        fields = [{"loc": ".".join(str(part) for part in error["loc"]),
                   "type": str(error["type"]), "message": str(error["msg"])} for error in exc.errors()]
        return JSONResponse(_error("validation", "Dữ liệu yêu cầu không hợp lệ", fields=fields), status_code=422)

    @app.get("/api/v1/health", response_model=HealthResponse, responses={503: {"model": HealthResponse}}, tags=["system"])
    def health() -> JSONResponse:
        try:
            db: str = services.health_check()
        except Exception:
            logger.exception("Database health check failed")
            db = "down"
        database = "ok" if db == "ok" else "down"
        return JSONResponse(
            {"status": "ok" if database == "ok" else "degraded",
             "version": settings.version or __version__, "db": database},
            status_code=200 if database == "ok" else 503,
        )

    if settings.frontend_dist.is_dir():
        root = settings.frontend_dist.resolve()

        @app.get("/{path:path}", include_in_schema=False)
        async def spa(path: str) -> FileResponse:
            if path == "api" or path.startswith("api/"):
                raise HTTPException(status_code=404, detail="not found")
            requested = (root / path).resolve()
            if root in requested.parents and requested.is_file():
                return FileResponse(requested)
            index = root / "index.html"
            if index.is_file():
                return FileResponse(index)
            raise HTTPException(status_code=404, detail="not found")

    @app.middleware("http")
    async def security_and_internal_errors(request: Request, call_next):
        try:
            await enforce_csrf(request)
            response = await call_next(request)
        except AuthError as exc:
            response = await account_error(request, exc)
        except WebError as exc:
            response = await web_error(request, exc)
        except Exception as exc:
            ref = uuid4().hex
            logger.exception("Unhandled request error ref=%s", ref, exc_info=exc)
            response = JSONResponse(_error("internal_error", "Đã xảy ra lỗi máy chủ", ref=ref), status_code=500)
        response.headers["content-security-policy"] = (
            "default-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'self'; img-src 'self' data: blob:; "
            "style-src 'self' https://fonts.googleapis.com; style-src-elem 'self' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com data:"
        )
        response.headers["x-content-type-options"] = "nosniff"
        recovery_page = request.url.path in {"/xac-minh", "/quen-mat-khau", "/dat-lai-mat-khau"}
        recovery_api = request.url.path.startswith("/api/v1/auth/password-reset/") or request.url.path in {
            "/api/v1/auth/verify-email", "/api/v1/auth/resend-verification"}
        response.headers["referrer-policy"] = "no-referrer" if recovery_page or recovery_api else "same-origin"
        if recovery_page or recovery_api:
            response.headers["cache-control"] = "no-store"
        return response

    return app
