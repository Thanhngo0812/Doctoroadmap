"""Bounded LOBO/publisher experiment on heading continuation; no production writes."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import sys
import time

import hoc_r4 as r4
import noi_tieu_de_r5 as pairs
import numpy as np
import joblib
from lightgbm import LGBMClassifier

base = r4.base


def run(out):
    source = base.ROOT / 'tmp/doc-nhe-v414'
    out = out.resolve()
    if not out.is_relative_to(base.ROOT / 'tmp') or out.exists():
        raise ValueError('Use a new output folder under tmp/')
    pinned = base.manifest(source)
    data, inputs = {}, {}
    for book in pinned['books']:
        key = book['id']
        path = source / 'datasets' / (key + '.json')
        label_path = base.ROOT / 'tmp/a1-v414-r3/labels' / (key + '.json')
        d, labels = base.read(path), base.read(label_path)
        assert labels['dataset_sha256'] == base.digest(path)
        assert [x['id'] for x in labels['rows']] == [f'{key}:{i}' for i in range(len(d['rows']))]
        data[key] = dict(book=book, rows=d['rows'], X=pairs.matrix(d['rows']), y=pairs.pair_labels(d['rows'], labels['rows']))
        inputs[key] = dict(dataset_sha256=base.digest(path), labels_sha256=base.digest(label_path))
    training = sorted(k for k, d in data.items() if d['book']['split'] == 'train')
    protocol = dict(script_sha256=base.digest(__file__), pair_code_sha256=base.digest(pairs.__file__),
                    base_fingerprint=base.code_fingerprint(), inputs=inputs,
                    protocol_sha256=base.digest(base.ROOT/'report/v4-14-r5-giao-thuc-2026-10-07.md'),
                    feature_names=pairs.FEATURES, threshold=.5, packages={
                        k: base.importlib.metadata.version(k) for k in ('lightgbm','numpy','joblib')})
    fingerprint = hashlib.sha256(json.dumps(protocol, sort_keys=True).encode()).hexdigest()
    base.write(out/'protocol.json', dict(protocol, fingerprint=fingerprint))
    counts = {k: {str(v):int(sum(d['y']==v)) for v in (-1,0,1)} for k,d in data.items()}
    results = []
    for name, heldout in r4.splits(training, data):
        x,y,names = base.training_arrays({k:data[k] for k in training}, heldout)
        assert set(y) == {0,1}
        start = time.perf_counter()
        model = LGBMClassifier(n_estimators=150,num_leaves=7,min_child_samples=10,learning_rate=.05,
                               class_weight='balanced',random_state=42,n_jobs=2,verbosity=-1,
                               deterministic=True,force_col_wise=True).fit(x,y)
        seconds = time.perf_counter()-start
        path = out/'models'/(name+'.joblib')
        path.parent.mkdir(parents=True,exist_ok=True)
        joblib.dump(model,path)
        tests = heldout or tuple(k for k in data if k not in training)
        predictions = {}
        for key in tests:
            d = data[key]
            probs = model.predict_proba(d['X'])[:,1]
            np.testing.assert_array_equal(probs,joblib.load(path).predict_proba(d['X'])[:,1])
            rules = {f'B{int(typo)}': [False]+[pairs.rule(a,b,typo) for a,b in zip(d['rows'],d['rows'][1:])]
                     for typo in (False,True)}
            predictions[key] = dict(probability=probs.tolist(), metrics={
                **{k:base.metrics(d['y'],v) for k,v in rules.items()},'B2':base.metrics(d['y'],probs>=.5)})
        record = dict(split=name,train_books=names,heldout=list(tests),fingerprint=fingerprint,
                      seconds=seconds,model_sha256=base.digest(path),model_bytes=path.stat().st_size,
                      predictions=predictions,importance=model.booster_.feature_importance(importance_type='gain').tolist())
        base.write(path.with_suffix('.json'),record)
        results.append(record)
        print(name,{k:p['metrics']['B2'] for k,p in predictions.items()},flush=True)
    summary = {}
    for split in ('lobo','publisher','external'):
        selected = [r for r in results if (r['split'] in training if split=='lobo' else r['split'].startswith('publisher') if split=='publisher' else r['split']=='full')]
        entries = [p for r in selected for p in r['predictions'].values()]
        summary[split] = {}
        for variant in ('B0','B1','B2'):
            metrics = [e['metrics'][variant] for e in entries]
            tp,fp,fn = [sum(m[k] for m in metrics) for k in ('tp','fp','fn')]
            summary[split][variant] = dict(tp=tp,fp=fp,fn=fn,micro_f1=2*tp/max(2*tp+fp+fn,1),
                                           median_book_f1=statistics.median(m['f1'] for m in metrics))
    base.write(out/'summary.json',dict(api_usd=0,fingerprint=fingerprint,counts=counts,summary=summary,
                                      fit_seconds=sum(r['seconds'] for r in results)))
    print(summary,flush=True)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--out',type=Path,required=True)
    run(cli.parse_args().out)
