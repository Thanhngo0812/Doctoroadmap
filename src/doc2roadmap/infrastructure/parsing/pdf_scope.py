"""Native PDF scope gate shared by A1 readers, independent of filenames."""
from collections import Counter
from contextlib import closing
import ctypes

import pypdfium2 as pdfium
import pypdfium2.raw as raw


def page_signals(page, number):
    width, height = page.get_size()
    coverage = 0.0
    for obj in page.get_objects(max_depth=15):
        if obj.type == raw.FPDF_PAGEOBJ_IMAGE:
            left, bottom, right, top = obj.get_bounds()
            coverage = max(coverage, max(0, min(width, right) - max(0, left))
                           * max(0, min(height, top) - max(0, bottom)) / max(width * height, 1))
    letters = hidden = glyphless = 0
    buffer = ctypes.create_string_buffer(256)
    flags = ctypes.c_int()
    with closing(page.get_textpage()) as text:
        for index in range(text.count_chars()):
            if not chr(raw.FPDFText_GetUnicode(text.raw, index)).isalpha():
                continue
            letters += 1
            obj = raw.FPDFText_GetTextObject(text.raw, index)
            hidden += bool(obj) and raw.FPDFTextObj_GetTextRenderMode(obj) == 3
            raw.FPDFText_GetFontInfo(text.raw, index, buffer, 256, ctypes.byref(flags))
            glyphless += b'GlyphLessFont' in buffer.value
    if not letters:
        kind = 'scan_no_text' if coverage >= .8 else 'no_text'
    elif hidden / letters >= .5 or glyphless / letters >= .5:
        kind = 'scan_ocr' if coverage >= .8 else 'hidden_text_without_full_image'
    else:
        kind = 'native'
    return dict(page=number, type=kind, letters=letters, hidden_render_3=hidden,
                glyphless=glyphless, max_image_coverage=coverage)


def route_pdf(source):
    with pdfium.PdfDocument(source) as pdf:
        pages = []
        for index in range(len(pdf)):
            with closing(pdf[index]) as page:
                pages.append(page_signals(page, index + 1))
    counts = Counter(p['type'] for p in pages)
    content = len(pages) - counts['no_text']
    if not content:
        kind = 'no_text'
    elif counts['scan_ocr'] or counts['hidden_text_without_full_image']:
        kind = 'scan_ocr'
    elif counts['scan_no_text'] > content * .5:
        kind = 'scan_no_text'
    elif counts['native']:
        kind = 'native'
    else:
        kind = 'mixed'
    return dict(pdf_type=kind, pages=pages, page_counts=dict(counts))


def require_native_pdf(source):
    result = route_pdf(source)
    if result['pdf_type'] != 'native':
        raise ValueError('PDF không phải PDF gốc; bản quét/không xác định nằm ngoài phạm vi A1: '
                         + result['pdf_type'])
    return result
