from pathlib import Path
from urllib.parse import urlsplit
from typing import Literal

from pydantic import AliasChoices, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class WebSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="WAYFINDER_", env_file=".env", env_ignore_empty=True,
                                      extra="ignore")

    version: str = "0.1.0"
    database_url: str | None = None
    test_database_url: str | None = None
    phase_b_lock_pool_size: int = Field(default=8, gt=0)
    frontend_dist: Path = Path("src/web/frontend/dist")
    allowed_origins: list[str] = Field(default_factory=list)
    public_base_url: str = "http://127.0.0.1:8000"
    session_idle_days: int = Field(default=7, gt=0)
    session_absolute_days: int = Field(default=30, gt=0)
    login_max_failures: int = Field(default=5, gt=0)
    login_failure_window_minutes: int = Field(default=15, gt=0)
    email_verify_ttl_hours: int = Field(default=24, gt=0)
    resend_verification_per_hour: int = Field(default=3, gt=0)
    password_reset_ttl_minutes: int = Field(default=60, gt=0)
    upload_max_mb: int = Field(default=10, gt=0)
    build_max_pages: int | None = Field(default=None, gt=0)
    scan_min_chars_per_page: int = Field(default=150, gt=0)
    scan_max_empty_page_ratio: float = Field(default=0.5, ge=0, le=1)
    vi_min_diacritic_ratio: float | None = Field(default=None, ge=0, le=1)
    build_monthly_max: int | None = Field(default=None, gt=0)
    system_daily_build_max_usd: float | None = Field(default=None, gt=0)
    env: Literal["dev", "prod"] = "dev"
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = Field(default=587, gt=0)
    smtp_username: str | None = None
    smtp_password: SecretStr | None = None
    smtp_from: str | None = None
    smtp_starttls: bool = True
    confirmation_ttl_hours: int = Field(default=72, gt=0)
    build_heartbeat_timeout_minutes: int = Field(default=10, gt=0)
    share_link_default_days: int = Field(default=7, gt=0)
    course_max_members: int = Field(default=200, gt=0)
    invite_batch_max: int = Field(default=50, gt=0)
    invite_ttl_days: int = Field(default=7, gt=0)
    invite_emails_per_day: int = Field(default=200, gt=0)
    assistant_turns_per_minute: int = Field(default=10, gt=0)
    documents_per_hour: int = Field(default=10, gt=0)
    mailer: Literal["console", "smtp"] = "console"
    artifact_root: Path = Field(default_factory=lambda: Path.home() / ".wayfinder" / "artifacts")
    cloudinary_url: SecretStr | None = Field(
        default=None, validation_alias=AliasChoices("CLOUDINARY_URL", "WAYFINDER_CLOUDINARY_URL")
    )
    cloudinary_folder: str | None = None
    signed_url_ttl_seconds: int = Field(default=300, gt=0)
    page_image_width: int = Field(default=1400, gt=0)

    @field_validator("public_base_url")
    @classmethod
    def validate_public_base_url(cls, value: str) -> str:
        parts = urlsplit(value)
        if (any(character.isspace() for character in value)
                or parts.scheme not in {"http", "https"} or not parts.hostname
                or parts.username is not None or parts.password is not None
                or parts.query or parts.fragment or parts.path not in {"", "/"}):
            raise ValueError("public_base_url must be an HTTP(S) origin without credentials or a path")
        _ = parts.port  # Reject malformed or out-of-range ports.
        return value.rstrip("/")

    @model_validator(mode="before")
    @classmethod
    def parse_optional_limits(cls, values):
        if not isinstance(values, dict):
            return values
        values = dict(values)
        for key in ("build_max_pages", "vi_min_diacritic_ratio", "build_monthly_max",
                    "system_daily_build_max_usd"):
            if isinstance(values.get(key), str) and values[key].strip().lower() in {"", "none", "null"}:
                values[key] = None
        env = values.get("env", "dev")
        if "mailer" not in values:
            values["mailer"] = "console" if env == "dev" else "smtp"
        if values.get("cloudinary_folder") is None:
            values["cloudinary_folder"] = f"wayfinder/{env}"
        return values
