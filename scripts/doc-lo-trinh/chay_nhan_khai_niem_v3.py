"""Vé 11b: đặt nhãn trên artifact teaching; mặc định dry-run."""
import argparse
import json
from pathlib import Path

from evaluation_runtime import EvaluationStore, MeteredGemini
from doc2roadmap.application.spend_guard import SpendGuard
from doc2roadmap.application.use_cases.name_concept_labels import NameConceptLabels
from doc2roadmap.application.use_cases.build_roadmap import BuildRoadmap
from doc2roadmap.config import Settings
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-spend", action="store_true")
    parser.add_argument("--max-usd", type=float, default=5.0)
    parser.add_argument("--upstream-summary", type=Path)
    parser.add_argument("--ledger-path", type=Path)
    args = parser.parse_args()
    if not 0 < args.max_usd <= 50:
        parser.error("trần chung dự án: tối đa 50 USD")
    if args.allow_spend and args.ledger_path is None:
        parser.error("--allow-spend cần --ledger-path dùng chung với 05b và 09b")
    settings = Settings()
    root = settings.artifact_dir
    output_root = root / "v3-11b-evaluation"
    output = JsonArtifactStore(output_root)
    store = EvaluationStore(JsonArtifactStore(root), output)
    raw = MeteredGemini(settings.gemini_api_key.get_secret_value() if settings.gemini_api_key else "no-key",
                        max_usd=args.max_usd, ledger_path=args.ledger_path or output_root / "spend.json",
                        max_output_tokens=512, transport=settings.llm_transport,
                        vertex_project=settings.vertex_project, vertex_location=settings.vertex_location)
    stage = NameConceptLabels(store, SpendGuard(raw, allowed=args.allow_spend),
                              concurrency=(settings.vertex_concurrency if settings.llm_transport == "vertex"
                                           else settings.roadmap_concurrency))
    summary = json.loads((args.upstream_summary or root / "v3-first-wave-evaluation" / "summary.json").read_text(encoding="utf-8"))
    prepared, plans = [], {}
    for doc, row in summary.items():
        artifact_path = Path(row["teaching_reuse_path"])
        version = int(artifact_path.name[1:])
        upstream = JsonArtifactStore(artifact_path.parents[2]).load_graph(doc, version)
        prepared.append((doc, upstream))
        plans[doc] = stage.plan(doc, upstream=upstream).to_dict()
    print(json.dumps(plans, ensure_ascii=True, indent=2), flush=True)
    print("estimate USD", sum(plan["usd_estimate"] or 0 for plan in plans.values()), flush=True)
    if not args.allow_spend:
        return
    results = {}
    for doc, upstream in prepared:
        artifact, reused = stage.execute(doc, upstream=upstream)
        roadmap, _ = BuildRoadmap(store, stage_cap=settings.roadmap_stage_cap).execute(doc, upstream=artifact)
        results[doc] = {"path": str(artifact.path), "version": artifact.version, "reused": reused,
                        "stats": artifact.payload["stats"], "roadmap_path": str(roadmap.path)}
        print(doc, json.dumps(results[doc], ensure_ascii=True), flush=True)
    output._write(output_root / "summary.json", results)


if __name__ == "__main__":
    main()
