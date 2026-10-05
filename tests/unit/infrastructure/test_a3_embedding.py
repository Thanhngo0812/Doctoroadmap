from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.error import URLError

import pytest

from doc2roadmap.application.ports.embedding import EmbeddingRequest
from doc2roadmap.infrastructure.embedding.gemini import GeminiEmbedding
from doc2roadmap.infrastructure.embedding.replay import (
    ReplayEmbedding,
    embedding_request_hash,
    record_embedding_fixture,
)


class _Response:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


@dataclass
class _FakeEmbedding:
    identifier: str = "fake-embedding"
    embedding_model_id: str = "fake-model:2"
    calls: int = 0

    def embed(self, requests):
        self.calls += 1
        return [
            [float(len(request.text)), float(request.task_type == "RETRIEVAL_QUERY")]
            for request in requests
        ]


def test_gemini_embedding_requires_key_at_construction() -> None:
    with pytest.raises(ValueError, match="API key"):
        GeminiEmbedding("")


def test_gemini_embedding_uses_batch_rest_without_leaking_key(monkeypatch) -> None:
    captured = {}

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return _Response(
            {
                "embeddings": [
                    {"values": [3.0, 4.0]},
                    {"values": [0.0, 5.0]},
                ]
            }
        )

    monkeypatch.setattr("doc2roadmap.infrastructure.embedding.gemini.urlopen", fake_urlopen)
    secret = "secret-must-not-leak"
    embedding = GeminiEmbedding(secret, output_dimensionality=2)

    vectors = embedding.embed(
        [
            EmbeddingRequest("document", "RETRIEVAL_DOCUMENT"),
            EmbeddingRequest("query", "RETRIEVAL_QUERY"),
        ]
    )

    request = captured["request"]
    body = json.loads(request.data)
    assert request.full_url.endswith("/models/gemini-embedding-001:batchEmbedContents")
    assert secret not in request.full_url
    assert secret not in request.data.decode("utf-8")
    assert request.get_header("X-goog-api-key") == secret
    assert body["requests"][0]["content"]["parts"][0]["text"] == "document"
    assert body["requests"][1]["taskType"] == "RETRIEVAL_QUERY"
    assert body["requests"][1]["outputDimensionality"] == 2
    assert vectors[0] == pytest.approx([0.6, 0.8])
    assert vectors[1] == pytest.approx([0.0, 1.0])


def test_gemini_embedding_retries_a_transient_connection_failure(monkeypatch) -> None:
    calls = 0
    sleeps = []

    def fail_once(request, timeout):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise URLError("temporary")
        return _Response({"embeddings": [{"values": [3.0, 4.0]}]})

    monkeypatch.setattr("doc2roadmap.infrastructure.embedding.gemini.urlopen", fail_once)
    monkeypatch.setattr("doc2roadmap.infrastructure.embedding.gemini.sleep", sleeps.append)

    vector = GeminiEmbedding(
        "secret", output_dimensionality=2, max_retries=1
    ).embed([EmbeddingRequest("document")])

    assert calls == 2
    assert sleeps == [1]
    assert vector[0] == pytest.approx([0.6, 0.8])


def test_embedding_replay_is_a_request_dictionary_and_invalidates_by_model(tmp_path) -> None:
    fixture = tmp_path / "embedding.json"
    requests = [
        EmbeddingRequest("same text", "RETRIEVAL_DOCUMENT"),
        EmbeddingRequest("same text", "RETRIEVAL_QUERY"),
    ]
    source = _FakeEmbedding()

    size = record_embedding_fixture(fixture, source, requests)
    replay = ReplayEmbedding(fixture, expected_model_id=source.embedding_model_id)

    assert size == fixture.stat().st_size
    assert source.calls == 1
    assert replay.embed(requests) == source.embed(requests)
    assert embedding_request_hash(requests[0]) != embedding_request_hash(requests[1])
    payload = json.loads(fixture.read_text(encoding="utf-8"))
    assert sorted(payload["vectors"]) == sorted(map(embedding_request_hash, requests))
    with pytest.raises(ValueError, match="model"):
        ReplayEmbedding(fixture, expected_model_id="another-model")


def test_embedding_replay_never_falls_through_to_network(tmp_path) -> None:
    fixture = tmp_path / "embedding.json"
    record_embedding_fixture(fixture, _FakeEmbedding(), [EmbeddingRequest("known")])
    replay = ReplayEmbedding(fixture, expected_model_id="fake-model:2")

    with pytest.raises(LookupError, match="không có vector"):
        replay.embed([EmbeddingRequest("unknown")])


def test_vertex_embedding_counts_parallel_retries_and_reported_tokens(tmp_path, monkeypatch):
    from threading import Barrier, local
    from types import SimpleNamespace
    from urllib.error import HTTPError
    from doc2roadmap.application.stage_measurements import measure_stage
    from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore
    state, barrier = local(), Barrier(2)
    def respond(request, timeout):
        if not getattr(state, "retried", False):
            state.retried = True
            barrier.wait(timeout=5)
            raise HTTPError(request.full_url, 429, "busy", {}, None)
        return _Response({"predictions": [{"embeddings": {"values": [3, 4], "statistics": {"token_count": 6}}}]})
    monkeypatch.setattr("doc2roadmap.infrastructure.embedding.gemini.urlopen", respond)
    monkeypatch.setattr("doc2roadmap.infrastructure.embedding.gemini.sleep", lambda _: None)
    embedding = GeminiEmbedding("fake-key", output_dimensionality=2, batch_size=2, max_retries=1)
    embedding._vertex = SimpleNamespace(url=lambda *args: "https://fake.invalid/predict", headers=lambda: {})
    store = JsonArtifactStore(tmp_path)
    @measure_stage
    def execute():
        assert embedding.embed([EmbeddingRequest("one"), EmbeddingRequest("two")]) == [[0.6, 0.8], [0.6, 0.8]]
        return store.save_retrieval("book", "s", "c", {}, {}, upstream_version=1)
    stats = execute().manifest["stats"]
    assert (stats["model_calls"], stats["input_tokens"], stats["output_tokens"]) == (4, 12, 0)
    assert stats["usage_responses"] == 2
    assert stats["embedding_model_calls"] == 4
    assert stats["embedding_input_tokens"] == 12


def test_committed_embedding_fixture_has_all_reviewed_chunks() -> None:
    fixture = __import__("pathlib").Path("tests/fixtures/embedding/a3-chunks.json")
    payload = json.loads(fixture.read_text(encoding="utf-8"))

    assert payload["embedding_model_id"] == "gemini-embedding-001:768"
    assert len(payload["vectors"]) == 233
    assert {len(vector) for vector in payload["vectors"].values()} == {768}
