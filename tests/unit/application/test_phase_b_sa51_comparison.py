import importlib.util
from pathlib import Path


def _module():
    root = Path(__file__).resolve().parents[3]
    path = root / "scripts/phase-b/sa51_compare_replay.py"
    spec = importlib.util.spec_from_file_location("sa51_compare_replay", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _arm(temperature, status="ready", *, fixture_status="matched", request=None):
    return {"repair_temperature": temperature, "fixture_status": fixture_status,
            "first_request": request, "result": {"status": status}}


def test_unmatched_prompt_is_excluded_and_not_mislabeled_as_model_failure():
    compare = _module().compare_pairs
    first_request = {"system_prompt": "s", "prompt": "p", "schema": {"x": "string"}}
    rows = [{"seed": 43, "operation": {"doc_id": "doc-1", "node_id": "n"},
             "shared_first": {"system_prompt": "s", "request": {"prompt": "p", "schema": {"x": "string"}}},
             "shared_first_cost_usd": .012,
             "arms": [_arm(0.0, "ready", request=first_request),
                      _arm(1.0, "failed", fixture_status="mismatch", request={**first_request, "prompt": "changed"})]}]

    result = compare(43, rows)

    assert result["matched_pair_count"] == 0
    assert result["pairs"][0]["arm_statuses"] == {"0.0": "matched", "1.0": "fixture_mismatch"}
    assert result["pairs"][0]["exclusion"] == "shared_prompt_or_schema_mismatch"
    assert result["shared_first_count"] == 1
    assert result["shared_first_cost_counted_once_usd"] == .012


def test_matched_failure_remains_a_comparable_model_outcome():
    compare = _module().compare_pairs
    request = {"system_prompt": "s", "prompt": "p", "schema": {"type": "object"}}
    rows = [{"seed": 43, "shared_first": {"system_prompt": "s", "request": {"prompt": "p", "schema": {"type": "object"}}},
             "arms": [_arm(0.0, "ready", request=request), _arm(1.0, "failed", request=request)]}]

    result = compare(43, rows)

    assert result["matched_pair_count"] == 1
    assert result["pairs"][0]["arm_statuses"]["1.0"] == "failure_model"


def test_schema_mismatch_is_not_counted_as_a_matched_comparison():
    compare = _module().compare_pairs
    shared = {"system_prompt": "s", "prompt": "p", "schema": {"x": "string"}}
    rows = [{"seed": 43, "shared_first": {"system_prompt": "s", "request": shared},
             "arms": [_arm(0.0, request=shared),
                      _arm(1.0, request={**shared, "schema": {"x": "integer"}})]}]

    result = compare(43, rows)

    assert result["matched_pair_count"] == 0
    assert result["pairs"][0]["exclusion"] == "shared_prompt_or_schema_mismatch"


def test_missing_first_request_is_not_assumed_to_match():
    compare = _module().compare_pairs
    request = {"system_prompt": "s", "prompt": "p", "schema": {"type": "object"}}
    rows = [{"seed": 43, "shared_first": {"system_prompt": "s", "request": request},
             "arms": [_arm(0.0, request=request), _arm(1.0, request=None)]}]

    result = compare(43, rows)

    assert result["matched_pair_count"] == 0
    assert result["pairs"][0]["exclusion"] == "shared_prompt_or_schema_mismatch"


def test_wrapped_sessions_forward_model_completion_metadata():
    forwarder = _module()._SessionAttributeForwarder

    class Session:
        last_usage = {"output_tokens": 17}
        last_finish_reason = "MAX_TOKENS"
        last_ttft_ms = 31

    class Wrapped(forwarder):
        _session_delegate = Session()

    wrapped = Wrapped()
    assert wrapped.last_usage == {"output_tokens": 17}
    assert wrapped.last_finish_reason == "MAX_TOKENS"
    assert wrapped.last_ttft_ms == 31


def test_timing_uses_full_real_rows_nearest_rank_and_dedupes_contexts():
    summarize = _module().summarize_timings
    rows = [
        {"purpose": "lecture_timing", "doc_id": "d", "context_hash": str(value),
         "created_at": f"2026-10-19T00:00:0{value}+00:00", "skeleton_ms": value,
         "gate_ms": value * 2, "final_ms": value * 4, "gate_to_final_ms": value * 2,
         "timing_kind": "measured complete click"}
        for value in (1, 2, 3, 4)
    ]
    rows.extend([
        {**rows[0], "created_at": "2026-10-19T01:00:00+00:00", "final_ms": 900},
        {**rows[1], "context_hash": "replay", "replayed": True},
        {"purpose": "lecture_timing", "doc_id": "d", "context_hash": "incomplete",
         "created_at": "2026-10-19T00:00:00+00:00", "skeleton_ms": 10},
        {"purpose": "lecture", "doc_id": "d", "context_hash": "not-timing"},
    ])

    result = summarize(rows)

    assert result["n"] == 4
    assert result["metrics"]["final_ms"] == {"n": 4, "p50_ms": 10.0, "p90_ms": 16.0}
    assert result["metrics"]["gate_to_final_ms"] == {"n": 4, "p50_ms": 5.0, "p90_ms": 8.0}
    assert result["excluded"] == {"replay": 1, "incomplete": 1, "duplicate": 1}


def test_live_ledger_keeps_only_ready_measured_first_arm_and_dedupes_replay():
    ledger_timing_rows = _module()._ledger_timing_rows
    key = "sha256:context"
    live = {
        "usage_rows": [
            {"purpose": "lecture_timing", "doc_id": "d", "context_hash": key,
             "created_at": "2026-10-19T00:00:00+00:00", "skeleton_ms": 1,
             "gate_ms": 10, "final_ms": 15, "gate_to_final_ms": 5},
            {"purpose": "lecture_timing", "doc_id": "d", "context_hash": key,
             "created_at": "2026-10-19T00:01:00+00:00", "skeleton_ms": 1,
             "gate_ms": 10, "final_ms": 0, "gate_to_final_ms": 0},
            {"purpose": "lecture", "generation_id": "g0", "generation_index": 0, "cost_usd": .02},
            {"purpose": "lecture", "generation_id": "g1", "generation_index": 1, "cost_usd": .03},
        ],
        "completed": [{"operation": {"doc_id": "d"}, "arms": [
            {"repair_temperature": 0, "timing_kind": "measured complete click",
             "result": {"status": "ready", "diagnostics": {"skeleton_ms": 1,
                 "gate_ms": 10, "final_ms": 15, "gate_to_final_ms": 5}},
             "validation": [{"generation_id": "g0", "generation_index": 0,
                            "context_hash": key},
                           {"generation_id": "g1", "generation_index": 1,
                            "context_hash": key}]},
            {"repair_temperature": 1, "timing_kind": "replay",
             "result": {"status": "ready"},
             "validation": [{"generation_id": "g0", "generation_index": 0,
                            "context_hash": key}]},
        ]}],
    }

    timing = ledger_timing_rows(live)
    assert _module()._ledger_cost_totals(live) == {
        "shared_first_cost_counted_once_usd": .02,
        "repair_cost_usd": .03,
        "total_historical_comparison_cost_usd": .05,
    }
    summary = _module().summarize_timings(timing)
    assert summary["n"] == 1
    assert summary["metrics"]["final_ms"]["p50_ms"] == 15
    assert summary["excluded"]["replay"] == 1


def test_bridge_metrics_dedupe_lecture_prerequisite_but_keep_generation_rules_separate():
    measure = _module().bridge_metrics
    result = measure("lecture-1", ["p1", "p2"], [
        {"generation_id": "first", "emitted": [{"prereq": "p1"}, {"prereq": "p1"}],
         "dropped_by_rule": {"K10": 1, "K11": 2}},
        {"generation_id": "repair", "emitted": [{"prereq": "p1"}, {"prereq": "p2"}],
         "dropped_by_rule": {"K12": 1}},
    ])

    assert result["eligible_pairs"] == 2
    assert result["emitted_items"] == 4
    assert result["distinct_emitted_pairs"] == 2
    assert result["generations"] == [
        {"generation_id": "first", "eligible_prerequisites": 2, "emitted_items": 2,
         "distinct_emitted_pairs": 1, "rule_counts": {"K10": 1, "K11": 2, "K12": 0}},
        {"generation_id": "repair", "eligible_prerequisites": 2, "emitted_items": 2,
         "distinct_emitted_pairs": 2, "rule_counts": {"K10": 0, "K11": 0, "K12": 1}},
    ]
