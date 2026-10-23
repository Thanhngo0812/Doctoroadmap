"""SA-64: the ten invariants of doc/bai-giang-3-spec.md, at use case level. No network, no real model."""
import json
import re
import threading
from dataclasses import replace
from pathlib import Path

import pytest

from doc2roadmap.application.phase_b import lectures
from doc2roadmap.application.phase_b.lecture3 import SELF_CHECK_LINE, Lecture3UseCase, split_self_check, system_prompt
from doc2roadmap.application.phase_b.lecture_context3 import formula_pages, gather_chunks
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore

from sa64_support import (
    GOOD_LESSON, FakeClock, FakeModel, FakePages, list_pieces, make_graph, wait_for,
)

SPEC = (Path(__file__).resolve().parents[3] / "doc" / "bai-giang-3-spec.md").read_text(encoding="utf-8")
JPEG = b"\xff\xd8jpeg-bytes"


def run(model=None, *, graph=None, pages=None, settings=None, node="a", store=None, clock=None, owner=None, **kwargs):
    store = store if store is not None else InMemoryPhaseBStore()
    model = model if model is not None else FakeModel()
    events = []
    use_case = Lecture3UseCase(model, store, page_images=pages, settings=settings or BSettings(), clock=clock or FakeClock())
    result = use_case.make("d1", "g1", graph or make_graph(), node, allow_spend=True, on_event=events.append,
                           owner=owner, **kwargs)
    return result, events, store, model, use_case


def cached_validation(store, result):
    return store.get_cache(result["lecture_key"])["validation"]


def keys_anywhere(value, found=None):
    found = set() if found is None else found
    if isinstance(value, dict):
        for key, child in value.items():
            found.add(key)
            keys_anywhere(child, found)
    elif isinstance(value, list):
        for child in value:
            keys_anywhere(child, found)
    return found


# ---------------------------------------------------------------- 1. context gathering

def picked_ids(settings=None, **options):
    graph = make_graph(**options)
    settings = settings or BSettings()
    node = graph.nodes["a"]
    return [c.chunk_id for c in gather_chunks(graph, node, "c2", settings)], graph


def test_context_takes_a_far_section_named_after_the_concept_and_keeps_reading_order():
    ids, _ = picked_ids()
    assert "c10" in ids and "c11" in ids
    assert ids == sorted(ids, key=lambda cid: int(cid[1:]))
    assert ids[:2] == ["c2", "c3"]


def test_context_never_takes_syllabus_or_admin_chunks_even_when_they_name_the_concept_most():
    ids, _ = picked_ids()
    assert "c0" not in ids and "c1" not in ids


def test_context_stops_at_the_character_limit_and_drops_lower_priority_chunks():
    ids, graph = picked_ids(settings=replace(BSettings(), lecture_context_chars=1000))
    assert ids == ["c2", "c3", "c10", "c11"]
    assert sum(len(graph.chunks[cid].text.strip()) for cid in ids) <= 1000
    assert "c4" not in ids and "c5" not in ids


def test_context_default_limit_is_nine_thousand_characters():
    ids, graph = picked_ids(pile=30)
    total = sum(len(graph.chunks[cid].text.strip()) for cid in ids)
    assert 9000 - 900 < total <= 9000
    assert BSettings().lecture_context_chars == 9000


def test_context_without_any_chunk_naming_the_concept_is_no_source():
    result, events, store, model, _ = run(node="z")
    assert result["status"] == "no_source"
    assert model.calls == []
    assert [e["event"] for e in events] == ["skeleton", "final"]


# ---------------------------------------------------------------- 2. page pictures

def test_pictures_of_exactly_the_formula_pages_are_sent_at_most_four_in_reading_order():
    pages = FakePages({p: JPEG + bytes([p]) for p in (30, 12, 13, 14, 15, 16)})
    result, _, _, model, _ = run(graph=make_graph(formula_pages=(12, 13, 14, 15, 16)), pages=pages)
    sent = [page for page, _ in model.calls[0].images]
    assert sent == [30, 12, 13, 14]
    assert [call[2] for call in pages.calls] == sent
    assert all(data == JPEG + bytes([page]) for page, data in model.calls[0].images)
    assert 2 not in sent  # page 2 holds the definition but no [formula]


def test_no_formula_in_the_material_means_no_picture_is_read_or_sent():
    graph = make_graph()
    for chunk in graph.chunks.values():
        chunk.text = chunk.text.replace("[formula]", "công thức")
    pages = FakePages({p: JPEG for p in range(1, 60)})
    result, _, store, model, _ = run(graph=graph, pages=pages)
    assert result["status"] == "ready"
    assert pages.calls == [] and model.calls[0].images == []
    assert cached_validation(store, result)["thieu_anh_trang"] is False


def test_empty_picture_port_still_gives_a_lesson_and_logs_the_missing_pictures():
    result, _, store, model, _ = run(pages=FakePages({}))
    assert result["status"] == "ready" and result["body_md"]
    assert model.calls[0].images == []
    assert cached_validation(store, result)["thieu_anh_trang"] is True
    assert "Đừng đoán công thức" in model.calls[0].system


def test_picture_rule_follows_whether_pictures_were_sent():
    with_images = run(pages=FakePages({30: JPEG}))[3].calls[0].system
    without = run(pages=FakePages({}))[3].calls[0].system
    assert "đọc công thức đúng từ ảnh" in with_images and "Đừng đoán" not in with_images
    assert "Đừng đoán công thức" in without and "đọc công thức đúng từ ảnh" not in without


def test_formula_pages_helper_keeps_reading_order_and_the_limit():
    chunks = [c for c in make_graph(formula_pages=(40, 41, 42)).chunks.values() if "[formula]" in c.text]
    assert formula_pages(chunks, 2) == [30, 40]


# ---------------------------------------------------------------- 3. system prompt verbatim from the spec

def spec_prompt_and_rules():
    block = re.search(r"### 4\. Lời nhắc.*?```text\n(.*?)\n```", SPEC, re.S).group(1)
    rule1 = re.search(r"Luật 1, khi có ảnh: `([^`]+)`", SPEC).group(1)
    rule2 = re.search(r"Luật 2, khi không có ảnh: `([^`]+)`", SPEC).group(1)
    return block, rule1, rule2


@pytest.mark.parametrize("with_images", [True, False])
def test_system_prompt_sent_to_the_model_is_the_spec_text_plus_one_format_line(with_images):
    block, rule1, rule2 = spec_prompt_and_rules()
    pages = FakePages({30: JPEG}) if with_images else FakePages({})
    sent = run(pages=pages)[3].calls[0].system
    expected = block.replace("{formula_rule}", rule1 if with_images else rule2)
    assert sent.replace(SELF_CHECK_LINE, "") == expected
    assert sent != expected and len(sent.splitlines()) == len(expected.splitlines()) + 1
    for literal in ("### Tự kiểm tra", "**Câu hỏi:**", "**Đáp án:**"):
        assert literal in SELF_CHECK_LINE


def test_user_message_follows_the_trial_layout():
    prompt = run(pages=FakePages({}))[3].calls[0].prompt
    assert prompt.startswith("Khái niệm: Tập hợp (còn gọi: Set)\nThuộc module 1: Cơ sở\n")
    assert "Khái niệm tiếp theo dùng tới khái niệm này: Phép hợp" in prompt
    assert "Tư liệu từ sách:\n[S1] (trang 2, mục Toán > Mở đầu)\n" in prompt
    bprompt = run(node="b", pages=FakePages({}))[3].calls[0].prompt
    assert "Khái niệm tiên quyết:\n- Tập hợp (module 1): " in bprompt


def test_defaults_are_temperature_one_and_four_thousand_tokens_and_the_model_gets_them():
    settings = BSettings()
    assert (settings.lecture_temperature, settings.lecture_max_output_tokens) == (1.0, 4096)
    assert (settings.lecture_contract_version, settings.lecture_prompt_version, settings.lecture_context_version,
            settings.lecture_max_page_images) == ("lecture-3", "lecture-prompt-3", "lecture-context-3", 4)
    assert run()[3].calls[0].temperature == 1.0


# ---------------------------------------------------------------- 4. stream

def test_first_piece_reaches_the_caller_while_the_model_is_still_writing():
    release, first = threading.Event(), threading.Event()
    finished_when_first_arrived = []
    holder = {}

    def script():
        yield "Tập hợp là ý tưởng gom nhóm. "
        assert release.wait(10)
        yield "Phần còn lại."

    model = FakeModel(script)

    def on_event(event):
        if event["event"] == "delta" and not first.is_set():
            finished_when_first_arrived.append(model.calls[0].finished)
            first.set()

    def go():
        holder["result"] = Lecture3UseCase(model, InMemoryPhaseBStore(), settings=BSettings(), clock=FakeClock()).make(
            "d1", "g1", make_graph(), "a", allow_spend=True, on_event=on_event)

    thread = threading.Thread(target=go)
    thread.start()
    arrived = first.wait(3)
    release.set()
    thread.join(10)
    assert arrived, "the first piece must reach the caller before the model finishes"
    assert finished_when_first_arrived == [False]
    assert holder["result"]["body_md"] == "Tập hợp là ý tưởng gom nhóm. Phần còn lại."


def test_events_are_skeleton_then_deltas_then_final_and_deltas_add_up_to_the_lesson():
    result, events, *_ = run()
    kinds = [e["event"] for e in events]
    assert kinds[0] == "skeleton" and kinds[-1] == "final" and set(kinds[1:-1]) == {"delta"}
    assert "".join(e["text"] for e in events if e["event"] == "delta") == GOOD_LESSON
    assert events[0]["lecture"]["status"] == "generating" and events[0]["lecture"]["body_md"] == ""


def test_error_midway_keeps_the_text_already_sent_as_a_cut_ready_lesson():
    sent = "Tập hợp là cách gom các đối tượng. Theo sách [S1] đó là nhóm xác định."
    model = FakeModel([sent, RuntimeError("Gemini request failed")])
    result, events, *_ = run(model)
    assert result["status"] == "ready" and "cat_ngan" in result["warnings"]
    assert result["body_md"] == sent
    assert "".join(e["text"] for e in events if e["event"] == "delta") == sent
    assert events[-1]["event"] == "final" and model.calls and len(model.calls) == 1


def test_deadline_in_the_middle_of_the_stream_keeps_the_text_too():
    pause = threading.Event()

    def script():
        yield "Phần đầu của bài. "
        pause.wait(0.6)
        yield "Phần hai. "
        yield "Không tới được."

    result, *_ = run(FakeModel(script), settings=replace(BSettings(), lecture_click_timeout_seconds=0.3))
    assert result["status"] == "ready" and "cat_ngan" in result["warnings"]
    assert result["body_md"].startswith("Phần đầu của bài.") and "Không tới được" not in result["body_md"]


def test_network_error_before_any_text_is_a_retryable_failure_and_is_remembered_for_sixty_seconds():
    clock = FakeClock()
    model = FakeModel([ConnectionError("down")])
    result, events, store, _, use_case = run(model, clock=clock)
    assert result["status"] == "failed" and events[-1]["event"] == "failure"
    failure = result["failure"]
    assert failure["reason_code"] == "loi_mang" and failure["retryable"] is True
    assert failure["message"] and failure["ask_assistant"] is True and failure["read_page"]["page"] == 2
    again = use_case.make("d1", "g1", make_graph(), "a", allow_spend=True)
    assert again["status"] == "failed" and len(model.calls) == 1
    clock.advance(61)
    use_case.make("d1", "g1", make_graph(), "a", allow_spend=True)
    assert len(model.calls) == 2


# ---------------------------------------------------------------- 5. checks never block or edit

ODD = ("Tập hợp là nền tảng. Theo sách [S1] và cả [S9] nữa. Công thức còn lại là [formula] trong bài.\n\n"
       + "mỗi phần tử của tập hợp đều thuộc về một nhóm xác định rõ ràng. " * 4)


def test_unknown_label_leftover_formula_and_repeated_ngrams_never_block_or_edit_the_lesson():
    result, _, store, *_ = run(FakeModel([ODD]))
    assert result["status"] == "ready" and result["body_md"] == ODD and result["warnings"] == []
    validation = cached_validation(store, result)
    assert validation["unknown_labels"] == ["S9"]
    assert validation["formula_left"] is True and validation["repeated_8grams"] >= 1
    assert "S1" in validation["labels"] and validation["word_count"] > 20


def test_validation_scores_a_label_by_syllable_pairs_shared_with_the_cited_chunk():
    cited = "Tập hợp là một nhóm đối tượng được xác định rõ ràng. [S1]"
    result, _, store, *_ = run(FakeModel([cited + "\n\nMột đoạn hoàn toàn khác về véc tơ riêng. [S1]"]))
    assert 0.2 < cached_validation(store, result)["labels"]["S1"] < 0.8
    full = run(FakeModel(["Tập hợp là một nhóm đối tượng được xác định rõ ràng. [S1]"]))
    assert cached_validation(full[2], full[0])["labels"]["S1"] == 1.0


# ---------------------------------------------------------------- 6. self-check split

def test_self_check_is_split_off_the_lesson():
    result, *_ = run()
    assert result["self_check"] == {"question_md": "Số 5 có thuộc A không?",
                                    "answer_md": "Không, vì A chỉ gồm 1, 2, 3."}
    assert "Tự kiểm tra" not in result["body_md"] and result["body_md"].endswith("[S2]")


def test_wrong_self_check_shape_keeps_the_lesson_whole_and_is_logged():
    wrong = GOOD_LESSON.replace("**Câu hỏi:**", "Hỏi:").replace("**Đáp án:**", "Trả lời:")
    result, _, store, *_ = run(FakeModel([wrong]))
    assert result["status"] == "ready" and result["self_check"] is None and result["body_md"] == wrong
    assert cached_validation(store, result)["khong_tach_tu_kiem"] is True
    assert split_self_check("Không có mục nào.") == ("Không có mục nào.", None)
    assert split_self_check("Bài.\n\n### Tự kiểm tra\n\n**Đáp án:** x\n\n**Câu hỏi:** y")[1] is None


# ---------------------------------------------------------------- 7. validation never reaches the learner

def test_validation_is_in_the_cache_and_the_usage_row_but_not_in_any_learner_path():
    store = InMemoryPhaseBStore()
    fresh, fresh_events, _, _, use_case = run(store=store)
    again_events = []
    cached = use_case.make("d1", "g1", make_graph(), "a", allow_spend=True, on_event=again_events.append)
    peeked = use_case.make("d1", "g1", make_graph(), "a", cache_only=True)
    assert "validation" in store.get_cache(fresh["lecture_key"])
    assert [r for r in store.usage_rows("d1") if r["purpose"] == "lecture_validation"][0]["validation"]
    for lecture in (fresh, cached, peeked, *(e["lecture"] for e in fresh_events if "lecture" in e),
                    *(e["lecture"] for e in again_events if "lecture" in e)):
        assert "validation" not in keys_anywhere(lecture)


def test_assistant_get_lecture_tool_returns_body_and_sources_without_validation():
    from test_phase_b_assistant_content import Model, ask
    from doc2roadmap.application.ports.phase_b import Delta, Done, ToolCall
    store = InMemoryPhaseBStore()
    graph = make_graph()
    use_case = Lecture3UseCase(FakeModel(), store, settings=BSettings(), clock=FakeClock())
    use_case.make("d1", "g1", graph, "a", allow_spend=True)

    def lecture(**kwargs):
        return use_case.make("d1", "g1", graph, kwargs["concept"], cache_only=True)

    assistant_graph = make_graph()
    assistant_graph.doc_id = "book"
    model = Model([[ToolCall("get_lecture", {"concept": "a"}, "1"), Done({})], [Delta("KHONG_DU\nKhông đủ."), Done({})]])
    summary = ask(assistant_graph, model, lecture=lecture)["tool_calls"][0]["result_summary"]
    assert summary["status"] == "ready" and summary["body_md"] == use_case.make(
        "d1", "g1", graph, "a", cache_only=True)["body_md"]
    assert summary["sources"][0]["label"] == "S1" and summary["sources"][0]["chunk_id"] == "c2"
    assert "validation" not in keys_anywhere(summary)


# ---------------------------------------------------------------- 8. empty output

def test_empty_output_is_generated_again_exactly_once_then_fails_with_a_reason():
    model = FakeModel([""], ["   \n"])
    result, events, store, _, _ = run(model)
    assert len(model.calls) == 2
    assert result["status"] == "failed" and events[-1]["event"] == "failure"
    failure = result["failure"]
    assert failure["reason_code"] == "khong_dung_duoc" and failure["retryable"] is True and failure["message"]
    assert result["body_md"] == "" and "sections" not in result
    assert store.get_cache(result["lecture_key"]) is None


def test_second_try_after_an_empty_first_one_gives_the_lesson():
    model = FakeModel([""], list_pieces(GOOD_LESSON))
    result, events, *_ = run(model)
    assert len(model.calls) == 2 and result["status"] == "ready"
    assert "".join(e["text"] for e in events if e["event"] == "delta") == GOOD_LESSON


# ---------------------------------------------------------------- 9. cache

def test_second_click_costs_no_call_and_a_new_prompt_version_writes_again():
    store, model = InMemoryPhaseBStore(), FakeModel()
    first, _, _, _, use_case = run(model, store=store)
    second = use_case.make("d1", "g1", make_graph(), "a", allow_spend=True)
    assert len(model.calls) == 1 and second["body_md"] == first["body_md"] and second["lecture_key"] == first["lecture_key"]
    newer = Lecture3UseCase(model, store, settings=replace(BSettings(), lecture_prompt_version="lecture-prompt-4"),
                            clock=FakeClock()).make("d1", "g1", make_graph(), "a", allow_spend=True)
    assert len(model.calls) == 2 and newer["lecture_key"] != first["lecture_key"]


def test_a_new_page_picture_changes_the_key():
    first = run(pages=FakePages({30: JPEG}))[0]["lecture_key"]
    second = run(pages=FakePages({30: JPEG + b"x"}))[0]["lecture_key"]
    assert first != second


def test_cache_is_shared_and_learner_status_is_added_at_read_time():
    store, model = InMemoryPhaseBStore(), FakeModel()
    run(model, store=store, node="a")
    alice = run(model, store=store, node="a", owner="alice")[0]
    nobody = run(model, store=store, node="a")[0]
    assert len(model.calls) == 1
    assert alice["next_up"][0]["learner_status"] == "not_learned" and nobody["next_up"][0]["learner_status"] == "unknown"
    assert "learner_status" not in json.dumps(store.get_cache(alice["lecture_key"]))


# ---------------------------------------------------------------- 10. never a TextRank sentence

def test_no_path_returns_textrank_sentences(monkeypatch):
    def banned(*args, **kwargs):
        raise AssertionError("TextRank fallback must not run for lecture-3")
    monkeypatch.setattr(lectures, "_fallback_sections", banned)
    paths = [
        run(FakeModel([""], [""]))[0],                 # failed
        run(FakeModel([ConnectionError("x")]))[0],     # failed on the network
        run(node="z")[0],                              # no source
        run()[0],                                      # ready
    ]
    use_case = run()[4]
    paths += [use_case.make("d1", "g1", make_graph(), "a", cache_only=True),
              use_case.make("d1", "g1", make_graph(), "b", cache_only=True)]   # not cached
    for lecture in paths:
        assert "sections" not in lecture
        if lecture["status"] != "ready":
            assert lecture["body_md"] == "" and lecture["self_check"] is None


# ---------------------------------------------------------------- contract and ledger

def test_contract_lecture_3_fields_and_sources():
    result, *_ = run()
    assert result["contract_version"] == "lecture-3" and result["status"] == "ready"
    assert result["lecture_key"].startswith("sha256:") and result["failure"] is None
    for name in ("position", "definition", "prerequisites", "next_up", "sources", "usage", "warnings", "body_md"):
        assert name in result
    assert [s["label"] for s in result["sources"]] == [f"S{n}" for n in range(1, len(result["sources"]) + 1)]
    assert result["sources"][0] == {"label": "S1", "chunk_id": "c2", "page": 2, "section_path": ["Toán", "Mở đầu"]}
    assert [s["page"] for s in result["sources"]] == sorted(s["page"] for s in result["sources"])
    assert result["definition"]["quote"] == "Tập hợp là một nhóm đối tượng được xác định rõ ràng."
    assert result["usage"]["cost_usd"] > 0 and result["usage"]["ttft_ms"] is not None


def test_prerequisite_keeps_the_recall_block_without_a_bridge():
    result, *_ = run(node="b")
    assert result["prerequisites"][0]["recall"]["name"] == "Tập hợp"
    assert "bridge" not in result["prerequisites"][0] and result["prerequisites"][0]["learner_status"] == "unknown"


def test_each_generation_writes_one_usage_row_and_a_daily_spend_check_is_made():
    result, _, store, *_ = run(FakeModel([""], list_pieces(GOOD_LESSON)))
    rows = [r for r in store.usage_rows("d1") if r["purpose"] == "lecture"]
    assert len(rows) == 2 and all(r["cost_usd"] > 0 for r in rows)
    assert result["usage"]["cost_usd"] == pytest.approx(sum(r["cost_usd"] for r in rows))


def test_dry_run_estimates_without_calling_the_model():
    result, _, store, model, _ = run(dry_run=True)
    assert model.calls == [] and result["dry_run"] is True and result["estimate_usd"] > 0
    assert store.usage_rows("d1") == []


def test_no_model_is_a_failure_that_is_not_remembered():
    store = InMemoryPhaseBStore()
    use_case = Lecture3UseCase(None, store, settings=BSettings(), clock=FakeClock())
    result = use_case.make("d1", "g1", make_graph(), "a", allow_spend=True)
    assert result["failure"]["reason_code"] == "khong_co_mo_hinh"
    assert store.list_records("lecture_failure") == []


# ---------------------------------------------------------------- assistant focus reads the lecture-3 cache only

def test_assistant_focus_takes_lecture_3_paragraphs_without_labels_headings_or_generation():
    import sa56_support as support
    from test_phase_b_assistant_sa56 import FOCUS_ANSWER, CountingLectureModel, assistant_with, ask, sent_context
    store, counting = InMemoryPhaseBStore(), CountingLectureModel()
    lecture = Lecture3UseCase(counting, store, settings=BSettings(), clock=FakeClock())
    key = lecture.make("book", 1, support.make_graph(), "f", dry_run=True)["lecture_key"]
    store.put_cache(key, {"status": "ready", "node_id": "f", "lecture_key": key, "contract_version": "lecture-3",
                          "body_md": "Song ánh vừa đơn ánh vừa toàn ánh [S1].\n\n### Ví dụ\n\nMỗi phần tử đích có đúng một nghịch ảnh.",
                          "sources": [], "validation": {"word_count": 3}})

    def get_lecture(concept, *, owner, doc_id, graph_version, graph, **kwargs):
        return lecture.make(doc_id, graph_version, graph, concept, owner=owner, **kwargs)

    use_case, model, _, _ = support.build([support.answer_turn(FOCUS_ANSWER)], lecture=get_lecture, store=store)
    ask(use_case, "giải thích phần này", focus_node_id="f")
    ideas = sent_context(model)["focus"]["lecture_ideas"]["items"]
    assert ideas == ["Song ánh vừa đơn ánh vừa toàn ánh.", "Mỗi phần tử đích có đúng một nghịch ảnh."]
    assert counting.touched == 0 and "validation" not in json.dumps(sent_context(model))
