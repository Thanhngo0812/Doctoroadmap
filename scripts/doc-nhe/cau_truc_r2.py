"""A1 R2 research fork: preserve source rows across heading decisions.

Grouping geometry is the frozen v4 reader's, not a new reading-order algorithm.
No production integration. Keep the v1 parser/model fingerprint unchanged.
"""
from collections import defaultdict
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/thu-a1'))
sys.path.insert(0, str(ROOT / 'src'))
import doc_nhe as baseline
from doc2roadmap.infrastructure.parsing.docling_parser import _SYMBOL_TRANSLATION

VERSION = 'a1-r2-row-preservation-v2'


def normalize_row(text):
    """Map legacy glyph encoding, never deduplicate letters without geometry.

    Do not strip HTML comments either: PDF text can contain literal code.
    Whitespace and the inherited Symbol/font-Vietnamese mapping are explicit.
    """
    return re.sub(r'\s+', ' ', text.translate(_SYMBOL_TRANSLATION)).strip().replace('ƣ', 'ư').replace('Ƣ', 'Ư')


def row_types(rows, body, heading_flags, protect_types=False):
    if heading_flags is not None and len(heading_flags) != len(rows):
        raise ValueError('heading prediction count must equal retained row count')
    kinds, blocked = [], []
    for i, (row, standalone) in enumerate(zip(rows, baseline.standalone_flags(rows))):
        kind = baseline.classify_row(row, standalone, body, headings=heading_flags is None)
        if heading_flags is not None and heading_flags[i]:
            if protect_types and (kind in {'formula', 'caption'} or row['mono'] >= .6):
                blocked.append(i)
            else:
                kind = 'section_header'
        kinds.append(kind)
    return kinds, blocked


def group_rows(rows, figures, pages, heading_flags=None, *, protect_types=False,
               prepare_rows=baseline.prepare_rows):
    """Return research nodes with retained-row provenance and union bbox.

    source_rows indexes the output of baseline.prepare_rows, not PDF characters.
    Bbox follows DocumentNode: left, top, right, bottom (PDF bottom-left origin).
    Figures keep legacy end placement explicitly until the reading-order round.
    """
    retained, body = prepare_rows(rows)
    kinds, blocked = row_types(retained, body, heading_flags, protect_types)
    by_page = defaultdict(list)
    for row in retained:
        by_page[row['page']].append(row)
    margins = {}
    for page, page_rows in by_page.items():
        lefts = sorted(r['x0'] for r in page_rows if r['letters'] >= 3)
        rights = sorted(r['x1'] for r in page_rows if r['letters'] >= 3)
        margins[page] = (lefts[len(lefts)//5] if lefts else 0., rights[-(len(rights)//5)-1] if rights else 0.)
    nodes, previous = [], None
    for index, (row, kind) in enumerate(zip(retained, kinds)):
        text = normalize_row(row['text'])
        gap = previous['bottom'] - row['top'] if previous and previous['page'] == row['page'] else None
        height = max(row['size'], 1.)
        last = nodes[-1] if nodes else None
        joinable = last is not None and gap is not None and -height < gap < 1.2 * height
        left, right = margins[row['page']]
        ended = last is not None and last['text'].endswith(('.', ':', '?', '!'))
        new_paragraph = ended and (row['x0'] > left + .8 * height or previous['x1'] < right - 3 * height)
        join_text = (joinable and kind == 'text' and last['node_type'] in {'text', 'list_item', 'footnote'}
                     and abs(row['size'] - previous['size']) <= .15 * height and not new_paragraph)
        join_formula = (kind == 'formula' and last is not None and last['node_type'] == 'formula'
                        and gap is not None and -height < gap < 2.5 * height)
        join_heading = (joinable and kind == 'section_header' and last['node_type'] == 'section_header'
                        and not baseline.HEADING_NUMBER.match(row['text'])
                        and not baseline.CHAPTER_LABEL.fullmatch(last['text'].strip()))
        bbox = [row['x0'], row['top'], row['x1'], row['bottom']]
        if join_text or join_formula or join_heading:
            last['text'] += ' ' + text
            last['source_rows'].append(index)
            a = last['bbox']
            last['bbox'] = [min(a[0], bbox[0]), max(a[1], bbox[1]), max(a[2], bbox[2]), min(a[3], bbox[3])]
        else:
            nodes.append({'node_type': kind, 'text': text, 'page': row['page'], 'x0': row['x0'],
                          'level': baseline.heading_level(text) if kind == 'section_header' else None,
                          'bbox': bbox, 'source_rows': [index]})
        previous = row
    for index, figure in enumerate(figures):
        left, bottom, right, top = figure['bbox']  # PDFium object bounds differ in tuple order
        nodes.append({'node_type': 'figure', 'text': '', 'page': figure['page'], 'x0': figure['bbox'][0],
                      'level': None, 'bbox': [left, top, right, bottom], 'source_rows': [], 'source_figure': index})
    return nodes, {'version': VERSION, 'pages': pages, 'body_size': body,
                   'repeated_lines_removed': len(rows)-len(retained), 'blocked_heading_rows': blocked,
                   'known_limits': ['legacy_header_footer_filter', 'legacy_reading_order',
                                    'figures_appended_without_assets', 'tables_not_recognized']}


def parse(path, heading_predictor=None, *, protect_types=False):
    rows, figures, pages = baseline.extract_rows(path)
    retained, body = baseline.prepare_rows(rows)
    flags = heading_predictor(retained, body) if heading_predictor is not None else None
    return group_rows(rows, figures, pages, flags, protect_types=protect_types)
