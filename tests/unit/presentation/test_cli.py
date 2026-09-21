from pathlib import Path
from types import SimpleNamespace

from doc2roadmap.domain.chunking import chunk_document
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore
from doc2roadmap.presentation.cli.main import _ingest, _inspect, _parser, main

from tests.conftest import WordCounter, reference_tree, splitter


def test_inspect_shows_tree_empty_sections_and_direct_windows(tmp_path, monkeypatch, capsys) -> None:
    result = chunk_document(reference_tree(), "book", WordCounter(), splitter())
    store = JsonArtifactStore(tmp_path)
    store.save_chunks("book", "source", "config", {}, 1, result)
    monkeypatch.setenv("DOC2ROADMAP_ARTIFACT_DIR", str(tmp_path))

    _inspect("book")

    output = capsys.readouterr().out
    assert "- <document> (<document>) [không có nội dung trực tiếp]" in output
    assert "  - Chương 2: Mô hình ngôn ngữ" in output
    assert "Windows:" in output
    chapter = next(section for section in result.sections if section.title.startswith("Chương 2"))
    architecture = next(section for section in result.sections if section.title.startswith("2.1 Kiến"))
    chapter_window = output.split(f"[{chapter.section_id}]", 1)[1].split(
        f"[{architecture.section_id}]", 1
    )[0]
    assert "Chương này trình bày" in chapter_window
    assert "Ta bắt đầu" in chapter_window
    assert "Transformer bỏ hồi quy" not in chapter_window
    assert "Cảnh báo: không" in output


def test_ingest_prints_each_warning_and_parse_stats(tmp_path, monkeypatch, capsys) -> None:
    source = tmp_path / "book.pdf"
    source.write_bytes(b"pdf")
    calls = []

    class UseCase:
        def execute(self, *args, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(
                doc_id="book",
                section_count=2,
                chunk_count=3,
                window_count=1,
                source_seen_before=False,
                structure_warnings=[
                    "rejected_heading: trong đó:",
                    "sentence_splitter_no_boundary: page 7",
                ],
                parse_stats={
                    "items_total": 5,
                    "nodes_kept": 3,
                    "dropped": {"caption": 1, "formula": 1},
                    "captions": {"total": 2, "recovered": 1, "orphaned": 1},
                    "images_extracted": 2,
                },
                artifact_path=Path("artifacts/chunks/book/v1"),
            )

    settings = SimpleNamespace(
        max_tokens=512,
        max_table_tokens=2048,
        hard_cap_tokens=6000,
        target_tokens=256,
        sentence_overlap=1,
    )
    monkeypatch.setattr("doc2roadmap.presentation.cli.main.build_ingest", lambda: (UseCase(), settings))

    _ingest(source, "book", strip_lines=["first", "second"])

    output = capsys.readouterr().out
    assert calls[0]["strip_lines"] == ["first", "second"]
    assert "parse: giữ 3/5; bỏ: caption=1, formula=1" in output
    assert "stitch=0; sắp lại trang=0" in output
    assert "media: ảnh=2; chú thích=2 (lấy lại=1, mồ côi=1)" in output
    assert "Cảnh báo:" in output
    assert "- rejected_heading: trong đó:" in output
    assert "- sentence_splitter_no_boundary: page 7" in output


def test_parser_exposes_repeatable_a3_operations() -> None:
    parser = _parser()

    ingest = parser.parse_args([
        "ingest", "book.pdf", "--doc-id", "book",
        "--strip-line", "first", "--strip-line", "second",
    ])
    assert ingest.strip_line == ["first", "second"]

    extract = parser.parse_args(
        ["extract", "--doc-id", "book", "--few-shot", "prompts/fine.txt"]
    )
    assert extract.command == "extract"
    assert extract.few_shot == Path("prompts/fine.txt")
    assert parser.parse_args(["index", "--doc-id", "book"]).command == "index"
    a3 = parser.parse_args(
        ["a3", "--doc-id", "book", "--few-shot", "prompts/coarse.txt"]
    )
    assert a3.few_shot == Path("prompts/coarse.txt")
    search = parser.parse_args(
        ["search", "Naïve Bayes", "--doc-id", "book", "--stage-id", "s1"]
    )
    assert search.query == "Naïve Bayes" and search.stage_id == ["s1"]
    report = parser.parse_args(["a3-report", "--doc-id", "a", "--doc-id", "b"])
    assert report.doc_id == ["a", "b"]
    compare = parser.parse_args(
        ["a3-compare", "--doc-id", "book", "--first", "1", "--second", "2"]
    )
    assert (compare.first, compare.second) == (1, 2)
    evaluate = parser.parse_args(
        ["a3-evaluate", "--doc-id", "book", "--gold", "gold.json"]
    )
    assert evaluate.gold == Path("gold.json")
    a4_evaluate = parser.parse_args([
        "a4-evaluate", "--doc-id", "book", "--gold", "gold.json",
        "--exclude-subtype-item", "first", "--exclude-subtype-item", "second",
    ])
    assert a4_evaluate.exclude_subtype_item == ["first", "second"]
    a4_new = parser.parse_args([
        "a4", "--doc-id", "new-book", "--gold", "gold.json", "--no-gold-for-doc",
    ])
    assert a4_new.no_gold_for_doc is True


def test_a4_new_document_requires_explicit_gold_exception(monkeypatch, capsys) -> None:
    calls = []
    gold_calls = []

    class UseCase:
        def execute(self, doc_id, **kwargs):
            calls.append((doc_id, kwargs))
            return SimpleNamespace(
                path=Path("artifact"), version=1,
                payload={"stage": "complete", "stats": {}, "cost_summary": {}},
            ), False

    monkeypatch.setattr("doc2roadmap.presentation.cli.main.build_artifact_store", lambda: object())
    monkeypatch.setattr("doc2roadmap.presentation.cli.main.build_canonical", lambda: UseCase())
    def load_gold(*args, **kwargs):
        gold_calls.append(kwargs)
        return {"documents": {"old-book": {}}, "sheet_id": "frozen-sheet"}

    monkeypatch.setattr("doc2roadmap.presentation.cli.main.load_gold", load_gold)

    base = ["a4", "--doc-id", "new-book", "--gold", "gold.json"]
    assert main(base) == 2
    assert "bộ vàng không có tài liệu này" in capsys.readouterr().err
    assert calls == []

    assert main([*base, "--no-gold-for-doc"]) == 0
    assert calls == [(
        "new-book",
        {"a4_gold_coverage": "none", "gold_sheet_id": "frozen-sheet"},
    )]
    assert gold_calls == [{"require_complete": True}, {"require_complete": True}]


def test_extract_cli_forwards_few_shot_override(monkeypatch) -> None:
    selected = []

    class UseCase:
        def execute(self, *args, **kwargs):
            return object()

    def build(*, few_shot_path=None):
        selected.append(few_shot_path)
        return UseCase(), SimpleNamespace(extraction_concurrency=1)

    monkeypatch.setattr("doc2roadmap.presentation.cli.main.build_extract", build)
    monkeypatch.setattr("doc2roadmap.presentation.cli.main._print_extraction", lambda summary: None)

    assert main(
        ["extract", "--doc-id", "book", "--few-shot", "prompts/fine.txt"]
    ) == 0
    assert selected == [Path("prompts/fine.txt")]


def test_a3_cli_forwards_few_shot_override(monkeypatch) -> None:
    selected = []

    class UseCase:
        def execute(self, *args, **kwargs):
            return object()

    class Index:
        def execute(self, doc_id):
            return SimpleNamespace(payload={"documents": []})

    def build(*, few_shot_path=None):
        selected.append(few_shot_path)
        return UseCase(), Index(), SimpleNamespace(extraction_concurrency=1)

    monkeypatch.setattr("doc2roadmap.presentation.cli.main.build_a3", build)
    monkeypatch.setattr("doc2roadmap.presentation.cli.main._print_extraction", lambda summary: None)

    assert main(
        ["a3", "--doc-id", "book", "--few-shot", "prompts/coarse.txt"]
    ) == 0
    assert selected == [Path("prompts/coarse.txt")]
