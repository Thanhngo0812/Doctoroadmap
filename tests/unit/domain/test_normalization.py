import unicodedata

from doc2roadmap.domain.normalization import normalize_text


def test_normalizes_each_required_form_without_losing_vietnamese() -> None:
    text = "  Qua\u0301   khớp\u00ad  \r\n  mô-\n hình “tốt” — đúng  "

    normalized = normalize_text(text)

    assert normalized == 'Quá khớp\nmôhình "tốt" - đúng'
    assert unicodedata.is_normalized("NFC", normalized)
    assert "Quá" in normalized

