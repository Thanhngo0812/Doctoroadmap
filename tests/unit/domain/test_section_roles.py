import unicodedata

import pytest

from doc2roadmap.domain.chunking import chunk_document
from doc2roadmap.domain.models import DocumentNode, DocumentTree
from tests.conftest import WordCounter, splitter


def chunk(nodes):
    return chunk_document(DocumentTree(nodes), "roles", WordCounter(), splitter(), target_tokens=1)


@pytest.mark.parametrize("title,role", [
    ("Bài tập chương 4", "bai_tap"), ("Câu hỏi ôn tập", "bai_tap"), ("Đề số 5", "bai_tap"),
    ("Exercises 3B", "bai_tap"), ("Problems", "bai_tap"), ("Exercise set", "bai_tap"),
    ("Nội dung môn học", "de_cuong"), ("Đề cương học phần", "de_cuong"), ("Mục lục", "de_cuong"),
    ("Contents", "de_cuong"), ("Nội dung", "de_cuong"),
    ("MỤCLỤC", "de_cuong"), ("10. Hình thức và tiêu chuẩn đánh giá sinh viên", "hanh_chinh"),
    ("Lời nói đầu", "mo_dau"), ("Preface for Students", "mo_dau"), ("Foreword", "mo_dau"),
    ("About the author", "mo_dau"), ("Major improvements in this edition", "mo_dau"), ("MỞĐẦU", "mo_dau"),
    ("Thang điểm", "hanh_chinh"), ("Lịch học", "hanh_chinh"), ("Thông tin giảng viên", "hanh_chinh"),
    ("Grading", "hanh_chinh"), ("Schedule", "hanh_chinh"), ("Instructor information", "hanh_chinh"),
])
@pytest.mark.parametrize("unaccented", [False, True])
def test_each_role_heading_pattern_with_and_without_accents(title, role, unaccented):
    if unaccented:
        title = "".join(c for c in unicodedata.normalize("NFD", title) if not unicodedata.combining(c)).replace("Đ", "D").replace("đ", "d")
    result = chunk([DocumentNode("section_header", title, 0, level=1), DocumentNode("text", "Một đoạn.", 1)])
    assert result.sections[-1].role == role
    assert result.chunks[0].role == role


def test_region_inherits_to_children_but_closes_at_same_or_higher_level():
    result = chunk([
        DocumentNode("section_header", "Chapter 1", 0, level=1),
        DocumentNode("section_header", "Exercises 3B", 1, level=2),
        DocumentNode("section_header", "Hints", 2, level=3),
        DocumentNode("text", "Exercise text.", 3),
        DocumentNode("section_header", "Matrices", 4, level=2),
        DocumentNode("text", "Definition of matrices.", 5),
        DocumentNode("section_header", "Chapter 2", 6, level=1),
        DocumentNode("text", "New chapter.", 7),
    ])
    assert [c.role for c in result.chunks] == ["bai_tap", "noi_dung", "noi_dung"]


def test_front_matter_and_role_refresh_preserve_ids_text_and_spans():
    from doc2roadmap.domain.chunking import assign_section_roles, chunk_roles

    result = chunk([
        DocumentNode("text", "Copyright information.", 0),
        DocumentNode("section_header", "Contents", 1, level=1),
        DocumentNode("text", "List of chapters.", 2),
        DocumentNode("section_header", "Welcome", 3, level=1),
        DocumentNode("text", "Before numbered chapter.", 4),
        DocumentNode("section_header", "Chương 1: Tập hợp", 5, level=1),
        DocumentNode("text", "Tập hợp được định nghĩa...", 6),
    ])
    assert [c.role for c in result.chunks] == ["mo_dau", "de_cuong", "mo_dau", "noi_dung"]
    before = [{k: v for k, v in c.to_dict().items() if k != "role"} for c in result.chunks]
    for s in result.sections:
        s.role = "noi_dung"
    for c in result.chunks:
        c.role = "noi_dung"
    assign_section_roles(result.sections, result.chunks)
    assert list(chunk_roles(result.chunks).values()) == ["mo_dau", "de_cuong", "mo_dau", "noi_dung"]
    assert before == [{k: v for k, v in c.to_dict().items() if k != "role"} for c in result.chunks]


def test_detected_toc_run_has_role_without_reintroducing_filtered_text():
    result = chunk([
        DocumentNode("section_header", "Book", 0, level=1),
        DocumentNode("text", "Chapter 1 3\nChapter 2 9", 1),
        DocumentNode("section_header", "Chapter 1", 2, level=1),
        DocumentNode("text", "First lesson.", 3),
        DocumentNode("section_header", "Chapter 2", 4, level=1),
        DocumentNode("text", "Second lesson.", 5),
    ])
    assert next(s for s in result.sections if s.title == "Book").role == "de_cuong"
    assert all(c.role == "noi_dung" for c in result.chunks)
    assert "Chapter 1 3" not in result.normalized_full_text


def test_a_filtered_toc_inside_content_does_not_relabel_the_whole_section():
    result = chunk([
        DocumentNode("section_header", "Chapter 1", 0, level=1),
        DocumentNode("text", "Chapter 1 3\nChapter 2 9", 1),
        DocumentNode("text", "Here is the lesson, not a table of contents.", 2),
        DocumentNode("section_header", "Chapter 2", 3, level=1),
    ])
    assert result.chunks[0].role == "noi_dung"


def test_roles_roundtrip_and_legacy_defaults():
    from doc2roadmap.domain.models import Section, Chunk

    result = chunk([DocumentNode("section_header", "Bài tập", 0, level=1), DocumentNode("text", "Làm bài.", 1)])
    for obj, model in ((result.sections[-1], Section), (result.chunks[0], Chunk)):
        value = obj.to_dict()
        assert model.from_dict(value).role == "bai_tap"
        del value["role"]
        assert model.from_dict(value).role == "noi_dung"


def test_outline_children_keep_outline_role_even_before_first_numbered_chapter():
    result = chunk([
        DocumentNode("section_header", "Contents", 0, level=1),
        DocumentNode("section_header", "Part A", 1, level=2),
        DocumentNode("text", "List of topics.", 2),
        DocumentNode("section_header", "Chapter 1", 3, level=1),
        DocumentNode("text", "First lesson.", 4),
    ])
    assert [c.role for c in result.chunks] == ["de_cuong", "noi_dung"]
