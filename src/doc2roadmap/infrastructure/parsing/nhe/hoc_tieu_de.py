"""Frozen 73-feature heading inference matrix."""
from collections import defaultdict
import numpy as np
from . import doc_nhe as light

BASE_NAMES = ('size_ratio', 'bold', 'italic', 'uppercase', 'digits', 'chars', 'tokens',
              'left', 'width', 'center', 'vertical', 'gap_before', 'gap_after',
              'numbered', 'enumerator', 'terminal', 'viet_accent', 'math', 'mono',
              'symbols', 'single', 'repeat', 'indent')
CONTEXT_NAMES = tuple(f'{side}_{name}' for side in ('prev', 'next') for name in BASE_NAMES)
FEATURE_NAMES = BASE_NAMES + CONTEXT_NAMES + ('has_prev', 'has_next', 'prev_font_diff', 'next_font_diff')


def feature_matrix(rows, body):
    repeats = defaultdict(set)
    margins = defaultdict(list)
    for r in rows:
        repeats[light.norm_repeat(r['text'])].add(r['page'])
        margins[r['page']].append(r['x0'])
    lefts = {p: float(np.percentile(v, 20)) for p, v in margins.items()}
    base = []
    for i, r in enumerate(rows):
        text = r['text']
        letters = [c for c in text if c.isalpha()]
        size, width, height = max(r['size'], 1), max(r.get('width') or 600, 1), max(r['height'], 1)
        prev = rows[i-1] if i and rows[i-1]['page'] == r['page'] else None
        nxt = rows[i+1] if i+1 < len(rows) and rows[i+1]['page'] == r['page'] else None
        base.append([r['size']/max(body, 1), float(r['bold']), r.get('italic', 0),
            sum(c.isupper() for c in letters)/max(len(letters), 1), sum(c.isdigit() for c in text)/max(len(text), 1),
            np.log1p(r['chars']), np.log1p(r['tokens']), r['x0']/width, (r['x1']-r['x0'])/width,
            abs((r['x0']+r['x1'])/2-width/2)/width, r['top']/height,
            np.clip((prev['bottom']-r['top'])/size, -5, 20) if prev else 0,
            np.clip((r['bottom']-nxt['top'])/size, -5, 20) if nxt else 0,
            float(bool(light.HEADING_NUMBER.match(text))), float(bool(light.ENUMERATOR.match(text))),
            float(text.endswith(('.', ',', ';', ':', '?', '!'))), r['viet']/max(r['tokens'], 1), r['math'], r['mono'],
            r['symbol_share'], r['single'], np.log1p(len(repeats[light.norm_repeat(text)])), (r['x0']-lefts[r['page']])/size])
    x = np.asarray(base, dtype=np.float32).reshape((-1, len(BASE_NAMES)))
    previous, following = np.zeros_like(x), np.zeros_like(x)
    flags = np.zeros((len(rows), 4), dtype=np.float32)
    for i, r in enumerate(rows):
        if i and rows[i-1]['page'] == r['page']:
            previous[i] = x[i-1]
            flags[i, 0], flags[i, 2] = 1, r.get('font') != rows[i-1].get('font')
        if i+1 < len(rows) and rows[i+1]['page'] == r['page']:
            following[i] = x[i+1]
            flags[i, 1], flags[i, 3] = 1, r.get('font') != rows[i+1].get('font')
    return np.concatenate((x, previous, following, flags), axis=1)
