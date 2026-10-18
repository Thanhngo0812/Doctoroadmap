from doc2roadmap.application.phase_b.lectures import LectureUseCase, _lecture_output_text, _merge_emitted
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore
from test_phase_b_lecture_b2 import EXPLANATION, EXPLANATION_2, _Model, _payload
from test_phase_b_lecture_sa26 import _graph


def test_k6_scans_idea_text_without_serialized_citation_metadata():
    output = {
        "explanation": [{
            "text": "Một phát biểu riêng biệt về khái niệm.",
            "citations": [{"quote": "cụm trích dẫn lặp lại"}],
        }],
        "example": [],
    }

    assert _lecture_output_text(output) == "Một phát biểu riêng biệt về khái niệm."


def test_same_prerequisite_has_only_one_bridge_in_lecture_sections():
    first = {"prereq": "a", "text": "Tập hợp là nền để hiểu phép hợp.",
             "citations": [{"label": "Q1", "quote": "nguồn"}]}
    second = {"prereq": "a", "text": "Phép hợp dùng các phần tử của tập hợp.",
              "citations": [{"label": "Q1", "quote": "nguồn"}]}

    sections = _merge_emitted([], {"bridges": [first, second]})

    bridges = next(section["items"] for section in sections
                   if section["kind"] == "cau_noi")
    assert len(bridges) == 1


def _bridge(prereq, text, *, source="Q1", quote=EXPLANATION_2):
    return {"prereq": prereq, "text": text, "sources": [source], "quote": quote}


def _two_prerequisite_graph():
    graph = _graph(with_later=True)
    extra = {"node_id": "c", "name": "Quy tắc", "display_name": "Quy tắc",
             "learnable": True, "module_id": "m1", "teaching_chunk_ids": ["c1"],
             "defining_chunk_ids": [],
             "anchor": {"chunk_id": "c1", "sentence": EXPLANATION_2}}
    graph.payload["nodes"].append(extra)
    graph.nodes["c"] = dict(extra)
    graph.learnable_nodes["c"] = dict(extra)
    graph.modules["m1"]["node_ids"].append("c")
    graph._node_module["c"] = "m1"
    graph.payload["requires_edges"].append({
        "source": "c", "target": "b", "edge_type": "requires",
        "quote": EXPLANATION_2, "chunk_ids": ["c1"],
    })
    return graph


def _bridge_items(result):
    return next(section["items"] for section in result["sections"]
                if section["kind"] == "cau_noi")


def test_stream_uses_first_valid_bridge_then_suppresses_duplicate_and_cache_preserves_it():
    graph = _graph(with_later=True)
    invalid = _bridge("a", "Tập hợp là nền của phép hợp.", source="Q9")
    first_valid = _bridge("a", "Tập hợp giúp hiểu các phần tử của phép hợp.")
    later_valid = _bridge('a', 'Tập hợp cung cấp các đối tượng để tạo phép hợp.')
    payload = _payload(
        bridges=[invalid, first_valid, later_valid],
        explanation=[
            {"text": EXPLANATION, "quote": EXPLANATION, "sources": ["S1"]},
            {"text": EXPLANATION_2, "quote": EXPLANATION_2, "sources": ["S1"]},
        ],
    )[0]
    model, store, events = _Model([payload]), InMemoryPhaseBStore(), []
    use_case = LectureUseCase(model, store)

    result = use_case.make("d1", "g1", graph, "b", allow_spend=True,
                           on_event=events.append)

    bridges = _bridge_items(result)
    bridge_events = [event["item"] for event in events
                     if event.get("event") == "item" and event.get("section_kind") == "cau_noi"]
    assert result["status"] == "ready"
    assert "cat_ngan" not in result["warnings"]
    assert len(next(section["items"] for section in result["sections"]
                    if section["kind"] == "giai_thich")) == 2
    assert [item["text"] for item in bridges] == [first_valid["text"]]
    assert [item["text"] for item in bridge_events] == [first_valid["text"]]
    assert result["prerequisites"][0]["bridge"] == bridges[0]
    gate_index = next(index for index, event in enumerate(events) if event["event"] == "gate")
    assert all(index > gate_index for index, event in enumerate(events)
               if event["event"] == "item")

    cached = use_case.make("d1", "g1", graph, "b", allow_spend=True)
    assert model.calls == 1
    assert _bridge_items(cached) == bridges
    assert cached["prerequisites"][0]["bridge"] == bridges[0]


def test_repair_keeps_first_bridge_emits_once_and_retains_other_prerequisite():
    graph = _two_prerequisite_graph()
    bridge_a = _bridge("a", "Tập hợp giúp hiểu phép hợp.")
    duplicate_a = _bridge("a", "Tập hợp tạo nền cho phép hợp.")
    bridge_c = _bridge("c", "Quy tắc giúp hiểu phép hợp.")
    first_attempt = _payload(
        bridges=[bridge_a],
        explanation=[{"text": EXPLANATION, "quote": EXPLANATION, "sources": ["S1"]}],
    )[0]
    repaired_attempt = _payload(
        bridges=[duplicate_a, bridge_c],
        explanation=[
            {"text": EXPLANATION, "quote": EXPLANATION, "sources": ["S1"]},
            {"text": EXPLANATION_2, "quote": EXPLANATION_2, "sources": ["S1"]},
        ],
    )[0]
    model, store, events = _Model([first_attempt, repaired_attempt]), InMemoryPhaseBStore(), []
    use_case = LectureUseCase(model, store)

    result = use_case.make("d1", "g1", graph, "b", allow_spend=True,
                           on_event=events.append)

    bridges = _bridge_items(result)
    bridge_events = [event["item"] for event in events
                     if event.get("event") == "item" and event.get("section_kind") == "cau_noi"]
    assert result["status"] == "ready"
    assert model.calls == 2
    assert {item["prereq"] for item in bridges} == {"a", "c"}
    assert len(bridges) == 2
    assert next(item for item in bridges if item["prereq"] == "a")["text"] == bridge_a["text"]
    assert len(bridge_events) == 2
    assert {item["prereq"] for item in bridge_events} == {"a", "c"}
    assert sum(item["prereq"] == "a" for item in bridge_events) == 1
    gate_index = next(index for index, event in enumerate(events) if event["event"] == "gate")
    assert all(index > gate_index for index, event in enumerate(events)
               if event["event"] == "item")
    by_prereq = {item["prereq"]: item for item in bridges}
    result_bridges = {item.get("node_id") or item["recall"]["node_id"]: item["bridge"]
                      for item in result["prerequisites"]}
    assert result_bridges == by_prereq

    cached = use_case.make("d1", "g1", graph, "b", allow_spend=True)
    assert model.calls == 2
    assert _bridge_items(cached) == bridges
    cached_bridges = {item.get("node_id") or item["recall"]["node_id"]: item["bridge"]
                      for item in cached["prerequisites"]}
    assert cached_bridges == by_prereq


def test_k6_tail_cut_keeps_bridge_raw_indices_and_cache_consistent():
    graph = _two_prerequisite_graph()
    bridge_a = _bridge("a", "Tập hợp giúp hiểu phép hợp.")
    duplicate_a = _bridge("a", "Tập hợp tạo nền cho phép hợp.")
    bridge_c = _bridge("c", "Quy tắc giúp hiểu phép hợp.")
    payload = _payload(
        bridges=[bridge_a, duplicate_a, bridge_c],
        explanation=[
            {"text": EXPLANATION, "quote": EXPLANATION, "sources": ["S1"]},
            {"text": EXPLANATION_2, "quote": EXPLANATION_2, "sources": ["S1"]},
            {"text": EXPLANATION_2, "quote": EXPLANATION_2, "sources": ["S1"]},
        ],
    )[0]
    model, store, events = _Model([payload]), InMemoryPhaseBStore(), []
    use_case = LectureUseCase(model, store)

    result = use_case.make("d1", "g1", graph, "b", allow_spend=True,
                           on_event=events.append)

    expected = [bridge_a["text"], bridge_c["text"]]
    bridge_events = [event["item"]["text"] for event in events
                     if event.get("event") == "item" and event.get("section_kind") == "cau_noi"]
    assert result["status"] == "ready"
    assert "cat_ngan" in result["warnings"]
    assert [item["text"] for item in _bridge_items(result)] == expected
    assert bridge_events == expected

    cached = use_case.make("d1", "g1", graph, "b", allow_spend=True)
    assert model.calls == 1
    assert [item["text"] for item in _bridge_items(cached)] == expected
    assert cached["prerequisites"] == result["prerequisites"]
