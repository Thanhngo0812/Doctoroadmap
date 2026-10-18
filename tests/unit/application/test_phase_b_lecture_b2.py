import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from doc2roadmap.application.phase_b.lectures import LectureUseCase
from doc2roadmap.application.phase_b.progress import ProgressUseCase
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore

from test_phase_b_lecture_sa26 import _graph


DEFINITION = "Tập hợp là một nhóm đối tượng được xác định rõ ràng."
EXPLANATION = "Tập hợp gồm các phần tử có cùng một đặc điểm."
EXPLANATION_2 = "Mỗi phần tử của tập hợp được xét theo một quy tắc xác định."


def _idea(text, quote=EXPLANATION, sources=("S1",)):
    return {"text": text, "quote": quote, "sources": list(sources), "outside_document": False}


def _payload(*, explanation=None, bridges=(), suffix=""):
    return {
        "bridges": list(bridges),
        "explanation": list(explanation if explanation is not None else [
            _idea(EXPLANATION), _idea(EXPLANATION_2, EXPLANATION_2),
        ]),
        "example": [], "contrasts": [], "gaps": [], "self_check": None,
    }, suffix


class _Session:
    def __init__(self, model, payload, *, delay=0, error=None, chunks=None):
        self.model, self.payload, self.delay, self.error, self.chunks = model, payload, delay, error, chunks
        self.last_usage = {"promptTokenCount": 20, "candidatesTokenCount": 10}
        self.last_finish_reason = "STOP"
        self.last_ttft_ms = None
        self.temperatures = []

    def stream_json(self, prompt, *, response_schema, temperature=None, transport_retries=None, timeout_seconds=None):
        self.model.prompts.append(prompt)
        self.model.schemas.append(response_schema)
        self.temperatures.append(temperature)
        if self.delay:
            time.sleep(self.delay)
        if self.error:
            raise self.error
        if self.chunks is not None:
            yield from self.chunks
        else:
            yield json.dumps(self.payload, ensure_ascii=False)


class _Model:
    model_id = "scripted"

    def __init__(self, payloads, *, delay=0, errors=None, chunks=None):
        self.payloads = list(payloads)
        self.errors = list(errors or [])
        self.delay, self.chunks = delay, chunks
        self.calls, self.prompts, self.schemas, self.sessions = 0, [], [], []
        self.entered, self.release = threading.Event(), threading.Event()
        self.block = False

    def start_session(self, system_prompt):
        index = self.calls
        self.calls += 1
        if self.block and index == 0:
            self.entered.set()
            assert self.release.wait(3)
        payload = self.payloads[min(index, len(self.payloads) - 1)]
        error = self.errors[index] if index < len(self.errors) else None
        session = _Session(self, payload, delay=self.delay, error=error, chunks=self.chunks)
        self.sessions.append(session)
        return session


class _Clock:
    def __init__(self, now=None):
        self.current = now or datetime(2026, 10, 18, 2, tzinfo=timezone.utc)

    def now(self):
        return self.current

    def today(self, timezone_name):
        from zoneinfo import ZoneInfo
        return self.current.astimezone(ZoneInfo(timezone_name)).date()

    def advance(self, seconds):
        self.current += timedelta(seconds=seconds)


class _Guard:
    def __init__(self, allowed=True):
        self.allowed, self.calls = allowed, []

    def check(self, purpose, estimated_usd, owner=None):
        self.calls.append((purpose, estimated_usd, owner))
        return self.allowed


def test_offline_no_model_returns_failed_without_extractive_fallback():
    result = LectureUseCase(None, InMemoryPhaseBStore()).make("d1", "g1", _graph(), "a")

    assert result["status"] == "failed"
    assert result["failure"]["reason_code"] == "khong_co_mo_hinh"
    assert result["failure"]["retryable"] is False
    assert not any(section.get("kind") == "moc_trich_cau" for section in result["sections"])
    assert result["definition"]["citation"]["quote"] == DEFINITION
    assert result["definition"]["citation"]["char_start"] >= 0
    assert result["definition"]["citation"]["char_end"] > result["definition"]["citation"]["char_start"]


def test_validation_failure_returns_failure_event_and_does_not_persist_as_ready():
    broken = _payload(explanation=[])[0]
    store = InMemoryPhaseBStore()
    model = _Model([broken, broken])
    events = []

    result = LectureUseCase(model, store).make("d1", "g1", _graph(), "a", allow_spend=True,
                                               on_event=events.append)

    assert result["status"] == "failed"
    assert result["failure"]["reason_code"] == "kiem_noi_dung"
    assert events[-1]["event"] == "failure"
    assert store.get_cache(result["lecture_key"]) is None


def test_preload_option_keeps_foreground_retry_budget_and_uses_preload_budget_for_next_node():
    from test_phase_b_lecture_sa26 import _graph as graph_with_later

    payload = _payload()[0]
    entered = threading.Event()
    observed = []

    class Session:
        def stream_json(self, prompt, *, response_schema, temperature=None,
                        transport_retries=None, timeout_seconds=None):
            observed.append(transport_retries)
            if len(observed) == 2:
                entered.set()
            yield json.dumps(payload, ensure_ascii=False)

    class Model:
        model_id = "retry-options"

        def start_session(self, system_prompt):
            return Session()

    settings = replace(BSettings(), lecture_click_transport_retries=1,
                       lecture_preload_transport_retries=2)
    graph = graph_with_later(with_later=True)
    graph.modules["m1"]["node_ids"].append("b")
    result = LectureUseCase(Model(), InMemoryPhaseBStore(), settings=settings).make(
        "d1", "g1", graph, "a", allow_spend=True,
        preload_next=True)

    assert result["status"] == "ready"
    assert entered.wait(2)
    assert observed[:2] == [1, 2]


def test_recorded_stream_with_two_items_and_broken_json_stays_ready(tmp_path):
    from doc2roadmap.infrastructure.llm.phase_b import RecordingToolModel

    payload, _ = _payload()
    truncated = json.dumps(payload, ensure_ascii=False)[:-1]

    class Session:
        last_usage = {"promptTokenCount": 20, "candidatesTokenCount": 10}
        last_ttft_ms = 5
        last_finish_reason = "STOP"

        def stream_json(self, prompt, *, response_schema, temperature=None,
                        transport_retries=None, timeout_seconds=None):
            yield truncated

    class Delegate:
        model_id = "recorded-fake"

        def start_session(self, system_prompt, tools=()):
            return Session()

    store = InMemoryPhaseBStore()
    recorded = RecordingToolModel(Delegate(), tmp_path / "lecture.json", prompt_hash="lecture-test")
    result = LectureUseCase(recorded, store).make("d1", "g1", _graph(), "a", allow_spend=True)

    assert result["status"] == "ready"
    assert "cat_ngan" in result["warnings"]
    assert len(next(section for section in result["sections"] if section["kind"] == "giai_thich")["items"]) == 2
    assert len([row for row in store.usage_rows("d1") if row.get("purpose") == "lecture"]) == 1


def test_timed_out_worker_cannot_start_a_late_repair():
    released = threading.Event()
    ended = threading.Event()

    class Session:
        def stream_json(self, prompt, *, response_schema, temperature=None,
                        transport_retries=None, timeout_seconds=None):
            try:
                yield '{"explanation":['
                assert released.wait(2)
            finally:
                ended.set()

    class Model:
        model_id = "blocking"

        def __init__(self):
            self.calls = 0

        def start_session(self, system_prompt):
            self.calls += 1
            return Session()

    model = Model()
    settings = replace(BSettings(), lecture_click_timeout_seconds=0.05,
                       lecture_click_transport_retries=0)
    result = LectureUseCase(model, InMemoryPhaseBStore(), settings=settings).make(
        "d1", "g1", _graph(), "a", allow_spend=True)
    assert result["status"] == "failed"
    assert result["failure"]["reason_code"] == "het_thoi_gian"
    released.set()
    assert ended.wait(2)
    time.sleep(0.05)
    assert model.calls == 1


def test_shared_eightgram_only_truncates_at_three_occurrences_in_idea_text():
    phrase = "hệ thống có thể điều chỉnh theo những điều kiện ban đầu"
    ideas = [
        "Phương pháp thứ nhất mô tả nhiều yếu tố riêng biệt trong bài học " + phrase +
        " rồi phân tích các quan hệ giữa những thành phần cụ thể.",
        "Cách tiếp cận thứ hai xem xét những dữ kiện khác nhau " + phrase +
        " trước khi đưa ra một kết luận phù hợp.",
        "Ví dụ thứ ba phân tích một trường hợp mới " + phrase +
        " và giải thích vì sao kết quả thay đổi.",
    ]

    def run(count):
        graph = _graph()
        chunk = graph.chunks["c1"]
        chunk.text = DEFINITION + " " + " ".join(ideas[:count])
        chunk.char_end = chunk.char_start + len(chunk.text)
        payload = {"bridges": [],
                   "explanation": [_idea(text, text) for text in ideas[:count]],
                   "example": [], "contrasts": [], "gaps": [], "self_check": None}
        return LectureUseCase(_Model([payload]), InMemoryPhaseBStore()).make(
            "d1", "g1", graph, "a", allow_spend=True)

    two = run(2)
    three = run(3)
    two_items = next(section for section in two["sections"] if section["kind"] == "giai_thich")["items"]
    three_items = next(section for section in three["sections"] if section["kind"] == "giai_thich")["items"]
    assert two["status"] == "ready"
    assert len(two_items) == 2
    assert "cat_ngan" not in two["warnings"]
    assert three["status"] == "ready"
    assert len(three_items) == 2
    assert "cat_ngan" in three["warnings"]
    assert all(item["status"] != "fallback" for item in [two, three])


def test_failed_validation_is_remembered_for_failure_ttl_and_expires():
    broken = _payload(explanation=[])[0]
    store, model, clock = InMemoryPhaseBStore(), _Model([broken] * 4), _Clock()
    use_case = LectureUseCase(model, store, settings=BSettings(), clock=clock)

    first = use_case.make("d1", "g1", _graph(), "a", allow_spend=True)
    second = use_case.make("d1", "g1", _graph(), "a", allow_spend=True)
    assert first["status"] == second["status"] == "failed"
    assert model.calls == 2
    clock.advance(BSettings().lecture_failure_ttl_seconds + 1)
    use_case.make("d1", "g1", _graph(), "a", allow_spend=True)
    assert model.calls == 4


def test_network_failure_is_retryable_and_remembered_only_for_short_ttl():
    store, model, clock = InMemoryPhaseBStore(), _Model([{}] * 4,
                                                        errors=[OSError("offline")] * 4), _Clock()
    use_case = LectureUseCase(model, store, clock=clock)

    first = use_case.make("d1", "g1", _graph(), "a", allow_spend=True)
    second = use_case.make("d1", "g1", _graph(), "a", allow_spend=True)
    assert first["failure"]["reason_code"] == "loi_mang"
    assert first["failure"]["retryable"] is True
    assert model.calls == 1
    clock.advance(BSettings().negative_cache_seconds + 1)
    use_case.make("d1", "g1", _graph(), "a", allow_spend=True)
    assert model.calls == 2


def test_daily_system_limit_blocks_before_model_call_and_records_failure():
    store, model, guard = InMemoryPhaseBStore(), _Model([_payload()[0]]), _Guard(False)
    result = LectureUseCase(model, store, spend_guard=guard).make(
        "d1", "g1", _graph(), "a", allow_spend=True)

    assert result["status"] == "failed"
    assert result["failure"]["reason_code"] == "tran_he_thong"
    assert result["failure"]["retryable"] is True
    assert model.calls == 0
    assert guard.calls[0][0] == "lecture"


def test_click_timeout_returns_failure_without_waiting_for_slow_stream():
    model = _Model([_payload()[0]], delay=0.2)
    settings = replace(BSettings(), lecture_click_timeout_seconds=0.03)
    started = time.perf_counter()
    result = LectureUseCase(model, InMemoryPhaseBStore(), settings=settings).make(
        "d1", "g1", _graph(), "a", allow_spend=True)

    assert time.perf_counter() - started < 0.15
    assert result["status"] == "failed"
    assert result["failure"]["reason_code"] == "het_thoi_gian"


def test_retry_generation_uses_configured_temperature_after_validation_failure():
    model = _Model([_payload(explanation=[])[0], _payload()[0]])
    settings = replace(BSettings(), lecture_retry_temperature=1.0)
    result = LectureUseCase(model, InMemoryPhaseBStore(), settings=settings).make(
        "d1", "g1", _graph(), "a", allow_spend=True)

    assert result["status"] == "ready"
    assert model.calls == 2
    assert [session.temperatures[0] for session in model.sessions] == [settings.lecture_temperature,
                                                                      settings.lecture_retry_temperature]


def test_stream_hides_items_until_two_valid_explanations_open_gate():
    payload = _payload()[0]
    events = []
    result = LectureUseCase(_Model([payload]), InMemoryPhaseBStore()).make(
        "d1", "g1", _graph(), "a", allow_spend=True, on_event=events.append)

    item_events = [event for event in events if event["event"] == "item"]
    assert result["status"] == "ready"
    assert len(item_events) >= 2
    assert events.index(item_events[0]) > events.index(next(e for e in events if e["event"] == "skeleton"))
    assert all(event.get("gate_open") is True for event in item_events)


def test_stream_failure_before_gate_emits_no_items_and_returns_failed():
    one_item = json.dumps({"explanation": [_idea(EXPLANATION)]}, ensure_ascii=False)
    model = _Model([{}], errors=[None], chunks=[one_item])
    events = []
    result = LectureUseCase(model, InMemoryPhaseBStore()).make(
        "d1", "g1", _graph(), "a", allow_spend=True, on_event=events.append)

    assert result["status"] == "failed"
    assert not any(event["event"] == "item" for event in events)


def test_truncated_json_after_gate_keeps_emitted_items_and_returns_ready():
    payload = _payload()[0]
    encoded = json.dumps(payload, ensure_ascii=False)
    chunks = [encoded[:encoded.rfind("]") + 1], " , {\"text\": \"truncated"]
    model = _Model([{}], chunks=chunks)
    events = []
    result = LectureUseCase(model, InMemoryPhaseBStore()).make(
        "d1", "g1", _graph(), "a", allow_spend=True, on_event=events.append)

    item_events = [event for event in events if event["event"] == "item"]
    assert result["status"] == "ready"
    assert "cat_ngan" in result["warnings"]
    assert len(item_events) == 2
    assert len(next(section for section in result["sections"] if section["kind"] == "giai_thich")["items"]) == 2


def test_lecture_reports_timing_order_for_skeleton_gate_and_final():
    events = []
    store = InMemoryPhaseBStore()
    result = LectureUseCase(_Model([_payload()[0]], delay=0.01), store).make(
        "d1", "g1", _graph(), "a", allow_spend=True, on_event=events.append)
    row = next(row for row in store.usage_rows("d1") if row.get("purpose") == "lecture_timing")

    assert row["skeleton_ms"] <= row["gate_ms"] <= row["final_ms"]
    assert row["gate_to_final_ms"] == row["final_ms"] - row["gate_ms"]


def test_bridge_is_validated_and_attached_to_recall_without_retry():
    graph = _graph(with_later=True)
    bridge = {"prereq": "a", "text": "Tập hợp là nền để hiểu phép hợp.",
              "sources": ["Q1"], "quote": "Mỗi phần tử của tập hợp được xét theo một quy tắc xác định."}
    payload = _payload(bridges=[bridge])[0]
    model, events = _Model([payload]), []
    result = LectureUseCase(model, InMemoryPhaseBStore()).make(
        "d1", "g1", graph, "b", allow_spend=True, on_event=events.append)

    assert result["status"] == "ready"
    assert result["prerequisites"][0]["bridge"]["text"] == bridge["text"]
    assert model.calls == 1
    assert any(event.get("section_kind") == "cau_noi" for event in events)


def test_bridge_with_wrong_prerequisite_label_is_dropped_as_k11_without_retry():
    graph = _graph(with_later=True)
    bridge = {"prereq": "a", "text": "Tập hợp là nền để hiểu phép hợp.",
              "sources": ["Q9"], "quote": "Mỗi phần tử của tập hợp được xét theo một quy tắc xác định."}
    model, store = _Model([_payload(bridges=[bridge])[0]]), InMemoryPhaseBStore()
    result = LectureUseCase(model, store).make("d1", "g1", graph, "b", allow_spend=True)

    assert result["status"] == "ready"
    assert result["prerequisites"][0]["bridge"] is None
    assert model.calls == 1
    validation = next(row for row in store.usage_rows("d1") if row["purpose"] == "lecture_validation")
    assert validation["dropped_by_rule"]["K11"] == 1


def test_bridge_with_forbidden_learner_phrase_is_dropped_as_k12():
    graph = _graph(with_later=True)
    bridge = {"prereq": "a", "text": "Như bạn đã học, tập hợp là nền để hiểu phép hợp.",
              "sources": ["Q1"], "quote": "Mỗi phần tử của tập hợp được xét theo một quy tắc xác định."}
    store = InMemoryPhaseBStore()
    result = LectureUseCase(_Model([_payload(bridges=[bridge])[0]]), store).make(
        "d1", "g1", graph, "b", allow_spend=True)

    assert result["prerequisites"][0]["bridge"] is None
    validation = next(row for row in store.usage_rows("d1") if row["purpose"] == "lecture_validation")
    assert validation["dropped_by_rule"]["K12"] == 1


def test_missing_bridge_is_k10_and_does_not_trigger_generation_retry():
    graph = _graph(with_later=True)
    store, model = InMemoryPhaseBStore(), _Model([_payload()[0]])
    result = LectureUseCase(model, store).make("d1", "g1", graph, "b", allow_spend=True)

    assert result["prerequisites"][0]["bridge"] is None
    assert model.calls == 1
    validation = next(row for row in store.usage_rows("d1") if row["purpose"] == "lecture_validation")
    assert validation["dropped_by_rule"]["K10"] == 1


def test_legacy_excerpt_prerequisite_is_recalled_but_not_sent_for_bridge():
    graph = _graph(with_later=True)
    why_here = graph.why_here
    graph.why_here = lambda *args, **kwargs: {
        "prerequisites": [{"node_id": "a", "name": "Tập hợp", "source_label": "S1",
                           "quote": EXPLANATION, "citation_source": "legacy_excerpt",
                           "module_id": "m1"}],
    }
    model = _Model([_payload()[0]])
    result = LectureUseCase(model, InMemoryPhaseBStore()).make(
        "d1", "g1", graph, "b", allow_spend=True)

    assert result["prerequisites"][0]["recall"]["name"] == "Tập hợp"
    assert result["prerequisites"][0]["bridge"] is None
    assert "bridge_candidates" not in model.prompts[0] or "legacy_excerpt" not in model.prompts[0]


def test_next_up_uses_outgoing_requires_and_omits_quote_when_edge_has_none():
    graph = _graph(with_later=True)
    store = InMemoryPhaseBStore()
    result = LectureUseCase(_Model([_payload()[0]]), store).make(
        "d1", "g1", graph, "a", allow_spend=True)

    assert result["next_up"][0]["node_id"] == "b"
    assert result["next_up"][0]["quote"] == EXPLANATION_2
    assert result["contract_version"] == "lecture-2"


def test_learner_status_is_per_request_not_cached_or_sent_to_model():
    graph, store = _graph(with_later=True), InMemoryPhaseBStore()
    progress = ProgressUseCase(store, graph)
    progress.set_progress("alice", "d1", "a", True)
    model, events = _Model([_payload()[0]]), []
    use_case = LectureUseCase(model, store, progress=progress)

    alice = use_case.make("d1", "g1", graph, "b", owner="alice", allow_spend=True, on_event=events.append)
    bob = use_case.get("d1", "g1", graph, "b", owner="bob", allow_spend=True)
    cached = store.get_cache(alice["lecture_key"])

    assert alice["lecture_key"] == bob["lecture_key"]
    assert alice["prerequisites"][0]["learner_status"] == "learned"
    assert bob["prerequisites"][0]["learner_status"] == "not_learned"
    assert cached is not None and "learner_status" not in json.dumps(cached)
    assert "learner_status" not in model.prompts[0]
    assert model.calls == 1
    assert events[0]["lecture"]["prerequisites"][0]["learner_status"] == "learned"


def test_unowned_lecture_marks_prerequisite_and_next_up_unknown():
    graph = _graph(with_later=True)
    result = LectureUseCase(_Model([_payload()[0]]), InMemoryPhaseBStore()).make(
        "d1", "g1", graph, "a", allow_spend=True)

    assert result["next_up"][0]["learner_status"] == "unknown"


def test_bridge_limit_is_in_prompt_and_lecture_key():
    graph, store = _graph(with_later=True), InMemoryPhaseBStore()
    settings = replace(BSettings(), bridge_max_chars=47)
    model = _Model([_payload()[0]])
    result = LectureUseCase(model, store, settings=settings).make(
        "d1", "g1", graph, "b", dry_run=True)

    assert result["dry_run_limits"]["bridge_max_chars"] == 47
    default = LectureUseCase(None, InMemoryPhaseBStore()).make(
        "d1", "g1", graph, "b", dry_run=True)
    assert result["lecture_key"] != default["lecture_key"]
