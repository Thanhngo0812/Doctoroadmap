"""Shared evaluation store and completion budget, independent of retired stages.

TEACHING retains only the frozen artifact versions used by historical read-only analyses.
"""
import json
from threading import Lock
from time import sleep

from doc2roadmap.application.prerequisite_prompt import PRICING_USD_PER_MILLION as PRICE
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
    """Tính từng HTTP completion, kể cả sửa JSON; giữ chỗ trước khi gửi và qua retry transport.

    Dự phòng input bằng số byte UTF-8 + 4096 token overhead và trần output được cấu hình (mặc định 1024).
    Phản hồi lỗi/thiếu usage giữ nguyên dự phòng, không coi là miễn phí. Sổ chi tiếp tục qua các lần chạy.
    """

    def __init__(self, key, *, max_usd, ledger_path, max_output_tokens=1024,
                 transport="developer_api", vertex_project=None, vertex_location="global", limiter=None,
                 max_retries=8):
        super().__init__(key, "gemini-3.1-flash-lite", max_output_tokens=max_output_tokens,
                         temperature=0, max_retries=max_retries, transport=transport,
                         vertex_project=vertex_project, vertex_location=vertex_location, limiter=limiter)
        self.limit, self.ledger_path, self.lock = max_usd, ledger_path, Lock()
        if ledger_path.suffix == ".jsonl":
            rows = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines()] if ledger_path.exists() else []
            latest, order = {}, []
            for row in rows:
                call_id = row.get("call_id")
                if call_id is None:
                    call_id = f"legacy-{len(order) + 1}"
                if call_id not in latest:
                    order.append(call_id)
                latest[call_id] = row
            legacy = ledger_path.with_suffix(".json")
            if not rows and legacy.exists():
                for row in json.loads(legacy.read_text(encoding="utf-8")):
                    call_id = f"legacy-{len(order) + 1}"
                    row = {**row, "call_id": call_id}
                    order.append(call_id)
                    latest[call_id] = row
                    self._append_event(row)
            self.ledger = [latest[call_id] for call_id in order]
        else:
            self.ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else []

    def _append_event(self, row):
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        for attempt in range(5):
            try:
                with self.ledger_path.open("a", encoding="utf-8", newline="\n") as handle:
                    handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
                return
            except PermissionError:
                if attempt == 4:
                    raise
                sleep(0.1 * (attempt + 1))

    def _write_ledger(self, row):
        if self.ledger_path.suffix == ".jsonl":
            self._append_event(row)
        else:
            for attempt in range(5):
                try:
                    JsonArtifactStore._write(self.ledger_path, self.ledger)
                    return
                except PermissionError:
                    if attempt == 4:
                        raise
                    sleep(0.1 * (attempt + 1))

    def _complete(self, system_prompt, turns, response_schema):
        content = system_prompt + json.dumps(response_schema, ensure_ascii=False) + "".join(t.text for t in turns)
        reserve = ((len(content.encode("utf-8")) + 4096) * PRICE["input"] + self._max_output_tokens * PRICE["output"]) / 1e6
        with self.lock:
            if sum(r["usd"] for r in self.ledger) + reserve > self.limit:
                raise BudgetStop("Chạm dự phòng ngân sách; giữ checkpoint, không gọi thêm.")
            row = {"call_id": f"call-{len(self.ledger) + 1}", "usd": reserve,
                   "reserved": True, "transport": self.transport}
            self.ledger.append(row)
            call_index = len(self.ledger)
            self._write_ledger(row)
        before_429 = getattr(self._retry_state, "count", 0)
        text, usage = super()._complete(system_prompt, turns, response_schema)
        if usage.get("promptTokenCount") is not None and usage.get("candidatesTokenCount") is not None:
            with self.lock:
                row.update(usage=usage, reserved=False,
                           retry_429=getattr(self._retry_state, "count", 0) - before_429,
                    usd=(usage["promptTokenCount"] * PRICE["input"] +
                         (usage["candidatesTokenCount"] + usage.get("thoughtsTokenCount", 0)) * PRICE["output"]) / 1e6)
                self._write_ledger(row)
                if call_index % 50 == 0:
                    print(f"completion {call_index}; spent/reserved {sum(r['usd'] for r in self.ledger):.6f} USD", flush=True)
        return text, usage
