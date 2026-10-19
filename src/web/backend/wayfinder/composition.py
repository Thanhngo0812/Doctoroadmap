from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from doc2roadmap.config import Settings
from doc2roadmap.infrastructure.embedding.gemini import GeminiEmbedding
from doc2roadmap.infrastructure.llm.phase_b import GeminiToolModel
from google.auth import default as google_auth_default

from wayfinder.application.accounts import AccountService, AuthPolicy
from wayfinder.settings import WebSettings


HealthStatus = Literal["ok", "down"]


@dataclass(slots=True)
class WebServices:
    health_check: Callable[[], HealthStatus]
    close: Callable[[], None] = lambda: None
    model: object | None = None
    embedding: object | None = None
    accounts: AccountService | None = None


def validate_vertex_auth(project: str, location: str) -> None:
    if not project or not location:
        raise ValueError("Vertex project and location are required")
    google_auth_default(scopes=["https://www.googleapis.com/auth/cloud-platform"])


def compose_services(
    settings: WebSettings,
    *,
    health_check: Callable[[], HealthStatus] | None = None,
    close: Callable[[], None] | None = None,
    core_settings: Settings | None = None,
    auth_validator: Callable[[str, str], None] = validate_vertex_auth,
    model_factory: Callable[..., object] = GeminiToolModel,
    embedding_factory: Callable[..., object] = GeminiEmbedding,
) -> WebServices:
    core = core_settings or Settings(artifact_dir=settings.artifact_root)
    if core.llm_transport != "vertex":
        raise ValueError("WayFinder web requires DOC2ROADMAP_LLM_TRANSPORT=vertex")
    if not core.vertex_project:
        raise ValueError("missing DOC2ROADMAP_VERTEX_PROJECT")
    if not core.vertex_location:
        raise ValueError("missing DOC2ROADMAP_VERTEX_LOCATION")

    auth_validator(core.vertex_project, core.vertex_location)
    if health_check is None:
        if settings.database_url is None:
            raise ValueError("missing WAYFINDER_DATABASE_URL")
        from wayfinder.infrastructure.database import DatabaseHealth
        database_health = DatabaseHealth(settings.database_url)
        health_check = database_health
        close = database_health.close
    api_key = core.gemini_api_key.get_secret_value() if core.gemini_api_key else None
    model = model_factory(api_key, core.roadmap_model_id, transport="vertex",
                          vertex_project=core.vertex_project, vertex_location=core.vertex_location,
                          timeout_seconds=core.gemini_timeout_seconds)
    embedding = embedding_factory(api_key, model=core.embedding_model_id,
                                  output_dimensionality=core.embedding_dimensions,
                                  timeout=core.gemini_timeout_seconds, max_retries=core.gemini_max_retries,
                                  transport="vertex", vertex_project=core.vertex_project,
                                  vertex_location=core.vertex_location)
    accounts = None
    if settings.database_url:
        from wayfinder.infrastructure.database import create_database_engine
        engine = getattr(health_check, "engine", None)
        if engine is None:
            engine = create_database_engine(settings.database_url)
            previous_close = close or (lambda: None)

            def close_accounts():
                try:
                    previous_close()
                finally:
                    engine.dispose()

            close = close_accounts
        accounts = compose_account_service(settings, engine)
    return WebServices(health_check=health_check, close=close or (lambda: None), model=model,
                       embedding=embedding, accounts=accounts)


def compose_account_service(settings: WebSettings, engine) -> AccountService:
    from doc2roadmap.application.phase_b.clock import SystemClock
    from wayfinder.infrastructure.auth_store import PostgresAuthStore
    from wayfinder.infrastructure.passwords import Argon2PasswordHasher, load_common_passwords

    policy = AuthPolicy(settings.session_idle_days, settings.session_absolute_days,
                        settings.login_max_failures, settings.login_failure_window_minutes)
    return AccountService(PostgresAuthStore(engine), Argon2PasswordHasher(), SystemClock(), policy,
                          load_common_passwords())
