from __future__ import annotations

from types import SimpleNamespace
from copy import deepcopy
import json
from pathlib import Path
from pydantic import SecretStr

from doc2roadmap.application.phase_b.quiz import QUIZ_SCHEMA, QuizUseCase
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


def test_dry_run_quiz_cost_uses_context_and_four_calls_with_configured_caps():
    class NoCalls:
        model_id = "fake"

        def ask_json(self, *args, **kwargs):
            raise AssertionError("dry-run called a model")

    settings = BSettings(quiz_generation_max_output_tokens=77, quiz_verifier_max_output_tokens=23)
    store = InMemoryPhaseBStore()
    usecase = QuizUseCase(Graph(), store, NoCalls(), verifier_model=NoCalls(), settings=settings)
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

    larger_graph = Graph()
    larger_graph.chunks["ca"].text += " Tài liệu bổ sung mô tả khái niệm." * 200
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


def test_quiz_sources_are_short_context_labels_and_context_hash_is_order_independent():
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
    assert usecase._bank_key("d", "m", concept_a, None, context=context_a_first) == \
        usecase._bank_key("d", "m", concept_a, None, context=context_a_second)

    prompt = usecase._generation_prompt(context_a_first)
    assert "tuyệt đối không ghi chunk_id hay ID nội bộ" in prompt
    assert "tối đa 200 ký tự" in prompt
    assert "đúng 3 phương án" in prompt
    assert "_source_registry" not in prompt


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


def test_blind_verifier_rejecting_its_answer_uses_cloze_and_logs_both_model_calls():
    class Reply:
        usage = {"promptTokenCount": 100, "candidatesTokenCount": 20}

        def __init__(self, payload):
            self.payload = payload

    class Model:
        def __init__(self, model_id):
            self.model_id = model_id
            self.calls = 0

        def start_session(self, _system_prompt):
            return self

        def ask_json(self, prompt, response_schema):
            import json
            self.calls += 1

            assert response_schema["type"] == "object"
            assert response_schema["properties"]["items"]["items"]["type"] == "object"

            if prompt.startswith("Giải mù"):
                data = json.loads(prompt.split("\n", 1)[1])
                item = data["items"][0]
                assert set(item) == {"item_id", "stem", "options"}
                assert all(set(option) == {"option_id", "text"} for option in item["options"])
                assert all("correct" not in repr(option).casefold() for option in item["options"])
                wrong = next(option for option in item["options"] if option["text"] != "Tam giác")
                return Reply({"items": [{"item_id": item["item_id"],
                                         "selected_option_id": wrong["option_id"],
                                         "valid": True, "quote": "Tam giác là hình phẳng có ba cạnh.",
                                         "distractor_verdicts": []}]})
            return Reply({"items": [{
                "concept": "Tam giác",
                "stem": "Một hình phẳng có ba cạnh được gọi là gì?", "bloom": "hieu",
                "correct": {"text": "Tam giác", "sources": ["S1"], "quote": "Tam giác là hình phẳng có ba cạnh."},
                "distractors": [
                    {"text": "Hình vuông", "from": "D1", "why_wrong": "Có bốn cạnh.",
                     "sources": ["D1"], "quote": "Hình vuông là hình phẳng có bốn cạnh bằng nhau."},
                    {"text": "Hình tròn", "from": "D2", "why_wrong": "Không có cạnh.",
                     "sources": ["D2"], "quote": "Hình tròn là tập hợp các điểm cách đều một tâm."},
                ],
                "explanation": "Nguồn định nghĩa khái niệm qua số cạnh.", "formula_refs": [],
            }]})

    store = InMemoryPhaseBStore()
    generator, verifier = Model("generator"), Model("verifier")
    quiz = QuizUseCase(Graph(), store, generator, verifier_model=verifier).make_quiz(
        "d", "m", "alice", node_ids=["a"], allow_spend=True)

    assert quiz["ready_count"] == 1
    assert quiz["items"][0]["generator"] == "cloze"
    assert len(store.usage_rows("d")) == 4
    assert {row["purpose"] for row in store.usage_rows("d")} == {"quiz_gen", "quiz_verify"}
    assert generator.calls == verifier.calls == 2
    assert {row["model_id"] for row in store.usage_rows("d")} == {"generator", "verifier"}


def test_generator_repairs_chunk_ids_to_short_labels_then_blind_verifier_accepts():
    class Reply:
        usage = {"promptTokenCount": 80, "candidatesTokenCount": 20}

        def __init__(self, payload):
            self.payload = payload

    class Generator:
        model_id = "generator"

        def __init__(self):
            self.calls = 0
            self.prompts = []

        def start_session(self, _system_prompt, _tools=()):
            return self

        def ask_json(self, prompt, *, response_schema):
            self.calls += 1
            self.prompts.append(prompt)
            assert response_schema["type"] == "object"
            sources = ["ca"] if self.calls == 1 else ["S1"]
            return Reply({"items": [{
                "concept": "Tam giác", "stem": "Một hình có ba cạnh là gì?", "bloom": "hieu",
                "correct": {"text": "Tam giác", "sources": sources,
                            "quote": "Tam giác là hình phẳng có ba cạnh."},
                "distractors": [
                    {"text": "Hình vuông", "from": "D1", "why_wrong": "Có bốn cạnh.",
                     "sources": ["D1"], "quote": "Hình vuông là hình phẳng có bốn cạnh bằng nhau."},
                    {"text": "Hình tròn", "from": "D2", "why_wrong": "Không có cạnh.",
                     "sources": ["D2"], "quote": "Hình tròn là tập hợp các điểm cách đều một tâm."},
                ], "explanation": "Định nghĩa nêu số cạnh.", "formula_refs": [],
            }], "gaps": []})

    class Verifier:
        model_id = "verifier"

        def __init__(self):
            self.calls = 0

        def start_session(self, _system_prompt, _tools=()):
            return self

        def ask_json(self, prompt, *, response_schema):
            self.calls += 1
            assert prompt.startswith("Giải mù")
            data = json.loads(prompt.split("\n", 1)[1])
            options = data["items"][0]["options"]
            assert all(set(option) == {"option_id", "text"} for option in options)
            assert "is_correct" not in prompt and "why_wrong" not in prompt
            answer = next(option for option in options if option["text"] == "Tam giác")
            distractor_verdicts = [
                {"option_id": option["option_id"], "verdict": "sai theo nguồn"}
                for option in options if option is not answer
            ]
            return Reply({"items": [{"item_id": data["items"][0]["item_id"],
                                     "selected_option_id": answer["option_id"], "valid": True,
                                     "quote": "Tam giác là hình phẳng có ba cạnh.",
                                     "distractor_verdicts": distractor_verdicts}]})

    store = InMemoryPhaseBStore()
    generator, verifier = Generator(), Verifier()
    usecase = QuizUseCase(Graph(), store, generator, verifier_model=verifier)
    concept = usecase._concepts("m", ["a"])[0]
    context = usecase._context("m", concept)
    first_payload = {"concept": "Tam giác", "stem": "Một hình có ba cạnh là gì?", "bloom": "hieu",
                     "correct": {"text": "Tam giác", "sources": ["ca"],
                                 "quote": "Tam giác là hình phẳng có ba cạnh."},
                     "distractors": [
                         {"text": "Hình vuông", "from": "D1", "why_wrong": "Có bốn cạnh.",
                          "sources": ["D1"], "quote": "Hình vuông là hình phẳng có bốn cạnh bằng nhau."},
                         {"text": "Hình tròn", "from": "D2", "why_wrong": "Không có cạnh.",
                          "sources": ["D2"], "quote": "Hình tròn là tập hợp các điểm cách đều một tâm."}],
                     "explanation": "Định nghĩa nêu số cạnh.", "formula_refs": []}
    assert usecase._normalize_item(concept, context, first_payload) is None

    quiz = usecase.make_quiz("d", "m", "alice", node_ids=["a"], allow_spend=True)
    assert quiz["status"] == "ready"
    assert quiz["items"][0]["generator"] == "llm"
    assert generator.calls == 2
    assert verifier.calls == 1
    assert all("tuyệt đối không ghi chunk_id hay ID nội bộ" in prompt for prompt in generator.prompts)
    assert len(store.usage_rows("d")) == 3


def test_no_eligible_distractors_uses_moi_source_and_passes_blind_verifier():
    class Reply:
        usage = {"promptTokenCount": 90, "candidatesTokenCount": 22}

        def __init__(self, payload):
            self.payload = payload

    class Generator:
        model_id = "generator"

        def start_session(self, _system_prompt, _tools=()):
            return self

        def ask_json(self, prompt, *, response_schema):
            assert "Nếu không có candidate phù hợp" in prompt
            assert "from='moi'" in prompt and "sources chỉ chứa S-label" in prompt
            assert "1.3 lần" in prompt
            return Reply({"items": [{
                "concept": "Tam giác", "stem": "Một hình phẳng có ba cạnh được gọi là gì?",
                "bloom": "hieu",
                "correct": {"text": "Tam giác", "sources": ["S1"],
                            "quote": "Tam giác là hình phẳng có ba cạnh."},
                "distractors": [
                    {"text": "Hình vuông", "from": "moi", "why_wrong": "Có bốn cạnh.",
                     "sources": ["S1"], "quote": "Tam giác là hình phẳng có ba cạnh."},
                    {"text": "Hình tròn", "from": "moi", "why_wrong": "Không có cạnh.",
                     "sources": ["S1"], "quote": "Tam giác là hình phẳng có ba cạnh."},
                ], "explanation": "Nguồn nói tam giác có ba cạnh.", "formula_refs": [],
            }], "gaps": []})

    class Verifier:
        model_id = "verifier"

        def __init__(self):
            self.calls = 0

        def start_session(self, _system_prompt, _tools=()):
            return self

        def ask_json(self, prompt, *, response_schema):
            self.calls += 1
            assert prompt.startswith("Giải mù")
            data = json.loads(prompt.split("\n", 1)[1])
            item = data["items"][0]
            answer = next(option for option in item["options"] if option["text"] == "Tam giác")
            return Reply({"items": [{"item_id": item["item_id"],
                                     "selected_option_id": answer["option_id"], "valid": True,
                                     "quote": "Tam giác là hình phẳng có ba cạnh.",
                                     "distractor_verdicts": [
                                         {"option_id": option["option_id"], "verdict": "sai theo nguồn"}
                                         for option in item["options"] if option is not answer]}]})

    graph = Graph()
    # All distractor concepts point to the target's chunk, so none can be cited as D.
    for node_id in ("b", "c"):
        graph.nodes[node_id]["anchor"]["chunk_id"] = "ca"
    store = InMemoryPhaseBStore()
    verifier = Verifier()
    usecase = QuizUseCase(graph, store, Generator(), verifier_model=verifier)
    concept = usecase._concepts("m", ["a"])[0]
    context = usecase._context("m", concept)
    assert context["distractor_candidates"] == []

    quiz = usecase.make_quiz("d", "m", "alice", node_ids=["a"], allow_spend=True)
    assert quiz["status"] == "ready"
    assert quiz["items"][0]["generator"] == "llm"
    assert verifier.calls == 1
    assert all(option["text"] in {"Tam giác", "Hình vuông", "Hình tròn"}
               for option in quiz["items"][0]["options"])
    private = store.get_record("quiz_attempt", quiz["attempt_id"])["_private"]
    item = next(iter(private.values()))
    assert {option["from"] for option in item["options"] if not option["is_correct"]} == {"moi"}
    assert {option["sources"][0] for option in item["options"] if not option["is_correct"]} == {"S1"}


def test_context_excludes_same_chunk_and_substring_overlapping_distractors():
    graph = Graph()
    graph.nodes["a"].update(name="Tập hợp", aliases=["tập"])
    graph.nodes["b"].update(name="Tập hợp con", aliases=[])
    graph.nodes["b"]["anchor"]["chunk_id"] = "cb"
    graph.nodes["c"]["anchor"]["chunk_id"] = "ca"
    usecase = QuizUseCase(graph, InMemoryPhaseBStore())
    concept = usecase._concepts("m", ["a"])[0]

    context = usecase._context("m", concept)

    assert all(row["name"] != "Tập hợp con" for row in context["distractor_candidates"])
    assert all(row["evidence_chunk_id"] != "ca" for row in context["distractor_candidates"])


def test_distractor_from_must_match_its_cited_source_family():
    usecase = QuizUseCase(Graph(), InMemoryPhaseBStore())
    concept = usecase._concepts("m", ["a"])[0]
    context = usecase._context("m", concept)
    good = {
        "concept": "Tam giác", "stem": "Một hình có ba cạnh là gì?",
        "correct": {"text": "Tam giác", "sources": ["S1"],
                    "quote": "Tam giác là hình phẳng có ba cạnh."},
        "distractors": [
            {"text": "Hình vuông", "from": "D1", "why_wrong": "Có bốn cạnh.",
             "sources": ["D1"], "quote": "Hình vuông là hình phẳng có bốn cạnh bằng nhau."},
            {"text": "Hình tròn", "from": "moi", "why_wrong": "Không có cạnh.",
             "sources": ["S1"], "quote": "Tam giác là hình phẳng có ba cạnh."},
        ], "explanation": "Định nghĩa nêu số cạnh.", "formula_refs": [],
    }
    assert usecase._normalize_item(concept, context, good)

    mismatch = deepcopy(good)
    mismatch["distractors"][0]["sources"] = ["S1"]
    mismatch["distractors"][0]["quote"] = "Tam giác là hình phẳng có ba cạnh."
    assert usecase._normalize_item(concept, context, mismatch) is None
    mismatch = deepcopy(good)
    mismatch["distractors"][1]["sources"] = ["D1"]
    mismatch["distractors"][1]["quote"] = "Hình vuông là hình phẳng có bốn cạnh bằng nhau."
    assert usecase._normalize_item(concept, context, mismatch) is None


def test_blind_verifier_is_told_to_route_options_to_distractor_anchor_evidence():
    usecase = QuizUseCase(Graph(), InMemoryPhaseBStore())
    concept = usecase._concepts("m", ["a"])[0]
    context = usecase._context("m", concept)
    prompt = usecase._verifier_prompt(context, [{
        "item_id": "q1", "stem": "Which concept is described?",
        "options": [{"option_id": "0", "text": "Tam giác"},
                    {"option_id": "1", "text": "Hình vuông"},
                    {"option_id": "2", "text": "Hình tròn"}],
    }])
    evidence = json.loads(prompt.split("\n", 1)[1])

    assert "bằng cả hai nhóm chứng cứ" in prompt
    assert "Không chỉ tìm tên option trong chunks" in prompt
    assert "Đối chiếu tên/alias" in prompt and "anchor của candidate đó" in prompt
    assert evidence["distractor_sources"][0]["label"] == "D1"
    assert evidence["distractor_sources"][0]["anchor"]
    assert all(set(option) == {"option_id", "text"} for option in evidence["items"][0]["options"])
    assert "is_correct" not in prompt and '"correct"' not in prompt

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


def _generated_candidate(usecase, concept, context):
    return usecase._normalize_item(concept, context, {
        "concept": "Tam giác", "stem": "Một hình phẳng có ba cạnh được gọi là gì?", "bloom": "hieu",
        "correct": {"text": "Tam giác", "sources": ["S1"],
                    "quote": "Tam giác là hình phẳng có ba cạnh."},
        "distractors": [
            {"text": "Hình vuông", "from": "D1", "why_wrong": "Có bốn cạnh.",
             "sources": ["D1"], "quote": "Hình vuông là hình phẳng có bốn cạnh bằng nhau."},
            {"text": "Hình tròn", "from": "D2", "why_wrong": "Không có cạnh.",
             "sources": ["D2"], "quote": "Hình tròn là tập hợp các điểm cách đều một tâm."},
        ], "explanation": "Nguồn định nghĩa khái niệm qua số cạnh.", "formula_refs": [],
    })


def test_q2_q3_q4_source_alias_and_anchor_guards_reject_bad_items():
    usecase = QuizUseCase(Graph(), InMemoryPhaseBStore())
    concept = usecase._concepts("m", ["a"])[0]
    context = usecase._context("m", concept)
    assert usecase._rules_pass(_generated_candidate(usecase, concept, context), context)
    assert {"hình tam giác", "tam giác"} <= set(usecase._aliases(concept))

    wrong_source = _generated_candidate(usecase, concept, context)
    wrong_source["evidence"] = [{"label": "S2", "quote": "Tam giác là hình phẳng có ba cạnh."}]
    assert not usecase._quote_for_label(wrong_source["evidence"][0]["quote"], "S2", context, correct=True)

    alias_as_distractor = _generated_candidate(usecase, concept, context)
    alias_as_distractor["options"][1]["text"] = "Hình tam giác"
    assert not usecase._rules_pass(alias_as_distractor, context)

    context["distractor_candidates"][0]["evidence_chunk_id"] = "ca"
    assert usecase._normalize_item(concept, context, {
        "stem": "Một hình phẳng có ba cạnh được gọi là gì?",
        "concept": "Tam giác",
        "correct": {"text": "Tam giác", "sources": ["S1"], "quote": "Tam giác là hình phẳng có ba cạnh."},
        "distractors": [{"text": "Hình vuông", "from": "D1", "why_wrong": "Có bốn cạnh.",
                         "sources": ["D1"], "quote": "Hình vuông là hình phẳng có bốn cạnh bằng nhau."},
                        {"text": "Hình tròn", "from": "D2", "why_wrong": "Không có cạnh.",
                         "sources": ["D2"], "quote": "Hình tròn là tập hợp các điểm cách đều một tâm."}],
    }) is None


def test_q5_q6_q7_and_q8_guards_have_reproducible_rejections():
    usecase = QuizUseCase(Graph(), InMemoryPhaseBStore())
    concept = usecase._concepts("m", ["a"])[0]
    context = usecase._context("m", concept)
    candidate = _generated_candidate(usecase, concept, context)

    answer_cue = deepcopy(candidate)
    answer_cue["options"][0]["text"] = "ba cạnh"
    assert not usecase._rules_pass(answer_cue, context)

    formula = deepcopy(candidate)
    formula["options"][0]["text"] = "x^2"
    assert not usecase._rules_pass(formula, context)

    english = deepcopy(candidate)
    english["stem"] = "Which phrase describes this geometric object?"
    assert not usecase._rules_pass(english, context)

    duplicate = deepcopy(candidate)
    assert usecase._duplicate(candidate, duplicate)


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


def test_quiz_schema_is_sent_as_json_schema_in_fake_http_request():
    model = GeminiToolModel("test-key")
    captured = {}

    class Response:
        def __init__(self):
            import io
            self.body = io.BytesIO(json.dumps({"candidates": [{"content": {"parts": [{"text": "{\"items\":[],\"gaps\":[]}"}]}}]}).encode())

        def read(self, size=-1):
            return self.body.read(size)

        def close(self):
            pass

    def fake_http(operation, body, *, stream):
        assert operation == "generateContent" and stream is False
        captured.update(body)
        return Response()

    model._request = fake_http
    reply = model.ask_json("prompt", response_schema=QUIZ_SCHEMA)

    schema = captured["generationConfig"]["responseJsonSchema"]
    assert reply.payload == {"items": [], "gaps": []}
    assert schema["type"] == "object"
    assert schema["properties"]["items"]["items"]["properties"]["correct"]["required"] == ["text", "sources", "quote"]


def test_runtime_gives_verifier_its_400_token_budget():
    runtime = PhaseBRuntime(settings=Settings(artifact_dir=Path("artifacts"),
                                               gemini_api_key=SecretStr("fake-key")), mode="gemini")
    usecase = runtime.quiz(Graph())

    assert usecase.model.max_output_tokens == 1200
    assert usecase.verifier_model.max_output_tokens == 400
    assert usecase.model is not usecase.verifier_model
