"""SA-70: the assistant gets the same raw formula text as the lecture, counts formula pages before the cut, and its
prompt is `assistant-prompt-5`. Scripted model, fake search and pictures; 0 USD."""
import re
from types import SimpleNamespace as NS

from doc2roadmap.application.phase_b.assistant import AssistantUseCase
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore
from tests.unit.application.test_phase_b_assistant_sa66 import (
    Images, Model, SPEC, ask, first_text, make_graph, seed, turn)


def raw_graph():
    graph = make_graph()
    graph.chunks["c5"].text = "Tích vô hướng là [formula] và độ dài là [formula] ở trang năm."
    graph.chunks["c5"].formula_refs = [NS(formula_id="f1", char_start=0), NS(formula_id="f2", char_start=0)]
    graph.tree = NS(nodes=[NS(formula_id="f1", raw_text="a ·  b"), NS(formula_id="f2", raw_text="√ a")])
    return graph


def build(*chunk_ids, graph=None, images=None, turns=None):
    graph, store = graph or raw_graph(), InMemoryPhaseBStore()
    seed(store, graph, "m3")

    def search(query, **kwargs):
        return [{"chunk_id": cid, "text": graph.chunks[cid].text, "page": graph.chunks[cid].page, "score": 1.0}
                for cid in chunk_ids]
    model = Model(turns or [turn()])
    return AssistantUseCase(graph, store, model, search=search, page_images=images), model, store


def last_validation(store):
    return list(store.list_records("assistant_validation"))[-1]


def test_source_passages_carry_the_raw_formula_text_in_order():
    use_case, model, _ = build("c5", "c4", images=Images())
    ask(use_case)
    assert "Tích vô hướng là [formula: a · b] và độ dài là [formula: √ a] ở trang năm." in first_text(model)


def test_sources_of_the_answer_and_the_graph_keep_the_original_text():
    graph = raw_graph()
    use_case, model, _ = build("c5", graph=graph, images=Images())
    result = ask(use_case)
    assert [row["chunk_id"] for row in result["sources"]] == ["c5"]
    assert graph.chunks["c5"].text == "Tích vô hướng là [formula] và độ dài là [formula] ở trang năm."
    assert [page for page, _ in model.calls[0][0][0]["images"]] == [5]      # the picture is still chosen from the original


def test_passage_without_refs_keeps_the_bare_mark():
    use_case, model, _ = build("c6", images=Images())
    ask(use_case)
    assert "Độ dài véctơ là [formula] trang sáu." in first_text(model)


def test_pages_with_formula_counts_every_page_before_the_picture_limit():
    use_case, model, store = build("c5", "c6", "c7", "c8", images=Images({5, 6, 7, 8}))
    ask(use_case)
    assert [page for page, _ in model.calls[0][0][0]["images"]] == [5, 6, 7]
    log = last_validation(store)
    assert log["pages_with_formula"] == 4 and log["images_sent"] == 3


def test_prompt_is_assistant_prompt_5_the_text_block_of_the_spec():
    block = re.search(r"```text\n(.*?)\n```", SPEC.read_text(encoding="utf-8"), re.S).group(1)
    use_case, model, _ = build("c4")
    ask(use_case)
    assert model.prompt == block
    assert 'Chữ "[formula: …]" là chỗ công thức bị mất khi trích PDF' in model.prompt
    assert model.prompt.splitlines()[-1].startswith("- Khi đã tạo quiz hay tài liệu bằng công cụ")
    assert BSettings().assistant_prompt_version == "assistant-prompt-5"
