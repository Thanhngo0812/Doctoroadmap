from __future__ import annotations

from typing import Any

from doc2roadmap.application.prompt_library import load_prompt
from doc2roadmap.domain.canonical import digest
from doc2roadmap.domain.relation_check import VERDICTS

RELATION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "edge_id": {"type": "string"},
        "verdict": {"type": "string", "enum": list(VERDICTS)},
        "quote": {"type": "string"},
        "reason": {"type": "string"},
    },
    "required": ["edge_id", "verdict", "reason"],
}


def relation_system_prompt():
    return load_prompt("a9", "relation-check")


def relation_prompt_hash(model_id, generation):
    return digest([relation_system_prompt(), RELATION_SCHEMA, model_id, generation])
