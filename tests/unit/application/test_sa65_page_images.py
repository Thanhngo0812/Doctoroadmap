"""SA-65: page pictures of formula pages are captured at build time and read back by SA-64's adapter."""
import hashlib
import json
import types
from pathlib import Path

import pytest

from doc2roadmap.application.phase_b.page_images import CapturePageImages, PageImageMismatch, formula_pages
from doc2roadmap.domain.models import DocumentNode, DocumentTree
from doc2roadmap.infrastructure.artifacts.page_images import ArtifactPageImages
from doc2roadmap.infrastructure.media.page_images import PdfiumPageRenderer
from tests.unit.presentation.test_a1_d02_packets import make_pdf


def chunk(page, text, block_types=("paragraph",)):
    return types.SimpleNamespace(page=page, text=text, block_types=list(block_types))


class FakeRenderer:
    def __init__(self, pages=6, texts=None):
        self.pages, self.texts, self.rendered = pages, texts or {}, []

    def page_count(self, pdf):
        return self.pages

    def page_text(self, pdf, page):
        return self.texts.get(page, "")

    def render_pages(self, pdf, pages, *, scale, quality):
        self.rendered.append((list(pages), scale, quality))
        return {page: f"jpeg-{page}".encode() for page in pages if 1 <= page <= self.pages}


TREE = DocumentTree([DocumentNode("text", "a", 1, page=1), DocumentNode("formula", "[formula]", 2, page=3),
                     DocumentNode("formula", "[formula]", 3, page=3), DocumentNode("text", "b", 4, page=5)])
CHUNKS = [chunk(2, "Văn bản không công thức."), chunk(4, "Tính $x$ là [formula] trong bước này"), chunk(5, "tiếp")]


def test_only_formula_pages_are_captured_once_each_at_scale_1_5_quality_80(tmp_path):
    assert formula_pages(TREE, CHUNKS) == [3, 4]          # a formula node on p3 (twice), a "[formula]" chunk on p4
    renderer = FakeRenderer()
    result = CapturePageImages(renderer).execute("x.pdf", TREE, CHUNKS, root=tmp_path, doc_id="doc-1", parse_version=2)
    assert renderer.rendered == [([3, 4], 1.5, 80)]
    assert result["page_count"] == 2
    index = json.loads((tmp_path / "phase_b/page_images/doc-1/parse-v2/index.json").read_text(encoding="utf-8"))
    assert sorted(index["pages"]) == ["3", "4"] and index["format"] == "jpeg" and index["scale"] == 1.5
    assert index["pages"]["3"]["file"] == "pages/p003.jpg"
    assert index["pages"]["3"]["sha256"] == hashlib.sha256(b"jpeg-3").hexdigest()


def test_book_without_formulas_writes_nothing(tmp_path):
    result = CapturePageImages(FakeRenderer()).execute(
        "x.pdf", DocumentTree([DocumentNode("text", "a", 1, page=1)]), [chunk(1, "chữ")],
        root=tmp_path, doc_id="doc-1", parse_version=1)
    assert result["page_count"] == 0 and not (tmp_path / "phase_b").exists()


def test_round_trip_with_the_sa64_reader_returns_exact_bytes(tmp_path):
    CapturePageImages(FakeRenderer()).execute("x.pdf", TREE, CHUNKS, root=tmp_path, doc_id="doc-1", parse_version=2)
    reader = ArtifactPageImages(tmp_path)
    assert reader.get("doc-1", 2, 3) == b"jpeg-3" and reader.get("doc-1", 2, 4) == b"jpeg-4"
    assert reader.get("doc-1", 2, 1) is None and reader.get("doc-1", 3, 3) is None and reader.get("other", 2, 3) is None
    (tmp_path / "phase_b/page_images/doc-1/parse-v2/pages/p003.jpg").write_bytes(b"tampered")
    assert reader.get("doc-1", 2, 3) is None                # the stored sha256 is really what the reader checks


def test_rerun_does_not_rewrite_files_with_the_same_sha256(tmp_path, monkeypatch):
    use_case = CapturePageImages(FakeRenderer())
    use_case.execute("x.pdf", TREE, CHUNKS, root=tmp_path, doc_id="doc-1", parse_version=2)
    writes = []
    original = Path.write_bytes
    monkeypatch.setattr(Path, "write_bytes", lambda self, data: writes.append(self.name) or original(self, data))
    original_text = Path.write_text
    monkeypatch.setattr(Path, "write_text", lambda self, *a, **k: writes.append(self.name) or original_text(self, *a, **k))
    use_case.execute("x.pdf", TREE, CHUNKS, root=tmp_path, doc_id="doc-1", parse_version=2)
    assert writes == []
    monkeypatch.setattr(FakeRenderer, "render_pages", lambda self, pdf, pages, *, scale, quality: {p: b"new-%d" % p for p in pages})
    use_case.execute("x.pdf", TREE, CHUNKS, root=tmp_path, doc_id="doc-1", parse_version=2)
    assert sorted(writes) == ["index.json", "p003.jpg", "p004.jpg"]   # changed bytes are written


def test_parse_versions_are_kept_apart(tmp_path):
    use_case = CapturePageImages(FakeRenderer())
    use_case.execute("x.pdf", TREE, CHUNKS, root=tmp_path, doc_id="doc-1", parse_version=1)
    use_case.execute("x.pdf", TREE, CHUNKS, root=tmp_path, doc_id="doc-1", parse_version=2)
    assert sorted(p.name for p in (tmp_path / "phase_b/page_images/doc-1").iterdir()) == ["parse-v1", "parse-v2"]


def test_bad_doc_id_and_version_are_rejected(tmp_path):
    use_case = CapturePageImages(FakeRenderer())
    with pytest.raises(ValueError):
        use_case.execute("x.pdf", TREE, CHUNKS, root=tmp_path, doc_id="../evil", parse_version=1)
    with pytest.raises(ValueError):
        use_case.execute("x.pdf", TREE, CHUNKS, root=tmp_path, doc_id="doc-1", parse_version=0)


GOOD_TEXT = {2: "Văn bản không công thức, rất dài.", 4: "Tính x là trong bước này"}
SAMPLES = [chunk(2, "Văn bản không công thức, rất dài để kiểm tra khớp trang"), chunk(4, "Tính x là formula trong bước này nữa để kiểm tra khớp")]


def test_verify_accepts_a_matching_pdf_and_refuses_a_shifted_or_shorter_one(tmp_path):
    ok = FakeRenderer(pages=5, texts={2: "văn bản không công thức, rất dài để kiểm tra khớp trang!", 4: "TÍNH x là formula trong bước này nữa để kiểm tra khớp"})
    tree = DocumentTree([DocumentNode("formula", "[formula]", 1, page=4)], parse_stats={"page_count": 5})
    CapturePageImages(ok).execute("x.pdf", tree, SAMPLES, root=tmp_path, doc_id="d", parse_version=1, verify=True)
    assert (tmp_path / "phase_b/page_images/d/parse-v1/index.json").exists()

    shorter = FakeRenderer(pages=4, texts=ok.texts)
    shifted = FakeRenderer(pages=5, texts={3: ok.texts[2], 5: ok.texts[4]})
    for bad, other in ((shorter, "d2"), (shifted, "d3")):
        with pytest.raises(PageImageMismatch):
            CapturePageImages(bad).execute("x.pdf", tree, SAMPLES, root=tmp_path, doc_id=other, parse_version=1, verify=True)
        assert not (tmp_path / "phase_b/page_images" / other).exists() and bad.rendered == []


def test_verify_refuses_when_there_is_nothing_to_compare(tmp_path):
    tree = DocumentTree([DocumentNode("formula", "[formula]", 1, page=1)], parse_stats={"page_count": 2})
    with pytest.raises(PageImageMismatch):
        CapturePageImages(FakeRenderer(pages=2)).execute("x.pdf", tree, [chunk(1, "ngắn")], root=tmp_path,
                                                         doc_id="d", parse_version=1, verify=True)


def test_real_pdf_round_trip_with_pdfium(tmp_path):
    pdf = tmp_path / "book.pdf"
    make_pdf(pdf, "BT /F1 12 Tf 30 150 Td (Chapter 1 about gradient descent and its many uses) Tj ET")
    tree = DocumentTree([DocumentNode("formula", "[formula]", 1, page=1)], parse_stats={"page_count": 1})
    chunks = [chunk(1, "Chapter 1 about gradient descent and its many uses")]
    renderer = PdfiumPageRenderer()
    assert renderer.page_count(pdf) == 1 and "gradient" in renderer.page_text(pdf, 1)
    root = tmp_path / "art"
    result = CapturePageImages(renderer).execute(pdf, tree, chunks, root=root, doc_id="book", parse_version=1, verify=True)
    assert result["page_count"] == 1
    data = ArtifactPageImages(root).get("book", 1, 1)
    assert data[:3] == b"\xff\xd8\xff"                          # a real JPEG
    from io import BytesIO
    from PIL import Image
    assert Image.open(BytesIO(data)).size == (300, 300)         # 200 pt page at scale 1.5
    assert renderer.render_pages(pdf, [1, 9], scale=1.5, quality=80).keys() == {1}   # absent page is not invented


def test_cli_page_images_refuses_a_mismatched_pdf_and_writes_nothing(tmp_path, monkeypatch):
    from doc2roadmap.presentation.cli import phase_b
    import argparse

    commands = argparse.ArgumentParser().add_subparsers()
    phase_b.configure(commands)
    parser = commands.choices["phase-b"]
    args = parser.parse_args(["page-images", "--doc", "book", "--pdf", "x.pdf"])
    assert args.doc_id == "book" and args.pdf == Path("x.pdf")

    pdf = tmp_path / "book.pdf"
    make_pdf(pdf, "BT /F1 12 Tf 30 150 Td (Totally different words here) Tj ET")
    tree = DocumentTree([DocumentNode("formula", "[formula]", 1, page=1)], parse_stats={"page_count": 1})
    stored = types.SimpleNamespace(manifest={"parse_version": 3, "config": {"chunks_version": 1}},
                                   result=types.SimpleNamespace(chunks=[chunk(1, "Chapter 1 about gradient descent and its many uses")]))
    artifacts = types.SimpleNamespace(load_graph=lambda doc, v: stored, load_chunks=lambda doc, v: stored)
    runtime = types.SimpleNamespace(artifacts=artifacts, settings=types.SimpleNamespace(artifact_dir=tmp_path / "art"))
    graph = types.SimpleNamespace(tree=tree, graph_version=1)
    monkeypatch.setattr(phase_b, "PhaseBRuntime", lambda **kw: runtime)
    runtime.graph = lambda doc, version: graph
    args = parser.parse_args(["page-images", "--doc", "book", "--pdf", str(pdf)])
    with pytest.raises(PageImageMismatch):
        phase_b.run(args)
    assert not (tmp_path / "art").exists()
    stored.result.chunks = [chunk(1, "Chapter 1 about gradient descent and its many uses")]
    make_pdf(pdf, "BT /F1 12 Tf 30 150 Td (Chapter 1 about gradient descent and its many uses) Tj ET")
    out = phase_b.run(args)
    assert out["page_count"] == 1 and ArtifactPageImages(tmp_path / "art").get("book", 3, 1)
