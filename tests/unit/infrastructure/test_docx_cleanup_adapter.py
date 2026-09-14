from io import BytesIO
from types import SimpleNamespace
from zipfile import ZipFile

from PIL import Image

from doc2roadmap.domain.chunking import chunk_document
from doc2roadmap.infrastructure.parsing import DoclingParser

from tests.conftest import WordCounter, load_docling_fixture, splitter


class _Document:
    def __init__(self, *items) -> None:
        self.items = items

    def iterate_items(self):
        return [(item, 1) for item in self.items]


class _Picture:
    label = "picture"
    prov = []

    def __init__(self, image) -> None:
        self.image = image

    def get_image(self, **_):
        return self.image


def _text(value: str, *, label: str = "text", prov=None):
    return SimpleNamespace(label=label, text=value, orig="", prov=prov or [])


def test_docx_extracts_available_images_and_warns_when_bytes_are_missing() -> None:
    document = _Document(_Picture(Image.new("RGB", (2, 2), "red")), _Picture(None))

    parsed = DoclingParser().adapt(document, "fixture.docx")
    figures = [node for node in parsed.tree.nodes if node.node_type == "figure"]

    assert len(parsed.images) == 1
    assert figures[0].image_id in parsed.images
    assert figures[1].image_id is None and figures[1].text == "[figure]"
    assert any(
        warning.startswith("missing_image:")
        and "LibreOffice" in warning
        and "bytes unavailable" in warning
        for warning in parsed.tree.structure_warnings
    )


def test_docx_drawingml_shape_is_reported_by_the_system_channel() -> None:
    source = BytesIO()
    with ZipFile(source, "w") as archive:
        archive.writestr(
            "word/document.xml",
            '<a:graphicData uri="http://schemas.microsoft.com/office/word/2010/'
            'wordprocessingShape"><wps:wsp/></a:graphicData>',
        )
    parser = DoclingParser()
    parser._converter_instance = SimpleNamespace(
        convert=lambda _: SimpleNamespace(document=_Document(_text("nội dung")))
    )

    parsed = parser.parse(source.getvalue(), "shape.docx")

    assert parsed.tree.structure_warnings == [
        "missing_image: DOCX DrawingML shape bytes unavailable; "
        "install LibreOffice to render it"
    ]


def test_docx_fixture_extracts_all_three_embedded_pngs() -> None:
    parsed = DoclingParser().adapt(
        load_docling_fixture("baocao-canhan"), "baocao-canhan.docx"
    )
    figures = [node for node in parsed.tree.nodes if node.node_type == "figure"]

    assert len(figures) == len(parsed.images) == 3
    assert all(node.image_id in parsed.images for node in figures)
    assert parsed.tree.parse_stats["images_extracted"] == 3
    assert parsed.tree.parse_stats["runs_stitched"] == 56
    assert any(
        node.text.startswith("+ Triển khai dự án bằng Docker Compose, thực hiện kiểm thử")
        for node in parsed.tree.nodes
    )
    assert not any(
        warning.startswith("missing_image:")
        for warning in parsed.tree.structure_warnings
    )


def test_unpositioned_formatting_runs_stitch_in_a_chain_with_guards() -> None:
    positioned = SimpleNamespace(
        page_no=1,
        bbox=SimpleNamespace(l=0, t=10, r=10, b=0),
    )
    document = _Document(
        _text("+ Triển khai dự án bằng"),
        _text("Docker Compose"),
        _text(", thực hiện kiểm thử đầu cuối."),
        _text("+ bullet một"),
        _text("+ bullet hai."),
        _text("Câu đã xong."),
        _text("Câu kế tiếp"),
        _text("có bbox", prov=[positioned]),
        _text("không được nối", prov=[positioned]),
    )

    tree = DoclingParser().adapt(document, "runs.docx").tree

    assert tree.nodes[0].text == (
        "+ Triển khai dự án bằng Docker Compose, thực hiện kiểm thử đầu cuối."
    )
    assert tree.nodes[1].text == "+ bullet một"
    assert tree.nodes[2].text == "+ bullet hai."
    assert tree.nodes[3].text == "Câu đã xong."
    assert tree.nodes[4].text == "Câu kế tiếp"
    assert [node.text for node in tree.nodes[-2:]] == ["có bbox", "không được nối"]
    assert tree.parse_stats["runs_stitched"] == 2


def test_private_use_bullet_is_removed_only_at_list_start_after_symbol_mapping() -> None:
    parsed = DoclingParser().adapt(
        _Document(
            _text("\uf097   nội dung", label="list_item"),
            _text("\uf0b7 mục Symbol", label="list_item"),
            _text("giữa \uf097 câu", label="list_item"),
        ),
        "slide.pdf",
    )

    assert [node.text for node in parsed.tree.nodes] == [
        "nội dung",
        "• mục Symbol",
        "giữa \uf097 câu",
    ]
    assert parsed.tree.parse_stats["stripped_pua_bullets"] == 1
    assert "remaining_private_use: 1" in parsed.tree.structure_warnings


def test_slide_fixture_strips_all_72_template_bullets() -> None:
    tree = DoclingParser().adapt(
        load_docling_fixture("naive-bayes"), "naive-bayes.pdf"
    ).tree
    output = chunk_document(tree, "naive-bayes", WordCounter(), splitter())

    assert tree.parse_stats["stripped_pua_bullets"] == 72
    assert not any("\uf097" in chunk.text for chunk in output.chunks)
