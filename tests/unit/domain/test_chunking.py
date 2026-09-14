import unicodedata

import pytest

from doc2roadmap.application.windows import assemble_windows
from doc2roadmap.domain.chunking import (
    OVERSIZE_HARD_CAP,
    OVERSIZE_SENTENCE_BOUNDARY,
    OVERSIZE_TABLE_PRESERVED,
    OVERSIZE_TABLE_ROW,
    chunk_document,
)
from doc2roadmap.domain.models import Chunk, DocumentNode, DocumentTree, FormulaRef, TableRef

from tests.conftest import WordCounter, reference_tree, splitter


class CharacterCounter:
    identifier = "test-character-counter:v1"

    def count(self, text: str) -> int:
        return len(text)


def result(
    tree: DocumentTree,
    max_tokens: int = 512,
    target_tokens: int = 1,
    max_table_tokens: int = 2048,
    hard_cap_tokens: int = 6000,
    counter=None,
):
    return chunk_document(
        tree,
        "book",
        counter or WordCounter(),
        splitter(),
        max_tokens=max_tokens,
        target_tokens=target_tokens,
        max_table_tokens=max_table_tokens,
        hard_cap_tokens=hard_cap_tokens,
    )


def test_reference_tree_windows_cover_chunks_and_preserve_direct_content() -> None:
    output = result(reference_tree())
    sections = {section.title: section for section in output.sections}
    windows = assemble_windows(output.chunks)

    assert sum(len(window) for window in windows.values()) == len(output.chunks)  # I1
    assert len({chunk.chunk_id for window in windows.values() for chunk in window}) == len(output.chunks)
    chapter = sections["Chương 2: Mô hình ngôn ngữ"]
    architecture = sections["2.1 Kiến trúc Transformer"]
    attention = sections["2.1.1 Cơ chế Attention"]
    multihead = sections["2.1.2 Multi-head Attention"]
    assert [chunk.text for chunk in windows[chapter.section_id]] == [
        "Chương này trình bày kiến trúc nền tảng.",
        "Ta bắt đầu từ kiến trúc nền tảng.",
    ]  # I2, I3
    assert windows[architecture.section_id][0].text == "Transformer bỏ hồi quy."
    assert windows[attention.section_id][0].text == "Attention gán trọng số."
    assert windows[multihead.section_id][0].text == "Multi-head chạy h phép."
    assert all(window for window in windows.values())  # I4
    assert all(section.has_direct_content == (section.section_id in windows) for section in output.sections)


def test_ids_order_unicode_and_spans_are_deterministic() -> None:
    first = result(reference_tree())
    second = result(reference_tree())

    assert {chunk.chunk_id for chunk in first.chunks} == {chunk.chunk_id for chunk in second.chunks}  # I5
    assert [chunk.order_index for chunk in first.chunks] == sorted(
        chunk.order_index for chunk in first.chunks
    )  # I6
    assert all(unicodedata.is_normalized("NFC", chunk.text) for chunk in first.chunks)  # I8
    assert all(
        first.normalized_full_text[chunk.char_start : chunk.char_end] == chunk.text
        for chunk in first.chunks
    )  # I9


def test_flat_document_has_one_root_window() -> None:
    tree = DocumentTree(
        [
            DocumentNode("paragraph", "Đoạn một.", 0),
            DocumentNode("paragraph", "Đoạn hai.", 1),
        ]
    )

    output = result(tree)

    assert len(output.sections) == 1
    assert len(assemble_windows(output.chunks)) == 1
    assert {chunk.parent_section_id for chunk in output.chunks} == {output.sections[0].section_id}  # I10


def test_inserting_a_block_at_start_keeps_unchanged_ids() -> None:
    original = result(reference_tree())
    inserted = result(reference_tree([DocumentNode("paragraph", "Lời nói đầu mới.", 0)]))
    original_by_text = {chunk.text: chunk.chunk_id for chunk in original.chunks}
    inserted_by_text = {chunk.text: chunk.chunk_id for chunk in inserted.chunks}
    original_sections = {section.title: section.section_id for section in original.sections}
    inserted_sections = {section.title: section.section_id for section in inserted.sections}
    original_parents = {chunk.text: chunk.parent_section_id for chunk in original.chunks}
    inserted_parents = {chunk.text: chunk.parent_section_id for chunk in inserted.chunks}

    assert all(inserted_by_text[text] == chunk_id for text, chunk_id in original_by_text.items())  # I11
    assert inserted_sections == original_sections
    assert all(inserted_parents[text] == parent for text, parent in original_parents.items())


def test_duplicate_blocks_in_one_section_have_distinct_ids() -> None:
    tree = DocumentTree(
        [
            DocumentNode("section_header", "Bài tập", 0, level=1),
            DocumentNode("paragraph", "Làm lại ví dụ.", 1),
            DocumentNode("paragraph", "Làm lại ví dụ.", 2),
        ]
    )

    output = result(tree)

    assert len({chunk.chunk_id for chunk in output.chunks}) == len(output.chunks)


def test_duplicate_sibling_sections_do_not_share_chunk_occurrences() -> None:
    def duplicate_sections(extra_first_block: bool) -> DocumentTree:
        nodes = [
            DocumentNode("section_header", "Bài tập", 0, level=1),
            DocumentNode("paragraph", "Làm lại ví dụ.", 1),
        ]
        if extra_first_block:
            nodes.append(DocumentNode("paragraph", "Làm lại ví dụ.", 2))
        order = len(nodes)
        nodes.extend(
            [
                DocumentNode("section_header", "Bài tập", order, level=1),
                DocumentNode("paragraph", "Làm lại ví dụ.", order + 1),
            ]
        )
        return DocumentTree(nodes)

    original = result(duplicate_sections(False))
    changed = result(duplicate_sections(True))

    assert len({section.section_id for section in original.sections}) == len(original.sections)
    assert len({chunk.chunk_id for chunk in original.chunks}) == len(original.chunks)
    assert original.sections[-1].section_id == changed.sections[-1].section_id
    assert original.chunks[-1].parent_section_id == changed.chunks[-1].parent_section_id
    assert original.chunks[-1].chunk_id == changed.chunks[-1].chunk_id


def test_long_block_splits_on_sentences_with_one_sentence_overlap() -> None:
    tree = DocumentTree(
        [
            DocumentNode("section_header", "Mục", 0, level=1),
            DocumentNode("paragraph", "Một hai ba. Bốn năm sáu. Bảy tám chín.", 1),
        ]
    )

    output = result(tree, max_tokens=6)

    assert [chunk.text for chunk in output.chunks] == [
        "Một hai ba. Bốn năm sáu.",
        "Bốn năm sáu. Bảy tám chín.",
    ]
    assert [chunk.split_index for chunk in output.chunks] == [0, 1]
    assert len({chunk.parent_section_id for chunk in output.chunks}) == 1
    assert all(chunk.text.endswith(".") for chunk in output.chunks)  # I7
    assert all(chunk.oversize_reason is None for chunk in output.chunks)
    assert not any(OVERSIZE_SENTENCE_BOUNDARY in warning for warning in output.structure_warnings)
    assert all(
        output.normalized_full_text[chunk.char_start : chunk.char_end] == chunk.text
        for chunk in output.chunks
    )  # I9 after splitting


def test_long_block_does_not_split_abbreviations_or_decimals() -> None:
    text = "TS. An đo 3.14 đơn vị. PGS. Bình đồng ý! Câu cuối?"
    output = result(DocumentTree([DocumentNode("paragraph", text, 0)]), max_tokens=10)

    assert [chunk.text for chunk in output.chunks] == [
        "TS. An đo 3.14 đơn vị. PGS. Bình đồng ý!",
        "PGS. Bình đồng ý! Câu cuối?",
    ]


def test_threshold_change_only_changes_a_block_that_is_resplit() -> None:
    tree = DocumentTree(
        [
            DocumentNode("paragraph", "Ngắn gọn.", 0),
            DocumentNode("paragraph", "Một hai ba. Bốn năm sáu. Bảy tám chín.", 1),
        ]
    )

    high = result(tree, max_tokens=9)
    low = result(tree, max_tokens=6)

    high_short = next(chunk for chunk in high.chunks if chunk.text == "Ngắn gọn.")
    low_short = next(chunk for chunk in low.chunks if chunk.text == "Ngắn gọn.")
    assert high_short.chunk_id == low_short.chunk_id  # I12
    assert {chunk.chunk_id for chunk in high.chunks if "Một hai" in chunk.text} != {
        chunk.chunk_id for chunk in low.chunks if "Một hai" in chunk.text
    }


def test_jump_level_and_table_caption() -> None:
    tree = DocumentTree(
        [
            DocumentNode("section_header", "Chương", 0, level=1),
            DocumentNode("section_header", "Mục nhảy", 1, level=3),
            DocumentNode(
                "table",
                "",
                2,
                table_rows=[["Tên", "Giá trị"], ["A", "1"]],
                context_prefix="Bảng 1 — Kết quả",
            ),
        ]
    )

    output = result(tree)
    table = output.chunks[0]

    assert table.text == "| Tên | Giá trị |\n| --- | --- |\n| A | 1 |"
    assert table.context_prefix == "Bảng 1 - Kết quả"
    assert output.normalized_full_text == table.text
    assert output.sections[-1].heading_level_raw == 3


def test_nested_heading_with_bad_raw_level_is_clamped_and_warned() -> None:
    tree = DocumentTree(
        [
            DocumentNode("section_header", "Cha", 0, level=2, tree_depth=1),
            DocumentNode("section_header", "Con", 1, level=1, tree_depth=2),
            DocumentNode("paragraph", "Nội dung con.", 2, tree_depth=3),
        ]
    )

    output = result(tree)
    parent, child = output.sections[1:]

    assert child.heading_level_raw == 1
    assert child.level == parent.level + 1
    assert child.parent_section_id == parent.section_id
    assert output.structure_warnings


def test_numbered_titles_infer_three_levels_when_all_raw_levels_are_one() -> None:
    titles = ["1 Mục một", "1.1 Mục con", "1.1.1 Mục cháu", "1.2 Mục hai", "2 Mục mới"]
    nodes = [DocumentNode("section_header", title, index, level=1) for index, title in enumerate(titles)]
    nodes.insert(3, DocumentNode("paragraph", "Nội dung mục cháu.", 3))
    for index, node in enumerate(nodes):
        node.reading_order = index

    output = result(DocumentTree(nodes))
    sections = {section.title: section for section in output.sections}

    assert [sections[title].level for title in titles] == [1, 2, 3, 2, 1]  # I13
    assert sections["1.1.1 Mục cháu"].section_path == [
        "1 Mục một",
        "1.1 Mục con",
        "1.1.1 Mục cháu",
    ]
    assert sections["1.1.1 Mục cháu"].parent_section_id == sections["1.1 Mục con"].section_id
    assert sections["1.1 Mục con"].parent_section_id == sections["1 Mục một"].section_id
    assert all(section.heading_level_raw == 1 for section in output.sections[1:])
    assert not any(warning.startswith("flat_heading_tree") for warning in output.structure_warnings)


def test_unnumbered_flat_tree_warns_only_from_four_headings() -> None:
    def flat(count: int):
        return result(
            DocumentTree(
                [DocumentNode("section_header", f"Mục {chr(65 + index)}", index, level=1) for index in range(count)]
            )
        )

    assert not flat(3).structure_warnings
    assert flat(5).structure_warnings == ["flat_heading_tree: 5 headings at level 1"]  # I14


def test_letter_and_unnumbered_titles_follow_the_open_numbered_section() -> None:
    titles = [
        "MỞ ĐẦU",
        "1 Mục chính",
        "a) Chọn kiểu mô hình:",
        "b) Chọn giải thuật học:",
        "Làm sạch dữ liệu",
        "CHƯƠNG 2. PHẦN MỚI",
    ]
    output = result(
        DocumentTree(
            [DocumentNode("section_header", title, index, level=1) for index, title in enumerate(titles)]
        )
    )
    sections = {section.title: section for section in output.sections}

    assert [sections[title].level for title in titles] == [1, 1, 2, 2, 2, 2]
    assert sections["MỞ ĐẦU"].parent_section_id == output.sections[0].section_id
    assert sections["a) Chọn kiểu mô hình:"].parent_section_id == sections["1 Mục chính"].section_id
    assert sections["Làm sạch dữ liệu"].parent_section_id == sections["1 Mục chính"].section_id


def test_false_heading_is_demoted_without_breaking_its_parent_window() -> None:
    tree = DocumentTree(
        [
            DocumentNode("section_header", "1.1.1 Mục thật", 0, level=1),
            DocumentNode("paragraph", "Câu dẫn.", 1),
            DocumentNode("section_header", "trong đó:", 2, level=1),
            DocumentNode("paragraph", "Nội dung tiếp tục.", 3),
        ]
    )

    output = result(tree, target_tokens=100)

    assert "trong đó:" not in {section.title for section in output.sections}
    assert [chunk.text for chunk in output.chunks] == ["Câu dẫn.\ntrong đó:\nNội dung tiếp tục."]
    assert output.chunks[0].section_path == ["1.1.1 Mục thật"]
    assert output.structure_warnings == ["rejected_heading: trong đó:"]


def test_long_unnumbered_heading_is_demoted_but_known_valid_colon_titles_remain() -> None:
    long_title = "đây là một câu rất dài có hơn mười lăm từ và không nên trở thành một tiêu đề trong cây"
    titles = ["TẬP THỂ TÁC GIẢ:", "1 Mục chính", "a) Chọn kiểu mô hình:", "Làm sạch dữ liệu"]
    nodes = [DocumentNode("section_header", title, index, level=1) for index, title in enumerate(titles)]
    nodes.append(DocumentNode("section_header", long_title, len(nodes), level=1))

    output = result(DocumentTree(nodes))

    section_titles = {section.title for section in output.sections}
    assert set(titles) <= section_titles
    assert long_title not in section_titles
    assert output.chunks[-1].text == long_title


def test_leaf_blocks_merge_to_target_and_keep_exact_spans() -> None:
    tree = DocumentTree(
        [
            DocumentNode("section_header", "1 Mục", 0, level=1),
            DocumentNode("paragraph", "một hai ba", 1),
            DocumentNode("list_item", "bốn năm sáu", 2),
            DocumentNode("paragraph", "bảy tám chín", 3),
        ]
    )

    output = result(tree, max_tokens=8, target_tokens=5)

    assert [chunk.text for chunk in output.chunks] == ["một hai ba\nbốn năm sáu", "bảy tám chín"]
    assert all(
        output.normalized_full_text[chunk.char_start : chunk.char_end] == chunk.text
        for chunk in output.chunks
    )
    assert all(chunk.token_count <= 8 for chunk in output.chunks)
    assert output.chunks[0].block_types == ["paragraph", "list_item"]
    assert output.chunks[1].block_types == ["paragraph"]


def test_figures_and_small_tables_merge_but_keep_their_block_types() -> None:
    tree = DocumentTree(
        [
            DocumentNode("paragraph", "đoạn trước", 0),
            DocumentNode("figure", "Hình minh họa", 1, image_id="a" * 64),
            DocumentNode("paragraph", "đoạn giữa", 2),
            DocumentNode("table", "", 3, table_rows=[["Tên"], ["A"]], table_id="b" * 64),
        ]
    )

    output = result(tree, target_tokens=100)

    assert len(output.chunks) == 1
    assert output.chunks[0].block_types == ["paragraph", "figure", "table"]
    assert output.chunks[0].image_refs[0].image_id == "a" * 64
    assert output.chunks[0].table_refs[0].table_id == "b" * 64
    assert output.chunks[0].table_refs[0].char_start == output.normalized_full_text.index("| Tên |")


def test_image_refs_use_document_offsets_and_do_not_change_chunk_id() -> None:
    def tree(first_id: str, second_id: str) -> DocumentTree:
        return DocumentTree(
            [
                DocumentNode("paragraph", "mở đầu", 0),
                DocumentNode("figure", "Hình có chú thích", 1, image_id=first_id),
                DocumentNode("figure", "[Hình không có chú thích]", 2, image_id=second_id),
                DocumentNode("paragraph", "kết thúc", 3),
            ]
        )

    first = result(tree("a" * 64, "b" * 64), target_tokens=100)
    changed = result(tree("c" * 64, "d" * 64), target_tokens=100)
    chunk = first.chunks[0]

    assert [reference.image_id for reference in chunk.image_refs] == ["a" * 64, "b" * 64]
    assert [reference.char_start for reference in chunk.image_refs] == [
        first.normalized_full_text.index("Hình có chú thích"),
        first.normalized_full_text.index("[Hình không có chú thích]"),
    ]
    assert chunk.chunk_id == changed.chunks[0].chunk_id


def test_merge_never_crosses_footnote_or_section_boundary() -> None:
    tree = DocumentTree(
        [
            DocumentNode("section_header", "1 Mục", 0, level=1),
            DocumentNode("paragraph", "đoạn ngắn", 1),
            DocumentNode("footnote", "chú thích", 2),
            DocumentNode("paragraph", "đoạn sau", 3),
            DocumentNode("section_header", "2 Mục", 4, level=1),
            DocumentNode("paragraph", "đoạn khác", 5),
        ]
    )

    output = result(tree, target_tokens=20)

    assert [chunk.text for chunk in output.chunks] == ["đoạn ngắn", "chú thích", "đoạn sau", "đoạn khác"]
    assert len({chunk.parent_section_id for chunk in output.chunks}) == 2  # I16
    assert output.chunks[1].block_types == ["footnote"]


def test_target_tokens_changes_grouping() -> None:
    tree = DocumentTree([DocumentNode("paragraph", f"đoạn {index} đủ dài", index) for index in range(4)])

    small = result(tree, target_tokens=4)
    large = result(tree, target_tokens=8)

    assert [chunk.text for chunk in small.chunks] != [chunk.text for chunk in large.chunks]


def test_table_splits_by_rows_and_repeats_header_without_exceeding_limit() -> None:
    rows = [["Tên", "Giá trị"], *[[f"Mục {index}", f"Số {index}"] for index in range(40)]]
    table_id = "a" * 64
    tree = DocumentTree([DocumentNode("table", "", 0, table_rows=rows, table_id=table_id)])

    output = result(tree, max_tokens=20, max_table_tokens=20)

    assert len(output.chunks) > 1
    assert all(chunk.text.startswith("| Tên | Giá trị |\n| --- | --- |") for chunk in output.chunks)
    assert all(chunk.block_types == ["table"] for chunk in output.chunks)
    assert all(chunk.token_count <= 20 and chunk.oversize_reason is None for chunk in output.chunks)
    assert all(chunk.table_refs == [TableRef(table_id, chunk.char_start)] for chunk in output.chunks)  # I18
    assert all(
        output.normalized_full_text[chunk.char_start : chunk.char_end] == chunk.text
        for chunk in output.chunks
    )


def test_short_table_stays_whole_and_one_oversize_row_is_marked() -> None:
    short = result(
        DocumentTree([DocumentNode("table", "", 0, table_rows=[["Tên"], ["A"]])]),
        max_tokens=20,
        max_table_tokens=20,
    )
    long_row = " ".join(f"từ{index}" for index in range(20))
    oversize = result(
        DocumentTree([DocumentNode("table", "", 0, table_rows=[["Tên"], [long_row]])]),
        max_tokens=10,
        max_table_tokens=10,
    )

    assert len(short.chunks) == 1 and short.chunks[0].oversize_reason is None
    assert len(oversize.chunks) == 1
    assert oversize.chunks[0].token_count > 10
    assert oversize.chunks[0].oversize_reason == OVERSIZE_TABLE_ROW
    assert not any(OVERSIZE_SENTENCE_BOUNDARY in warning for warning in oversize.structure_warnings)


def test_unsplittable_oversize_text_records_reason_and_location_warning() -> None:
    text = " ".join(f"word{index}" for index in range(20))
    output = result(DocumentTree([DocumentNode("paragraph", text, 0, page=7)]), max_tokens=10)

    assert len(output.chunks) == 1
    assert output.chunks[0].oversize_reason == OVERSIZE_SENTENCE_BOUNDARY
    assert output.structure_warnings == [f"{OVERSIZE_SENTENCE_BOUNDARY}: page 7"]  # I17


def test_table_refs_use_document_offsets_and_do_not_change_chunk_id() -> None:
    def tree(table_id: str) -> DocumentTree:
        return DocumentTree(
            [
                DocumentNode("paragraph", "mở đầu", 0),
                DocumentNode(
                    "table",
                    "",
                    1,
                    table_rows=[["Tên", "Giá trị"], ["A", "1"]],
                    table_id=table_id,
                ),
                DocumentNode("paragraph", "kết thúc", 2),
            ]
        )

    first = result(tree("a" * 64), target_tokens=100)
    changed = result(tree("b" * 64), target_tokens=100)
    chunk = first.chunks[0]

    assert chunk.table_refs[0].table_id == "a" * 64
    assert chunk.table_refs[0].char_start == first.normalized_full_text.index("| Tên | Giá trị |")
    assert first.normalized_full_text[chunk.table_refs[0].char_start :].startswith("| Tên | Giá trị |")
    assert chunk.chunk_id == changed.chunks[0].chunk_id  # I19


def test_table_threshold_keeps_eleven_long_rows_in_one_chunk() -> None:
    cell = " ".join(f"word{index}" for index in range(10))
    rows = [[f"Cột {index}" for index in range(6)], *[[cell] * 6 for _ in range(11)]]

    output = result(
        DocumentTree([DocumentNode("table", "", 0, table_rows=rows, table_id="a" * 64)]),
        max_tokens=512,
        max_table_tokens=2048,
    )

    assert len(output.chunks) == 1
    assert 512 < output.chunks[0].token_count <= 2048
    assert output.chunks[0].oversize_reason == OVERSIZE_TABLE_PRESERVED  # I25


def test_table_merge_limit_keeps_lead_with_thirty_row_table_but_not_following_text() -> None:
    rows = [["Tên", "Mô tả"], *[[f"Mục {index}", "một hai ba bốn năm sáu"] for index in range(30)]]
    lead = "Bảng dưới đây so sánh các mô hình theo nhiều tiêu chí quan trọng"
    tree = DocumentTree(
        [
            DocumentNode("paragraph", lead, 0),
            DocumentNode("table", "", 1, table_rows=rows, table_id="a" * 64),
            DocumentNode("paragraph", "Nhận xét phía sau không thuộc câu dẫn", 2),
        ]
    )

    output = result(tree, target_tokens=256)

    assert output.chunks[0].block_types == ["paragraph", "table"]
    assert output.chunks[0].text.startswith(lead)
    assert output.chunks[1].text == "Nhận xét phía sau không thuộc câu dẫn"


def test_small_table_still_closes_at_text_target() -> None:
    tree = DocumentTree(
        [
            DocumentNode("paragraph", "câu dẫn ngắn", 0),
            DocumentNode("table", "", 1, table_rows=[["Tên"], ["A"]], table_id="a" * 64),
            DocumentNode("paragraph", "đoạn sau một hai ba", 2),
            DocumentNode("paragraph", "đoạn xa bốn năm sáu", 3),
        ]
    )

    output = result(tree, target_tokens=10)

    assert output.chunks[0].block_types == ["paragraph", "table"]
    assert "đoạn sau" not in output.chunks[0].text


def test_long_prose_still_uses_text_threshold() -> None:
    text = " ".join(f"Câu {index} có năm từ nữa." for index in range(100))

    output = result(
        DocumentTree([DocumentNode("paragraph", text, 0)]),
        max_tokens=512,
        max_table_tokens=2048,
    )

    assert len(output.chunks) > 1
    assert all(chunk.token_count <= 512 for chunk in output.chunks)
    assert all("table" not in chunk.block_types for chunk in output.chunks)


def test_hard_cap_forces_unsplittable_text_and_table_row_below_cap() -> None:
    text = " ".join(f"word{index}" for index in range(30))
    prose = result(
        DocumentTree([DocumentNode("paragraph", text, 0)]),
        max_tokens=10,
        hard_cap_tokens=12,
    )
    table = result(
        DocumentTree(
            [
                DocumentNode(
                    "table",
                    "",
                    0,
                    table_rows=[["Tên"], [text]],
                    table_id="a" * 64,
                )
            ]
        ),
        max_table_tokens=10,
        hard_cap_tokens=12,
    )

    for output in (prose, table):
        assert len(output.chunks) > 1
        assert all(chunk.token_count <= 12 for chunk in output.chunks)  # I20
        assert all(chunk.oversize_reason == OVERSIZE_HARD_CAP for chunk in output.chunks)
        assert [chunk.split_index for chunk in output.chunks] == list(range(len(output.chunks)))
        assert all(
            first.char_end == second.char_start
            for first, second in zip(output.chunks, output.chunks[1:])
        )
        assert all(
            output.normalized_full_text[chunk.char_start : chunk.char_end] == chunk.text
            for chunk in output.chunks
        )
    assert all(chunk.table_refs[0].table_id == "a" * 64 for chunk in table.chunks)


@pytest.mark.parametrize("text", ["q\u0301" * 8, "这是没有空格的一段文字"])
def test_hard_cap_uses_grapheme_boundaries_without_requiring_spaces(text: str) -> None:
    output = result(
        DocumentTree([DocumentNode("paragraph", text, 0)]),
        max_tokens=100,
        hard_cap_tokens=5,
        counter=CharacterCounter(),
    )

    assert all(chunk.token_count <= 5 for chunk in output.chunks)
    assert all(not chunk.text or not unicodedata.combining(chunk.text[0]) for chunk in output.chunks)
    assert "".join(chunk.text for chunk in output.chunks) == output.normalized_full_text


@pytest.mark.parametrize(
    ("text", "first_piece"),
    [("12345678 90123", "12345678 "), ("123456 789012", "123456 789")],
)
def test_hard_cap_uses_only_whitespace_in_last_ten_percent(
    text: str, first_piece: str
) -> None:
    output = result(
        DocumentTree([DocumentNode("paragraph", text, 0)]),
        max_tokens=100,
        hard_cap_tokens=10,
        counter=CharacterCounter(),
    )

    assert output.chunks[0].text == first_piece


def test_content_below_hard_cap_is_not_forced() -> None:
    output = result(
        DocumentTree([DocumentNode("paragraph", "12345", 0)]),
        max_tokens=100,
        hard_cap_tokens=5,
        counter=CharacterCounter(),
    )

    assert len(output.chunks) == 1
    assert output.chunks[0].oversize_reason is None


def test_legacy_chunk_block_type_loads_as_a_single_type() -> None:
    chunk = result(DocumentTree([DocumentNode("paragraph", "nội dung", 0)])).chunks[0]
    legacy = chunk.to_dict()
    legacy["block_type"] = legacy.pop("block_types")[0]
    legacy.pop("image_refs")
    legacy.pop("table_refs")
    legacy.pop("formula_refs")
    legacy.pop("oversize_reason")
    legacy["oversize"] = False

    loaded = Chunk.from_dict(legacy)

    assert loaded.block_types == ["paragraph"]
    assert loaded.image_refs == []
    assert loaded.table_refs == []
    assert loaded.formula_refs == []
    assert loaded.oversize_reason is None

    legacy_node = DocumentNode.from_dict(
        {"node_type": "paragraph", "text": "legacy", "reading_order": 0}
    )
    assert legacy_node.raw_text is None and legacy_node.formula_id is None

    legacy["oversize"] = True
    with pytest.raises(ValueError, match="oversize=true.*ingest lại"):
        Chunk.from_dict(legacy)


def test_formula_markers_merge_and_refs_do_not_affect_chunk_ids() -> None:
    def formula_tree(first_id: str, second_id: str) -> DocumentTree:
        return DocumentTree(
            [
                DocumentNode("paragraph", "before", 0),
                DocumentNode("formula", "[formula]", 1, raw_text="raw one", formula_id=first_id),
                DocumentNode("paragraph", "between", 2),
                DocumentNode("formula", "[formula]", 3, raw_text="raw two", formula_id=second_id),
                DocumentNode("paragraph", "after", 4),
            ]
        )

    first = result(formula_tree("a" * 64, "b" * 64), target_tokens=256)
    changed_refs = result(formula_tree("c" * 64, "d" * 64), target_tokens=256)

    assert len(first.chunks) == 1
    chunk = first.chunks[0]
    assert chunk.text == "before\n[formula]\nbetween\n[formula]\nafter"
    assert chunk.formula_refs == [
        FormulaRef("a" * 64, chunk.char_start + chunk.text.index("[formula]")),
        FormulaRef("b" * 64, chunk.char_start + chunk.text.rindex("[formula]")),
    ]
    assert "raw one" not in chunk.text and "raw two" not in chunk.text
    assert chunk.chunk_id == changed_refs.chunks[0].chunk_id  # I24


def test_warning_groups_are_stable_without_hiding_payloads() -> None:
    warnings = [
        *("empty_node: dropped formula" for _ in range(300)),
        "remaining_private_use: 1",
        "orphan_caption: first raw caption",
        "orphan_caption: second raw caption",
    ]

    output = result(DocumentTree([], structure_warnings=warnings))

    assert output.structure_warnings == [
        "empty_node: dropped formula ×300",
        "remaining_private_use: 1",
        "orphan_caption: first raw caption",
        "orphan_caption: second raw caption",
    ]
    assert result(DocumentTree([])).structure_warnings == []


def test_repeated_and_bulleted_false_headings_return_content_to_parent() -> None:
    nodes = [
        DocumentNode("section_header", "Trong đó:", 0, level=1),
        DocumentNode("paragraph", "child content", 1),
        DocumentNode("paragraph", "Trong đó:", 2),
        DocumentNode("paragraph", "Trong đó:", 3),
        DocumentNode("section_header", "• bullet item", 4, level=1),
        DocumentNode("paragraph", "bullet content", 5),
    ]

    output = result(DocumentTree(nodes), target_tokens=256)

    assert [section.title for section in output.sections] == ["<document>"]
    assert all(chunk.parent_section_id == output.sections[0].section_id for chunk in output.chunks)
    assert "child content" in output.normalized_full_text
    assert "bullet content" in output.normalized_full_text
    assert output.structure_warnings == [
        "rejected_heading_repeated: Trong đó:",
        "rejected_heading_bullet: • bullet item",
    ]


def test_repeated_heading_rule_exempts_numbered_and_keeps_single_body_match() -> None:
    nodes = [
        DocumentNode("section_header", "Overview", 0, level=1),
        DocumentNode("paragraph", "Overview", 1),
        DocumentNode("section_header", "2.1 Numbered", 2, level=2),
        *(DocumentNode("paragraph", "2.1 Numbered", order) for order in range(3, 8)),
    ]

    output = result(DocumentTree(nodes))

    assert {section.title for section in output.sections} == {
        "<document>",
        "Overview",
        "2.1 Numbered",
    }
