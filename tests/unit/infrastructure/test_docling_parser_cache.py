from types import SimpleNamespace

from doc2roadmap.infrastructure.parsing import DoclingParser


def test_document_converter_is_created_lazily_and_reused(monkeypatch) -> None:
    calls = 0

    class FakeConverter:
        def __init__(self) -> None:
            nonlocal calls
            calls += 1

        def convert(self, source: str):
            document = SimpleNamespace(iterate_items=lambda: [])
            return SimpleNamespace(document=document)

    monkeypatch.setattr(DoclingParser, "_new_converter", staticmethod(FakeConverter))
    parser = DoclingParser()
    assert calls == 0

    parser.parse(b"pdf", "one.pdf")
    parser.parse(b"pdf", "two.pdf")

    assert calls == 1


def test_the_default_backend_keeps_the_identifier_and_another_backend_changes_it(monkeypatch) -> None:
    # Đổi identifier của bộ đọc mặc định sẽ đổi hash parse của mọi tài liệu đã có vàng — không được.
    import importlib.metadata

    version = importlib.metadata.version("docling")
    assert DoclingParser().identifier == f"docling:{version}"
    assert DoclingParser(pdf_backend="pypdfium2").identifier == f"docling:{version}+pypdfium2"
    seen = []

    def fake(backend="docling-parse"):
        seen.append(backend)
        return SimpleNamespace(convert=lambda source: SimpleNamespace(document=SimpleNamespace(iterate_items=lambda: [])))

    monkeypatch.setattr(DoclingParser, "_new_converter", staticmethod(fake))
    DoclingParser(pdf_backend="pypdfium2").parse(b"pdf", "a.pdf")
    DoclingParser().parse(b"pdf", "b.pdf")
    assert seen == ["pypdfium2", "docling-parse"]


def test_an_unknown_backend_is_refused() -> None:
    import pytest

    with pytest.raises(ValueError, match="pdf_backend"):
        DoclingParser(pdf_backend="pdfminer")
