"""Replay-only evidence extraction for the SA-45 lecture audit (no model calls)."""
import json
import math
import statistics
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPLAY = ROOT / "tmp/phaseb-sa43-replay-20261018.json"
LIVE = ROOT / "tmp/phaseb-sa43-live-20261018.json"
ISOLATED = ROOT / "artifacts/phase_b/sa43-20261018.json"
OUTPUT = ROOT / "tmp/sa45-lecture-repro.json"


def percentile(values, q):
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * q) - 1)]


def main():
    replay = json.loads(REPLAY.read_text(encoding="utf-8"))
    live = json.loads(LIVE.read_text(encoding="utf-8"))
    isolated = json.loads(ISOLATED.read_text(encoding="utf-8"))
    usage = isolated["usage"]
    by_purpose = Counter(row.get("purpose") for row in usage)
    total_cost = sum(float(row.get("cost_usd", 0) or 0) for row in usage)

    lectures = []
    totals = Counter()
    validation = Counter()
    for completed in replay["completed"]:
        arm = completed["arms"][0]
        result = arm["result"]
        request = json.loads(completed["shared_first"]["request"]["prompt"].splitlines()[0])
        eligible = request.get("bridge_candidates", [])
        emitted = [item for section in result.get("sections", [])
                   if section.get("kind") == "cau_noi" for item in section.get("items", [])]
        prereq_ids = [str(item.get("prereq")) for item in emitted]
        distinct = len(set(prereq_ids))
        totals.update(eligible_q=len(eligible), emitted=len(emitted),
                      distinct_prerequisites=distinct,
                      duplicate_emissions=len(emitted) - distinct)
        for row in arm.get("validation", []):
            validation.update(row.get("dropped_by_rule", {}))
        lectures.append({
            "name": completed["operation"]["name"],
            "doc_id": completed["operation"]["doc_id"],
            "node_id": completed["operation"]["node_id"],
            "status": result.get("status"),
            "failure_reason_code": (result.get("failure") or {}).get("reason_code"),
            "eligible_q_prerequisites": [item.get("prereq") for item in eligible],
            "emitted_bridge_prerequisites": prereq_ids,
            "distinct_emitted_bridge_prerequisites": distinct,
            "sections": [{
                "kind": section.get("kind"),
                "items": [{
                    "text": item.get("text"),
                    "question": item.get("question"),
                    "answer": item.get("answer"),
                    "citations": [{"label": c.get("label"), "page": c.get("page"),
                                  "quote": c.get("quote")} for c in item.get("citations", [])],
                } for item in section.get("items", [])]
            } for section in result.get("sections", [])],
            "validation_drop_counts": dict(Counter(
                key for row in arm.get("validation", [])
                for key, count in row.get("dropped_by_rule", {}).items()
                for _ in range(count))),
        })

    timing_rows = [row for row in usage if row.get("purpose") == "lecture_timing"]
    timing = {}
    for field in ("skeleton_ms", "gate_ms", "final_ms", "gate_to_final_ms"):
        values = [row[field] for row in timing_rows if isinstance(row.get(field), (int, float))]
        timing[field] = {"n": len(values), "all_raw_times_p50": statistics.median(values) if values else None,
                         "all_raw_times_p90_nearest_rank": percentile(values, 0.9), "values_ms": values}

    selected_hashes = {}
    full_click_rows = {}
    fields = ("skeleton_ms", "gate_ms", "final_ms", "gate_to_final_ms")
    for completed in live["completed"]:
        result = completed["arms"][0]["result"]
        diagnostics = result.get("diagnostics", {})
        if result.get("status") != "ready" or not all(field in diagnostics for field in fields):
            continue
        rows = [row for row in timing_rows if row.get("doc_id") == completed["operation"]["doc_id"]
                and all(row.get(field) == diagnostics[field] for field in fields)]
        assert len(rows) == 1, 'complete first-arm timing must match exactly one ledger row'
        context_hash = rows[0]["context_hash"]
        selected_hashes[context_hash] = completed["operation"]["name"]
        full_click_rows[context_hash] = rows[0]
    matched_full_clicks = [{"name": selected_hashes[context_hash], "context_hash": context_hash,
                            "created_at": row.get("created_at"), "skeleton_ms": row.get("skeleton_ms"),
                            "gate_ms": row.get("gate_ms"), "final_ms": row.get("final_ms"),
                            "gate_to_final_ms": row.get("gate_to_final_ms")}
                           for context_hash, row in full_click_rows.items()]
    real_full_timing = {}
    for field in ("skeleton_ms", "gate_ms", "final_ms", "gate_to_final_ms"):
        values = [row[field] for row in full_click_rows.values() if isinstance(row.get(field), (int, float))]
        real_full_timing[field] = {"n": len(values), "p50": statistics.median(values) if values else None,
                                   "p90_nearest_rank": percentile(values, 0.9), "values_ms": values}

    output = {
        "provenance": {"replay_file": str(REPLAY.relative_to(ROOT)),
                       "live_file": str(LIVE.relative_to(ROOT)),
                       "isolated_artifact": str(ISOLATED.relative_to(ROOT)),
                       "replayed": replay.get("replayed"),
                       "replay_http_attempts": replay.get("http_attempts"),
                       "replay_new_cost_usd": replay.get("new_cost_usd")},
        "lectures_count": len(lectures),
        "bridge_totals_by_lecture_then_summed": dict(totals),
        "validation_drop_event_totals": dict(validation),
        "isolated_usage_rows_by_purpose": dict(by_purpose),
        "isolated_cost_usd_recomputed": total_cost,
        "isolated_timing_rows_n": len(timing_rows),
        "isolated_timing_summary_all_raw_rows": timing,
        "isolated_timing_matched_full_clicks": matched_full_clicks,
        "isolated_timing_summary_four_real_full_clicks": real_full_timing,
        "lectures": lectures,
    }
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT.relative_to(ROOT)),
                      "lectures": len(lectures), "bridge_totals": dict(totals),
                      "usage_rows": dict(by_purpose), "cost_usd": total_cost,
                      "timing_rows_all_raw": len(timing_rows),
                      "timing_all_raw": timing,
                      "timing_four_real_full_clicks": real_full_timing},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
