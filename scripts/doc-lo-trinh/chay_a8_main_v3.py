"""Vé 12: A8 pass chính trên sáu artifact danh tính đã chốt trong kho đánh giá.

Mặc định chỉ dry-run. Lượt trả tiền cần --allow-spend --max-usd; không chạy pass phụ.
"""
import argparse
import json
import sys
from pathlib import Path

from evaluation_runtime import EvaluationStore, MeteredGemini
from doc2roadmap.application.spend_guard import SpendGuard
from doc2roadmap.application.use_cases.build_main_edges import BuildMainEdges
from doc2roadmap.application.use_cases.judge_identity import JudgeIdentity, load_identity_review
from doc2roadmap.config import Settings
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore

IDENTITY_VERSIONS = {
    "doc-1": 41, "doc-2": 33, "doc-3": 24, "doc-6": 13,
    "naive-bayes": 42, "nhap-mon-ml": 42,
}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-spend", action="store_true")
    parser.add_argument("--max-usd", type=float, default=5.0)
    parser.add_argument("--evaluation-root", type=Path, default=Path("artifacts/v3-r12-window-evaluation"))
    args = parser.parse_args()
    if not 0 < args.max_usd <= 5.0:
        parser.error("trần an toàn cho A8 main đánh giá: 5 USD")
    settings = Settings()
    output_root = args.evaluation_root
    store = EvaluationStore(JsonArtifactStore(settings.artifact_dir), JsonArtifactStore(output_root))
    concurrency = settings.vertex_concurrency if settings.llm_transport == "vertex" else settings.roadmap_concurrency
    generation = {"temperature": 0.0, "max_output_tokens": settings.extraction_max_output_tokens}
    raw = MeteredGemini(
        settings.gemini_api_key.get_secret_value() if settings.gemini_api_key else None,
        max_usd=args.max_usd,
        ledger_path=output_root / "main-llm-ledger.json",
        max_output_tokens=settings.extraction_max_output_tokens,
        transport=settings.llm_transport,
        vertex_project=settings.vertex_project,
        vertex_location=settings.vertex_location,
    )
    model = SpendGuard(raw, allowed=args.allow_spend)
    for doc_id, version in IDENTITY_VERSIONS.items():
        identity = store.load_graph(doc_id, version)
        if identity.payload.get("stage") != "identity":
            raise ValueError(f"{doc_id} v{version} không phải artifact danh tính")
        teaching = store.load_graph(doc_id, identity.manifest["upstream_version"])
        review_path = settings.artifact_dir / "a8-gold" / f"duyet-danh-tinh-{doc_id}.json"
        review = load_identity_review(review_path, doc_id=doc_id) if review_path.exists() else {}
        check = JudgeIdentity(store.base, model, concurrency=concurrency, review=review).plan(doc_id, upstream=teaching)
        if check.status != "reused" or check.artifact.version != version:
            raise ValueError(f"{doc_id}: artifact danh tính không khớp review/cấu hình hiện tại")
        main = BuildMainEdges(store, model, single_session_limit=settings.roadmap_single_session_limit,
                              concurrency=concurrency, generation=generation,
                              definition_before=settings.a8_definition_before,
                              definition_after=settings.a8_definition_after)
        plan = main.plan(doc_id, upstream=identity)
        print(doc_id, json.dumps(plan.to_dict(), ensure_ascii=False), flush=True)
        if not args.allow_spend:
            continue
        artifact, reused = main.execute(doc_id, upstream=identity)
        assert artifact.payload["stage"] == "edges" and artifact.payload["main_complete"]
        print(doc_id, "main_edges", "v" + str(artifact.version), "reused" if reused else "new", flush=True)
    print("A8 main spent/reserved USD", round(sum(row["usd"] for row in raw.ledger), 6), flush=True)
    print("STOP before A8 secondary", flush=True)


if __name__ == "__main__":
    main()
