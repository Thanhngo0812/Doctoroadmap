"""Pairwise heading continuation, separate from the row heading classifier."""
from copy import deepcopy
import re
import numpy as np
import cau_truc_r2 as r2

FEATURES = ('gap', 'left_delta', 'right_delta', 'center_delta', 'overlap',
            'size_ratio', 'same_font', 'same_bold', 'same_italic', 'first_bold', 'second_bold',
            'first_chars', 'second_chars', 'first_uppercase', 'second_uppercase',
            'first_numbered', 'second_numbered', 'first_chapter', 'first_terminal', 'second_lower')


def pair_features(a, b):
    scale = max(a['size'], b['size'], 1)
    overlap = max(0, min(a['x1'], b['x1']) - max(a['x0'], b['x0']))
    upper = lambda s: sum(c.isupper() for c in s)/max(sum(c.isalpha() for c in s), 1)
    return [(a['bottom']-b['top'])/scale, (b['x0']-a['x0'])/scale,
            (b['x1']-a['x1'])/scale, ((b['x0']+b['x1'])-(a['x0']+a['x1']))/(2*scale),
            overlap/max(min(a['x1']-a['x0'], b['x1']-b['x0']), 1), b['size']/max(a['size'], 1),
            float(a.get('font') == b.get('font')), float(a['bold'] == b['bold']),
            float(a.get('italic') == b.get('italic')), float(a['bold']), float(b['bold']),
            np.log1p(len(a['text'])), np.log1p(len(b['text'])), upper(a['text']), upper(b['text']),
            float(bool(r2.baseline.HEADING_NUMBER.match(a['text']))),
            float(bool(r2.baseline.HEADING_NUMBER.match(b['text']))),
            float(bool(r2.baseline.CHAPTER_LABEL.fullmatch(a['text'].strip()))),
            float(a['text'].endswith(('.', ':', ';', '?', '!'))),
            float(bool(re.match(r'^\s*[a-zà-ỹ]', b['text'])))]


def pair_labels(rows, labels):
    result = np.full(len(rows), -1, dtype=np.int8)
    for i in range(1, len(rows)):
        a, b = labels[i-1], labels[i]
        if rows[i-1]['page'] != rows[i]['page'] or a['label'] != 'heading' or b['label'] != 'heading':
            continue
        first, second = ({m['node'] for m in row['matches']} for row in (a, b))
        if len(first) == len(second) == 1:
            result[i] = int(first == second)
    return result


def matrix(rows):
    x = np.zeros((len(rows), len(FEATURES)), dtype=np.float32)
    for i in range(1, len(rows)):
        if rows[i-1]['page'] == rows[i]['page']:
            x[i] = pair_features(rows[i-1], rows[i])
    return x


def rule(a, b, typography=False):
    if a['page'] != b['page'] or r2.baseline.HEADING_NUMBER.match(b['text']):
        return False
    scale = max(b['size'], 1)
    if not -scale < a['bottom']-b['top'] < 1.2*scale:
        return False
    if not typography:
        return not bool(r2.baseline.CHAPTER_LABEL.fullmatch(a['text'].strip()))
    aligned = min(abs(a['x0']-b['x0']), abs((a['x0']+a['x1']-b['x0']-b['x1'])/2)) < scale
    return (aligned and a.get('font') == b.get('font') and a['bold'] == b['bold']
            and abs(a['size']-b['size']) <= .1*scale)


def regroup(rows, nodes, joins):
    """Change only heading grouping; preserve nonheading nodes and every row."""
    if len(joins) != len(rows):
        raise ValueError('Need one continuation decision per retained row')
    split = []
    for node in nodes:
        if node['node_type'] != 'section_header':
            split.append(deepcopy(node))
            continue
        for i in node['source_rows']:
            row = rows[i]
            text = r2.normalize_row(row['text'])
            split.append(dict(node_type='section_header', text=text, page=row['page'], x0=row['x0'],
                              level=r2.baseline.heading_level(text), source_rows=[i],
                              bbox=[row['x0'], row['top'], row['x1'], row['bottom']]))
    result = []
    for node in split:
        previous = result[-1] if result else None
        i = node['source_rows'][0] if node['source_rows'] else None
        merge = (previous is not None and node['node_type'] == previous['node_type'] == 'section_header'
                 and node['page'] == previous['page'] and i == previous['source_rows'][-1]+1 and joins[i])
        if merge:
            previous['text'] += ' ' + node['text']
            previous['source_rows'] += node['source_rows']
            a, b = previous['bbox'], node['bbox']
            previous['bbox'] = [min(a[0], b[0]), max(a[1], b[1]), max(a[2], b[2]), min(a[3], b[3])]
        else:
            result.append(node)
    return result
