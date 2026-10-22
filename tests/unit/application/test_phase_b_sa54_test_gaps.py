"""SA-54: tests for guards that no test protected (K5, module-name vocabulary, SA-52 cloze, SA-53 bridges)."""
from types import SimpleNamespace

from doc2roadmap.application.phase_b.lectures import LectureUseCase, _valid_item
from doc2roadmap.application.phase_b.naming import NameModulesB
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore
from test_phase_b_lecture_b2 import EXPLANATION_2, _Model, _payload
from test_phase_b_naming import Store
from test_phase_b_naming_sa28 import CaptureModel, one_module_graph, response
from test_phase_b_quiz import Graph
from test_phase_b_sa45_lecture_audit import _bridge, _bridge_items, _two_prerequisite_graph
from test_phase_b_sa52_cloze import _add_node, _quiz, _reasons, _with_text

# ---------------------------------------------------------------- K5: invented math symbols

SOURCE = "Tập A có 3 phần tử và tích 2 × 3 bằng 6 theo quy ước."


def _k5(text):
    dropped, labels = {}, {}
    context = {"sources": {"S1": {"text": SOURCE}},
               "registry": SimpleNamespace(citation=lambda label, quote=None: {"label": label, "quote": quote})}
    item = _valid_item({"text": text, "sources": ["S1"], "quote": "Tập A có 3 phần tử"}, context,
                       section="explanation", settings=BSettings(),
                       dropped_by_rule=dropped, dropped_by_source_label=labels)
    return item, dropped, labels


def test_k5_drops_an_idea_whose_math_symbol_is_absent_from_the_cited_source():
    for invented in ("Tập A có 7 phần tử.", "Tập A có phần tử với tích 2 + 3.", "Tập A có 3 phần tử khi x lớn."):
        item, dropped, labels = _k5(invented)
        assert item is None, invented
        assert dropped == {"K5": 1}, (invented, dropped)  # not K3 (quote is verbatim) and not accepted
        assert labels == {"S1": 1}


def test_k5_keeps_the_same_symbols_when_the_cited_source_has_them():
    item, dropped, _ = _k5("Tập A có 3 phần tử và tích 2 × 3 bằng 6.")
    assert item is not None and item["citations"] and dropped == {}


# ---------------------------------------------------------------- module-name vocabulary

def test_module_title_with_a_word_outside_the_module_vocabulary_is_replaced_by_the_fallback():
    graph = one_module_graph()
    model = CaptureModel([response("Ma trận foobarbaz", "Ma trận biểu diễn hệ số của hệ tuyến tính.", "n0a")])

    result, _ = NameModulesB(Store(), model, phase_b_store=InMemoryPhaseBStore(), allow_spend=True).execute(
        "book", upstream=graph)

    module = result.payload["modules"][0]
    assert module["naming_flags"] == ["vocabulary"]
    assert module["title_source"] == "fallback" and "foobarbaz" not in module["title"].casefold()
    assert module["description_source"] == "llm"  # the description rule is separate (SA-29)


def test_module_title_made_only_of_module_words_is_kept():
    graph = one_module_graph()
    model = CaptureModel([response("Ma trận hệ số", "Ma trận biểu diễn hệ số của hệ tuyến tính.", "n0a")])

    result, _ = NameModulesB(Store(), model, phase_b_store=InMemoryPhaseBStore(), allow_spend=True).execute(
        "book", upstream=graph)

    module = result.payload["modules"][0]
    assert module["title"] == "Ma trận hệ số" and module["title_source"] == "llm"
    assert module["naming_flags"] == []


# ---------------------------------------------------------------- SA-52 cloze gaps

def test_distractor_that_only_shares_letters_with_a_longer_word_of_the_sentence_stays_usable():
    graph = _with_text(Graph(), "Tam giác là hình phẳng có ba cạnh, khác hình tròn.")
    _add_node(graph, "d", "Cạn")  # a substring of "cạnh", not a word of the sentence

    _, result = _quiz(graph)

    options = [option["text"] for item in result["items"] for option in item["options"]]
    assert result["items"] and "Cạn" in options and "Hình tròn" not in options


def test_distractor_visible_in_the_sentence_only_through_its_alias_is_dropped():
    graph = _with_text(Graph(), "Tam giác là hình phẳng có ba cạnh, khác hình tròn và tứ giác lồi.")
    _add_node(graph, "d", "Hình thang")
    graph.nodes["d"]["aliases"] = [{"display_name": "tứ giác lồi"}]

    quiz, result = _quiz(graph)

    assert result["status"] == "failed" and result["failed_concepts"] == ["a"]
    assert "cloze.distractor_in_stem" in _reasons(quiz)


def test_fallback_distractor_visible_only_through_its_alias_is_dropped_for_that_sentence_only():
    graph = Graph()
    del graph.nodes["c"]
    graph.modules["m"]["node_ids"].remove("c")
    _add_node(graph, "d", "Hình thang")
    # Its alias equals an alias of the answer, so the normal pass skips it and the fallback pass adds it.
    graph.nodes["d"]["aliases"] = [{"display_name": "hình tam giác"}]

    quiz, result = _quiz(graph)

    stems = [item["stem"] for item in result["items"]]
    assert any("có ba cạnh" in stem for stem in stems)  # first sentence does not show the alias
    assert not any("đoạn thẳng khép kín" in stem for stem in stems)  # second sentence shows "Hình tam giác"
    assert "cloze.distractor_in_stem" in _reasons(quiz)


def test_distractor_with_a_caret_is_never_an_option():
    graph = Graph()
    graph.nodes["b"]["name"] = "Hình vuông^2"
    _add_node(graph, "d", "Hình thang")

    _, result = _quiz(graph)

    options = [option["text"] for item in result["items"] for option in item["options"]]
    assert result["items"] and "Hình thang" in options
    assert not any("^" in text for text in options)


# ---------------------------------------------------------------- SA-53: emitted bridge survives the final pass

C_TEXT = "Quy tắc giúp hiểu phép hợp của hai tập hợp trong bài này."
A1_NEAR_COPY_OF_C = "Tập hợp giúp hiểu phép hợp của hai tập hợp trong bài này."
A2_TEXT = "Tập hợp tạo nền cho phép hợp."
EXPLANATIONS = [{"text": text, "quote": text, "sources": ["S1"]} for text in
                ("Tập hợp gồm các phần tử có cùng một đặc điểm.", EXPLANATION_2)]


def test_second_bridge_of_a_prerequisite_emitted_after_the_first_was_dropped_by_k6_is_not_withdrawn():
    graph = _two_prerequisite_graph()
    bridges = [_bridge("c", C_TEXT), _bridge("a", A1_NEAR_COPY_OF_C), _bridge("a", A2_TEXT)]
    model, store, events = _Model([_payload(bridges=bridges, explanation=EXPLANATIONS)[0]]), InMemoryPhaseBStore(), []
    use_case = LectureUseCase(model, store)

    result = use_case.make("d1", "g1", graph, "b", allow_spend=True, on_event=events.append)
    cached = use_case.make("d1", "g1", graph, "b", allow_spend=True)

    streamed = [event["item"]["text"] for event in events
                if event.get("event") == "item" and event.get("section_kind") == "cau_noi"]
    assert streamed == [C_TEXT, A2_TEXT]  # a1 was rejected by K6 at stream time, a2 was emitted
    for lecture in (result, cached):
        assert [item["text"] for item in _bridge_items(lecture)] == streamed
        by_prerequisite = {row["recall"]["node_id"]: row["bridge"]["text"] for row in lecture["prerequisites"]
                           if row.get("bridge")}
        assert by_prerequisite == {"c": C_TEXT, "a": A2_TEXT}
    assert model.calls == 1
    assert not [event for event in events if event.get("event") in {"retract", "withdraw", "remove"}]
