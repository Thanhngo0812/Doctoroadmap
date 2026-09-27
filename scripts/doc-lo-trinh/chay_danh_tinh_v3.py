"""Kiểm chứng v3-10 trên ba artifact phát triển cố định; mặc định chỉ dự toán.

--allow-spend --max-usd 1.50 mới gọi Gemini. Kết quả thử ở artifacts/v3-identity-evaluation,
không trở thành cache mặc định và không tự phê duyệt các gộp chạm vàng. Không chạy A8.
"""
import argparse
import json
from pathlib import Path
from threading import Lock

from doc2roadmap.application.prerequisite_prompt import PRICING_USD_PER_MILLION as PRICE
from doc2roadmap.application.spend_guard import SpendGuard
from doc2roadmap.application.use_cases.build_roadmap import BuildRoadmap
from doc2roadmap.application.use_cases.judge_identity import JudgeIdentity, load_identity_review
from doc2roadmap.config import Settings
from doc2roadmap.domain.global_validation import strongly_connected_components
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore
from doc2roadmap.infrastructure.llm import GeminiEntityExtractor

TEACHING = {"doc-1": 33, "doc-2": 27, "doc-6": 9}


class EvaluationStore:
    """Đọc đầu vào đóng băng từ kho chính; ghi thử nghiệm vào kho riêng."""

    def __init__(self, base, output):
        self.base, self.output = base, output
        self.find_graph = output.find_graph
        self.save_graph = output.save_graph
        self.load_checkpoint = output.load_checkpoint
        self.save_checkpoint = output.save_checkpoint
        self.clear_checkpoint = output.clear_checkpoint

    def __getattr__(self, name):
        return getattr(self.base, name)


class BudgetStop(Exception):
    pass


class MeteredGemini(GeminiEntityExtractor):
    """Tính từng HTTP completion, kể cả sửa JSON; giữ chỗ trước khi gửi, không retry transport.

    Dự phòng input bằng số byte UTF-8 + 4096 token overhead và trần output được cấu hình (mặc định 1024).
    Phản hồi lỗi/thiếu usage giữ nguyên dự phòng, không coi là miễn phí. Sổ chi tiếp tục qua các lần chạy.
    """

    def __init__(self, key, *, max_usd, ledger_path, max_output_tokens=1024):
        super().__init__(key, "gemini-3.1-flash-lite", max_output_tokens=max_output_tokens, temperature=0, max_retries=0)
        self.limit, self.ledger_path, self.lock = max_usd, ledger_path, Lock()
        self.ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else []

    def _complete(self, system_prompt, turns, response_schema):
        content = system_prompt + json.dumps(response_schema, ensure_ascii=False) + "".join(t.text for t in turns)
        reserve = ((len(content.encode("utf-8")) + 4096) * PRICE["input"] + self._max_output_tokens * PRICE["output"]) / 1e6
        with self.lock:
            if sum(r["usd"] for r in self.ledger) + reserve > self.limit:
                raise BudgetStop("Chạm dự phòng ngân sách; giữ checkpoint, không gọi thêm.")
            row = {"usd": reserve, "reserved": True}
            self.ledger.append(row)
            call_index = len(self.ledger)
            JsonArtifactStore._write(self.ledger_path, self.ledger)
        text, usage = super()._complete(system_prompt, turns, response_schema)
        if usage.get("promptTokenCount") is not None and usage.get("candidatesTokenCount") is not None:
            with self.lock:
                row.update(usage=usage, reserved=False,
                    usd=(usage["promptTokenCount"] * PRICE["input"] +
                         (usage["candidatesTokenCount"] + usage.get("thoughtsTokenCount", 0)) * PRICE["output"]) / 1e6)
                JsonArtifactStore._write(self.ledger_path, self.ledger)
                if call_index % 50 == 0:
                    print(f"completion {call_index}; spent/reserved {sum(r['usd'] for r in self.ledger):.6f} USD", flush=True)
        return text, usage


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-spend", action="store_true")
    parser.add_argument("--max-usd", type=float, default=1.50)
    args = parser.parse_args()
    if not 0 < args.max_usd <= 1.50:
        parser.error("ngân sách được duyệt của lượt này: tối đa 1.50 USD")
    settings = Settings()
    root = settings.artifact_dir / "v3-identity-evaluation"
    output = JsonArtifactStore(root)
    store = EvaluationStore(JsonArtifactStore(settings.artifact_dir), output)
    key = settings.gemini_api_key.get_secret_value() if settings.gemini_api_key else "dry-run-no-key"
    raw = MeteredGemini(key, max_usd=args.max_usd, ledger_path=root / "spend.json")
    model = SpendGuard(raw, allowed=args.allow_spend)
    prepared = []
    for doc, version in TEACHING.items():
        review_path = settings.artifact_dir / "a8-gold" / f"duyet-danh-tinh-{doc}.json"
        review = load_identity_review(review_path, doc_id=doc) if review_path.exists() else {}
        judge = JudgeIdentity(store, model, concurrency=settings.roadmap_concurrency, review=review)
        upstream = store.load_graph(doc, version)
        plan = judge.plan(doc, upstream=upstream)
        print(doc, json.dumps(plan.to_dict(), ensure_ascii=False), flush=True)
        prepared.append((doc, judge, upstream))
    if not args.allow_spend:
        return
    summary = {}
    for doc, judge, upstream in prepared:
        artifact, _ = judge.execute(doc, upstream=upstream)
        roadmap, _ = BuildRoadmap(store).execute(doc, upstream=artifact)
        payload = artifact.payload
        edges = payload["requires_edges"]
        ids = {n["node_id"] for n in payload["nodes"]}
        assert not [c for c in strongly_connected_components(ids, edges) if len(c) > 1]
        assert all(e["source"] in ids and e["target"] in ids for e in edges)
        summary[doc] = {"teaching_version": upstream.version, "identity_path": str(artifact.path),
                        "stages_path": str(roadmap.path), "stats": payload["stats"],
                        "identity_usd": payload["cost_summary"]["identity_usd"], "evaluation_only": True}
        output._write(root / "summary.json", summary)
        print(doc, json.dumps(summary[doc], ensure_ascii=False), flush=True)
    print(f"Total spent/reserved: {sum(r['usd'] for r in raw.ledger):.6f} USD", flush=True)


if __name__ == "__main__":
    main()
