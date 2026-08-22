from pathlib import Path

import pytest

from doc2roadmap.infrastructure.parsing import DoclingParser


@pytest.mark.integration
@pytest.mark.parametrize(
    "fixture",
    [
        Path("tests/fixtures/smoke.pdf"),
        Path("tests/fixtures/smoke.docx"),
        Path("tests/fixtures/two-column.pdf"),
    ],
)
def test_docling_parses_real_document(fixture: Path) -> None:
    if not fixture.exists():
        pytest.skip("fixture được tạo bởi scripts/create_smoke_pdf.py")

    parsed = DoclingParser().parse(fixture.read_bytes(), fixture.name)
    tree = parsed.tree

    assert tree.nodes
    assert [node.reading_order for node in tree.nodes] == list(range(len(tree.nodes)))
    assert any(node.node_type not in {"title", "section_header"} for node in tree.nodes)
    if fixture.name != "two-column.pdf":
        assert any(node.node_type in {"title", "section_header"} for node in tree.nodes)
    if fixture.suffix == ".docx":
        assert not parsed.images
        tables = [node for node in tree.nodes if node.node_type == "table"]
        assert len(tables) == 1
        assert "Name" in tables[0].text and "Value" in tables[0].text
        assert tables[0].table_rows == [["Name", "Value"], ["A", "1"]]
        assert len(tables[0].table_id or "") == 64
    if fixture.name == "two-column.pdf":
        text = " ".join(node.text for node in tree.nodes)
        assert text.index("Left column first") < text.index("Left column third")
        assert text.index("Left column third") < text.index("Right column first")
