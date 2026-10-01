"""Vé 12: thử pass phụ trên cặp thuộc hai chương vàng, tách khỏi cache production.

Chỉ dùng danh sách ID đích để chọn cặp; KHÔNG đưa nhãn cạnh vàng vào prompt.
Mặc định dry-run. --allow-spend --max-usd 2 cần chủ dự án duyệt trước khi gọi Vertex.
"""
import argparse
import json
import sys
from pathlib import Path
from types import SimpleNamespace

from chay_danh_tinh_v3 import EvaluationStore, MeteredGemini
from doc2roadmap.application.spend_guard import SpendGuard
from doc2roadmap.application.use_cases.build_secondary_edges import BuildSecondaryEdges
from doc2roadmap.config import Settings
from doc2roadmap.domain.secondary import select_secondary_pairs
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore

CASES = (("doc-1", "doc-1-10-12-vang.json"),
         ("doc-2", "doc-2-98-115-vang.json"))


def pilot_pairs(payload, target_ids):
    identity = payload.get("identity_map", {})
    targets = {identity.get(node_id, node_id) for node_id in target_ids}
    askable, _ = select_secondary_pairs(payload["nodes"], payload["suspected_pairs"],
                                        payload["pair_cluster_ledger"], payload["main_edges"],
                                        route=payload["routing"]["route"])
    return [pair for pair in askable if pair["left"] in targets and pair["right"] in targets]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-spend", action="store_true")
    parser.add_argument("--max-usd", type=float, default=2.0)
    parser.add_argument("--evaluation-root", type=Path, default=Path("artifacts/v3-r12-window-evaluation"))
    args = parser.parse_args()
    if not 0 < args.max_usd <= 2:
        parser.error("trần pilot nếu được duyệt: 2 USD")
    settings = Settings()
    if settings.llm_transport != "vertex":
        raise ValueError("pilot này chỉ được duyệt qua Vertex")
    output_root = args.evaluation_root
    store = EvaluationStore(JsonArtifactStore(settings.artifact_dir), JsonArtifactStore(output_root))
    raw = MeteredGemini(settings.gemini_api_key.get_secret_value() if settings.gemini_api_key else None,
                        max_usd=args.max_usd, ledger_path=output_root / "pilot-llm-ledger.json",
                        max_output_tokens=settings.extraction_max_output_tokens,
                        transport=settings.llm_transport, vertex_project=settings.vertex_project,
                        vertex_location=settings.vertex_location)
    model = SpendGuard(raw, allowed=args.allow_spend)
    for doc_id, gold_name in CASES:
        main_artifact = store.output.load_graph(doc_id, 1)
        if main_artifact.payload.get("stage") != "edges" or not main_artifact.payload.get("main_complete"):
            raise ValueError(f"{doc_id} v{main_artifact.version} không phải A8 main hoàn chỉnh")
        # Đọc đúng trường targets. Nhãn edges của bộ vàng không đi vào payload hay prompt.
        target_ids = json.loads((settings.artifact_dir / "a8-gold" / gold_name).read_text(encoding="utf-8"))["targets"]
        pairs = pilot_pairs(main_artifact.payload, target_ids)
        pilot_main = SimpleNamespace(payload={**main_artifact.payload, "suspected_pairs": pairs},
                                     manifest=main_artifact.manifest, version=main_artifact.version)
        stage = BuildSecondaryEdges(store, model,
                                    concurrency=settings.vertex_concurrency,
                                    generation=main_artifact.manifest["config"]["generation"])
        plan = stage.plan(doc_id, upstream=pilot_main)
        print(doc_id, "pilot_pairs", len(pairs), json.dumps(plan.to_dict(), ensure_ascii=False), flush=True)
        if not args.allow_spend:
            continue
        artifact, reused = stage.execute(doc_id, upstream=pilot_main)
        print(doc_id, "pilot_secondary", "v" + str(artifact.version), "reused" if reused else "new", flush=True)
    print("pilot spent/reserved USD", round(sum(row["usd"] for row in raw.ledger), 6), flush=True)
    print("Evaluation-only; production secondary untouched", flush=True)


if __name__ == "__main__":
    main()
