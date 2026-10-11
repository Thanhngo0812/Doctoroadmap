"""R3: geometry + lossless token alignment, never predictions, for silver block roles."""
import argparse
from collections import Counter, defaultdict
import hashlib
import html
import json
import math
from pathlib import Path
import time
import unicodedata
import re

import hoc_tieu_de as learn
from cau_truc_r2 import normalize_row

ROOT = learn.ROOT
VERSION = 'a1-r3-block-labels-v1'
CLASSES = ('heading', 'text', 'formula', 'caption', 'list_item', 'code', 'table', 'footnote')
ROLE = {**{k: k for k in CLASSES}, 'title': 'heading', 'section_header': 'heading', 'paragraph': 'text'}


def tokens(text):
    return re.findall(r'\w+|[^\w\s]', unicodedata.normalize('NFC', normalize_row(text)))


def coverage(row, box):
    if box is None:
        return 0.0
    left, top, right, bottom = box
    values = [*box, row['x0'], row['top'], row['x1'], row['bottom']]
    if (not all(math.isfinite(v) for v in values) or right < left or top < bottom
            or row['x1'] < row['x0'] or row['top'] < row['bottom']):
        raise ValueError('Invalid PDF bbox')
    area = (row['x1'] - row['x0']) * (row['top'] - row['bottom'])
    overlap = max(0, min(right, row['x1']) - max(left, row['x0'])) * max(0, min(top, row['top']) - max(bottom, row['bottom']))
    return overlap / area if area else 0.0


def node_text(node):
    if node['node_type'] == 'formula':
        return node.get('raw_text') or node.get('text', '')
    if node['node_type'] == 'table':
        return ' '.join(' '.join(cells) for cells in node.get('table_rows') or []) or node.get('text', '')
    return node.get('text', '')


def align_rows(rows, nodes):
    pages = defaultdict(list)
    for index, node in enumerate(nodes):
        pages[node.get('page')].append((index, node, tokens(node_text(node))))
    result = []
    for row in rows:
        key = tokens(row['text'])
        matches, partial = [], []
        for index, node, value in pages[row['page']]:
            ratio = coverage(row, node.get('bbox'))
            if ratio < .5 or not key or not value:
                continue
            exact = key == value
            enough = sum(any(c.isalnum() for c in t) for t in key) >= 2 or sum(c.isalpha() for t in key for c in t) >= 8
            hit = {'node': index, 'label': ROLE.get(node['node_type'], 'unsupported'),
                   'coverage': round(ratio, 6)}
            if exact or (enough and learn.contains(key, value)):
                matches.append({**hit, 'match': 'exact' if exact else 'contained'})
            elif learn.contains(value, key):
                partial.append(hit)  # a heading embedded in a prose row is not a whole-row label
        classes = {m['label'] for m in matches + partial}
        supported = {m['label'] for m in matches}
        valid = len(classes) == 1 and bool(matches) and 'unsupported' not in classes
        label = next(iter(supported)) if valid else 'unknown'
        status = ('exact' if any(m['match'] == 'exact' for m in matches) else 'contained') if valid else (
            'ambiguous' if len(classes) > 1 else 'partial' if partial else 'unsupported' if matches else 'unmatched')
        result.append({'label': label, 'status': status, 'matches': matches, 'partial_nodes': partial})
    return result


def review_role(book, page):
    number = int(hashlib.sha256(f'42:{book}:{page}'.encode()).hexdigest(), 16)
    return 'audit' if number % 5 == 0 else 'development'


def sample_review(entries):
    groups = defaultdict(list)
    for entry in entries:
        groups[entry['book'], entry['label']].append(entry)
    chosen = []
    for (book, label), values in sorted(groups.items()):
        ordered = sorted(values, key=lambda e: hashlib.sha256(f"42:{book}:{e['page']}:{e['row']}".encode()).hexdigest())
        chosen.extend(ordered[:4 if label == 'unknown' else 2])
    return chosen


def validate_output(out, source):
    out, source = Path(out).resolve(), Path(source).resolve()
    base = (ROOT / 'tmp').resolve()
    if out == base or not out.is_relative_to(base) or out == source or out.is_relative_to(source) or source.is_relative_to(out):
        raise ValueError('R3 output must be a separate experiment below tmp, not baseline/production')


def run(source, out):
    source, out = source.resolve(), out.resolve()
    validate_output(out, source)
    if not (source / 'manifest.json').is_file():
        raise ValueError('Existing frozen manifest required; do not prepare new inputs implicitly')
    if out.exists() and any(out.iterdir()):
        raise ValueError('Use a new empty R3 directory; preserve previous experiments')
    pinned = learn.manifest(source)
    started = time.perf_counter()
    summary = {'version': VERSION, 'api_usd': 0, 'baseline_manifest_sha256': learn.digest(source / 'manifest.json'),
               'source_sha256': {str(p): learn.digest(ROOT / p) for p in (
                   'scripts/doc-nhe/nhan_khoi_r3.py', 'scripts/doc-nhe/cau_truc_r2.py',
                   'scripts/doc-nhe/hoc_tieu_de.py', 'scripts/thu-a1/doc_nhe.py',
                   'src/doc2roadmap/infrastructure/parsing/docling_parser.py')}, 'books': []}
    packet, key = [], []
    for book in pinned['books']:
        path = source / 'datasets' / (book['id'] + '.json')
        data = learn.read(path)
        if data['fingerprint'] != learn.code_fingerprint() or data['book'] != book:
            raise ValueError('Frozen dataset provenance changed')
        rows = data['rows']
        if len(rows) != len(data['y']):
            raise ValueError('Frozen row/label lengths differ')
        nodes = learn.read(ROOT / book['tree'])['nodes']
        labels = align_rows(rows, nodes)
        entries = [dict(id=f"{book['id']}:{i}", book=book['id'], row=i, page=r['page'],
                        role=review_role(book['id'], r['page']), **label)
                   for i, (r, label) in enumerate(zip(rows, labels, strict=True))]
        sampled = sample_review(entries)
        for entry in sampled:
            i = entry['row']
            packet.append({k: entry[k] for k in ('id', 'book', 'row', 'page', 'role')} | {
                'pdf': book['pdf'], 'text': rows[i]['text'],
                'bbox': [rows[i]['x0'], rows[i]['top'], rows[i]['x1'], rows[i]['bottom']],
                'context': [{'row': j, 'text': rows[j]['text']} for j in range(max(0, i-1), min(len(rows), i+2)) if rows[j]['page'] == entry['page']],
                'review_label': None, 'reviewer': None, 'evidence': None})
            key.append(entry)
        counts = Counter(e['label'] for e in entries)
        transitions = Counter(f"{old}->{int(e['label'] == 'heading') if e['label'] != 'unknown' else -1}"
                              for old, e in zip(data['y'], entries, strict=True))
        summary['books'].append({'id': book['id'], 'split': book['split'], 'field': book['field'],
                                 'publisher': book['publisher'], 'rows': len(rows),
                                 'v1_filtered_rows_not_audited': data['raw_count'] - len(rows),
                                 'dataset_sha256': learn.digest(path), 'labels': dict(counts),
                                 'status': dict(Counter(e['status'] for e in entries)),
                                 'heading_label_transitions_from_v1': dict(transitions),
                                 'sampled': dict(Counter(e['label'] for e in sampled)),
                                 'absent_classes': [k for k in CLASSES if not counts[k]],
                                 'linked_captions_without_separate_bbox': sum(bool(n.get('context_prefix')) for n in nodes)})
        learn.write(out / 'labels' / (book['id'] + '.json'), {'dataset_sha256': learn.digest(path), 'version': VERSION, 'rows': entries})
        print(f"{book['id']}: {len(rows)} rows, {counts['unknown']} unknown, {len(sampled)} review", flush=True)
    packet.sort(key=lambda e: hashlib.sha256(('review:' + e['id']).encode()).hexdigest())
    summary['seconds'] = time.perf_counter() - started
    summary['review_count'] = len(packet)
    summary['review_roles'] = dict(Counter(e['role'] for e in packet))
    learn.write(out / 'summary.json', summary)
    learn.write(out / 'review-packet.json', packet)
    learn.write(out / 'review-key.json', key)
    panels = []
    for e in packet:
        context = '\n'.join(f"{c['row']}: {c['text']}" for c in e['context'])
        panels.append(f"<article><h2>{html.escape(e['id'])} · trang {e['page']} · {e['role']}</h2>"
                      f"<p>{html.escape(e['pdf'])}</p><blockquote>{html.escape(e['text'])}</blockquote><pre>{html.escape(context)}</pre></article>")
    (out / 'review.html').write_text('<!doctype html><meta charset="utf-8"><title>A1 R3 review</title>'
                                   '<style>body{max-width:1000px;margin:auto;font:18px sans-serif}article{border-bottom:1px solid #aaa;padding:20px}pre{white-space:pre-wrap}</style>'
                                   '<h1>A1 R3 — mẫu review, không hiển thị nhãn bạc</h1><p>Chưa gán nhãn; cần đối chiếu PDF. Không phải tập test mù.</p>' + ''.join(panels), encoding='utf-8')
    print(json.dumps({'review': len(packet), 'seconds': summary['seconds']}), flush=True)


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--source', type=Path, default=Path('tmp/doc-nhe-v414'))
    cli.add_argument('--out', type=Path, default=Path('tmp/a1-v414-r3'))
    args = cli.parse_args()
    run(args.source, args.out)
