"""One-book weak-label hierarchy experiment; doc-4 is evaluation only."""
import argparse
from pathlib import Path
import sys
import time
import joblib
import numpy as np
from lightgbm import LGBMClassifier
import hoc_tieu_de as base
import cay_tieu_de_r14 as tree

CONFIG=dict(n_estimators=100,num_leaves=7,min_child_samples=10,learning_rate=.05,
            random_state=42,n_jobs=2,verbosity=-1,class_weight='balanced',deterministic=True,force_col_wise=True)


def fit(entries):
    x,y,ids=tree.training_pairs(entries)
    return LGBMClassifier(**CONFIG).fit(x,y),ids


def evaluate(model,entries):
    rows=[e['row'] for e in entries]
    def score(rows,i,parents,chosen):
        return model.predict_proba(np.asarray([tree.pair_features(rows,i,p,chosen) for p in parents],dtype=np.float32))[:,1]
    predicted=tree.decode(rows,score)
    target=[e['parent'] for e in entries]
    return dict(H0=tree.metrics(target,tree.baseline(rows)),H2=tree.metrics(target,predicted),
                target=target,predicted=predicted,bookmark_ids=[e['bookmark'] for e in entries])


def run(out):
    assert not out.exists()
    pinned={b['id']:b for b in base.manifest(base.ROOT/'tmp/doc-nhe-v414')['books']}
    outlines=base.read(base.ROOT/'tmp/a1-v414-r5/bookmarks.json')
    inputs={}
    data={}
    for key in ('d01-08','doc-4'):
        source=next(b for b in outlines['books'] if b['book']==key)
        assert source['source_sha256']==pinned[key]['pdf_sha256']
        path=base.ROOT/'tmp/doc-nhe-v414/datasets'/(key+'.json')
        d=base.read(path)
        assert d['fingerprint']==base.code_fingerprint()
        entries=tree.project_outline(source['bookmarks'],d['rows'])
        data[key]=entries
        inputs[key]=dict(dataset_sha256=base.digest(path),bookmarks=len(source['bookmarks']),
                         matched=len(entries),groups=len({e['group'] for e in entries}),
                         entries=entries)
    result=dict(api_usd=0,config=CONFIG,status='weak_outline_one_training_book_not_production',
                inputs=inputs,folds=[],code_sha256={str(Path(p).resolve().relative_to(base.ROOT)):base.digest(p) for p in (
                    __file__,tree.__file__,base.ROOT/'report/v4-14-r14-giao-thuc-phan-tang-2026-10-07.md')},
                outline_sha256=base.digest(base.ROOT/'tmp/a1-v414-r5/bookmarks.json'))
    groups={e['group'] for e in data['d01-08']}
    for held in sorted(groups):
        train=tree.subset(data['d01-08'],groups-{held})
        test=tree.subset(data['d01-08'],{held})
        start=time.perf_counter()
        model,ids=fit(train)
        assert set(ids).isdisjoint(e['bookmark'] for e in test)
        values=evaluate(model,test)
        record=dict(group=held,train_book='d01-08',heldout_book='d01-08',
                    train_ids=sorted(set(ids)),seconds=time.perf_counter()-start,**values)
        result['folds'].append(record)
        print('group',held,'n',len(test),'H0/H2',round(values['H0']['parent_accuracy'],4),round(values['H2']['parent_accuracy'],4),flush=True)
    model,ids=fit(data['d01-08'])
    out.mkdir(parents=True)
    path=out/'parent-model.joblib'
    joblib.dump(model,path)
    result['external']=dict(train_book='d01-08',heldout_book='doc-4',train_ids=sorted(set(ids)),**evaluate(model,data['doc-4']))
    assert evaluate(joblib.load(path),data['doc-4'])==evaluate(model,data['doc-4'])
    result['model_sha256']=base.digest(path)
    base.write(out/'results.json',result)
    print('external',result['external']['H0'],result['external']['H2'],flush=True)


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--out',type=Path,required=True)
    run(cli.parse_args().out)
