from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any, Sequence

from doc2roadmap.application.ports.extraction import (
    ConversationTurn,
    EntityExtractor,
    ExtractionReply,
    ExtractionSession,
    PromptImage,
)


_FIXTURE_VERSION = 1


def _image_to_dict(image: PromptImage) -> dict[str, str]:
    return {
        "image_id": image.image_id,
        "mime_type": image.mime_type,
        "data": base64.b64encode(image.data).decode("ascii"),
    }


def _image_from_dict(value: dict[str, str]) -> PromptImage:
    return PromptImage(
        value["image_id"],
        base64.b64decode(value["data"], validate=True),
        value["mime_type"],
    )


def _turn_to_dict(turn: ConversationTurn) -> dict[str, Any]:
    return {
        "role": turn.role,
        "text": turn.text,
        "images": [_image_to_dict(image) for image in turn.images],
    }


def _turn_from_dict(value: dict[str, Any]) -> ConversationTurn:
    return ConversationTurn(
        value["role"],
        value["text"],
        tuple(_image_from_dict(image) for image in value.get("images", [])),
    )


def _request_dict(
    prompt: str,
    response_schema: dict[str, Any],
    images: Sequence[PromptImage],
) -> dict[str, Any]:
    return {
        "prompt": prompt,
        "response_schema": response_schema,
        "images": [_image_to_dict(image) for image in images],
    }


class RecordingEntityExtractor:
    def __init__(
        self,
        delegate: EntityExtractor,
        path: Path,
        *,
        prompt_hash: str,
    ) -> None:
        self._delegate = delegate
        self._path = path
        self._prompt_hash = prompt_hash

    @property
    def identifier(self) -> str:
        return self._delegate.identifier

    @property
    def model_id(self) -> str:
        return self._delegate.model_id

    def start_session(self, system_prompt: str) -> RecordingExtractionSession:
        return RecordingExtractionSession(self, system_prompt)


class RecordingExtractionSession:
    def __init__(self, recorder: RecordingEntityExtractor, system_prompt: str) -> None:
        self._recorder = recorder
        self._system_prompt = system_prompt
        self._delegate: ExtractionSession = recorder._delegate.start_session(system_prompt)
        self._calls: list[dict[str, Any]] = []

    @property
    def turns(self) -> tuple[ConversationTurn, ...]:
        return self._delegate.turns

    @property
    def call_count(self) -> int:
        return self._delegate.call_count

    @property
    def repair_count(self) -> int:
        return self._delegate.repair_count

    def ask_json(
        self,
        prompt: str,
        *,
        response_schema: dict[str, Any],
        images: Sequence[PromptImage] = (),
    ) -> ExtractionReply:
        images = tuple(images)
        previous_turn_count = len(self._delegate.turns)
        reply = self._delegate.ask_json(
            prompt, response_schema=response_schema, images=images
        )
        self._calls.append(
            {
                "request": _request_dict(prompt, response_schema, images),
                "reply": {
                    "payload": reply.payload,
                    "raw_text": reply.raw_text,
                    "repaired": reply.repaired,
                },
                "new_turns": [
                    _turn_to_dict(turn)
                    for turn in self._delegate.turns[previous_turn_count:]
                ],
            }
        )
        self._write()
        return reply

    def _write(self) -> None:
        value = {
            "fixture_version": _FIXTURE_VERSION,
            "prompt_hash": self._recorder._prompt_hash,
            "identifier": self._recorder.identifier,
            "model_id": self._recorder.model_id,
            "system_prompt": self._system_prompt,
            "calls": self._calls,
        }
        path = self._recorder._path
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, path)


class ReplayEntityExtractor:
    def __init__(self, path: Path, *, prompt_hash: str) -> None:
        try:
            fixture = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"không đọc được fixture hội thoại: {path}") from error
        if fixture.get("fixture_version") != _FIXTURE_VERSION:
            raise ValueError("fixture hội thoại không đúng phiên bản")
        if fixture.get("prompt_hash") != prompt_hash:
            raise ValueError("fixture hội thoại không khớp prompt_hash")
        self._identifier = f"replay:{fixture['identifier']}"
        self._model_id = fixture["model_id"]
        self._system_prompt = fixture["system_prompt"]
        self._calls = fixture["calls"]

    @property
    def identifier(self) -> str:
        return self._identifier

    @property
    def model_id(self) -> str:
        return self._model_id

    def start_session(self, system_prompt: str) -> ReplayExtractionSession:
        if system_prompt != self._system_prompt:
            raise ValueError("fixture hội thoại không khớp system prompt")
        return ReplayExtractionSession(self._calls)


class ReplayExtractionSession:
    def __init__(self, calls: list[dict[str, Any]]) -> None:
        self._calls = calls
        self._index = 0
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

    def ask_json(
        self,
        prompt: str,
        *,
        response_schema: dict[str, Any],
        images: Sequence[PromptImage] = (),
    ) -> ExtractionReply:
        if self._index >= len(self._calls):
            raise RuntimeError("fixture hội thoại đã hết lượt")
        call = self._calls[self._index]
        actual = _request_dict(prompt, response_schema, tuple(images))
        if actual != call["request"]:
            raise ValueError(f"lượt phát lại {self._index + 1} không khớp yêu cầu đã ghi")
        new_turns = [_turn_from_dict(turn) for turn in call["new_turns"]]
        self._turns.extend(new_turns)
        self._call_count += sum(turn.role == "model" for turn in new_turns)
        reply = call["reply"]
        self._repair_count += bool(reply["repaired"])
        self._index += 1
        return ExtractionReply(
            reply["payload"], reply["raw_text"], repaired=reply["repaired"]
        )
