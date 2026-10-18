"""Offline analysis helpers for the SA-43 retry-temperature replay."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from statistics import median
from datetime import datetime
from math import ceil
from pathlib import Path
from typing import Any, Iterable, Mapping


RULES = ("K10", "K11", "K12")
TIMING_FIELDS = ("skeleton_ms", "gate_ms", "final_ms", "gate_to_final_ms")


def nearest_rank(values: Iterable[float], percentile: float) -> float | None:
    ordered = sorted(values)
    if not ordered:
        return None
    if not 0 < percentile <= 1:
        raise ValueError("percentile must be in (0, 1]")
    return ordered[ceil(percentile * len(ordered)) - 1]


def summarize_timings(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Use complete, real click timing rows once per document/context."""
    accepted: dict[tuple[str, str], Mapping[str, Any]] = {}
    excluded = {"replay": 0, "incomplete": 0, "duplicate": 0}
    ordered = sorted(rows, key=lambda row: str(row.get("created_at", "")))
    for row in ordered:
        if row.get("purpose") != "lecture_timing":
            continue
        kind = str(row.get("timing_kind", "")).casefold()
        if row.get("replayed") or row.get("is_replay") or "replay" in kind:
            excluded["replay"] += 1
            continue
        if kind != "measured complete click":
            excluded["incomplete"] += 1
            continue
        try:
            created_at = datetime.fromisoformat(str(row.get("created_at", "")))
        except ValueError:
            created_at = None
        if (created_at is None or created_at.tzinfo is None or
                any(not isinstance(row.get(field), (int, float)) for field in TIMING_FIELDS)):
            excluded["incomplete"] += 1
            continue
        context_hash = row.get("context_hash")
        doc_id = row.get("doc_id")
        if not context_hash or not doc_id:
            excluded["incomplete"] += 1
            continue
        key = (str(doc_id), str(context_hash))
        if key in accepted:
            excluded["duplicate"] += 1
            continue
        accepted[key] = row

    metrics = {}
    for field in TIMING_FIELDS:
        values = [float(row[field]) for row in accepted.values()]
        metrics[field] = {"n": len(values), "p50_ms": median(values) if values else None,
                          "p90_ms": nearest_rank(values, .90)}
    return {"n": len(accepted), "p50_rule": "median",
            "p90_rule": "nearest-rank: sorted[ceil(p*n)-1]",
            "dedupe_key": ["doc_id", "context_hash"], "excluded": excluded,
            "metrics": metrics}


def bridge_metrics(doc_id: str, eligible_prereqs: Iterable[str],
                   generations: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    eligible = {str(node_id) for node_id in eligible_prereqs}
    by_generation = []
    emitted_pairs: set[tuple[str, str]] = set()
    emitted_count = 0
    rule_totals = {rule: 0 for rule in RULES}
    for index, generation in enumerate(generations):
        items = generation.get("emitted", [])
        prereqs = [str(item.get("prereq")) for item in items if isinstance(item, Mapping) and item.get("prereq")]
        distinct = {(doc_id, prereq) for prereq in prereqs}
        emitted_count += len(prereqs)
        emitted_pairs.update(distinct)
        dropped = generation.get("dropped_by_rule", {})
        counts = {}
        for rule in RULES:
            count = int(dropped.get(rule, 0) or 0)
            counts[rule] = count
            rule_totals[rule] += count
        by_generation.append({"generation_id": generation.get("generation_id", str(index)),
                              "eligible_prerequisites": len(eligible), "emitted_items": len(prereqs),
                              "distinct_emitted_pairs": len(distinct), "rule_counts": counts})
    return {"eligible_pairs": len({(doc_id, prereq) for prereq in eligible}),
            "eligible_prerequisite_ids": sorted(eligible),
            "emitted_items": emitted_count, "distinct_emitted_pairs": len(emitted_pairs),
            "emitted_prerequisite_ids": sorted(prereq for _, prereq in emitted_pairs),
            "rule_totals": rule_totals, "generations": by_generation}


def summarize_bridges(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    eligible: set[tuple[str, str]] = set()
    emitted: set[tuple[str, str]] = set()
    emitted_items = 0
    for row in rows:
        operation = row.get("operation") or {}
        lecture = f"{operation.get('doc_id')}:{operation.get('node_id')}"
        for arm in row.get("arms", []):
            metrics = arm.get("bridge_metrics") or {}
            eligible.update((lecture, str(prereq)) for prereq in metrics.get("eligible_prerequisite_ids", []))
            emitted_items += int(metrics.get("emitted_items", 0) or 0)
            emitted.update((lecture, str(prereq)) for prereq in metrics.get("emitted_prerequisite_ids", []))
    return {"eligible_pairs": len(eligible), "emitted_items": emitted_items,
            "distinct_emitted_pairs": len(emitted)}


def _arm_status(arm: Mapping[str, Any]) -> str:
    fixture = str(arm.get("fixture_status", "matched"))
    if fixture != "matched":
        return "missing_fixture" if fixture == "missing" else "fixture_mismatch"
    result = arm.get("result") or {}
    if result.get("status") == "failed":
        return "failure_model"
    return "matched"


def _first_request_matches_shared(request: Mapping[str, Any] | None,
                                  shared: Mapping[str, Any]) -> bool:
    if not request:
        return False
    return all(request.get(key) == shared.get(key)
               for key in ("system_prompt", "prompt", "schema", "temperature"))


class _SessionAttributeForwarder:
    """Expose completion metadata from a wrapped model session unchanged."""
    _session_delegate: Any

    def __getattr__(self, name: str) -> Any:
        return getattr(self._session_delegate, name)


def compare_pairs(seed: int, rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    pairs = []
    shared_first_count = 0
    shared_first_cost = 0.0
    repair_cost = 0.0
    for row in rows:
        shared = row.get("shared_first") or {}
        operation = row.get("operation") or {}
        arms = {float(arm["repair_temperature"]): arm for arm in row.get("arms", [])}
        left, right = arms.get(0.0), arms.get(1.0)
        shared_request = {"system_prompt": shared.get("system_prompt"),
                          **(shared.get("request") or {})}
        shared_present = bool(shared.get("system_prompt") is not None and shared.get("request"))
        if shared_present:
            shared_first_count += 1
            shared_first_cost += float(row.get("shared_first_cost_usd", 0) or 0)
        repair_cost += sum(float(arm.get("repair_cost_usd", 0) or 0)
                           for arm in row.get("arms", []))
        arm_statuses = {"0.0": _arm_status(left) if left else "missing_fixture",
                        "1.0": _arm_status(right) if right else "missing_fixture"}
        requests_match = bool(left and right and shared_present and
                              _first_request_matches_shared(left.get("first_request"), shared_request) and
                              _first_request_matches_shared(right.get("first_request"), shared_request))
        planned_seed = row.get("seed", seed)
        seed_matches = planned_seed == seed
        fixture_matched = all(status in {"matched", "failure_model"} for status in arm_statuses.values())
        comparable = shared_present and requests_match and seed_matches and fixture_matched
        if not shared_present:
            exclusion = "missing_shared_first"
        elif not seed_matches:
            exclusion = "seed_mismatch"
        elif not requests_match:
            exclusion = "shared_prompt_or_schema_mismatch"
        elif not comparable:
            exclusion = "fixture_missing_or_mismatched"
        else:
            exclusion = None
        pairs.append({"operation": operation, "seed": planned_seed,
                      "arm_statuses": arm_statuses, "shared_first_counted_once": shared_present,
                      "comparable": comparable, "exclusion": exclusion})
    comparable_count = sum(pair["comparable"] for pair in pairs)
    return {"pairs": pairs, "pair_count": len(pairs), "matched_pair_count": comparable_count,
            "unmatched_pair_count": len(pairs) - comparable_count,
            "shared_first_count": shared_first_count,
            "shared_first_cost_counted_once_usd": round(shared_first_cost, 8),
            "repair_cost_usd": round(repair_cost, 8),
            "total_historical_comparison_cost_usd": round(shared_first_cost + repair_cost, 8)}


ROOT = Path(__file__).resolve().parents[2]
PLAN_PATH = ROOT / "report/pha-b2-sa43-plan-2026-10-18.json"
RECORDINGS = ROOT / "artifacts/phase_b/recordings/sa43-20261018"
PINNED_DOCS = {("doc-1", 57), ("xstk-ch3-1", 68), ("doc-4", 27)}


def _fixture_issue(error: BaseException) -> tuple[str, str] | None:
    message = str(error)
    if "tool replay fixture version or prompt hash does not match" in message:
        return "envelope_hash_mismatch", "recording envelope metadata differs"
    if "tool replay has no unused session matching this request" in message:
        return "actual_session_mismatch", "recorded session does not match current system prompt/tools"
    if "tool replay call" in message and "does not match" in message:
        return "actual_prompt_schema_mismatch", "recorded call does not match current request"
    if "tool replay fixture has no remaining calls" in message:
        return "missing_response", "recording has no response for this generation"
    if isinstance(error, AssertionError) and "no paid repair session" in message:
        return "missing_response", "repair response recording is absent"
    return None


def _load_sa43_runner():
    scripts_dir = ROOT / "scripts/phase-b"
    sys.path.insert(0, str(scripts_dir))
    spec = importlib.util.spec_from_file_location("sa43_acceptance_for_sa51", scripts_dir / "sa43_acceptance.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load SA-43 replay runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _validate_plan(plan: Mapping[str, Any]) -> None:
    rows = plan.get("rows", [])
    if plan.get("seed") != 43 or len(rows) != 12:
        raise ValueError("SA-51 replay requires the pinned seed-43 12-row plan")
    for operation in rows:
        pin = (str(operation.get("doc_id")), int(operation.get("graph_version", -1)))
        if pin not in PINNED_DOCS:
            raise ValueError(f"SA-51 replay refuses non-development pin {pin!r}")


def _run_replay(plan: Mapping[str, Any], output_dir: Path) -> dict[str, Any]:
    """Replay only the pinned SA-43 recordings, writing outputs under output_dir."""
    _validate_plan(plan)
    runner = _load_sa43_runner()
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "tmp").mkdir(parents=True, exist_ok=True)
    previous = {name: getattr(runner, name) for name in ("ROOT", "RESULT", "STORE", "RECORDINGS",
                                                          "_delegate", "SharedFirstModel", "LectureUseCase")}
    states: list[dict[str, Any]] = []
    original_delegate = runner._delegate
    original_shared = runner.SharedFirstModel
    original_lecture = runner.LectureUseCase
    trace_records: list[dict[str, Any]] = []

    class DeferredFixtureError:
        model_id = "sa43-recording"
        is_replay = True

        def __init__(self, state, issue):
            self.state, self.issue = state, issue

        def start_session(self, *_args, **_kwargs):
            self.state["issue"] = self.issue
            raise ValueError(self.issue[1])

    class ObservedReplayModel:
        def __init__(self, delegate, state):
            self.delegate, self.state = delegate, state
            self.model_id = getattr(delegate, "model_id", "sa43-recording")
            self.is_replay = True

        def start_session(self, *args, **kwargs):
            try:
                session = self.delegate.start_session(*args, **kwargs)
            except BaseException as error:
                issue = _fixture_issue(error)
                if issue:
                    self.state["issue"] = issue
                raise
            observed = self

            class ObservedSession(_SessionAttributeForwarder):
                _session_delegate = session

                def stream_json(self, *stream_args, **stream_kwargs):
                    try:
                        yield from session.stream_json(*stream_args, **stream_kwargs)
                    except BaseException as error:
                        issue = _fixture_issue(error)
                        if issue:
                            observed.state["issue"] = issue
                        raise

            return ObservedSession()

    def safe_delegate(runtime, path, prompt_hash, *, replay):
        state = {"issue": None}
        states.append(state)
        try:
            delegate = original_delegate(runtime, path, prompt_hash, replay=replay)
        except (ValueError, OSError, json.JSONDecodeError) as error:
            issue = _fixture_issue(error) or ("unreadable_fixture", "recording file cannot be read")
            return DeferredFixtureError(state, issue)
        return ObservedReplayModel(delegate, state)

    class TracedSharedFirstModel(original_shared):
        def __init__(self, delegate, shared, *, reuse=False):
            super().__init__(delegate, shared, reuse=reuse)
            self.replay_state = getattr(delegate, "state", {"issue": None})
            self.first_requests = []
            self.current_generation = 0

        def start_session(self, system_prompt):
            generation = self.calls
            self.current_generation = generation
            try:
                session = super().start_session(system_prompt)
            except BaseException as error:
                if "comparison arms must share the exact first" in str(error):
                    self.replay_state["issue"] = ("shared_first_mismatch", "first request differs between arms")
                raise
            traced = self

            class TracedSession(_SessionAttributeForwarder):
                _session_delegate = session

                def stream_json(self, prompt, *, response_schema, temperature=None,
                                transport_retries=None, timeout_seconds=None):
                    if generation == 0 and not traced.first_requests:
                        traced.first_requests.append({"system_prompt": system_prompt, "prompt": prompt,
                            "schema": response_schema, "temperature": temperature,
                            "transport_retries": transport_retries, "timeout_seconds": timeout_seconds})
                    try:
                        yield from session.stream_json(prompt, response_schema=response_schema,
                            temperature=temperature, transport_retries=transport_retries,
                            timeout_seconds=timeout_seconds)
                    except BaseException as error:
                        if "comparison arms must share the exact first" in str(error):
                            traced.replay_state["issue"] = ("shared_first_mismatch", "first request differs between arms")
                        raise

            return TracedSession()

    class TracedLectureUseCase(original_lecture):
        def make(self, *args, on_event=None, **kwargs):
            before = len(self.store.usage_rows())
            model = self.model
            tagged_events = []

            def trace(event):
                tagged = dict(event)
                if tagged.get("event") == "item":
                    tagged["generation_index"] = max(0, getattr(model, "current_generation", 0))
                tagged_events.append(tagged)
                if on_event:
                    on_event(tagged)

            result = super().make(*args, on_event=trace if on_event else None, **kwargs)
            new_rows = self.store.usage_rows()[before:]
            trace_records.append({"events": tagged_events,
                "usage_rows": new_rows,
                "first_request": (model.first_requests[0] if model.first_requests else None),
                "fixture_issue": model.replay_state.get("issue"),
                "generation_count": getattr(model, "calls", 0)})
            return result

    try:
        runner.ROOT = output_dir
        runner.RESULT = output_dir / "unused-live-result.json"
        runner.STORE = output_dir / "unused-store.json"
        runner.RECORDINGS = RECORDINGS
        runner._delegate = safe_delegate
        runner.SharedFirstModel = TracedSharedFirstModel
        runner.LectureUseCase = TracedLectureUseCase
        result = runner.execute(dict(plan), replay=True)
    finally:
        for name, value in previous.items():
            setattr(runner, name, value)

    trace_index = 0
    for row in result["completed"]:
        operation = row["operation"]
        eligible = []
        from doc2roadmap.composition_phase_b import PhaseBRuntime
        runtime = PhaseBRuntime(mode="offline", allow_spend=False,
                                store_path=output_dir / "unused-runtime-store.json")
        graph = runtime.graph(operation["doc_id"], operation["graph_version"])
        from doc2roadmap.application.phase_b.lectures import _assemble
        context = _assemble(graph, operation["node_id"], runtime.b_settings)[0]
        eligible = [str(item["prereq"]) for item in context.get("bridge_candidates", [])]
        for arm in row["arms"]:
            trace = trace_records[trace_index] if trace_index < len(trace_records) else {}
            trace_index += 1
            issue = trace.get("fixture_issue")
            arm["fixture_status"] = ("missing" if issue and issue[0] == "missing_response" else
                                     "mismatch" if issue else "matched")
            arm["fixture_issue"] = {"code": issue[0], "detail": issue[1]} if issue else None
            arm["first_request"] = trace.get("first_request")
            validation = [entry for entry in trace.get("usage_rows", [])
                          if entry.get("purpose") == "lecture_validation"]
            arm["validation"] = validation
            generation_rows = []
            final_bridge_items = [item for section in (arm.get("result") or {}).get("sections", [])
                                  if section.get("kind") == "cau_noi"
                                  for item in section.get("items", [])]
            final_generation = max((int(entry.get("generation_index", 0)) for entry in validation),
                                  default=0)
            for entry in validation:
                index = int(entry.get("generation_index", 0))
                emitted = final_bridge_items if index == final_generation else []
                generation_rows.append({"generation_id": entry.get("generation_id"),
                    "eligible_prerequisites": eligible, "emitted": emitted,
                    "dropped_by_rule": entry.get("dropped_by_rule", {})})
            lecture_id = f"{operation['doc_id']}:{operation['node_id']}"
            arm["bridge_metrics"] = bridge_metrics(lecture_id, eligible, generation_rows)
            arm["generation_count"] = trace.get("generation_count", len(validation))
    return result


def _ledger_timing_rows(live: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Extract measured first-arm click timings from the live SA-43 artifact."""
    usage_rows = live.get("usage_rows", [])
    timing_rows = []
    raw_timing = [row for row in usage_rows if row.get("purpose") == "lecture_timing"]
    for completed in live.get("completed", []):
        for arm in completed.get("arms", []):
            doc_id = str(completed.get("operation", {}).get("doc_id", ""))
            result = arm.get("result") or {}
            diagnostics = result.get("diagnostics") or {}
            validation_hashes = [str(entry.get("context_hash")) for entry in arm.get("validation", [])
                                 if entry.get("context_hash")]
            candidates = [row for row in raw_timing if str(row.get("doc_id")) == doc_id and
                          row.get("gate_ms") == diagnostics.get("gate_ms") and
                          row.get("final_ms") == diagnostics.get("final_ms")]
            context_hash = next((str(row.get("context_hash")) for row in candidates
                                 if row.get("context_hash")),
                                validation_hashes[-1] if validation_hashes else "")
            normalized = {"purpose": "lecture_timing", "doc_id": doc_id,
                          "context_hash": context_hash,
                          "created_at": next((row.get("created_at") for row in candidates),
                                             completed.get("operation", {}).get("created_at")),
                          "timing_kind": "replay" if float(arm.get("repair_temperature", -1)) != 0.0
                                         else "incomplete"}
            if (float(arm.get("repair_temperature", -1)) == 0.0 and
                    arm.get("timing_kind") == "measured complete click" and result.get("status") == "ready" and
                    all(isinstance(diagnostics.get(field), (int, float)) for field in TIMING_FIELDS)):
                normalized["timing_kind"] = "measured complete click"
                normalized.update({field: diagnostics[field] for field in TIMING_FIELDS})
            timing_rows.append(normalized)
    return timing_rows


def _ledger_cost_totals(live: Mapping[str, Any]) -> dict[str, float]:
    lecture_rows = [row for row in live.get("usage_rows", []) if row.get("purpose") == "lecture"]
    unique = {str(row.get("generation_id")): row for row in lecture_rows if row.get("generation_id")}
    shared = sum(float(row.get("cost_usd", 0) or 0) for row in unique.values()
                 if int(row.get("generation_index", 0)) == 0)
    repair = sum(float(row.get("cost_usd", 0) or 0) for row in unique.values()
                 if int(row.get("generation_index", 0)) > 0)
    return {"shared_first_cost_counted_once_usd": round(shared, 8),
            "repair_cost_usd": round(repair, 8),
            "total_historical_comparison_cost_usd": round(shared + repair, 8)}


def run_analysis(plan_path: Path = PLAN_PATH, *, output_dir: Path | None = None,
                 timing_artifact: Path | None = None) -> dict[str, Any]:
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    target = output_dir or ROOT / "tmp/sa51"
    replay = _run_replay(plan, target / "isolated")
    timing_rows = []
    if timing_artifact and timing_artifact.exists():
        live = json.loads(timing_artifact.read_text(encoding="utf-8"))
        timing_rows = _ledger_timing_rows(live)
        ledger_costs = _ledger_cost_totals(live)
    comparison = compare_pairs(int(plan["seed"]), replay.get("completed", []))
    if timing_artifact and timing_artifact.exists():
        comparison.update(ledger_costs)
    result = {"ticket": "SA-51", "seed": plan["seed"], "pin_allowlist": sorted(
        [{"doc_id": doc_id, "graph_version": version} for doc_id, version in PINNED_DOCS],
        key=lambda item: (item["doc_id"], item["graph_version"])),
        "comparison": comparison, "timing": summarize_timings(timing_rows),
        "bridge_summary": summarize_bridges(replay.get("completed", [])),
        "rows": replay.get("completed", []), "replayed": True,
        "network_calls": 0, "new_usd": 0.0}
    target.mkdir(parents=True, exist_ok=True)
    (target / "sa51-replay-analysis.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=PLAN_PATH)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "tmp/sa51")
    parser.add_argument("--timing-artifact", type=Path,
                        help="SA-43 result JSON containing the original measured usage_rows")
    args = parser.parse_args()
    result = run_analysis(args.plan, output_dir=args.output_dir, timing_artifact=args.timing_artifact)
    print(json.dumps({"pairs": result["comparison"]["pair_count"],
        "matched_pairs": result["comparison"]["matched_pair_count"],
        "unmatched_pairs": result["comparison"]["unmatched_pair_count"],
        "shared_first_count": result["comparison"]["shared_first_count"],
        "timing_n": result["timing"]["n"], "network_calls": 0, "new_usd": 0.0},
        ensure_ascii=False))


if __name__ == "__main__":
    main()
