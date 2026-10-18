from __future__ import annotations

import json
from types import SimpleNamespace

from doc2roadmap.application.phase_b.quiz import QuizUseCase
from doc2roadmap.domain import phase_b_pricing
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore


class EmptyGraph:
    payload = {"doc_id": "d"}
    nodes = {}
    modules = {}
    chunks = {}


class CapturedModel:
    model_id = "gemini-3.1-flash-lite"

    def __init__(self):
        self.calls = []
        self.generation_calls = 0

    def ask_json(self, prompt, *, response_schema, system_prompt=""):
        self.calls.append((prompt, response_schema))
        if "distractor_verdicts" not in str(response_schema):
            self.generation_calls += 1
            if self.generation_calls > 1:
                return SimpleNamespace(payload={"items": []}, usage={}, elapsed_ms=1,
                                       ttft_ms=1, cost_usd=0.0)
            return SimpleNamespace(payload={"items": [{
                "concept": "Tam giác", "bloom": "hieu",
                "stem": "Mô tả nào phù hợp theo nội dung?",
                "correct": {"text": "Hình phẳng có ba cạnh", "sources": ["S1"],
                            "quote": "Tam giác là hình phẳng có ba cạnh."},
                "distractors": [
                    {"text": "Hình phẳng có bốn cạnh", "from": "D1", "why_wrong": "Mô tả này có bốn cạnh.",
                     "sources": ["D1"], "quote": "Hình vuông là hình phẳng có bốn cạnh."},
                    {"text": "Tập hợp điểm cách đều tâm", "from": "D2", "why_wrong": "Đây là mô tả khác.",
                     "sources": ["D2"], "quote": "Hình tròn là tập hợp điểm cách đều tâm."},
                ],
                "explanation": "Tài liệu mô tả hình phẳng có ba cạnh.", "formula_refs": [],
            }]}, usage={}, elapsed_ms=1, ttft_ms=1, cost_usd=0.0)

        context = json.loads(prompt.split("\n", 1)[1])
        label = context["items"][0]
        wrong_id = next(row["option_id"] for row in label["options"]
                        if row["text"] != "Hình phẳng có ba cạnh")
        distractor_ids = [row["option_id"] for row in label["options"]
                          if row["text"] != "Hình phẳng có ba cạnh"]
        return SimpleNamespace(payload={"items": [{
            "item_id": label["item_id"], "selected_option_id": wrong_id,
            "valid": True, "quote": "Tam giác là hình phẳng có ba cạnh.",
            "distractor_verdicts": [{"option_id": option_id, "verdict": "sai theo nguồn"}
                                    for option_id in distractor_ids],
        }]}, usage={}, elapsed_ms=1, ttft_ms=1, cost_usd=0.0)


def test_wrong_verifier_choice_rejects_candidate_even_with_complete_distractor_verdicts():
    model = CapturedModel()
    usecase = QuizUseCase(EmptyGraph(), InMemoryPhaseBStore(), model)
    concept = {"node_id": "n1", "name": "Tam giác", "module_id": "m"}
    context = {
        "module": {"module_id": "m"}, "concept": concept,
        "target_blooms": ["hieu", "van_dung"],
        "chunks": [{"label": "S1", "chunk_id": "s1", "text": "Tam giác là hình phẳng có ba cạnh."}],
        "distractor_candidates": [
            {"label": "D1", "evidence_chunk_id": "d1", "anchor": "Hình vuông là hình phẳng có bốn cạnh."},
            {"label": "D2", "evidence_chunk_id": "d2", "anchor": "Hình tròn là tập hợp điểm cách đều tâm."},
        ], "prerequisites": [], "exercises": [], "limits": {
            "generation_output_tokens": 1200, "verifier_output_tokens": 400,
            "why_wrong_chars": 150, "explanation_chars": 300, "bank_variants": 2},
    }
    generated = {}

    bank = usecase._generate_bank(concept, context, generated, "d")

    assert bank == []
    assert [row["reason"] for row in usecase.diagnostics] == ["verifier.wrong_choice"]
    assert len(model.calls) == 3
    assert model.generation_calls == 2


def test_target_name_in_stem_is_allowed_when_correct_answer_is_not_the_concept_name():
    usecase = QuizUseCase(EmptyGraph(), InMemoryPhaseBStore())
    context = {"concept": {"node_id": "n1", "name": "Tam giác", "aliases": []},
               "chunks": [{"text": "Tam giác có ba cạnh."}]}
    item = {"stem": "Trong tài liệu, Tam giác được dùng để mô tả gì?", "explanation": "",
            "options": [
                {"text": "Hình phẳng có ba cạnh", "is_correct": True, "why_wrong": ""},
                {"text": "Hình phẳng có bốn cạnh", "is_correct": False, "why_wrong": ""},
                {"text": "Tập hợp điểm cách đều tâm", "is_correct": False, "why_wrong": ""},
            ]}

    passed, reason = usecase._rules_pass_with_reason(item, context)

    assert passed is True
    assert reason is None


def test_target_name_still_rejects_when_it_is_the_correct_answer():
    usecase = QuizUseCase(EmptyGraph(), InMemoryPhaseBStore())
    context = {"concept": {"node_id": "n1", "name": "Tam giác", "aliases": []},
               "chunks": [{"text": "Tam giác có ba cạnh."}]}
    item = {"stem": "Trong tài liệu, Tam giác được dùng để mô tả gì?", "explanation": "",
            "options": [
                {"text": "Tam giác", "is_correct": True, "why_wrong": ""},
                {"text": "Hình vuông", "is_correct": False, "why_wrong": ""},
                {"text": "Hình tròn", "is_correct": False, "why_wrong": ""},
            ]}

    passed, reason = usecase._rules_pass_with_reason(item, context)

    assert passed is False
    assert reason == "local.target_name_in_stem"


def test_dry_run_quiz_cost_uses_shared_price_table_and_separate_model_ids(monkeypatch):
    class Model:
        def __init__(self, model_id):
            self.model_id = model_id

    monkeypatch.setitem(phase_b_pricing.PRICES_USD_PER_MILLION,
                        "generator-test", {"input": 2.0, "output": 4.0})
    monkeypatch.setitem(phase_b_pricing.PRICES_USD_PER_MILLION,
                        "verifier-test", {"input": 3.0, "output": 5.0})
    usecase = QuizUseCase(EmptyGraph(), InMemoryPhaseBStore(), Model("generator-test"),
                          verifier_model=Model("verifier-test"),
                          settings=BSettings(quiz_generation_max_output_tokens=50,
                                             quiz_verifier_max_output_tokens=20))
    usecase._concepts = lambda module_id, requested: [
        {"node_id": "n1", "name": "Tam giác", "module_id": "m"}]
    usecase._context = lambda module_id, concept, level=None: {
        "module": {"module_id": "m"}, "concept": concept, "target_blooms": ["hieu", "hieu"],
        "chunks": [{"label": "S1", "chunk_id": "s1", "text": "Tam giác là hình phẳng có ba cạnh."}],
        "distractor_candidates": [], "prerequisites": [], "exercises": [], "limits": {
            "generation_output_tokens": 50, "verifier_output_tokens": 20,
            "explanation_chars": 300, "why_wrong_chars": 150, "bank_variants": 2}}
    usecase._bank_key = lambda *args, **kwargs: "uncached"

    result = usecase.make_quiz("d", "m", "alice", dry_run=True)
    gen_input, gen_output, verify_input, verify_output = usecase._bank_estimate_token_breakdown(
        usecase._context("m", {"node_id": "n1", "name": "Tam giác", "module_id": "m"}))
    expected = (phase_b_pricing.estimate_cost("generator-test", gen_input, gen_output)
                + phase_b_pricing.estimate_cost("verifier-test", verify_input, verify_output))

    assert result["estimated_usd"] == round(expected, 6)
    assert result["estimated_calls"] == 4
