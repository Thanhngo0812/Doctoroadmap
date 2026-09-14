from pathlib import Path


def _object(properties):
    return {"type": "object", "properties": properties, "required": list(properties)}


def _array(items):
    return {"type": "array", "items": items}


STRING = {"type": "string"}
IDS = _array(STRING)
PARTITION_SCHEMA = _object({
    "nodes": _array(_object({"groups": IDS, "reason": STRING})),
    "subtype_edges": _array(_object({"child": STRING, "parent": STRING, "chunk_ids": IDS, "reason": STRING})),
    "deferred": _array(_object({"group_id": STRING, "reason": STRING})),
})
DESCRIPTION_SCHEMA = _object({
    "sentences": _array(_object({"text": STRING, "chunk_ids": IDS})),
    "defining_chunk_ids": IDS, "nghi_gop_nham": {"type": "boolean"}, "reason": STRING,
})
SINGLE_SCHEMA = _object({"nodes": _array(_object({"node_id": STRING, "keep": {"type": "boolean"}, "reason": STRING}))})


def canonical_prompts():
    directory = Path(__file__).with_name("prompts")
    return {stage: (directory / f"a4-{stage}.txt").read_text(encoding="utf-8").strip()
            for stage in ("merge", "repair", "describe", "check")}
