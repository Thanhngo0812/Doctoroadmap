from __future__ import annotations

import base64
import json
import re
from random import random
from time import sleep
from typing import Any, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from doc2roadmap.application.ports.extraction import (
    ConversationTurn,
    ExtractionReply,
    ModelTransportError,
    PromptImage,
)


DEFAULT_MODEL_ID = "gemini-3.1-flash-lite"
_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
_MODEL_ID = re.compile(r"^[A-Za-z0-9._-]+$")
_RETRYABLE_HTTP = {408, 429, 500, 502, 503, 504}
class MalformedModelResponse(ValueError):
    def __init__(self, message: str, raw_text: str) -> None:
        super().__init__(message)
        self.raw_text = raw_text


class GeminiEntityExtractor:
    def __init__(
        self,
        api_key: str,
        model_id: str = DEFAULT_MODEL_ID,
        *,
        timeout_seconds: float = 120,
        max_retries: int = 3,
        temperature: float = 0,
        max_output_tokens: int = 8192,
    ) -> None:
        if not api_key.strip():
            raise ValueError("thiếu DOC2ROADMAP_GEMINI_API_KEY")
        if not _MODEL_ID.fullmatch(model_id):
            raise ValueError("Gemini model_id không hợp lệ")
        if timeout_seconds <= 0:
            raise ValueError("Gemini timeout phải lớn hơn 0")
        if max_retries < 0:
            raise ValueError("Gemini max_retries không được âm")
        if temperature < 0:
            raise ValueError("Gemini temperature không được âm")
        if max_output_tokens <= 0:
            raise ValueError("Gemini max_output_tokens phải lớn hơn 0")
        self._api_key = api_key
        self._model_id = model_id
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self._temperature = temperature
        self._max_output_tokens = max_output_tokens

    @property
    def identifier(self) -> str:
        return "gemini-generate-content-rest:v1beta"

    @property
    def model_id(self) -> str:
        return self._model_id

    def start_session(self, system_prompt: str) -> GeminiExtractionSession:
        return GeminiExtractionSession(self, system_prompt)

    @staticmethod
    def _parts(turn: ConversationTurn) -> list[dict[str, Any]]:
        parts: list[dict[str, Any]] = [{"text": turn.text}]
        for image in turn.images:
            parts.extend((
                {"text": f"MEDIA_ID: {image.image_id}"},
                {
                "inlineData": {
                    "mimeType": image.mime_type,
                    "data": base64.b64encode(image.data).decode("ascii"),
                }
                },
            ))
        return parts

    def _complete(
        self,
        system_prompt: str,
        turns: Sequence[ConversationTurn],
        response_schema: dict[str, Any],
    ) -> str:
        body = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [
                {"role": turn.role, "parts": self._parts(turn)} for turn in turns
            ],
            "generationConfig": {
                "temperature": self._temperature,
                "maxOutputTokens": self._max_output_tokens,
                "responseMimeType": "application/json",
                "responseJsonSchema": response_schema,
            },
        }
        request = Request(
            _ENDPOINT.format(model=self._model_id),
            data=json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode(),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self._api_key,
            },
            method="POST",
        )
        response = self._post(request)
        try:
            payload = json.loads(response)
            candidates = payload["candidates"]
            parts = candidates[0]["content"]["parts"]
            text = "".join(part.get("text", "") for part in parts)
            if not text:
                raise KeyError("text")
            return text
        except (json.JSONDecodeError, KeyError, IndexError, TypeError) as error:
            raise RuntimeError("Gemini trả phản hồi không có nội dung văn bản") from error

    def _post(self, request: Request) -> bytes:
        attempts = self._max_retries + 1
        for attempt in range(attempts):
            try:
                with urlopen(request, timeout=self._timeout_seconds) as response:
                    return response.read()
            except HTTPError as error:
                if error.code not in _RETRYABLE_HTTP:
                    raise ModelTransportError(f"Gemini API trả HTTP {error.code}") from error
                failure: Exception = error
            except (URLError, TimeoutError) as error:
                failure = error
            if attempt == attempts - 1:
                raise ModelTransportError(
                    f"Gemini API lỗi tạm thời sau {attempts} lần thử"
                ) from failure
            sleep(2**attempt + random())
        raise AssertionError("unreachable")


class GeminiExtractionSession:
    def __init__(self, extractor: GeminiEntityExtractor, system_prompt: str) -> None:
        self._extractor = extractor
        self._system_prompt = system_prompt
        self._turns: list[ConversationTurn] = []
        self._call_count = 0
        self._repair_count = 0

    @property
    def turns(self) -> tuple[ConversationTurn, ...]:
        return tuple(self._turns)

    @property
    def call_count(self) -> int:
        return self._call_count

    @property
    def repair_count(self) -> int:
        return self._repair_count

    def _ask_raw(self, response_schema: dict[str, Any]) -> str:
        self._call_count += 1
        raw_text = self._extractor._complete(
            self._system_prompt, self._turns, response_schema
        )
        self._turns.append(ConversationTurn("model", raw_text))
        return raw_text

    @staticmethod
    def _decode(raw_text: str) -> Any:
        return json.loads(raw_text)

    def ask_json(
        self,
        prompt: str,
        *,
        response_schema: dict[str, Any],
        images: Sequence[PromptImage] = (),
    ) -> ExtractionReply:
        self._turns.append(ConversationTurn("user", prompt, tuple(images)))
        raw_text = self._ask_raw(response_schema)
        try:
            return ExtractionReply(self._decode(raw_text), raw_text)
        except json.JSONDecodeError as error:
            self._repair_count += 1
            self._turns.append(
                ConversationTurn(
                    "user",
                    "JSON không hợp lệ: "
                    f"{error.msg} ở dòng {error.lineno}, cột {error.colno}. "
                    "Chỉ sửa định dạng và trả đúng một giá trị JSON theo schema đã yêu cầu.",
                )
            )
            repaired_text = self._ask_raw(response_schema)
            try:
                return ExtractionReply(
                    self._decode(repaired_text), repaired_text, repaired=True
                )
            except json.JSONDecodeError as repaired_error:
                raise MalformedModelResponse(
                    "Gemini vẫn trả JSON không hợp lệ sau một lượt sửa", repaired_text
                ) from repaired_error
