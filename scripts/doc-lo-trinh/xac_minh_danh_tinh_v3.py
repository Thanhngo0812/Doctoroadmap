"""V3-10b: mặc định dự toán, --allow-spend kiểm tập đóng; --run-documents chạy tài liệu theo quyết định reviewer.

Tái dùng lượt 1 đúng khoá/source từ bản thử v3-10, không chạy A8. Kết quả mới vẫn là bản chờ duyệt T18,
ở artifacts/v3-identity-verification; không thay kho mặc định hoặc quyết định của người.
"""
import argparse
import json

from chay_danh_tinh_v3 import EvaluationStore, MeteredGemini, TEACHING
from doc2roadmap.application.spend_guard import SpendGuard
from doc2roadmap.application.use_cases.build_roadmap import BuildRoadmap
from doc2roadmap.application.use_cases.judge_identity import JudgeIdentity, _concept, load_identity_review, verify_identity_pairs
from doc2roadmap.config import Settings
from doc2roadmap.domain.canonical import digest
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-spend", action="store_true")
    parser.add_argument("--run-documents", action="store_true")
    parser.add_argument("--max-usd", type=float, default=.15)
    args = parser.parse_args()
    if not 0 < args.max_usd <= .15:
        parser.error("trần của lượt xác minh này là 0.15 USD")
    settings = Settings()
    root = settings.artifact_dir / "v3-identity-verification"
    output, base = JsonArtifactStore(root), JsonArtifactStore(settings.artifact_dir)
    trial = JsonArtifactStore(settings.artifact_dir / "v3-identity-evaluation")
    store = EvaluationStore(base, output)
    # Chỉ đọc đúng checkpoint_id được use case tính; use case kiểm lại source_hash trước khi dùng.
    store.load_checkpoint = lambda doc, key: output.load_checkpoint(doc, key) or trial.load_checkpoint(doc, key)
    raw = MeteredGemini(settings.gemini_api_key.get_secret_value() if settings.gemini_api_key else "no-key",
                        max_usd=args.max_usd, ledger_path=root / "spend.json")
    model = SpendGuard(raw, allowed=args.allow_spend)
    generation = {"temperature": 0.0, "max_output_tokens": 1024}
    teaching = {doc: base.load_graph(doc, version) for doc, version in TEACHING.items()}
    nodes = {doc: {n["node_id"]: n for n in artifact.payload["nodes"]} for doc, artifact in teaching.items()}
    test_path = Path("task/v3-lo-trinh-doc-duoc/10b-tap-kiem-danh-tinh.json")
    labels = json.loads(test_path.read_text(encoding="utf-8"))["pairs"]
    inputs = [{"pair_id": f"k{i:03}", "first": _concept(nodes[row["doc_id"]][row["left"]]),
               "second": _concept(nodes[row["doc_id"]][row["right"]])} for i, row in enumerate(labels)]
    kwargs = {"generation": generation, "concurrency": settings.roadmap_concurrency}
    plan = verify_identity_pairs(store, model, "v3-10b-check", inputs, planning=True, **kwargs)
    print("check", json.dumps(plan.to_dict(), ensure_ascii=False), flush=True)
    if args.run_documents:
        for doc, upstream in teaching.items():
            review_path = settings.artifact_dir / "a8-gold" / f"duyet-danh-tinh-{doc}.json"
            review = load_identity_review(review_path, doc_id=doc) if review_path.exists() else {}
            judge = JudgeIdentity(store, model, review=review, **kwargs)
            print(doc, json.dumps(judge.plan(doc, upstream=upstream).to_dict(), ensure_ascii=False), flush=True)
    if not args.allow_spend:
        return 0
    answers, log, metrics = verify_identity_pairs(store, model, "v3-10b-check", inputs, **kwargs)
    rows = [{**row, "expected_relation": row["relation"], **answers[data["pair_id"]], "predicted": "same" if answers[data["pair_id"]]["relation"] == "dong_nhat"
             else "different"} for row, data in zip(labels, inputs)]
    scored = [r for r in rows if not r["gray"] and r["labeler"] != "human-T5"]
    different = [r for r in scored if r["label"] == "different"]
    same = [r for r in scored if r["label"] == "same"]
    human = [r for r in rows if r["labeler"] == "human-T5"]
    correct = lambda values: sum(r["predicted"] == r["label"] and r["relation"] is not None for r in values)
    assert (len(different), len(same), len(human)) == (10, 26, 9), "tập kiểm thay đổi, không tự đổi cổng"
    gates = {"reject_different": [correct(different), 10, 9], "keep_same": [correct(same), 26, 23],
             "human_T5": [correct(human), 9, 8]}
    passed = all(correct_count >= threshold for correct_count, _, threshold in gates.values())
    report = {"passed": passed, "gates": gates, "rows": rows, "metrics": dict(metrics),
              "decision_log": log, "input_hash": digest(inputs), "test_hash": digest(labels)}
    output._write(root / (plan.checkpoint_id + "-results.json"), report)
    print("GATES", json.dumps(gates), "PASS" if passed else "FAIL", flush=True)
    for row in rows:
        if row["gray"] or row["label"] != row["predicted"]:
            print(json.dumps(row, ensure_ascii=False), flush=True)
    # Reviewer nhận prompt 2 (vé 10b): số tập kiểm là thông tin, không còn là cổng buộc dừng.
    if args.run_documents:
        summary = {}
        for doc, upstream in teaching.items():
            review_path = settings.artifact_dir / "a8-gold" / f"duyet-danh-tinh-{doc}.json"
            review = load_identity_review(review_path, doc_id=doc) if review_path.exists() else {}
            artifact, _ = JudgeIdentity(store, model, review=review, **kwargs).execute(doc, upstream=upstream)
            roadmap, _ = BuildRoadmap(store).execute(doc, upstream=artifact)
            summary[doc] = {"identity_path": str(artifact.path), "stages_path": str(roadmap.path),
                            "stats": artifact.payload["stats"], "evaluation_only": True}
            output._write(root / "summary.json", summary)
            print(doc, json.dumps(summary[doc], ensure_ascii=False), flush=True)
    print("spent/reserved", sum(r["usd"] for r in raw.ledger), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
