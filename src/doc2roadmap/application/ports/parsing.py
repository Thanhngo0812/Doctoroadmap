from dataclasses import dataclass, field
from typing import Protocol

from doc2roadmap.domain.models import DocumentTree


@dataclass(slots=True)
class ParsedDocument:
    tree: DocumentTree
    images: dict[str, bytes] = field(default_factory=dict)


class DocumentParser(Protocol):
    @property
    def identifier(self) -> str: ...

    @property
    def adapter_version(self) -> int: ...

    @property
    def image_scale(self) -> float: ...

    def parse(self, source: bytes, filename: str) -> ParsedDocument: ...
