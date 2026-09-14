from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol, Sequence


EmbeddingTask = Literal[
    "RETRIEVAL_DOCUMENT",
    "RETRIEVAL_QUERY",
    "SEMANTIC_SIMILARITY",
]


@dataclass(frozen=True, slots=True)
class EmbeddingRequest:
    text: str
    task_type: EmbeddingTask = "RETRIEVAL_DOCUMENT"


class EmbeddingPort(Protocol):
    @property
    def identifier(self) -> str: ...

    @property
    def embedding_model_id(self) -> str: ...

    def embed(self, requests: Sequence[EmbeddingRequest]) -> list[list[float]]: ...
