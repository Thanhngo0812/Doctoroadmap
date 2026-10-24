"""SA-61: schemas reach Gemini without `additionalProperties` on the Developer API, and untouched on Vertex."""
import io
import json
from copy import deepcopy

import pytest

from doc2roadmap.application.phase_b import documents, naming, quiz_context3
from doc2roadmap.application.phase_b.assistant import TOOLS, _check_args
from doc2roadmap.application.phase_b.lectures import LECTURE_SCHEMA
from doc2roadmap.application.prerequisite_prompt import MAIN_SCHEMA
from doc2roadmap.infrastructure.google_auth import VertexCredentials
from doc2roadmap.infrastructure.llm import gemini, phase_b
from doc2roadmap.infrastructure.llm.gemini import GeminiEntityExtractor
from doc2roadmap.infrastructure.llm.phase_b import GeminiToolModel, _normalize_function_schema

BANNED = "additionalProperties"

# Hostile schema: the banned key at every level a schema can nest, plus a PROPERTY that is literally named like the key.
NESTED = {
    "type": "object", BANNED: False,
    "properties": {
        BANNED: {"type": "string"},
        "list": {"type": "array", "items": {"type": "object", BANNED: False, "properties": {"x": {"type": "string"}}}},
        "either": {"anyOf": [{"type": "object", BANNED: True, "properties": {}}, {"type": "null"}]},
        "deep": {"type": "object", "properties": {"inner": {"type": "object", BANNED: {"type": "string"}}}},
    },
    "required": ["list"],
}


class _Reply(io.BytesIO):
    """Serves a plain JSON reply (read) and a one-event SSE stream (iteration)."""

    def __init__(self):
        payload = {"candidates": [{"content": {"parts": [{"text": "{}"}]}, "finishReason": "STOP"}]}
        super().__init__(json.dumps(payload).encode())
        self.payload = json.dumps(payload).encode()

    def __iter__(self):
        return iter([b"data: " + self.payload + b"\n", b"\n"])


def _walk(value, path=""):
    """Every key path in a body that carries the banned key as a schema keyword (not as a property name)."""
    found = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key == BANNED:
                found.append(path)
            if key == "properties" and isinstance(child, dict):
                for name, sub in child.items():
                    found += _walk(sub, f"{path}.properties.{name}")
            else:
                found += _walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found += _walk(child, f"{path}[{index}]")
    return found


@pytest.fixture
def sent(monkeypatch):
    """Records every request body; both clients share the fake network."""
    bodies = []

    def urlopen(request, timeout):
        bodies.append(json.loads(request.data))
        return _Reply()

    monkeypatch.setattr(phase_b, "urlopen", urlopen)
    monkeypatch.setattr(gemini, "urlopen", urlopen)
    monkeypatch.setattr(VertexCredentials, "headers", lambda self: {"Authorization": "Bearer t"})
    return bodies


def _model(transport):
    if transport == "vertex":
        return GeminiToolModel(None, transport="vertex", vertex_project="p")
    return GeminiToolModel("key")


def _calls(model, schema):
    """Every place the product sends a schema or a thinking config, for one schema."""
    session = model.start_session("s")
    session.ask_json("p", response_schema=schema)
    session.ask_json("p", response_schema=schema, thinking_level="medium", temperature=0.0, images=[(1, b"jpg")])
    list(session.stream_json("p", response_schema=schema))
    list(session.stream_text("p"))
    list(session.stream_text("p", thinking_level="low", images=[(1, b"jpg")]))


SCHEMAS = {
    "nested": NESTED,
    "quiz_generation": quiz_context3.GENERATION_SCHEMA,
    "quiz_solver": quiz_context3.SOLVER_SCHEMA,
    "lecture": LECTURE_SCHEMA,
    "document": documents.DOCUMENT_SCHEMA,
    "module_naming": naming.SCHEMA,
}


@pytest.mark.parametrize("name", SCHEMAS)
def test_developer_api_never_receives_the_banned_key_in_any_schema(sent, name):
    _calls(_model("developer_api"), SCHEMAS[name])
    assert len(sent) == 5
    assert [_walk(body) for body in sent] == [[]] * 5


def test_developer_api_keeps_a_property_that_is_merely_named_like_the_key(sent):
    _calls(_model("developer_api"), NESTED)
    schema = sent[0]["generationConfig"]["responseJsonSchema"]
    assert schema["properties"][BANNED] == {"type": "string"}
    assert schema["properties"]["list"]["items"]["properties"] == {"x": {"type": "string"}}
    assert schema["properties"]["either"]["anyOf"][1] == {"type": "null"}
    assert schema["properties"]["deep"]["properties"]["inner"] == {"type": "object"}


def test_developer_api_sends_thinking_config_as_given_and_drops_nothing_else(sent):
    _calls(_model("developer_api"), NESTED)
    configs = [body["generationConfig"] for body in sent]
    assert [config.get("thinkingConfig") for config in configs] == [None, {"thinkingLevel": "medium"}, None, None, {"thinkingLevel": "low"}]
    assert all({"temperature", "maxOutputTokens"} <= set(config) for config in configs)
    assert sent[1]["contents"][0]["parts"][2]["inlineData"]["data"]


@pytest.mark.parametrize("name", SCHEMAS)
def test_vertex_body_is_exactly_what_it_was_before(sent, name):
    schema = SCHEMAS[name]
    _calls(_model("vertex"), schema)
    assert sent[0]["generationConfig"]["responseJsonSchema"] == schema
    assert sent[1]["generationConfig"]["responseJsonSchema"] == schema
    assert sent[2]["generationConfig"]["responseJsonSchema"] == schema
    assert "responseJsonSchema" not in sent[3]["generationConfig"]
    if name == "nested":
        assert len(_walk(sent[0])) == 4


def test_assistant_tools_developer_api_drops_the_key_vertex_keeps_it(sent):
    original = deepcopy(TOOLS)
    for transport in ("developer_api", "vertex"):
        session = _model(transport).start_session("s", TOOLS)
        list(session.stream([{"role": "user", "text": "hi", "images": [(2, b"jpg")]}]))
    developer, vertex = sent
    assert _walk(developer) == [] and len(developer["tools"][0]["functionDeclarations"]) == len(TOOLS)
    assert vertex["tools"][0]["functionDeclarations"] == [_normalize_function_schema(tool) for tool in TOOLS]
    assert len(_walk(vertex)) == len(TOOLS)
    assert [name for name in (tool["name"] for tool in developer["tools"][0]["functionDeclarations"])] == [tool["name"] for tool in TOOLS]
    # the filter works on a copy: the product's own schemas keep the key and still reject strangers
    assert TOOLS == original
    assert _check_args(TOOLS[1]["parameters"], {"name": "x", "extra": 1}) == "Thiếu hoặc thừa tham số"
    assert all(tool["parameters"][BANNED] is False for tool in TOOLS)


def test_a_vertex_call_after_a_developer_call_still_has_the_key(sent):
    schema = deepcopy(NESTED)
    _model("developer_api").start_session("s").ask_json("p", response_schema=schema)
    _model("vertex").start_session("s").ask_json("p", response_schema=schema)
    assert _walk(sent[0]) == [] and len(_walk(sent[1])) == 4 and schema == NESTED


def test_phase_a_extractor_follows_the_same_rule(sent):
    for transport in ("developer_api", "vertex"):
        extractor = GeminiEntityExtractor("key" if transport == "developer_api" else None,
                                          transport=transport, vertex_project="p")
        extractor.start_session("s").ask_json("p", response_schema=NESTED)
    developer, vertex = sent
    assert _walk(developer) == [] and len(_walk(vertex)) == 4
    assert vertex["generationConfig"]["responseJsonSchema"] == NESTED


def test_phase_a_real_schema_is_the_same_on_both_transports(sent):
    for transport in ("developer_api", "vertex"):
        extractor = GeminiEntityExtractor("key" if transport == "developer_api" else None,
                                          transport=transport, vertex_project="p")
        extractor.start_session("s").ask_json("p", response_schema=MAIN_SCHEMA)
    assert sent[0] == sent[1]
