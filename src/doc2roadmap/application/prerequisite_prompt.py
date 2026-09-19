from __future__ import annotations

from typing import Any

from doc2roadmap.application.prompt_library import load_prompt
from doc2roadmap.domain.canonical import digest


PRICING_USD_PER_MILLION = {"input": 0.25, "output": 1.50}
PRICING_SOURCE = {
    "model_id": "gemini-3.1-flash-lite",
    "tier": "Gemini Developer API paid standard",
    "checked_on": "2026-09-18",
    "url": "https://ai.google.dev/gemini-api/docs/pricing",
}


MAIN_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "edges": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "target": {"type": "string"},
                    "prerequisite": {"type": "string"},
                    "edge_type": {"type": "string"},
                    "evidence_kind": {"type": "string"},
                    "chunk_ids": {"type": "array", "items": {"type": "string"}},
                    "reason": {"type": "string"},
                },
                "required": ["target", "prerequisite", "evidence_kind", "chunk_ids", "reason"],
            },
        },
        "flags": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "kind": {"type": "string"},
                    "name": {"type": "string"},
                    "chunk_ids": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["kind"],
            },
        },
    },
    "required": ["edges", "flags"],
}

SECONDARY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "pair_id": {"type": "string"},
        "decision": {"type": "string", "enum": ["create", "no_direct_relation", "indirect_path", "defer"]},
        "prerequisite": {"type": "string"},
        "target": {"type": "string"},
        "evidence_kind": {"type": "string"},
        "chunk_ids": {"type": "array", "items": {"type": "string"}},
        "reason": {"type": "string"},
        "flags": {"type": "array", "items": {"type": "object"}},
    },
    "required": ["pair_id", "decision", "flags"],
}

PROVENANCE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "node_id": {"type": "string"},
        "selections": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "chunk_id": {"type": "string"},
                    "quote": {"type": "string"},
                },
                "required": ["chunk_id", "quote"],
            },
        },
    },
    "required": ["node_id", "selections"],
}


def provenance_system_prompt():
    return load_prompt("a8", "provenance")


def provenance_prompt_hash(model_id, generation):
    return digest([provenance_system_prompt(), PROVENANCE_SCHEMA, model_id, generation])


def main_system_prompt():
    return load_prompt("a8", "main")


def main_prompt_hash(model_id, generation):
    return digest([main_system_prompt(), MAIN_SCHEMA, model_id, generation])


def secondary_system_prompt():
    return load_prompt("a8", "secondary")


def secondary_prompt_hash(model_id, generation):
    return digest([secondary_system_prompt(), SECONDARY_SCHEMA, model_id, generation])
