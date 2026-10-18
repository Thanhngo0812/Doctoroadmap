import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

from doc2roadmap.application.phase_b.lectures import LectureUseCase
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore, JsonPhaseBStore

from test_phase_b_lecture_sa26 import _graph, _item, _payload


def _three_distinct_ideas(shared_text_prefix=None):
    texts = [
        "Phép hợp tạo ra một tập hợp mới từ các phần tử đã cho.",
        "Mỗi phần tử của tập hợp được xét theo một quy tắc xác định.",
        "Tập hợp gồm các phần tử có cùng một đặc điểm.",
    ]
    if shared_text_prefix:
        texts = [shared_text_prefix + " " + text for text in texts]
    quote = "Tập hợp là một nhóm đối tượng được xác định rõ ràng."
    return [_item(text, quote) for text in texts]


class _PayloadStream:
    model_id = "scripted"

    def __init__(self, payloads, *, block_first=False):
        self.payloads = list(payloads)
        self.calls = 0
        self.entered = threading.Event()
        self.release = threading.Event()
        self.block_first = block_first

    def stream_json(self, system, prompt, schema):
        index = self.calls
        self.calls += 1
        if self.block_first and index == 0:
            self.entered.set()
            assert self.release.wait(3)
        payload = self.payloads[index]
        self.last_usage = {"promptTokenCount": 20, "candidatesTokenCount": 10}
        self.last_finish_reason = "STOP"
        return iter([json.dumps(payload, ensure_ascii=False)])


def test_k6_ignores_repeated_verbatim_quotes_when_idea_text_is_distinct():
    ideas = _three_distinct_ideas()
    payload = _payload(ideas)
    model = _PayloadStream([payload, payload])
    store = InMemoryPhaseBStore()

    result = LectureUseCase(model, store).make("d1", "g1", _graph(), "a", allow_spend=True)

    assert result["status"] == "ready"
    assert model.calls == 1
    assert len(next(s for s in result["sections"] if s["kind"] == "giai_thich")["items"]) == 3
    diagnostics = [row for row in store.usage_rows("d1") if row.get("purpose") == "lecture_validation"]
    assert all("K6" not in row["validation_rules"] for row in diagnostics)


def test_k6_third_occurrence_after_gate_keeps_two_qualified_ideas():
    repeated = "Mỗi phần tử của tập hợp được xét theo một quy tắc xác định."
    payload = _payload(_three_distinct_ideas(repeated))
    model = _PayloadStream([payload, payload])
    store = InMemoryPhaseBStore()

    result = LectureUseCase(model, store).make("d1", "g1", _graph(), "a", allow_spend=True)

    assert result["status"] == "ready"
    assert "cat_ngan" in result["warnings"]
    assert len(next(s for s in result["sections"] if s["kind"] == "giai_thich")["items"]) == 2
    assert model.calls == 1
    diagnostics = [row for row in store.usage_rows("d1") if row.get("purpose") == "lecture_validation"]
    assert any(row["dropped_by_rule"].get("K6", 0) for row in diagnostics)


def test_failed_lecture_is_memoized_but_never_persisted_as_ready(tmp_path):
    path = tmp_path / "phase-b.json"
    store = JsonPhaseBStore(path)
    model = _PayloadStream([_payload([]) for _ in range(8)])
    settings = replace(BSettings(), negative_cache_seconds=30)
    use_case = LectureUseCase(model, store, settings=settings)

    first = use_case.make("d1", "g1", _graph(), "a", allow_spend=True)
    second = use_case.make("d1", "g1", _graph(), "a", allow_spend=True)
    stored = json.loads(path.read_text(encoding="utf-8"))
    assert first["status"] == second["status"] == "failed"
    assert model.calls == 2
    assert stored["cache"] == {}
    assert "lecture_failure" in stored["records"]
    assert use_case.make("d1", "g1", _graph(), "a", allow_spend=True)["status"] == "failed"
    assert model.calls == 2


def test_ready_lecture_persists_and_reloads_from_json_cache(tmp_path):
    path = tmp_path / "phase-b.json"
    store = JsonPhaseBStore(path)
    payload = _payload([
        _item("Tập hợp gồm các phần tử có cùng một đặc điểm.", "Tập hợp là một nhóm đối tượng được xác định rõ ràng."),
        _item("Mỗi phần tử của tập hợp được xét theo một quy tắc xác định.", "Tập hợp là một nhóm đối tượng được xác định rõ ràng."),
    ])
    model = _PayloadStream([payload])
    first = LectureUseCase(model, store).make("d1", "g1", _graph(), "a", allow_spend=True)

    reloaded = JsonPhaseBStore(path)
    second = LectureUseCase(_PayloadStream([]), reloaded).make("d1", "g1", _graph(), "a", allow_spend=True)

    assert first["status"] == second["status"] == "ready"
    assert reloaded.get_cache(first["lecture_key"])["status"] == "ready"


def test_stale_persisted_fallback_is_not_returned_or_kept(tmp_path):
    store = JsonPhaseBStore(tmp_path / "phase-b.json")
    store.put_cache("lecture-key", {"status": "fallback", "sections": []})
    generated = {"status": "ready", "sections": [{"kind": "giai_thich"}]}

    result = store.single_flight(
        "lecture-key", lambda: generated,
        cache_if=lambda value: isinstance(value, dict) and value.get("status") == "ready",
        negative_ttl_seconds=30,
    )

    assert result == generated
    assert store.get_cache("lecture-key") == generated


def test_concurrent_failed_requests_share_one_generation_sequence():
    store = InMemoryPhaseBStore()
    model = _PayloadStream([_payload([]) for _ in range(4)], block_first=True)
    use_case = LectureUseCase(model, store)
    second_started = threading.Event()

    def make(second=False):
        if second:
            second_started.set()
        return use_case.make("d1", "g1", _graph(), "a", allow_spend=True)

    with ThreadPoolExecutor(max_workers=2) as pool:
        first_future = pool.submit(make)
        assert model.entered.wait(2)
        second_future = pool.submit(make, True)
        assert second_started.wait(2)
        time.sleep(0.05)
        model.release.set()
        first, second = first_future.result(timeout=4), second_future.result(timeout=4)

    assert first["status"] == second["status"] == "failed"
    assert first["lecture_key"] == second["lecture_key"]
    assert model.calls == 2


def test_lecture_ttft_measures_delayed_first_chunk_when_adapter_has_no_ttft():
    payload = _payload([
        _item("Tập hợp gồm các phần tử có cùng một đặc điểm.", "Tập hợp là một nhóm đối tượng được xác định rõ ràng."),
        _item("Mỗi phần tử của tập hợp được xét theo một quy tắc xác định.", "Tập hợp là một nhóm đối tượng được xác định rõ ràng."),
    ])

    class DelayedSession:
        last_usage = {"promptTokenCount": 12, "candidatesTokenCount": 9}
        last_finish_reason = "STOP"

        def stream_json(self, prompt, *, response_schema):
            time.sleep(0.03)
            yield json.dumps(payload, ensure_ascii=False)

    class DelayedModel:
        model_id = "scripted"

        def start_session(self, system_prompt):
            return DelayedSession()

    store = InMemoryPhaseBStore()
    result = LectureUseCase(DelayedModel(), store).make("d1", "g1", _graph(), "a", allow_spend=True)

    assert result["status"] == "ready"
    row = next(row for row in store.usage_rows("d1") if row.get("purpose") == "lecture")
    assert row["ttft_ms"] is not None and row["ttft_ms"] > 0


def test_replay_does_not_replace_unknown_recorded_ttft_with_replay_speed():
    payload = _payload([
        _item("Tập hợp gồm các phần tử có cùng một đặc điểm.", "Tập hợp là một nhóm đối tượng được xác định rõ ràng."),
        _item("Mỗi phần tử của tập hợp được xét theo một quy tắc xác định.", "Tập hợp là một nhóm đối tượng được xác định rõ ràng."),
    ])

    class ReplaySession:
        last_usage = {"promptTokenCount": 12, "candidatesTokenCount": 9}
        last_finish_reason = "STOP"
        last_ttft_ms = 0

        def stream_json(self, prompt, *, response_schema):
            time.sleep(0.02)
            yield json.dumps(payload, ensure_ascii=False)

    class ReplayModel:
        model_id = "scripted"
        is_replay = True

        def start_session(self, system_prompt):
            return ReplaySession()

    store = InMemoryPhaseBStore()
    LectureUseCase(ReplayModel(), store).make("d1", "g1", _graph(), "a", allow_spend=True)

    row = next(row for row in store.usage_rows("d1") if row.get("purpose") == "lecture")
    assert row["ttft_ms"] is None


def test_max_tokens_finish_reason_after_gate_keeps_items_as_short_ready():
    payload = _payload([
        _item("Tập hợp gồm các phần tử có cùng một đặc điểm.", "Tập hợp là một nhóm đối tượng được xác định rõ ràng."),
        _item("Mỗi phần tử của tập hợp được xét theo một quy tắc xác định.", "Tập hợp là một nhóm đối tượng được xác định rõ ràng."),
    ])

    class TruncatedSession:
        last_usage = {"promptTokenCount": 12, "candidatesTokenCount": 9}
        last_finish_reason = "MAX_TOKENS"

        def stream_json(self, prompt, *, response_schema):
            yield json.dumps(payload, ensure_ascii=False)

    class TruncatedModel:
        model_id = "scripted"

        def start_session(self, system_prompt):
            return TruncatedSession()

    store = InMemoryPhaseBStore()
    result = LectureUseCase(TruncatedModel(), store).make("d1", "g1", _graph(), "a", allow_spend=True)

    assert result["status"] == "ready"
    assert "cat_ngan" in result["warnings"]
    assert len(next(s for s in result["sections"] if s["kind"] == "giai_thich")["items"]) == 2


def test_custom_quote_limit_reaches_learning_graph_context():
    graph = _graph(with_later=True)
    observed = []
    why_here = graph.why_here

    def recording_why_here(*args, **kwargs):
        observed.append(kwargs["settings"].quote_max_chars)
        return why_here(*args, **kwargs)

    graph.why_here = recording_why_here
    settings = replace(BSettings(), quote_max_chars=180)
    LectureUseCase(None, InMemoryPhaseBStore(), settings=settings).make(
        "d1", "g1", graph, "b", dry_run=True)

    assert observed == [180]
