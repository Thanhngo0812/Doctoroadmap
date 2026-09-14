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


@dataclass(slots=True)
class StoredStageArtifact:
    payload: dict[str, Any]
    version: int
    path: Path
    manifest: dict[str, Any]


class ArtifactStore(Protocol):
    def load_type_aliases(self) -> dict[str, str]: ...

    def load_chunks(self, doc_id: str, version: int) -> StoredChunks: ...

    def load_canonical(self, doc_id: str, version: int) -> StoredStageArtifact: ...

    def load_latest_canonical(self, doc_id: str) -> StoredStageArtifact: ...

    def load_reviewed_node_types(self) -> dict[str, bool]: ...

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

    def load_parse(self, doc_id: str, version: int) -> StoredParse: ...

    def load_image(self, doc_id: str, parse_version: int, image_id: str) -> bytes: ...

    def find_candidates(
        self, doc_id: str, source_hash: str, config_hash: str
    ) -> StoredStageArtifact | None: ...

    def save_candidates(
        self,
        doc_id: str,
        source_hash: str,
        config_hash: str,
        config: dict[str, Any],
        payload: dict[str, Any],
        *,
        upstream_version: int,
        manifest_fields: dict[str, Any] | None = None,
        force_new: bool = False,
    ) -> StoredStageArtifact: ...

    def find_canonical(
        self, doc_id: str, source_hash: str, config_hash: str
    ) -> StoredStageArtifact | None: ...

    def save_canonical(
        self,
        doc_id: str,
        source_hash: str,
        config_hash: str,
        config: dict[str, Any],
        payload: dict[str, Any],
        *,
        upstream_version: int,
        manifest_fields: dict[str, Any] | None = None,
    ) -> StoredStageArtifact: ...

    def find_graph(
        self, doc_id: str, source_hash: str, config_hash: str
    ) -> StoredStageArtifact | None: ...

    def save_graph(
        self,
        doc_id: str,
        source_hash: str,
        config_hash: str,
        config: dict[str, Any],
        payload: dict[str, Any],
        *,
        upstream_version: int,
        manifest_fields: dict[str, Any] | None = None,
    ) -> StoredStageArtifact: ...

    def find_retrieval(
        self, doc_id: str, source_hash: str, config_hash: str
    ) -> StoredStageArtifact | None: ...

    def save_retrieval(
        self,
        doc_id: str,
        source_hash: str,
        config_hash: str,
        config: dict[str, Any],
        payload: dict[str, Any],
        *,
        upstream_version: int,
        manifest_fields: dict[str, Any] | None = None,
    ) -> StoredStageArtifact: ...

    def load_candidates(self, doc_id: str, version: int) -> StoredStageArtifact: ...

    def load_latest_candidates(self, doc_id: str) -> StoredStageArtifact: ...

    def load_latest_retrieval(self, doc_id: str) -> StoredStageArtifact: ...
