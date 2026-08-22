import hashlib
from collections import Counter
from types import SimpleNamespace

from docling_core.types.doc import DoclingDocument

from doc2roadmap.domain.chunking import chunk_document
from doc2roadmap.infrastructure.parsing import DoclingParser

from tests.conftest import WordCounter, load_docling_fixture, splitter


def _label(item) -> str:
    value = getattr(item, "label", "text")
    return str(getattr(value, "value", value)).lower()


def _pua_count(text: str) -> int:
    return sum(0xE000 <= ord(character) <= 0xF8FF for character in text)


class _Document:
    def __init__(self, *items) -> None:
        self.items = items

    def iterate_items(self):
        return [(item, 1) for item in self.items]


def test_xstk_fixture_characterizes_the_three_regressions_and_round_trips() -> None:
    document = load_docling_fixture("xstk-ch3-1")
    items = list(document.iterate_items())
    formulas = [item for item, _ in items if _label(item) == "formula"]
    headings = [item for item, _ in items if _label(item) == "section_header"]

    assert len(items) == 992
    assert Counter(_label(item) for item, _ in items)["table"] == 51
    assert len(formulas) == 264
    assert all(not item.text for item in formulas)
    assert sum(bool(item.orig) for item in formulas) == 263
    assert sum(bool(item.text.lstrip()) and _pua_count(item.text.lstrip()[0]) for item in headings) == 23

    unmapped = DoclingParser().adapt(document, "xstk-ch3-1.docx")
    unmapped_output = chunk_document(
        unmapped.tree, "xstk-ch3-1", WordCounter(), splitter(), max_tokens=512, target_tokens=256
    )
    assert _pua_count(unmapped_output.normalized_full_text) == 653

    restored = DoclingDocument.model_validate(document.export_to_dict())
    restored_formulas = [
        item for item, _ in restored.iterate_items() if _label(item) == "formula"
    ]
    assert len(list(restored.iterate_items())) == 992
    assert sum(bool(item.orig) for item in restored_formulas) == 263


def test_pdf_symbol_mapping_covers_greek_bullet_table_and_reports_unknown_pua() -> None:
    table = SimpleNamespace(
        label="table",
        prov=[],
        data=SimpleNamespace(grid=[[SimpleNamespace(text="\uf053 x")]]),
        export_to_markdown=lambda **_: "| \uf053 x |",
    )
    text = SimpleNamespace(label="text", text="\uf061 \uf063 \uf06d \uf073 \uf0b7 \uf0ff", orig="", prov=[])

    tree = DoclingParser().adapt(_Document(text, table), "symbols.pdf").tree

    assert tree.nodes[0].text == "α χ μ σ • \uf0ff"
    assert tree.nodes[1].table_rows == [["Σ x"]]
    assert tree.parse_stats["symbol_characters_mapped"] == 7
    assert tree.structure_warnings == ["remaining_private_use: 1"]


def test_docx_keeps_private_use_characters_unchanged() -> None:
    item = SimpleNamespace(label="text", text="\uf061 \uf0b7", orig="", prov=[])

    tree = DoclingParser().adapt(_Document(item), "symbols.docx").tree

    assert tree.nodes[0].text == "\uf061 \uf0b7"
    assert tree.parse_stats["symbol_characters_mapped"] == 0
    assert not tree.structure_warnings


def test_raw_fallback_keeps_nodes_but_both_empty_fields_still_drop() -> None:
    raw_only = SimpleNamespace(label="text", text="", orig="raw fallback", prov=[])
    empty = SimpleNamespace(label="text", text="", orig="", prov=[])

    tree = DoclingParser().adapt(_Document(raw_only, empty), "raw.docx").tree

    assert [(node.text, node.raw_text) for node in tree.nodes] == [
        ("raw fallback", "raw fallback")
    ]  # I23
    assert tree.parse_stats["dropped"] == {"text": 1}
    assert tree.structure_warnings == ["empty_node: dropped text"]


def test_formula_uses_a_neutral_marker_and_hashes_normalized_raw_content() -> None:
    item = SimpleNamespace(label="formula", text="", orig="raw formula", prov=[])

    node = DoclingParser().adapt(_Document(item), "formula.pdf").tree.nodes[0]

    assert node.text == "[formula]"
    assert node.raw_text == "raw formula"
    assert node.formula_id == hashlib.sha256(b"raw formula").hexdigest()
    assert node.raw_text not in node.text


def test_xstk_fixture_maps_all_embedded_pua_and_restores_263_formulas() -> None:
    parsed = DoclingParser().adapt(load_docling_fixture("xstk-ch3-1"), "xstk-ch3-1.pdf")
    output = chunk_document(
        parsed.tree,
        "xstk-ch3-1",
        WordCounter(),
        splitter(),
        max_tokens=512,
        target_tokens=256,
    )
    formulas = [node for node in parsed.tree.nodes if node.node_type == "formula"]

    assert len(formulas) == 263
    assert all(node.text == "[formula]" and node.raw_text and node.formula_id for node in formulas)
    remaining = sum(DoclingParser._private_use_count(node) for node in parsed.tree.nodes)
    assert _pua_count(output.normalized_full_text) == 2
    assert f"remaining_private_use: {remaining}" in parsed.tree.structure_warnings  # I22
    assert parsed.tree.parse_stats["symbol_characters_mapped"] >= 653
    assert sum(len(chunk.formula_refs) for chunk in output.chunks) == 263
    assert sum(len(chunk.table_refs) for chunk in output.chunks) == 51
    assert all(
        output.normalized_full_text[chunk.char_start : chunk.char_end] == chunk.text
        for chunk in output.chunks
    )
    assert not any(chunk.token_count > 6000 for chunk in output.chunks)
    assert not any(
        _pua_count(chunk.text) and not any("remaining_private_use" in warning for warning in output.structure_warnings)
        for chunk in output.chunks
    )


def test_xstk_false_headings_are_demoted_after_symbol_mapping() -> None:
    parsed = DoclingParser().adapt(load_docling_fixture("xstk-ch3-1"), "xstk-ch3-1.pdf")
    output = chunk_document(parsed.tree, "xstk-ch3-1", WordCounter(), splitter())
    titles = {section.title for section in output.sections}

    assert "Trong đó:" not in titles
    assert "Chú ý ." not in titles
    assert not any(title.startswith(("•", "▪", "▫", "◦", "‣", "⁃", "-", "–", "—")) for title in titles)
