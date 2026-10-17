from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Literal, Protocol, TypeVar

T = TypeVar("T")


class PhaseBStore(Protocol):
    """Persistence used by learner-facing Phase B features."""

    def get_cache(self, key: str) -> Any | None: ...

    def put_cache(self, key: str, value: Any) -> None: ...

    def get_record(self, kind: str, record_id: str) -> dict[str, Any] | None: ...

    def put_record(self, kind: str, record_id: str, value: Mapping[str, Any]) -> None: ...

    def list_records(self, kind: str, owner: str | None = None) -> list[dict[str, Any]]: ...

    def append_usage(self, row: Mapping[str, Any]) -> None: ...

    def usage_rows(self, doc_id: str | None = None) -> list[dict[str, Any]]: ...

    def single_flight(self, key: str, generate: Callable[[], T]) -> T: ...


class JsonCallModel(Protocol):
    def ask_json(
        self, prompt: str, *, response_schema: dict[str, Any], system_prompt: str = ""
    ) -> Any: ...


@dataclass(frozen=True, slots=True)
class JsonCallResult:
    payload: dict[str, Any]
    usage: dict[str, Any]
    elapsed_ms: int
    ttft_ms: int | None
    cost_usd: float
    dry_run: bool = False


@dataclass(frozen=True, slots=True)
class Delta:
    text: str


@dataclass(frozen=True, slots=True)
class ToolCall:
    name: str
    args: dict[str, Any]
    call_id: str
    signature: str | None = None


@dataclass(frozen=True, slots=True)
class Done:
    usage: dict[str, Any]
    finish_reason: str | None = None
    turn_id: str | None = None
    ttft_ms: int | None = None


ConversationEvent = Delta | ToolCall | Done


class ToolConversationSession(Protocol):
    def stream(
        self,
        messages: list[dict[str, Any]],
        *,
        mode: Literal["AUTO", "NONE"] = "AUTO",
    ) -> Any: ...
