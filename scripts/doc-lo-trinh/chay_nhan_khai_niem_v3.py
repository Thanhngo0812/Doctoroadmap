"""Vé 11 trên sáu artifact teaching đã có; mặc định dry-run, không chạy lại A8/neo/danh tính.

Vé 09 và 11 dùng chung spend.json; chạy hai driver tuần tự để giữ trần 0,75 USD.
"""
import argparse
import json
from pathlib import Path

from chay_danh_tinh_v3 import EvaluationStore, MeteredGemini
from doc2roadmap.application.spend_guard import SpendGuard
from doc2roadmap.application.use_cases.name_concept_labels import NameConceptLabels
from doc2roadmap.application.use_cases.build_roadmap import BuildRoadmap
from doc2roadmap.config import Settings
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-spend", action="store_true")
    parser.add_argument("--max-usd", type=float, default=0.75)
    args = parser.parse_args()
    if not 0 < args.max_usd <= 0.75:
        parser.error("trần chung vé 09 và 11: tối đa 0,75 USD")
    settings = Settings()
    root = settings.artifact_dir
    source = JsonArtifactStore(root / "v3-first-wave-evaluation")
    output_root = root / "v3-concept-label-evaluation"
    output = JsonArtifactStore(output_root)
    store = EvaluationStore(JsonArtifactStore(root), output)
    raw = MeteredGemini(settings.gemini_api_key.get_secret_value() if settings.gemini_api_key else "no-key",
                        max_usd=args.max_usd, ledger_path=root / "v3-title-label-evaluation" / "spend.json",
                        max_output_tokens=512)
    stage = NameConceptLabels(store, SpendGuard(raw, allowed=args.allow_spend),
                              concurrency=settings.roadmap_concurrency)
    summary = json.loads((root / "v3-first-wave-evaluation" / "summary.json").read_text(encoding="utf-8"))
    prepared, plans = [], {}
    for doc, row in summary.items():
        version = int(Path(row["teaching_reuse_path"]).name[1:])
        upstream = source.load_graph(doc, version)
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
