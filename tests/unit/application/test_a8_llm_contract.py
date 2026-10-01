import json
from pathlib import Path

import pytest

from doc2roadmap.application.prerequisite_prompt import (
    MAIN_SCHEMA,
    SECONDARY_SCHEMA,
    main_prompt_hash,
    main_system_prompt,
    secondary_prompt_hash,
    secondary_system_prompt,
)
from doc2roadmap.domain.canonical import digest
from doc2roadmap.domain.prerequisites import validate_main_response
from doc2roadmap.domain.secondary import validate_secondary_response
from doc2roadmap.infrastructure.llm import ReplayEntityExtractor


ROOT = Path("tests/fixtures/a8/baocao-canhan")
MODEL = "gemini-3.1-flash-lite"
GENERATION = {"temperature": 0.0, "max_output_tokens": 8192}


@pytest.mark.parametrize(
    ("name", "schema", "system_prompt", "prompt_hash"),
    [
        ("main", MAIN_SCHEMA, main_system_prompt(), main_prompt_hash(MODEL, GENERATION)),
        ("secondary", SECONDARY_SCHEMA, secondary_system_prompt(), secondary_prompt_hash(MODEL, GENERATION)),
    ],
)
def test_a8_real_contract_replays_offline(name, schema, system_prompt, prompt_hash, monkeypatch):
    monkeypatch.setattr(
        "doc2roadmap.infrastructure.llm.gemini.urlopen",
        lambda *args, **kwargs: pytest.fail("fixture A8 không được chạm mạng"),
    )
    fixture = json.loads((ROOT / f"{name}.json").read_text(encoding="utf-8"))
    request = fixture["calls"][0]["request"]
    assert fixture["prompt_hash"] != prompt_hash  # v3 deliberately supersedes, never rewrites archived calls.
    replay = ReplayEntityExtractor(ROOT / f"{name}.json", prompt_hash=fixture["prompt_hash"])
    reply = replay.start_session(fixture["system_prompt"]).ask_json(
        request["prompt"], response_schema=request["response_schema"]
    )
    if name == "main":
        validate_main_response(reply.payload)
    else:
        data = json.loads(request["prompt"])
        dossier = data["dossier"]
        validate_secondary_response(
            reply.payload,
            {"pair_id": dossier["pair_id"], "left": dossier["left"], "right": dossier["right"]},
        )
    assert reply.usage and reply.usage["totalTokenCount"] > 0


def test_a8_fixture_rejects_one_character_prompt_change():
    changed_hash = digest([main_system_prompt() + "x", MAIN_SCHEMA, MODEL, GENERATION])
    with pytest.raises(ValueError, match="prompt_hash"):
        ReplayEntityExtractor(ROOT / "main.json", prompt_hash=changed_hash)
