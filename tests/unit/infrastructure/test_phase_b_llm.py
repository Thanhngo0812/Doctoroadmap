import io
import json

import pytest

from doc2roadmap.application.ports.phase_b import Done, ToolCall
from doc2roadmap.infrastructure.llm import phase_b
from doc2roadmap.infrastructure.llm.phase_b import GeminiToolModel, RecordingToolModel, ReplayToolModel


class _Response:
    def __init__(self, lines):
        self._stream = io.BytesIO(b"".join(lines))

    def __iter__(self):
        return self._stream

    def read(self):
        return self._stream.read()

    def close(self):
        self._stream.close()


def test_interleaved_json_streams_keep_their_own_usage(monkeypatch):
    def response(tokens, text):
        events = [{'candidates': [{'content': {'parts': [{'text': text}]}}],
                   'usageMetadata': {'promptTokenCount': tokens}},
                  {'candidates': [{'finishReason': 'STOP'}]}]
        return _Response([b'data: ' + json.dumps(event).encode() + b'\n\n' for event in events])
    responses = iter([response(11, 'a'), response(99, 'b')])
    monkeypatch.setattr(phase_b, 'urlopen', lambda request, timeout: next(responses))
    model = GeminiToolModel('key')
    first, second = model.start_session('system'), model.start_session('system')
    stream = first.stream_json('first', response_schema={'type': 'object'})
    assert next(stream) == 'a'
    assert list(second.stream_json('second', response_schema={'type': 'object'})) == ['b']
    assert list(stream) == []
    assert first.last_usage['promptTokenCount'] == 11
    assert second.last_usage['promptTokenCount'] == 99


@pytest.mark.parametrize("transport", ["developer_api", "vertex"])
def test_tool_turn_preserves_parallel_calls_signatures_and_matching_responses(monkeypatch, transport):
    first_parts = [
        {"text": "private thought", "thought": True, "thoughtSignature": "text-signature"},
        {"functionCall": {"name": "lookup", "args": {"id": 1}, "id": "call-a"},
         "thoughtSignature": "opaque-a"},
        {"functionCall": {"name": "lookup", "args": {"id": 2}, "id": "call-b"},
         "thoughtSignature": "opaque-b"},
    ]
    responses = [
        _Response([b"data: " + json.dumps({"candidates": [{"content": {"role": "model", "parts": first_parts}}]}).encode() + b"\n\n",
                   b"data: " + json.dumps({"candidates": [{"finishReason": "STOP"}],
                                          "usageMetadata": {"promptTokenCount": 7, "thoughtsTokenCount": 3}}).encode() + b"\n\n"]),
        _Response([b"data: " + json.dumps({"candidates": [{"content": {"role": "model", "parts": [{"text": "done"}]},
                                           "finishReason": "STOP"}],
                                          "usageMetadata": {"promptTokenCount": 9}}).encode() + b"\n\n"]),
    ]
    requests = []

    def fake_urlopen(request, timeout):
        requests.append(request)
        return responses.pop(0)

    monkeypatch.setattr(phase_b, "urlopen", fake_urlopen)
    model = GeminiToolModel("key" if transport == "developer_api" else None, "gemini-test",
                            transport=transport, vertex_project="test-project" if transport == "vertex" else None)
    if transport == "vertex":
        model.vertex.headers = lambda: {"Authorization": "Bearer test"}
    session = model.start_session("system", [{"name": "lookup", "parameters": {"type": "object"}}])
    first_events = list(session.stream([{"role": "user", "text": "find two"}]))
    calls = [event for event in first_events if isinstance(event, ToolCall)]
    done = next(event for event in first_events if isinstance(event, Done))
    assert [call.call_id for call in calls] == ["call-a", "call-b"]
    assert done.usage["thoughtsTokenCount"] == 3
    assert "?alt=sse" in requests[0].full_url
    first_body = json.loads(requests[0].data)
    assert "parametersJsonSchema" not in first_body["tools"][0]["functionDeclarations"][0]

    list(session.stream([
        {"role": "model", "turn_id": done.turn_id},
        {"role": "tool", "tool_results": [
            {"name": "lookup", "call_id": "call-a", "result": {"value": "one"}},
            {"name": "lookup", "call_id": "call-b", "result": {"value": "two"}},
        ]},
    ]))
    second_body = json.loads(requests[1].data)
    assert second_body["contents"][0]["parts"] == first_parts
    responses_from_tools = second_body["contents"][1]
    assert responses_from_tools["role"] == "user"
    assert [part["functionResponse"]["id"] for part in responses_from_tools["parts"]] == ["call-a", "call-b"]
    assert all("?alt=sse" in request.full_url for request in requests)


@pytest.mark.parametrize("transport", ["developer_api", "vertex"])
def test_json_stream_assembles_fragmented_sse_text_and_final_usage(monkeypatch, transport):
    events = [
        {"candidates": [{"content": {"parts": [{"text": '{"title":'}]}}]},
        {"candidates": [{"content": {"parts": [{"text": '"ok"}'}]}, "finishReason": "STOP"}],
         "usageMetadata": {"promptTokenCount": 11, "candidatesTokenCount": 3}},
    ]
    raw = b"".join(b"data: " + json.dumps(event).encode() + b"\n\n" for event in events)
    requests = []
    monkeypatch.setattr(phase_b, "urlopen", lambda request, timeout: (requests.append(request) or _Response([raw])))
    model = GeminiToolModel("key" if transport == "developer_api" else None, "gemini-test",
                            transport=transport, vertex_project="test-project" if transport == "vertex" else None)
    if transport == "vertex":
        model.vertex.headers = lambda: {"Authorization": "Bearer test"}
    session = model.start_session("system")
    assert "".join(session.stream_json("prompt", response_schema={"type": "object"})) == '{"title":"ok"}'
    assert session.last_usage == {"promptTokenCount": 11, "candidatesTokenCount": 3}
    assert session.last_ttft_ms is not None
    assert "?alt=sse" in requests[0].full_url


def test_document_schema_is_sent_to_http_and_typed_reply_replays_offline(monkeypatch, tmp_path):
    from doc2roadmap.application.phase_b.documents import DOCUMENT_SCHEMA
    from doc2roadmap.application.phase_b.lectures import LECTURE_SCHEMA

    typed = {"title": "Tế bào", "markdown": "Tế bào [S1]",
             "citations": [{"label": "S1", "quote": "Tế bào là đơn vị cấu trúc."}],
             "outside_document_blocks": []}
    lecture = {"prereq_notes": [], "explanation": [{"text": "Tế bào là đơn vị cấu trúc.",
                "sources": ["S1"], "quote": "Tế bào là đơn vị cấu trúc.", "outside_document": False}],
               "example": [], "contrasts": [], "gaps": [],
               "self_check": {"question": "Tế bào là gì?", "answer": "Đơn vị cấu trúc.",
                              "sources": ["S1"], "quote": "Tế bào là đơn vị cấu trúc."}}
    def response(payload):
        envelope = {"candidates": [{"finishReason": "STOP",
                                     "content": {"parts": [{"text": json.dumps(payload, ensure_ascii=False)}]}}],
                    "usageMetadata": {"promptTokenCount": 12, "candidatesTokenCount": 9}}
        return _Response([json.dumps(envelope).encode()])
    requests, responses = [], [response(typed), response(lecture)]
    monkeypatch.setattr(phase_b, "urlopen", lambda request, timeout:
                        (requests.append(request) or responses.pop(0)))
    delegate = GeminiToolModel("key", "gemini-test")
    fixture = tmp_path / "typed.json"
    recorded = RecordingToolModel(delegate, fixture, prompt_hash="document-contract")
    session = recorded.start_session("system")
    reply = session.ask_json("prompt", response_schema=DOCUMENT_SCHEMA)
    assert reply.payload == typed
    posted_schema = json.loads(requests[0].data)["generationConfig"]["responseJsonSchema"]
    citation_schema = posted_schema["properties"]["citations"]["items"]
    assert citation_schema["required"] == ["label", "quote"]
    lecture_reply = session.ask_json("lecture", response_schema=LECTURE_SCHEMA)
    assert lecture_reply.payload == lecture
    posted_lecture = json.loads(requests[1].data)["generationConfig"]["responseJsonSchema"]
    explanation_item = posted_lecture["properties"]["explanation"]["items"]
    assert {"text", "sources", "quote", "outside_document"} <= set(explanation_item["required"])
    assert {"question", "answer", "sources", "quote"} <= set(posted_lecture["properties"]["self_check"]["required"])

    replay = ReplayToolModel(fixture, prompt_hash="document-contract")
    replay_session = replay.start_session("system")
    replayed = replay_session.ask_json("prompt", response_schema=DOCUMENT_SCHEMA)
    assert replayed.payload["citations"] == typed["citations"]
    assert replayed.usage == {"promptTokenCount": 12, "candidatesTokenCount": 9}
    assert replay_session.ask_json("lecture", response_schema=LECTURE_SCHEMA).payload == lecture


def test_invalid_json_records_raw_text_usage_and_replays_failure_without_http(monkeypatch, tmp_path):
    envelope = {"candidates": [{"finishReason": "MAX_TOKENS",
                                 "content": {"parts": [{"text": '{"markdown":"cut'}]}}],
                "usageMetadata": {"promptTokenCount": 70, "candidatesTokenCount": 30,
                                  "thoughtsTokenCount": 4}}
    monkeypatch.setattr(phase_b, "urlopen", lambda request, timeout:
                        _Response([json.dumps(envelope).encode()]))
    fixture = tmp_path / "invalid.json"
    recorded = RecordingToolModel(GeminiToolModel("key", "gemini-test"), fixture,
                                  prompt_hash="invalid-response")
    session = recorded.start_session("system")
    with pytest.raises(json.JSONDecodeError):
        session.ask_json("prompt", response_schema={"type": "object"})
    call = json.loads(fixture.read_text(encoding="utf-8"))["sessions"][0]["calls"][0]
    assert call["raw_text"] == '{"markdown":"cut'
    assert call["usage"]["thoughtsTokenCount"] == 4

    def no_http(*args, **kwargs):
        raise AssertionError("replay must not use HTTP")
    monkeypatch.setattr(phase_b, "urlopen", no_http)
    replay_session = ReplayToolModel(fixture, prompt_hash="invalid-response").start_session("system")
    with pytest.raises(json.JSONDecodeError):
        replay_session.ask_json("prompt", response_schema={"type": "object"})
    assert replay_session.last_usage == envelope["usageMetadata"]


def test_tool_declaration_union_schema_is_normalized():
    model = GeminiToolModel("key")
    session = model.start_session("system", [{"name": "f", "parameters": {
        "type": "object", "properties": {"value": {"type": ["string", "array"]}}
    }}])
    assert session.tools[0]["parametersJsonSchema"]["properties"]["value"]["type"] == ["string", "array"]
    assert "parameters" not in session.tools[0]


def test_recorded_json_stream_reads_usage_from_session_not_model(tmp_path):
    class DelegateSession:
        last_usage = {"promptTokenCount": 5, "candidatesTokenCount": 2}
        last_ttft_ms = 17
        last_finish_reason = "STOP"

        def stream_json(self, prompt, *, response_schema):
            yield '{"ok":true}'

    class Delegate:
        model_id = "fake-session-only-usage"

        def start_session(self, system_prompt, tools=()):
            return DelegateSession()

    fixture = tmp_path / "recording.json"
    recorder = RecordingToolModel(Delegate(), fixture, prompt_hash="test-hash")
    session = recorder.start_session("system")
    assert "".join(session.stream_json("prompt", response_schema={"type": "object"})) == '{"ok":true}'
    replay = ReplayToolModel(fixture, prompt_hash="test-hash")
    replay_session = replay.start_session("system")
    assert "".join(replay_session.stream_json("prompt", response_schema={"type": "object"})) == '{"ok":true}'
    assert replay_session.last_usage == {"promptTokenCount": 5, "candidatesTokenCount": 2}
    assert replay_session.last_ttft_ms == 17
    assert replay_session.last_finish_reason == "STOP"
    assert replay.is_replay is True


def test_replay_matches_parallel_sessions_by_prompt_not_start_order(tmp_path):
    class DelegateSession:
        last_usage = {}
        last_ttft_ms = 1

        def __init__(self, reply):
            self.reply = reply

        def stream_json(self, prompt, *, response_schema):
            yield self.reply

    class Delegate:
        model_id = "parallel-fixture"

        def start_session(self, system_prompt, tools=()):
            return DelegateSession("reply-one" if len(sessions) == 0 else "reply-two")

    sessions = []
    delegate = Delegate()
    # Preserve creation order while assigning distinct deterministic replies.
    def start(system_prompt, tools=()):
        reply = "reply-one" if len(sessions) == 0 else "reply-two"
        session = DelegateSession(reply)
        sessions.append(session)
        return session
    delegate.start_session = start

    fixture = tmp_path / "parallel.json"
    recorder = RecordingToolModel(delegate, fixture, prompt_hash="same-contract")
    first = recorder.start_session("system")
    second = recorder.start_session("system")
    assert "".join(first.stream_json("prompt-one", response_schema={"type": "object"})) == "reply-one"
    assert "".join(second.stream_json("prompt-two", response_schema={"type": "object"})) == "reply-two"

    replay = ReplayToolModel(fixture, prompt_hash="same-contract")
    replay_first = replay.start_session("system")
    replay_second = replay.start_session("system")
    assert "".join(replay_second.stream_json("prompt-two", response_schema={"type": "object"})) == "reply-two"
    assert "".join(replay_first.stream_json("prompt-one", response_schema={"type": "object"})) == "reply-one"
