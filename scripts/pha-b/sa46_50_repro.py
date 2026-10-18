"""Zero-cost local replay for the SA-46/50 quiz cases; writes only under tmp/."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from doc2roadmap.application.phase_b.quiz import QuizUseCase
from doc2roadmap.application.phase_b.retrieval import load_learning_graph
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore


OUTPUT = Path("tmp/sa46-50-repro.json")


def _run(graph, *, scope=None, node_ids=None):
    use_case = QuizUseCase(
        graph, InMemoryPhaseBStore(), model=None, settings=BSettings(),
    )
    attempt = use_case.make_quiz(
        doc_id=graph.doc_id, owner="sa46-50-offline-repro", origin="button",
        scope=scope, node_ids=node_ids, seed="37",
    )
    modules = Counter(item.get("module_id") for item in attempt["items"])
    return {
        "doc_id": graph.doc_id,
        "graph_version": graph.graph_version,
        "scope": scope,
        "seed": attempt.get("seed"),
        "status": attempt["status"],
        "total_concepts": attempt["total_concepts"],
        "ready_count": attempt["ready_count"],
        "failed_concepts": attempt["failed_concepts"],
        "module_counts": dict(modules),
        "rejections": use_case.diagnostics,
        "questions": [{
            "module_id": item.get("module_id"),
            "concept_id": item["concept_id"],
            "concept": graph.nodes[item["concept_id"]].get("display_name")
                       or graph.nodes[item["concept_id"]].get("name"),
            "stem": item["stem"],
            "options": [option["text"] for option in item["options"]],
        } for item in attempt["items"]],
        "usage": attempt["usage"],
    }


def main():
    artifacts = JsonArtifactStore(Path("artifacts"))
    results = []
    for doc_id, version in (("doc-4", 27), ("doc-1", 57)):
        graph = load_learning_graph(artifacts, doc_id, graph_version=version)
        if doc_id == "doc-4":
            results.append(_run(graph, scope="roadmap"))
            continue

        # Replay the two documented examples by their current canonical names.
        nodes = graph.payload.get("nodes", [])
        by_name = {}
        for node in nodes:
            labels = [node.get("display_name"), node.get("name")]
            labels.extend(alias.get("name") if isinstance(alias, dict) else alias
                          for alias in node.get("aliases", []))
            for label in labels:
                if label in {"Tích trực tiếp", "Nhóm"}:
                    by_name.setdefault(label, []).append(node["node_id"])
        for name in ("Tích trực tiếp", "Nhóm"):
            ids = by_name.get(name, [])
            if len(ids) != 1:
                raise RuntimeError(f"expected one {name!r} node, found {len(ids)}")
            results.append(_run(graph, node_ids=ids))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(OUTPUT),
        "model_calls": 0,
        "network_calls": 0,
        "results": [{
            "doc_id": row["doc_id"], "graph_version": row["graph_version"],
            "scope": row["scope"], "seed": row["seed"],
            "total_concepts": row["total_concepts"], "ready_count": row["ready_count"],
            "module_counts": row["module_counts"],
            "rejection_count": len(row["rejections"]),
        } for row in results],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
