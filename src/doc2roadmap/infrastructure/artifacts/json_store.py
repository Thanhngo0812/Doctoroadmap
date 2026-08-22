from __future__ import annotations

import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from doc2roadmap.application.ports import StoredChunks, StoredParse
from doc2roadmap.domain.models import Chunk, ChunkingResult, DocumentTree, Section


_VERSION = re.compile(r"^v(\d+)$")
_IMAGE_ID = re.compile(r"^[0-9a-f]{64}$")


class JsonArtifactStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    @staticmethod
    def _read(path: Path) -> Any:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    @staticmethod
    def _write(path: Path, value: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write("\n")
        os.replace(temporary, path)

    @staticmethod
    def _write_bytes(path: Path, value: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_bytes(value)
        os.replace(temporary, path)

    def _versions(self, artifact: str, doc_id: str) -> list[tuple[int, Path]]:
        base = self.root / artifact / doc_id
        if not base.exists():
            return []
        versions = []
        for path in base.iterdir():
            match = _VERSION.fullmatch(path.name)
            if match and path.is_dir():
                versions.append((int(match.group(1)), path))
        return sorted(versions)

    @staticmethod
    def _manifest(
        artifact_type: str,
        version: int,
        doc_id: str,
        source_hash: str,
        config_hash: str,
        config: dict[str, Any],
        **extra: Any,
    ) -> dict[str, Any]:
        return {
            "artifact_type": artifact_type,
            "version": version,
            "doc_id": doc_id,
            "source_hash": source_hash,
            "config_hash": config_hash,
            "config": config,
            "created_at": datetime.now(UTC).isoformat(),
            **extra,
        }

    def find_parse(
        self,
        doc_id: str,
        source_hash: str,
        parser_config_hash: str,
    ) -> StoredParse | None:
        for version, path in reversed(self._versions("parse_tree", doc_id)):
            manifest = self._read(path / "manifest.json")
            if (
                manifest["source_hash"] == source_hash
                and manifest["parser_config_hash"] == parser_config_hash
            ):
                return StoredParse(
                    tree=DocumentTree.from_dict(self._read(path / "tree.json")),
                    version=version,
                    path=path,
                    manifest=manifest,
                )
        return None

    def save_parse(
        self,
        doc_id: str,
        source_hash: str,
        parser_config_hash: str,
        config_hash: str,
        config: dict[str, Any],
        tree: DocumentTree,
        images: dict[str, bytes] | None = None,
    ) -> StoredParse:
        images = images or {}
        existing = self.find_parse(doc_id, source_hash, parser_config_hash)
        if existing:
            return existing
        if any(not _IMAGE_ID.fullmatch(image_id) for image_id in images):
            raise ValueError("image_id phải là SHA-256 viết thường")
        versions = self._versions("parse_tree", doc_id)
        version = versions[-1][0] + 1 if versions else 1
        path = self.root / "parse_tree" / doc_id / f"v{version}"
        manifest = self._manifest(
            "parse_tree",
            version,
            doc_id,
            source_hash,
            config_hash,
            config,
            parser_config_hash=parser_config_hash,
            parse_stats=tree.parse_stats,
        )
        for image_id, image in sorted(images.items()):
            self._write_bytes(path / "images" / f"{image_id}.png", image)
        self._write(path / "tree.json", tree.to_dict())
        self._write(path / "manifest.json", manifest)
        return StoredParse(tree=tree, version=version, path=path, manifest=manifest)

    def _stored_chunks(self, version: int, path: Path) -> StoredChunks:
        manifest = self._read(path / "manifest.json")
        sections = [Section.from_dict(item) for item in self._read(path / "sections.json")]
        chunks = [Chunk.from_dict(item) for item in self._read(path / "chunks.json")]
        document = self._read(path / "document.json")
        warnings = list(document.get("structure_warnings", []))
        if document.get("structure_warning") and not warnings:
            warnings.append("legacy_structure_warning")
        result = ChunkingResult(
            doc_id=manifest["doc_id"],
            sections=sections,
            chunks=chunks,
            normalized_full_text=document["normalized_full_text"],
            structure_warnings=warnings,
        )
        return StoredChunks(result=result, version=version, path=path, manifest=manifest)

    def save_chunks(
        self,
        doc_id: str,
        source_hash: str,
        config_hash: str,
        config: dict[str, Any],
        parse_version: int,
        result: ChunkingResult,
    ) -> StoredChunks:
        versions = self._versions("chunks", doc_id)
        for version, path in reversed(versions):
            manifest = self._read(path / "manifest.json")
            if manifest["source_hash"] == source_hash and manifest["config_hash"] == config_hash:
                return self._stored_chunks(version, path)
        version = versions[-1][0] + 1 if versions else 1
        path = self.root / "chunks" / doc_id / f"v{version}"
        manifest = self._manifest(
            "chunks",
            version,
            doc_id,
            source_hash,
            config_hash,
            config,
            parse_version=parse_version,
            structure_warnings=result.structure_warnings,
        )
        self._write(path / "sections.json", [section.to_dict() for section in result.sections])
        self._write(path / "chunks.json", [chunk.to_dict() for chunk in result.chunks])
        self._write(
            path / "document.json",
            {
                "normalized_full_text": result.normalized_full_text,
                "structure_warnings": result.structure_warnings,
            },
        )
        self._write(path / "manifest.json", manifest)
        return StoredChunks(result=result, version=version, path=path, manifest=manifest)

    def load_latest_chunks(self, doc_id: str) -> StoredChunks:
        versions = self._versions("chunks", doc_id)
        if not versions:
            raise FileNotFoundError(f"chưa có artifact chunk cho tài liệu '{doc_id}'")
        version, path = versions[-1]
        return self._stored_chunks(version, path)
