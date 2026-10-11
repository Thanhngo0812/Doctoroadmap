import json
from contextlib import closing
from pathlib import Path

import pypdfium2 as pdfium
import pytest

from doc2roadmap.infrastructure.parsing.pdf_scope import require_native_pdf
from doc2roadmap.infrastructure.parsing.nhe_parser import NheParser
from tests.unit.presentation.test_a1_d02_packets import make_pdf


def combine_pdf(tmp_path, contents):
    result = pdfium.PdfDocument.new()
    for i, content in enumerate(contents):
        path = tmp_path / f'page-{i}.pdf'
        make_pdf(path, content, image=True)
        with pdfium.PdfDocument(path) as part:
            result.import_pages(part)
    target = tmp_path / 'combined.pdf'
    result.save(target)
    result.close()
    return target.read_bytes()


NATIVE = 'BT /F1 12 Tf 30 150 Td (Native body line.) Tj ET'
IMAGE = 'q 200 0 0 200 0 0 cm /I Do Q'


def test_original_pdf_with_image_cover_and_blank_page_is_accepted(tmp_path):
    source = combine_pdf(tmp_path, [IMAGE, NATIVE, NATIVE, 'q Q'])
    assert require_native_pdf(source)['pdf_type'] == 'native'
    assert require_native_pdf(combine_pdf(tmp_path, [IMAGE, NATIVE]))['pdf_type'] == 'native'


@pytest.mark.parametrize('contents', [
    [IMAGE, IMAGE, NATIVE],
    [IMAGE + ' BT /F1 12 Tf 3 Tr 30 150 Td (OCR layer) Tj ET', NATIVE, NATIVE],
])
def test_scan_is_rejected_even_with_some_native_pages(tmp_path, contents):
    with pytest.raises(ValueError, match='bản quét'):
        require_native_pdf(combine_pdf(tmp_path, contents))


def test_models_missing_or_corrupt_stop_before_unpickling(tmp_path):
    with pytest.raises(ValueError, match='SHA-256'):
        NheParser(tmp_path)
    (tmp_path / 'heading.joblib').write_bytes(b'not a trusted model')
    with pytest.raises(ValueError, match='SHA-256'):
        NheParser(tmp_path)


def test_surrogate_pair_becomes_one_scalar_without_changing_line_count(tmp_path, monkeypatch):
    from doc2roadmap.infrastructure.parsing.nhe import doc_nhe as light
    path = tmp_path / 'symbol.pdf'
    make_pdf(path, 'BT /F1 12 Tf 30 150 Td (AB) Tj 0 -20 Td (C) Tj ET')
    original = light.raw.FPDFText_GetUnicode
    def unicode(text, index):
        return {0: 0xD835, 1: 0xDC65}.get(index, original(text, index))
    monkeypatch.setattr(light.raw, 'FPDFText_GetUnicode', unicode)
    with pdfium.PdfDocument(path) as pdf:
        with closing(pdf[0]) as page:
            lines = light.page_lines(page)
    texts = [''.join(c.ch for c in line) for line in lines]
    assert texts == ['𝑥', 'C']
    json.dumps(texts, ensure_ascii=False).encode('utf-8')


def test_product_adapter_returns_asset_bytes_with_matching_ids(tmp_path):
    import hashlib
    path = tmp_path / 'book.pdf'
    make_pdf(path, 'q 50 0 0 50 0 0 cm /I Do Q ' + NATIVE, image=True)
    parsed = NheParser().parse(path.read_bytes(), path.name)
    ids = {node.image_id for node in parsed.tree.nodes if node.image_id}
    assert ids and ids == set(parsed.images)
    assert all(hashlib.sha256(payload).hexdigest() == key for key, payload in parsed.images.items())
    assert parsed.tree.parse_stats['page_count'] == 1


def test_real_pdf_tounicode_supplementary_math_character_is_utf8_safe():
    from doc2roadmap.infrastructure.parsing.nhe import doc_nhe as light
    content = b'BT /F1 12 Tf 30 150 Td (A) Tj 0 -20 Td (B) Tj ET'
    cmap = b'/CIDInit /ProcSet findresource begin 12 dict begin begincmap /CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def /CMapName /Test def /CMapType 2 def 1 begincodespacerange <00> <FF> endcodespacerange 2 beginbfchar <41> <D835DC65> <42> <0042> endbfchar endcmap CMapName currentdict /CMap defineresource pop end end'
    objects = [b'<< /Type /Catalog /Pages 2 0 R >>', b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
               b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
               b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /ToUnicode 6 0 R >>',
               b'<< /Length ' + str(len(content)).encode() + b' >>\nstream\n' + content + b'\nendstream',
               b'<< /Length ' + str(len(cmap)).encode() + b' >>\nstream\n' + cmap + b'\nendstream']
    payload = b'%PDF-1.4\n'
    offsets = []
    for i, obj in enumerate(objects, 1):
        offsets.append(len(payload))
        payload += f'{i} 0 obj\n'.encode() + obj + b'\nendobj\n'
    xref = len(payload)
    payload += b'xref\n0 7\n0000000000 65535 f \n'
    payload += b''.join(f'{p:010} 00000 n \n'.encode() for p in offsets)
    payload += f'trailer\n<< /Root 1 0 R /Size 7 >>\nstartxref\n{xref}\n%%EOF'.encode()
    with pdfium.PdfDocument(payload) as pdf:
        with closing(pdf[0]) as page:
            texts = [''.join(c.ch for c in line) for line in light.page_lines(page)]
    assert ''.join(texts) == '𝑥B'
    json.dumps(texts, ensure_ascii=False).encode('utf-8')


def test_small_book_matches_frozen_research_r2_full_tree_and_chunks(tmp_path, monkeypatch):
    import sys
    import joblib
    root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(root / 'scripts/a1-d02'))
    sys.path.insert(0, str(root / 'scripts/doc-nhe'))
    from pha3 import extract_rows, tree_for
    from doc2roadmap.domain.chunking import chunk_document
    from tests.conftest import WordCounter, splitter
    path = tmp_path / 'small.pdf'
    make_pdf(path, 'q 50 0 0 50 0 0 cm /I Do Q ' + NATIVE, image=True)
    rows, figures, pages = extract_rows(path)
    # Keep the frozen research algorithm, but resolve its full models to versioned assets.
    load_model = joblib.load
    models = {'full-lightgbm.joblib': root / 'vendor/a1-nhe/heading.joblib',
              'full.joblib': root / 'vendor/a1-nhe/join.joblib'}
    monkeypatch.setattr(joblib, 'load', lambda filename, *a, **kw:
                        load_model(models.get(Path(filename).name, filename), *a, **kw))
    reference, *_ = tree_for(path, 'synthetic-full', tmp_path / 'reference', rows, figures, pages, 'grammar')
    product = NheParser().parse(path.read_bytes(), path.name).tree
    assert [n.to_dict() for n in product.nodes] == [n.to_dict() for n in reference.nodes]
    actual = chunk_document(product, 'small', WordCounter(), splitter())
    expected = chunk_document(reference, 'small', WordCounter(), splitter())
    assert [s.to_dict() for s in actual.sections] == [s.to_dict() for s in expected.sections]
    assert [c.to_dict() for c in actual.chunks] == [c.to_dict() for c in expected.chunks]
