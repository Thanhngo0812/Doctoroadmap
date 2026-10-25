from __future__ import annotations

from types import SimpleNamespace
from copy import deepcopy
import json
from pathlib import Path
from pydantic import SecretStr

from doc2roadmap.application.phase_b.quiz import QuizUseCase
from doc2roadmap.application.phase_b.quiz_context3 import GENERATION_SCHEMA
from doc2roadmap.application.prerequisite_prompt import PRICING_USD_PER_MILLION
from doc2roadmap.application.phase_b.retrieval import load_learning_graph
from doc2roadmap.application.phase_b.assistant import AssistantUseCase
from doc2roadmap.application.ports.phase_b import Done, ToolCall
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.domain.source_labels import SourceRegistry
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore
from doc2roadmap.infrastructure.llm.phase_b import GeminiToolModel
from doc2roadmap.composition_phase_b import PhaseBRuntime
from doc2roadmap.config import Settings

from sa68_support import make_book


class Graph:
    def __init__(self):
        self.nodes = {
            "a": {"node_id": "a", "name": "Tam giác", "aliases": [{"display_name": "hình tam giác"}],
                  "identity_aliases": [{"raw_name": "tam giác"}], "module_id": "m"},
            "b": {"node_id": "b", "name": "Hình vuông", "module_id": "m"},
            "c": {"node_id": "c", "name": "Hình tròn", "module_id": "m"},
        }
        self.modules = {"m": {"module_id": "m", "doc_id": "d", "title": "Hình học",
                              "node_ids": ["a", "b", "c"]}}
        self.chunks = {
            "ca": SimpleNamespace(chunk_id="ca", text=(
                "Tam giác là hình phẳng có ba cạnh. Hình tam giác được tạo bởi ba đoạn thẳng khép kín."),
                page=4, char_start=0, char_end=90, section_path=["1"]),
            "cb": SimpleNamespace(chunk_id="cb", text=(
                "Hình vuông là hình phẳng có bốn cạnh bằng nhau. Mỗi góc của hình vuông là góc vuông."),
                page=5, char_start=0, char_end=88, section_path=["2"]),
            "cc": SimpleNamespace(chunk_id="cc", text=(
                "Hình tròn là tập hợp các điểm cách đều một tâm. Bán kính nối tâm với đường tròn."),
                page=6, char_start=0, char_end=82, section_path=["3"]),
        }
        for node_id, chunk_id in zip(("a", "b", "c"), ("ca", "cb", "cc")):
            self.nodes[node_id]["teaching_chunk_ids"] = [chunk_id]
            text = self.chunks[chunk_id].text
            self.nodes[node_id]["anchor"] = {"chunk_id": chunk_id, "sentence": text.split(".")[0] + "."}
        self.payload = {"edges": []}

    def new_source_registry(self):
        return SourceRegistry(self.chunks.values())


def test_public_quiz_hides_all_answers_and_events_then_returns_feedback():
    store = InMemoryPhaseBStore()
    usecase = QuizUseCase(Graph(), store)
    events = []

    quiz = usecase.make_quiz("d", "m", "alice", on_event=events.append)

    assert quiz["status"] == "ready"
    assert quiz["ready_count"] == 5
    assert all(len(item["options"]) == 3 for item in quiz["items"])
    public_json = repr((quiz, events))
    for secret in ("is_correct", "why_wrong", "explanation", "correct_option"):
        assert secret not in public_json
    assert [event["event"] for event in events].count("item_ready") == 5
    assert events[-1]["event"] == "done"

    first = quiz["items"][0]
    answer = store.get_record("quiz_attempt", quiz["attempt_id"])["_private"][first["item_id"]]
    correct_option = next(option for option in answer["options"] if option["is_correct"])
    result = usecase.submit(quiz["attempt_id"], "alice", {first["item_id"]: correct_option["option_id"]})

    assert result["correct_count"] == 1
    assert result["results"][0]["is_correct"] is True
    assert result["results"][0]["correct_option"]["evidence"][0]["quote"]
    assert usecase.history("alice", "d")["attempts"][0]["correct_count"] == 1
    assert usecase.history("bob", "d")["attempts"] == []


def test_dry_run_has_no_model_calls_or_store_writes():
    class NoCalls:
        model_id = "fake"

        def start_session(self, _):
            raise AssertionError("dry-run called the model")

    class ReadOnlyStore(InMemoryPhaseBStore):
        writes = 0

        def put_record(self, *args, **kwargs):
            self.writes += 1
            super().put_record(*args, **kwargs)

        def put_cache(self, *args, **kwargs):
            self.writes += 1
            super().put_cache(*args, **kwargs)

        def append_usage(self, *args, **kwargs):
            self.writes += 1
            super().append_usage(*args, **kwargs)

    store = ReadOnlyStore()
    result = QuizUseCase(Graph(), store, NoCalls()).make_quiz("d", "m", "alice", dry_run=True)
    assert result["status"] == "dry_run"
    assert store.writes == 0
    assert store.usage_rows() == []


def test_dry_run_quiz_cost_uses_material_and_four_calls_with_configured_caps():
    class NoCalls:
        model_id = "fake"

        def ask_json(self, *args, **kwargs):
            raise AssertionError("dry-run called a model")

    settings = BSettings(quiz_generation_max_output_tokens=77, quiz_verifier_max_output_tokens=23)
    store = InMemoryPhaseBStore()
    usecase = QuizUseCase(make_book(plain=3, formula=False), store, NoCalls(), verifier_model=NoCalls(), settings=settings)
    result = usecase.make_quiz("d", "m", "alice", dry_run=True)

    assert result["estimated_calls"] == 4 * result["uncached_concepts"] == 12
    assert result["estimated_output_tokens"] == 3 * (2 * 77 + 2 * 23)
    assert result["estimated_input_tokens"] > 0
    expected = (result["estimated_input_tokens"] * PRICING_USD_PER_MILLION["input"]
                + result["estimated_output_tokens"] * PRICING_USD_PER_MILLION["output"]) / 1_000_000
    assert result["estimated_usd"] == round(expected, 6)
    assert result["estimated_usd"] > 0
    assert store.usage_rows() == []
    assert store.list_records("quiz_attempt") == []

    larger_graph = make_book(plain=3, formula=False)
    larger_graph.chunks["c0"].text += " Tài liệu bổ sung mô tả khái niệm." * 200
    larger = QuizUseCase(larger_graph, InMemoryPhaseBStore(), NoCalls(),
                         verifier_model=NoCalls(), settings=settings).make_quiz(
                             "d", "m", "alice", dry_run=True)
    assert larger["estimated_input_tokens"] > result["estimated_input_tokens"]
    assert larger["estimated_usd"] > result["estimated_usd"]


def test_cloze_does_not_blank_hiệu_inside_the_ký_hiệu_compound():
    graph = Graph()
    concept = graph.nodes["a"]
    concept.update(name="Hiệu", aliases=["Hiệu"])
    chunk = graph.chunks["ca"]
    chunk.text = ("Hợp của A và B được kí hiệu bởi A ∪ B. "
                  "Hiệu của A trừ B là các phần tử thuộc A mà không thuộc B.")
    concept["anchor"] = {"chunk_id": "ca", "sentence": "Hợp của A và B được kí hiệu bởi A ∪ B."}

    quiz = QuizUseCase(graph, InMemoryPhaseBStore()).make_quiz("d", "m", "alice", n=1)

    assert quiz["ready_count"] == 1
    assert "___ của A trừ B" in quiz["items"][0]["stem"]
    assert "kí ___" not in quiz["items"][0]["stem"]


def test_cloze_sources_are_short_context_labels_and_the_bank_key_is_order_independent():
    graph = Graph()
    usecase = QuizUseCase(graph, InMemoryPhaseBStore())
    concept_a, concept_b = usecase._concepts("m", ["a", "b"])

    context_a_first = usecase._context("m", concept_a)
    context_b_second = usecase._context("m", concept_b)
    context_b_first = usecase._context("m", concept_b)
    context_a_second = usecase._context("m", concept_a)

    assert [row["label"] for row in context_a_first["chunks"]] == ["S1"]
    assert [row["label"] for row in context_a_second["chunks"]] == ["S1"]
    assert [row["label"] for row in context_b_first["chunks"]] == ["S1"]
    assert [row["label"] for row in context_b_second["chunks"]] == ["S1"]
    assert usecase._bank_key("d", "m", concept_a, None) == usecase._bank_key("d", "m", concept_a, None)
    assert usecase._bank_key("d", "m", concept_a, None) != usecase._bank_key("d", "m", concept_b, None)


def test_question_reports_hide_after_distinct_owners_only():
    usecase = QuizUseCase(Graph(), InMemoryPhaseBStore(), settings={"quiz_hide_report_threshold": 2})
    quiz = usecase.make_quiz("d", "m", "alice")
    item_id = quiz["items"][0]["item_id"]

    assert usecase.report_question("alice", quiz["attempt_id"], item_id)["hidden"] is False
    assert usecase.report_question("alice", quiz["attempt_id"], item_id)["hidden"] is False
    bob_initial = usecase.make_quiz("d", "m", "bob")
    assert usecase.report_question("bob", bob_initial["attempt_id"], item_id)["hidden"] is True
    bob_quiz = usecase.make_quiz("d", "m", "bob")
    assert item_id not in {item["item_id"] for item in bob_quiz["items"]}


def test_small_modules_fill_five_with_variants_when_available():
    graph = Graph()
    graph.modules["m"]["node_ids"] = ["a", "b", "c"]
    # Each concept has two independent quoted sentences, so the fallback creates variants.
    for node_id in ("a", "b", "c"):
        chunk = graph.chunks[graph.nodes[node_id]["teaching_chunk_ids"][0]]
        chunk.text += f" {graph.nodes[node_id]['name']} is discussed again in this second source sentence."
    quiz = QuizUseCase(graph, InMemoryPhaseBStore()).make_quiz("d", "m", "alice")
    assert quiz["ready_count"] == 5


def test_cloze_requires_named_anchor_sentence_in_same_source_chunk():
    graph = Graph()
    graph.nodes["a"]["anchor"]["sentence"] = "A short unrelated sentence."
    usecase = QuizUseCase(graph, InMemoryPhaseBStore())
    concept = usecase._concepts("m", ["a"])[0]
    context = usecase._context("m", concept)

    assert usecase._cloze_bank(concept, context) == []


def test_fallback_context_only_uses_chunks_mapped_to_the_same_module():
    graph = Graph()
    concept = graph.nodes["a"]
    concept["teaching_chunk_ids"] = []
    concept.pop("anchor")
    graph.chunks["cb"].text = "Tam giác xuất hiện trong một chunk khác."
    graph.payload["chunk_module_map"] = {"cb": {"module_id": "other"}, "cc": {"module_id": "m"}}
    graph.chunks["cc"].text += " Tam giác xuất hiện trong module này."
    usecase = QuizUseCase(graph, InMemoryPhaseBStore())

    assert [chunk.chunk_id for chunk in usecase._chunks_for(concept)] == ["cc"]


def test_get_attempt_returns_owned_answer_free_snapshot():
    usecase = QuizUseCase(Graph(), InMemoryPhaseBStore())
    quiz = usecase.make_quiz("d", "m", "alice", n=1)

    snapshot = usecase.get_attempt(quiz["attempt_id"], "alice")
    assert snapshot["attempt_id"] == quiz["attempt_id"]
    assert snapshot["items"] == quiz["items"]
    assert "answers" not in repr(snapshot)
    assert "is_correct" not in repr(snapshot)
    try:
        usecase.get_attempt(quiz["attempt_id"], "bob")
    except KeyError:
        pass
    else:
        raise AssertionError("attempt snapshot was not owner-scoped")


# Serialized synthetic artifacts keep this regression independent of development caches.
QUIZ_GRAPH_FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "phase_b_quiz_graph"


def test_fixture_graph_dict_aliases_and_item_ready_stream_to_five():
    graph = load_learning_graph(JsonArtifactStore(QUIZ_GRAPH_FIXTURE), "doc-1", graph_version=1)
    alias_node = next(node for node in graph.learnable_nodes.values()
                      if node.get("aliases") and isinstance(node["aliases"][0], dict))
    usecase = QuizUseCase(graph, InMemoryPhaseBStore())
    assert usecase._aliases(alias_node)
    events = []

    quiz = usecase.make_quiz("doc-1", "module_023", "alice", n=5, on_event=events.append)

    assert quiz["ready_count"] == 5
    assert sum(event["event"] == "item_ready" for event in events) == 5
    assert events[-1]["event"] == "done"
    assert all("is_correct" not in repr(event) for event in events)


def test_assistant_make_quiz_tool_returns_only_attempt_reference_and_count():
    graph = load_learning_graph(JsonArtifactStore(QUIZ_GRAPH_FIXTURE), "doc-1", graph_version=1)
    store = InMemoryPhaseBStore()
    quiz_usecase = QuizUseCase(graph, store)

    class Model:
        model_id = "scripted-assistant"

        def start_session(self, _system_prompt, _tools):
            return self

        def stream(self, _messages, *, mode):
            if mode == "AUTO":
                yield ToolCall("make_quiz", {"scope": "module_023", "n": 5}, "quiz")
                yield Done({})
            else:
                yield Done({})

    def make_quiz(scope, n=None, level=None, *, owner, **kwargs):
        return quiz_usecase.make_quiz(graph.doc_id, scope, owner, n=n, level=level,
                                      origin="assistant", allow_spend=False)

    assistant = AssistantUseCase(graph, store, Model(), quiz=make_quiz)
    from doc2roadmap.domain.scope import module_scope
    session = assistant.sessions.create_session("alice", graph.doc_id, module_scope(graph, "module_023"))
    result = assistant.ask(graph.doc_id, graph.graph_version, session["session_id"], "Kiểm tra tôi.",
                           owner="alice", allow_spend=True)

    summary = result["tool_calls"][0]["result_summary"]
    assert summary["count"] == 5
    assert summary["artifact"]["kind"] == "quiz"
    assert "items" not in repr(summary) and "is_correct" not in repr(summary)


def test_quiz_3_schema_is_sent_as_json_schema_in_fake_http_request():
    model = GeminiToolModel("test-key")
    captured = {}

    class Response:
        def __init__(self):
            import io
            self.body = io.BytesIO(json.dumps({"candidates": [{"content": {"parts": [{"text": "{\"items\":[]}"}]}}]}).encode())

        def read(self, size=-1):
            return self.body.read(size)

        def close(self):
            pass

    def fake_http(operation, body, *, stream):
        assert operation == "generateContent" and stream is False
        captured.update(body)
        return Response()

    model._request = fake_http
    reply = model.ask_json("prompt", response_schema=GENERATION_SCHEMA)

    schema = captured["generationConfig"]["responseJsonSchema"]
    assert reply.payload == {"items": []}
    assert schema["type"] == "object"
    assert schema["properties"]["items"]["items"]["required"] == [
        "bloom", "stem", "options", "correct_index", "explanation", "source_labels"]
    assert schema["properties"]["items"]["items"]["properties"]["options"]["minItems"] == 4


def test_runtime_gives_the_generator_4096_and_the_solver_8192_output_tokens():
    runtime = PhaseBRuntime(settings=Settings(artifact_dir=Path("artifacts"),
                                               gemini_api_key=SecretStr("fake-key")), mode="gemini")
    usecase = runtime.quiz(Graph())

    assert usecase.model.max_output_tokens == 4096
    assert usecase.verifier_model.max_output_tokens == 8192
    assert usecase.model is not usecase.verifier_model


def test_aliases_of_a_concept_read_dict_and_identity_aliases():
    usecase = QuizUseCase(Graph(), InMemoryPhaseBStore())
    concept = usecase._concepts("m", ["a"])[0]
    assert {"hình tam giác", "tam giác"} <= set(usecase._aliases(concept))


def test_two_questions_with_the_same_stem_and_answer_are_duplicates():
    usecase = QuizUseCase(Graph(), InMemoryPhaseBStore())
    item = {"stem": "Một hình có ba cạnh là gì?",
            "options": [{"text": "Tam giác", "is_correct": True}, {"text": "Hình vuông", "is_correct": False}]}
    assert usecase._duplicate(item, deepcopy(item))
    assert not usecase._duplicate(item, {"stem": "Hình có bốn cạnh bằng nhau là gì?",
                                         "options": [{"text": "Hình vuông", "is_correct": True}]})
