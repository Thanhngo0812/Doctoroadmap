"""Vé 09: đặt tên module trên sáu A10 artifact đã có; mặc định chỉ dry-run.

Vé 09 và 11 dùng chung spend.json, nên chạy hai driver tuần tự để giữ trần 0,75 USD.
Không chạy lại A8, A9 hoặc A10.
"""
import argparse
import json
from pathlib import Path

from chay_danh_tinh_v3 import EvaluationStore, MeteredGemini
from doc2roadmap.application.spend_guard import SpendGuard
from doc2roadmap.application.use_cases.name_modules import NameModules
from doc2roadmap.config import Settings
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-spend", action="store_true")
    parser.add_argument("--max-usd", type=float, default=0.75)
    parser.add_argument("--doc", choices=("doc-1", "doc-2", "doc-3", "doc-6", "naive-bayes", "nhap-mon-ml"))
    args = parser.parse_args()
    if not 0 < args.max_usd <= 0.75:
        parser.error("trần chung vé 09 và 11: tối đa 0,75 USD")

    settings = Settings()
    if args.allow_spend and not settings.gemini_api_key:
        parser.error("cần GEMINI_API_KEY trước khi --allow-spend")
    root = settings.artifact_dir
    first_wave = JsonArtifactStore(root / "v3-first-wave-evaluation")
    output_root = root / "v3-title-label-evaluation"
    output = JsonArtifactStore(output_root)
    store = EvaluationStore(JsonArtifactStore(root), output)
    summary = json.loads((root / "v3-first-wave-evaluation" / "summary.json").read_text(encoding="utf-8"))
    raw = MeteredGemini(settings.gemini_api_key.get_secret_value() if settings.gemini_api_key else "no-key",
                        max_usd=args.max_usd, ledger_path=output_root / "spend.json", max_output_tokens=128)
    stage = NameModules(store, SpendGuard(raw, allowed=args.allow_spend))
    prepared, plans = [], {}
    for doc_id, row in summary.items():
        if args.doc and doc_id != args.doc:
            continue
        version = int(Path(row["a10_path"]).name[1:])
        upstream = first_wave.load_graph(doc_id, version)
        prepared.append((doc_id, upstream))
        plans[doc_id] = stage.plan(doc_id, upstream=upstream).to_dict()
    print(json.dumps(plans, ensure_ascii=True, indent=2), flush=True)
    print("estimate USD", sum(plan["usd_estimate"] or 0 for plan in plans.values()), flush=True)
    if not args.allow_spend:
        return
    results = {}
    for doc_id, upstream in prepared:
        artifact, reused = stage.execute(doc_id, upstream=upstream)
        results[doc_id] = {"version": artifact.version, "path": str(artifact.path), "reused": reused,
                           "module_count": len(artifact.payload["modules"]),
                           "model_calls": artifact.payload.get("module_title_metrics", {}).get("module_title_calls", 0)}
        print(json.dumps({doc_id: results[doc_id]}, ensure_ascii=True), flush=True)
    output._write(output_root / "summary-09.json", results)


if __name__ == "__main__":
    main()
