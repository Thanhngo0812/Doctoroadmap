"""Fixed loss-weight ablation on R8c; keep original and reviewed labels unchanged."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import joblib
import numpy as np
from lightgbm import LGBMClassifier
import hoc_loc_le_r8c as r8
import hoc_r4 as r4
import can_sach_r11 as balance

base=r8.base
CONFIGS={'WB73':dict(features=73,n_estimators=300,num_leaves=15,min_child_samples=30,book_weight=True),
         'ERM133':dict(features=133,n_estimators=400,num_leaves=31,min_child_samples=60,book_weight=False),
         'WB133':dict(features=133,n_estimators=400,num_leaves=31,min_child_samples=60,book_weight=True)}


def run(out):
    source=base.ROOT/'tmp/a1-v414-r8c-model'
    data,parent=r8.load(source)
    inputs={k:base.digest(source/'datasets'/(k+'.json')) for k in data}
    protocol=dict(parent=parent['fingerprint'],script_sha256=base.digest(__file__),weight_sha256=base.digest(balance.__file__),
                  features_sha256=base.digest(r4.__file__),protocol_sha256=base.digest(base.ROOT/'report/v4-14-r11-giao-thuc-2026-10-07.md'),
                  inputs=inputs,configs=CONFIGS,
                  packages={k:base.importlib.metadata.version(k) for k in ('lightgbm','scikit-learn','numpy','joblib')})
    protocol['fingerprint']=hashlib.sha256(json.dumps(protocol,sort_keys=True).encode()).hexdigest()
    path=out/'protocol.json'
    if path.exists():
        assert base.read(path)==protocol, 'Changed experiment: choose a fresh directory'
    else:
        base.write(path,protocol)
    training=sorted(k for k,d in data.items() if d['book']['split']=='train')
    for d in data.values():
        d['wide_X']=r4.feature_matrix(d['rows'],d['body'])
    results=[]
    for variant,config in CONFIGS.items():
        view={k:dict(d,X=d['wide_X'][:,:config['features']]) for k,d in data.items()}
        for name,heldout in r4.splits(training,data):
            path=out/'models'/(name+'-'+variant+'.json')
            if path.exists():
                record=base.read(path)
                assert record['fingerprint']==protocol['fingerprint'] and base.digest(path.with_suffix('.joblib'))==record['model_sha256']
                results.append(record)
                continue
            x,y,w,names=balance.training_arrays({k:view[k] for k in training},heldout)
            options={k:v for k,v in config.items() if k not in ('features','book_weight')}
            model=LGBMClassifier(**options,learning_rate=.05,random_state=42,n_jobs=2,verbosity=-1,
                                 deterministic=True,force_col_wise=True,
                                 class_weight=None if config['book_weight'] else 'balanced')
            start=time.perf_counter()
            model.fit(x,y,sample_weight=w if config['book_weight'] else None)
            seconds=time.perf_counter()-start
            path.parent.mkdir(parents=True,exist_ok=True)
            joblib.dump(model,path.with_suffix('.joblib'))
            restored=joblib.load(path.with_suffix('.joblib'))
            predictions={}
            for key in heldout or tuple(k for k in data if k not in training):
                assert key not in names
                d=view[key]
                p=model.predict_proba(d['X'])[:,1]
                np.testing.assert_array_equal(p,restored.predict_proba(d['X'])[:,1])
                raw=np.zeros(len(d['raw_y']),dtype=bool)
                raw[d['raw_indexes']]=p>=.5
                predictions[key]=dict(probability=p.tolist(),full_raw={label:base.metrics(np.asarray(d[field]),raw)
                                      for label,field in [('r1','raw_y'),('r3','raw_r3')]})
            weights={}
            offset=0
            for k in names:
                count=int(sum(view[k]['y']>=0))
                weights[k]=float(w[offset:offset+count].sum()) if config['book_weight'] else None
                offset+=count
            record=dict(variant=variant,name=name,fingerprint=protocol['fingerprint'],train_books=names,
                        heldout=list(predictions),seconds=seconds,model_sha256=base.digest(path.with_suffix('.joblib')),
                        weight_mass_per_book=weights,weight_mean=float(w.mean()) if config['book_weight'] else None,
                        predictions=predictions)
            base.write(path,record)
            results.append(record)
            print(variant,name,{k:round(p['full_raw']['r1']['f1'],4) for k,p in predictions.items()},flush=True)
    base.write(out/'training.json',dict(api_usd=0,models=len(results),fit_seconds=sum(r['seconds'] for r in results)))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--out',type=Path,required=True)
    run(cli.parse_args().out)
