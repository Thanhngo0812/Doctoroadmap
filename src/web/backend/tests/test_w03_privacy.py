import pytest
from fastapi.testclient import TestClient

from wayfinder.api.app import create_app
from wayfinder.composition import WebServices
from wayfinder.settings import WebSettings


@pytest.mark.parametrize("path", ["/xac-minh?token=private", "/quen-mat-khau", "/dat-lai-mat-khau?token=private", "/api/v1/auth/password-reset/confirm", "/api/v1/auth/verify-email"])
def test_recovery_pages_and_api_do_not_cache_or_forward_token_referrers(tmp_path, path):
    (tmp_path / "index.html").write_text("<html lang='vi'><title>WayFinder</title></html>", encoding="utf-8")
    client = TestClient(create_app(WebSettings(_env_file=None, frontend_dist=tmp_path), WebServices(lambda: "ok")))
    response = client.get(path)
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["cache-control"] == "no-store"
