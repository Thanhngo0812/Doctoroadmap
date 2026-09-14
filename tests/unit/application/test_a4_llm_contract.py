import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from doc2roadmap.application.canonical_prompt import PARTITION_SCHEMA, DESCRIPTION_SCHEMA, SINGLE_SCHEMA
from doc2roadmap.application.use_cases.canonical_reasoning import CanonicalReasoning
from doc2roadmap.domain.canonical_decisions import validate_partition, split_relation_edges, validate_description
from doc2roadmap.infrastructure.llm import ReplayEntityExtractor


@pytest.mark.parametrize("stage,schema", [("merge", PARTITION_SCHEMA), ("repair", PARTITION_SCHEMA),
                                          ("describe", DESCRIPTION_SCHEMA), ("check", SINGLE_SCHEMA)])
def test_real_a4_single_call_contract(stage, schema, monkeypatch):
    monkeypatch.setattr("doc2roadmap.infrastructure.llm.gemini.urlopen", lambda *a, **k: pytest.fail("network forbidden"))
    path = Path("tests/fixtures/a4/llm-v3") / f"{stage}.json"
    context = json.loads(path.with_suffix(".context.json").read_text(encoding="utf-8"))
    model = SimpleNamespace(model_id="gemini-3.1-flash-lite")
    reasoning = CanonicalReasoning(model, model)
    assert context["generation"] == reasoning.generation
    assert context["language_rule"] == reasoning.language_rule
    # Hash comes from product prompts/schema/config, never from the recorded hash.
    replay = ReplayEntityExtractor(path, prompt_hash=reasoning.prompt_hash(stage, schema))
    session = replay.start_session(reasoning.prompts[stage])
    data = context["input"]
    value = session.ask_json(json.dumps(data, ensure_ascii=False, sort_keys=True), response_schema=schema).payload
    assert session.call_count >= 1
    if stage in {"merge", "repair"}:
        sources = {g["group_id"]: context["sources"][g["group_id"]] for g in data["groups"]}
        validate_partition(value, sources)
        kept, rejected = split_relation_edges(value, sources)
        assert len(kept) + len(rejected) == len(value["relations"])
        assert all(row["error"] for row in rejected)
        if stage == "repair":
            assert data["repair_of_cut_edge"] is True
    elif stage == "describe":
        validate_description(value, context["sources"][data["node_id"]], data["language"])
    elif stage == "check":
        assert len(value["nodes"]) == len(data["nodes"])
        assert {r["node_id"] for r in value["nodes"]} == {n["node_id"] for n in data["nodes"]}
        assert all(type(r["keep"]) is bool and isinstance(r["reason"], str) for r in value["nodes"])
    reasoning.prompts[stage] += " Changed instruction."
    with pytest.raises(ValueError, match="prompt_hash"):
        ReplayEntityExtractor(path, prompt_hash=reasoning.prompt_hash(stage, schema))
