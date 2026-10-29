from typing import Literal


ErrorCode = Literal[
    "unauthenticated", "invalid_credentials", "account_disabled", "email_unverified", "forbidden",
    "csrf_failed", "not_found", "conflict", "validation", "file_invalid", "file_too_large",
    "too_many_pages", "file_encrypted", "link_invalid", "course_full", "rate_limited",
    "quota_exceeded", "owns_shared_courses", "internal_error", "confirmation_expired", "scope_too_large",
    "protected_admin", "bootstrap_required",
]

ERROR_STATUS: dict[ErrorCode, int] = {
    "unauthenticated": 401, "invalid_credentials": 401,
    "account_disabled": 403, "email_unverified": 403, "forbidden": 403, "csrf_failed": 403,
    "not_found": 404, "conflict": 409, "course_full": 409, "owns_shared_courses": 409,
    "link_invalid": 410, "validation": 422, "file_invalid": 422, "file_too_large": 422,
    "too_many_pages": 422, "file_encrypted": 422, "rate_limited": 429, "quota_exceeded": 429,
    "internal_error": 500, "confirmation_expired": 410, "scope_too_large": 422,
    "protected_admin": 409, "bootstrap_required": 409,
}


class WebError(Exception):
    def __init__(self, code: ErrorCode, message: str, *, retry_after: int | None = None,
                 fields: list[dict[str, str]] | None = None, ref: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = ERROR_STATUS[code]
        self.message = message
        self.retry_after = retry_after
        self.fields = fields
        self.ref = ref
