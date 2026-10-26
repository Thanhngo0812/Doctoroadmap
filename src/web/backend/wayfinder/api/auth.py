"""Cookie authentication boundary; the application never sees HTTP objects."""
from ipaddress import ip_address
import secrets
from typing import Literal

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator
from starlette.concurrency import run_in_threadpool

from wayfinder.api.errors import WebError
from wayfinder.application.accounts import AccountService, SessionIdentity
from wayfinder.domain.auth import Actor


COOKIE_NAME = "d2r_session"
REGISTER_MESSAGE = "Yêu cầu đăng ký đã được tiếp nhận. Bạn có thể đăng nhập để tiếp tục."
PREAUTH_ROUTES = frozenset({"/api/v1/auth/register", "/api/v1/auth/login"})
PUBLIC_TOKEN_ROUTES = frozenset({
    "/api/v1/auth/verify-email", "/api/v1/auth/password-reset/request",
    "/api/v1/auth/password-reset/confirm",
})


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(max_length=254)
    password: SecretStr = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=60)


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(max_length=254)
    password: SecretStr = Field(max_length=128)


class VerifyEmailRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=1, max_length=256)


class ResendVerificationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PasswordResetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(max_length=254)


class PasswordResetConfirmRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=1, max_length=256)
    password: SecretStr = Field(min_length=8, max_length=128)


class ProfileRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    display_name: str = Field(min_length=1, max_length=60)

    @field_validator("display_name", mode="before")
    @classmethod
    def trim_display_name(cls, value):
        return value.strip() if isinstance(value, str) else value


class PasswordChangeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    current_password: SecretStr = Field(max_length=128)
    new_password: SecretStr = Field(min_length=8, max_length=128)


class LogoutAllRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AccountResponse(BaseModel):
    id: str
    email: str
    display_name: str
    role: Literal["user", "admin"]
    email_verified: bool


class IdentityResponse(BaseModel):
    account: AccountResponse
    csrf_token: str


class MessageResponse(BaseModel):
    message: str


def _service(request: Request) -> AccountService:
    service = request.app.state.services.accounts
    if service is None:
        raise WebError("internal_error", "Dịch vụ tài khoản chưa sẵn sàng.")
    return service


def client_ip(request: Request) -> str | None:
    # Do not trust caller-supplied forwarding headers for abuse limits.
    try:
        return str(ip_address(request.client.host)) if request.client else None
    except ValueError:
        return None


def _identity_response(identity) -> dict:
    account = identity.account
    return {"account": {"id": account.id, "email": account.email,
                        "display_name": account.display_name, "role": account.role,
                        "email_verified": account.email_verified_at is not None},
            "csrf_token": identity.session.csrf_token}


def _secure_cookie(request: Request) -> bool:
    return request.url.scheme == "https" or request.app.state.settings.env == "prod"


def _set_session_cookie(response: Response, request: Request, token: str) -> None:
    response.set_cookie(COOKIE_NAME, token, max_age=request.app.state.settings.session_absolute_days * 86400,
                        path="/", secure=_secure_cookie(request), httponly=True, samesite="lax")


def get_identity(request: Request) -> SessionIdentity:
    identity = getattr(request.state, "identity", None)
    if identity is None:
        identity = _service(request).me(request.cookies.get(COOKIE_NAME))
        request.state.identity = identity
    return identity


def get_actor(request: Request) -> Actor:
    identity = get_identity(request)
    account = identity.account
    return Actor(account.id, account.role, account.email_verified_at is not None, account.status)


async def enforce_csrf(request: Request) -> None:
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return
    origin = request.headers.get("origin")
    settings = request.app.state.settings
    allowed = settings.allowed_origins
    if not allowed:
        host = request.url.hostname
        try:
            local = host == "localhost" or ip_address(host).is_loopback
        except ValueError:
            local = False
        allowed = [f"{request.url.scheme}://{request.url.netloc}"] if local else []
    if not origin or origin == "null" or origin not in allowed:
        raise WebError("csrf_failed", "Yêu cầu không hợp lệ. Vui lòng tải lại trang và thử lại.")
    if request.url.path in PREAUTH_ROUTES | PUBLIC_TOKEN_ROUTES and request.method == "POST":
        return
    token = request.headers.get("x-csrf-token")
    if not token or not request.cookies.get(COOKIE_NAME):
        raise WebError("csrf_failed", "Yêu cầu không hợp lệ. Vui lòng tải lại trang và thử lại.")
    identity = await run_in_threadpool(_service(request).me, request.cookies.get(COOKIE_NAME))
    if not secrets.compare_digest(token.encode("utf-8"), identity.session.csrf_token.encode("utf-8")):
        raise WebError("csrf_failed", "Yêu cầu không hợp lệ. Vui lòng tải lại trang và thử lại.")
    request.state.identity = identity


def auth_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["accounts"])

    @router.post("/auth/register", response_model=MessageResponse)
    def register(data: RegisterRequest, request: Request, response: Response):
        result = _service(request).register(data.email, data.password.get_secret_value(), data.display_name,
                                            ip=client_ip(request), user_agent=request.headers.get("user-agent"))
        if result.session is not None:
            _set_session_cookie(response, request, result.session.token)
        response.headers["cache-control"] = "no-store"
        return {"message": REGISTER_MESSAGE}

    @router.post("/auth/login", response_model=IdentityResponse)
    def login(data: LoginRequest, request: Request, response: Response):
        grant = _service(request).login(data.email, data.password.get_secret_value(), ip=client_ip(request),
                                        user_agent=request.headers.get("user-agent"))
        _set_session_cookie(response, request, grant.token)
        response.headers["cache-control"] = "no-store"
        return _identity_response(grant)

    @router.post("/auth/verify-email", response_model=MessageResponse)
    def verify_email(data: VerifyEmailRequest, request: Request, response: Response):
        _service(request).verify_email(data.token, ip=client_ip(request))
        response.headers["cache-control"] = "no-store"
        return {"message": "Email đã được xác minh."}

    @router.post("/auth/resend-verification", response_model=MessageResponse)
    def resend_verification(request: Request, response: Response):
        account_id = get_identity(request).account.id
        message = _service(request).resend_verification(account_id, ip=client_ip(request))
        response.headers["cache-control"] = "no-store"
        return {"message": message}

    @router.post("/auth/password-reset/request", response_model=MessageResponse)
    def request_password_reset(data: PasswordResetRequest, request: Request, response: Response):
        message = _service(request).request_password_reset(data.email, ip=client_ip(request))
        response.headers["cache-control"] = "no-store"
        return {"message": message}

    @router.post("/auth/password-reset/confirm", response_model=MessageResponse)
    def confirm_password_reset(data: PasswordResetConfirmRequest, request: Request, response: Response):
        _service(request).reset_password(data.token, data.password.get_secret_value(), ip=client_ip(request))
        response.delete_cookie(COOKIE_NAME, path="/", secure=_secure_cookie(request),
                               httponly=True, samesite="lax")
        response.headers["cache-control"] = "no-store"
        return {"message": "Đã đặt lại mật khẩu. Hãy đăng nhập bằng mật khẩu mới."}

    @router.get("/me", response_model=IdentityResponse)
    def me(request: Request, response: Response):
        response.headers["cache-control"] = "no-store"
        return _identity_response(get_identity(request))

    @router.patch("/me", response_model=IdentityResponse)
    def update_profile(data: ProfileRequest, request: Request, response: Response):
        identity = _service(request).update_profile(request.cookies.get(COOKIE_NAME), data.display_name)
        response.headers["cache-control"] = "no-store"
        return _identity_response(identity)

    @router.post("/me/password", response_model=MessageResponse)
    def change_password(data: PasswordChangeRequest, request: Request, response: Response):
        _service(request).change_password(request.cookies.get(COOKIE_NAME), data.current_password.get_secret_value(),
                                          data.new_password.get_secret_value(), ip=client_ip(request))
        response.headers["cache-control"] = "no-store"
        return {"message": "Đã đổi mật khẩu. Các phiên đăng nhập khác đã được đăng xuất."}

    @router.post("/auth/logout-all", response_model=MessageResponse)
    def logout_all(request: Request, response: Response, data: LogoutAllRequest | None = None):
        _service(request).logout_all(request.cookies.get(COOKIE_NAME), ip=client_ip(request))
        response.delete_cookie(COOKIE_NAME, path="/", secure=_secure_cookie(request),
                               httponly=True, samesite="lax")
        response.headers["cache-control"] = "no-store"
        return {"message": "Đã đăng xuất khỏi mọi thiết bị."}

    @router.post("/auth/logout", response_model=MessageResponse)
    def logout(request: Request, response: Response):
        _service(request).logout(request.cookies.get(COOKIE_NAME), ip=client_ip(request))
        response.delete_cookie(COOKIE_NAME, path="/", secure=_secure_cookie(request),
                               httponly=True, samesite="lax")
        response.headers["cache-control"] = "no-store"
        return {"message": "Đã đăng xuất."}

    return router
