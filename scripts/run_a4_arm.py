"""Chạy một nhánh A/B của A4/A5 vào kho artifact riêng, không đụng canonical/latest của kho chính.

Nguồn (candidates, chunks) và phiên bản canonical mới nhất — dùng làm cache quyết định — đọc ở kho chính; artifact
của nhánh ghi và tìm ở --out. Vector tên phát lại từ fixture, nên mọi nhánh dùng đúng một đồ thị đề cử.
--partition-prompt thay prompt của lượt cụm và lượt vá (hai lượt dùng chung một prompt); các biến thể đã thử nằm ở
scripts/a4_ab_prompts/. Lệnh gọi mô hình thật: chỉ chạy tay, không chạy trong test.
"""
import argparse
import json
from pathlib import Path

from doc2roadmap.application.use_cases.a4_gold import evaluate_canonical, load_gold
from doc2roadmap.application.use_cases.canonical_reasoning import CanonicalReasoning
from doc2roadmap.application.use_cases.canonicalize import Canonicalize
from doc2roadmap.config import Settings
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore
from doc2roadmap.infrastructure.embedding.replay import ReplayEmbedding
from doc2roadmap.infrastructure.llm import GeminiEntityExtractor
from doc2roadmap.infrastructure.text import SentencePieceTokenCounter

GOLD = Path("tests/fixtures/a4/gold-blind.json")


class ArmStore:
    def __init__(self, main, arm):
        self.main, self.arm = main, arm

    def __getattr__(self, name):
        return getattr(self.main, name)

    def find_canonical(self, *args, **kwargs):
        return self.arm.find_canonical(*args, **kwargs)

    def save_canonical(self, *args, **kwargs):
        return self.arm.save_canonical(*args, **kwargs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--judge-model", help="model phán cụm và vá; mặc định DOC2ROADMAP_MERGE_MODEL_ID")
    parser.add_argument("--partition-prompt", type=Path, help="file prompt thay cho a4-merge.txt và a4-repair.txt")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--doc-id", action="append", required=True)
    args = parser.parse_args()
    settings = Settings()
    main_store = JsonArtifactStore(settings.artifact_dir)
    if not args.out.resolve().is_relative_to(main_store.root.resolve()):
        raise ValueError("nhánh A/B chứa nội dung tài liệu: chỉ ghi trong artifact_dir")
    gold = load_gold(GOLD, main_store, require_complete=True)
    store = ArmStore(main_store, JsonArtifactStore(args.out))
    partition_prompt = args.partition_prompt.read_text(encoding="utf-8").strip() if args.partition_prompt else None

    def model(model_id):
        return GeminiEntityExtractor(settings.gemini_api_key.get_secret_value(), model_id,
            timeout_seconds=settings.gemini_timeout_seconds, max_retries=settings.gemini_max_retries,
            temperature=settings.extraction_temperature, max_output_tokens=settings.extraction_max_output_tokens)

    graph = {"k": settings.merge_neighbors, "ngram_threshold": settings.merge_ngram_threshold,
             "resolution": settings.merge_resolution, "seed": settings.merge_seed, "cap": settings.merge_cluster_cap}
    for doc in args.doc_id:
        embedding = ReplayEmbedding(Path(f"tests/fixtures/a4/{doc}/name-vectors.json"),
                                    expected_model_id=f"{settings.embedding_model_id}:{settings.embedding_dimensions}")
        reasoning = CanonicalReasoning(model(args.judge_model or settings.merge_model_id),
            model(settings.description_model_id),
            generation={"temperature": settings.extraction_temperature,
                        "max_output_tokens": settings.extraction_max_output_tokens},
            language_rule=settings.canonical_language_rule, batch_size=settings.canonical_batch_size,
            concurrency=settings.canonical_concurrency,
            counter=SentencePieceTokenCounter(settings.tokenizer_model, settings.tokenizer_id))
        if partition_prompt:
            reasoning.prompts = {**reasoning.prompts, "merge": partition_prompt, "repair": partition_prompt}
        artifact, reused = Canonicalize(store, embedding, graph_config=graph, reasoning=reasoning).execute(doc)
        result = evaluate_canonical(artifact, gold)
        stats = artifact.payload["stats"]
        print(json.dumps({"doc_id": doc, "version": artifact.version, "reused": reused,
                          **{key: result[key] for key in ("tp", "fp", "fn", "subtype_recall", "subtype_incorrect")},
                          "calls": {key: stats.get(key) for key in ("merge_calls", "repair_calls", "describe_calls",
                                                                    "check_calls", "merge_invalid", "repair_invalid")},
                          "subtype_rejected": stats.get("subtype_rejected"),
                          "subtype_conflicts_a3": stats.get("subtype_conflicts_a3"),
                          "deferred_groups": stats.get("deferred_groups")}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
