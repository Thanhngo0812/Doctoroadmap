"""Build review samples and metric tables from the frozen v4-14 run."""
import argparse
import random
import statistics
from collections import Counter
from pathlib import Path
import hoc_tieu_de as m


def errors(out):
    samples, per_book = [], Counter()
    books = [b for b in m.manifest(out)['books'] if b['split'] == 'train']
    rng = random.Random(m.SEED)
    rng.shuffle(books)
    for label in (0, 1):
        pools = {}
        for book in books:
            key = book['id']
            d = m.read(out / 'datasets' / (key + '.json'))
            record = m.read(out / 'models' / (key + '-lightgbm.json'))
            probs = record['predictions'][key]['probability']
            tree = m.read(m.ROOT / book['tree'])
            candidates = []
            for i, (y, p) in enumerate(zip(d['y'], probs)):
                if y != label or (p >= .5) == bool(y):
                    continue
                row = d['rows'][i]
                candidates.append(dict(id=key, row_index=i, label=y, probability=p,
                    numbered=bool(m.light.HEADING_NUMBER.match(row['text'])), row=row,
                    before=d['rows'][i-1]['text'] if i else '',
                    after=d['rows'][i+1]['text'] if i+1 < len(d['rows']) else '',
                    reference=[tree['nodes'][n] for n in d['alignments'][i]['nodes']]))
            pools[key] = sorted(candidates, key=lambda s: -abs(s['label']-s['probability']))
        count = 0
        while count < 25:
            added = False
            for book in books:
                key = book['id']
                pool = pools[key]
                if not pool or per_book[key] >= 5 or count >= 25:
                    continue
                # Alternate numbered/un-numbered when available; then largest disagreement.
                index = next((i for i, s in enumerate(pool) if s['numbered'] == bool(count % 2)), 0)
                samples.append(pool.pop(index))
                per_book[key] += 1
                count += 1
                added = True
            if not added:
                break
    m.write(out / 'errors-50.json', samples)
    for i, s in enumerate(samples, 1):
        print(f"{i}. {s['id']} p{s['row']['page']} y{s['label']} p={s['probability']:.3f} | {s['row']['text']} | BEFORE {s['before'][:130]} | AFTER {s['after'][:100]}")


def summary(out):
    rows = m.read(out / 'e2e.json')
    training = [r for r in rows if r['split'] == 'train']
    for group, values in [('TRAIN', training), ('EXTERNAL', [r for r in rows if r['split'] != 'train'])]:
        print(group)
        print('| id | M0 F1 | M1 F1 | M2 P/R/F1 | M3 F1 | heading strict M0/M2 | leaf M0/M2/oracle | leaf strict M0/M2 | chunk .8 M0/M2 | s/page M0/M2 |')
        print('|' + '---|'*10)
        for r in values:
            a, b = r['models']['baseline'], r['models']['lightgbm']
            print(f"| {r['id']} | {a['line']['f1']:.3f} | {r['models']['logistic']['line']['f1']:.3f} | "
                  f"{b['line']['precision']:.3f}/{b['line']['recall']:.3f}/{b['line']['f1']:.3f} | {r['models']['no_context']['line']['f1']:.3f} | "
                  f"{a['heading_strict']['f1']:.3f}/{b['heading_strict']['f1']:.3f} | "
                  f"{a['chunk_legacy']['cung_muc_la']:.3f}/{b['chunk_legacy']['cung_muc_la']:.3f}/{r['models']['silver_oracle']['chunk_legacy']['cung_muc_la']:.3f} | "
                  f"{a['leaf_strict']['share']:.3f}/{b['leaf_strict']['share']:.3f} | "
                  f"{a['chunk_legacy']['docling_co_ban_tu_0_8']:.3f}/{b['chunk_legacy']['docling_co_ban_tu_0_8']:.3f} | "
                  f"{a['seconds_per_page']:.4f}/{b['seconds_per_page']:.4f} |")
    aggregate = {}
    for kind in ('baseline', *m.KINDS, 'silver_oracle'):
        values = [r['models'][kind] for r in training]
        aggregate[kind] = {'f1_median': statistics.median(v['line']['f1'] for v in values),
            'f1_min': min(v['line']['f1'] for v in values),
            'strict_heading_f1_median': statistics.median(v['heading_strict']['f1'] for v in values),
            'leaf_median': statistics.median(v['chunk_legacy']['cung_muc_la'] for v in values),
            'strict_leaf_median': statistics.median(v['leaf_strict']['share'] for v in values),
            'chunk_08_median': statistics.median(v['chunk_legacy']['docling_co_ban_tu_0_8'] for v in values)}
        if kind != 'silver_oracle':
            aggregate[kind].update(seconds_per_page_median=statistics.median(v['seconds_per_page'] for v in values),
                                   seconds_per_page_max=max(v['seconds_per_page'] for v in values))
    m.write(out / 'summary.json', aggregate)
    print(aggregate)


def audit(out):
    """Metadata, content conservation and feature diagnostics; no PDF/API access."""
    import numpy as np
    pinned = m.manifest(out)
    results, coverage = {}, {}
    for b in pinned['books']:
        key = b['id']
        d = m.read(out / 'datasets' / (key + '.json'))
        if d['fingerprint'] != m.code_fingerprint():
            raise ValueError('Stale dataset')
        base, _ = m.light.group_rows(d['rows'], d['figures'], d['pages'])
        def content(nodes):
            return [(n['page'], w) for n in nodes for w in m.light.words(n['text'])]
        def page_text(nodes):
            pages = {}
            for node in nodes:
                pages.setdefault(node['page'], []).append(''.join(c for c in node['text'] if not c.isspace()))
            return {p: ''.join(parts) for p, parts in pages.items()}
        original = content(base)
        original_text = page_text(base)
        values = {}
        for kind in m.KINDS:
            name = key if b['split'] == 'train' else 'full'
            rec = m.read(out / 'models' / f'{name}-{kind}.json')
            flags = np.asarray(rec['predictions'][key]['probability']) >= .5
            nodes, _ = m.light.group_rows(d['rows'], d['figures'], d['pages'], flags)
            candidate = content(nodes)
            candidate_text = page_text(nodes)
            values[kind] = {'same_page_token_sequence': original == candidate,
                'same_nonspace_page_text': original_text == candidate_text,
                'nonspace_text_changed_pages': [p for p in sorted(set(original_text) | set(candidate_text))
                                                if original_text.get(p) != candidate_text.get(p)],
                'lost_tokens': sum((Counter(original)-Counter(candidate)).values()),
                'added_tokens': sum((Counter(candidate)-Counter(original)).values()),
                'figures_equal': [n for n in base if n['node_type'] == 'figure'] == [n for n in nodes if n['node_type'] == 'figure'],
                'formula_tokens': sum(len(m.light.words(n['text'])) for n in nodes if n['node_type'] == 'formula'),
                'baseline_formula_tokens': sum(len(m.light.words(n['text'])) for n in base if n['node_type'] == 'formula')}
        results[key] = values
        coverage[key] = {k: d[k] for k in ('pages', 'raw_count', 'detail', 'raw_detail', 'seconds')}
        coverage[key].update(rows=len(d['rows']), positive=d['y'].count(1), negative=d['y'].count(0), unknown=d['y'].count(-1))
    records = [m.read(p) for p in sorted((out / 'models').glob('*.json'))]
    gain = np.mean([np.asarray(r['importance'])/max(sum(r['importance']), 1)
                    for r in records if r['kind'] == 'lightgbm' and r['name'].startswith('d01-')], axis=0)
    coefficients = np.mean([np.abs(r['importance']) for r in records
                           if r['kind'] == 'logistic' and r['name'].startswith('d01-')], axis=0)
    result = {'manifest': pinned, 'coverage': coverage, 'integrity': results,
              'mean_normalized_lobo_gain': dict(sorted(zip(m.FEATURE_NAMES, gain.tolist()), key=lambda x: -x[1])),
              'mean_absolute_lobo_logistic_coefficient': dict(sorted(zip(m.FEATURE_NAMES, coefficients.tolist()), key=lambda x: -x[1])),
              'training_seconds': sum(r['seconds'] for r in records),
              'models_bytes': sum(r['model_bytes'] for r in records),
              'full_models': {r['kind']: {'bytes': r['model_bytes'], 'seconds': r['seconds']} for r in records if r['name'] == 'full'},
              'publisher_scores': {r['name']: {k: v['metrics'] for k, v in r['predictions'].items()} for r in records if r['name'].startswith('publisher-')},
              'review_50_counts': dict(Counter(r['verdict'] for r in m.read(out/'errors-50-reviewed.json')['reviews']))}
    m.write(out / 'audit.json', result)
    print('Audit written:', out / 'audit.json')


if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('errors', 'summary', 'audit'))
    parser.add_argument('--out', type=Path, default=m.ROOT/'tmp/doc-nhe-v414')
    parser.add_argument('--snapshot', type=Path, help='Publish completed metrics/reviews to an explicit JSON file')
    args = parser.parse_args()
    {'errors': errors, 'summary': summary, 'audit': audit}[args.stage](args.out)
    if args.snapshot:
        m.manifest(args.out)  # recheck pinned inputs before publishing
        files = list((m.ROOT/'scripts/doc-nhe').glob('*.py')) + [m.ROOT/p for p in (
            'scripts/thu-a1/doc_nhe.py', 'scripts/thu-a1/so_chunk_doc_nhe.py',
            'src/doc2roadmap/domain/chunking.py', 'src/doc2roadmap/domain/models.py',
            'src/doc2roadmap/domain/sentence_splitter.py',
            'src/doc2roadmap/infrastructure/parsing/docling_parser.py',
            'src/doc2roadmap/infrastructure/text/tokenizer.py', 'vendor/gemma/tokenizer.model')]
        m.write(args.snapshot, {
            'sources_sha256': {p.relative_to(m.ROOT).as_posix(): m.digest(p) for p in files},
            **{name: m.read(args.out/(name+'.json')) for name in (
                'summary', 'e2e', 'audit', 'alignment-review-80', 'alignment-review-80-reviewed',
                'errors-50', 'errors-50-reviewed')},
        })
        print('Snapshot written:', args.snapshot)
