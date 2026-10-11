"""R4: bounded LightGBM morphology/style/label ablations on frozen development books."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import sys
import time

import hoc_tieu_de as base
import numpy as np

EXTRA = ('semicolon', 'colon', 'comma', 'equals', 'brackets', 'quotes', 'underscore',
         'camel', 'operators', 'bullet', 'starts_lower', 'ends_closing',
         'style_share', 'style_page_share', 'style_long_share', 'style_short_share',
         'style_median_chars', 'style_uppercase', 'size_rank', 'family_share')
FEATURES = base.FEATURE_NAMES + tuple(f'{side}_{n}' for side in ('self', 'prev', 'next') for n in EXTRA)
CONFIGS = {'E1': dict(n_estimators=300, num_leaves=15, min_child_samples=30, labels='r1'),
           'E2': dict(n_estimators=400, num_leaves=31, min_child_samples=60, labels='r1'),
           'E3': dict(n_estimators=300, num_leaves=15, min_child_samples=30, labels='r3')}


def morphology(text):
    n = max(len(text), 1)
    return [text.count(';')/n, text.count(':')/n, text.count(',')/n, text.count('=')/n,
            sum(c in '()[]{}' for c in text)/n, sum(c in '\"\'`' for c in text)/n,
            text.count('_')/n, len(re.findall(r'[a-z][A-Z]', text))/n,
            sum(c in '+-*/<>!|&^%' for c in text)/n,
            float(bool(re.match(r'^\s*[•●▪◦–−-]\s', text))),
            float(bool(text) and text[0].islower()), float(text.endswith((')', ']', '}', ';')))]


def feature_matrix(rows, body):
    styles, families = defaultdict(list), defaultdict(list)
    keys = [(r.get('font', ''), round(r['size'] * 2)/2, bool(r['bold']), bool(r.get('italic'))) for r in rows]
    for i, (r, key) in enumerate(zip(rows, keys)):
        styles[key].append(i)
        families[r.get('font', '')].append(i)
    pages = len({r['page'] for r in rows})
    sizes = np.asarray([r['size'] for r in rows])
    stats = {}
    for key, indexes in styles.items():
        group = [rows[i] for i in indexes]
        stats[key] = [len(group)/max(len(rows), 1), len({r['page'] for r in group})/max(pages, 1),
                      sum(len(r['text']) >= 80 for r in group)/len(group),
                      sum(len(r['text']) <= 30 for r in group)/len(group),
                      np.log1p(np.median([len(r['text']) for r in group])),
                      np.mean([sum(c.isupper() for c in r['text'])/max(sum(c.isalpha() for c in r['text']), 1) for r in group]),
                      float(np.mean(sizes <= key[1])), len(families[key[0]])/max(len(rows), 1)]
    own = np.asarray([morphology(r['text']) + stats[key] for r, key in zip(rows, keys)], dtype=np.float32).reshape((-1, len(EXTRA)))
    previous, following = np.zeros_like(own), np.zeros_like(own)
    for i, r in enumerate(rows):
        if i and rows[i-1]['page'] == r['page']:
            previous[i] = own[i-1]
        if i+1 < len(rows) and rows[i+1]['page'] == r['page']:
            following[i] = own[i+1]
    return np.concatenate((base.feature_matrix(rows, body), own, previous, following), axis=1)


def binary_r3(records):
    known = {'text', 'formula', 'caption', 'list_item', 'code', 'table', 'footnote'}
    return np.asarray([1 if r['label'] == 'heading' else 0 if r['label'] in known else -1 for r in records], dtype=np.int8)


def splits(training, data):
    result = [(key, (key,)) for key in training]
    publishers = sorted({data[k]['book']['publisher'] for k in training})
    result += [(f'publisher-{i:02}', tuple(k for k in training if data[k]['book']['publisher'] == p)) for i, p in enumerate(publishers)]
    return result + [('full', ())]


def fit(x, y, variant):
    from lightgbm import LGBMClassifier
    config = {k: v for k, v in CONFIGS[variant].items() if k != 'labels'}
    model = LGBMClassifier(**config, learning_rate=.05, class_weight='balanced',
                           random_state=42, n_jobs=2, verbosity=-1, deterministic=True, force_col_wise=True)
    return model.fit(x, y)


def run(out):
    import joblib
    from threadpoolctl import threadpool_limits
    out = out.resolve()
    source = base.ROOT / 'tmp/doc-nhe-v414'
    if not out.is_relative_to(base.ROOT / 'tmp') or out == source or source.is_relative_to(out):
        raise ValueError('Use a separate tmp/ output, never the frozen baseline')
    pinned = base.manifest(source)
    data = base.load_data(source, pinned)
    inputs = {}
    for key, d in data.items():
        path = base.ROOT / 'tmp/a1-v414-r3/labels' / (key + '.json')
        reference = base.read(path)
        if reference['dataset_sha256'] != base.digest(source / 'datasets' / (key + '.json')):
            raise ValueError('R3 label input differs from frozen rows')
        if [r['id'] for r in reference['rows']] != [f'{key}:{i}' for i in range(len(d['rows']))]:
            raise ValueError('R3 row ordering differs')
        d['X'] = feature_matrix(d['rows'], d['body'])
        d['r1'], d['r3'] = d['y'], binary_r3(reference['rows'])
        inputs[key] = {'dataset_sha256': reference['dataset_sha256'], 'r3_sha256': base.digest(path)}
    protocol = dict(script_sha256=base.digest(__file__), baseline_fingerprint=base.code_fingerprint(),
                    protocol_sha256=base.digest(base.ROOT / 'report/v4-14-r4-giao-thuc-2026-10-07.md'),
                    inputs=inputs, configs=CONFIGS, feature_names=FEATURES,
                    packages={k: base.importlib.metadata.version(k) for k in ('lightgbm', 'scikit-learn', 'numpy', 'joblib')})
    stamp = hashlib.sha256(json.dumps(protocol, sort_keys=True).encode()).hexdigest()
    if (out / 'protocol.json').exists() and base.read(out / 'protocol.json')['fingerprint'] != stamp:
        raise ValueError('R4 inputs/code/protocol changed: choose a fresh output directory')
    base.write(out / 'protocol.json', dict(protocol, fingerprint=stamp))
    training = sorted(k for k, d in data.items() if d['book']['split'] == 'train')
    for variant, config in CONFIGS.items():
        train = {k: {'X': data[k]['X'], 'y': data[k][config['labels']]} for k in training}
        for name, heldout in splits(training, data):
            record = out / 'models' / f'{name}-{variant}.json'
            model_path = record.with_suffix('.joblib')
            if record.exists():
                old = base.read(record)
                if old['fingerprint'] != stamp or not model_path.exists() or base.digest(model_path) != old['model_sha256']:
                    raise ValueError('Changed or incomplete model checkpoint')
                continue
            x, y, names = base.training_arrays(train, heldout)
            start = time.perf_counter()
            with threadpool_limits(limits=2):
                model = fit(x, y, variant)
            seconds = time.perf_counter()-start
            record.parent.mkdir(parents=True, exist_ok=True)
            joblib.dump(model, model_path)
            tests = heldout or tuple(k for k in data if k not in training)
            predictions = {}
            restored = joblib.load(model_path)
            for key in tests:
                probability = model.predict_proba(data[key]['X'])[:, 1]
                np.testing.assert_array_equal(probability, restored.predict_proba(data[key]['X'])[:, 1])
                predictions[key] = {'probability': probability.tolist(), **{
                    label: base.metrics(data[key][label], probability >= .5) for label in ('r1', 'r3')}}
            result = dict(name=name, variant=variant, fingerprint=stamp, train_books=names, heldout=list(tests),
                          seconds=seconds, model_sha256=base.digest(model_path), model_bytes=model_path.stat().st_size,
                          predictions=predictions, importance=model.booster_.feature_importance(importance_type='gain').tolist())
            base.write(record, result)
            print(json.dumps({'variant': variant, 'split': name, 'seconds': seconds,
                              'f1_r1': {k: p['r1']['f1'] for k, p in predictions.items()}}), flush=True)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--out', type=Path, required=True)
    run(cli.parse_args().out)
