from .prompt_library import load_prompt


def _object(properties):
    return {"type": "object", "properties": properties, "required": list(properties)}


def _array(items):
    return {"type": "array", "items": items}


STRING = {"type": "string"}
IDS = _array(STRING)
PARTITION_SCHEMA = _object({
    "nodes": _array(_object({"groups": IDS, "reason": STRING})),
    "relations": _array(_object({"source": STRING, "target": STRING, "edge_type": STRING,
                                  "chunk_ids": IDS, "reason": STRING})),
    "deferred": _array(_object({"group_id": STRING, "reason": STRING})),
})
DESCRIPTION_SCHEMA = _object({
    "sentences": _array(_object({"text": STRING, "chunk_ids": IDS})),
    "defining_chunk_ids": IDS, "nghi_gop_nham": {"type": "boolean"}, "reason": STRING,
})
SINGLE_SCHEMA = _object({"nodes": _array(_object({"node_id": STRING, "keep": {"type": "boolean"}, "reason": STRING}))})


def canonical_prompts():
    partition = load_prompt("a4", "partition")
    return {"merge": partition, "repair": partition,
            "describe": load_prompt("a4", "describe"), "check": load_prompt("a4", "check")}
