from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from doc2roadmap.domain.models import ChunkingResult, DocumentTree


@dataclass(slots=True)
class StoredParse:
    tree: DocumentTree
    version: int
    path: Path
    manifest: dict[str, Any]


@dataclass(slots=True)
class StoredChunks:
    result: ChunkingResult
    version: int
    path: Path
    manifest: dict[str, Any]


class ArtifactStore(Protocol):
    def find_parse(
        self,
        doc_id: str,
        source_hash: str,
        parser_config_hash: str,
    ) -> StoredParse | None: ...

    def save_parse(
        self,
        doc_id: str,
        source_hash: str,
        parser_config_hash: str,
        config_hash: str,
        config: dict[str, Any],
        tree: DocumentTree,
        images: dict[str, bytes] | None = None,
    ) -> StoredParse: ...

    def save_chunks(
        self,
        doc_id: str,
        source_hash: str,
        config_hash: str,
        config: dict[str, Any],
        parse_version: int,
        result: ChunkingResult,
    ) -> StoredChunks: ...

    def load_latest_chunks(self, doc_id: str) -> StoredChunks: ...
