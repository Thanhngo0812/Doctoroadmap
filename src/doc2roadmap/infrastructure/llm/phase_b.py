from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import threading
from copy import deepcopy
from inspect import signature
from collections.abc import Iterator, Mapping, Sequence
from pathlib import Path
from time import perf_counter, sleep
from typing import Any, Literal
from uuid import uuid4
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from doc2roadmap.application.ports.phase_b import Delta, Done, ToolCall
from doc2roadmap.application.ports.extraction import ExtractionReply
from doc2roadmap.infrastructure.google_auth import VertexCredentials


_DEV = "https://generativelanguage.googleapis.com/v1beta/models/{model}:{operation}"
_MODEL_ID = re.compile(r"^[A-Za-z0-9._-]+$")


class GeminiToolModel:
    """Gemini Developer API / Vertex adapter for JSON streams and tool turns."""

    def __init__(
        self,
        api_key: str | None,
        model_id: str = "gemini-3.1-flash-lite",
        *,
        transport: Literal["developer_api", "vertex"] = "developer_api",
        vertex_project: str | None = None,
        vertex_location: str = "global",
        temperature: float = 0.0,
        max_output_tokens: int = 2048,
        timeout_seconds: float = 60,
        vertex_credentials: VertexCredentials | None = None,
    ) -> None:
        if transport == "developer_api" and not (api_key and api_key.strip()):
            raise ValueError("missing Gemini API key")
        if transport not in {"developer_api", "vertex"}:
            raise ValueError("invalid Gemini transport")
        if not _MODEL_ID.fullmatch(model_id) or max_output_tokens < 1 or timeout_seconds <= 0:
            raise ValueError("invalid Gemini model settings")
        self.api_key = api_key
        self.model_id = model_id
        self.transport = transport
        # A runtime passes one shared credentials object so every client reuses the same token.
        self.vertex = (vertex_credentials or VertexCredentials(vertex_project or "", vertex_location)
                       ) if transport == "vertex" else None
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.timeout_seconds = timeout_seconds
        self.last_usage: dict[str, Any] = {}

    def start_session(self, system_prompt: str, tools: Sequence[Mapping[str, Any]] = ()) -> GeminiToolSession:
        return GeminiToolSession(self, system_prompt, [_normalize_function_schema(tool) for tool in tools])

    def ask_json(self, prompt: str, *, response_schema: dict[str, Any], system_prompt: str = "") -> ExtractionReply:
        return self.start_session(system_prompt).ask_json(prompt, response_schema=response_schema)

    def _request(self, operation: str, body: Mapping[str, Any], *, stream: bool,
                 retries: int = 2, timeout_seconds: float | None = None) -> Any:
        if self.vertex:
            url = self.vertex.url(self.model_id, operation)
            if stream:
                url += "?alt=sse"
            headers = self.vertex.headers()
        else:
            url = _DEV.format(model=self.model_id, operation=operation)
            if stream:
                url += "?alt=sse"
            headers = {"x-goog-api-key": self.api_key or ""}
        request = Request(
            url,
            data=json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8"),
            headers={"Content-Type": "application/json", **headers},
            method="POST",
        )
        if retries < 0:
            raise ValueError("retries must be non-negative")
        timeout = self.timeout_seconds if timeout_seconds is None else timeout_seconds
        for attempt in range(retries + 1):
            try:
                return urlopen(request, timeout=timeout)
            except HTTPError as error:
                if error.code not in {429, 503} or attempt == retries:
                    raise RuntimeError("Gemini request failed") from error
            except (URLError, OSError) as error:
                if attempt == retries:
                    raise RuntimeError("Gemini request failed") from error
            sleep(2**attempt)
        raise AssertionError("unreachable")

    @staticmethod
    def _decode_sse(response: Any) -> Iterator[dict[str, Any]]:
        data: list[str] = []
        for raw_line in response:
            line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
            line = line.rstrip("\r\n")
            if not line:
                if data:
                    value = "\n".join(data)
                    data.clear()
                    if value != "[DONE]":
                        yield json.loads(value)
                continue
            if line.startswith("data:"):
                data.append(line[5:].lstrip())
        if data:
            value = "\n".join(data)
            if value != "[DONE]":
                yield json.loads(value)


class GeminiToolSession:
    def __init__(self, model: GeminiToolModel, system_prompt: str, tools: list[Mapping[str, Any]]) -> None:
        self.model = model
        self.system_prompt = system_prompt
        self.tools = tools
        # Full provider parts, including thought signatures, remain opaque here.
        self._call_parts: dict[str, dict[str, Any]] = {}
        self._call_turns: dict[str, str] = {}
        self._turn_parts: dict[str, list[dict[str, Any]]] = {}
        self.last_usage: dict[str, Any] = {}
        self.last_raw_text: str | None = None
        self.last_finish_reason: str | None = None

    def ask_json(self, prompt: str, *, response_schema: dict[str, Any]) -> ExtractionReply:
        started = perf_counter()
        self.last_ttft_ms = None
        self.last_usage = {}
        self.last_raw_text = None
        self.last_finish_reason = None
        body = {
            "systemInstruction": {"parts": [{"text": self.system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": self.model.temperature,
                "maxOutputTokens": self.model.max_output_tokens,
                "responseMimeType": "application/json",
                "responseJsonSchema": response_schema,
            },
        }
        response = self.model._request("generateContent", body, stream=False)
        try:
            first = response.read(1)
            if first:
                self.last_ttft_ms = round((perf_counter() - started) * 1000)
            payload = json.loads(first + response.read())
        finally:
            response.close()
        self.last_usage = dict(payload.get("usageMetadata", {}))
        self.model.last_usage = dict(self.last_usage)
        candidates = payload.get("candidates", [{}])
        candidate = candidates[0] if candidates else {}
        self.last_finish_reason = candidate.get("finishReason")
        parts = candidate.get("content", {}).get("parts", [])
        raw_text = "".join(str(part.get("text", "")) for part in parts)
        self.last_raw_text = raw_text
        if not raw_text:
            raise RuntimeError("Gemini returned no JSON text")
        value = json.loads(raw_text)
        return ExtractionReply(value, raw_text, usage=self.last_usage)

    def stream_json(self, prompt: str, *, response_schema: dict[str, Any],
                    temperature: float | None = None, transport_retries: int | None = None,
                    timeout_seconds: float | None = None) -> Iterator[str]:
        body = {
            "systemInstruction": {"parts": [{"text": self.system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": self.model.temperature if temperature is None else temperature,
                "maxOutputTokens": self.model.max_output_tokens,
                "responseMimeType": "application/json",
                "responseJsonSchema": response_schema,
            },
        }
        started = perf_counter()
        self.last_ttft_ms = None
        self.last_usage = {}
        self.last_finish_reason = None
        response = self.model._request(
            "streamGenerateContent", body, stream=True,
            retries=2 if transport_retries is None else transport_retries,
            timeout_seconds=timeout_seconds,
        )
        try:
            for event in self.model._decode_sse(response):
                self.last_usage.update(event.get("usageMetadata", {}))
                candidates = event.get("candidates", [])
                if candidates:
                    self.last_finish_reason = candidates[0].get("finishReason", self.last_finish_reason)
                for part in (candidates[0].get("content", {}).get("parts", []) if candidates else []):
                    if isinstance(part.get("text"), str) and part['text']:
                        if self.last_ttft_ms is None:
                            self.last_ttft_ms = round((perf_counter() - started) * 1000)
                        yield part["text"]
        finally:
            self.model.last_usage = dict(self.last_usage)
            response.close()

    def stream_text(self, prompt: str, *, images: Sequence[tuple[int, bytes]] = (),
                    temperature: float | None = None, transport_retries: int | None = None,
                    timeout_seconds: float | None = None) -> Iterator[str]:
        """Plain-text stream (no JSON schema). Each image is a (page, JPEG bytes) pair sent after the prompt."""
        parts: list[dict[str, Any]] = [{"text": prompt}]
        for page, data in images:
            parts += [{"text": f"Ảnh trang {page} của sách:"},
                      {"inlineData": {"mimeType": "image/jpeg", "data": base64.b64encode(data).decode("ascii")}}]
        body = {
            "systemInstruction": {"parts": [{"text": self.system_prompt}]},
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {
                "temperature": self.model.temperature if temperature is None else temperature,
                "maxOutputTokens": self.model.max_output_tokens,
            },
        }
        started = perf_counter()
        self.last_ttft_ms = None
        self.last_usage = {}
        self.last_finish_reason = None
        response = self.model._request(
            "streamGenerateContent", body, stream=True,
            retries=2 if transport_retries is None else transport_retries, timeout_seconds=timeout_seconds)
        try:
            for event in self.model._decode_sse(response):
                self.last_usage.update(event.get("usageMetadata", {}))
                candidates = event.get("candidates", [])
                if candidates:
                    self.last_finish_reason = candidates[0].get("finishReason", self.last_finish_reason)
                for part in (candidates[0].get("content", {}).get("parts", []) if candidates else []):
                    if isinstance(part.get("text"), str) and part["text"] and not part.get("thought"):
                        if self.last_ttft_ms is None:
                            self.last_ttft_ms = round((perf_counter() - started) * 1000)
                        yield part["text"]
        finally:
            self.model.last_usage = dict(self.last_usage)
            response.close()

    def stream(
        self,
        messages: list[dict[str, Any]],
        *,
        mode: Literal["AUTO", "NONE"] = "AUTO",
    ) -> Iterator[Delta | ToolCall | Done]:
        contents = self._contents(messages)
        body: dict[str, Any] = {
            "systemInstruction": {"parts": [{"text": self.system_prompt}]},
            "contents": contents,
            "generationConfig": {
                "temperature": self.model.temperature,
                "maxOutputTokens": self.model.max_output_tokens,
            },
        }
        if self.tools:
            body["tools"] = [{"functionDeclarations": self.tools}]
            body["toolConfig"] = {"functionCallingConfig": {"mode": mode}}
        started = perf_counter()
        self.last_ttft_ms = None
        response = self.model._request("streamGenerateContent", body, stream=True)
        usage: dict[str, Any] = {}
        finish_reason = None
        ttft_ms = None
        turn_id = uuid4().hex
        turn_parts: list[dict[str, Any]] = []
        try:
            for event in self.model._decode_sse(response):
                usage.update(event.get("usageMetadata", {}))
                candidates = event.get("candidates", [])
                if not candidates:
                    continue
                candidate = candidates[0]
                finish_reason = candidate.get("finishReason", finish_reason)
                for part in candidate.get("content", {}).get("parts", []):
                    turn_parts.append(dict(part))
                    if "functionCall" in part:
                        if ttft_ms is None:
                            ttft_ms = round((perf_counter() - started) * 1000)
                            self.last_ttft_ms = ttft_ms
                        function = part["functionCall"]
                        call_id = str(function.get("id") or part.get("id") or f"call_{len(self._call_parts) + 1}")
                        self._call_parts[call_id] = dict(part)
                        self._call_turns[call_id] = turn_id
                        yield ToolCall(
                            str(function.get("name", "")),
                            dict(function.get("args", {})),
                            call_id,
                            None,
                        )
                    elif isinstance(part.get("text"), str) and part["text"]:
                        if ttft_ms is None:
                            ttft_ms = round((perf_counter() - started) * 1000)
                            self.last_ttft_ms = ttft_ms
                        yield Delta(part["text"])
            self._turn_parts[turn_id] = turn_parts
            self.model.last_usage = usage
            yield Done(usage, finish_reason, turn_id, ttft_ms)
        finally:
            response.close()

    def _contents(self, messages: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
        contents: list[dict[str, Any]] = []
        for message in messages:
            role = message.get("role")
            if role == "user":
                parts = [{"text": str(message.get("text", ""))}]
                for page, data in message.get("images", ()):
                    parts += [{"text": f"Ảnh trang {page} của sách:"},
                              {"inlineData": {"mimeType": "image/jpeg", "data": base64.b64encode(data).decode("ascii")}}]
                contents.append({"role": "user", "parts": parts})
            elif role == "model":
                parts = []
                turn_id = message.get("turn_id")
                if not turn_id:
                    calls = message.get("calls", [])
                    if calls:
                        turn_id = self._call_turns.get(str(calls[0].get("call_id")))
                if turn_id:
                    contents.append({"role": "model", "parts": self._turn_parts[str(turn_id)]})
                    continue
                text = message.get("text")
                if text:
                    parts.append({"text": str(text)})
                for call in message.get("calls", []):
                    call_id = str(call["call_id"])
                    # Sending the exact provider part preserves Gemini's opaque signature.
                    parts.append(self._call_parts[call_id])
                contents.append({"role": "model", "parts": parts})
            elif role == "tool":
                parts = []
                for result in message.get("tool_results", []):
                    parts.append({"functionResponse": {
                            "name": result["name"],
                            "response": {"result": result.get("result")},
                            "id": result["call_id"],
                        }})
                if parts:
                    contents.append({"role": "user", "parts": parts})
            else:
                raise ValueError(f"unsupported conversation role: {role}")
        return contents


class RecordingToolModel:
    """Record completed JSON and conversation streams for offline replay."""

    def __init__(self, delegate: Any, path: Path | str, *, prompt_hash: str) -> None:
        self.delegate = delegate
        self.path = Path(path)
        self.prompt_hash = prompt_hash
        self.model_id = getattr(delegate, "model_id", "unknown")
        self._sessions: list[RecordingToolSession] = []
        self._lock = threading.RLock()

    def start_session(self, system_prompt: str, tools: Sequence[Mapping[str, Any]] = ()) -> RecordingToolSession:
        session = RecordingToolSession(self, system_prompt, list(tools), self.delegate.start_session(system_prompt, tools))
        with self._lock:
            self._sessions.append(session)
        return session

    def _write(self) -> None:
        with self._lock:
            value = {"fixture_version": 1, "prompt_hash": self.prompt_hash,
                     "model_id": self.model_id, "sessions": [session.fixture() for session in self._sessions]}
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix(self.path.suffix + f".{uuid4().hex}.tmp")
            temporary.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            os.replace(temporary, self.path)


class RecordingToolSession:
    def __init__(self, recorder: RecordingToolModel, system_prompt: str, tools: list[Mapping[str, Any]], delegate: Any) -> None:
        self.recorder, self.system_prompt, self.tools, self.delegate = recorder, system_prompt, tools, delegate
        self.calls: list[dict[str, Any]] = []
        self._lock = threading.RLock()

    def _record(self, call: dict[str, Any]) -> None:
        with self.recorder._lock, self._lock:
            self.calls.append(call)
            self.recorder._write()

    @property
    def last_usage(self) -> dict[str, Any]:
        return dict(getattr(self.delegate, "last_usage", {}) or {})

    @property
    def last_ttft_ms(self) -> int | None:
        return getattr(self.delegate, "last_ttft_ms", None)

    @property
    def last_finish_reason(self) -> str | None:
        return getattr(self.delegate, "last_finish_reason", None)

    def ask_json(self, prompt: str, *, response_schema: dict[str, Any]) -> Any:
        try:
            reply = self.delegate.ask_json(prompt, response_schema=response_schema)
        except Exception as error:
            raw_text = getattr(self.delegate, "last_raw_text", None)
            usage = dict(getattr(self.delegate, "last_usage", {}) or {})
            self._record({"kind": "json", "prompt": prompt, "schema": response_schema,
                          "error": {"type": type(error).__name__,
                                    "pos": getattr(error, "pos", None)},
                          "raw_text": raw_text, "usage": usage,
                          "finish_reason": getattr(self.delegate, "last_finish_reason", None),
                          "ttft_ms": self.last_ttft_ms})
            raise
        self._record({"kind": "json", "prompt": prompt, "schema": response_schema, "ttft_ms": self.last_ttft_ms,
                      "reply": {"payload": reply.payload, "raw_text": reply.raw_text,
                                "usage": reply.usage or {}}})
        return reply

    def stream_json(self, prompt: str, *, response_schema: dict[str, Any],
                    temperature: float | None = None, transport_retries: int | None = None,
                    timeout_seconds: float | None = None) -> Iterator[str]:
        chunks = []
        options = {"temperature": temperature, "transport_retries": transport_retries,
                   "timeout_seconds": timeout_seconds}
        try:
            try:
                supported = signature(self.delegate.stream_json).parameters
            except (TypeError, ValueError):
                supported = {}
            forwarded = {key: value for key, value in options.items()
                         if key in supported and value is not None}
            for chunk in self.delegate.stream_json(prompt, response_schema=response_schema, **forwarded):
                chunks.append(chunk)
                yield chunk
        except BaseException as error:
            self._record({"kind": "json_stream", "prompt": prompt, "schema": response_schema,
                          "options": options, "chunks": chunks, "usage": self.last_usage,
                          "ttft_ms": self.last_ttft_ms, "finish_reason": self.last_finish_reason,
                          "error": {"type": type(error).__name__}})
            raise
        self._record({"kind": "json_stream", "prompt": prompt, "schema": response_schema,
                      "options": options, "chunks": chunks, "usage": self.last_usage,
                      "ttft_ms": self.last_ttft_ms, "finish_reason": self.last_finish_reason})

    def stream_text(self, prompt: str, *, images: Sequence[tuple[int, bytes]] = (),
                    temperature: float | None = None, transport_retries: int | None = None,
                    timeout_seconds: float | None = None) -> Iterator[str]:
        chunks = []
        options = {"temperature": temperature, "transport_retries": transport_retries,
                   "timeout_seconds": timeout_seconds}
        pictures = _picture_ids(images)
        try:
            for chunk in self.delegate.stream_text(prompt, images=images, **{
                    key: value for key, value in options.items() if value is not None}):
                chunks.append(chunk)
                yield chunk
        except BaseException as error:
            self._record({"kind": "text_stream", "prompt": prompt, "images": pictures, "options": options,
                          "chunks": chunks, "usage": self.last_usage, "ttft_ms": self.last_ttft_ms,
                          "finish_reason": self.last_finish_reason, "error": {"type": type(error).__name__}})
            raise
        self._record({"kind": "text_stream", "prompt": prompt, "images": pictures, "options": options,
                      "chunks": chunks, "usage": self.last_usage, "ttft_ms": self.last_ttft_ms,
                      "finish_reason": self.last_finish_reason})

    def stream(self, messages: list[dict[str, Any]], *, mode: Literal["AUTO", "NONE"] = "AUTO") -> Iterator[Delta | ToolCall | Done]:
        # The caller extends `messages` after this call; record what was sent now.
        snapshot = _wire_messages(messages)
        events = []
        for event in self.delegate.stream(messages, mode=mode):
            events.append(_event_dict(event))
            yield event
        self._record({"kind": "conversation", "messages": snapshot, "mode": mode, "events": events})

    def fixture(self) -> dict[str, Any]:
        return {"system_prompt": self.system_prompt, "tools": self.tools, "calls": self.calls}


class ReplayToolModel:
    def __init__(self, path: Path | str, *, prompt_hash: str) -> None:
        fixture = json.loads(Path(path).read_text(encoding="utf-8"))
        if fixture.get("fixture_version") != 1 or fixture.get("prompt_hash") != prompt_hash:
            raise ValueError("tool replay fixture version or prompt hash does not match")
        self.model_id = fixture["model_id"]
        self._sessions = fixture["sessions"]
        self.is_replay = True
        self._reserved: set[int] = set()
        self._lock = threading.Lock()

    def start_session(self, system_prompt: str, tools: Sequence[Mapping[str, Any]] = ()) -> ReplayToolSession:
        return ReplayToolSession(self, system_prompt, list(tools))


class ReplayToolSession:
    def __init__(self, model: ReplayToolModel, system_prompt: str, tools: list[Mapping[str, Any]]) -> None:
        self.model, self.system_prompt, self.tools = model, system_prompt, tools
        self.calls: list[dict[str, Any]] | None = None
        self.index = 0
        self.last_usage: dict[str, Any] = {}
        self.last_ttft_ms: int | None = None
        self.last_finish_reason: str | None = None

    def _take(self, kind: str, actual: dict[str, Any]) -> dict[str, Any]:
        if self.calls is None:
            with self.model._lock:
                for index, fixture in enumerate(self.model._sessions):
                    if index in self.model._reserved:
                        continue
                    if fixture["system_prompt"] != self.system_prompt or fixture["tools"] != self.tools:
                        continue
                    calls = fixture["calls"]
                    if not calls or calls[0]["kind"] != kind:
                        continue
                    if {key: calls[0][key] for key in actual} != actual:
                        continue
                    self.model._reserved.add(index)
                    self.calls = calls
                    break
            if self.calls is None:
                raise ValueError("tool replay has no unused session matching this request")
        if self.index >= len(self.calls):
            raise RuntimeError("tool replay fixture has no remaining calls")
        call = self.calls[self.index]
        if call["kind"] != kind or {key: call[key] for key in actual} != actual:
            raise ValueError(f"tool replay call {self.index + 1} does not match")
        self.index += 1
        return call

    def ask_json(self, prompt: str, *, response_schema: dict[str, Any]) -> ExtractionReply:
        call = self._take("json", {"prompt": prompt, "schema": response_schema})
        self.last_ttft_ms = call.get('ttft_ms')
        if "error" in call:
            self.last_usage = dict(call.get("usage", {}))
            self.last_raw_text = call.get("raw_text")
            self.last_finish_reason = call.get("finish_reason")
            if call["error"].get("type") == "JSONDecodeError":
                raw_text = self.last_raw_text or ""
                raise json.JSONDecodeError("recorded invalid JSON", raw_text,
                                           int(call["error"].get("pos") or 0))
            raise RuntimeError(f"recorded JSON call failed: {call['error'].get('type', 'error')}")
        reply = call["reply"]
        self.last_usage = reply.get("usage", {})
        return ExtractionReply(reply["payload"], reply["raw_text"], usage=self.last_usage)

    def stream_json(self, prompt: str, *, response_schema: dict[str, Any],
                    temperature: float | None = None, transport_retries: int | None = None,
                    timeout_seconds: float | None = None) -> Iterator[str]:
        options = {"temperature": temperature, "transport_retries": transport_retries,
                   "timeout_seconds": timeout_seconds}
        call = self._take("json_stream", {"prompt": prompt, "schema": response_schema})
        recorded_options = call.get("options")
        # A click's remaining timeout varies with CPU/IO time; replay does no IO.
        # Sampling temperature and retry policy still have to match the recording.
        if recorded_options is not None and any(recorded_options.get(key) != options[key]
                                                for key in ('temperature', 'transport_retries')):
            raise ValueError("tool replay stream options do not match")
        self.last_usage = call.get("usage", {})
        self.last_ttft_ms = call.get("ttft_ms")
        self.last_finish_reason = call.get("finish_reason")
        yield from call["chunks"]
        if "error" in call:
            raise RuntimeError(f"recorded JSON stream failed: {call['error'].get('type', 'error')}")

    def stream_text(self, prompt: str, *, images: Sequence[tuple[int, bytes]] = (),
                    temperature: float | None = None, transport_retries: int | None = None,
                    timeout_seconds: float | None = None) -> Iterator[str]:
        options = {"temperature": temperature, "transport_retries": transport_retries}
        call = self._take("text_stream", {"prompt": prompt, "images": _picture_ids(images)})
        recorded = call.get("options") or {}
        if any(recorded.get(key) != value for key, value in options.items()):
            raise ValueError("tool replay stream options do not match")
        self.last_usage = call.get("usage", {})
        self.last_ttft_ms = call.get("ttft_ms")
        self.last_finish_reason = call.get("finish_reason")
        yield from call["chunks"]
        if "error" in call:
            raise RuntimeError(f"recorded text stream failed: {call['error'].get('type', 'error')}")

    def stream(self, messages: list[dict[str, Any]], *, mode: Literal["AUTO", "NONE"] = "AUTO") -> Iterator[Delta | ToolCall | Done]:
        call = self._take("conversation", {"messages": _wire_messages(messages), "mode": mode})
        for event in call["events"]:
            parsed = _event_from_dict(event)
            if isinstance(parsed, Done):
                self.last_usage = dict(parsed.usage)
                self.last_ttft_ms = parsed.ttft_ms
            yield parsed


def _picture_ids(images: Sequence[tuple[int, bytes]]) -> list[list[Any]]:
    return [[page, hashlib.sha256(data).hexdigest()] for page, data in images]


def _wire_messages(messages: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Messages as recorded: page pictures become (page, sha256) pairs so fixtures stay JSON and small."""
    wire = deepcopy([{key: value for key, value in message.items() if key != "images"} for message in messages])
    for row, message in zip(wire, messages):
        if message.get("images"):
            row["images"] = _picture_ids(message["images"])
    return wire


def _event_dict(event: Delta | ToolCall | Done) -> dict[str, Any]:
    if isinstance(event, Delta):
        return {"type": "delta", "text": event.text}
    if isinstance(event, ToolCall):
        return {"type": "tool_call", "name": event.name, "args": event.args,
                "call_id": event.call_id, "signature": event.signature}
    return {"type": "done", "usage": event.usage, "finish_reason": event.finish_reason,
            "turn_id": event.turn_id, "ttft_ms": event.ttft_ms}


def _event_from_dict(value: Mapping[str, Any]) -> Delta | ToolCall | Done:
    if value["type"] == "delta":
        return Delta(value["text"])
    if value["type"] == "tool_call":
        return ToolCall(value["name"], value["args"], value["call_id"], value.get("signature"))
    return Done(value.get("usage", {}), value.get("finish_reason"), value.get("turn_id"), value.get("ttft_ms"))


def _normalize_function_schema(value: Mapping[str, Any]) -> dict[str, Any]:
    declaration = dict(value)
    parameters = declaration.get("parameters")
    if isinstance(parameters, Mapping) and _has_union_type(parameters):
        declaration["parametersJsonSchema"] = parameters
        declaration.pop("parameters", None)
    return declaration


def _has_union_type(value: Any) -> bool:
    if isinstance(value, Mapping):
        if isinstance(value.get("type"), list) or "anyOf" in value or "oneOf" in value:
            return True
        return any(_has_union_type(child) for child in value.values())
    if isinstance(value, list):
        return any(_has_union_type(child) for child in value)
    return False
