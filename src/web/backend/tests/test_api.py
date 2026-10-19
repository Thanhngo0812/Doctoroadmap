from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from wayfinder.api.app import create_app
from wayfinder.api.errors import ERROR_STATUS, WebError
from wayfinder.settings import WebSettings
from wayfinder.composition import WebServices


NO_FRONTEND = Path("C:/missing-wayfinder-dist")


def test_health_and_security_headers() -> None:
    app = create_app(WebSettings(_env_file=None, version="0.1.0", frontend_dist=NO_FRONTEND),
                     WebServices(health_check=lambda: "ok"))

    response = TestClient(app).get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0", "db": "ok"}
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "same-origin"
    assert "content-security-policy" in response.headers


def test_health_reports_database_down() -> None:
    app = create_app(WebSettings(_env_file=None, frontend_dist=NO_FRONTEND), WebServices(health_check=lambda: "down"))

    response = TestClient(app).get("/api/v1/health")

    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "version": "0.1.0", "db": "down"}


def test_unknown_api_route_is_not_spa_fallback() -> None:
    frontend = Path(__file__).parent / "fixtures" / "frontend"
    app = create_app(WebSettings(_env_file=None, frontend_dist=frontend), WebServices(health_check=lambda: "ok"))

    response = TestClient(app).get("/api/v1/missing")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/json")
    assert response.json()["error"]["code"] == "not_found"


def test_spa_fallback_serves_index_for_unknown_page() -> None:
    frontend = Path(__file__).parent / "fixtures" / "frontend"
    app = create_app(WebSettings(_env_file=None, frontend_dist=frontend), WebServices(health_check=lambda: "ok"))

    response = TestClient(app).get("/courses/example")

    assert response.status_code == 200
    assert "frontend fixture" in response.text


def test_unhandled_exception_has_stable_envelope_and_security_headers() -> None:
    app = create_app(WebSettings(_env_file=None, frontend_dist=NO_FRONTEND), WebServices(health_check=lambda: "ok"))

    @app.get("/explode")
    def explode():
        raise RuntimeError("secret traceback detail")

    response = TestClient(app, raise_server_exceptions=False).get("/explode")

    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "internal_error"
    assert body["error"]["ref"]
    assert "secret traceback detail" not in response.text
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "same-origin"
    assert "content-security-policy" in response.headers


def test_http_errors_use_error_envelope() -> None:
    app = create_app(WebSettings(_env_file=None, frontend_dist=NO_FRONTEND), WebServices(health_check=lambda: "ok"))

    response = TestClient(app).get("/api/v1/missing")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_method_not_allowed_keeps_405_and_safe_envelope() -> None:
    app = create_app(WebSettings(_env_file=None, frontend_dist=NO_FRONTEND), WebServices(health_check=lambda: "ok"))

    response = TestClient(app).options("/api/v1/health", headers={"x-test-secret": "do-not-echo"})

    assert response.status_code == 405
    assert response.json()["error"]["code"] == "validation"
    assert "do-not-echo" not in response.text
    assert response.headers["x-content-type-options"] == "nosniff"


@pytest.mark.parametrize(("code", "status"), ERROR_STATUS.items())
def test_web_error_contract_maps_every_stable_code(code: str, status: int) -> None:
    app = create_app(WebSettings(_env_file=None, frontend_dist=NO_FRONTEND), WebServices(health_check=lambda: "ok"))

    @app.get("/error")
    def error():
        raise WebError(code, "Thông báo", retry_after=30 if status == 429 else None)

    response = TestClient(app).get("/error")

    assert response.status_code == status
    assert response.json()["error"]["code"] == code
    assert response.json()["error"]["retry_after"] == (30 if status == 429 else None)


def test_validation_envelope_does_not_echo_raw_input() -> None:
    app = create_app(WebSettings(_env_file=None, frontend_dist=NO_FRONTEND), WebServices(health_check=lambda: "ok"))

    @app.get("/typed")
    def typed(value: int):
        return {"value": value}

    response = TestClient(app).get("/typed?value=do-not-echo")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation"
    assert "do-not-echo" not in response.text
    assert set(response.json()["error"]["fields"][0]) == {"loc", "type", "message"}
