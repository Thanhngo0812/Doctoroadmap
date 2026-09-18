from __future__ import annotations

import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from doc2roadmap.application.ports import StoredChunks, StoredParse, StoredStageArtifact
from doc2roadmap.domain.models import Chunk, ChunkingResult, DocumentTree, Section
from doc2roadmap.domain.entities import validate_llm_node_type


_VERSION = re.compile(r"^v(\d+)$")
_IMAGE_ID = re.compile(r"^[0-9a-f]{64}$")
_CHECKPOINT_ID = re.compile(r"^[a-z0-9_-]+$")


class JsonArtifactStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    def load_reviewed_node_types(self) -> dict[str, bool]:
        path = self.root / "type_registry.json"
        if not path.exists():
            return {}
        payload = self._read(path)
        if not isinstance(payload, dict) or not isinstance(payload.get("node_types"), dict):
            raise ValueError("type_registry.json cần object node_types")
        reviewed = {}
        for name, entry in payload["node_types"].items():
            if validate_llm_node_type(name) != name:
                raise ValueError(f"kiểu chưa chuẩn hóa: {name}")
            if (not isinstance(entry, dict)
                or not isinstance(entry.get("reviewed"), bool)
                or not isinstance(entry.get("learnable"), bool)):
                raise ValueError(f"kiểu {name} cần learnable và reviewed dạng boolean")
            if entry["reviewed"]:
                reviewed[name] = entry["learnable"]
        return reviewed

    def _checkpoint_path(self, doc_id: str, checkpoint_id: str) -> Path:
        if not _CHECKPOINT_ID.fullmatch(checkpoint_id):
            raise ValueError("checkpoint_id không hợp lệ")
        return self.root / "checkpoints" / "graph" / doc_id / f"{checkpoint_id}.json"

    def load_checkpoint(self, doc_id: str, checkpoint_id: str) -> dict[str, Any] | None:
        path = self._checkpoint_path(doc_id, checkpoint_id)
        return self._read(path) if path.exists() else None

    def save_checkpoint(self, doc_id: str, checkpoint_id: str, payload: dict[str, Any]) -> None:
        self._write(self._checkpoint_path(doc_id, checkpoint_id), payload)

    def clear_checkpoint(self, doc_id: str, checkpoint_id: str) -> None:
        path = self._checkpoint_path(doc_id, checkpoint_id)
        if path.exists():
            path.unlink()

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

    def load_parse(self, doc_id: str, version: int) -> StoredParse:
        path = self.root / "parse_tree" / doc_id / f"v{version}"
        if not path.is_dir():
            raise FileNotFoundError(
                f"chưa có parse tree v{version} cho tài liệu '{doc_id}'"
            )
        manifest = self._read(path / "manifest.json")
        return StoredParse(
            tree=DocumentTree.from_dict(self._read(path / "tree.json")),
            version=version,
            path=path,
            manifest=manifest,
        )

    def load_image(self, doc_id: str, parse_version: int, image_id: str) -> bytes:
        if not _IMAGE_ID.fullmatch(image_id):
            raise ValueError("image_id phải là SHA-256 viết thường")
        path = (
            self.root
            / "parse_tree"
            / doc_id
            / f"v{parse_version}"
            / "images"
            / f"{image_id}.png"
        )
        return path.read_bytes()

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

    def load_chunks(self, doc_id: str, version: int) -> StoredChunks:
        return self._stored_chunks(version, self.root / "chunks" / doc_id / f"v{version}")

    def load_canonical(self, doc_id: str, version: int) -> StoredStageArtifact:
        return self._load_stage("canonical", doc_id, version)

    def load_latest_canonical(self, doc_id: str) -> StoredStageArtifact:
        return self._load_latest_stage("canonical", doc_id)

    def load_type_aliases(self) -> dict[str, str]:
        self.load_reviewed_node_types()  # Validate the shared registry before reading mappings.
        path = self.root / "type_registry.json"
        if not path.exists():
            return {}
        aliases = {}
        for name, entry in self._read(path)["node_types"].items():
            if entry["reviewed"] and "canonical_type" in entry:
                target = entry["canonical_type"]
                if not isinstance(target, str) or validate_llm_node_type(target) != target:
                    raise ValueError(f"canonical_type không hợp lệ: {name}")
                aliases[name] = target
        if any(target in aliases and aliases[target] != target for target in aliases.values()):
            raise ValueError("canonical_type phải trỏ thẳng tới kiểu chuẩn, không nối chuỗi")
        return aliases

    def _find_stage(
        self, artifact: str, doc_id: str, source_hash: str, config_hash: str
    ) -> StoredStageArtifact | None:
        for version, path in reversed(self._versions(artifact, doc_id)):
            manifest = self._read(path / "manifest.json")
            if (
                manifest["source_hash"] == source_hash
                and manifest["config_hash"] == config_hash
            ):
                return self._stored_stage(artifact, version, path)
        return None

    def _stored_stage(
        self, artifact: str, version: int, path: Path
    ) -> StoredStageArtifact:
        return StoredStageArtifact(
            payload=self._read(path / f"{artifact}.json"),
            version=version,
            path=path,
            manifest=self._read(path / "manifest.json"),
        )

    def _load_stage(
        self, artifact: str, doc_id: str, version: int
    ) -> StoredStageArtifact:
        path = self.root / artifact / doc_id / f"v{version}"
        if not path.is_dir():
            raise FileNotFoundError(
                f"chưa có artifact {artifact} v{version} cho tài liệu '{doc_id}'"
            )
        return self._stored_stage(artifact, version, path)

    def _load_latest_stage(self, artifact: str, doc_id: str) -> StoredStageArtifact:
        versions = self._versions(artifact, doc_id)
        if not versions:
            raise FileNotFoundError(
                f"chưa có artifact {artifact} cho tài liệu '{doc_id}'"
            )
        version, path = versions[-1]
        return self._stored_stage(artifact, version, path)

    def _save_stage(
        self,
        artifact: str,
        doc_id: str,
        source_hash: str,
        config_hash: str,
        config: dict[str, Any],
        payload: dict[str, Any],
        *,
        upstream_version: int,
        manifest_fields: dict[str, Any] | None = None,
        force_new: bool = False,
    ) -> StoredStageArtifact:
        existing = None if force_new else self._find_stage(
            artifact, doc_id, source_hash, config_hash
        )
        if existing:
            return existing
        versions = self._versions(artifact, doc_id)
        version = versions[-1][0] + 1 if versions else 1
        path = self.root / artifact / doc_id / f"v{version}"
        manifest = self._manifest(
            artifact,
            version,
            doc_id,
            source_hash,
            config_hash,
            config,
            upstream_version=upstream_version,
            **(manifest_fields or {}),
        )
        self._write(path / f"{artifact}.json", payload)
        self._write(path / "manifest.json", manifest)
        return StoredStageArtifact(payload, version, path, manifest)

    def find_candidates(
        self, doc_id: str, source_hash: str, config_hash: str
    ) -> StoredStageArtifact | None:
        return self._find_stage("candidates", doc_id, source_hash, config_hash)

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
    ) -> StoredStageArtifact:
        if payload.get("coverage_incomplete"):
            failed = ", ".join(payload.get("failed_sections", [])) or "không rõ"
            raise ValueError(f"coverage_incomplete: không đóng băng; section thiếu: {failed}")
        return self._save_stage(
            "candidates",
            doc_id,
            source_hash,
            config_hash,
            config,
            payload,
            upstream_version=upstream_version,
            manifest_fields=manifest_fields,
            force_new=force_new,
        )

    def find_canonical(
        self, doc_id: str, source_hash: str, config_hash: str
    ) -> StoredStageArtifact | None:
        return self._find_stage("canonical", doc_id, source_hash, config_hash)

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
    ) -> StoredStageArtifact:
        return self._save_stage(
            "canonical",
            doc_id,
            source_hash,
            config_hash,
            config,
            payload,
            upstream_version=upstream_version,
            manifest_fields=manifest_fields,
        )

    def find_graph(
        self, doc_id: str, source_hash: str, config_hash: str
    ) -> StoredStageArtifact | None:
        return self._find_stage("graph", doc_id, source_hash, config_hash)

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
    ) -> StoredStageArtifact:
        return self._save_stage(
            "graph",
            doc_id,
            source_hash,
            config_hash,
            config,
            payload,
            upstream_version=upstream_version,
            manifest_fields=manifest_fields,
        )

    def load_graph(self, doc_id: str, version: int) -> StoredStageArtifact:
        return self._load_stage("graph", doc_id, version)

    def load_latest_graph(self, doc_id: str) -> StoredStageArtifact:
        return self._load_latest_stage("graph", doc_id)

    def find_retrieval(
        self, doc_id: str, source_hash: str, config_hash: str
    ) -> StoredStageArtifact | None:
        return self._find_stage("retrieval", doc_id, source_hash, config_hash)

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
    ) -> StoredStageArtifact:
        return self._save_stage(
            "retrieval",
            doc_id,
            source_hash,
            config_hash,
            config,
            payload,
            upstream_version=upstream_version,
            manifest_fields=manifest_fields,
        )

    def load_candidates(self, doc_id: str, version: int) -> StoredStageArtifact:
        return self._load_stage("candidates", doc_id, version)

    def load_latest_candidates(self, doc_id: str) -> StoredStageArtifact:
        return self._load_latest_stage("candidates", doc_id)

    def load_latest_retrieval(self, doc_id: str) -> StoredStageArtifact:
        return self._load_latest_stage("retrieval", doc_id)
