from dataclasses import dataclass
from typing import Any, Literal, Protocol, Sequence


@dataclass(frozen=True, slots=True)
class PromptImage:
    image_id: str
    data: bytes
    mime_type: str = "image/png"


@dataclass(frozen=True, slots=True)
class ConversationTurn:
    role: Literal["user", "model"]
    text: str
    images: tuple[PromptImage, ...] = ()


class ModelTransportError(RuntimeError):
    """Lỗi đường truyền tới nhà cung cấp mô hình; không phải đầu ra sai."""


@dataclass(frozen=True, slots=True)
class ExtractionReply:
    payload: Any
    raw_text: str
    repaired: bool = False
    usage: dict[str, int] | None = None


class ExtractionSession(Protocol):
    @property
    def turns(self) -> tuple[ConversationTurn, ...]: ...

    @property
    def call_count(self) -> int: ...

    @property
    def repair_count(self) -> int: ...

    def ask_json(
        self,
        prompt: str,
        *,
        response_schema: dict[str, Any],
        images: Sequence[PromptImage] = (),
    ) -> ExtractionReply: ...


class EntityExtractor(Protocol):
    @property
    def identifier(self) -> str: ...

    @property
    def model_id(self) -> str: ...

    def start_session(self, system_prompt: str) -> ExtractionSession: ...
