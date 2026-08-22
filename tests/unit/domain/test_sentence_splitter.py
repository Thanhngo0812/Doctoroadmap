import pytest

from doc2roadmap.infrastructure.text import UnicodeSentenceSplitter
from doc2roadmap.infrastructure.text.sentence_splitter import COMMON_LATIN_ABBREVIATIONS


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            'TS. An đo 3.14 đơn vị. PGS. Bình nói "đồng ý!" Câu cuối?',
            ['TS. An đo 3.14 đơn vị.', 'PGS. Bình nói "đồng ý!"', "Câu cuối?"],
        ),
        ("Dr. Smith met Mr. Jones. They agreed.", ["Dr. Smith met Mr. Jones.", "They agreed."]),
        (
            "Use a model, e.g. logistic regression. Then evaluate.",
            ["Use a model, e.g. logistic regression.", "Then evaluate."],
        ),
        (
            "See Goodfellow et al. 2016 for details. It is standard.",
            ["See Goodfellow et al. 2016 for details.", "It is standard."],
        ),
        (
            "As shown in Fig. 3 the loss drops. We then stop.",
            ["As shown in Fig. 3 the loss drops.", "We then stop."],
        ),
        ("这是第一句。这是第二句。第三句。", ["这是第一句。", "这是第二句。", "第三句。"]),
        ("これは最初の文です。これは二番目です。", ["これは最初の文です。", "これは二番目です。"]),
        ("यह पहला वाक्य है। यह दूसरा है।", ["यह पहला वाक्य है।", "यह दूसरा है।"]),
        ("هذه الجملة الأولى؟ وهذه الثانية.", ["هذه الجملة الأولى؟", "وهذه الثانية."]),
        ("テスト！次の文？終わり。", ["テスト！", "次の文？", "終わり。"]),
    ],
)
def test_sentence_boundaries_across_scripts(text: str, expected: list[str]) -> None:
    splitter = UnicodeSentenceSplitter()

    sentences = [text[span.start : span.end] for span in splitter.split(text)]

    assert sentences == expected


@pytest.mark.parametrize(
    ("text", "count"),
    [
        ("Không có dấu kết câu", 1),
        ("Chờ… Tiếp tục.", 2),
        ("پہلا جملہ۔دوسرا۔", 2),
        ("ប្រយោគទីមួយ។ប្រយោគទីពីរ។", 2),
    ],
)
def test_additional_unicode_punctuation_and_unsplit_text(text: str, count: int) -> None:
    spans = UnicodeSentenceSplitter().split(text)

    assert len(spans) == count
    assert all(text[span.start : span.end] for span in spans)


def test_abbreviations_are_data_and_spans_still_index_the_original_text() -> None:
    text = "See Eq. 2 at 3.14 units. Done."
    spans = UnicodeSentenceSplitter().split(text)

    assert "Eq." in COMMON_LATIN_ABBREVIATIONS
    assert [text[span.start : span.end] for span in spans] == [
        "See Eq. 2 at 3.14 units.",
        "Done.",
    ]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Anh ấy do dự… rồi quyết định làm. Xong.", ["Anh ấy do dự… rồi quyết định làm.", "Xong."]),
        ("U.S.A. là viết tắt. Ai cũng biết.", ["U.S.A. là viết tắt.", "Ai cũng biết."]),
        ('Anh nói "tuyệt!" rồi đi. Hết chuyện.', ['Anh nói "tuyệt!" rồi đi.', "Hết chuyện."]),
    ],
)
def test_lowercase_after_punctuation_is_not_a_sentence_boundary(
    text: str, expected: list[str]
) -> None:
    spans = UnicodeSentenceSplitter().split(text)

    assert [text[span.start : span.end] for span in spans] == expected
