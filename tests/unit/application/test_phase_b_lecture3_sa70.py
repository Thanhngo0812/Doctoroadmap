"""SA-70: `lecture-3` bản 2. Invariants 11-16 of doc/bai-giang-3-spec.md, at use case level. No network, no real model."""
import re
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

from doc2roadmap.application.phase_b.lecture3 import SELF_CHECK_LINE, Lecture3UseCase, split_self_check
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore

from sa64_support import GOOD_LESSON, FakeClock, FakeModel, FakePages, list_pieces, make_graph

SPEC = (Path(__file__).resolve().parents[3] / "doc" / "bai-giang-3-spec.md").read_text(encoding="utf-8")
JPEG = b"\xff\xd8jpeg-bytes"
TWO_FORMULAS = "Ví dụ xa. Công thức một [formula] rồi công thức hai [formula] ở cuối đoạn."


def raw_graph(raws=("x²   +\ny", "∑ a_i"), refs=("f1", "f2"), text=TWO_FORMULAS, **options):
    """The usual small book, but chunk c10 carries two lost formulas whose raw text sits in the parse tree."""
    graph = make_graph(**options)
    graph.chunks["c10"].text = text
    graph.chunks["c10"].formula_refs = [NS(formula_id=ref, char_start=0) for ref in refs]
    graph.tree = NS(nodes=[NS(formula_id=None, raw_text=None),
                           *(NS(formula_id=f"f{number}", raw_text=raw) for number, raw in enumerate(raws, 1))])
    return graph


def run(model=None, *, graph=None, pages=None, settings=None, node="a", store=None):
    store = store if store is not None else InMemoryPhaseBStore()
    model = model if model is not None else FakeModel()
    events = []
    use_case = Lecture3UseCase(model, store, page_images=pages, settings=settings or BSettings(), clock=FakeClock())
    result = use_case.make("d1", "g1", graph or make_graph(), node, allow_spend=True, on_event=events.append)
    return result, events, store, model


def validation_of(store, result):
    return store.get_cache(result["lecture_key"])["validation"]


def deltas(events):
    return "".join(event["text"] for event in events if event["event"] == "delta")


# ---------------------------------------------------------------- 11. raw formula text, in order

def test_each_lost_formula_gets_its_raw_text_in_order_with_spaces_collapsed():
    prompt = run(graph=raw_graph())[3].calls[0].prompt
    assert "Công thức một [formula: x² + y] rồi công thức hai [formula: ∑ a_i] ở cuối đoạn." in prompt


def test_swapped_refs_swap_the_raw_text_so_the_order_comes_from_formula_refs():
    prompt = run(graph=raw_graph(refs=("f2", "f1")))[3].calls[0].prompt
    assert "Công thức một [formula: ∑ a_i] rồi công thức hai [formula: x² + y]" in prompt


def test_passage_without_formula_refs_keeps_the_bare_mark_and_missing_raw_text_too():
    prompt = run(graph=raw_graph(raws=("", "∑ a_i"), formula_pages=(41,)))[3].calls[0].prompt
    assert "Công thức một [formula] rồi công thức hai [formula: ∑ a_i]" in prompt      # f1 has no raw text
    assert "ở trang 41 [formula]." in prompt                                           # c20 has no formula_refs


def test_fewer_refs_than_marks_replaces_the_first_ones_only():
    prompt = run(graph=raw_graph(refs=("f1",)))[3].calls[0].prompt
    assert "Công thức một [formula: x² + y] rồi công thức hai [formula] ở cuối" in prompt


def test_sources_ids_and_the_graph_text_are_not_touched_by_raw_text():
    plain, _, _, plain_model = run(graph=make_graph())
    graph = raw_graph(text=make_graph().chunks["c10"].text)
    graph.chunks["c10"].formula_refs = [NS(formula_id="f1", char_start=0)]
    result, _, store, model = run(graph=graph)
    assert result["sources"] == plain["sources"]
    assert "[formula: x² + y]" in model.calls[0].prompt and "[formula: " not in plain_model.calls[0].prompt
    assert graph.chunks["c10"].text == make_graph().chunks["c10"].text       # picking pages still reads the original


def test_raw_text_does_not_change_which_pages_get_a_picture():
    pages = FakePages({30: JPEG})
    run(graph=raw_graph(), pages=pages)
    assert [call[2] for call in pages.calls] == [30]


def test_validation_scores_labels_against_the_original_chunk_text():
    lesson = "Ví dụ xa. Công thức một [formula] rồi công thức hai [formula] ở cuối đoạn. [S5]"
    graph = raw_graph()
    result, _, store, model = run(FakeModel([lesson]), graph=graph)
    label = "S%d" % (1 + [row["chunk_id"] for row in result["sources"]].index("c10"))
    lesson = lesson.replace("[S5]", f"[{label}]")
    result, _, store, model = run(FakeModel([lesson]), graph=graph)
    assert validation_of(store, result)["labels"][label] == 1.0


# ---------------------------------------------------------------- 12. eight pictures, counted before the cut

def ten_page_graph():
    return make_graph(formula_pages=tuple(range(12, 22)))        # ten more pages plus c10's page 30: eleven


def test_more_than_eight_formula_pages_send_the_first_eight_and_count_all_of_them():
    pages = FakePages({page: JPEG + bytes([page]) for page in range(1, 60)})
    result, _, store, model = run(graph=ten_page_graph(), pages=pages)
    sent = [page for page, _ in model.calls[0].images]
    assert sent == [30, 12, 13, 14, 15, 16, 17, 18]
    validation = validation_of(store, result)
    assert validation["pages_with_formula"] == 11
    assert validation["images_sent"] == 8 and validation["thieu_anh_trang"] is True


def test_exactly_eight_formula_pages_all_sent_means_nothing_is_missing():
    pages = FakePages({page: JPEG for page in range(1, 60)})
    result, _, store, model = run(graph=make_graph(formula_pages=tuple(range(12, 19))), pages=pages)
    validation = validation_of(store, result)
    assert len(model.calls[0].images) == 8 and validation["pages_with_formula"] == 8
    assert validation["thieu_anh_trang"] is False


def test_a_port_that_misses_some_of_the_eight_still_flags_it():
    pages = FakePages({30: JPEG, 12: JPEG})
    result, _, store, model = run(graph=make_graph(formula_pages=(12, 13)), pages=pages)
    validation = validation_of(store, result)
    assert validation["pages_with_formula"] == 3 and validation["images_sent"] == 2
    assert validation["thieu_anh_trang"] is True


def test_no_formula_in_the_material_counts_zero_pages():
    graph = make_graph()
    for chunk in graph.chunks.values():
        chunk.text = chunk.text.replace("[formula]", "công thức")
    result, _, store, _ = run(graph=graph, pages=FakePages({}))
    assert validation_of(store, result)["pages_with_formula"] == 0


@pytest.mark.parametrize("left,expected", [("Còn [formula] trong bài.", True), ("Còn [formula: x + y] trong bài.", True),
                                           ("Công thức $x+y$ đã viết xong.", False)])
def test_formula_left_catches_the_mark_with_or_without_raw_text(left, expected):
    result, _, store, _ = run(FakeModel([left + " [S1]"]))
    assert validation_of(store, result)["formula_left"] is expected


# ---------------------------------------------------------------- 13. the stream stops before the self-check

SELF_CHECK_BODY = "\n\n**Câu hỏi:** Số 5 có thuộc A không?\n\n**Đáp án:** Không, vì A chỉ gồm 1, 2, 3."
LESSON_HEAD = "Tập hợp cho ta cách gom đối tượng lại. [S1]\n\nVí dụ: A gồm 1, 2, 3. [S2]\n\n"


@pytest.mark.parametrize("heading", ["### Tự kiểm tra", "## Tự kiểm tra", "#### Tự kiểm tra", "### Tự kiểm tra:",
                                     "  ### Tự kiểm tra", "### TỰ KIỂM TRA"])
def test_deltas_never_carry_the_self_check_under_any_valid_heading(heading):
    text = LESSON_HEAD + heading + SELF_CHECK_BODY
    result, events, *_ = run(FakeModel(list_pieces(text, 7)))
    shown = deltas(events)
    assert result["self_check"] is not None
    assert not re.search(r"Câu hỏi|Đáp án|kiểm tra", shown, re.I)
    assert shown.rstrip() == result["body_md"].rstrip()


@pytest.mark.parametrize("heading", ["### Tự kiểm tra", "  ### Tự kiểm tra:"])
def test_a_heading_cut_across_two_pieces_is_still_held_back(heading):
    text = LESSON_HEAD + heading + SELF_CHECK_BODY
    start = text.index(heading)
    for cut in range(start, start + len(heading) + 1):
        result, events, *_ = run(FakeModel([text[:cut], text[cut:]]))
        assert not re.search(r"Câu hỏi|Đáp án|kiểm tra", deltas(events), re.I), cut
        assert deltas(events).rstrip() == result["body_md"].rstrip(), cut


def test_one_character_pieces_behave_the_same():
    text = LESSON_HEAD + "### Tự kiểm tra" + SELF_CHECK_BODY
    result, events, *_ = run(FakeModel(list(text)))
    assert deltas(events).rstrip() == result["body_md"].rstrip() and "Đáp án" not in deltas(events)


def test_other_headings_are_still_shown_even_when_cut_in_two_pieces():
    text = LESSON_HEAD + "### Ví dụ giải\n\nBước một. [S2]\n\n### Tự kiểm tra" + SELF_CHECK_BODY
    cut = text.index("### Ví dụ") + 5
    result, events, *_ = run(FakeModel([text[:cut], text[cut:]]))
    shown = deltas(events)
    assert "### Ví dụ giải\n\nBước một. [S2]" in shown and "Tự kiểm tra" not in shown
    assert shown.rstrip() == result["body_md"].rstrip()


def test_a_hash_line_that_is_not_the_heading_is_released_once_complete():
    text = "Mở đầu.\n\n### Tự kiểm tra lại bằng ví dụ\n\nNội dung thêm. [S1]"
    result, events, *_ = run(FakeModel(["Mở đầu.\n\n###", " Tự kiểm tra lại bằng", " ví dụ\n\nNội dung thêm. [S1]"]))
    assert deltas(events) == text == result["body_md"]


def test_ordinary_text_is_delivered_at_once_not_held_until_the_line_or_the_lesson_ends():
    seen_when_next_piece_is_asked = []
    events = []

    def script():
        yield "Tập hợp là một ý tưởng gom nhóm, "
        seen_when_next_piece_is_asked.append(deltas(events))
        yield "và đây là phần còn lại. [S1]\n\n"
        seen_when_next_piece_is_asked.append(deltas(events))
        yield "### Tự kiểm tra" + SELF_CHECK_BODY

    model = FakeModel(script)
    Lecture3UseCase(model, InMemoryPhaseBStore(), settings=BSettings(), clock=FakeClock()).make(
        "d1", "g1", make_graph(), "a", allow_spend=True, on_event=events.append)
    assert seen_when_next_piece_is_asked[0] == "Tập hợp là một ý tưởng gom nhóm, "
    assert seen_when_next_piece_is_asked[1].endswith("[S1]\n\n")


def test_error_with_a_half_written_hash_line_still_delivers_what_the_cut_lesson_keeps():
    result, events, *_ = run(FakeModel(["Bài ngắn. [S1]\n\n### Ví", RuntimeError("Gemini request failed")]))
    assert "cat_ngan" in result["warnings"] and result["body_md"] == "Bài ngắn. [S1]\n\n### Ví"
    assert deltas(events) == result["body_md"]


def test_an_unsplittable_self_check_keeps_the_whole_lesson_in_final():
    text = LESSON_HEAD + "### Tự kiểm tra\n\nHỏi: gì? Trả lời: đó."
    result, events, *_ = run(FakeModel([text]))
    assert result["self_check"] is None and result["body_md"] == text
    assert "Hỏi:" not in deltas(events)       # the stream stops at the heading; only final has the rest


# ---------------------------------------------------------------- 14. the prompt, word for word

def spec_block_and_rules():
    block = re.search(r"### 4\. Lời nhắc.*?```text\n(.*?)\n```", SPEC, re.S).group(1)
    return (block, re.search(r"Luật 1, khi có ảnh: `([^`]+)`", SPEC).group(1),
            re.search(r"Luật 2, khi không có ảnh: `([^`]+)`", SPEC).group(1))


@pytest.mark.parametrize("with_images", [True, False])
def test_prompt_is_the_v5_spec_text(with_images):
    block, rule1, rule2 = spec_block_and_rules()
    sent = run(pages=FakePages({30: JPEG} if with_images else {}))[3].calls[0].system
    assert sent.replace(SELF_CHECK_LINE, "") == block.replace("{formula_rule}", rule1 if with_images else rule2)
    for phrase in ("soát lại từng con số", "Đừng tự định nghĩa hay mô tả khái niệm tiếp theo", "Giữ đúng chiều và phạm vi"):
        assert phrase in sent
    assert "[formula: …]" in sent and "chữ trích thô" in sent


def test_the_rule_with_pictures_keeps_the_raw_text_fallback_and_the_one_without_has_no_picture_talk():
    _, rule1, rule2 = spec_block_and_rules()
    assert "đọc công thức đúng từ ảnh" in rule1 and "Công thức ở trang không có ảnh thì dựng lại" in rule1
    assert "ảnh" not in rule2


# ---------------------------------------------------------------- 15. thinking level

def test_default_sends_no_thinking_argument_and_a_level_sends_exactly_that_level():
    off = run()[3]
    assert off.calls[0].extra == {}
    low = run(settings=replace(BSettings(), lecture_thinking_level="low"))[3]
    assert low.calls[0].extra == {"thinking_level": "low"}


def test_thinking_level_changes_the_cache_key():
    keys = {level: run(settings=replace(BSettings(), lecture_thinking_level=level))[0]["lecture_key"]
            for level in (None, "low", "high")}
    assert len(set(keys.values())) == 3
    store, model = InMemoryPhaseBStore(), FakeModel()
    run(model, store=store)
    run(model, store=store, settings=replace(BSettings(), lecture_thinking_level="low"))
    assert len(model.calls) == 2           # a lesson written without thinking is not served for a thinking one


def test_new_defaults():
    settings = BSettings()
    assert (settings.lecture_prompt_version, settings.lecture_context_version, settings.lecture_max_page_images,
            settings.lecture_thinking_level) == ("lecture-prompt-4", "lecture-context-4", 8, None)
