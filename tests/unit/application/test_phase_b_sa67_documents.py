"""SA-67: `document-3`. The ten invariants of doc/tai-lieu-3-spec.md, at use case level. No network, no real model."""
import re
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

from doc2roadmap.application.phase_b.assistant import AssistantUseCase
from doc2roadmap.application.phase_b.documents import DocumentUseCase
from doc2roadmap.application.ports.phase_b import Done, ToolCall
from doc2roadmap.domain.learning_graph import LearningGraph
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore

from sa64_support import FakeClock, FakeModel, FakePages, chunk, list_pieces

SPEC = (Path(__file__).resolve().parents[3] / "doc" / "tai-lieu-3-spec.md").read_text(encoding="utf-8")
SPEC_LECTURE = (Path(__file__).resolve().parents[3] / "doc" / "bai-giang-3-spec.md").read_text(encoding="utf-8")
JPEG = b"\xff\xd8jpeg-bytes"
NAMES = ["Alpha", "Bravo", "Cobalt", "Delta", "Echo", "Foxtrot", "Gamma", "Hotel"]
HIT_ID = "c25"
GOOD_DOC = ("# Đề cương ôn tập\n\nAlpha là khái niệm cơ bản số 0. [S1]\n\nBravo đứng sau Alpha.\n\n"
            "| Khái niệm | Ý chính |\n|---|---|\n| Alpha | điều kiện $x^2$ [S1] |\n")


def doc_graph(modules=3, per=2, filler=0, filler_chars=900, formula_pages=(), raw=None, doc_id="d1"):
    """`modules` modules of `per` concepts. Concept k is defined in chunk c(10k+10) with the marker DEF-<name>.

    The searched-for passage c25 sits between the third and fourth definition; filler chunks name their concept again
    and come last; each formula page adds a passage of the first concept that lost one formula."""
    chunks, nodes, mods, k = [], [], [], 0
    for m in range(modules):
        ids = []
        for _ in range(per):
            name, cid = NAMES[k], 10 * k + 10
            sentence = f"{name} là khái niệm cơ bản số {k}."
            chunks.append(chunk(cid, "noi_dung", f"Chương {m + 1}", ["Định nghĩa"], 100 + k,
                                f"{sentence} DEF-{name} nằm ở đây."))
            nodes.append({"node_id": f"n{k}", "name": name, "display_name": name, "learnable": True,
                          "module_id": f"m{m}", "teaching_chunk_ids": [f"c{cid}"], "defining_chunk_ids": [],
                          "anchor": {"chunk_id": f"c{cid}", "sentence": sentence}})
            ids.append(f"n{k}")
            for j in range(filler):
                chunks.append(chunk(1000 + 100 * k + j, "noi_dung", f"Chương {m + 1}", ["Ví dụ"], 300 + j,
                                    f"{name} ví dụ số {j}. " + "chữ " * (filler_chars // 4)))
            k += 1
        mods.append({"module_id": f"m{m}", "index": m, "title": f"Phần {m + 1}", "node_ids": ids})
    chunks.append(chunk(25, "noi_dung", "Phụ lục", ["Ghi chú"], 55, "Ghi chú đặc biệt về TRUYVAN trong bài."))
    tree_nodes = []
    for i, page in enumerate(formula_pages):
        text = f"Alpha còn có công thức [formula] ở trang {page}."
        c = chunk(1000 + i, "noi_dung", "Chương 1", ["Công thức"], page, text)
        c.formula_refs = [NS(formula_id=f"f{page}", char_start=0)]
        chunks.append(c)
        tree_nodes.append(NS(formula_id=f"f{page}", raw_text=(raw or "RAW{}").format(page)))
    graph = LearningGraph({"doc_id": doc_id, "graph_version": "g1", "nodes": nodes, "modules": mods,
                           "requires_edges": [], "open_edges": []}, chunks)
    graph.parse_version = 3
    graph.tree = NS(nodes=tree_nodes)
    return graph


class Search:
    def __init__(self, ids=(HIT_ID,), error=None):
        self.ids, self.error, self.calls = list(ids), error, []

    def __call__(self, query, **kwargs):
        self.calls.append((query, kwargs))
        if self.error:
            raise self.error
        return [{"chunk_id": cid, "text": "x"} for cid in self.ids]


def run(model=None, *, graph=None, request="Tóm tắt TRUYVAN", scope=None, search=None, pages=None, settings=None,
        store=None, owner="alice", guard=None, **kwargs):
    store = store if store is not None else InMemoryPhaseBStore()
    model = model if model is not None else FakeModel(list_pieces(GOOD_DOC))
    graph = graph or doc_graph()
    search = search if search is not None else Search()
    events = []
    use_case = DocumentUseCase(model, store, settings=settings or BSettings(), search=search, page_images=pages,
                               clock=FakeClock(), spend_guard=guard)
    result = use_case.create("d1", "g1", graph, request, scope or {"module_ids": list(graph.modules)},
                             owner=owner, allow_spend=True, on_event=events.append, **kwargs)
    return result, events, store, model, search, use_case


def passages(prompt):
    """[(label, page, text)] of the book passages in the user message."""
    body = prompt.split("Tư liệu từ sách:\n", 1)[1]
    parts = re.split(r"^\[(S\d+)\] \(trang (\d+)[^\n]*\)\n", body, flags=re.M)
    return [(parts[i], int(parts[i + 1]), parts[i + 2].strip()) for i in range(1, len(parts), 3)]


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


def validation_of(store, result):
    return store.get_record("document_validation", result["document_id"])


# ---------------------------------------------------------------- 1. wide material, every concept covered

def test_three_modules_send_the_definition_of_every_concept_and_the_searched_passage_in_reading_order():
    result, _, _, model, search, _ = run(graph=doc_graph(modules=3, per=2, filler=3))
    prompt = model.calls[0].prompt
    shown = " ".join(text for _, _, text in passages(prompt))
    for name in NAMES[:6]:
        assert f"DEF-{name}" in shown, name
    assert "TRUYVAN" in shown
    assert search.calls and search.calls[0][0] == "Tóm tắt TRUYVAN" and search.calls[0][1].get("k") == 6
    ids = [row["chunk_id"] for row in result["sources"]]
    assert ids == sorted(ids, key=lambda cid: int(cid[1:]))
    assert [label for label, _, _ in passages(prompt)] == [f"S{n}" for n in range(1, len(ids) + 1)]
    assert ids.index(HIT_ID) == ids.index("c30") - 1       # between the third and the fourth definition


def test_message_names_the_request_the_scope_and_every_concept_with_app_module_numbers():
    _, _, _, model, _, _ = run(graph=doc_graph(modules=3, per=2), scope={"module_ids": ["m1", "m2"]})
    prompt = model.calls[0].prompt
    head = prompt.split("Tư liệu từ sách:", 1)[0]
    assert head.startswith("Yêu cầu của sinh viên: Tóm tắt TRUYVAN\n")
    assert "Phạm vi đã chọn: module 2: Phần 2; module 3: Phần 3" in head
    assert "Các khái niệm trong phạm vi:\n- Cobalt (module 2)\n- Delta (module 2)\n- Echo (module 3)\n- Foxtrot (module 3)" in head
    assert "Alpha" not in head
    assert re.search(r"^\[S1\] \(trang \d+, mục .+\)$", prompt, flags=re.M)


def test_empty_request_uses_the_default_request():
    _, _, _, model, search, _ = run(request="  ")
    assert model.calls[0].prompt.startswith(
        "Yêu cầu của sinh viên: Tóm tắt các ý chính của phạm vi này để ôn tập, có ví dụ.\n")


def test_material_never_passes_twenty_thousand_characters_and_definitions_still_win_a_place():
    settings = replace(BSettings(), document_per_concept_chars=10_000)
    graph = doc_graph(modules=3, per=2, filler=14)
    assert sum(len(c.text) for c in graph.chunks.values()) > 60_000
    result, _, _, model, _, _ = run(graph=graph, settings=settings)
    rows = passages(model.calls[0].prompt)
    assert 15_000 < sum(len(text) for _, _, text in rows) <= 20_000
    shown = " ".join(text for _, _, text in rows)
    assert all(f"DEF-{name}" in shown for name in NAMES[:6]) and "TRUYVAN" in shown


def test_default_per_concept_limit_keeps_a_concept_to_sixteen_hundred_characters_beyond_its_definition():
    assert BSettings().document_per_concept_chars == 1600 and BSettings().document_context_chars == 20_000
    _, _, _, model, _, _ = run(graph=doc_graph(modules=1, per=1, filler=14))
    body = " ".join(text for _, _, text in passages(model.calls[0].prompt))
    assert body.count("Alpha ví dụ số") <= 2


def test_search_failure_still_gives_a_document_and_is_logged():
    result, _, store, model, _, _ = run(search=Search(error=RuntimeError("mạng")))
    assert result["status"] == "ready"
    assert "TRUYVAN" not in model.calls[0].prompt.split("Tư liệu từ sách:", 1)[1].replace("Ghi chú đặc biệt về", "")
    assert validation_of(store, result)["search_error"] is True


# ---------------------------------------------------------------- 2. formulas: raw text and page pictures

def test_each_formula_mark_becomes_its_raw_text_and_exactly_the_formula_pages_get_a_picture_up_to_eight():
    order = [40, 12, 13, 14, 15, 16, 17, 18, 19, 20]
    pages = FakePages({page: JPEG + page.to_bytes(2, "big") for page in range(1, 400)})
    result, _, store, model, _, _ = run(graph=doc_graph(formula_pages=order, raw="x²  +\ny{}"), pages=pages)
    prompt = model.calls[0].prompt
    assert "[formula: x² + y40]" in prompt and "[formula: x² + y20]" in prompt and "[formula]" not in prompt
    sent = [page for page, _ in model.calls[0].images]
    assert sent == order[:8]
    assert [call[2] for call in pages.calls] == sent
    assert all(data == JPEG + page.to_bytes(2, "big") for page, data in model.calls[0].images)
    assert 100 not in sent                                  # the definition page holds no [formula]
    log = validation_of(store, result)
    assert log["pages_with_formula"] == 10 and log["images_sent"] == 8 and log["thieu_anh_trang"] is True


def test_no_formula_in_the_material_means_no_picture_is_read_or_sent():
    pages = FakePages({page: JPEG for page in range(1, 400)})
    result, _, store, model, _, _ = run(pages=pages)
    assert result["status"] == "ready"
    assert pages.calls == [] and model.calls[0].images == []
    assert validation_of(store, result)["thieu_anh_trang"] is False
    assert "Dựng lại công thức từ chữ trích thô" in model.calls[0].system


def test_missing_pictures_still_give_a_document_with_the_text_only_rule_and_a_log():
    result, _, store, model, _, _ = run(graph=doc_graph(formula_pages=[40]), pages=FakePages({}))
    assert result["status"] == "ready" and model.calls[0].images == []
    assert "[formula: RAW40]" in model.calls[0].prompt
    assert validation_of(store, result)["thieu_anh_trang"] is True
    assert "Ảnh các trang sách được đính kèm" not in model.calls[0].system


# ---------------------------------------------------------------- 3. the prompt, word for word

def spec_prompt():
    section = SPEC.split("### 3. Lời nhắc", 1)[1]
    return re.search(r"```text\n(.*?)\n```", section, flags=re.S).group(1)


def formula_rule(number):
    return re.search(rf"- Luật {number}, khi [^:]*: `(.*?)`\n", SPEC_LECTURE).group(1)


def test_system_prompt_is_the_spec_text_with_the_formula_rule_of_the_lecture_spec():
    template = spec_prompt()
    assert "{formula_rule}" in template
    pages = FakePages({40: JPEG})
    with_images = run(graph=doc_graph(formula_pages=[40]), pages=pages)[3].calls[0].system
    text_only = run()[3].calls[0].system
    assert with_images == template.replace("{formula_rule}", formula_rule(1))
    assert text_only == template.replace("{formula_rule}", formula_rule(2))


def test_call_uses_temperature_one_and_streams_text_with_a_long_timeout():
    _, _, _, model, _, _ = run()
    call = model.calls[0]
    assert call.temperature == 1.0 and call.timeout_seconds > 60 and call.extra == {}


# ---------------------------------------------------------------- 4. the document is the model's text

def test_markdown_is_exactly_what_the_model_wrote_and_the_checks_live_only_in_the_log():
    written = ("# Tài liệu thử\n\nCâu này không có nhãn và dài hơn bốn từ đâu. Công thức $a^2 + b^2$ ở đây.\n\n"
               "Nhãn lạ ở cuối đoạn này [S99].\n\nCòn sót [formula: x] ở đây [S1].\n")
    result, _, store, _, _, use_case = run(FakeModel(list_pieces(written)))
    assert result["markdown"] == written
    log = validation_of(store, result)
    assert log["unknown_labels"] == ["S99"] and log["labels_used"] == ["S1", "S99"]
    assert log["unsourced_sentences"] >= 1 and log["formula_left"] is True and log["has_formula"] is True
    assert log["words"] > 10 and log["finish_reason"] == "STOP"
    assert log["seconds_to_first_text"] is not None and log["seconds_total"] is not None
    assert use_case.get(result["document_id"], owner="alice")["markdown"] == written


def test_checker_and_json_machinery_of_document_2_are_never_called(monkeypatch):
    from doc2roadmap.application.phase_b import common, postcheck

    def boom(*args, **kwargs):
        raise AssertionError("document-2 machinery was called")
    for module, name in ((postcheck, "check_text"), (postcheck, "best_matching_source_sentence"),
                         (common, "call_json"), (common, "quote_is_verbatim")):
        monkeypatch.setattr(module, name, boom)
    import doc2roadmap.application.phase_b.documents as documents
    for name in ("check_text", "call_json", "quote_is_verbatim", "best_matching_source_sentence"):
        if hasattr(documents, name):
            monkeypatch.setattr(documents, name, boom)
    result = run(FakeModel(list_pieces("# T\n\nSai nhãn [S77]. Không nhãn.")))[0]
    assert result["status"] == "ready" and result["markdown"] == "# T\n\nSai nhãn [S77]. Không nhãn."


def test_contract_has_no_document_2_fields_and_lists_the_sources_that_were_sent():
    result, _, _, model, _, _ = run()
    assert result["contract_version"] == "document-3"
    assert not {"validation", "citations", "outside_document_blocks", "postcheck", "reason"} & set(result)
    assert result["failure"] is None and result["status"] == "ready" and result["warnings"] == []
    assert result["scope"]["module_ids"] == ["m0", "m1", "m2"] and result["origin"] == "button"
    assert result["session_id"] is None and result["home_scope"] == {"kind": "roadmap"}
    assert result["request"] == "Tóm tắt TRUYVAN" and result["graph_version"] == "g1"
    assert [row["label"] for row in result["sources"]] == [label for label, _, _ in passages(model.calls[0].prompt)]
    assert set(result["sources"][0]) == {"label", "chunk_id", "page", "section_path"}
    assert {"model_id", "cost_usd", "elapsed_ms", "input_tokens", "output_tokens"} <= set(result["usage"])


# ---------------------------------------------------------------- 5. text arrives while the model is writing

def test_first_text_reaches_the_caller_before_the_model_has_finished_and_events_are_in_order():
    seen = {}
    events = []

    def script():
        yield "# Tiêu đề\n\n"
        seen["after_first_piece"] = [e["event"] for e in events]
        yield "Phần hai. [S1]"
        seen["after_second_piece"] = "".join(e.get("text", "") for e in events if e["event"] == "delta")

    model = FakeModel(script)
    store, graph = InMemoryPhaseBStore(), doc_graph()
    use_case = DocumentUseCase(model, store, search=Search(), clock=FakeClock())
    result = use_case.create("d1", "g1", graph, "Hỏi", {"module_ids": ["m0"]}, owner="alice", allow_spend=True,
                             on_event=events.append)
    assert seen["after_first_piece"] == ["skeleton", "delta"]
    assert seen["after_second_piece"].startswith("# Tiêu đề")
    assert [e["event"] for e in events][-1] == "final" and events[0] == {
        "event": "skeleton", "document_id": result["document_id"], "title": None}
    assert "".join(e["text"] for e in events if e["event"] == "delta") == result["markdown"]
    assert events[-1]["document"] == result


# ---------------------------------------------------------------- 6. empty output, cut output

def test_empty_output_is_generated_once_more_then_fails_as_not_usable_and_retryable():
    result, events, store, model, _, _ = run(FakeModel([" \n"], []))
    assert len(model.calls) == 2
    assert result["status"] == "failed" and result["markdown"] == ""
    assert result["failure"]["reason_code"] == "khong_dung_duoc" and result["failure"]["retryable"] is True
    assert result["failure"]["message"]
    assert [e["event"] for e in events][-1] == "failure" and events[-1]["document"] == result
    assert len([r for r in store.usage_rows("d1") if r["purpose"] == "document"]) == 2
    assert store.get_record("documents", result["document_id"])["status"] == "failed"


def test_second_try_after_an_empty_one_gives_the_document():
    result, _, _, model, _, _ = run(FakeModel([], list_pieces(GOOD_DOC)))
    assert len(model.calls) == 2 and result["status"] == "ready" and result["markdown"] == GOOD_DOC


def test_error_after_some_text_keeps_the_text_as_a_ready_cut_document():
    result, events, store, model, _, _ = run(FakeModel(["# Tiêu đề\n\nĐã viết được một nửa ", RuntimeError("đứt")]))
    assert len(model.calls) == 1
    assert result["status"] == "ready" and result["failure"] is None
    assert result["markdown"] == "# Tiêu đề\n\nĐã viết được một nửa " and "cat_ngan" in result["warnings"]
    assert result["title"] == "Tiêu đề"
    assert events[-1]["event"] == "final"
    assert store.get_record("documents", result["document_id"])["status"] == "ready"


@pytest.mark.parametrize("error,code", [(RuntimeError("mạng"), "loi_mang"), (TimeoutError("lâu"), "het_thoi_gian")])
def test_error_before_any_text_fails_with_the_reason_and_no_second_call(error, code):
    result, _, store, model, _, _ = run(FakeModel([error]))
    assert len(model.calls) == 1 and result["status"] == "failed" and result["markdown"] == ""
    assert result["failure"]["reason_code"] == code and result["failure"]["retryable"] is True


def test_no_model_fails_with_its_own_reason_without_a_call():
    store = InMemoryPhaseBStore()
    result = DocumentUseCase(None, store, search=Search(), clock=FakeClock()).create(
        "d1", "g1", doc_graph(), "Hỏi", {"module_ids": ["m0"]}, owner="alice", allow_spend=True)
    assert result["status"] == "failed" and result["failure"]["reason_code"] == "khong_co_mo_hinh"


def test_cut_by_the_output_limit_is_marked_cut():
    model = FakeModel(list_pieces(GOOD_DOC))
    original = model.start_session

    def start(system, tools=()):
        session = original(system, tools)
        real = session.stream_text

        def stream(*args, **kwargs):
            yield from real(*args, **kwargs)
            session.last_finish_reason = "MAX_TOKENS"
        session.stream_text = stream
        return session
    model.start_session = start
    result = run(model)[0]
    assert result["status"] == "ready" and "cat_ngan" in result["warnings"]


# ---------------------------------------------------------------- 7. scope and budget gates

def test_more_than_five_modules_fails_before_any_call_search_picture_or_spend():
    graph = doc_graph(modules=6, per=1)
    pages, search = FakePages({}), Search()
    result, events, store, model, _, _ = run(graph=graph, pages=pages, search=search)
    assert result["status"] == "failed" and result["failure"]["reason_code"] == "scope_too_large"
    assert result["failure"]["retryable"] is False and result["usage"] == {}
    assert model.calls == [] and search.calls == [] and pages.calls == []
    assert store.usage_rows("d1") == [] and store.list_records("spend_reservation") == []
    assert [e["event"] for e in events] == ["failure"]


def test_five_modules_are_allowed():
    result = run(graph=doc_graph(modules=5, per=1))[0]
    assert result["status"] == "ready" and len(result["scope"]["module_ids"]) == 5


def test_learner_over_the_daily_cap_gets_daily_limit_without_a_call():
    settings = replace(BSettings(), learner_daily_max_usd=0.0000001)
    result, events, store, model, _, _ = run(settings=settings)
    assert result["status"] == "failed" and result["failure"]["reason_code"] == "daily_limit"
    assert model.calls == [] and result["usage"] == {}
    assert store.get_record("documents", result["document_id"])["failure"]["reason_code"] == "daily_limit"
    assert [e["event"] for e in events][-1] == "failure"


def test_spend_guard_is_asked_once_for_the_learner_with_the_document_purpose():
    class Guard:
        checks = []

        def check(self, purpose, estimated_usd, owner=None):
            self.checks.append((purpose, estimated_usd, owner))
            return False
    guard = Guard()
    result, _, _, model, _, _ = run(guard=guard)
    assert result["failure"]["reason_code"] == "daily_limit" and model.calls == []
    assert [(p, o) for p, _, o in guard.checks] == [("document", "alice")]


def test_estimated_cost_over_the_limit_fails_before_the_call_at_zero_usd():
    settings = replace(BSettings(), document_max_usd=0.0001)
    result, _, store, model, _, _ = run(settings=settings)
    assert result["failure"]["reason_code"] == "estimated_cost_over_limit" and result["usage"] == {}
    assert model.calls == [] and store.usage_rows("d1") == []


def test_estimate_counts_text_a_third_and_thirteen_hundred_tokens_per_picture():
    pages = FakePages({40: JPEG})
    plain = run(graph=doc_graph(formula_pages=[40]), settings=replace(BSettings(), document_max_usd=1.0))
    dry = run(graph=doc_graph(formula_pages=[40]), pages=pages, dry_run=True, settings=replace(BSettings(), document_max_usd=1.0))
    assert plain[3].calls and dry[0]["dry_run"] is True and dry[3].calls == []
    base = run(graph=doc_graph(formula_pages=[40]), dry_run=True)[0]["estimate_usd"]
    assert dry[0]["estimate_usd"] > base
    from doc2roadmap.application.phase_b.document_context3 import system_prompt
    from doc2roadmap.domain.phase_b_pricing import estimate_cost
    extra_tokens = 1300 + (len(system_prompt(True)) - len(system_prompt(False))) // 3
    assert dry[0]["estimate_usd"] - base == pytest.approx(estimate_cost(BSettings().model_id, extra_tokens, 0))


def test_dry_run_makes_no_call_and_stores_nothing():
    result, events, store, model, _, _ = run(dry_run=True)
    assert result["dry_run"] is True and result["status"] == "generating" and result["estimate_usd"] > 0
    assert model.calls == [] and store.list_records("documents") == [] and events == []


def test_usage_rows_and_the_document_record_are_written_per_attempt():
    result, _, store, _, _, _ = run()
    rows = [r for r in store.usage_rows("d1") if r["purpose"] == "document"]
    assert len(rows) == 1 and rows[0]["learner_id"] == "alice" and rows[0]["cost_usd"] > 0
    assert result["usage"]["cost_usd"] == pytest.approx(rows[0]["cost_usd"])
    assert store.get_record("documents", result["document_id"]) == result


# ---------------------------------------------------------------- 8. validation never reaches the learner

def test_validation_is_in_no_learner_facing_output():
    result, events, store, _, _, use_case = run()
    assert validation_of(store, result) is not None
    assert "validation" not in keys_anywhere(result)
    assert "validation" not in keys_anywhere([e for e in events])
    assert "validation" not in keys_anywhere(store.get_record("documents", result["document_id"]))
    assert "validation" not in keys_anywhere(use_case.get(result["document_id"], owner="alice"))


def test_make_document_tool_result_carries_no_validation_and_only_artifact_title_status():
    from tests.unit.application.test_phase_b_assistant_sa66 import Model, ask, seed, turn
    graph, store = doc_graph(modules=2, per=1, doc_id="book"), InMemoryPhaseBStore()
    seed(store, graph, "m0")
    made = []

    def make_document(request, scope, *, owner, **kwargs):
        made.append(DocumentUseCase(FakeModel(list_pieces(GOOD_DOC)), store, search=Search(), clock=FakeClock()).create(
            "book", "g1", graph, request, scope, owner=owner, origin="assistant", allow_spend=True,
            home_scope=kwargs.get("home_scope"), session_id=kwargs.get("session_id")))
        return made[-1]
    model = Model([[ToolCall("make_document", {"request": "Đề cương", "scope": "module 1"}, "1"), Done({})], turn("Xong.")])
    result = ask(AssistantUseCase(graph, store, model, document=make_document, search=lambda *a, **k: []), "Tạo giúp")
    summary = result["tool_calls"][0]["result_summary"]
    assert summary == {"artifact": {"kind": "document", "id": made[0]["document_id"]},
                       "title": "Đề cương ôn tập", "status": "ready"}
    assert "validation" not in keys_anywhere(result)


def test_failed_document_tool_result_reports_the_reason_code_of_the_failure_block():
    from tests.unit.application.test_phase_b_assistant_sa66 import Model, ask, seed, turn
    graph, store = doc_graph(modules=2, per=1, doc_id="book"), InMemoryPhaseBStore()
    seed(store, graph, "m0")

    def make_document(request, scope, *, owner, **kwargs):
        return DocumentUseCase(FakeModel(), store, settings=BSettings(document_max_modules=1), clock=FakeClock()).create(
            "book", "g1", graph, request, scope, owner=owner, origin="assistant", allow_spend=True)
    model = Model([[ToolCall("make_document", {"request": "Tất cả", "scope": "roadmap"}, "1"), Done({})], turn("Xong.")])
    summary = ask(AssistantUseCase(graph, store, model, document=make_document, search=lambda *a, **k: []),
                  "Tạo giúp")["tool_calls"][0]["result_summary"]
    assert summary["error"]["code"] == "scope_too_large"
    assert summary["error"]["message"].startswith("Chọn tối đa")


# ---------------------------------------------------------------- 9. title

@pytest.mark.parametrize("text,title", [
    ("# Đề cương ôn tập\n\nNội dung.", "Đề cương ôn tập"),
    ("Lời dẫn.\n\n# Tiêu đề muộn\n\nNội dung.\n\n# Tiêu đề hai", "Tiêu đề muộn"),
    ("## Mục nhỏ\n\nNội dung #1 không phải tiêu đề.", "Tài liệu học tập"),
    ("Chỉ có văn bản.", "Tài liệu học tập"),
    ("#Không có dấu cách\n\nx", "Tài liệu học tập"),
])
def test_title_is_the_first_level_one_heading_else_the_default(text, title):
    result = run(FakeModel(list_pieces(text)))[0]
    assert result["title"] == title and result["markdown"] == text


# ---------------------------------------------------------------- 10. export with page footnotes

def test_export_turns_labels_into_footnotes_with_page_section_and_chunk():
    result, _, _, _, _, use_case = run(FakeModel(list_pieces(
        "# Đề cương\n\nA là gì. [S1]\n\nB và C. [S2, S3]\n\nNhãn lạ [S99].\n")))
    exported = use_case.export(result["document_id"], owner="alice")
    rows = {row["label"]: row for row in result["sources"]}
    assert "A là gì. [^S1]" in exported and "B và C. [^S2][^S3]" in exported
    assert "[S99]" in exported and "[^S99]" not in exported
    for label in ("S1", "S2", "S3"):
        row = rows[label]
        section = " › ".join(row["section_path"])
        assert f"[^{label}]: tr. {row['page']}, {section} (đoạn {row['chunk_id']})" in exported
    assert "[^S4]:" not in exported                          # sent but never cited
    assert exported.endswith("\n") and exported.startswith("# Đề cương")


def test_export_is_owner_only():
    result, _, _, _, _, use_case = run()
    assert use_case.get(result["document_id"], owner="bob") is None
    with pytest.raises(KeyError):
        use_case.export(result["document_id"], owner="bob")


# ---------------------------------------------------------------- inputs kept from document-2

def test_owner_and_doc_id_and_origin_are_still_checked():
    graph, store = doc_graph(), InMemoryPhaseBStore()
    use_case = DocumentUseCase(FakeModel(), store, search=Search(), clock=FakeClock())
    with pytest.raises(PermissionError):
        use_case.create("d1", "g1", graph, "x", "m0", owner="", allow_spend=True)
    with pytest.raises(ValueError):
        use_case.create("khác", "g1", graph, "x", "m0", owner="a", allow_spend=True)
    with pytest.raises(ValueError):
        use_case.create("d1", "g1", graph, "x", "m0", owner="a", allow_spend=True, origin="web")


def test_assistant_origin_keeps_session_and_home_scope_and_button_drops_the_session():
    home = {"kind": "module", "node_ids": ["n0"]}
    a = run(origin="assistant", session_id="s1", home_scope=home)[0]
    b = run(origin="button", session_id="s1")[0]
    assert (a["origin"], a["session_id"], a["home_scope"]) == ("assistant", "s1", home)
    assert (b["origin"], b["session_id"]) == ("button", None)
