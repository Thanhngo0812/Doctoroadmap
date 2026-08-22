from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class TextSpan:
    start: int
    end: int


class TokenCounter(Protocol):
    @property
    def identifier(self) -> str: ...

    def count(self, text: str) -> int: ...


class SentenceSplitter(Protocol):
    def split(self, text: str) -> list[TextSpan]: ...

