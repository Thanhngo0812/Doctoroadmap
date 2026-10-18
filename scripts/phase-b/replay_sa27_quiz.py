from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from doc2roadmap.application.phase_b.quiz import QuizUseCase


RECORDINGS = ROOT / "artifacts/phase_b/recordings"
RUNS = {
    "V1": "acceptance-group3",
    "V2": "acceptance-group3-v2",
    "V3": "acceptance-group3-v3",
    "V4": "acceptance-group3-v4",
    "SA27-live-v2": "acceptance-sa27-v2",
}


class EmptyStore:
    pass


class EmptyGraph:
    payload = {}
    nodes = {}
    modules = {}
    chunks = {}


def parse_context(prompt):
    return json.loads(prompt.split("\n", 1)[1].split("\n", 1)[0])


def replay_run(version, directory):
    path = RECORDINGS / directory / "quiz_gen.json"
    recording = json.loads(path.read_text(encoding="utf-8"))
    usecase = QuizUseCase(EmptyGraph(), EmptyStore())
    totals = Counter()
    by_document = defaultdict(Counter)
    samples = defaultdict(list)
    normalized = {}
    gen_calls = []
    for session_index, session in enumerate(recording.get("sessions", [])):
        for call_index, call in enumerate(session.get("calls", [])):
            gen_calls.append((session_index, call_index, call))
            try:
                context = parse_context(call["prompt"])
            except (KeyError, ValueError, IndexError):
                totals["recording.context_parse_error"] += 1
                continue
            context["_source_registry"] = None
            concept = context["concept"]
            doc_id = context.get("doc_id", "unknown")
            payload = call.get("reply", {}).get("payload")
            items = payload.get("items", []) if isinstance(payload, dict) else []
            if not isinstance(payload, dict):
                totals["generation.no_json_payload"] += 1
                by_document[doc_id]["generation.no_json_payload"] += 1
                continue
            for candidate_index, raw in enumerate(items):
                totals["candidates"] += 1
                by_document[doc_id]["candidates"] += 1
                item, reason = usecase._normalize_item_with_reason(concept, context, raw)
                if reason:
                    code = reason
                    usecase._record_rejection("normalize", code, concept, raw)
                else:
                    passed, reason = usecase._rules_pass_with_reason(item, context)
                    if not passed:
                        code = reason
                        usecase._record_rejection("local_rules", code, concept, raw, item)
                    else:
                        code = "local.passed"
                        normalized[item["item_id"]] = (item, context, concept, doc_id)
                totals[code] += 1
                by_document[doc_id][code] += 1
                if code != "local.passed" and len(samples[code]) < 3:
                    samples[code].append({
                        "doc_id": doc_id, "concept": usecase._name(concept),
                        "stem": str(raw.get("stem", ""))[:250],
                        "correct": str(raw.get("correct", {}).get("text", ""))[:100],
                        "distractors": [str(row.get("text", ""))[:100]
                                        for row in raw.get("distractors", []) if isinstance(row, dict)],
                    })

    verify_path = RECORDINGS / directory / "quiz_verify.json"
    verifier_calls = 0
    if verify_path.exists():
        verify_recording = json.loads(verify_path.read_text(encoding="utf-8"))
        for session in verify_recording.get("sessions", []):
            for call in session.get("calls", []):
                verifier_calls += 1
                try:
                    verifier_input = parse_context(call["prompt"])
                except (KeyError, ValueError, IndexError):
                    totals["verifier.recording_parse_error"] += 1
                    continue
                payload = call.get("reply", {}).get("payload")
                results = payload.get("items", []) if isinstance(payload, dict) else []
                labels = verifier_input.get("items", [])
                for result in results:
                    item_id = result.get("item_id")
                    matched = normalized.get(item_id)
                    if not matched:
                        totals["verifier.unknown_item"] += 1
                        continue
                    item, context, concept, doc_id = matched
                    label = next((row for row in labels if row.get("item_id") == item_id), {})
                    choice_by_id = {str(option.get("option_id")): option.get("text")
                                    for option in label.get("options", [])}
                    options = []
                    for option_id in sorted(choice_by_id, key=lambda value: int(value) if value.isdigit() else value):
                        text = choice_by_id[option_id]
                        full = next((row for row in item["options"] if row["text"] == text), None)
                        if full is not None:
                            options.append(full)
                    verdicts = result.get("distractor_verdicts", [])
                    verdict_by_option = {str(v.get("option_id")): v.get("verdict", "")
                                         for v in verdicts if isinstance(v, dict)}
                    correct_index = next((str(i) for i, option in enumerate(options) if option.get("is_correct")), None)
                    complete = (correct_index is not None
                                and all(verdict_by_option.get(str(i), "").casefold() == "sai theo nguồn"
                                        for i in range(len(options)) if str(i) != correct_index))
                    verdict_values = [v.get("verdict", "") for v in verdicts if isinstance(v, dict)]
                    reason = usecase._verifier_rejection_reason(
                        item, context, options, result, complete, verdict_values)
                    code = reason or "verifier.passed"
                    totals[code] += 1
                    by_document[doc_id][code] += 1
                    if reason:
                        usecase._record_rejection("verifier", reason, concept, {}, item)
                        if len(samples[code]) < 3:
                            samples[code].append({"doc_id": doc_id, "concept": usecase._name(concept),
                                                  "stem": item["stem"][:250],
                                                  "correct": next(o["text"] for o in item["options"] if o["is_correct"]),
                                                  "distractors": [o["text"] for o in item["options"] if not o["is_correct"]],
                                                  "verdicts": verdict_values})

    if normalized:
        # Missing verifier records are explicit, while a successful replay with no recorded
        # verifier calls is intentionally not simulated as a verifier execution.
        if not verifier_calls:
            totals["verifier.not_recorded"] += len(normalized)
    return {
        "generation_calls": len(gen_calls), "verifier_calls": verifier_calls,
        "counters": dict(sorted(totals.items())),
        "by_document": {doc: dict(sorted(counts.items())) for doc, counts in sorted(by_document.items())},
        "samples": dict(samples),
        "private_diagnostic_rows": len(usecase.diagnostics),
    }


def main():
    result = {version: replay_run(version, path) for version, path in RUNS.items()}
    out = ROOT / "tmp/phaseb-sa27-replay-v1-v4.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: {"generation_calls": value["generation_calls"],
                            "verifier_calls": value["verifier_calls"],
                            "counters": value["counters"],
                            "by_document": value["by_document"]}
                      for key, value in result.items()}, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
