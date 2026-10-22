"""SA-52: cloze items choose distractors per quoted sentence and keep the Q-rule hygiene of the LLM path."""
from doc2roadmap.application.phase_b.quiz import QuizUseCase
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore
from test_phase_b_quiz import Graph


def _with_text(graph, text, anchor=None):
    graph.chunks["ca"].text = text
    graph.nodes["a"]["anchor"]["sentence"] = anchor or text.split(".")[0] + "."
    return graph


def _add_node(graph, node_id, name):
    graph.nodes[node_id] = {"node_id": node_id, "name": name, "module_id": "m"}
    graph.modules["m"]["node_ids"].append(node_id)


def _quiz(graph):
    quiz = QuizUseCase(graph, InMemoryPhaseBStore())
    return quiz, quiz.make_quiz("d", "m", "alice", node_ids=["a"])


def _reasons(quiz):
    return {row["reason"] for row in quiz.diagnostics if row["stage"] == "cloze"}


def _options(result):
    return [option["text"] for item in result["items"] for option in item["options"]]


def test_distractor_named_in_the_quoted_sentence_is_replaced_by_another_safe_one():
    graph = _with_text(Graph(), "Tam giác là hình phẳng có ba cạnh, ít hơn hình vuông một cạnh.")
    _add_node(graph, "d", "Hình thang")

    _, result = _quiz(graph)

    assert result["items"]
    assert "Hình vuông" not in _options(result)
    for item in result["items"]:
        stem = item["stem"].casefold()
        assert all(option["text"].casefold() not in stem for option in item["options"])


def test_cloze_is_dropped_when_the_sentence_names_every_safe_distractor():
    graph = _with_text(Graph(), "Tam giác là hình phẳng có ba cạnh, khác hình vuông và hình tròn.")

    quiz, result = _quiz(graph)

    assert result["status"] == "failed" and result["failed_concepts"] == ["a"]
    assert "cloze.distractor_in_stem" in _reasons(quiz)


def test_blank_is_not_cut_out_of_a_longer_concept_name():
    graph = _with_text(Graph(), "Tam giác là hình phẳng có ba cạnh. Tam giác đều là tam giác có ba cạnh bằng nhau.")
    _add_node(graph, "d", "Tam giác đều")

    quiz, result = _quiz(graph)

    stems = [item["stem"] for item in result["items"]]
    assert stems and all("___ đều" not in stem for stem in stems)
    assert "cloze.blank_inside_longer_term" in _reasons(quiz)


def test_notation_name_is_never_a_cloze_option():
    graph = Graph()
    graph.nodes["c"]["name"] = "Mm×n"
    _add_node(graph, "d", "Hình thang")

    _, result = _quiz(graph)

    assert result["items"]
    assert all("×" not in text for text in _options(result))


def test_concept_named_by_notation_has_no_cloze_item():
    graph = Graph()
    graph.nodes["a"].update(name="Mm×n", aliases=[], identity_aliases=[])
    text = "Tập Mm×n gồm mọi ma trận cỡ m nhân n trên trường số thực."
    graph = _with_text(graph, text, anchor=text)

    quiz, result = _quiz(graph)

    assert result["status"] == "failed"
    assert "cloze.notation_option" in _reasons(quiz)


def test_sentence_ending_with_a_colon_is_not_used_as_a_cloze_stem():
    text = "Tam giác có các tính chất sơ cấp sau đây:"
    graph = _with_text(Graph(), text, anchor=text)

    quiz, result = _quiz(graph)

    assert result["status"] == "failed"
    assert "cloze.incomplete_lead_in" in _reasons(quiz)


def test_bank_cached_under_rules_v3_is_not_served_by_the_shipped_rules(monkeypatch):
    graph, store = Graph(), InMemoryPhaseBStore()
    quiz = QuizUseCase(graph, store)
    concept = quiz._concepts("m", ["a"])[0]
    context = quiz._context("m", concept)
    with monkeypatch.context() as patch:
        patch.setattr(QuizUseCase, "LOCAL_RULES_VERSION", "quiz-local-rules-v3")
        old_key = quiz._bank_key("d", "m", concept, None, context=context)
    store.put_cache(old_key, [{"item_id": "legacy-v3", "concept_id": "a", "generator": "cloze",
                               "stem": "old", "options": [], "checks": {}}])

    bank, _ = quiz._bank("d", "m", concept, False, None)

    assert bank and [item["item_id"] for item in bank] != ["legacy-v3"]
