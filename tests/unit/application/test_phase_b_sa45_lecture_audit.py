import pytest

from doc2roadmap.application.phase_b.lectures import _lecture_output_text, _merge_emitted


def test_k6_scans_idea_text_without_serialized_citation_metadata():
    output = {
        "explanation": [{
            "text": "Một phát biểu riêng biệt về khái niệm.",
            "citations": [{"quote": "cụm trích dẫn lặp lại"}],
        }],
        "example": [],
    }

    assert _lecture_output_text(output) == "Một phát biểu riêng biệt về khái niệm."


@pytest.mark.xfail(strict=True, reason="SA-49: bridge merge currently deduplicates full item JSON only")
def test_same_prerequisite_has_only_one_bridge_in_lecture_sections():
    first = {"prereq": "a", "text": "Tập hợp là nền để hiểu phép hợp.",
             "citations": [{"label": "Q1", "quote": "nguồn"}]}
    second = {"prereq": "a", "text": "Phép hợp dùng các phần tử của tập hợp.",
              "citations": [{"label": "Q1", "quote": "nguồn"}]}

    sections = _merge_emitted([], {"bridges": [first, second]})

    bridges = next(section["items"] for section in sections
                   if section["kind"] == "cau_noi")
    assert len(bridges) == 1
