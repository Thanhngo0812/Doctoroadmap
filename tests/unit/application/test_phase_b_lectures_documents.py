import json
from types import SimpleNamespace

from doc2roadmap.application.phase_b.documents import DocumentUseCase, _cap_context
from doc2roadmap.application.phase_b.lectures import LectureUseCase, _assemble, _trim_context
from doc2roadmap.application.phase_b.common import stable_json
from doc2roadmap.domain.learning_graph import LearningGraph
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore
import doc2roadmap.application.phase_b.lectures as lecture_module


def _graph():
    text = "Tế bào là đơn vị cấu trúc cơ bản của cơ thể. Tế bào thực hiện các chức năng sống."
    chunk = SimpleNamespace(chunk_id="c1", doc_id="d1", order_index=0, split_index=0,
                            page=2, char_start=50, char_end=50 + len(text), parent_section_id="s1",
                            section_path=["Sinh học"], heading_level=1, block_types=["paragraph"],
                            text=text, context_prefix=None, image_refs=[], token_count=20,
                            tokenizer_id="test", table_refs=[], formula_refs=[], role="noi_dung")
    payload = {
        "doc_id": "d1", "graph_version": "g1",
        "nodes": [{"node_id": "n1", "name": "Tế bào", "display_name": "Tế bào",
                   "learnable": True, "module_id": "m1", "teaching_chunk_ids": ["c1"],
                   "defining_chunk_ids": [],
                   "anchor": {"chunk_id": "c1", "sentence": "Tế bào là đơn vị cấu trúc cơ bản của cơ thể."}}],
        "modules": [{"module_id": "m1", "index": 1, "title": "Cơ sở", "node_ids": ["n1"]}],
        "requires_edges": [], "open_edges": [],
    }
    extra_text = "Tế bào gồm nhiều thành phần có chức năng khác nhau."
    extra = SimpleNamespace(**{**vars(chunk), "chunk_id": "c2", "order_index": 1,
                               "char_start": 200, "char_end": 200 + len(extra_text), "text": extra_text})
    return LearningGraph(payload, [chunk, extra])


def test_real_learning_graph_assembles_json_prompt_without_serializing_registry():
    context, _, _ = _assemble(_graph(), "n1", BSettings())
    assert context["sources"]["S1"]["text"].startswith("Tế bào")
    assert context["registry"].resolve("S1")["chunk_id"] == "c1"


def test_lecture_context_trim_prunes_dropped_raw_source_from_serialized_prompt():
    context = {
        "definition": {"source": "S1"},
        "teaching": [{"label": "S1", "text": "core"}],
        "extra_definitions": [{"label": "S2", "text": "optional" * 100}],
        "sources": {"S1": {"label": "S1", "text": "core"},
                    "S2": {"label": "S2", "text": "optional" * 100}},
    }
    before_bytes = len(stable_json(context).encode("utf-8"))
    trimmed = _trim_context(context, BSettings(lecture_context_tokens=80))
    prompt_context = {key: value for key, value in trimmed.items() if key != "registry"}
    after_bytes = len(stable_json(prompt_context).encode("utf-8"))
    assert "S2" not in trimmed["sources"]
    assert after_bytes < before_bytes


def test_legacy_prerequisite_excerpt_is_shown_with_missing_quote_warning():
    graph = _graph()
    graph.chunks["c2"].text = "Nền tảng hỗ trợ khái niệm Tế bào trong bài học."
    graph.chunks["c2"].char_end = graph.chunks["c2"].char_start + len(graph.chunks["c2"].text)
    graph.payload["nodes"][0]["display_prerequisites"] = ["n0"]
    graph.nodes["n0"] = {"node_id": "n0", "name": "Nền tảng", "display_name": "Nền tảng",
                          "learnable": True, "module_id": "m1", "anchor": {"chunk_id": "c2"},
                          "teaching_chunk_ids": ["c2"]}
    graph.payload["requires_edges"] = [{"source": "n0", "target": "n1", "edge_type": "requires",
                                         "chunk_ids": ["c2"], "reason": "legacy generated reason"}]
    context, skeleton, _ = _assemble(graph, "n1", BSettings())
    prerequisite = context["prerequisites"][0]
    assert prerequisite["citation_source"] == "legacy_excerpt"
    assert prerequisite["warning"] == "missing_edge_quote"
    assert "thiếu câu trích" in prerequisite["note"]
    assert skeleton["prerequisites"][0]["why"]["citation_source"] == "legacy_excerpt"


def test_no_model_falls_back_locally_and_cache_rebinds_graph_version():
    graph = _graph()
    store = InMemoryPhaseBStore()
    use_case = LectureUseCase(None, store)

    first = use_case.make("d1", "g1", graph, "n1")
    second = use_case.get("d1", "g2", graph, "n1")

    assert first["status"] == "fallback"
    assert first["sections"][0]["items"][0]["citations"][0]["chunk_id"] == "c1"
    assert second["lecture_key"] == first["lecture_key"]
    assert second["graph_version"] == "g2"
    assert store.usage_rows("d1") == []


def test_extractive_fallback_cache_does_not_hide_later_live_generation():
    sentence1 = "Tế bào là đơn vị cấu trúc cơ bản của cơ thể."
    sentence2 = "Tế bào thực hiện các chức năng sống."

    class LiveModel:
        model_id = "gemini-3.1-flash-lite"

        def __init__(self):
            self.calls = 0

        def stream_json(self, system, prompt, schema):
            self.calls += 1
            payload = {"prereq_notes": [], "example": [], "contrasts": [], "gaps": [],
                       "explanation": [
                           {"text": sentence1, "sources": ["S1"], "quote": sentence1},
                           {"text": sentence2, "sources": ["S1"], "quote": sentence2},
                       ]}
            return iter([json.dumps(payload, ensure_ascii=False)])

    store = InMemoryPhaseBStore()
    fallback = LectureUseCase(None, store).make("d1", "g1", _graph(), "n1")
    model = LiveModel()
    live = LectureUseCase(model, store).make("d1", "g1", _graph(), "n1", allow_spend=True)

    assert fallback["status"] == "fallback"
    assert live["status"] == "ready"
    assert live["lecture_key"] != fallback["lecture_key"]
    assert model.calls == 1


def test_lecture_no_source_is_explicit_and_reports_mention_only_sources():
    graph = _graph()
    graph.nodes["n1"]["teaching_chunk_ids"] = []
    graph.nodes["n1"]["defining_chunk_ids"] = []
    graph.nodes["n1"]["anchor"] = {}
    result = LectureUseCase(None, InMemoryPhaseBStore()).make("d1", "g1", graph, "n1")
    assert result["status"] == "no_source"
    assert result["sections"] == []
    assert result["mention_sources"]


def test_missing_formula_warning_survives_local_fallback():
    graph = _graph()
    graph.chunks["c1"].formula_refs = [{"formula_id": "f1"}]
    graph.tree = SimpleNamespace(nodes=[{"node_type": "formula", "formula_id": "f1", "page": 2,
                                        "reading_order": 0, "raw_text": "x = 1", "bbox": None}])
    result = LectureUseCase(None, InMemoryPhaseBStore()).make("d1", "g1", graph, "n1")
    assert "thieu_cong_thuc" in result["warnings"]
    assert "model_unavailable" in result["warnings"]


def test_public_lecture_retains_formula_image_ids_for_repeated_occurrences():
    graph = _graph()
    graph.chunks["c1"].formula_refs = [{"formula_id": "f1"}]
    graph.chunks["c2"].formula_refs = [{"formula_id": "f1"}]
    graph.chunks["c2"].page = 3
    graph.nodes["n1"]["teaching_chunk_ids"] = ["c1", "c2"]
    graph.tree = SimpleNamespace(nodes=[
        {"node_type": "formula", "formula_id": "f1", "page": 2, "reading_order": 0,
         "raw_text": "x = 1", "bbox": [1, 2, 3, 4]},
        {"node_type": "formula", "formula_id": "f1", "page": 3, "reading_order": 0,
         "raw_text": "x = 2", "bbox": [5, 6, 7, 8]},
    ])
    first = "a" * 64
    second = "b" * 64
    graph.formula_images = {
        "f1@p2:r0": {"occurrence_id": "f1@p2:r0", "formula_id": "f1", "page": 2,
                      "reading_order": 0, "bbox": [1, 2, 3, 4], "raw_text": "x = 1",
                      "status": "cut", "media_id": first, "image_ref": f"images/{first}.png"},
        "f1@p3:r0": {"occurrence_id": "f1@p3:r0", "formula_id": "f1", "page": 3,
                      "reading_order": 0, "bbox": [5, 6, 7, 8], "raw_text": "x = 2",
                      "status": "cut", "media_id": second, "image_ref": f"images/{second}.png"},
    }

    result = LectureUseCase(None, InMemoryPhaseBStore()).make("d1", "g1", graph, "n1")
    refs = result["definition"]["formula_refs"]
    assert [row["occurrence_id"] for row in refs] == ["f1@p2:r0", "f1@p3:r0"]
    assert [row["media_id"] for row in refs] == [first, second]
    assert [row["image_ref"] for row in refs] == [f"images/{first}.png", f"images/{second}.png"]
    assert "thieu_cong_thuc" not in result["warnings"]


def test_formula_image_missing_with_bbox_still_warns():
    graph = _graph()
    graph.chunks["c1"].formula_refs = [{"formula_id": "f1"}]
    graph.tree = SimpleNamespace(nodes=[{"node_type": "formula", "formula_id": "f1", "page": 2,
                                        "reading_order": 0, "raw_text": None, "bbox": [1, 2, 3, 4]}])
    graph.formula_images = {}
    result = LectureUseCase(None, InMemoryPhaseBStore()).make("d1", "g1", graph, "n1")
    assert "thieu_cong_thuc" in result["warnings"]


def test_lecture_prefetch_queues_next_concept_after_current_response(monkeypatch):
    graph = _graph()
    graph.nodes["n2"] = {"node_id": "n2", "name": "Thành phần", "display_name": "Thành phần",
                          "learnable": True, "module_id": "m1", "teaching_chunk_ids": ["c2"],
                          "defining_chunk_ids": [], "anchor": {"chunk_id": "c2"}}
    graph.modules["m1"]["node_ids"] = ["n1", "n2"]
    queued = []

    class Background:
        def __init__(self, *, target, args, kwargs, daemon):
            queued.append((target, args, kwargs, daemon))

        def start(self):
            pass

    monkeypatch.setattr(lecture_module, "Thread", Background)
    result = LectureUseCase(None, InMemoryPhaseBStore()).make("d1", "g1", graph, "n1", preload_next=True)
    assert result["status"] == "fallback"
    assert queued[0][1][3] == "n2"
    assert queued[0][3] is True


def test_stream_failure_does_not_retract_validated_item():
    sentence = "Tế bào là đơn vị cấu trúc cơ bản của cơ thể."

    class BrokenStream:
        model_id = "scripted"

        def stream_json(self, system, prompt, schema):
            def events():
                yield '{"explanation":[{"text":"' + sentence + '","sources":["S1"],"quote":"' + sentence + '"}'
                raise RuntimeError("disconnected")
            return events()

    store = InMemoryPhaseBStore()
    result = LectureUseCase(BrokenStream(), store).make("d1", "g1", _graph(), "n1", allow_spend=True)
    explanation = next(section for section in result["sections"] if section["kind"] == "giai_thich")
    assert explanation["items"][0]["text"] == sentence
    assert result["status"] == "fallback"
    assert len(store.usage_rows("d1")) == 2


def test_document_context_cap_prunes_removed_source_text():
    settings = BSettings(document_context_tokens=1)
    context = {
        "concepts": [{"concept": {"node_id": "n1"}, "teaching": [{"label": "S1"}],
                      "extra_definitions": [{"label": "S2"}]}],
        "retrieved": [{"label": "S3", "text": "large"}],
        "sources": {label: {"text": "x" * 100} for label in ("S1", "S2", "S3")},
    }
    capped, truncated = _cap_context(context, settings)
    assert truncated
    mentioned = {row["label"] for row in capped["concepts"][0]["teaching"]}
    assert set(capped["sources"]) == mentioned
    assert "S3" not in capped["sources"]


def test_document_context_cap_keeps_serialized_prompt_under_token_budget():
    source_text = "x" * 40_000
    context = {"scope": {"node_ids": ["n1"]},
               "concepts": [{"concept": {"node_id": "n1"}, "teaching": [{"label": "S1"}]}],
               "retrieved": [], "sources": {"S1": {"label": "S1", "text": source_text}}}
    capped, truncated = _cap_context(context, BSettings(document_context_tokens=8000))
    assert truncated
    assert len(stable_json(capped)) // 3 <= 8000
    assert len(source_text) == 40_000


def test_document_owner_boundary_export_and_dry_run():
    sentence = "Tế bào là đơn vị cấu trúc cơ bản của cơ thể."

    class ScriptedJson:
        model_id = "scripted"

        def ask_json(self, prompt, *, response_schema, system_prompt=""):
            from doc2roadmap.application.ports.extraction import ExtractionReply
            return ExtractionReply({"title": "Tế bào", "markdown": f"{sentence} [S1]",
                                   "citations": [{"label": "S1", "quote": sentence}],
                                   "outside_document_blocks": ["Ví dụ bổ sung"]}, "", usage={
                                       "promptTokenCount": 100, "candidatesTokenCount": 50,
                                       "thoughtsTokenCount": 10})

    store = InMemoryPhaseBStore()
    use_case = DocumentUseCase(ScriptedJson(), store)
    estimate = use_case.create("d1", "g1", _graph(), "Tạo tài liệu", "n1", owner="alice", dry_run=True)
    assert estimate["dry_run"] is True
    assert store.list_records("documents") == []
    document = use_case.create("d1", "g1", _graph(), "Tạo tài liệu", "n1", owner="alice", allow_spend=True)
    assert use_case.get(document["document_id"], owner="bob") is None
    assert use_case.get(document["document_id"], owner="alice")["status"] == "ready"
    exported = use_case.export(document["document_id"], owner="alice")
    assert "Ví dụ bổ sung" in exported
    assert "[^S1]: tr. 2" in exported
    assert document["usage"]["thought_tokens"] == 10


def test_invalid_document_json_returns_persisted_failed_document_with_billed_usage():
    class Session:
        last_usage = {"promptTokenCount": 100, "candidatesTokenCount": 20, "thoughtsTokenCount": 5}

        def ask_json(self, prompt, *, response_schema):
            raise json.JSONDecodeError("invalid", "{truncated", 1)

    class Model:
        model_id = "scripted"

        def start_session(self, system_prompt):
            return Session()

    store = InMemoryPhaseBStore()
    use_case = DocumentUseCase(Model(), store)
    document = use_case.create("d1", "g1", _graph(), "Tạo tài liệu", "n1",
                               owner="alice", allow_spend=True)
    assert document["status"] == "failed"
    assert document["reason"] == "invalid_model_response"
    assert document["usage"]["input_tokens"] == 100
    assert document["usage"]["output_tokens"] == 20
    assert document["usage"]["thought_tokens"] == 5
    assert use_case.get(document["document_id"], owner="alice") == document
    assert len(store.usage_rows("d1")) == 1
    assert store.usage_rows("d1")[0]["cost_usd"] > 0


def test_provider_schemas_require_grounded_lecture_fields_and_document_citations():
    from doc2roadmap.application.phase_b.documents import DOCUMENT_SCHEMA
    from doc2roadmap.application.phase_b.lectures import LECTURE_SCHEMA

    citation = DOCUMENT_SCHEMA["properties"]["citations"]["items"]
    assert citation["required"] == ["label", "quote"]
    assert set(citation["properties"]) == {"label", "quote"}
    for field in ("prereq_notes", "explanation", "example", "contrasts"):
        item = LECTURE_SCHEMA["properties"][field]["items"]
        assert {"text", "sources", "quote", "outside_document"} <= set(item["required"])
    check = LECTURE_SCHEMA["properties"]["self_check"]
    assert {"question", "answer", "sources", "quote"} <= set(check["required"])


def test_document_injected_hybrid_retriever_is_dry_run_safe_and_uses_local_labels():
    sentence = "Tế bào gồm nhiều thành phần có chức năng khác nhau."

    class Search:
        calls = []

        def search(self, query, **kwargs):
            self.calls.append(kwargs)
            if kwargs["dry_run"]:
                return {"estimated_cost_usd": 0.00001}
            return [{"chunk_id": "c2", "text": sentence}]

    class ScriptedJson:
        model_id = "scripted"

        def ask_json(self, prompt, *, response_schema, system_prompt=""):
            from doc2roadmap.application.ports.extraction import ExtractionReply
            return ExtractionReply({"title": "Tế bào", "markdown": f"{sentence} [S2]",
                                   "citations": [{"label": "S2", "quote": sentence}],
                                   "outside_document_blocks": []}, "", usage={})

    search = Search()
    use_case = DocumentUseCase(ScriptedJson(), InMemoryPhaseBStore(), retriever=search)
    estimate = use_case.create("d1", "g1", _graph(), "khác", "n1", owner="a", dry_run=True)
    assert estimate["estimate_usd"] >= 0.00001
    result = use_case.create("d1", "g1", _graph(), "khác", "n1", owner="a", allow_spend=True)
    assert search.calls == [
        {"doc_id": "d1", "graph_version": "g1", "current_module_id": "m1", "scope": "all",
         "k": 5, "dry_run": True, "allow_spend": False},
        {"doc_id": "d1", "graph_version": "g1", "current_module_id": "m1", "scope": "all",
         "k": 5, "dry_run": False, "allow_spend": True},
    ]
    assert result["status"] == "ready"
