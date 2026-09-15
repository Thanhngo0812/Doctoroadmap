from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .prompt_library import load_prompt


SEED_NODE_TYPES = (
    "concept",
    "definition",
    "theorem",
    "algorithm",
    "metric",
    "method",
)


@dataclass(frozen=True, slots=True)
class ExtractionPrompts:
    system: str
    few_shot: str
    section: str
    glean: str
    validation: str


def load_prompts(few_shot_path: Path | None = None) -> ExtractionPrompts:
    return ExtractionPrompts(
        system=load_prompt("a3", "system"),
        few_shot=(few_shot_path.read_text(encoding="utf-8").strip()
                  if few_shot_path else load_prompt("a3", "few-shot/default")),
        section=load_prompt("a3", "section"),
        glean=load_prompt("a3", "glean"),
        validation=load_prompt("a3", "validation"),
    )


ENTITY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "entities": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "node_type": {"type": "string"},
                    "description_draft": {"type": "string"},
                    "evidence": {"type": "string"},
                    "media_evidence_id": {"type": "string"},
                    "learnable": {"type": "boolean"},
                    "aliases": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "evidence": {"type": "string"},
                            },
                            "required": ["name", "evidence"],
                        },
                    },
                },
                "required": [
                    "name",
                    "node_type",
                    "description_draft",
                    "evidence",
                    "media_evidence_id",
                    "learnable",
                    "aliases",
                ],
            },
        },
        "edges": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "source": {"type": "string"},
                    "target": {"type": "string"},
                    "edge_type": {"type": "string"},
                    "evidence": {"type": "string"},
                },
                "required": ["source", "target", "edge_type", "evidence"],
            },
        },
        "media_descriptions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "media_id": {"type": "string"},
                    "media_type": {
                        "type": "string",
                        "enum": ["figure", "table"],
                    },
                    "description": {"type": "string"},
                    "confirmed_entities": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": [
                    "media_id",
                    "media_type",
                    "description",
                    "confirmed_entities",
                ],
            },
        },
    },
    "required": ["entities", "edges", "media_descriptions"],
}

VALIDATION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "remove_entity_ids": {"type": "array", "items": {"type": "string"}},
        "remove_edge_ids": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["remove_entity_ids", "remove_edge_ids"],
}


def prompt_hash(
    *,
    model_id: str,
    generation: dict[str, Any],
    prompts: ExtractionPrompts | None = None,
) -> str:
    """Hash every prompt input that can change extraction output; secrets are not accepted."""
    prompts = prompts or load_prompts()
    payload = {
        "template": {
            "system": prompts.system,
            "section": prompts.section,
            "glean": prompts.glean,
            "validation": prompts.validation,
        },
        "few_shot": prompts.few_shot,
        "model_id": model_id,
        "generation": generation,
        "schema": {"extract": ENTITY_SCHEMA, "validate": VALIDATION_SCHEMA},
        "seed_types": SEED_NODE_TYPES,
    }
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def section_prompt(
    section_path: list[str],
    chunks: list[tuple[str, str]],
    formulas: list[tuple[str, str, int]],
    media: list[tuple[str, str, str, int, str]] | None = None,
    *,
    prompts: ExtractionPrompts | None = None,
) -> str:
    prompts = prompts or load_prompts()
    chunk_text = "\n\n".join(
        f"<chunk id=\"{chunk_id}\">\n{text}\n</chunk>" for chunk_id, text in chunks
    )
    formula_text = "\n".join(
        f"- chunk={chunk_id} char_start={char_start}: {raw}"
        for chunk_id, raw, char_start in formulas
    ) or "(none)"
    media_text = "\n".join(
        f"- type={media_type} id={media_id} chunk={chunk_id} char_start={char_start} "
        f"caption_status={caption_status}"
        for media_type, media_id, chunk_id, char_start, caption_status in (media or [])
    ) or "(none)"
    return (
        f"{prompts.few_shot}\n\nSECTION_PATH: {' > '.join(section_path) or '<document>'}\n"
        f"CHUNK_TEXT:\n{chunk_text}\n\n"
        f"FORMULA_RAW (context only; never use as evidence):\n{formula_text}\n\n"
        f"MEDIA TO DESCRIBE/CONFIRM:\n{media_text}\n\n"
        + prompts.section
    )


def glean_prompt(
    existing_names: list[str], prompts: ExtractionPrompts | None = None
) -> str:
    prompts = prompts or load_prompts()
    return prompts.glean + (
        f"\nDo not repeat existing names: {json.dumps(existing_names, ensure_ascii=False)}"
    )


def validation_prompt(
    entities: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    prompts: ExtractionPrompts | None = None,
) -> str:
    prompts = prompts or load_prompts()
    return prompts.validation + "\n" + json.dumps(
        {"entities": entities, "edges": edges}, ensure_ascii=False
    )
