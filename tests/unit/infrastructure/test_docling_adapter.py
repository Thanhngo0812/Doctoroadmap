import hashlib
import re
from collections import Counter
from types import SimpleNamespace

from doc2roadmap.domain.chunking import chunk_document
from doc2roadmap.domain.models import DocumentNode
from doc2roadmap.infrastructure.parsing import DoclingParser

from tests.conftest import WordCounter, load_docling_fixture, splitter


def label(item) -> str:
    value = getattr(item, "label", "text")
    return str(getattr(value, "value", value)).lower()


def test_real_fixture_contains_all_picture_images() -> None:
    document = load_docling_fixture()
    items = list(document.iterate_items())
    counts = Counter(label(item) for item, _ in items)
    pictures = [item for item, _ in items if label(item) == "picture"]
    formulas = [item for item, _ in items if label(item) == "formula"]
    headings = [item for item, _ in items if label(item) == "section_header"]

    assert len(items) == 170
    assert len(pictures) == 9
    assert all(item.get_image(doc=document) is not None for item in pictures)
    assert len(headings) == 27 and {item.level for item in headings} == {1}
    assert counts["formula"] == 1 and not formulas[0].text


def test_adapter_cleans_figures_and_reports_every_dropped_item() -> None:
    parsed = DoclingParser().adapt(load_docling_fixture(), "nhap-mon-ml.pdf")
    tree = parsed.tree
    figures = [node for node in tree.nodes if node.node_type == "figure"]
    stats = tree.parse_stats

    assert len(tree.nodes) == stats["nodes_kept"]
    assert len(figures) == len(parsed.images) == 9
    assert {node.image_id for node in figures} == set(parsed.images)
    assert all(image_id == hashlib.sha256(image).hexdigest() for image_id, image in parsed.images.items())
    assert all(len(node.text) < 10_000 and node.context_prefix is None for node in figures)
    assert sum(node.text == "[figure]" for node in figures) == 1
    assert stats["items_total"] == 170
    assert stats["dropped"] == {"caption": 8, "document_index": 1}
    assert stats["captions"] == {"total": 9, "recovered": 8, "orphaned": 1}
    assert stats["images_extracted"] == 9
    assert (
        stats["nodes_kept"]
        + stats["page_breaks_stitched"]
        + sum(stats["dropped"].values())
        == stats["items_total"]
    )
    formulas = [node for node in tree.nodes if node.node_type == "formula"]
    assert len(formulas) == 1 and formulas[0].raw_text and formulas[0].formula_id
    assert "empty_node: dropped formula" not in tree.structure_warnings

    repeated = DoclingParser().adapt(load_docling_fixture(), "nhap-mon-ml.pdf")
    assert set(repeated.images) == set(parsed.images)


def test_orphan_caption_is_kept_once_at_its_reading_position() -> None:
    tree = DoclingParser().adapt(load_docling_fixture(), "nhap-mon-ml.pdf").tree
    caption = "Hình 2: Tập các bức ảnh và các mô tả về chúng."
    texts = [node.text for node in tree.nodes]
    orphan = texts.index(caption)
    heading = texts.index("1.1.2 Bản chất của việc học, suy diễn, và phán đoán")
    figure_positions = [
        texts.index("lychee-inspired spherical chair"),
        texts.index("a girl giving cat a gentle hug"),
        texts.index("a small hedgehog holding a piece of watermelon"),
    ]

    assert texts.count(caption) == 1
    assert max(figure_positions) < orphan < heading
    assert [warning for warning in tree.structure_warnings if warning.startswith("orphan_caption:")] == [
        f"orphan_caption: {caption}"
    ]


def test_real_fixture_chunks_keep_image_refs_types_and_spans() -> None:
    parsed = DoclingParser().adapt(load_docling_fixture(), "nhap-mon-ml.pdf")
    output = chunk_document(
        parsed.tree,
        "nhap-mon-ml",
        WordCounter(),
        splitter(),
        max_tokens=512,
        target_tokens=256,
    )

    assert sum(len(chunk.image_refs) for chunk in output.chunks) == 9
    assert sum(len(chunk.formula_refs) for chunk in output.chunks) == 1
    assert all(chunk.table_refs == [] for chunk in output.chunks)
    assert not any(
        warning.startswith("sentence_splitter_no_boundary")
        for warning in output.structure_warnings
    )
    assert any("list_item" in chunk.block_types for chunk in output.chunks)
    assert "Hình 2: Tập các bức ảnh và các mô tả về chúng." in output.normalized_full_text
    assert not any(chunk.text == "[figure]" for chunk in output.chunks)
    assert all(
        output.normalized_full_text[chunk.char_start : chunk.char_end] == chunk.text
        for chunk in output.chunks
    )


def test_adapter_repairs_pdf_floats_before_stitching_page_breaks() -> None:
    tree = DoclingParser().adapt(load_docling_fixture(), "nhap-mon-ml.pdf").tree
    texts = [node.text for node in tree.nodes]

    heading = texts.index("1.1.2 Bản chất của việc học, suy diễn, và phán đoán")
    introduction = next(
        index
        for index, node in enumerate(tree.nodes)
        if node.page == 7 and node.text.startswith("Con người")
    )
    definition = next(
        index
        for index, node in enumerate(tree.nodes)
        if node.page == 7 and node.text == "trong đó:"
    )
    stitched = next(index for index, text in enumerate(texts) if "đã thu thập trong quá khứ" in text)

    assert heading < introduction < definition < stitched
    assert not any(text.startswith("thập trong quá khứ") for text in texts)
    assert any("nhu cầu thực tế kia" in text for text in texts)
    assert any("tham số đã tốt chưa" in text for text in texts)
    assert any("Chúng ta cần xác định rõ mục tiêu" in text for text in texts)
    assert tree.parse_stats["pages_reordered"] == 1
    assert tree.parse_stats["page_breaks_stitched"] == 5
    assert [node.reading_order for node in tree.nodes] == list(range(len(tree.nodes)))


def test_pdf_glyph_repetitions_are_removed_without_touching_vietnamese_words() -> None:
    cases = {
        "tiêu chí P P P khi giải quyết": "tiêu chí P khi giải quyết",
        "T T T : Cần phán đoán": "T : Cần phán đoán",
        "{ x x x 1 , x x x 2 , ..., x x xN }": "{ x 1 , x 2 , ..., xN }",
        "các c c c là nhãn lớp": "các c là nhãn lớp",
        "học c c c trong tập": "học c trong tập",
        "lần n n n quan sát": "lần n quan sát",
        "ha ha ha": "ha ha ha",
        "Hà Nội và Hà Nam": "Hà Nội và Hà Nam",
    }

    class Document:
        def iterate_items(self):
            bbox = SimpleNamespace(l=0, t=10, r=10, b=0)
            provenance = [SimpleNamespace(page_no=1, bbox=bbox)]
            return [
                (SimpleNamespace(label="text", text=text, prov=provenance), 1)
                for text in cases
            ]

    tree = DoclingParser().adapt(Document(), "fixture.pdf").tree

    assert [node.text for node in tree.nodes] == list(cases.values())

    tree = DoclingParser().adapt(load_docling_fixture(), "nhap-mon-ml.pdf").tree
    repeated = re.compile(r"(?<![A-Za-z])([A-Za-z])(?: \1){2,}")
    assert not any(repeated.search(node.text) for node in tree.nodes)


def test_docx_does_not_collapse_pdf_glyphs() -> None:
    parsed = DoclingParser().adapt(load_docling_fixture(), "fixture.docx")
    tree = parsed.tree

    assert len(parsed.images) == 9
    assert sum(node.image_id is not None for node in tree.nodes) == 9
    assert any("P P P" in node.text for node in tree.nodes)
    assert tree.parse_stats["pages_reordered"] == 0
    assert tree.parse_stats["page_breaks_stitched"] == 0


def test_multi_column_guard_is_exercised_directly() -> None:
    right = DocumentNode("text", "right", 0, page=1, bbox=(320, 700, 530, 650))
    left = DocumentNode("text", "left", 1, page=1, bbox=(70, 700, 280, 650))

    assert not DoclingParser._is_single_column([right, left])
    repaired, pages_reordered = DoclingParser._repair_pdf_order([right, left])
    assert repaired == [right, left]
    assert pages_reordered == 0

    figure = DocumentNode("figure", "side figure", 1, page=1, bbox=(320, 700, 530, 650))
    assert DoclingParser._is_single_column([left, figure])
    assert not DoclingParser._is_single_column(
        [left, DocumentNode("text", "missing bbox", 2, page=1)]
    )


def test_pdf_row_order_uses_left_position_despite_small_top_offsets() -> None:
    right = DocumentNode("figure", "right", 0, page=1, bbox=(410, 785, 540, 690))
    left = DocumentNode("figure", "left", 1, page=1, bbox=(70, 780, 200, 680))
    middle = DocumentNode("figure", "middle", 2, page=1, bbox=(220, 790, 390, 685))

    repaired, pages_reordered = DoclingParser._repair_pdf_order([right, left, middle])

    assert [node.text for node in repaired] == ["left", "middle", "right"]
    assert pages_reordered == 1


def test_table_id_uses_normalized_cells_not_markdown_or_position() -> None:
    class Table:
        label = "table"
        prov = []

        def __init__(self, rows: list[list[str]], markdown: str) -> None:
            self.data = SimpleNamespace(
                grid=[[SimpleNamespace(text=cell) for cell in row] for row in rows]
            )
            self.markdown = markdown

        def export_to_markdown(self, **kwargs) -> str:
            return self.markdown

    class Document:
        def __init__(self, item) -> None:
            self.item = item

        def iterate_items(self):
            return [(self.item, 1)]

    def node(rows: list[list[str]], markdown: str):
        return DoclingParser().adapt(Document(Table(rows, markdown)), "table.docx").tree.nodes[0]

    first = node([[" Name ", "Va\u0301lue"], ["A|B", "1"]], "markdown version one")
    moved_or_reformatted = node([["Name", "Válue"], ["A|B", "1"]], "different | escaping")
    changed = node([["Name", "Válue"], ["A|B", "2"]], "markdown version one")

    assert first.table_id == moved_or_reformatted.table_id
    assert first.table_id != changed.table_id
    assert first.table_rows == [["Name", "Va\u0301lue"], ["A|B", "1"]]
    assert len(first.table_id or "") == 64

    text_node = DoclingParser().adapt(
        Document(SimpleNamespace(label="text", text="nội dung", prov=[])), "text.docx"
    ).tree.nodes[0]
    assert text_node.table_id is None and text_node.table_rows is None
