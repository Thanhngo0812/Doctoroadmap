"""Vé 12: chạy A6, A7, neo, danh tính; dừng trước A8. Mặc định chỉ dự toán.

Trần được duyệt cho sáu tài liệu: 5 USD (4.5 LLM + 0.5 embedding theo byte UTF-8).
"""
import argparse
import json
import sys
from pathlib import Path

from evaluation_runtime import BudgetStop, MeteredGemini
from doc2roadmap.application.spend_guard import SpendGuard
from doc2roadmap.application.use_cases.anchor_concepts import AnchorConcepts
from doc2roadmap.application.use_cases.build_mentions import BuildMentions
from doc2roadmap.application.use_cases.build_provenance import BuildProvenance
from doc2roadmap.application.use_cases.judge_identity import JudgeIdentity, load_identity_review
from doc2roadmap.composition import _a3_dependencies
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore

DOCS = ("doc-1", "doc-2", "doc-3", "doc-6", "naive-bayes", "nhap-mon-ml")
EMBEDDING_USD_PER_MILLION_INPUT = 0.15


class BudgetedEmbedding:
    def __init__(self, embedding, ledger_path: Path, *, limit=0.5):
        self.embedding, self.ledger_path, self.limit = embedding, ledger_path, limit
        self.ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else []

    def __getattr__(self, name):
        return getattr(self.embedding, name)

    def embed(self, requests):
        # UTF-8 byte count conservatively bounds input token count for these plain-text requests.
        reserve = sum(len(request.text.encode("utf-8")) for request in requests) * EMBEDDING_USD_PER_MILLION_INPUT / 1e6
        if sum(row["usd_upper_bound"] for row in self.ledger) + reserve > self.limit:
            raise BudgetStop("embedding upper bound vượt 0.5 USD; chưa gọi Vertex")
        self.ledger.append({"texts": len(requests), "usd_upper_bound": reserve, "reserved": True})
        JsonArtifactStore._write(self.ledger_path, self.ledger)
        result = self.embedding.embed(requests)
        self.ledger[-1]["reserved"] = False
        JsonArtifactStore._write(self.ledger_path, self.ledger)
        return result


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--doc", choices=DOCS)
    parser.add_argument("--allow-spend", action="store_true")
    parser.add_argument("--max-usd", type=float, default=5.0)
    args = parser.parse_args()
    if not 0 < args.max_usd <= 5:
        parser.error("trần lượt pre-A8 được duyệt: 5 USD")
    settings, store, embedding = _a3_dependencies()
    root = settings.artifact_dir / "v3-r12-pre-a8"
    concurrency = settings.vertex_concurrency if settings.llm_transport == "vertex" else settings.roadmap_concurrency
    budgeted_embedding = SpendGuard(BudgetedEmbedding(embedding, root / "embedding-ledger.json",
        limit=min(0.5, args.max_usd / 10)), allowed=args.allow_spend)
    def model(output_tokens):
        # Construct at stage boundary so each instance reloads the latest shared ledger.
        raw = MeteredGemini(settings.gemini_api_key.get_secret_value() if settings.gemini_api_key else None,
            max_usd=args.max_usd * 0.9, ledger_path=root / "llm-ledger.json", max_output_tokens=output_tokens,
            transport=settings.llm_transport, vertex_project=settings.vertex_project,
            vertex_location=settings.vertex_location)
        return SpendGuard(raw, allowed=args.allow_spend)
    selected = [doc for doc in DOCS if not args.doc or doc == args.doc]
    pending_bytes = 0
    for doc_id in selected:
        preview = BuildMentions(store, budgeted_embedding,
            dense_top_k=settings.mention_dense_top_k, dense_min_z=settings.mention_dense_min_z,
            pair_cluster_top_k=settings.mention_pair_cluster_top_k,
            common_name_fraction=settings.mention_common_name_fraction)
        if preview.plan(doc_id).status == "reused":
            continue
        clusters = preview._clusters(doc_id)
        pending_bytes += sum(len((node.get("description") or node["name"]).encode("utf-8"))
                             for node in clusters.payload["nodes"] if node.get("learnable"))
    embedding_bound = pending_bytes * EMBEDDING_USD_PER_MILLION_INPUT / 1e6
    print("embedding_preflight_upper_bound_usd", round(embedding_bound, 6), flush=True)
    if args.allow_spend and sum(row["usd_upper_bound"] for row in budgeted_embedding._model.ledger) + embedding_bound > min(0.5, args.max_usd / 10):
        raise BudgetStop("toàn bộ lượt embedding có thể vượt quỹ 0.5 USD; chưa gọi Vertex")
    for doc_id in selected:
        mentions = BuildMentions(store, budgeted_embedding,
            dense_top_k=settings.mention_dense_top_k, dense_min_z=settings.mention_dense_min_z,
            pair_cluster_top_k=settings.mention_pair_cluster_top_k,
            common_name_fraction=settings.mention_common_name_fraction)
        review_path = settings.artifact_dir / "a8-gold" / f"duyet-danh-tinh-{doc_id}.json"
        review = load_identity_review(review_path, doc_id=doc_id) if review_path.exists() else {}
        stages = (("mentions", lambda: mentions),
                  ("provenance", lambda: BuildProvenance(store, model(8192), concurrency=concurrency,
                     generation={"temperature": 0.0, "max_output_tokens": 8192})),
                  ("teaching", lambda: AnchorConcepts(store, model(2048), concurrency=concurrency)),
                  ("identity", lambda: JudgeIdentity(store, model(1024), concurrency=concurrency, review=review)))
        for name, make_stage in stages:
            stage = make_stage()
            plan = stage.plan(doc_id) if name == "mentions" else stage.plan(doc_id, upstream=artifact)
            print(doc_id, name, json.dumps(plan.to_dict(), ensure_ascii=False), flush=True)
            if not args.allow_spend:
                if plan.artifact is None:
                    break
                artifact = plan.artifact
                continue
            artifact, reused = stage.execute(doc_id) if name == "mentions" else stage.execute(doc_id, upstream=artifact)
            print(doc_id, name, "v" + str(artifact.version), "reused" if reused else "new", flush=True)
        if args.allow_spend:
            print(doc_id, "STOP before A8", flush=True)
    llm_ledger = root / "llm-ledger.json"
    llm_rows = json.loads(llm_ledger.read_text(encoding="utf-8")) if llm_ledger.exists() else []
    print("LLM spent/reserved USD", round(sum(row["usd"] for row in llm_rows), 6), flush=True)
    print("Embedding upper-bound USD", round(sum(row["usd_upper_bound"] for row in budgeted_embedding._model.ledger), 6), flush=True)


if __name__ == "__main__":
    main()
