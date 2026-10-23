"""`lecture-3`: a prose lecture written by the model from wide book context and page pictures.

The lecture is shown as written. Checks only fill the admin `validation` block; none of them blocks, edits or
repeats a lecture (ADR 0024, ADR 0025). Spec: doc/bai-giang-3-spec.md.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from threading import Thread
from time import perf_counter
from typing import Any, Callable
from zoneinfo import ZoneInfo

from doc2roadmap.application.phase_b.budget import DailyLimitExceeded, DailySpendGuard, spending_call
from doc2roadmap.application.phase_b.clock import SystemClock
from doc2roadmap.application.phase_b.common import stable_json
from doc2roadmap.application.phase_b.lecture_context3 import (
    FORMULA_MARK, formula_pages, gather_chunks, prerequisite_rows, source_rows, source_texts, user_message,
)
from doc2roadmap.application.phase_b.lectures import _aggregate_usage, _assemble, _without_learner_status
from doc2roadmap.application.ports.page_images import PageImages
from doc2roadmap.domain.phase_b_limits import BSettings, context_hash, usage_row
from doc2roadmap.domain.phase_b_pricing import estimate_cost, token_cost

SYSTEM_TEMPLATE = """Bạn là một giảng viên đại học giỏi và tận tâm. Bạn viết bài giảng bằng tiếng Việt cho sinh viên đang tự học từ một cuốn sách. Mục tiêu: đọc xong, sinh viên hiểu thật sự khái niệm, không chỉ thuộc định nghĩa.

Cách viết:
- Văn xuôi tự nhiên, mạch lạc, như đang giảng trên lớp: gần gũi nhưng chính xác. Không liệt kê khô khan, không lặp lại cùng một ý bằng lời khác.
- Mở đầu bằng một hai câu cho thấy khái niệm này giải quyết vấn đề gì, hay vì sao cần nó. Nếu có khái niệm tiên quyết, nối sang nó tự nhiên; không viết "như bạn đã học".
- Giải thích trực giác trước, rồi nêu chính xác định nghĩa hay phát biểu theo sách.
- Có ít nhất một ví dụ cụ thể, giải từng bước. Ưu tiên ví dụ trong sách. Được thêm một ví dụ hay hình ảnh so sánh đời thường do bạn nghĩ ra nếu nó giúp hiểu, miễn là đúng.
- Nêu một hai chỗ người học hay nhầm, hoặc phân biệt với khái niệm gần.
- Kết bằng một câu cho biết khái niệm này sẽ được dùng vào đâu tiếp theo, dựa trên danh sách "Khái niệm tiếp theo" nếu có.
- Cuối bài: một câu hỏi tự kiểm tra ngắn, kèm đáp án.
{self_check_line}
Trung thực với sách:
- Sách là chuẩn. Không viết điều mâu thuẫn với sách. Dùng đúng ký hiệu và thuật ngữ của sách.
- Viết công thức bằng LaTeX trong $...$ hoặc $$...$$.
- {formula_rule}
- Đoạn nào dựa vào sách thì gắn nhãn nguồn như [S2] ở cuối đoạn. Phần trực giác hay ví dụ tự nghĩ thì không cần nhãn.
- Nếu tư liệu nói ít về khái niệm, vẫn giảng đầy đủ bằng hiểu biết chung, nhưng không mâu thuẫn với sách.

Định dạng: Markdown, có thể dùng vài tiêu đề nhỏ (###) nếu giúp dễ đọc. Dài khoảng 300–550 từ, tuỳ khái niệm khó hay dễ. Không chào hỏi, không nói về bản thân, không nhắc tới "tư liệu" hay "đoạn trích"."""
# The one line added to the spec text: it lets code split the self-check off the lesson.
SELF_CHECK_LINE = ('- Mục tự kiểm tra viết đúng khuôn: một dòng "### Tự kiểm tra", rồi một dòng "**Câu hỏi:** …", '
                   'rồi một dòng "**Đáp án:** …".\n')
FORMULA_RULE_WITH_IMAGES = ('Chữ "[formula]" là chỗ công thức bị mất khi trích PDF. '
                            'Ảnh các trang sách được đính kèm: đọc công thức đúng từ ảnh.')
FORMULA_RULE_TEXT_ONLY = ('Chữ "[formula]" là chỗ công thức bị mất khi trích PDF. '
                          'Đừng đoán công thức bạn không chắc; khi đó diễn đạt bằng lời.')
IMAGE_TOKEN_ESTIMATE = 1300
VALIDATION_VERSION = "lecture3-validation-1"
_MESSAGES = {
    "loi_mang": "Chưa kết nối được tới mô hình để viết bài giảng. Bạn thử lại sau ít phút.",
    "het_thoi_gian": "Mô hình trả lời quá lâu nên bài giảng chưa viết xong. Bạn thử lại sau ít phút.",
    "tran_he_thong": "Hôm nay hệ thống đã dùng hết hạn mức viết bài giảng. Bạn thử lại vào ngày mai.",
    "khong_dung_duoc": "Mô hình chưa viết được bài giảng dùng được cho khái niệm này. Bạn thử lại.",
    "khong_co_mo_hinh": "Chưa có mô hình để viết bài giảng ở chế độ này.",
}


def system_prompt(with_images: bool) -> str:
    rule = FORMULA_RULE_WITH_IMAGES if with_images else FORMULA_RULE_TEXT_ONLY
    return SYSTEM_TEMPLATE.replace("{self_check_line}", SELF_CHECK_LINE).replace("{formula_rule}", rule)


_HEADING = re.compile(r"^[ \t]*#{2,4}[ \t]*Tự kiểm tra[ \t:]*$", re.IGNORECASE | re.MULTILINE)
_QUESTION = re.compile(r"^[ \t]*\*\*Câu hỏi:?\*\*:?[ \t]*", re.MULTILINE)
_ANSWER = re.compile(r"^[ \t]*\*\*Đáp án:?\*\*:?[ \t]*", re.MULTILINE)


def split_self_check(text: str) -> tuple[str, dict[str, str] | None]:
    """Lesson without its `### Tự kiểm tra` section, and that section. A different shape leaves the lesson whole."""
    headings = list(_HEADING.finditer(text))
    if not headings:
        return text, None
    heading = headings[-1]
    tail = text[heading.end():]
    question = _QUESTION.search(tail)
    answer = _ANSWER.search(tail, question.end()) if question else None
    if not question or not answer:
        return text, None
    parts = {"question_md": tail[question.end():answer.start()].strip(), "answer_md": tail[answer.end():].strip()}
    body = text[:heading.start()].rstrip()
    if not body or not parts["question_md"] or not parts["answer_md"]:
        return text, None
    return body, parts


_LABEL_GROUP = re.compile(r"\[(S\d+(?:\s*[,;]\s*S\d+)*)\]")


def _words(text: str) -> list[str]:
    return re.findall(r"\w+", unicodedata.normalize("NFC", text).casefold())


def _bigrams(words: list[str]) -> set[tuple[str, str]]:
    return set(zip(words, words[1:]))


def _repeated_8grams(words: list[str]) -> int:
    counts = Counter(tuple(words[index:index + 8]) for index in range(max(0, len(words) - 7)))
    return sum(count >= 3 for count in counts.values())


def build_validation(text: str, sources: dict[str, str], *, finish_reason: str | None, images_sent: int,
                     pages_wanted: int, self_check_found: bool) -> dict[str, Any]:
    """Admin log of one lecture. Nothing here changes or blocks the lecture."""
    scores: dict[str, list[float]] = {}
    for paragraph in re.split(r"\n\s*\n", text):
        labels = [label.strip() for group in _LABEL_GROUP.findall(paragraph) for label in re.split(r"[,;]", group)]
        grams = _bigrams(_words(_LABEL_GROUP.sub(" ", paragraph)))
        for label in labels:
            values = scores.setdefault(label, [])
            if label in sources and grams:
                values.append(len(grams & _bigrams(_words(sources[label]))) / len(grams))
    return {"word_count": len(re.findall(r"\w+", text)), "has_self_check": self_check_found,
            "khong_tach_tu_kiem": not self_check_found,
            "labels": {label: round(sum(values) / len(values), 3) if values else None
                       for label, values in sorted(scores.items()) if label in sources},
            "unknown_labels": sorted(label for label in scores if label not in sources),
            "formula_left": FORMULA_MARK in text, "repeated_8grams": _repeated_8grams(_words(text)),
            "finish_reason": finish_reason, "thieu_anh_trang": images_sent < pages_wanted,
            "images_sent": images_sent}


@dataclass
class _Attempt:
    text: str = ""
    finish_reason: str | None = None
    usage: dict[str, Any] = field(default_factory=dict)
    cost_usd: float = 0.0
    elapsed_ms: int = 0
    ttft_ms: int | None = None
    error: BaseException | None = None
    timed_out: bool = False

    @property
    def usable(self) -> bool:
        return bool(re.search(r"\w", self.text))


class Lecture3UseCase:
    def __init__(self, model: Any, store: Any, *, page_images: PageImages | None = None,
                 settings: BSettings | None = None, clock: Any | None = None, progress: Any | None = None,
                 spend_guard: Any | None = None) -> None:
        self.model = model
        self.store = store
        self.page_images = page_images
        self.settings = settings or BSettings()
        self.clock = clock or SystemClock()
        self.progress = progress
        self.spend_guard = spend_guard or DailySpendGuard(store, settings=self.settings, clock=self.clock)

    def get(self, doc_id: str, graph_version: str, graph: Any, node_id: str, **kwargs: Any) -> dict[str, Any]:
        return self.make(doc_id, graph_version, graph, node_id, **kwargs)

    def make(
        self, doc_id: str, graph_version: str, graph: Any, node_id: str, *,
        dry_run: bool = False, allow_spend: bool = False,
        on_event: Callable[[dict[str, Any]], None] | None = None,
        preload_next: bool = False, _background: bool = False, owner: str | None = None,
        cache_only: bool = False,
    ) -> dict[str, Any]:
        started = perf_counter()
        emit = on_event or (lambda event: None)
        settings = self.settings
        context, base, _ = _assemble(graph, node_id, settings)
        node = graph.nodes[node_id]
        chunks = gather_chunks(graph, node, base["definition"].get("chunk_id"), settings)
        skeleton = self._skeleton(base, graph_version, source_rows(chunks))
        if not chunks:
            result = self._with_learner_status(
                {**skeleton, "status": "no_source",
                 "warnings": list(dict.fromkeys([*skeleton["warnings"], "khong_co_doan_day"]))}, owner, doc_id)
            emit({"event": "skeleton", "lecture": result})
            emit({"event": "final", "lecture": result})
            return result

        pages = formula_pages(chunks, settings.lecture_max_page_images)
        images = self._load_images(doc_id, graph, pages)
        system = system_prompt(bool(images))
        user = user_message(node, graph.modules.get(node.get("module_id"), {}), chunks,
                            prerequisite_rows(base, context), [row["name"] for row in base["next_up"]])
        material = context_hash({"user": user, "images": [[page, hashlib.sha256(data).hexdigest()] for page, data in images]})
        key = context_hash({
            "contract_version": settings.lecture_contract_version, "doc_id": doc_id, "node_id": node_id,
            "material": material, "prompt_version": settings.lecture_prompt_version,
            "system_prompt": hashlib.sha256(system.encode("utf-8")).hexdigest(),
            "context_version": settings.lecture_context_version, "model_id": settings.model_id,
            "temperature": settings.lecture_temperature, "max_output_tokens": settings.lecture_max_output_tokens})
        skeleton["lecture_key"] = key
        emit({"event": "skeleton", "lecture": self._with_learner_status(skeleton, owner, doc_id)})

        if cache_only:
            cached = self.store.get_cache(key)
            if isinstance(cached, dict) and cached.get("status") == "ready":
                return self._public(cached, graph_version, owner, doc_id)
            return {**skeleton, "status": "not_cached"}
        if dry_run:
            tokens = (len(system) + len(user)) // 3 + IMAGE_TOKEN_ESTIMATE * len(images)
            result = {**skeleton, "dry_run": True, "estimate_input_tokens": tokens, "images": [page for page, _ in images],
                      "estimate_usd": estimate_cost(settings.model_id, tokens, settings.lecture_max_output_tokens)}
            emit({"event": "final", "lecture": result})
            return result
        cached = self.store.get_cache(key)
        if isinstance(cached, dict) and cached.get("status") == "ready":
            result = self._public(cached, graph_version, owner, doc_id)
            emit({"event": "final", "lecture": result})
            return result
        failure = self.store.get_record("lecture_failure", key)
        if failure:
            if datetime.fromisoformat(str(failure.get("expires_at", ""))) > self.clock.now():
                result = self._public(failure["result"], graph_version, owner, doc_id)
                emit({"event": "failure", "lecture": result})
                return result
            self.store.delete_record("lecture_failure", key)

        retries = settings.lecture_preload_transport_retries if _background else settings.lecture_click_transport_retries
        stored = self.store.single_flight(
            key, lambda: self._generate(skeleton, system, user, images, len(pages), chunks, key, material, doc_id,
                                        allow_spend, started, retries, emit),
            cache_if=lambda value: isinstance(value, dict) and value.get("status") == "ready", negative_ttl_seconds=0)
        result = self._public(stored, graph_version, owner, doc_id)
        if result["status"] == "failed":
            self._remember_failure(key, doc_id, result)
        emit({"event": "final" if result["status"] == "ready" else "failure", "lecture": result})
        next_node_id = result["position"].get("next_node_id")
        if preload_next and next_node_id:
            Thread(target=self.make, args=(doc_id, graph_version, graph, next_node_id),
                   kwargs={"allow_spend": allow_spend, "_background": True}, daemon=True).start()
        return result

    # -- building blocks ---------------------------------------------------------------------------------------

    def _skeleton(self, base: dict[str, Any], graph_version: Any, sources: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "contract_version": self.settings.lecture_contract_version, "doc_id": base["doc_id"],
            "graph_version": graph_version, "node_id": base["node_id"], "status": "generating", "lecture_key": None,
            "position": base["position"], "definition": base["definition"],
            "prerequisites": [{"recall": row["recall"], "learner_status": "unknown"} for row in base["prerequisites"]],
            "body_md": "", "self_check": None, "sources": sources, "next_up": list(base["next_up"]),
            "media": base["media"], "failure": None, "warnings": list(base["warnings"]), "usage": {},
        }

    def _load_images(self, doc_id: str, graph: Any, pages: list[int]) -> list[tuple[int, bytes]]:
        parse_version = getattr(graph, "parse_version", None)
        if not pages or self.page_images is None or parse_version is None:
            return []
        found = ((page, self.page_images.get(doc_id, int(parse_version), page)) for page in pages)
        return [(page, data) for page, data in found if data]

    def _with_learner_status(self, lecture: dict[str, Any], owner: str | None, doc_id: str) -> dict[str, Any]:
        result = json.loads(stable_json(lecture))
        states = {}
        if self.progress is not None and owner:
            states = (self.progress.get_progress(owner, doc_id) or {}).get("nodes", {})

        def status(node_id: Any) -> str:
            return "unknown" if not owner else "learned" if states.get(node_id, {}).get("state") == "learned" else "not_learned"

        for item in result.get("prerequisites", []):
            item["learner_status"] = status(item["recall"].get("node_id"))
        for item in result.get("next_up", []):
            item["learner_status"] = status(item.get("node_id"))
        return result

    def _public(self, stored: dict[str, Any], graph_version: Any, owner: str | None, doc_id: str) -> dict[str, Any]:
        """What a learner may see: no admin `validation`, a fresh graph version and learner status."""
        result = {key: value for key, value in stored.items() if key != "validation"}
        return self._with_learner_status({**result, "graph_version": graph_version}, owner, doc_id)

    def _remember_failure(self, key: str, doc_id: str, result: dict[str, Any]) -> None:
        reason = result["failure"]["reason_code"]
        if reason == "khong_co_mo_hinh":
            return
        if reason == "tran_he_thong":
            zone = ZoneInfo(self.settings.spend_day_timezone)
            tomorrow = self.clock.today(self.settings.spend_day_timezone) + timedelta(days=1)
            expiry = datetime.combine(tomorrow, datetime.min.time(), tzinfo=zone).astimezone(self.clock.now().tzinfo)
        else:
            expiry = self.clock.now() + timedelta(seconds=self.settings.negative_cache_seconds)
        self.store.put_record("lecture_failure", key, {
            "doc_id": doc_id, "expires_at": expiry.isoformat(), "result": _without_learner_status(result)})

    def _failure(self, skeleton: dict[str, Any], reason: str, attempts: list[_Attempt]) -> dict[str, Any]:
        definition = skeleton["definition"]
        failure = {"reason_code": reason, "message": _MESSAGES[reason], "retryable": True,
                   "read_page": {"page": definition.get("page"), "chunk_id": definition.get("chunk_id")},
                   "ask_assistant": True}
        return {**skeleton, "status": "failed", "failure": failure, "usage": self._usage(attempts)}

    def _usage(self, attempts: list[_Attempt]) -> dict[str, Any]:
        total = _aggregate_usage([{**attempt.usage, "cost_usd": attempt.cost_usd} for attempt in attempts])
        first = next((attempt.ttft_ms for attempt in attempts if attempt.ttft_ms is not None), None)
        return {"model_id": getattr(self.model, "model_id", self.settings.model_id),
                "elapsed_ms": sum(attempt.elapsed_ms for attempt in attempts), "ttft_ms": first, **total}

    # -- generation --------------------------------------------------------------------------------------------

    def _generate(self, skeleton: dict[str, Any], system: str, user: str, images: list[tuple[int, bytes]],
                  pages_wanted: int, chunks: list[Any], key: str, material: str, doc_id: str, allow_spend: bool,
                  started: float, retries: int, emit: Callable[[dict[str, Any]], None]) -> dict[str, Any]:
        if self.model is None or not allow_spend:
            return self._failure(skeleton, "khong_co_mo_hinh", [])
        deadline = started + self.settings.lecture_click_timeout_seconds
        attempts: list[_Attempt] = []
        for index in range(2):
            if perf_counter() >= deadline:
                attempts.append(_Attempt(timed_out=True))
                break
            try:
                attempts.append(self._attempt(system, user, images, doc_id, material, index, deadline, retries, emit))
            except DailyLimitExceeded:
                return self._failure(skeleton, "tran_he_thong", attempts)
            last = attempts[-1]
            if last.usable or last.error is not None or last.timed_out:
                break
        last = attempts[-1]
        if not last.usable:
            reason = ("het_thoi_gian" if last.timed_out or isinstance(last.error, TimeoutError)
                      else "loi_mang" if last.error is not None else "khong_dung_duoc")
            return self._failure(skeleton, reason, attempts)
        cut = last.error is not None or last.timed_out or last.finish_reason in {"MAX_TOKENS", "LENGTH"}
        body, self_check = split_self_check(last.text)
        validation = build_validation(
            last.text, source_texts(chunks), finish_reason=last.finish_reason, images_sent=len(images),
            pages_wanted=pages_wanted, self_check_found=self_check is not None)
        self.store.append_usage({
            "purpose": "lecture_validation", "model_id": getattr(self.model, "model_id", self.settings.model_id),
            "doc_id": doc_id, "learner_id": None, "context_hash": material, "input_tokens": 0, "output_tokens": 0,
            "thought_tokens": 0, "cost_usd": 0.0, "ttft_ms": None, "elapsed_ms": 0, "generation_index": len(attempts) - 1,
            "validator_version": VALIDATION_VERSION, "validation_rules": [], "dropped_by_rule": {},
            "dropped_by_source_label": {}, "passed": True, "failure_reason": None, "validation": validation,
            "created_at": self.clock.now().isoformat()})
        return _without_learner_status({
            **skeleton, "status": "ready", "body_md": body, "self_check": self_check,
            "warnings": list(dict.fromkeys([*skeleton["warnings"], *(["cat_ngan"] if cut else [])])),
            "usage": self._usage(attempts), "validation": validation})

    def _attempt(self, system: str, user: str, images: list[tuple[int, bytes]], doc_id: str, material: str,
                 index: int, deadline: float, retries: int, emit: Callable[[dict[str, Any]], None]) -> _Attempt:
        model_id = getattr(self.model, "model_id", self.settings.model_id)
        replayed = bool(getattr(self.model, "is_replay", False))
        estimate = estimate_cost(self.settings.model_id,
                                 (len(system) + len(user)) // 3 + IMAGE_TOKEN_ESTIMATE * len(images),
                                 self.settings.lecture_max_output_tokens)
        attempt = _Attempt()
        with spending_call(self.spend_guard, "lecture", estimate, replayed=replayed, clock=self.clock) as admitted_at:
            began = perf_counter()
            session = stream = None
            try:
                session = self.model.start_session(system)
                stream = iter(session.stream_text(
                    user, images=images, temperature=self.settings.lecture_temperature, transport_retries=retries,
                    timeout_seconds=max(0.1, deadline - perf_counter())))
            except Exception as error:
                attempt.error = error
            try:
                while stream is not None:
                    try:
                        piece = next(stream)
                    except StopIteration:
                        break
                    except Exception as error:
                        attempt.error = error
                        break
                    if not attempt.text:
                        piece = piece.lstrip()
                    if piece:
                        if not attempt.text:
                            attempt.ttft_ms = round((perf_counter() - began) * 1000)
                        attempt.text += piece
                        emit({"event": "delta", "text": piece})
                    if perf_counter() >= deadline:
                        attempt.timed_out = True
                        break
            finally:
                close = getattr(stream, "close", None)
                if close:
                    close()
                attempt.usage = dict(getattr(session, "last_usage", None) or {})
                attempt.finish_reason = getattr(session, "last_finish_reason", None)
                attempt.elapsed_ms = round((perf_counter() - began) * 1000)
                attempt.cost_usd = 0.0 if replayed else token_cost(model_id, attempt.usage)
                ledger = usage_row(purpose="lecture", model_id=model_id, doc_id=doc_id, context_hash=material,
                                   usage=attempt.usage, elapsed_ms=attempt.elapsed_ms, ttft_ms=attempt.ttft_ms,
                                   cost_usd=attempt.cost_usd)
                ledger.update(generation_index=index, created_at=admitted_at, replayed=replayed)
                self.store.append_usage(ledger)
        return attempt
