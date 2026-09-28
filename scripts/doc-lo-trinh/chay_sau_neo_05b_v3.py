"""Đo end-to-end sau neo 05b: identity → nhãn → A10 → tên; không chạy lại A8."""
import argparse
import json
from pathlib import Path

from chay_danh_tinh_v3 import EvaluationStore, MeteredGemini
from doc2roadmap.application.use_cases.a8_score import score_roadmap_order
from doc2roadmap.application.spend_guard import SpendGuard
from doc2roadmap.application.use_cases.build_roadmap import BuildRoadmap
from doc2roadmap.application.use_cases.judge_identity import JudgeIdentity, load_identity_review
from doc2roadmap.application.use_cases.name_concept_labels import NameConceptLabels
from doc2roadmap.application.use_cases.name_modules import NameModules
from doc2roadmap.config import Settings
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--doc", choices=("doc-1", "doc-2", "doc-3", "doc-6", "naive-bayes", "nhap-mon-ml"))
    parser.add_argument("--allow-spend", action="store_true")
    parser.add_argument("--max-usd", type=float, default=5.0)
    args = parser.parse_args()
    if not 0 < args.max_usd <= 50:
        parser.error("trần dự án tối đa 50 USD")
    settings = Settings()
    root = settings.artifact_dir / "v3-05b-a9v10-evaluation"
    summary_path = root / "anchors05b-summary.json"
    anchors = json.loads(summary_path.read_text(encoding="utf-8"))
    output = JsonArtifactStore(root)
    store = EvaluationStore(JsonArtifactStore(settings.artifact_dir), output)
    def model(output_tokens):
        return SpendGuard(MeteredGemini(
            settings.gemini_api_key.get_secret_value() if settings.gemini_api_key else None,
            max_usd=args.max_usd, ledger_path=root / "spend.json", max_output_tokens=output_tokens,
            transport=settings.llm_transport, vertex_project=settings.vertex_project,
            vertex_location=settings.vertex_location), allowed=args.allow_spend)
    concurrency = settings.vertex_concurrency if settings.llm_transport == "vertex" else settings.roadmap_concurrency
    finished = output._read(root / "end-to-end-summary.json") if (root / "end-to-end-summary.json").exists() else {}
    for doc_id, row in anchors.items():
        if args.doc and doc_id != args.doc:
            continue
        teaching = output.load_graph(doc_id, row["version"])
        review_path = settings.artifact_dir / "a8-gold" / f"duyet-danh-tinh-{doc_id}.json"
        review = load_identity_review(review_path, doc_id=doc_id) if review_path.exists() else {}
        identity_stage = JudgeIdentity(store, model(1024), concurrency=concurrency, review=review)
        plan = identity_stage.plan(doc_id, upstream=teaching)
        print(doc_id, "identity", json.dumps(plan.to_dict(), ensure_ascii=False), flush=True)
        if not args.allow_spend:
            continue
        identity, _ = identity_stage.execute(doc_id, upstream=teaching)
        labels, _ = NameConceptLabels(store, model(512), concurrency=concurrency).execute(doc_id, upstream=identity)
        roadmap, _ = BuildRoadmap(store, stage_cap=settings.roadmap_stage_cap).execute(doc_id, upstream=labels)
        try:
            old_titles = JsonArtifactStore(settings.artifact_dir / "v3-title-label-evaluation").load_latest_graph(doc_id)
        except FileNotFoundError:
            old_titles = None
        titled, _ = NameModules(store, model(128), concurrency=concurrency,
                                reuse_artifact=old_titles).execute(doc_id, upstream=roadmap)
        finished[doc_id] = {"teaching_reuse_path": str(teaching.path), "identity_path": str(identity.path),
                            "labels_path": str(labels.path), "a10_path": str(roadmap.path),
                            "titled_path": str(titled.path), "module_count": len(titled.payload["modules"])}
        gold_names = {"doc-1": "doc-1-10-12-vang.json", "doc-2": "doc-2-98-115-vang.json"}
        if doc_id in gold_names:
            score = score_roadmap_order(Path(titled.path) / "graph.json",
                                         [settings.artifact_dir / "a8-gold" / gold_names[doc_id]])
            finished[doc_id]["quality"] = {
                "q6": score["gold_order"], "q7": score["target_coverage"]["mean_coverage"],
                "q7b": score["target_precision"]["mean_precision"],
                "gold_edges": score["gold_edge_count"]}
        output._write(root / "end-to-end-summary.json", finished)
        print(doc_id, json.dumps(finished[doc_id], ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
