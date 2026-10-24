from types import SimpleNamespace as NS

from sa64_support import FakeClock, FakeModel, list_pieces

from doc2roadmap.application.phase_b.documents import DocumentUseCase
from doc2roadmap.application.phase_b.postcheck import check_text
from doc2roadmap.domain.learning_graph import LearningGraph
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.domain.source_labels import SourceRegistry
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore


def _graph(text):
    chunk = NS(chunk_id="c1", text=text, page=3, char_start=40,
               char_end=40 + len(text), section_path=["Phần I"], order_index=1, role="noi_dung")
    payload = {
        "doc_id": "book",
        "nodes": [{"node_id": "n1", "name": "Khái niệm", "learnable": True,
                   "module_id": "m1", "teaching_chunk_ids": ["c1"]}],
        "modules": [{"module_id": "m1", "index": 0, "title": "Khái niệm", "node_ids": ["n1"]}],
        "requires_edges": [],
    }
    graph = LearningGraph(payload, [chunk])
    graph.sources.label("c1", "S")
    return graph


def test_document_removes_heading_without_retained_body_and_punctuation_only_lines():
    graph = _graph("Khái niệm được trình bày trong đoạn này.")
    result = check_text(
        "## Hạn chế\n\nKhông có nguồn [S999].\n\n.\n\n## Định nghĩa\n\n"
        "Khái niệm được trình bày trong đoạn này [S1].",
        graph=graph, settings=BSettings(),
        citations_by_label={"S1": graph.sources.citation("S1", "Khái niệm được trình bày trong đoạn này.")},
    )

    assert "## Hạn chế" not in result["text"]
    assert "## Định nghĩa" in result["text"]
    assert "Không có nguồn" not in result["text"]
    assert not any(line.strip() == "." for line in result["text"].splitlines())
    assert result["counts"]["empty_heading_removed"] == 1


def test_failed_document_has_no_title_and_no_text_when_the_model_wrote_nothing():
    # SA-67 (was: a failed document rendered no title when every sentence was deleted). document-3 fails only on no text.
    graph = _graph("Khái niệm được trình bày trong đoạn này.")
    result = DocumentUseCase(FakeModel([]), InMemoryPhaseBStore(), clock=FakeClock()).create(
        "book", 1, graph, "Giải thích khái niệm", "n1", owner="learner", allow_spend=True)

    assert result["status"] == "failed"
    assert not result["markdown"].strip() and not result["title"]


def test_document_keeps_a_nonverbatim_quote_claim_and_a_fake_label_as_written():
    # SA-67 (was: the quote of a valid label was repaired and the fake label dropped). No quotes exist any more:
    # the text is kept, the fake label is only logged for the admin.
    graph = _graph("Khái niệm A được xác định bằng các thuộc tính và quan hệ. Khái niệm B có ví dụ khác.")
    written = "Khái niệm A được xác định qua nhiều điều [S1]. Một trích dẫn bịa [S999]."
    store = InMemoryPhaseBStore()
    result = DocumentUseCase(FakeModel(list_pieces(written)), store, clock=FakeClock()).create(
        "book", 1, graph, "Giải thích khái niệm A", "n1", owner="learner", allow_spend=True)

    assert result["status"] == "ready" and result["markdown"] == written
    assert [row["label"] for row in result["sources"]] == ["S1"]
    assert result["usage"]["ttft_ms"] is not None
    assert store.get_record("document_validation", result["document_id"])["unknown_labels"] == ["S999"]


def test_document_compound_label_is_read_as_its_parts_and_the_fake_part_is_logged():
    graph = _graph("Khái niệm A có liên hệ trực tiếp với X. Khái niệm A được xác định bằng các thuộc tính B và C.")
    written = "Các thuộc tính B và C xác định khái niệm A. [S1, S999]"
    store = InMemoryPhaseBStore()
    result = DocumentUseCase(FakeModel(list_pieces(written)), store, clock=FakeClock()).create(
        "book", 1, graph, "Giải thích khái niệm A", "n1", owner="learner", allow_spend=True)

    assert result["status"] == "ready" and result["markdown"] == written
    log = store.get_record("document_validation", result["document_id"])
    assert log["labels_used"] == ["S1", "S999"] and log["unknown_labels"] == ["S999"]


def _why_quote(quote, limit=None):
    chunks = [NS(chunk_id="edge", text=quote, page=1, char_start=100,
                 char_end=100 + len(quote), section_path=["Chương 1"]),
              NS(chunk_id="anchor", text="A là nền tảng.", page=1, char_start=0,
                 char_end=14, section_path=["Chương 1"])]
    graph = LearningGraph({
        "nodes": [
            {"node_id": "a", "name": "A", "learnable": True, "module_id": "m1",
             "anchor": {"chunk_id": "anchor", "sentence": "A là nền tảng."}},
            {"node_id": "b", "name": "B", "learnable": True, "module_id": "m2",
             "display_prerequisites": ["a"]},
        ],
        "modules": [{"module_id": "m1", "index": 0}, {"module_id": "m2", "index": 1}],
        "requires_edges": [{"source": "a", "target": "b", "edge_type": "requires",
                            "chunk_ids": ["edge"], "quote": quote}],
    }, chunks)
    if limit is None:
        return graph.why_here("b", source_registry=SourceRegistry(chunks))
    settings = BSettings(quote_max_chars=limit)
    return graph.why_here("b", source_registry=SourceRegistry(chunks), settings=settings)


def test_180_character_edge_quote_is_not_truncated_by_old_120_character_limit():
    quote = ("từ " * 58) + "abcde."
    assert len(quote) == 180
    row = _why_quote(quote)["prerequisites"][0]

    assert row["quote"] == quote
    assert len(row["quote"]) <= BSettings().quote_max_chars


def test_long_edge_quote_truncates_at_sentence_boundary_and_keeps_exact_offsets():
    first_sentence = ("từ " * 58) + "kết."
    assert len(first_sentence) == 178
    quote = first_sentence + " " + ("dài " * 20) + "sau."
    row = _why_quote(quote)["prerequisites"][0]
    citation = row["citation"]
    source = quote
    start = citation["char_start"] - 100
    end = citation["char_end"] - 100

    assert row["quote"] == first_sentence
    assert source[start:end] == row["quote"]
    assert len(row["quote"]) <= BSettings().quote_max_chars


def test_edge_quote_uses_configured_quote_max_chars():
    first_sentence = "một câu nguồn trọn vẹn."
    quote = first_sentence + " " + ("thêm chữ " * 20)
    row = _why_quote(quote, limit=40)["prerequisites"][0]

    assert row["quote"] == first_sentence
    assert len(row["quote"]) <= 40


def test_long_single_sentence_quote_stops_at_word_boundary_with_exact_offsets():
    quote = ("từ " * 90) + "cuối."
    row = _why_quote(quote)["prerequisites"][0]
    citation = row["citation"]
    cited = quote[citation["char_start"] - 100:citation["char_end"] - 100]

    assert row["quote"] == cited
    assert len(row["quote"]) <= BSettings().quote_max_chars
    assert quote[len(row["quote"]):].startswith(" ")
