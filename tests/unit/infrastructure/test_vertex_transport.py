import json
from io import BytesIO
from types import SimpleNamespace
from urllib.error import HTTPError

import pytest

from doc2roadmap.application.ports.embedding import EmbeddingRequest
from doc2roadmap.infrastructure.embedding.gemini import GeminiEmbedding
from doc2roadmap.infrastructure.google_auth import VertexCredentials
from doc2roadmap.infrastructure.llm.gemini import GeminiEntityExtractor


def test_vertex_token_refresh_without_exposing_key(monkeypatch):
    credential = SimpleNamespace(valid=False, token=None, refresh=lambda request: None)
    calls = []

    def refresh(request):
        calls.append(request)
        credential.token = "fresh-token"
        credential.valid = True

    credential.refresh = refresh
    monkeypatch.setattr("doc2roadmap.infrastructure.google_auth.google.auth.default",
                        lambda **kwargs: (credential, "ignored"))
    auth = VertexCredentials("project-1")
    assert auth.headers()["Authorization"] == "Bearer fresh-token"
    assert auth.headers()["x-goog-user-project"] == "project-1"
    assert len(calls) == 1
    credential.valid = False
    assert auth.headers()["Authorization"] == "Bearer fresh-token"
    assert len(calls) == 2


def test_vertex_llm_preserves_request_contract_and_cache_identity(monkeypatch):
    requests = []
    monkeypatch.setattr(VertexCredentials, "headers", lambda self: {
        "Authorization": "Bearer token", "x-goog-user-project": self.project})

    def fake_open(request, timeout):
        requests.append(request)
        return BytesIO(json.dumps({"candidates": [{"content": {"parts": [{"text": "{}"}]}}]}).encode())

    monkeypatch.setattr("doc2roadmap.infrastructure.llm.gemini.urlopen", fake_open)
    for transport in ("developer_api", "vertex"):
        model = GeminiEntityExtractor("key" if transport == "developer_api" else None,
                                      transport=transport, vertex_project="project-1")
        assert model.start_session("system").ask_json("prompt", response_schema={"type": "object"}).payload == {}
        assert model.identifier == "gemini-generate-content-rest:v1beta"
        assert model.model_id == "gemini-3.1-flash-lite"
    assert requests[0].data == requests[1].data
    assert requests[1].full_url.endswith("/projects/project-1/locations/global/publishers/google/models/gemini-3.1-flash-lite:generateContent")
    assert requests[1].get_header("Authorization") == "Bearer token"
    assert requests[1].get_header("X-goog-user-project") == "project-1"
    assert requests[1].get_header("X-goog-api-key") is None


def test_vertex_embedding_normalizes_each_prediction(monkeypatch):
    requests = []
    monkeypatch.setattr(VertexCredentials, "headers", lambda self: {"Authorization": "Bearer token"})

    def fake_open(request, timeout):
        requests.append(request)
        return BytesIO(json.dumps({"predictions": [{"embeddings": {"values": [3.0, 4.0]}}]}).encode())

    monkeypatch.setattr("doc2roadmap.infrastructure.embedding.gemini.urlopen", fake_open)
    model = GeminiEmbedding(None, transport="vertex", vertex_project="project-1", output_dimensionality=2)
    vectors = model.embed([EmbeddingRequest("alpha", "RETRIEVAL_DOCUMENT"),
                           EmbeddingRequest("beta", "RETRIEVAL_QUERY")])
    assert all(vector == pytest.approx([0.6, 0.8]) for vector in vectors)
    assert len(requests) == 2
    assert requests[0].full_url.endswith("/models/gemini-embedding-001:predict")
    assert json.loads(requests[0].data)["instances"] == [{"content": "alpha", "task_type": "RETRIEVAL_DOCUMENT"}]
    assert model.identifier == "gemini-rest-embedding-v1"
    assert model.embedding_model_id == "gemini-embedding-001:2"


def test_vertex_429_retries_and_counts_per_call(monkeypatch):
    seen = []
    monkeypatch.setattr(VertexCredentials, "headers", lambda self: {"Authorization": "Bearer token"})
    monkeypatch.setattr("doc2roadmap.infrastructure.llm.gemini.sleep", lambda seconds: None)

    def fake_open(request, timeout):
        seen.append(request)
        if len(seen) == 1:
            raise HTTPError(request.full_url, 429, "quota", {}, None)
        return BytesIO(json.dumps({"candidates": [{"content": {"parts": [{"text": "{}"}]}}]}).encode())

    monkeypatch.setattr("doc2roadmap.infrastructure.llm.gemini.urlopen", fake_open)
    model = GeminiEntityExtractor(None, transport="vertex", vertex_project="project-1", max_retries=1)
    assert model.start_session("system").ask_json("prompt", response_schema={"type": "object"}).payload == {}
    assert model.retry_429_count == model._retry_state.count == 1
    assert len(seen) == 2
