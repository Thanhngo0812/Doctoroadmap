"""Vé 09b: đặt tên module trên A10 artifact đã có; mặc định chỉ dry-run.

Vé 05b, 09b và 11b dùng chung spend.json; chạy các driver tuần tự.
Không chạy lại A8, A9 hoặc A10.
"""
import argparse
import json
from pathlib import Path

from evaluation_runtime import EvaluationStore, MeteredGemini
from doc2roadmap.application.spend_guard import SpendGuard
from doc2roadmap.application.use_cases.name_modules import NameModules
from doc2roadmap.config import Settings
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-spend", action="store_true")
    parser.add_argument("--max-usd", type=float, default=0.5)
    parser.add_argument("--upstream-summary", type=Path)
    parser.add_argument("--ledger-path", type=Path)
    parser.add_argument("--doc", choices=("doc-1", "doc-2", "doc-3", "doc-6", "naive-bayes", "nhap-mon-ml"))
    args = parser.parse_args()
    if not 0 < args.max_usd <= 50:
        parser.error("trần chung dự án: tối đa 50 USD")
    if args.allow_spend and args.ledger_path is None:
        parser.error("--allow-spend cần --ledger-path dùng chung với 05b và 11b")

    settings = Settings()
    if args.allow_spend and settings.llm_transport == "developer_api" and not settings.gemini_api_key:
        parser.error("cần GEMINI_API_KEY trước khi --allow-spend")
    root = settings.artifact_dir
    output_root = root / "v3-09b-evaluation"
    output = JsonArtifactStore(output_root)
    store = EvaluationStore(JsonArtifactStore(root), output)
    summary_path = args.upstream_summary or root / "v3-first-wave-evaluation" / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    raw = MeteredGemini(settings.gemini_api_key.get_secret_value() if settings.gemini_api_key else "no-key",
                        max_usd=args.max_usd, ledger_path=args.ledger_path or output_root / "spend.json",
                        max_output_tokens=128,transport=settings.llm_transport,
                        vertex_project=settings.vertex_project,vertex_location=settings.vertex_location)
    prior = JsonArtifactStore(root / "v3-title-label-evaluation")
    prepared, plans = [], {}
    for doc_id, row in summary.items():
        if args.doc and doc_id != args.doc:
            continue
        version = int(Path(row["a10_path"]).name[1:])
        upstream = JsonArtifactStore(Path(row["a10_path"]).parents[2]).load_graph(doc_id, version)
        try:
            old = prior.load_latest_graph(doc_id)
        except FileNotFoundError:
            old = None
        stage = NameModules(store, SpendGuard(raw, allowed=args.allow_spend), reuse_artifact=old,
                            concurrency=(settings.vertex_concurrency if settings.llm_transport == "vertex"
                                         else settings.roadmap_concurrency))
        prepared.append((doc_id, upstream, stage))
        plans[doc_id] = stage.plan(doc_id, upstream=upstream).to_dict()
    print(json.dumps(plans, ensure_ascii=True, indent=2), flush=True)
    print("estimate USD", sum(plan["usd_estimate"] or 0 for plan in plans.values()), flush=True)
    if not args.allow_spend:
        return
    results = {}
    for doc_id, upstream, stage in prepared:
        artifact, reused = stage.execute(doc_id, upstream=upstream)
        results[doc_id] = {"version": artifact.version, "path": str(artifact.path), "reused": reused,
                           "module_count": len(artifact.payload["modules"]),
                           "model_calls": artifact.payload.get("module_title_metrics", {}).get("module_title_calls", 0)}
        print(json.dumps({doc_id: results[doc_id]}, ensure_ascii=True), flush=True)
    output._write(output_root / "summary-09b.json", results)


if __name__ == "__main__":
    main()
