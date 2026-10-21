from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from doc2roadmap.config import Settings
from doc2roadmap.application.ports.phase_b import PhaseBStore
from doc2roadmap.domain.phase_b_limits import BSettings
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
    phase_b_store: PhaseBStore | None = None
    courses: object | None = None
    learning: object | None = None


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
    phase_b_store: PhaseBStore | None = None,
    graph_loader: Callable | None = None,
    clock=None,
) -> WebServices:
    core = core_settings or Settings(artifact_dir=settings.artifact_root)
    if core.llm_transport != "vertex":
        raise ValueError("WayFinder web requires DOC2ROADMAP_LLM_TRANSPORT=vertex")
    if not core.vertex_project:
        raise ValueError("missing DOC2ROADMAP_VERTEX_PROJECT")
    if not core.vertex_location:
        raise ValueError("missing DOC2ROADMAP_VERTEX_LOCATION")

    auth_validator(core.vertex_project, core.vertex_location)
    database_engine = None
    if health_check is None:
        if settings.database_url is None:
            raise ValueError("missing WAYFINDER_DATABASE_URL")
        from wayfinder.infrastructure.database import DatabaseHealth
        database_health = DatabaseHealth(settings.database_url)
        database_engine = database_health.engine
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
    created_engine = None
    database_engine = database_engine or getattr(health_check, "engine", None)
    if database_engine is None and settings.database_url is not None:
        from wayfinder.infrastructure.database import create_database_engine
        created_engine = create_database_engine(settings.database_url)
        database_engine = created_engine
    created_store = None
    if phase_b_store is None and database_engine is not None:
        from wayfinder.infrastructure.phase_b_store import PostgresPhaseBStore
        created_store = PostgresPhaseBStore(database_engine,
            lock_pool_size=settings.phase_b_lock_pool_size,
            lock_timeout_seconds=BSettings().lecture_click_timeout_seconds)
        phase_b_store = created_store
    accounts = compose_account_service(settings, database_engine) if database_engine is not None else None
    courses = learning = None
    if database_engine is not None:
        courses, learning = compose_course_services(settings, database_engine, phase_b_store,
            model=model, embedding=embedding, graph_loader=graph_loader, clock=clock)

    def close_services():
        try:
            close_mailer = getattr(getattr(accounts, "mailer", None), "close", None)
            if close_mailer is not None:
                close_mailer()
        finally:
            try:
                if created_store is not None:
                    created_store.close()
                elif created_engine is not None:
                    created_engine.dispose()
            finally:
                if close is not None:
                    close()

    return WebServices(health_check=health_check, close=close_services, model=model,
                       embedding=embedding, accounts=accounts, phase_b_store=phase_b_store,
                       courses=courses, learning=learning)


def compose_course_services(settings, engine, phase_b_store, *, model=None, embedding=None,
                            clock=None, graph_loader=None):
    from doc2roadmap.application.phase_b.retrieval import load_learning_graph
    from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore
    from wayfinder.application.courses import CourseService
    from wayfinder.application.learning_gateway import LearningGateway
    from wayfinder.infrastructure.course_store import PostgresCourseStore
    from wayfinder.infrastructure.learning_runtime import WebLearningRuntime

    if graph_loader is None:
        def graph_loader(doc_id, version):
            return load_learning_graph(JsonArtifactStore(settings.artifact_root), doc_id, version)
    runtime = WebLearningRuntime(phase_b_store, model=model, embedding=embedding, clock=clock)
    courses = CourseService(PostgresCourseStore(engine), settings=settings, clock=clock)
    gateway = LearningGateway(courses, runtime, graph_loader)
    courses.gateway = gateway
    return courses, gateway


def compose_account_service(settings: WebSettings, engine, *, mailer=None) -> AccountService:
    from doc2roadmap.application.phase_b.clock import SystemClock
    from wayfinder.infrastructure.auth_store import PostgresAuthStore
    from wayfinder.infrastructure.passwords import Argon2PasswordHasher, load_common_passwords

    policy = AuthPolicy(settings.session_idle_days, settings.session_absolute_days,
                        settings.login_max_failures, settings.login_failure_window_minutes,
                        email_verify_ttl_hours=settings.email_verify_ttl_hours,
                        resend_verification_per_hour=settings.resend_verification_per_hour,
                        password_reset_ttl_minutes=settings.password_reset_ttl_minutes,
                        public_base_url=settings.public_base_url,
                        email_logo_url=settings.email_logo_url)
    return AccountService(PostgresAuthStore(engine), Argon2PasswordHasher(), SystemClock(), policy,
                          load_common_passwords(), mailer=mailer if mailer is not None else compose_mailer(settings))


def compose_mailer(settings: WebSettings):
    from wayfinder.infrastructure.mail import ConsoleMailer, SmtpMailer
    from wayfinder.infrastructure.mail_dispatch import BackgroundMailer

    if settings.mailer == "console":
        if settings.env == "prod":
            raise ValueError("console mailer is only available in development")
        return ConsoleMailer()
    if not all([settings.smtp_username, settings.smtp_password, settings.smtp_from]):
        raise ValueError("SMTP username, password and from address are required")
    if not settings.smtp_starttls:
        raise ValueError("SMTP requires STARTTLS")
    if settings.env == "prod" and not settings.public_base_url.startswith("https://"):
        raise ValueError("WAYFINDER_PUBLIC_BASE_URL requires HTTPS in production")
    return BackgroundMailer(SmtpMailer(
        host=settings.smtp_host, port=settings.smtp_port, username=settings.smtp_username,
        password=settings.smtp_password.get_secret_value(), from_address=settings.smtp_from,
        starttls=settings.smtp_starttls,
    ))
