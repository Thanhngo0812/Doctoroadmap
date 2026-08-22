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
