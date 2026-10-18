from pathlib import Path
from io import BytesIO

from PIL import Image

from doc2roadmap.application.phase_b.formula_images import CutFormulaImages
from doc2roadmap.domain.models import DocumentNode, DocumentTree
from doc2roadmap.infrastructure.media.formula_images import PdfiumFormulaRenderer
from tests.unit.presentation.test_a1_d02_packets import make_pdf


def test_pdfium_formula_crop_converts_bottom_left_pdf_coordinates(tmp_path):
    pdf = tmp_path / "formula.pdf"
    make_pdf(pdf, "1 0 0 rg 10 20 20 10 re f")
    node = DocumentNode("formula", "[formula]", 1, page=1, bbox=(10, 30, 30, 20),
                        raw_text="x", formula_id="same", bbox_origin="bottomleft")
    tree = DocumentTree([node])

    result = CutFormulaImages(PdfiumFormulaRenderer(), scale=2).execute(pdf, tree)

    assert result["cut_count"] == 1
    image = Image.open(BytesIO(next(iter(result["images"].values()))))
    assert image.size == (40, 20)
    red, green, blue = image.getpixel((20, 10))[:3]
    assert red > 240 and green < 20 and blue < 20

    top_left = PdfiumFormulaRenderer().render_formula(
        pdf, 1, (10, 170, 30, 180), scale=2, origin="topleft"
    )
    top_left_image = Image.open(BytesIO(top_left))
    assert top_left_image.size == image.size
    assert top_left_image.getpixel((20, 10))[:3] == image.getpixel((20, 10))[:3]


def test_formula_occurrences_do_not_overwrite_same_formula_id(tmp_path):
    class Renderer:
        def render_formula(self, _path, page, bbox, *, scale, origin=None):
            return f"{page}:{bbox}:{scale}:{origin}".encode()

    first = DocumentNode("formula", "[formula]", 3, page=1, bbox=(1, 4, 3, 2),
                         raw_text="x", formula_id="same")
    second = DocumentNode("formula", "[formula]", 9, page=2, bbox=(4, 8, 6, 5),
                          raw_text=None, formula_id="same")
    missing = DocumentNode("formula", "[formula]", 10, page=2, bbox=None,
                           raw_text="y", formula_id="other")

    result = CutFormulaImages(Renderer()).execute(Path("unused.pdf"), DocumentTree([first, second, missing]))

    assert [row["occurrence_id"] for row in result["formula_refs"]] == [
        "same@p1:r3", "same@p2:r9", "other@p2:r10"
    ]
    assert result["formula_refs"][0]["media_id"] != result["formula_refs"][1]["media_id"]
    assert result["formula_refs"][1]["raw_text_available"] is False
    assert result["formula_refs"][2]["status"] == "missing_bbox"


def test_batch_renderer_keeps_each_occurrence_image_attached_to_its_formula():
    class Renderer:
        def render_formula_batch(self, _path, formulas, *, scale):
            return [f"page={page};bbox={bbox};scale={scale}".encode()
                    for page, bbox, _origin in formulas]

    nodes = [
        DocumentNode("formula", "[formula]", i, page=i + 1, bbox=(i, 4, i + 2, 2),
                     raw_text=f"formula {i}", formula_id=f"id{i}")
        for i in range(2)
    ]

    result = CutFormulaImages(Renderer()).execute("unused.pdf", DocumentTree(nodes))

    assert result["formula_refs"][0]["media_id"] != result["formula_refs"][1]["media_id"]
