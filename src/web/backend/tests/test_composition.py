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
