import base64
import json
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError

import pytest

from doc2roadmap.application.ports.extraction import ModelTransportError, PromptImage
from doc2roadmap.infrastructure.llm.gemini import (
    DEFAULT_MODEL_ID,
    GeminiEntityExtractor,
    MalformedModelResponse,
)
from doc2roadmap.infrastructure.llm.replay import (
    RecordingEntityExtractor,
    ReplayEntityExtractor,
)


SCHEMA = {
    "type": "object",
    "properties": {"entities": {"type": "array", "items": {"type": "string"}}},
    "required": ["entities"],
}


class _Response(BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def _response(text: str, usage: dict | None = None) -> _Response:
    payload = {
        "candidates": [
            {
                "content": {"role": "model", "parts": [{"text": text}]},
                "finishReason": "STOP",
            }
        ]
    }
    if usage is not None:
        payload["usageMetadata"] = usage
    return _Response(json.dumps(payload).encode())


def test_gemini_rejects_missing_key_before_any_request() -> None:
    with pytest.raises(ValueError, match="DOC2ROADMAP_GEMINI_API_KEY"):
        GeminiEntityExtractor("  ")


def test_gemini_sends_structured_multimodal_request_without_key_in_url(
    monkeypatch,
) -> None:
    requests = []

    def open_request(request, timeout):
        requests.append((request, timeout))
        return _response('{"entities":["Bayes"]}')

    monkeypatch.setattr("doc2roadmap.infrastructure.llm.gemini.urlopen", open_request)
    extractor = GeminiEntityExtractor(
        "test-secret", temperature=0.25, max_output_tokens=4096
    )
    session = extractor.start_session("Chỉ trích điều được giảng.")
    image = PromptImage("a" * 64, b"png-bytes")

    reply = session.ask_json("Đọc section này", response_schema=SCHEMA, images=(image,))

    assert extractor.identifier == "gemini-generate-content-rest:v1beta"
    assert extractor.model_id == DEFAULT_MODEL_ID == "gemini-3.1-flash-lite"
    assert reply.payload == {"entities": ["Bayes"]}
    assert not reply.repaired
    assert [turn.role for turn in session.turns] == ["user", "model"]
    request, timeout = requests[0]
    assert "test-secret" not in request.full_url
    assert request.get_header("X-goog-api-key") == "test-secret"
    assert timeout == 120
    body = json.loads(request.data)
    assert body["systemInstruction"] == {
        "parts": [{"text": "Chỉ trích điều được giảng."}]
    }
    assert body["generationConfig"] == {
        "temperature": 0.25,
        "maxOutputTokens": 4096,
        "responseMimeType": "application/json",
        "responseJsonSchema": SCHEMA,
    }
    assert body["contents"][0]["role"] == "user"
    assert body["contents"][0]["parts"] == [
        {"text": "Đọc section này"},
        {"text": f"MEDIA_ID: {image.image_id}"},
        {
            "inlineData": {
                "mimeType": "image/png",
                "data": base64.b64encode(b"png-bytes").decode("ascii"),
            }
        },
    ]


def test_gemini_exposes_usage_metadata(monkeypatch) -> None:
    monkeypatch.setattr(
        "doc2roadmap.infrastructure.llm.gemini.urlopen",
        lambda request, timeout: _response(
            '{"entities":[]}',
            {"promptTokenCount": 12, "candidatesTokenCount": 3, "thoughtsTokenCount": 2, "totalTokenCount": 17},
        ),
    )
    reply = GeminiEntityExtractor("test-secret").start_session("system").ask_json("extract", response_schema=SCHEMA)
    assert reply.usage == {"promptTokenCount": 12, "candidatesTokenCount": 3, "thoughtsTokenCount": 2, "totalTokenCount": 17}


def test_stage_counts_http_retry_json_repair_and_parallel_calls(tmp_path, monkeypatch):
    from threading import Barrier, local
    from doc2roadmap.application.stage_measurements import measure_stage
    from doc2roadmap.application.model_calls import ModelJob, run_model_jobs
    from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore

    state = local()
    barrier = Barrier(2)
    def respond(request, timeout):
        state.attempt = getattr(state, "attempt", 0) + 1
        if state.attempt == 1:
            barrier.wait(timeout=5)
            raise HTTPError(request.full_url, 429, "busy", {}, None)
        return _response("not json" if state.attempt == 2 else '{"entities":[]}',
                         {"promptTokenCount": 10, "candidatesTokenCount": 3, "thoughtsTokenCount": 2})
    monkeypatch.setattr("doc2roadmap.infrastructure.llm.gemini.urlopen", respond)
    monkeypatch.setattr("doc2roadmap.infrastructure.llm.gemini.sleep", lambda _: None)
    store = JsonArtifactStore(tmp_path)
    model = GeminiEntityExtractor("fake-key", max_retries=1)
    @measure_stage
    def execute():
        jobs = [ModelJob("test", model, "system", "hash", {"item": i}, SCHEMA, lambda _: None) for i in range(2)]
        values, _, _ = run_model_jobs(jobs, [], concurrency=2)
        assert values == [{"entities": []}, {"entities": []}]
        return store.save_graph("book", "s", "c", {}, {}, upstream_version=1)
    stats = execute().manifest["stats"]
    # Two requests, each with 429 -> malformed JSON -> repair, regardless of pool scheduling.
    assert stats["model_calls"] == 6
    assert stats["usage_responses"] == 4
    assert stats["input_tokens"] == 40
    assert stats["output_tokens"] == 20
    assert stats["token_usage_complete"] is False  # don't silently claim usage for missing 429 responses


def test_session_repairs_malformed_json_once_in_the_same_conversation(
    monkeypatch,
) -> None:
    responses = iter(["not json", '{"entities":[]}', '{"entities":["Sau sửa"]}'])
    bodies = []

    def open_request(request, timeout):
        bodies.append(json.loads(request.data))
        return _response(next(responses))

    monkeypatch.setattr("doc2roadmap.infrastructure.llm.gemini.urlopen", open_request)
    session = GeminiEntityExtractor("test-secret").start_session("system")

    repaired = session.ask_json("lượt một", response_schema=SCHEMA)
    later = session.ask_json("lượt hai", response_schema=SCHEMA)

    assert repaired.payload == {"entities": []} and repaired.repaired
    assert later.payload == {"entities": ["Sau sửa"]} and not later.repaired
    assert session.call_count == 3
    assert session.repair_count == 1
    assert [turn.role for turn in session.turns] == [
        "user",
        "model",
        "user",
        "model",
        "user",
        "model",
    ]
    repair_contents = bodies[1]["contents"]
    assert [content["role"] for content in repair_contents] == ["user", "model", "user"]
    assert "JSON không hợp lệ" in repair_contents[-1]["parts"][0]["text"]


def test_second_malformed_response_fails_without_a_third_repair_call(monkeypatch) -> None:
    calls = 0

    def open_request(request, timeout):
        nonlocal calls
        calls += 1
        return _response("still not json")

    monkeypatch.setattr("doc2roadmap.infrastructure.llm.gemini.urlopen", open_request)
    session = GeminiEntityExtractor("test-secret").start_session("system")

    with pytest.raises(MalformedModelResponse, match="sau một lượt sửa") as error:
        session.ask_json("extract", response_schema=SCHEMA)

    assert calls == session.call_count == 2
    assert session.repair_count == 1
    assert error.value.raw_text == "still not json"


def test_transient_http_error_retries_but_permanent_error_does_not_leak_key(
    monkeypatch,
) -> None:
    calls = 0
    sleeps = []

    def retry_once(request, timeout):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise HTTPError(request.full_url, 429, "rate limited", {}, None)
        return _response('{"entities":[]}')

    monkeypatch.setattr("doc2roadmap.infrastructure.llm.gemini.urlopen", retry_once)
    monkeypatch.setattr("doc2roadmap.infrastructure.llm.gemini.sleep", sleeps.append)
    monkeypatch.setattr("doc2roadmap.infrastructure.llm.gemini.random", lambda: 0.25)
    session = GeminiEntityExtractor("test-secret").start_session("system")

    session.ask_json("extract", response_schema=SCHEMA)

    assert calls == 2
    assert sleeps == [1.25]

    def forbidden(request, timeout):
        raise HTTPError(request.full_url, 403, "forbidden test-secret", {}, None)

    monkeypatch.setattr("doc2roadmap.infrastructure.llm.gemini.urlopen", forbidden)
    with pytest.raises(ModelTransportError) as error:
        GeminiEntityExtractor("test-secret").start_session("system").ask_json(
            "extract", response_schema=SCHEMA
        )
    assert "HTTP 403" in str(error.value)
    assert "test-secret" not in str(error.value)


def test_exhausted_transient_errors_raise_transport_error(monkeypatch) -> None:
    def always_503(request, timeout):
        raise HTTPError(request.full_url, 503, "unavailable", {}, None)

    monkeypatch.setattr("doc2roadmap.infrastructure.llm.gemini.urlopen", always_503)
    monkeypatch.setattr("doc2roadmap.infrastructure.llm.gemini.sleep", lambda seconds: None)
    session = GeminiEntityExtractor("test-secret", max_retries=2).start_session("system")

    with pytest.raises(ModelTransportError, match="lỗi tạm thời"):
        session.ask_json("extract", response_schema={"type": "object"})


def test_record_and_replay_are_ordered_and_invalidated_by_prompt_hash(
    tmp_path: Path, monkeypatch
) -> None:
    responses = iter(['{"entities":["first"]}', '{"entities":["second"]}'])

    def open_request(request, timeout):
        return _response(next(responses))

    monkeypatch.setattr("doc2roadmap.infrastructure.llm.gemini.urlopen", open_request)
    path = tmp_path / "section.json"
    image = PromptImage("b" * 64, b"image")
    recorder = RecordingEntityExtractor(
        GeminiEntityExtractor("never-record-this"), path, prompt_hash="prompt-v1"
    )
    recorded = recorder.start_session("system")
    first = recorded.ask_json("first prompt", response_schema=SCHEMA, images=(image,))
    second = recorded.ask_json("second prompt", response_schema=SCHEMA)

    assert first.payload == {"entities": ["first"]}
    assert second.payload == {"entities": ["second"]}
    fixture_text = path.read_text(encoding="utf-8")
    fixture = json.loads(fixture_text)
    assert "never-record-this" not in fixture_text
    assert fixture["prompt_hash"] == "prompt-v1"
    assert [call["request"]["prompt"] for call in fixture["calls"]] == [
        "first prompt",
        "second prompt",
    ]
    assert fixture["calls"][0]["request"]["images"][0]["data"] == base64.b64encode(
        b"image"
    ).decode("ascii")

    monkeypatch.setattr(
        "doc2roadmap.infrastructure.llm.gemini.urlopen",
        lambda *args, **kwargs: pytest.fail("replay must not touch the network"),
    )
    replay = ReplayEntityExtractor(path, prompt_hash="prompt-v1")
    replayed = replay.start_session("system")

    assert replayed.ask_json(
        "first prompt", response_schema=SCHEMA, images=(image,)
    ).payload == {"entities": ["first"]}
    assert replayed.ask_json("second prompt", response_schema=SCHEMA).payload == {
        "entities": ["second"]
    }
    assert replayed.call_count == 2

    with pytest.raises(ValueError, match="prompt_hash"):
        ReplayEntityExtractor(path, prompt_hash="changed")


def test_committed_multimodal_fixture_replays_without_network(monkeypatch) -> None:
    path = Path("tests/fixtures/llm/a3-section-with-image.json")
    fixture = json.loads(path.read_text(encoding="utf-8"))
    monkeypatch.setattr(
        "doc2roadmap.infrastructure.llm.gemini.urlopen",
        lambda *args, **kwargs: pytest.fail("replay must not touch the network"),
    )
    from doc2roadmap.application.extraction_prompt import load_prompts, prompt_hash
    from doc2roadmap.config import Settings

    defaults = Settings.model_fields
    replay = ReplayEntityExtractor(path, prompt_hash=prompt_hash(
        model_id=defaults["extraction_model_id"].default,
        generation={"temperature": defaults["extraction_temperature"].default,
                    "max_output_tokens": defaults["extraction_max_output_tokens"].default},
    ))
    session = replay.start_session(load_prompts().system)

    replies = []
    for call in fixture["calls"]:
        request = call["request"]
        images = tuple(
            PromptImage(
                image["image_id"],
                base64.b64decode(image["data"]),
                image["mime_type"],
            )
            for image in request["images"]
        )
        replies.append(
            session.ask_json(
                request["prompt"],
                response_schema=request["response_schema"],
                images=images,
            ).payload
        )

    assert fixture["model_id"] == "gemini-3.1-flash-lite"
    assert len(replies) == session.call_count == 4
    assert fixture["calls"][0]["request"]["images"]
    assert replies[0]["media_descriptions"]

    from doc2roadmap.application.use_cases.extract_entities import (
        FormulaContext, SectionContext, extract_section,
    )
    from doc2roadmap.domain.models import Chunk

    source = json.loads(path.with_suffix(".context.json").read_text(encoding="utf-8"))
    context = SectionContext(
        source["section_id"], source["title"], source["section_path"],
        [Chunk.from_dict(chunk) for chunk in source["chunks"]],
        [PromptImage(image["image_id"], base64.b64decode(image["data"]), image["mime_type"])
         for image in fixture["calls"][0]["request"]["images"]],
        [FormulaContext(**formula) for formula in source["formulas"]],
        {(kind, media_id): caption for kind, media_id, caption in source["media_captions"]},
    )
    result = extract_section(context, replay)
    assert result.stats["missing_media_descriptions"] == 0
    assert any(entity.learnable and entity.evidence for entity in result.entities)
    assert any(entity.is_media and entity.description for entity in result.entities)
