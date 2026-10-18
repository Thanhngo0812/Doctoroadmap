"""Offline SA-43 sampling and conservative lecture-2 price estimate."""
from __future__ import annotations

import json
from pathlib import Path

from doc2roadmap.application.phase_b.lectures import LectureUseCase, _assemble
from doc2roadmap.composition_phase_b import PhaseBRuntime
from doc2roadmap.config import Settings
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.domain.phase_b_pricing import estimate_cost
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore

PINS = [("doc-1", 57), ("xstk-ch3-1", 68), ("doc-4", 27)]
SEED = 43
ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "tmp/phaseb-sa43-dryrun.json"
PLAN = ROOT / "report/pha-b2-sa43-plan-2026-10-18.json"


def main() -> None:
    runtime = PhaseBRuntime(settings=Settings(artifact_dir=ROOT / "artifacts"),
                            b_settings=BSettings(), allow_spend=False, mode="offline")
    use_case = LectureUseCase(None, InMemoryPhaseBStore(), settings=runtime.b_settings)
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    if plan.get("seed") != SEED or len(plan.get("rows", [])) != 12:
        raise RuntimeError("preflight plan must contain 12 concepts with seed 43")
    graphs = {doc: runtime.graph(doc, version) for doc, version in PINS}
    selected = []
    for planned in plan["rows"]:
        doc_id, version, node_id = planned["doc_id"], int(planned["graph_version"]), planned["node_id"]
        if (doc_id, version) not in PINS or node_id not in graphs[doc_id].learnable_nodes:
            raise RuntimeError(f"plan pin mismatch for {doc_id}@{version}/{node_id}")
        graph = graphs[doc_id]
        context, _, _ = _assemble(graph, node_id, runtime.b_settings)
        if not context.get("bridge_candidates"):
            raise RuntimeError(f"planned concept lost its quoted prerequisite: {doc_id}/{node_id}")
        lecture = use_case.make(doc_id, str(version), graph, node_id, dry_run=True)
        selected.append({"doc_id": doc_id, "graph_version": version, "node_id": node_id,
                         "concept": graph.nodes[node_id].get("display_name") or graph.nodes[node_id].get("name"),
                         "q_prerequisites": len(context["bridge_candidates"]),
                         "input_tokens": lecture["estimate_input_tokens"],
                         "output_token_cap": runtime.b_settings.lecture_max_output_tokens,
                         "status": lecture["status"],
                         "first_estimate_usd": lecture["estimate_usd"],
                         "planned_first_estimate_usd": planned["estimate_usd"]})
    model_id = runtime.b_settings.model_id
    shared_first = sum(estimate_cost(model_id, row["input_tokens"], row["output_token_cap"])
                       for row in selected)
    one_repair_each_temp = sum(estimate_cost(model_id, row["input_tokens"] + 250,
                                             row["output_token_cap"]) for row in selected)
    conservative_total = shared_first + 2 * one_repair_each_temp
    payload = {"ticket": "SA-43", "seed": SEED,
        "pins": [{"doc_id": doc_id, "graph_version": version} for doc_id, version in PINS],
        "model_id": model_id, "settings": {
            "lecture_temperature": runtime.b_settings.lecture_temperature,
            "retry_temperatures": [0.0, 1.0],
            "max_output_tokens": runtime.b_settings.lecture_max_output_tokens,
            "input_usd_per_million": 0.25, "output_usd_per_million": 1.5},
        "logical_calls": {"shared_first_generations": 12, "repairs_per_retry_temperature": 12,
                          "max_total": 36},
        "shared_first_call_usd": round(shared_first, 8),
        "scenario_zero_repairs_usd": round(shared_first, 8),
        "scenario_one_repair_per_temperature_usd": round(conservative_total, 8),
        "repair_input_overhead_tokens_assumed": 250,
        "total_input_tokens_first_calls": sum(row["input_tokens"] for row in selected),
        "total_output_tokens_first_calls_cap": sum(row["output_token_cap"] for row in selected),
        "selected": selected, "network_calls": 0, "ledger_writes": 0, "holdout_access": False}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: payload[key] for key in ("logical_calls", "shared_first_call_usd",
        "scenario_zero_repairs_usd", "scenario_one_repair_per_temperature_usd", "network_calls")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
