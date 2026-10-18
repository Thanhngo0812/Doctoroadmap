from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from doc2roadmap.application.phase_b.retrieval import load_learning_graph
from doc2roadmap.composition_phase_b import PhaseBRuntime
from doc2roadmap.config import Settings


CAP_USD = 0.50
STORE_PATH = ROOT / "artifacts/phase_b/acceptance-sa27-v2.json"
RECORD_DIR = ROOT / "artifacts/phase_b/recordings/acceptance-sa27-v2"
PLAN_PATH = ROOT / "tmp/phaseb-sa27-dry-run.json"
RESULT_PATH = ROOT / "tmp/phaseb-sa27-live-v2.json"
PRIOR_STORE_PATH = ROOT / "artifacts/phase_b/acceptance-sa27.json"
DOCS = ("doc-1", "doc-4")


def ledger_total(store):
    return sum(float(row.get("cost_usd", 0) or 0) for row in store.usage_rows())


def prior_ledger_total():
    if not PRIOR_STORE_PATH or not PRIOR_STORE_PATH.exists():
        return 0.0
    value = json.loads(PRIOR_STORE_PATH.read_text(encoding="utf-8"))
    return sum(float(row.get("cost_usd", 0) or 0) for row in value.get("usage", []))


def save(report):
    RESULT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-spend", action="store_true",
                        help="Perform paid model calls; omitted means dry-run only.")
    parser.add_argument("--cap-usd", type=float, default=CAP_USD)
    args = parser.parse_args()
    if args.cap_usd <= 0 or args.cap_usd > CAP_USD:
        raise SystemExit(f"cap-usd must be > 0 and <= {CAP_USD:.2f}")
    if args.allow_spend and RESULT_PATH.exists():
        raise SystemExit(
            f"paid result already exists at {RESULT_PATH}; refusing to overwrite it. "
            "Use scripts/phase-b/replay_sa27_quiz.py for offline replay."
        )

    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    if not args.allow_spend:
        result = {"mode": "dry_run_only", "network_calls": 0, "artifact_writes": 0,
                  "cap_usd": args.cap_usd, "results": plan["results"],
                  "combined_estimated_usd": plan["combined_estimated_usd"]}
        RESULT_PATH.with_name("phaseb-sa27-live-dry-run-v2.json").write_text(
            json.dumps(result, ensure_ascii=True, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return
    approved_estimate = {row["doc_id"]: row["estimated_usd"] for row in plan["results"]}
    runtime = PhaseBRuntime(settings=Settings(artifact_dir=ROOT / "artifacts"),
                            mode="gemini", allow_spend=args.allow_spend,
                            store_path=STORE_PATH, record_dir=RECORD_DIR)
    prior_spend = prior_ledger_total()
    report = {"started_at": datetime.now(timezone.utc).isoformat(),
              "mode": "gemini" if args.allow_spend else "dry_run", "cap_usd": args.cap_usd,
              "store_path": str(STORE_PATH), "record_dir": str(RECORD_DIR),
              "prior_store_path": str(PRIOR_STORE_PATH) if PRIOR_STORE_PATH else None,
              "documents": [], "stopped_reason": None}

    for doc_id in DOCS:
        graph = load_learning_graph(runtime.artifacts, doc_id)
        module = min(graph.modules.values(), key=lambda row: row.get("index", 0))
        usecase = runtime.quiz(graph)
        dry = usecase.make_quiz(doc_id, module["module_id"], "sa27-acceptance",
                                graph_version=graph.graph_version, dry_run=True)
        estimate = float(dry["estimated_usd"])
        if estimate > float(approved_estimate[doc_id]) + 0.000001:
            report["stopped_reason"] = f"current estimate exceeded approved preflight for {doc_id}"
            save(report)
            break
        spent_before = prior_spend + ledger_total(runtime.store)
        if spent_before + estimate > args.cap_usd:
            report["stopped_reason"] = f"ledger plus remaining estimate exceeds cap before {doc_id}"
            save(report)
            break
        if not args.allow_spend:
            report["documents"].append({"doc_id": doc_id, "graph_version": graph.graph_version,
                                        "module_id": module["module_id"], "module_title": module["title"],
                                        "dry_run": dry, "spent_before_usd": round(spent_before, 6),
                                        "status": "dry_run_only"})
            continue

        started = time.perf_counter()
        item_times = []

        def event(row):
            if row.get("event") == "item_ready":
                item_times.append(round((time.perf_counter() - started) * 1000))

        print(f"Starting {doc_id} {module['module_id']}: estimate=${estimate:.6f}, ledger=${spent_before:.6f}",
              flush=True)
        result = usecase.make_quiz(doc_id, module["module_id"], "sa27-acceptance",
                                   graph_version=graph.graph_version, allow_spend=True, on_event=event)
        rows = [row for row in runtime.store.usage_rows(doc_id)
                if row.get("purpose") in {"quiz_gen", "quiz_verify"}]
        doc_spend = sum(float(row.get("cost_usd", 0) or 0) for row in rows)
        entry = {"doc_id": doc_id, "graph_version": graph.graph_version,
                 "module_id": module["module_id"], "module_title": module["title"],
                 "dry_run": dry, "spent_before_usd": round(spent_before, 6),
                 "actual_quiz_usd": round(doc_spend, 6),
                 "total_ledger_usd": round(prior_spend + ledger_total(runtime.store), 6),
                 "status": result.get("status"), "total_concepts": result.get("total_concepts"),
                 "ready_count": result.get("ready_count"), "failed_concepts": len(result.get("failed_concepts", [])),
                 "elapsed_ms": round((time.perf_counter() - started) * 1000),
                 "first_item_ms": item_times[0] if item_times else None,
                 "last_item_ms": item_times[-1] if item_times else None,
                 "usage_rows": len(rows),
                 "purpose_usage": {purpose: {
                     "calls": sum(row.get("purpose") == purpose for row in rows),
                     "usd": round(sum(float(row.get("cost_usd", 0) or 0) for row in rows
                                       if row.get("purpose") == purpose), 6),
                     "input_tokens": sum(row.get("input_tokens", 0) for row in rows
                                          if row.get("purpose") == purpose),
                     "output_tokens": sum(row.get("output_tokens", 0) for row in rows
                                           if row.get("purpose") == purpose),
                 } for purpose in ("quiz_gen", "quiz_verify")}}
        report["documents"].append(entry)
        save(report)
        print(f"Finished {doc_id}: {entry['status']} ready={entry['ready_count']} "
              f"cost=${entry['actual_quiz_usd']:.6f}; first={entry['first_item_ms']}ms "
              f"last={entry['last_item_ms']}ms", flush=True)
        if entry["total_ledger_usd"] > args.cap_usd:
            report["stopped_reason"] = "measured ledger exceeded cap; stopped before next module"
            save(report)
            break

    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    report["total_ledger_usd"] = round(prior_spend + ledger_total(runtime.store), 6)
    save(report)
    print(json.dumps(report, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
