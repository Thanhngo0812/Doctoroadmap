import pytest

from wayfinder.composition import compose_services
from wayfinder.settings import WebSettings
from doc2roadmap.config import Settings


def test_vertex_transport_is_passed_to_model_and_embedding_without_api_key() -> None:
    calls = []

    class Model:
        def __init__(self, *args, **kwargs):
            calls.append(("model", args, kwargs))

    class Embedding:
        def __init__(self, *args, **kwargs):
            calls.append(("embedding", args, kwargs))

    def validate_auth(project: str, location: str) -> None:
        calls.append(("auth", project, location))

    services = compose_services(
        WebSettings(_env_file=None), health_check=lambda: "ok", close=lambda: None,
        core_settings=Settings(_env_file=None, llm_transport="vertex", vertex_project="project-test",
                               vertex_location="us-central1"),
        auth_validator=validate_auth, model_factory=Model, embedding_factory=Embedding,
    )

    assert [call[0] for call in calls] == ["auth", "model", "embedding"]
    assert calls[1][2]["transport"] == "vertex"
    assert calls[2][2]["transport"] == "vertex"
    assert calls[1][1][0] is None and calls[2][1][0] is None
    assert calls[1][2]["vertex_project"] == calls[2][2]["vertex_project"] == "project-test"
    assert services.model is not None and services.embedding is not None


def test_lecture_model_uses_core_limits_instead_of_transport_defaults() -> None:
    from types import SimpleNamespace
    from doc2roadmap.domain.phase_b_limits import BSettings
    from doc2roadmap.infrastructure.llm.phase_b import GeminiToolModel
    settings = BSettings()
    services = compose_services(WebSettings(_env_file=None), health_check=lambda: 'ok',
        core_settings=Settings(_env_file=None, llm_transport='vertex', vertex_project='fake-project', vertex_location='us-central1'),
        auth_validator=lambda *_: None, model_factory=GeminiToolModel,
        embedding_factory=lambda *_a, **_k: object())
    try:
        assert services.model.max_output_tokens == settings.lecture_max_output_tokens
        assert services.model.temperature == settings.lecture_temperature
        assert services.model.model_id == settings.model_id
        requests = []
        def capture(operation, body, **kwargs):
            requests.append(body)
            return SimpleNamespace(close=lambda: None)
        services.model._request = capture
        services.model._decode_sse = lambda _response: iter(())
        assert list(services.model.start_session('fake system').stream_text('fake prompt', temperature=settings.lecture_temperature)) == []
        request = requests[0]
        assert request['generationConfig']['maxOutputTokens'] == settings.lecture_max_output_tokens
        assert request['generationConfig']['temperature'] == settings.lecture_temperature
    finally:
        services.close()


def test_missing_vertex_project_fails_before_auth_or_model() -> None:
    calls = []

    with pytest.raises(ValueError, match="VERTEX_PROJECT"):
        compose_services(
            WebSettings(_env_file=None), health_check=lambda: "ok", close=lambda: None,
            core_settings=Settings(_env_file=None, llm_transport="vertex", vertex_project=None),
            auth_validator=lambda *_: calls.append("auth"),
            model_factory=lambda *_a, **_k: calls.append("model"),
            embedding_factory=lambda *_a, **_k: calls.append("embedding"),
        )

    assert calls == []


def test_non_vertex_transport_is_rejected_before_auth_or_model() -> None:
    calls = []
    with pytest.raises(ValueError, match="vertex"):
        compose_services(
            WebSettings(_env_file=None), health_check=lambda: "ok", close=lambda: None,
            core_settings=Settings(_env_file=None, llm_transport="developer_api", gemini_api_key="fake"),
            auth_validator=lambda *_: calls.append("auth"),
            model_factory=lambda *_a, **_k: calls.append("model"),
            embedding_factory=lambda *_a, **_k: calls.append("embedding"),
        )
    assert calls == []


def test_auth_validation_failure_prevents_model_construction() -> None:
    calls = []

    def reject_auth(*_args):
        calls.append("auth")
        raise RuntimeError("ADC unavailable")

    with pytest.raises(RuntimeError, match="ADC unavailable"):
        compose_services(
            WebSettings(_env_file=None), health_check=lambda: "ok", close=lambda: None,
            core_settings=Settings(_env_file=None, llm_transport="vertex", vertex_project="project-test",
                                   vertex_location="us-central1"),
            auth_validator=reject_auth,
            model_factory=lambda *_a, **_k: calls.append("model"),
            embedding_factory=lambda *_a, **_k: calls.append("embedding"),
        )
    assert calls == ["auth"]


def _compose(settings, **kwargs):
    return compose_services(
        settings,
        core_settings=Settings(_env_file=None, llm_transport="vertex", vertex_project="project-test",
                               vertex_location="us-central1"),
        auth_validator=lambda *_: None,
        model_factory=lambda *_a, **_k: object(),
        embedding_factory=lambda *_a, **_k: object(),
        **kwargs,
    )


def test_without_database_configuration_keeps_database_services_unconfigured() -> None:
    closed = []
    health = lambda: "ok"

    services = _compose(WebSettings(_env_file=None), health_check=health,
                        close=lambda: closed.append("external"))

    assert services.health_check is health
    assert services.accounts is None
    assert services.phase_b_store is None
    services.close()
    assert closed == ["external"]


def test_default_database_services_share_and_close_composition_owned_engine(monkeypatch) -> None:
    from wayfinder.infrastructure import database, phase_b_store

    events = []
    engine = object()

    class FakeHealth:
        def __init__(self, url):
            assert url == "postgresql+psycopg://test/db"
            self.engine = engine

        def __call__(self):
            return "ok"

        def close(self):
            events.append("health.close")

    class FakeStore:
        def __init__(self, received_engine, **kwargs):
            assert received_engine is engine
            assert kwargs["lock_pool_size"] == WebSettings(_env_file=None).phase_b_lock_pool_size
            events.append("store.create")

        def close(self):
            events.append("store.close")

    from types import SimpleNamespace
    account_service = SimpleNamespace(mailer=None, on_email_verified=None)
    account_engines = []
    monkeypatch.setattr(database, "DatabaseHealth", FakeHealth)
    monkeypatch.setattr(phase_b_store, "PostgresPhaseBStore", FakeStore)
    monkeypatch.setattr(
        "wayfinder.composition.compose_account_service",
        lambda _settings, received_engine: account_engines.append(received_engine) or account_service,
    )

    services = _compose(WebSettings(_env_file=None, database_url="postgresql+psycopg://test/db"))

    assert services.accounts is account_service
    assert services.phase_b_store is not None
    assert account_engines == [engine]
    assert events == ["store.create"]
    services.close()
    assert events == ["store.create", "store.close", "health.close"]


def test_default_phase_b_store_closes_before_injected_health_callback(monkeypatch) -> None:
    from wayfinder.infrastructure import phase_b_store

    events = []
    engine = object()

    class FakeHealth:
        def __init__(self):
            self.engine = engine

        def __call__(self):
            return "ok"

    class FakeStore:
        def __init__(self, received_engine, **_kwargs):
            assert received_engine is engine

        def close(self):
            events.append("store.close")

    monkeypatch.setattr(phase_b_store, "PostgresPhaseBStore", FakeStore)
    services = _compose(WebSettings(_env_file=None), health_check=FakeHealth(),
                        close=lambda: events.append("caller.close"))

    services.close()

    assert events == ["store.close", "caller.close"]


def test_caller_owned_phase_b_store_is_not_closed_by_composition(monkeypatch) -> None:
    from wayfinder.infrastructure import phase_b_store

    monkeypatch.setattr(
        phase_b_store, "PostgresPhaseBStore",
        lambda *_args, **_kwargs: pytest.fail("composition replaced the caller's store"),
    )
    events = []
    supplied_store = object()
    services = _compose(WebSettings(_env_file=None), health_check=lambda: "ok",
                        phase_b_store=supplied_store, close=lambda: events.append("caller.close"))

    assert services.phase_b_store is supplied_store
    services.close()
    assert events == ["caller.close"]
