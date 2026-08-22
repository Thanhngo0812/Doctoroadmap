from pathlib import Path
from types import SimpleNamespace

from doc2roadmap.domain.chunking import chunk_document
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore
from doc2roadmap.presentation.cli.main import _ingest, _inspect

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

    class UseCase:
        def execute(self, *args, **kwargs):
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

    _ingest(source, "book")

    output = capsys.readouterr().out
    assert "parse: giữ 3/5; bỏ: caption=1, formula=1" in output
    assert "stitch=0; sắp lại trang=0" in output
    assert "media: ảnh=2; chú thích=2 (lấy lại=1, mồ côi=1)" in output
    assert "Cảnh báo:" in output
    assert "- rejected_heading: trong đó:" in output
    assert "- sentence_splitter_no_boundary: page 7" in output
