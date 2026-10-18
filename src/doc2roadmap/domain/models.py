from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class DocumentNode:
    node_type: str
    text: str
    reading_order: int
    level: int | None = None
    page: int | None = None
    bbox: tuple[float, float, float, float] | None = None
    table_rows: list[list[str]] | None = None
    table_id: str | None = None
    context_prefix: str | None = None
    image_id: str | None = None
    tree_depth: int | None = None
    raw_text: str | None = None
    formula_id: str | None = None
    bbox_origin: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DocumentNode:
        if data.get("bbox") is not None:
            data = {**data, "bbox": tuple(data["bbox"])}
        return cls(**data)


@dataclass(slots=True)
class DocumentTree:
    nodes: list[DocumentNode]
    structure_warnings: list[str] = field(default_factory=list)
    parse_stats: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [node.to_dict() for node in self.nodes],
            "structure_warnings": self.structure_warnings,
            "parse_stats": self.parse_stats,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DocumentTree:
        warnings = list(data.get("structure_warnings", []))
        if data.get("structure_warning") and not warnings:
            warnings.append("legacy_structure_warning")
        return cls(
            nodes=[DocumentNode.from_dict(node) for node in data["nodes"]],
            structure_warnings=warnings,
            parse_stats=data.get("parse_stats", {}),
        )


@dataclass(slots=True)
class Section:
    section_id: str
    doc_id: str
    title: str
    level: int
    heading_level_raw: int | None
    parent_section_id: str | None
    section_path: list[str]
    order_index: int
    has_direct_content: bool = False
    role: str = "noi_dung"
    is_toc: bool = False
    role_source: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Section:
        return cls(**data)


@dataclass(slots=True)
class ImageRef:
    image_id: str
    char_start: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ImageRef:
        return cls(**data)


@dataclass(slots=True)
class TableRef:
    table_id: str
    char_start: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TableRef:
        return cls(**data)


@dataclass(slots=True)
class FormulaRef:
    formula_id: str
    char_start: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FormulaRef:
        return cls(**data)


@dataclass(slots=True)
class Chunk:
    chunk_id: str
    doc_id: str
    order_index: int
    split_index: int
    page: int | None
    char_start: int
    char_end: int
    parent_section_id: str
    section_path: list[str]
    heading_level: int
    block_types: list[str]
    text: str
    context_prefix: str | None
    image_refs: list[ImageRef]
    token_count: int
    tokenizer_id: str
    table_refs: list[TableRef] = field(default_factory=list)
    formula_refs: list[FormulaRef] = field(default_factory=list)
    oversize_reason: str | None = None
    role: str = "noi_dung"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Chunk:
        data = dict(data)
        if "block_type" in data:
            data["block_types"] = [data.pop("block_type")]
        if data.pop("oversize", False):
            raise ValueError(
                "artifact chunk schema cũ có oversize=true nhưng không lưu lý do; hãy ingest lại"
            )
        data["image_refs"] = [ImageRef.from_dict(item) for item in data.get("image_refs", [])]
        data["table_refs"] = [TableRef.from_dict(item) for item in data.get("table_refs", [])]
        data["formula_refs"] = [
            FormulaRef.from_dict(item) for item in data.get("formula_refs", [])
        ]
        return cls(**data)


@dataclass(slots=True)
class ChunkingResult:
    doc_id: str
    sections: list[Section]
    chunks: list[Chunk]
    normalized_full_text: str
    structure_warnings: list[str] = field(default_factory=list)
