import json
from types import SimpleNamespace

from doc2roadmap.application.phase_b.lectures import LectureUseCase, _assemble, summarize_lecture_diagnostics
from doc2roadmap.domain.learning_graph import LearningGraph
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore


def _graph(with_later=False):
    quotes = [
        "Tập hợp là một nhóm đối tượng được xác định rõ ràng.",
        "Tập hợp gồm các phần tử có cùng một đặc điểm.",
        "Mỗi phần tử của tập hợp được xét theo một quy tắc xác định.",
        "Phép hợp tạo ra một tập hợp mới từ các phần tử đã cho.",
    ]
    text = " ".join(quotes)
    chunk = SimpleNamespace(
        chunk_id="c1", doc_id="d1", order_index=0, split_index=0, page=1,
        char_start=0, char_end=len(text), parent_section_id="s1", section_path=["Toán"],
        heading_level=1, block_types=["paragraph"], text=text, context_prefix=None,
        image_refs=[], token_count=50, tokenizer_id="test", table_refs=[], formula_refs=[],
        role="noi_dung",
    )
    nodes = [{"node_id": "a", "name": "Tập hợp", "display_name": "Tập hợp",
              "learnable": True, "module_id": "m1", "teaching_chunk_ids": ["c1"],
              "defining_chunk_ids": [], "anchor": {"chunk_id": "c1", "sentence": quotes[0]}}]
    modules = [{"module_id": "m1", "index": 1, "title": "Cơ sở", "node_ids": ["a"]}]
    edges = []
    if with_later:
        nodes.append({"node_id": "b", "name": "Phép hợp", "display_name": "Phép hợp",
                      "learnable": True, "module_id": "m2", "teaching_chunk_ids": ["c1"],
                      "defining_chunk_ids": [], "anchor": {"chunk_id": "c1", "sentence": quotes[3]}})
        modules.append({"module_id": "m2", "index": 2, "title": "Phép toán", "node_ids": ["b"]})
        edges.append({"source": "a", "target": "b", "edge_type": "requires",
                      "quote": quotes[2], "chunk_ids": ["c1"]})
    return LearningGraph({"doc_id": "d1", "graph_version": "g1", "nodes": nodes,
                          "modules": modules, "requires_edges": edges, "open_edges": []}, [chunk])


class _StreamModel:
    model_id = "scripted"

    def __init__(self, payloads, usages=None):
        self.payloads = list(payloads)
        self.usages = list(usages or [{"promptTokenCount": 10, "candidatesTokenCount": 20}] * len(payloads))
        self.calls = 0

    def stream_json(self, system, prompt, schema):
        index = self.calls
        self.calls += 1
        payload = self.payloads[index]
        self.last_usage = self.usages[index]
        return iter([json.dumps(payload, ensure_ascii=False)])


def _item(text, quote):
    return {"text": text, "sources": ["S1"], "quote": quote}


def _payload(explanations):
    return {"prereq_notes": [], "explanation": explanations, "example": [],
            "contrasts": [], "gaps": []}


def test_stream_drops_jaccard_duplicate_and_definition_paraphrase_without_emitting_them():
    first = "Tập hợp gồm các phần tử có cùng một đặc điểm."
    paraphrase = "Tập hợp gồm các phần tử có cùng một đặc điểm chung."
    third = "Phép hợp tạo ra một tập hợp mới từ các phần tử đã cho."
    definition_copy = "Tập hợp là một nhóm đối tượng được xác định rõ ràng."
    model = _StreamModel([_payload([_item(first, "Tập hợp là một nhóm đối tượng được xác định rõ ràng."),
                                   _item(paraphrase, "Tập hợp là một nhóm đối tượng được xác định rõ ràng."),
                                   _item(third, "Phép hợp tạo ra một tập hợp mới từ các phần tử đã cho."),
                                   _item(definition_copy, "Tập hợp là một nhóm đối tượng được xác định rõ ràng.")])])
    events = []
    store = InMemoryPhaseBStore()

    result = LectureUseCase(model, store).make("d1", "g1", _graph(), "a", allow_spend=True,
                                                on_event=events.append)

    explanation = next(section for section in result["sections"] if section["kind"] == "giai_thich")
    assert [item["text"] for item in explanation["items"]] == [first, third]
    emitted = [event["item"]["text"] for event in events if event["event"] == "item"]
    assert paraphrase not in emitted
    assert result["status"] == "ready"
    diagnostics = [row for row in store.usage_rows("d1") if row.get("purpose") == "lecture_validation"]
    assert diagnostics[0]["dropped_by_rule"]["K6"] == 2


def test_repaired_lecture_reports_usage_from_both_generation_attempts():
    valid = _payload([
        _item("Tập hợp gồm các phần tử có cùng một đặc điểm.", "Tập hợp gồm các phần tử có cùng một đặc điểm."),
        _item("Mỗi phần tử của tập hợp được xét theo một quy tắc xác định.", "Mỗi phần tử của tập hợp được xét theo một quy tắc xác định."),
    ])
    model = _StreamModel([_payload([]), valid], [
        {"promptTokenCount": 11, "candidatesTokenCount": 13, "thoughtsTokenCount": 2},
        {"promptTokenCount": 17, "candidatesTokenCount": 19, "thoughtsTokenCount": 3},
    ])
    store = InMemoryPhaseBStore()

    result = LectureUseCase(model, store).make("d1", "g1", _graph(), "a", allow_spend=True)

    assert result["status"] == "ready"
    assert result["usage"]["promptTokenCount"] == 28
    assert result["usage"]["candidatesTokenCount"] == 32
    assert result["usage"]["thoughtsTokenCount"] == 5
    rows = [row for row in store.usage_rows("d1") if row.get("purpose") == "lecture"]
    assert len(rows) == 2
    assert result["usage"]["cost_usd"] == sum(row["cost_usd"] for row in rows)
    diagnostics = [row for row in store.usage_rows("d1") if row.get("purpose") == "lecture_validation"]
    assert len(diagnostics) == 2
    assert all(row.get("generation_id") for row in diagnostics)


def test_failed_generations_keep_both_attempt_usage_and_log_each_rule_failure():
    model = _StreamModel([_payload([]), _payload([])], [
        {"promptTokenCount": 10, "candidatesTokenCount": 2},
        {"promptTokenCount": 20, "candidatesTokenCount": 3},
    ])
    store = InMemoryPhaseBStore()

    result = LectureUseCase(model, store).make("d1", "g1", _graph(), "a", allow_spend=True)

    assert result["status"] == "fallback"
    assert result["usage"]["promptTokenCount"] == 30
    assert result["usage"]["candidatesTokenCount"] == 5
    diagnostics = [row for row in store.usage_rows("d1") if row.get("purpose") == "lecture_validation"]
    assert len(diagnostics) == 2
    assert [row["validation_rules"] for row in diagnostics] == [["K8"], ["K8"]]


def test_used_later_follows_outgoing_requires_edges_only():
    graph = _graph(with_later=True)

    earlier, _, _ = _assemble(graph, "a", BSettings())
    later, _, _ = _assemble(graph, "b", BSettings())

    assert earlier["used_later"] == ["Phép hợp"]
    assert later["used_later"] == []


def test_lecture_cache_key_includes_validator_version():
    graph = _graph()
    store = InMemoryPhaseBStore()
    first = LectureUseCase(None, store, settings=BSettings(lecture_validator_version="v2")).make(
        "d1", "g1", graph, "a", dry_run=True)
    second = LectureUseCase(None, store, settings=BSettings(lecture_validator_version="v3")).make(
        "d1", "g1", graph, "a", dry_run=True)
    assert first["lecture_key"] != second["lecture_key"]


def test_public_lecture_diagnostics_summarizer_filters_to_validation_rows():
    rows = [
        {"purpose": "lecture", "doc_id": "d1", "input_tokens": 10, "cost_usd": 0.1},
        {"purpose": "lecture_validation", "doc_id": "d1", "generation_id": "g1",
         "generation_index": 0, "validator_version": "v2", "passed": False,
         "validation_rules": ["K6", "K8"], "dropped_by_rule": {"K6": 2},
         "dropped_by_source_label": {"S1": 1}, "failure_reason": "K8: too few"},
        {"purpose": "lecture_validation", "doc_id": "d2", "passed": True,
         "validation_rules": [], "dropped_by_rule": {}, "dropped_by_source_label": {}},
    ]

    result = summarize_lecture_diagnostics(rows, doc_id="d1")

    assert result["generation_count"] == 1
    assert result["failed_by_rule"] == {"K6": 1, "K8": 1}
    assert result["dropped_by_rule"] == {"K6": 2}
    assert result["dropped_by_source_label"] == {"S1": 1}
    assert "cost_usd" not in result


def test_validation_diagnostics_keep_spec_rule_ids_for_bad_label_and_quote():
    from doc2roadmap.application.phase_b.lectures import _valid_item

    graph = _graph()
    context, _, _ = _assemble(graph, "a", BSettings())
    dropped = {}

    bad_label = _valid_item(_item("Một câu có nguồn.", "Tập hợp là một nhóm đối tượng được xác định rõ ràng."),
                            {**context, "sources": {}}, section="explanation", settings=BSettings(),
                            dropped_by_rule=dropped)
    assert bad_label is None
    assert dropped == {"K2": 1}  # Spec K2: source label exists.

    dropped.clear()
    bad_quote = _valid_item(_item("Một câu có nguồn.", "Câu không có trong nguồn."), context,
                            section="explanation", settings=BSettings(), dropped_by_rule=dropped)
    assert bad_quote is None
    assert dropped == {"K3": 1}  # Spec K3: quote is short and verbatim.


def test_truncated_stream_keeps_rule_counts_for_closed_rejected_items():
    invalid = _item("Một câu có nguồn.", "Câu không có trong nguồn.")
    # The candidate is complete, but the top-level array/object is cut off.
    raw = '{"prereq_notes":[],"explanation":[' + json.dumps(invalid, ensure_ascii=False) + ', '
    model = _StreamModel([{}])
    model.stream_json = lambda system, prompt, schema: iter([raw])
    store = InMemoryPhaseBStore()

    LectureUseCase(model, store).make("d1", "g1", _graph(), "a", allow_spend=True)

    diagnostics = [row for row in store.usage_rows("d1") if row.get("purpose") == "lecture_validation"]
    assert diagnostics[0]["dropped_by_rule"].get("K3") == 1


def test_k8_counts_explanations_kept_across_repair_streams_after_dedup():
    first = _item("Tập hợp gồm các phần tử có cùng một đặc điểm.",
                  "Tập hợp gồm các phần tử có cùng một đặc điểm.")
    second = _item("Phép hợp tạo ra một tập hợp mới từ các phần tử đã cho.",
                   "Phép hợp tạo ra một tập hợp mới từ các phần tử đã cho.")
    model = _StreamModel([_payload([first]), _payload([second])])

    result = LectureUseCase(model, InMemoryPhaseBStore()).make(
        "d1", "g1", _graph(), "a", allow_spend=True)

    assert result["status"] == "ready"
    explanation = next(section for section in result["sections"] if section["kind"] == "giai_thich")
    assert [item["text"] for item in explanation["items"]] == [first["text"], second["text"]]
