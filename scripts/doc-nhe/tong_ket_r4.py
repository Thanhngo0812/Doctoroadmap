"""Summarize all frozen R4 fits, keeping both weak-label evaluation masks."""
import argparse
from pathlib import Path
import statistics
import numpy as np
import hoc_r4 as r4

base = r4.base


def run(out):
    source = base.ROOT / 'tmp/doc-nhe-v414'
    pinned = base.manifest(source)
    data = {}
    for book in pinned['books']:
        key = book['id']
        d = base.read(source / 'datasets' / (key + '.json'))
        data[key] = {'book': book, 'r1': np.asarray(d['y']),
                     'r3': r4.binary_r3(base.read(base.ROOT / 'tmp/a1-v414-r3/labels' / (key + '.json'))['rows'])}
    stamp = base.read(out / 'protocol.json')['fingerprint']
    results = {}
    training = sorted(k for k, d in data.items() if d['book']['split'] == 'train')
    for variant in ('M2', *r4.CONFIGS):
        rows, seconds = [], []
        for name, heldout in r4.splits(training, data):
            path = (source if variant == 'M2' else out) / 'models' / f"{name}-{'lightgbm' if variant == 'M2' else variant}.json"
            record = base.read(path)
            assert record['fingerprint'] == (base.code_fingerprint() if variant == 'M2' else stamp)
            assert base.digest(path.with_suffix('.joblib')) == record['model_sha256']
            seconds.append(record['seconds'])
            for key, p in record['predictions'].items():
                assert key not in record['train_books'] and key in record['heldout']
                probs = np.asarray(p['probability'])
                rows.append({'book': key, 'split': name, 'field': data[key]['book']['field'],
                             'publisher': data[key]['book']['publisher'],
                             **{label: base.metrics(data[key][label], probs >= .5) for label in ('r1', 'r3')}})
        summaries = {}
        for split_type in ('lobo', 'publisher', 'external'):
            group = [r for r in rows if (r['split'] in training if split_type == 'lobo' else
                                        r['split'].startswith('publisher') if split_type == 'publisher' else r['split'] == 'full')]
            summaries[split_type] = {label: {'median_f1': statistics.median(r[label]['f1'] for r in group),
                                           'minimum_f1': min(r[label]['f1'] for r in group),
                                           'worst_book': min(group, key=lambda r: r[label]['f1'])['book'],
                                           'books': len(group)} for label in ('r1', 'r3')}
        results[variant] = {'rows': rows, 'summary': summaries, 'fit_seconds': sum(seconds), 'models': len(seconds)}
    # Pick two distinct development candidates: strongest minimum and strongest median.
    # This is model selection on development results, not a new unbiased test score.
    candidates = []
    for metric in ('minimum_f1', 'median_f1'):
        winner = max(r4.CONFIGS, key=lambda v: results[v]['summary']['lobo']['r1'][metric])
        if results[winner]['summary']['lobo']['r1'][metric] > results['M2']['summary']['lobo']['r1'][metric] and winner not in candidates:
            candidates.append(winner)
    value = {'api_usd': 0, 'scope': '19 previously inspected development books, silver labels only',
             'protocol_fingerprint': stamp, 'results': results, 'e2e_candidates': candidates}
    base.write(out / 'summary.json', value)
    print({v: r['summary'] for v, r in results.items()}, flush=True)
    print('Candidates:', candidates)


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--out', type=Path, required=True)
    run(cli.parse_args().out)
