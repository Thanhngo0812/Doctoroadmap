"""Read-only replay of frozen v1 predictions; write R2 evidence to a NEW folder."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import statistics
import time

import hoc_tieu_de as learn  # configures the isolated ML environment paths
import cau_truc_r2 as r2
from danh_gia import heading_score


def page_text(nodes):
    pages = defaultdict(str)
    for node in nodes:
        if node['node_type'] != 'figure':
            pages[node['page']] += ''.join(node['text'].split())
    return dict(pages)


def verify_nodes(rows, figures, nodes):
    """Check independently from node text + source inputs; fail before reporting."""
    indexes = [i for n in nodes for i in n['source_rows']]
    assert indexes == list(range(len(rows))), 'Missing, duplicated or reordered retained rows'
    expected = defaultdict(str)
    for row in rows:
        expected[row['page']] += ''.join(r2.normalize_row(row['text']).split())
    assert page_text(nodes) == dict(expected), 'Text changed during grouping'
    for node in nodes:
        indexes = node['source_rows']
        if not indexes:
            continue
        source = [rows[i] for i in indexes]
        assert all(r['page'] == node['page'] for r in source)
        assert node['text'] == ' '.join(r2.normalize_row(r['text']) for r in source)
        assert node['bbox'] == [min(r['x0'] for r in source), max(r['top'] for r in source),
                                max(r['x1'] for r in source), min(r['bottom'] for r in source)]
    found = [n for n in nodes if n['node_type'] == 'figure']
    assert len(found) == len(figures)
    for index, (actual, expected_figure) in enumerate(zip(found, figures)):
        assert actual['source_figure'] == index
        left, bottom, right, top = expected_figure['bbox']
        assert actual['bbox'] == [left, top, right, bottom]
        assert actual['page'] == expected_figure['page']


def validate_prediction(record, key, fingerprint, row_count):
    if (record['fingerprint'] != fingerprint or key in record['train_books']
            or key not in record['heldout'] or record['threshold'] != .5):
        raise ValueError('Invalid frozen prediction provenance')
    values = record['predictions'][key]['probability']
    if len(values) != row_count:
        raise ValueError('Frozen prediction row count changed')
    return [p >= .5 for p in values]


def run(source, out):
    source, out = source.resolve(), out.resolve()
    if out == source or out.is_relative_to(source):
        raise ValueError('R2 must not overwrite frozen v1 directory')
    pinned = learn.manifest(source)  # validates PDF/tree/chunk-manifest hashes + test allowlist
    result = {'version': r2.VERSION, 'started_utc': datetime.now(timezone.utc).isoformat(),
              'api_usd': 0, 'baseline_manifest_sha256': learn.digest(source/'manifest.json'),
              'code_sha256': {name: learn.digest(learn.ROOT/name) for name in (
                  'scripts/doc-nhe/cau_truc_r2.py', 'scripts/doc-nhe/do_r2.py',
                  'scripts/doc-nhe/hoc_tieu_de.py', 'scripts/doc-nhe/danh_gia.py',
                  'scripts/thu-a1/doc_nhe.py', 'src/doc2roadmap/infrastructure/parsing/docling_parser.py')},
              'scope': '19 previously inspected development books; no blind test, no retraining', 'books': []}
    began = time.perf_counter()
    for book in pinned['books']:
        started = time.perf_counter()
        key = book['id']
        path = source/'datasets'/f'{key}.json'
        data = learn.read(path)
        if data['fingerprint'] != learn.code_fingerprint():
            raise ValueError('Frozen dataset fingerprint mismatch')
        rows, body = r2.baseline.prepare_rows(data['rows'])
        if rows != data['rows']:
            raise ValueError('Second filtering changed retained rows')
        reference = learn.read(learn.ROOT/book['tree'])['nodes']
        entry = {'id': key, 'split': book['split'], 'field': book['field'], 'rows': len(rows),
                 'pages': data['pages'], 'raw_rows_removed_in_v1': data['raw_count']-len(rows),
                 'dataset_sha256': learn.digest(path), 'models': {}}
        baseline_nodes, _ = r2.baseline.group_rows(rows, data['figures'], data['pages'])
        baseline_pages = page_text(baseline_nodes)
        for kind in ('baseline', *learn.KINDS):
            flags = None
            record_hash = None
            if kind != 'baseline':
                name = key if book['split'] == 'train' else 'full'
                record_path = source/'models'/f'{name}-{kind}.json'
                record = learn.read(record_path)
                flags = validate_prediction(record, key, data['fingerprint'], len(rows))
                if learn.digest(record_path.with_suffix('.joblib')) != record['model_sha256']:
                    raise ValueError('Frozen model hash changed')
                record_hash = learn.digest(record_path)
            old, _ = r2.baseline.group_rows(rows, data['figures'], data['pages'], flags)
            old_pages = page_text(old)
            changed = sorted(p for p in old_pages.keys() | baseline_pages.keys() if old_pages.get(p) != baseline_pages.get(p))
            modes = {}
            for protect in (False, True):
                stage_start = time.perf_counter()
                nodes, stats = r2.group_rows(rows, data['figures'], data['pages'], flags, protect_types=protect)
                elapsed = time.perf_counter()-stage_start
                verify_nodes(rows, data['figures'], nodes)
                texts = page_text(nodes)
                differences = sorted(p for p in old_pages.keys() | texts.keys() if old_pages.get(p) != texts.get(p))
                blocked = stats['blocked_heading_rows']
                modes['protected' if protect else 'text'] = {
                    'grouping_seconds_only': elapsed,
                    'types': dict(Counter(n['node_type'] for n in nodes)),
                    'changed_pages_vs_v1_same_flags': differences,
                    'nonspace_character_delta_vs_v1': sum(map(len, texts.values()))-sum(map(len, old_pages.values())),
                    'blocked': len(blocked), 'blocked_silver': dict(Counter(str(data['y'][i]) for i in blocked)),
                    'source_partition_text_bbox_figures_verified': True,
                }
                # Strict node metric on the leading model only; no change of labels or threshold.
                if kind == 'lightgbm':
                    modes['protected' if protect else 'text']['strict_heading'] = heading_score(reference, nodes)
            entry['models'][kind] = {'prediction_sha256': record_hash, 'old_changed_pages_vs_baseline': changed,
                                     'old_types': dict(Counter(n['node_type'] for n in old)), 'r2': modes}
            if kind == 'lightgbm':
                entry['models'][kind]['old_strict_heading'] = heading_score(reference, old)
        entry['seconds'] = time.perf_counter()-started
        result['books'].append(entry)
        learn.write(out/'books'/f'{key}.json', entry)
        print(f"{key}: {len(result['books'])}/19 verified; {entry['seconds']:.1f}s", flush=True)
    result['seconds'] = time.perf_counter()-began
    train = [b for b in result['books'] if b['split'] == 'train']
    result['train_strict_heading_f1_median'] = {
        'v1_m2': statistics.median(b['models']['lightgbm']['old_strict_heading']['f1'] for b in train),
        **{k: statistics.median(b['models']['lightgbm']['r2'][k]['strict_heading']['f1'] for b in train)
           for k in ('text', 'protected')}}
    learn.write(out/'replay.json', result)
    print(result['train_strict_heading_f1_median'], flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--source', type=Path, default=Path('tmp/doc-nhe-v414'))
    parser.add_argument('--out', type=Path, default=Path('tmp/a1-v414-r2'))
    args = parser.parse_args()
    run(args.source, args.out)
