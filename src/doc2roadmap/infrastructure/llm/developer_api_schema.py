from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

# Keys the Developer API rejects ("Unknown name ... at ...function_declarations[i].parameters", SA-60) and the
# documented Schema object does not list. The application keeps them (the assistant's `_check_args` relies on them).
DEVELOPER_API_REJECTED = frozenset({"additionalProperties"})
_SCHEMA_LISTS = ("anyOf", "oneOf", "allOf", "prefixItems")


def for_developer_api(body: Mapping[str, Any]) -> dict[str, Any]:
    """Copy of a request body whose schemas lack the keys the Developer API rejects. The input is never changed."""
    result = dict(body)
    config = result.get("generationConfig")
    if isinstance(config, Mapping):
        config = dict(config)
        for field in ("responseJsonSchema", "responseSchema"):
            if field in config:
                config[field] = _clean(config[field])
        result["generationConfig"] = config
    if isinstance(result.get("tools"), list):
        result["tools"] = [_clean_tool(tool) for tool in result["tools"]]
    return result


def _clean_tool(tool: Any) -> Any:
    if not isinstance(tool, Mapping) or not isinstance(tool.get("functionDeclarations"), list):
        return tool
    declarations = []
    for declaration in tool["functionDeclarations"]:
        declaration = dict(declaration)
        for field in ("parameters", "parametersJsonSchema", "response", "responseJsonSchema"):
            if field in declaration:
                declaration[field] = _clean(declaration[field])
        declarations.append(declaration)
    return {**tool, "functionDeclarations": declarations}


def _clean(schema: Any) -> Any:
    """Recurse through every sub-schema; a property that is merely *named* like a rejected key survives."""
    if not isinstance(schema, Mapping):
        return deepcopy(schema)
    result: dict[str, Any] = {}
    for key, value in schema.items():
        if key in DEVELOPER_API_REJECTED:
            continue
        if key == "properties" and isinstance(value, Mapping):
            result[key] = {name: _clean(sub) for name, sub in value.items()}
        elif key == "items":
            result[key] = [_clean(sub) for sub in value] if isinstance(value, list) else _clean(value)
        elif key in _SCHEMA_LISTS and isinstance(value, list):
            result[key] = [_clean(sub) for sub in value]
        else:
            result[key] = deepcopy(value)
    return result
