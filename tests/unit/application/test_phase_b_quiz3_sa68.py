"""SA-68: `quiz-3`. Three four-option questions per concept, kept when a blind solver (thinking on) answers them the same way.

Every model is a script; nothing is paid. The ten invariants of doc/quiz-3-spec.md ("Quyết định kiểm thử") are the first ten tests.
"""
from __future__ import annotations

import base64
import io
import json
import re
from dataclasses import replace
from pathlib import Path

import pytest
from pydantic import SecretStr

from doc2roadmap.application.phase_b.lecture3 import FORMULA_RULE_TEXT_ONLY, FORMULA_RULE_WITH_IMAGES
from doc2roadmap.application.phase_b.quiz import QuizUseCase
from doc2roadmap.application.phase_b.quiz_context3 import SYSTEM_GENERATION, SYSTEM_SOLVER
from doc2roadmap.composition_phase_b import PhaseBRuntime
from doc2roadmap.config import Settings
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore
from doc2roadmap.infrastructure.llm.phase_b import GeminiToolModel

from sa64_support import FakeClock, FakePages
from sa68_support import (
    EXPLANATION, MARKER, SOLVER_REASON, WHY_WRONG, Generator, Reverse, Solver, make_book, raw_item,
)

SPEC = Path(__file__).resolve().parents[3] / "doc" / "quiz-3-spec.md"
ALL_PAGES = FakePages({page: b"jpeg-" + str(page).encode() for page in range(1, 40)})


def three_ok(concept, lap):
    return [raw_item(f"{concept} lượt {lap} câu {k}", correct=k, bloom=bloom)
            for k, bloom in enumerate(("nho", "hieu", "van_dung"))]


def build(*, script=three_ok, mode=lambda stem: "right", graph=None, settings=None, store=None, pages=ALL_PAGES,
          rng=None, delay=0.0):
    generator = Generator(script, delay=delay)
    solver = Solver(generator, mode)
    store = store if store is not None else InMemoryPhaseBStore()
    use = QuizUseCase(graph or make_book(), store, generator, verifier_model=solver, settings=settings or BSettings(),
                      rng=rng or Reverse(), page_images=pages, clock=FakeClock())
    return use, generator, solver, store


def bank_of(use, node_id="n1", allow_spend=True):
    concept = use._concepts("m", [node_id])[0]
    return use._bank("d", "m", concept, allow_spend, None)[0]


def rejections(store):
    return store.list_records("quiz_rejection")


# --- 1. the solver sees shuffled options and nothing about the answer ------------------------------------------

def test_solver_gets_the_options_shuffled_and_no_answer_explanation_or_why_wrong():
    use, generator, solver, _ = build()
    bank = bank_of(use)
    call = solver.calls[0]
    shown = json.loads(call.prompt.split(MARKER, 1)[1])
    assert [set(row) for row in shown] == [{"q", "stem", "options"}] * 3
    for row in shown:
        original = [f"{row['stem']} / phương án {k}" for k in range(4)]
        assert row["options"] == original[::-1]           # the Reverse rng reversed them: not the generator's order
        assert all(isinstance(text, str) for text in row["options"])
    for secret in (EXPLANATION, WHY_WRONG, "is_correct", "correct_index", "explanation", "why_wrong"):
        assert secret not in call.prompt and secret not in call.system
    assert call.system == SYSTEM_SOLVER
    assert len(bank) == 3                                  # and the answer is mapped back through the shuffle


# --- 2. only questions the solver answers the same way, and not ambiguous, are kept -----------------------------

def test_a_question_is_kept_only_when_the_solver_agrees_and_finds_no_second_answer():
    modes = {"Khái niệm 1 lượt 0 câu 0": "right", "Khái niệm 1 lượt 0 câu 1": "wrong",
             "Khái niệm 1 lượt 0 câu 2": "ambiguous"}
    use, _, _, store = build(script=lambda c, lap: three_ok(c, lap) if lap == 0 else [], mode=lambda s: modes[s])
    bank = bank_of(use)
    assert [item["stem"] for item in bank] == ["Khái niệm 1 lượt 0 câu 0"]
    rows = {row["stem"]: row for row in rejections(store)}
    assert set(rows) == {"Khái niệm 1 lượt 0 câu 1", "Khái niệm 1 lượt 0 câu 2"}
    assert rows["Khái niệm 1 lượt 0 câu 1"]["reason"] == "solver.wrong_choice"
    assert rows["Khái niệm 1 lượt 0 câu 2"]["reason"] == "solver.ambiguous"
    for row in rows.values():
        assert (row["concept_id"], row["concept_name"], row["lap"], row["stage"]) == ("n1", "Khái niệm 1", 1, "solver")
        assert row["solver_reason"] == SOLVER_REASON and row["doc_id"] == "d"


@pytest.mark.parametrize("mode,reason", [("missing", "solver.missing_answer"), ("badchoice", "solver.invalid_choice")])
def test_a_question_the_solver_did_not_answer_or_answered_out_of_range_is_dropped_and_logged(mode, reason):
    use, _, _, store = build(script=lambda c, lap: three_ok(c, lap) if lap == 0 else [],
                             mode=lambda s: "right" if s.endswith("câu 0") else mode)
    assert [item["stem"] for item in bank_of(use)] == ["Khái niệm 1 lượt 0 câu 0"]
    assert [row["reason"] for row in rejections(store)] == [reason, reason]


def _bad(**change):
    item = raw_item("Câu hỏng")
    item.update(change)
    return item


@pytest.mark.parametrize("bad,reason", [
    (_bad(options=raw_item("x")["options"][:3]), "local.option_count"),
    (_bad(options=[*raw_item("x")["options"][:3], {"text": "  ", "why_wrong": ""}]), "local.option_count"),
    (_bad(options=[{"text": t, "why_wrong": ""} for t in ("A", "a ", "B", "C")]), "local.duplicate_options"),
    (_bad(correct_index=4), "local.correct_index"),
    (_bad(correct_index=-1), "local.correct_index"),
    (_bad(correct_index=True), "local.correct_index"),
    (_bad(stem="   "), "local.empty_stem"),
])
def test_a_malformed_question_is_logged_and_never_reaches_the_solver(bad, reason):
    use, generator, solver, store = build(script=lambda c, lap: [bad, *three_ok(c, lap)[:2]] if lap == 0 else [])
    bank = bank_of(use)
    assert len(bank) == 2
    assert [(row["reason"], row["stage"], row["lap"]) for row in rejections(store)] == [(reason, "local", 1)]
    assert "Câu hỏng" not in solver.calls[0].prompt


# --- 3. the solver thinks at `medium` and temperature 0; the generator does not think ---------------------------

def test_solver_call_has_medium_thinking_and_temperature_zero_and_generator_call_has_no_thinking():
    use, generator, solver, _ = build()
    bank_of(use)
    assert (solver.calls[0].thinking_level, solver.calls[0].temperature) == ("medium", 0.0)
    assert (generator.calls[0].thinking_level, generator.calls[0].temperature) == (None, 1.0)


def test_the_requests_on_the_wire_carry_thinkingConfig_only_for_the_solver_and_both_carry_the_pages():
    generator = Generator(three_ok)
    solver = Solver(generator)
    bodies = []

    def client(kind):
        model = GeminiToolModel("key", max_output_tokens=4096 if kind == "gen" else 8192)

        def request(operation, body, *, stream, retries=2, timeout_seconds=None):
            bodies.append((kind, operation, stream, body))
            schema = body["generationConfig"]["responseJsonSchema"]
            scripted = generator if "items" in schema["properties"] else solver
            payload = scripted.reply(type("Call", (), {"prompt": body["contents"][0]["parts"][0]["text"]})())
            text = json.dumps(payload, ensure_ascii=False)
            return io.BytesIO(json.dumps({"candidates": [{"content": {"parts": [{"text": text}]}}],
                                          "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 5}}).encode())
        model._request = request
        return model

    use = QuizUseCase(make_book(), InMemoryPhaseBStore(), client("gen"), verifier_model=client("sol"),
                      settings=BSettings(), rng=Reverse(), page_images=ALL_PAGES, clock=FakeClock())
    concept = use._concepts("m", ["nf"])[0]
    assert len(use._bank("d", "m", concept, True, None)[0]) == 3
    (_, _, _, gen), (_, _, _, sol) = bodies[0], bodies[1]
    assert "thinkingConfig" not in gen["generationConfig"] and gen["generationConfig"]["temperature"] == 1.0
    assert gen["generationConfig"]["maxOutputTokens"] == 4096
    assert sol["generationConfig"]["thinkingConfig"] == {"thinkingLevel": "medium"}
    assert sol["generationConfig"]["temperature"] == 0.0 and sol["generationConfig"]["maxOutputTokens"] == 8192
    for body in (gen, sol):
        parts = body["contents"][0]["parts"]
        pictures = [base64.b64decode(part["inlineData"]["data"]) for part in parts if "inlineData" in part]
        assert pictures == [b"jpeg-7", b"jpeg-9"]
    assert gen["systemInstruction"]["parts"][0]["text"] == SYSTEM_GENERATION.replace("{formula_rule}", FORMULA_RULE_WITH_IMAGES)
    assert sol["systemInstruction"]["parts"][0]["text"] == SYSTEM_SOLVER


# --- 4. formulas in the question and the options are kept; the quiz-2 rules are gone ------------------------------

def test_latex_in_stem_and_options_is_kept_and_the_old_rules_no_longer_reject():
    stem = "Với $r = \\frac{s_{xy}}{s_x s_y}$ và $s_{xy} = 2$, giá trị nào của $r$ đúng khi $s_x s_y = 4$?"
    long_right = "Giá trị $r = 0{,}5$, vì $\\frac{2}{4} = 0{,}5$ nằm trong đoạn $[-1, 1]$ và cho thấy hai dấu hiệu tương quan thuận, tuyến tính yếu"
    texts = [long_right, "$r = 2$", "$r = [formula]$", "$r = -\\frac{1}{2}$"]
    use, _, _, _ = build(script=lambda c, lap: [raw_item(stem, texts=texts, bloom="van_dung"),
                                                raw_item(stem + " (b)", texts=texts, bloom="hieu")])
    bank = bank_of(use)
    assert [item["stem"] for item in bank] == [stem, stem + " (b)"]
    assert [option["text"] for option in bank[0]["options"]] == texts
    quiz = use.make_quiz("d", "m", "alice", node_ids=["n1"], allow_spend=True)
    assert quiz["items"][0]["stem"] in {stem, stem + " (b)"}
    assert "$r = [formula]$" in {o["text"] for o in quiz["items"][0]["options"]}


# --- 5. fewer than two kept: one more lap, once ----------------------------------------------------------------

def test_one_kept_question_makes_exactly_one_more_lap_and_the_bank_keeps_three():
    use, generator, solver, _ = build(mode=lambda s: "right" if "lượt 1" in s or s.endswith("lượt 0 câu 0") else "wrong")
    bank = bank_of(use)
    assert (len(generator.calls), len(solver.calls)) == (2, 2)
    assert [item["stem"] for item in bank] == ["Khái niệm 1 lượt 0 câu 0", "Khái niệm 1 lượt 1 câu 0",
                                               "Khái niệm 1 lượt 1 câu 1"]


def test_two_laps_at_most_even_when_nothing_is_kept_and_the_empty_result_is_stored():
    use, generator, solver, store = build(mode=lambda s: "wrong")
    assert len(rejections(store)) == 0
    assert bank_of(use) != []                                # nothing kept: the learner still gets a cloze question
    assert (len(generator.calls), len(solver.calls)) == (2, 2)
    assert len(rejections(store)) == 6
    bank_of(use)
    assert (len(generator.calls), len(solver.calls)) == (2, 2)   # the empty bank is the bank: no third lap, no fourth


def test_two_kept_in_the_first_lap_make_no_second_lap():
    use, generator, _, _ = build(mode=lambda s: "wrong" if s.endswith("câu 2") else "right")
    assert len(bank_of(use)) == 2 and len(generator.calls) == 1


def test_a_lap_that_fails_after_the_first_kept_one_still_stores_that_one():
    def script(concept, lap):
        if lap == 1:
            raise RuntimeError("network")
        return three_ok(concept, lap)
    use, generator, _, store = build(script=script, mode=lambda s: "right" if s.endswith("câu 0") else "wrong")
    assert [item["stem"] for item in bank_of(use)] == ["Khái niệm 1 lượt 0 câu 0"]
    assert len(generator.calls) == 2
    assert bank_of(use)[0]["generator"] == "llm" and len(generator.calls) == 2   # stored: not asked again


# --- 6. the bank is shared and versioned ------------------------------------------------------------------------

def test_a_second_quiz_of_the_same_concept_makes_no_model_call():
    use, generator, solver, store = build()
    use.make_quiz("d", "m", "alice", node_ids=["n1"], allow_spend=True)
    calls = (len(generator.calls), len(solver.calls))
    assert calls == (1, 1)
    again = QuizUseCase(make_book(), store, generator, verifier_model=solver, settings=BSettings(), clock=FakeClock())
    quiz = again.make_quiz("d", "m", "bob", node_ids=["n1"], allow_spend=True)
    assert quiz["items"][0]["generator"] == "llm"
    assert (len(generator.calls), len(solver.calls)) == calls


@pytest.mark.parametrize("change", [{"quiz_generation_prompt_version": "quiz-gen-6"},
                                    {"quiz_verifier_prompt_version": "quiz-verify-6"},
                                    {"quiz_verifier_thinking_level": "high"}])
def test_a_new_prompt_version_or_thinking_level_asks_again(change):
    use, generator, solver, store = build()
    bank_of(use)
    newer = QuizUseCase(make_book(), store, generator, verifier_model=solver, settings=replace(BSettings(), **change),
                        clock=FakeClock())
    bank_of(newer)
    assert len(generator.calls) == 2


def test_other_book_text_or_other_model_asks_again():
    use, generator, solver, store = build()
    bank_of(use)
    edited = make_book()
    edited.chunks["c0"].text += " Một câu mới được thêm vào sách."
    bank_of(QuizUseCase(edited, store, generator, verifier_model=solver, settings=BSettings(), clock=FakeClock()))
    other = Generator(three_ok, model_id="another-model")
    bank_of(QuizUseCase(make_book(), store, other, verifier_model=Solver(other), settings=BSettings(), clock=FakeClock()))
    assert len(generator.calls) == 2 and len(other.calls) == 1


def test_the_cloze_question_is_never_stored_so_it_cannot_hide_the_model_later():
    use, generator, _, store = build()
    first = use.make_quiz("d", "m", "alice", node_ids=["n1"], allow_spend=False)
    assert first["items"][0]["generator"] == "cloze" and generator.calls == []
    second = use.make_quiz("d", "m", "alice", node_ids=["n1"], allow_spend=True)
    assert second["items"][0]["generator"] == "llm"


# --- 7. cap reached: the stored bank, then the cloze question ---------------------------------------------------

def test_cap_reached_serves_the_stored_bank_then_cloze_without_maths():
    store = InMemoryPhaseBStore()
    use, generator, solver, _ = build(store=store)
    assert use.make_quiz("d", "m", "alice", node_ids=["n1"], allow_spend=True)["items"][0]["generator"] == "llm"
    calls = len(generator.calls)

    capped = QuizUseCase(make_book(), store, generator, verifier_model=solver,
                         settings=BSettings(system_daily_max_usd=0.0), clock=FakeClock(), rng=Reverse())
    quiz = capped.make_quiz("d", "m", "bob", node_ids=["n1", "n2", "nf"], allow_spend=True)
    by_concept = {item["concept_id"]: item["generator"] for item in quiz["items"]}
    assert by_concept == {"n1": "llm", "n2": "cloze"}          # n1 from the stored bank, n2 cloze
    assert quiz["failed_concepts"] == ["nf"]                   # its only sentences hold a formula: no cloze question
    assert len(generator.calls) == calls


def test_cloze_drops_a_sentence_with_maths_or_a_formula_mark():
    graph = make_book()
    graph.chunks["c0"].text = "Khái niệm 1 là biểu thức y = 2x trong sách học của sinh viên."
    graph.nodes["n1"]["anchor"]["sentence"] = graph.chunks["c0"].text
    graph.chunks["c1"].text = "Khái niệm 2 là đối tượng dùng [formula] trong sách học của sinh viên."
    graph.nodes["n2"]["anchor"]["sentence"] = graph.chunks["c1"].text
    graph.chunks["c2"].text = "Khái niệm 3 là đại lượng 2x đã nêu trong sách học của sinh viên."
    graph.nodes["n3"]["anchor"]["sentence"] = graph.chunks["c2"].text
    use = QuizUseCase(graph, InMemoryPhaseBStore(), clock=FakeClock())
    quiz = use.make_quiz("d", "m", "alice", node_ids=["n1", "n2", "n3", "n4"])
    assert {item["concept_id"] for item in quiz["items"]} == {"n4"}
    reasons = {row["reason"] for row in use.diagnostics if row["stage"] == "cloze"}
    assert "cloze.math_notation" in reasons


# --- 8. the result of a submission ------------------------------------------------------------------------------

def test_submit_gives_why_wrong_of_the_chosen_option_and_evidence_by_source_labels_and_never_the_solvers_reason():
    graph = make_book()
    script = lambda c, lap: [raw_item(f"{c} câu {k}", correct=k, labels=("S1",) if k < 2 else ("S9",)) for k in range(3)]
    use, _, _, store = build(script=script, graph=graph, mode=lambda s: "wrong" if s.endswith("câu 2") else "right")
    quiz = use.make_quiz("d", "m", "alice", node_ids=["nf"], allow_spend=True, seed="s")
    item = quiz["items"][0]
    private = store.get_record("quiz_attempt", quiz["attempt_id"])["_private"][item["item_id"]]
    wrong = next(option for option in private["options"] if not option["is_correct"])
    correct = next(option for option in private["options"] if option["is_correct"])
    result = use.submit(quiz["attempt_id"], "alice", {item["item_id"]: wrong["option_id"]})
    row = result["results"][0]
    assert result["contract_version"] == "quiz-3" and row["is_correct"] is False
    assert row["why_wrong"] == wrong["why_wrong"] and WHY_WRONG in row["why_wrong"]
    assert row["correct_option"]["text"] == correct["text"] and row["explanation"].startswith(EXPLANATION)
    first = next(chunk for chunk in graph.chunks.values() if chunk.page == 7)
    assert row["evidence"] == [{"label": "S1", "chunk_id": first.chunk_id, "page": 7}]
    for everything in (quiz, result, use.get_attempt(quiz["attempt_id"], "alice"), use.history("alice"),
                       store.get_record("quiz_attempt", quiz["attempt_id"])):
        assert SOLVER_REASON not in json.dumps(everything, ensure_ascii=False, default=str)
    assert all(SOLVER_REASON in r["solver_reason"] for r in rejections(store))


def test_an_unknown_source_label_gives_no_evidence_and_the_public_question_has_four_options_and_no_answer():
    use, _, _, _ = build(script=lambda c, lap: [raw_item(f"{c} câu {k}", labels=("S9", "S1", "S1")) for k in range(3)])
    quiz = use.make_quiz("d", "m", "alice", node_ids=["n1"], allow_spend=True)
    item = quiz["items"][0]
    assert set(item) == {"item_id", "concept_id", "module_id", "generator", "bloom", "stem", "options"}
    assert len(item["options"]) == 4 and all(set(option) == {"option_id", "text"} for option in item["options"])
    result = use.submit(quiz["attempt_id"], "alice", {})
    assert len(result["results"][0]["evidence"]) == 1 and result["results"][0]["evidence"][0]["label"] == "S1"


def test_every_result_says_quiz_3():
    use, _, _, _ = build()
    quiz = use.make_quiz("d", "m", "alice", node_ids=["n1"], allow_spend=True)
    assert quiz["contract_version"] == "quiz-3"
    assert use.history("alice")["contract_version"] == "quiz-3"
    assert use.report_question("alice", quiz["attempt_id"], quiz["items"][0]["item_id"])["contract_version"] == "quiz-3"
    assert use.make_quiz("d", "m", "alice", dry_run=True)["contract_version"] == "quiz-3"


# --- 9. the prompts are the spec's text ---------------------------------------------------------------------------

def test_both_prompts_are_the_text_blocks_of_the_spec_word_for_word():
    blocks = re.findall(r"```text\n(.*?)\n```", SPEC.read_text(encoding="utf-8"), re.S)
    assert len(blocks) == 2
    assert SYSTEM_GENERATION == blocks[0] and SYSTEM_SOLVER == blocks[1]
    use, generator, solver, _ = build()
    bank_of(use, "n1")
    assert generator.calls[0].system == blocks[0].replace("{formula_rule}", FORMULA_RULE_TEXT_ONLY)
    assert solver.calls[0].system == blocks[1]
    bank_of(use, "nf")
    assert generator.calls[1].system == blocks[0].replace("{formula_rule}", FORMULA_RULE_WITH_IMAGES)


# --- 10. the material ---------------------------------------------------------------------------------------------

def test_material_has_raw_formula_text_the_other_concepts_and_the_pages_with_formulas():
    use, generator, solver, _ = build()
    bank_of(use, "nf")
    call = generator.calls[0]
    assert call.prompt.startswith("Khái niệm: Hệ số tương quan\nCác khái niệm khác cùng module: "
                                  "Khái niệm 1, Khái niệm 2, Khái niệm 3, Khái niệm 4\n\nTư liệu từ sách:\n[S1] (trang 7, mục Tương quan > Hệ số)")
    assert "[formula: r = 0,8165]" in call.prompt and "[formula: S xy / S x S y]" in call.prompt
    assert "[formula: r → 1]" in call.prompt and "[formula]" not in call.prompt
    assert [page for page, _ in call.images] == [7, 9]
    assert [page for page, _ in solver.calls[0].images] == [7, 9]
    assert solver.calls[0].prompt.startswith(call.prompt)


def test_a_concept_without_formulas_sends_no_picture_and_the_cap_on_pictures_is_the_lecture_cap():
    use, generator, _, _ = build()
    bank_of(use, "n2")
    assert generator.calls[0].images == []
    capped, gen, _, _ = build(settings=BSettings(lecture_max_page_images=1))
    bank_of(capped, "nf")
    assert [page for page, _ in gen.calls[0].images] == [7]


def test_the_siblings_line_names_at_most_twelve_other_concepts():
    use, generator, _, _ = build(graph=make_book(plain=15, formula=False))
    bank_of(use, "n1")
    line = generator.calls[0].prompt.split("\n")[1]
    assert line.removeprefix("Các khái niệm khác cùng module: ").split(", ") == [f"Khái niệm {k}" for k in range(2, 14)]


# --- the rest of the spec: usage, parallelism, estimate, wiring -------------------------------------------------

def test_the_quiz_verify_usage_row_counts_kept_and_rejected():
    use, _, _, store = build(mode=lambda s: "wrong" if s.endswith("câu 2") else "right")
    bank_of(use)
    rows = {row["purpose"]: row for row in store.usage_rows("d")}
    assert (rows["quiz_verify"]["kept"], rows["quiz_verify"]["rejected"]) == (2, 1)
    assert "kept" not in rows["quiz_gen"]


@pytest.mark.parametrize("limit,expected", [(4, 4), (2, 2)])
def test_concepts_of_one_quiz_are_generated_in_parallel_up_to_the_setting(limit, expected):
    use, generator, _, _ = build(graph=make_book(plain=8, formula=False), delay=0.05,
                                 settings=BSettings(quiz_parallel_concepts=limit))
    quiz = use.make_quiz("d", "m", "alice", allow_spend=True)
    assert quiz["ready_count"] == 8 and generator.peak == expected


def test_dry_run_adds_the_pages_to_the_estimate_and_skips_stored_concepts():
    use, _, _, store = build()
    with_pages = use.make_quiz("d", "m", "alice", node_ids=["nf"], dry_run=True)
    use.settings = BSettings(lecture_max_page_images=1)
    one_page = use.make_quiz("d", "m", "alice", node_ids=["nf"], dry_run=True)
    # two laps, a generation call and a solver call each, 1.300 tokens for the second page
    assert with_pages["estimated_input_tokens"] - one_page["estimated_input_tokens"] == 2 * 2 * 1300
    assert with_pages["estimated_calls"] == 4 and with_pages["uncached_concepts"] == 1 and with_pages["estimated_usd"] > 0
    use.settings = BSettings()
    use.make_quiz("d", "m", "alice", node_ids=["nf"], allow_spend=True)
    assert use.make_quiz("d", "m", "alice", node_ids=["nf"], dry_run=True)["uncached_concepts"] == 0


def test_runtime_wires_the_page_pictures_and_the_new_output_caps():
    runtime = PhaseBRuntime(settings=Settings(artifact_dir=Path("artifacts"), gemini_api_key=SecretStr("fake-key")),
                            mode="gemini")
    use = runtime.quiz(make_book())
    assert use.page_images is runtime.page_images
    assert (use.model.max_output_tokens, use.verifier_model.max_output_tokens) == (4096, 8192)
    assert use.model is not use.verifier_model
    limits = BSettings()
    assert (limits.quiz_contract_version, limits.quiz_generation_prompt_version, limits.quiz_verifier_prompt_version,
            limits.quiz_verifier_thinking_level, limits.quiz_items_per_concept, limits.quiz_parallel_concepts) == (
        "quiz-3", "quiz-gen-5", "quiz-verify-5", "medium", 3, 4)


def test_lecture_keys_do_not_move_when_only_quiz_limits_change():
    import sa56_support as support
    changed = replace(BSettings(), quiz_parallel_concepts=1, quiz_verifier_thinking_level="high",
                      quiz_generation_prompt_version="quiz-gen-9", quiz_items_per_concept=5)
    assert support.lecture_keys(changed) == support.lecture_keys()
