import re

from doc2roadmap.domain.chunking import chunk_document
from doc2roadmap.domain.models import DocumentNode, DocumentTree
from doc2roadmap.infrastructure.parsing import DoclingParser

from tests.conftest import WordCounter, load_docling_fixture, splitter


class CharacterCounter:
    identifier = "test-character-counter:v1"

    def count(self, text: str) -> int:
        return len(text)


def _result(tree: DocumentTree, *, counter=None, target_tokens: int = 256):
    return chunk_document(
        tree,
        "book",
        counter or WordCounter(),
        splitter(),
        target_tokens=target_tokens,
    )


def test_heading_level_uses_explicit_then_declared_then_fallback_evidence() -> None:
    explicit = _result(
        DocumentTree(
            [
                DocumentNode("section_header", "CHƯƠNG IV", 0, level=1),
                DocumentNode("section_header", "A. Mục một", 1, level=1),
                DocumentNode("section_header", "A) Mục hai", 2, level=1),
                DocumentNode("section_header", "Đ. Mục ba", 3, level=1),
            ]
        )
    )
    declared = _result(
        DocumentTree(
            [
                DocumentNode("section_header", "Overview", 0, level=1),
                DocumentNode("section_header", "Details", 1, level=2),
                DocumentNode("section_header", "2.1 Explicit wins", 2, level=1),
            ]
        )
    )
    flat = _result(
        DocumentTree(
            [
                DocumentNode("section_header", "1. Parent", 0, level=1),
                DocumentNode("section_header", "1.1 Child", 1, level=1),
            ]
        )
    )

    assert [(section.title, section.level) for section in explicit.sections[1:]] == [
        ("CHƯƠNG IV", 1),
        ("A. Mục một", 2),
        ("A) Mục hai", 2),
        ("Đ. Mục ba", 2),
    ]
    assert all(
        section.parent_section_id == explicit.sections[1].section_id
        for section in explicit.sections[2:]
    )
    assert [(section.title, section.level) for section in declared.sections[1:]] == [
        ("Overview", 1),
        ("Details", 2),
        ("2.1 Explicit wins", 2),
    ]
    assert [section.level for section in flat.sections[1:]] == [1, 2]


def test_self_tuning_chapter_sequences_are_language_independent_and_nested() -> None:
    vietnamese = _result(
        DocumentTree(
            [
                DocumentNode("section_header", "CHƯƠNG I", 0, level=1),
                DocumentNode("section_header", "1.1 Mục", 1, level=1),
                DocumentNode("section_header", "CHƯƠNG II", 2, level=1),
                DocumentNode("section_header", "2.1 Mục", 3, level=1),
                DocumentNode("section_header", "CHƯƠNG III", 4, level=1),
            ]
        )
    )
    chinese = _result(
        DocumentTree(
            [
                DocumentNode("section_header", "第1章 Tổng quan", 0, level=1),
                DocumentNode("section_header", "1.1 Mục", 1, level=1),
                DocumentNode("section_header", "第2章 Chi tiết", 2, level=1),
            ]
        )
    )
    nested = _result(
        DocumentTree(
            [
                DocumentNode("section_header", "Teil 1", 0, level=1),
                DocumentNode("section_header", "Kapitel 1", 1, level=1),
                DocumentNode("section_header", "1.1 Thema", 2, level=1),
                DocumentNode("section_header", "Kapitel 2", 3, level=1),
                DocumentNode("section_header", "Teil 2", 4, level=1),
            ]
        )
    )

    assert [section.level for section in vietnamese.sections[1:] if "CHƯƠNG" in section.title] == [1, 1, 1]
    assert [section.level for section in chinese.sections[1:] if "章" in section.title] == [1, 1]
    assert [(section.title, section.level) for section in nested.sections[1:]] == [
        ("Teil 1", 1),
        ("Kapitel 1", 2),
        ("1.1 Thema", 2),
        ("Kapitel 2", 2),
        ("Teil 2", 1),
    ]


def test_chapter_sequence_exempts_running_headers_but_adjacent_numbered_labels_are_not_chapters() -> None:
    running_headers = _result(
        DocumentTree(
            [
                DocumentNode("section_header", "KAPITEL 1", 0, level=1),
                DocumentNode("section_header", "1.1 Thema", 1, level=1),
                DocumentNode("section_header", "Kapitel 2", 2, level=1),
                DocumentNode("paragraph", "KAPITEL 1", 3),
                DocumentNode("paragraph", "KAPITEL 1", 4),
            ]
        )
    )
    adjacent = _result(
        DocumentTree(
            [
                DocumentNode("section_header", "1. Parent", 0, level=1),
                DocumentNode("section_header", "Bài tập 1", 1, level=1),
                DocumentNode("section_header", "Bài tập 2", 2, level=1),
            ]
        )
    )

    assert {section.title for section in running_headers.sections} >= {
        "KAPITEL 1",
        "Kapitel 2",
    }
    assert [section.level for section in adjacent.sections[2:]] == [2, 2]


def test_symbol_only_numeric_prefix_is_not_a_chapter_sequence() -> None:
    output = _result(
        DocumentTree(
            [
                DocumentNode("section_header", "1. Parent", 0, level=1),
                DocumentNode("section_header", "§1", 1, level=1),
                DocumentNode("section_header", "1.1 Child", 2, level=1),
                DocumentNode("section_header", "§2", 3, level=1),
            ]
        )
    )

    assert all(
        section.level > 1 for section in output.sections if section.title.startswith("§")
    )


def test_docx_fixture_has_no_letter_section_at_root() -> None:
    parsed = DoclingParser().adapt(
        load_docling_fixture("baocao-canhan"), "baocao-canhan.docx"
    )
    output = _result(parsed.tree)
    letter_sections = [
        section
        for section in output.sections
        if re.match(r"^[^\W\d_][.)]\s", section.title)
    ]

    assert len(output.sections) == 27
    assert letter_sections
    assert all(section.level == 2 for section in letter_sections)
    assert all(section.section_path[0].startswith("CHƯƠNG") for section in letter_sections)
    assert {"MỤC LỤC", "NHẬN XÉT, ĐÁNH GIÁ CỦA GIẢNG VIÊN"} <= {
        section.title for section in output.sections
    }
    assert "." * 100 not in output.normalized_full_text
    assert not any(
        re.search(r"\s\d+$", line)
        and re.sub(r"\s+\d+$", "", line) in {section.title for section in output.sections}
        for line in output.normalized_full_text.splitlines()
    )


def test_non_linguistic_and_toc_content_are_filtered_with_auditable_warnings() -> None:
    tree = DocumentTree(
        [
            DocumentNode("section_header", "1. CHƯƠNG I", 0, level=1),
            DocumentNode("paragraph", "." * 200, 1),
            DocumentNode("paragraph", "x = 5", 2),
            DocumentNode("section_header", "MỤC LỤC", 3, level=1),
            DocumentNode("text", "1. CHƯƠNG I\t1", 4),
            DocumentNode("text", "MỤC LỤC\t2", 5),
            DocumentNode(
                "paragraph",
                "Đoạn mở đầu.\n1. CHƯƠNG I\nĐoạn kết thúc.",
                6,
            ),
        ]
    )

    output = _result(tree)

    assert "." * 100 not in output.normalized_full_text
    assert "1. CHƯƠNG I\t1" not in output.normalized_full_text
    assert "x = 5" in output.normalized_full_text
    assert "Đoạn mở đầu" in output.normalized_full_text
    assert {section.title for section in output.sections} >= {"1. CHƯƠNG I", "MỤC LỤC"}
    assert any(
        warning.startswith("non_linguistic_block:") and "200 chars" in warning
        for warning in output.structure_warnings
    )
    assert any(
        warning.startswith("toc_block:") and "1. CHƯƠNG I" in warning
        for warning in output.structure_warnings
    )


def test_clean_document_does_not_get_cleanup_warnings() -> None:
    output = _result(
        DocumentTree([DocumentNode("paragraph", "Một đoạn văn bình thường.", 0)])
    )

    assert not any(
        warning.startswith(("non_linguistic_block:", "toc_block:"))
        for warning in output.structure_warnings
    )


def test_all_identical_warnings_are_grouped_but_distinct_payloads_survive() -> None:
    repeated = "rejected_heading_repeated: Naïve Bayes Classification"
    output = _result(
        DocumentTree(
            [],
            structure_warnings=[
                *([repeated] * 300),
                "rejected_heading_repeated: Ví dụ A",
                "rare_warning: inspect me",
                "rejected_heading_repeated: Ví dụ B",
            ],
        )
    )

    assert output.structure_warnings == [
        f"{repeated} ×300",
        "rejected_heading_repeated: Ví dụ A",
        "rare_warning: inspect me",
        "rejected_heading_repeated: Ví dụ B",
    ]


def test_every_path_above_the_text_limit_records_why() -> None:
    table = _result(
        DocumentTree(
            [
                DocumentNode(
                    "table",
                    "",
                    0,
                    table_rows=[["Tên"], ["x" * 550]],
                    table_id="a" * 64,
                )
            ]
        ),
        counter=CharacterCounter(),
    )
    prose = _result(
        DocumentTree([DocumentNode("paragraph", "x" * 550, 0)]),
        counter=CharacterCounter(),
    )
    within_limit = _result(
        DocumentTree([DocumentNode("paragraph", "short", 0)]),
        counter=CharacterCounter(),
    )

    assert table.chunks[0].token_count > 512
    assert table.chunks[0].oversize_reason == "table_kept_whole_above_text_limit"
    assert prose.chunks[0].oversize_reason == "sentence_splitter_no_boundary"
    assert within_limit.chunks[0].oversize_reason is None
