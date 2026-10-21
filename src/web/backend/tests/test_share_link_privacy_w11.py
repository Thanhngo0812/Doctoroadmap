import logging

from fastapi.testclient import TestClient

from wayfinder.api.app import create_app
from wayfinder.api.token_privacy import ShareLinkAccessFilter, install_share_link_log_filter
from wayfinder.composition import WebServices
from wayfinder.settings import WebSettings


def test_access_log_hides_raw_and_auth_return_share_tokens():
    token = "disposable-share-token-that-must-not-appear"
    for target in (
        f"/join/{token}",
        f"/api/v1/join/{token}",
        f"/dang-nhap?next=%2Fjoin%2F{token}",
        f"/dang-ky?next=%252Fjoin%252F{token}",
    ):
        record = logging.LogRecord("uvicorn.access", logging.INFO, "", 0,
            '%s - "%s %s HTTP/%s" %d', ("127.0.0.1", "GET", target, "1.1", 200), None)
        assert ShareLinkAccessFilter().filter(record)
        assert token not in record.getMessage()
        assert "/[share-link-request]" in record.getMessage()
        assert "200" in record.getMessage()


def test_normal_access_log_is_unchanged_and_filter_installation_is_idempotent():
    record = logging.LogRecord("uvicorn.access", logging.INFO, "", 0,
        '%s - "%s %s HTTP/%s" %d', ("127.0.0.1", "GET", "/api/v1/courses?page=1", "1.1", 200), None)
    before = record.getMessage()
    assert ShareLinkAccessFilter().filter(record)
    assert record.getMessage() == before
    logger = logging.getLogger("uvicorn.access")
    existing = list(logger.filters)
    try:
        install_share_link_log_filter()
        install_share_link_log_filter()
        assert sum(isinstance(item, ShareLinkAccessFilter) for item in logger.filters) == 1
    finally:
        logger.filters[:] = existing


def test_join_and_auth_documents_do_not_send_referrers_or_allow_cached_tokens(tmp_path):
    (tmp_path / "index.html").write_text("<!doctype html><html lang='vi'><title>WayFinder</title></html>", encoding="utf-8")
    app = create_app(WebSettings(_env_file=None, frontend_dist=tmp_path), WebServices(health_check=lambda: "ok"))
    client = TestClient(app)
    for path in ("/join/disposable-token", "/dang-nhap?next=%2Fjoin%2Fdisposable-token",
                 "/dang-ky?next=%2Fjoin%2Fdisposable-token"):
        response = client.get(path)
        assert response.status_code == 200
        assert response.headers.get("referrer-policy") == "no-referrer"
        assert response.headers.get("cache-control") == "no-store"
