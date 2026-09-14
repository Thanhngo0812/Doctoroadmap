"""Record four single-call A4/A5 contracts; explicit network-only fixture command."""
import json
from pathlib import Path

from doc2roadmap.application.canonical_prompt import PARTITION_SCHEMA, DESCRIPTION_SCHEMA, SINGLE_SCHEMA
from doc2roadmap.application.use_cases.a4_gold import load_gold
from doc2roadmap.composition import build_canonical
from doc2roadmap.infrastructure.llm import RecordingEntityExtractor


def main():
    use_case = build_canonical()
    gold = load_gold(Path("tests/fixtures/a4/gold-blind.json"), use_case.store, require_complete=True)
    doc = "baocao-canhan"
    artifact = use_case.store.load_latest_canonical(doc)
    if artifact.payload["stage"] != "complete":
        raise ValueError("record fixtures after a complete A4 run")
    original = use_case.store.load_canonical(doc, gold["documents"][doc]["canonical_version"])
    sources = {n["node_id"]: n["source_chunk_ids"] for n in original.payload["nodes"]}
    sources.update({n["node_id"]: n["source_chunk_ids"] for n in artifact.payload["nodes"]})
    reasoning = use_case.reasoning
    for stage, schema in [("merge", PARTITION_SCHEMA), ("repair", PARTITION_SCHEMA),
                          ("describe", DESCRIPTION_SCHEMA), ("check", SINGLE_SCHEMA)]:
        row = next(r for r in artifact.payload["decision_log"] if r.get("stage") == stage and r.get("valid"))
        path = Path("tests/fixtures/a4/llm-v2") / f"{stage}.json"
        if path.exists():
            raise ValueError(f"refusing to overwrite recorded fixture: {path}")
        model = reasoning.writer if stage in {"describe", "check"} else reasoning.judge
        recorder = RecordingEntityExtractor(model, path, prompt_hash=reasoning.prompt_hash(stage, schema))
        recorder.start_session(reasoning.prompts[stage]).ask_json(
            json.dumps(row["input"], ensure_ascii=False, sort_keys=True), response_schema=schema)
        use_case.store._write(path.with_suffix(".context.json"), {
            "input": row["input"], "sources": sources, "canonical_version": artifact.version,
            "generation": reasoning.generation, "language_rule": reasoning.language_rule,
        })
        print(f"recorded {stage}", flush=True)


if __name__ == "__main__":
    main()
