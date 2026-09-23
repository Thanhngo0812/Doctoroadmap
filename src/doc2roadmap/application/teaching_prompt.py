from __future__ import annotations

from typing import Any

from doc2roadmap.application.prompt_library import load_prompt
from doc2roadmap.domain.canonical import digest
from doc2roadmap.domain.teaching import KINDS, ROLES

TEACHING_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "node_id": {"type": "string"},
        "chunk_id": {"type": "string"},
        "kind": {"type": "string", "enum": list(KINDS)},
        "role": {"type": "string", "enum": list(ROLES)},
        "quote": {"type": "string"},
        "reason": {"type": "string"},
    },
    "required": ["node_id", "chunk_id", "kind", "role", "reason"],
}


def teaching_system_prompt():
    return load_prompt("a10", "teaching")


def teaching_prompt_hash(model_id, generation):
    return digest([teaching_system_prompt(), TEACHING_SCHEMA, model_id, generation])
