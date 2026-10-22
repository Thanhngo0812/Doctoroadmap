"""SA-53: the final lecture filters duplicate prerequisite bridges without shifting raw stream indices."""
from doc2roadmap.application.phase_b.lectures import LectureUseCase
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore
from test_phase_b_lecture_b2 import EXPLANATION, EXPLANATION_2, _Model, _payload
from test_phase_b_sa45_lecture_audit import _bridge, _bridge_items, _two_prerequisite_graph

A_TEXT = "Tập hợp giúp hiểu phép hợp của hai tập hợp trong bài này."
C_NEAR_COPY = "Quy tắc giúp hiểu phép hợp của hai tập hợp trong bài này."
EXPLANATIONS = [{"text": EXPLANATION, "quote": EXPLANATION, "sources": ["S1"]},
                {"text": EXPLANATION_2, "quote": EXPLANATION_2, "sources": ["S1"]}]


def _run(bridges):
    graph = _two_prerequisite_graph()
    model, store, events = _Model([_payload(bridges=bridges, explanation=EXPLANATIONS)[0]]), InMemoryPhaseBStore(), []
    use_case = LectureUseCase(model, store)
    result = use_case.make("d1", "g1", graph, "b", allow_spend=True, on_event=events.append)
    streamed = [event["item"]["text"] for event in events
                if event.get("event") == "item" and event.get("section_kind") == "cau_noi"]
    cached = use_case.make("d1", "g1", graph, "b", allow_spend=True)
    return result, streamed, cached, model


def _prerequisite_bridges(result):
    return [row["bridge"]["text"] for row in result["prerequisites"] if row.get("bridge")]


def test_bridge_dropped_by_k6_in_stream_stays_out_of_final_after_an_earlier_duplicate():
    result, streamed, cached, model = _run([
        _bridge("a", A_TEXT), _bridge("a", "Tập hợp tạo nền cho phép hợp."), _bridge("c", C_NEAR_COPY)])

    assert streamed == [A_TEXT]
    assert [item["text"] for item in _bridge_items(result)] == streamed
    assert _prerequisite_bridges(result) == streamed
    assert model.calls == 1
    assert [item["text"] for item in _bridge_items(cached)] == streamed
    assert _prerequisite_bridges(cached) == streamed


def test_same_k6_drop_without_an_earlier_duplicate_matches_the_stream():
    result, streamed, cached, _ = _run([_bridge("a", A_TEXT), _bridge("c", C_NEAR_COPY)])

    assert streamed == [A_TEXT]
    assert [item["text"] for item in _bridge_items(result)] == streamed
    assert [item["text"] for item in _bridge_items(cached)] == streamed


def test_duplicate_prerequisite_bridges_do_not_trigger_repeated_text_k6():
    repeated = "Tập hợp là nền tảng để hiểu phép hợp của hai tập hợp đã cho trong bài."
    result, streamed, cached, model = _run([_bridge("a", repeated), _bridge("a", repeated), _bridge("a", repeated)])

    assert streamed == [repeated]
    assert result["status"] == "ready"
    assert "cat_ngan" not in result["warnings"]
    assert model.calls == 1
    assert [item["text"] for item in _bridge_items(cached)] == [repeated]


def test_lecture_cached_by_validator_6_is_not_served_by_the_shipped_validator():
    graph = _two_prerequisite_graph()
    model, store = _Model([_payload(bridges=[_bridge("a", A_TEXT)], explanation=EXPLANATIONS)[0]]), InMemoryPhaseBStore()
    old_key = LectureUseCase(model, store, settings=BSettings(lecture_validator_version="lecture-validator-6")).make(
        "d1", "g1", graph, "b", dry_run=True)["lecture_key"]
    store.put_cache(old_key, {"status": "ready", "sections": [], "warnings": [], "legacy": True})

    result = LectureUseCase(model, store).make("d1", "g1", graph, "b", allow_spend=True)

    assert model.calls == 1
    assert "legacy" not in result
    assert result["lecture_key"] != old_key
