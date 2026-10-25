from __future__ import annotations

from types import MethodType

from doc2roadmap.application.phase_b.assistant import AssistantUseCase
from doc2roadmap.application.phase_b.quiz import QuizUseCase
from doc2roadmap.application.ports.phase_b import Done, ToolCall
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore
from test_phase_b_b2_artifacts import RoadmapGraph
from test_phase_b_quiz import Graph


def _bank(self, _doc_id, _module_id, concept, _allow_spend, _level, *, owner=None):
    node_id = concept["node_id"]
    return [{"item_id": f"q-{node_id}", "concept_id": node_id,
             "stem": f"Câu riêng cho {node_id}", "options": [
                 {"option_id": "a", "text": f"Đúng {node_id}", "is_correct": True},
                 {"option_id": "b", "text": f"Sai B {node_id}", "is_correct": False},
                 {"option_id": "c", "text": f"Sai C {node_id}", "is_correct": False}],
             "evidence": [], "explanation": "ẩn", "checks": {}}], {}


def test_roadmap_string_and_object_share_seeded_learned_round_robin_sample():
    graph = RoadmapGraph(module_count=6, nodes_per_module=3)

    class Progress:
        def get_progress(self, owner, doc_id):
            assert (owner, doc_id) == ("alice", "dev")
            return {"nodes": {
                "n0_0": {"state": "learned"},
                "n2_0": {"state": "learned"},
            }}

    usecase = QuizUseCase(graph, InMemoryPhaseBStore(), settings=BSettings(),
                          progress_use_case=Progress())
    usecase._bank = MethodType(_bank, usecase)

    canonical = usecase.make_quiz("dev", owner="alice", scope={"kind": "roadmap"}, seed="same")
    tool_form = usecase.make_quiz("dev", owner="alice", scope="roadmap", seed="same")

    assert set(tool_form["node_ids"]) == set(canonical["node_ids"])
    assert {"n0_0", "n2_0"} <= set(tool_form["node_ids"])
    assert tool_form["seed"] == "same"
    counts = {}
    for node_id in tool_form["node_ids"]:
        if node_id in {"n0_0", "n2_0"}:
            continue
        module_id = graph.nodes[node_id]["module_id"]
        counts[module_id] = counts.get(module_id, 0) + 1
    assert max(counts.values()) - min(counts.values()) <= 1


def test_assistant_make_quiz_roadmap_obeys_configured_cap_and_keeps_answer_private():
    graph = RoadmapGraph(module_count=6, nodes_per_module=3)
    graph.tree = None
    store = InMemoryPhaseBStore()

    class Progress:
        def get_progress(self, owner, doc_id):
            return {"nodes": {"n0_0": {"state": "learned"},
                              "n2_0": {"state": "learned"}}}

    quiz = QuizUseCase(graph, store, settings=BSettings(quiz_roadmap_max_items=3),
                       progress_use_case=Progress())
    quiz._bank = MethodType(_bank, quiz)

    class Model:
        model_id = "scripted-assistant"

        def start_session(self, _system_prompt, _tools):
            return self

        def stream(self, _messages, *, mode):
            if mode == "AUTO":
                yield ToolCall("make_quiz", {"scope": "roadmap", "n": 10}, "quiz")
                yield Done({})
            else:
                yield Done({})

    def make_quiz(scope, n=None, level=None, *, owner, **kwargs):
        return quiz.make_quiz(graph.doc_id, owner=owner, scope=scope, n=n, level=level,
                              origin="assistant", home_scope=kwargs.get("home_scope"),
                              session_id=kwargs.get("session_id"))

    assistant = AssistantUseCase(graph, store, Model(), quiz=make_quiz)
    session = assistant.sessions.create_session("alice", "dev", {"kind": "roadmap"})
    result = assistant.ask("dev", 1, session["session_id"], "Kiểm tra tôi.",
                           owner="alice", allow_spend=True)

    summary = result["tool_calls"][0]["result_summary"]
    attempt = store.get_record("quiz_attempt", summary["artifact"]["id"])
    assert summary["count"] <= 3
    assert {"n0_0", "n2_0"} <= set(attempt["node_ids"])
    assert attempt["origin"] == "assistant" and attempt["home_scope"] == {"kind": "roadmap"}
    assert attempt["seed"]
    assert "items" not in repr(summary) and "is_correct" not in repr(summary)


def test_roadmap_returns_one_item_per_ready_sampled_concept_without_variant_fill():
    graph = RoadmapGraph(module_count=6, nodes_per_module=3)
    quiz = QuizUseCase(graph, InMemoryPhaseBStore(), settings=BSettings())
    sampled = quiz._roadmap_sample(quiz._concepts(None, None), "alice", "dev", 10, "banks")
    ready_ids = {concept["node_id"] for concept in sampled[:4]}

    def bank(self, _doc_id, _module_id, concept, _allow_spend, _level, *, owner=None):
        if concept["node_id"] not in ready_ids:
            return [], {}
        variants = []
        for variant in ("alpha", "beta"):
            variants.append({
                "item_id": f"q-{concept['node_id']}-{variant}",
                "concept_id": concept["node_id"],
                "module_id": concept["module_id"],
                "stem": f"Distinct {variant} question statement for {concept['node_id']}.",
                "options": [
                    {"option_id": "a", "text": f"Correct {concept['node_id']}", "is_correct": True},
                    {"option_id": "b", "text": f"Wrong B {concept['node_id']}", "is_correct": False},
                    {"option_id": "c", "text": f"Wrong C {concept['node_id']}", "is_correct": False},
                ],
                "evidence": [], "explanation": "private", "checks": {},
            })
        return variants, {}

    quiz._bank = MethodType(bank, quiz)
    attempt = quiz.make_quiz("dev", owner="alice", scope="roadmap", n=10, seed="banks")

    assert attempt["total_concepts"] == 10
    assert len(attempt["items"]) == 4
    assert len(attempt["node_ids"]) == len(attempt["items"])
    assert set(attempt["node_ids"]) == ready_ids


def test_cloze_keeps_complete_definition_and_public_quiz_has_no_answers():
    graph = Graph()
    store = InMemoryPhaseBStore()
    quiz = QuizUseCase(graph, store)

    result = quiz.make_quiz("d", "m", "alice", node_ids=["a"])

    assert result["ready_count"] == 1
    assert result["items"][0]["generator"] == "cloze"
    assert "___" in result["items"][0]["stem"]
    assert all("is_correct" not in option for item in result["items"] for option in item["options"])
    assert "explanation" not in repr(result) and "correct_option" not in repr(result)


def test_cloze_rejection_codes_and_coverage_are_recorded():
    cases = [
        ("Tam giác được xác định bởi biểu thức [formula] sau đây.",
         "local.visual_or_formula_reference"),
        ("Tam giác là hình phẳng được xác định bởi ba điều kiện sau đây:",
         "cloze.incomplete_lead_in"),
        ("Tích trực tiếp (hay tích Descartes) của hai tập hợp X và Y là tập hợp sau đây:",
         "cloze.incomplete_lead_in"),
        ("Tam giác được minh họa ở Hình 2 dưới đây.",
         "local.visual_or_formula_reference"),
    ]
    for quote, reason in cases:
        graph = Graph()
        if quote.startswith("Tích trực tiếp"):
            graph.nodes["a"]["name"] = "Tích trực tiếp"
        graph.chunks["ca"].text = quote
        graph.nodes["a"]["anchor"]["sentence"] = quote
        quiz = QuizUseCase(graph, InMemoryPhaseBStore())

        result = quiz.make_quiz("d", "m", "alice", node_ids=["a"])

        assert result["status"] == "failed" and result["failed_concepts"] == ["a"]
        assert any(row["stage"] == "cloze" and row["reason"] == reason
                   for row in quiz.diagnostics), (quote, quiz.diagnostics)


def test_cloze_skips_substring_overlapping_alias_and_uses_safe_distractors():
    graph = Graph()
    graph.nodes["b"]["name"] = "Hình tam giác đều"
    graph.nodes["d"] = {"node_id": "d", "name": "Tứ giác", "module_id": "m"}
    graph.modules["m"]["node_ids"].append("d")

    result = QuizUseCase(graph, InMemoryPhaseBStore()).make_quiz("d", "m", "alice", node_ids=["a"])

    assert result["items"]
    texts = [option["text"].casefold() for option in result["items"][0]["options"]]
    assert all(left not in right and right not in left
               for index, left in enumerate(texts) for right in texts[index + 1:])


def test_generic_chart_word_does_not_reject_cloze_by_itself():
    text = "Đồ thị là một biểu diễn của quan hệ trên tập hợp."

    assert not QuizUseCase._cloze_visual_or_formula_reference(text)


def test_new_local_rule_version_invalidates_cached_cloze_bank(monkeypatch):
    graph = Graph()
    store = InMemoryPhaseBStore()
    quiz = QuizUseCase(graph, store)
    concept = quiz._concepts("m", ["a"])[0]
    monkeypatch.setattr(QuizUseCase, "LOCAL_RULES_VERSION", "quiz-local-rules-v2", raising=False)
    old_key = quiz._bank_key("d", "m", concept, None)
    legacy = [{"item_id": "legacy-invalid", "concept_id": "a", "generator": "llm",
               "stem": "old invalid bank", "options": [], "checks": {}}]
    store.put_cache(old_key, legacy)

    monkeypatch.setattr(QuizUseCase, "LOCAL_RULES_VERSION", "quiz-local-rules-v3", raising=False)
    bank, _ = quiz._bank("d", "m", concept, False, None)

    assert bank and bank != legacy
    assert all(item["generator"] == "cloze" for item in bank)

