from doc2roadmap.application.phase_b.naming import NameModulesB
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore
from test_phase_b_naming_sa28 import CaptureModel, one_module_graph, response
from test_phase_b_naming import Store


def test_bad_description_keeps_valid_llm_title_and_marks_only_description_fallback():
    graph = one_module_graph()
    model = CaptureModel([response("Ma trận", "Ma trận foobarbaz.", "n0a")])

    result, _ = NameModulesB(Store(), model, phase_b_store=InMemoryPhaseBStore(), allow_spend=True).execute(
        "book", upstream=graph)

    module = result.payload["modules"][0]
    assert module["title"] == "Ma trận"
    assert module["title_source"] == "llm"
    assert module["description_source"] == "template"
    assert module["description"][0]["text"].startswith("Học:")
    assert module["naming_flags"] == ["description_vocabulary"]


def test_bad_title_keeps_valid_llm_description():
    graph = one_module_graph()
    description = "Ma trận biểu diễn hệ số của hệ tuyến tính."
    model = CaptureModel([response("Khái niệm", description, "n0a")])

    result, _ = NameModulesB(Store(), model, phase_b_store=InMemoryPhaseBStore(), allow_spend=True).execute(
        "book", upstream=graph)

    module = result.payload["modules"][0]
    assert module["title_source"] == "fallback"
    assert module["description_source"] == "llm"
    assert module["description"][0]["text"] == description
    assert module["naming_flags"] == ["generic_title"]


def test_description_accepts_syllables_from_target_teaching_chunks():
    graph = one_module_graph()
    store = Store()
    store.chunks.result.chunks[0].text = "Ma trận dạy."
    model = CaptureModel([response("Ma trận", "Ma trận dạy.", "n0a")])

    result, _ = NameModulesB(store, model, phase_b_store=InMemoryPhaseBStore(), allow_spend=True).execute(
        "book", upstream=graph)

    module = result.payload["modules"][0]
    assert module["title_source"] == "llm"
    assert module["description_source"] == "llm"


def test_common_chunk_ratio_changes_book_vocabulary_threshold():
    graph = one_module_graph()
    graph.payload["nodes"][0]["teaching_chunk_ids"] = []
    store = Store()
    chunks = store.chunks.result.chunks
    for index, chunk in enumerate(chunks):
        chunk.text = "sachwide noi dung" if index < 3 else "khac"
    for index in range(3, 150):
        clone = __import__("copy").deepcopy(chunks[0])
        clone.chunk_id = f"extra-{index}"
        clone.order_index = index
        clone.text = "khac"
        chunks.append(clone)

    low_ratio = NameModulesB(store, settings=BSettings(naming_common_chunk_ratio=0.02))
    high_ratio = NameModulesB(store, settings=BSettings(naming_common_chunk_ratio=0.04))
    _, prepared = low_ratio._prepare("book", graph)
    low_vocab, _ = low_ratio._description_lexicons(store.chunks, prepared, graph)
    high_vocab, _ = high_ratio._description_lexicons(store.chunks, prepared, graph)

    assert "sachwide" in low_vocab[0]
    assert "sachwide" not in high_vocab[0]


def test_description_rejects_neighbor_concept_token_as_borrowed():
    from test_phase_b_naming import upstream

    graph = upstream()
    graph.payload["nodes"][0]["display_name"] = "Ma trận xylophone"
    for node in graph.payload["nodes"][2:4]:
        node["teaching_chunk_ids"] = []
    store = Store()
    for chunk in store.chunks.result.chunks:
        chunk.text = "xylophone"
    outputs = [response("Ma trận", "Ma trận.", "n0a"),
               response("Định thức", "Định thức xylophone.", "n1a"),
               response("Hệ phương trình", "Hệ phương trình.", "n2a")]

    result, _ = NameModulesB(store, CaptureModel(outputs), phase_b_store=InMemoryPhaseBStore(),
                             allow_spend=True).execute("book", upstream=graph)

    central = result.payload["modules"][1]
    assert central["title"] == "Định thức"
    assert central["title_source"] == "llm"
    assert central["description_source"] == "template"
    assert "description_borrowed" in central["naming_flags"]


def test_new_prompt_bans_self_reference_and_sends_content_without_frequency_list():
    sentence = "Ma trận biểu diễn hệ số trong hệ tuyến tính."
    graph = one_module_graph(description=sentence)
    model = CaptureModel([response("Ma trận", sentence, "n0a")])

    NameModulesB(Store(), model, phase_b_store=InMemoryPhaseBStore(), allow_spend=True).execute(
        "book", upstream=graph)

    prompt = model.system_prompts[0].casefold()
    request = model.requests[0]
    assert "không tự xưng" in prompt
    assert "module này" in prompt and "chương này" in prompt and "bài này" in prompt and "nội dung" in prompt
    assert "từ thông dụng" in prompt
    assert "content_vocabulary" in request
    assert "function_words" not in request and "allowed_vocabulary" not in request
    assert "dạy" in prompt and "việc đó dùng để làm gì" in prompt
