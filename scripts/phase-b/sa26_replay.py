from __future__ import annotations

import json
from pathlib import Path

from doc2roadmap.application.phase_b.lectures import LectureUseCase
from doc2roadmap.composition_phase_b import PhaseBRuntime
from doc2roadmap.config import Settings
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore
from doc2roadmap.infrastructure.llm.phase_b import ReplayToolModel


ROOT = Path.cwd()
SOURCE = ROOT / "tmp/phaseb-live-group2-v2.json"
FIXTURE = ROOT / "tmp/phaseb-live-group2-v2-merged-recordings/lecture.json"
OUTPUT = ROOT / "tmp/phaseb-sa26-replay.json"


def main() -> None:
    live = json.loads(SOURCE.read_text(encoding="utf-8"))
    fixture_metadata = json.loads(FIXTURE.read_text(encoding="utf-8"))
    model = ReplayToolModel(FIXTURE, prompt_hash=fixture_metadata["prompt_hash"])
    runtime = PhaseBRuntime(settings=Settings(artifact_dir=Path("artifacts")),
                            b_settings=BSettings(), allow_spend=False, mode="offline")
    store = InMemoryPhaseBStore()
    results = []
    for operation in (row for row in live["operations"] if row["kind"] == "lecture"):
        graph = runtime.graph(operation["doc_id"], operation["graph_version"])
        # The saved xstk/doc-4 prompts were assembled before SA-26 fixed the
        # used_later edge direction. Preserve that recorded prompt context so
        # ReplayToolModel can supply the exact saved answer; the production
        # direction is covered by the focused A -> B regression test.
        if operation["doc_id"] in {"xstk-ch3-1", "doc-4"}:
            traverse = graph.traverse
            graph.traverse = lambda node_id, edge_type, direction="out", _traverse=traverse: _traverse(
                node_id, edge_type, "in" if direction == "out" and edge_type == "requires" else direction)
        result = LectureUseCase(model, store, settings=runtime.b_settings).make(
            operation["doc_id"], str(operation["graph_version"]), graph, operation["node_id"],
            allow_spend=True)
        results.append({
            "doc_id": operation["doc_id"], "graph_version": operation["graph_version"],
            "node_id": operation["node_id"], "concept": operation["concept"],
            "before_status": operation["result"].get("status"),
            "after_status": result.get("status"), "warnings": result.get("warnings", []),
            "lecture_key": result.get("lecture_key"), "usage": result.get("usage", {}),
        })
    ledger = store.usage_rows()
    payload = {"results": results, "usage_rows": ledger,
               "total_cost_usd": sum(float(row.get("cost_usd", 0) or 0) for row in ledger),
               "replayed_sessions": len(model._reserved)}
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"count": len(results), "statuses": {
        status: sum(row["after_status"] == status for row in results)
        for status in sorted({row["after_status"] for row in results})},
        "cost_usd": payload["total_cost_usd"], "sessions": payload["replayed_sessions"]},
        ensure_ascii=False))


if __name__ == "__main__":
    main()
