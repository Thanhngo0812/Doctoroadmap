"""R8c datasets derived from R8b raw-index labels, with fixed M2 training."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import joblib
import numpy as np
import hoc_tieu_de as base
import hoc_r4 as r4
import hoc_loc_le_r8 as previous
import loc_le_r8c as margin


def prepare(out):
    assert not out.exists(), 'Use a new output directory'
    source=base.ROOT/'tmp/a1-v414-r8-model'
    data,parent=previous.load(source)
    protocol=dict(parent_fingerprint=parent['fingerprint'],script_sha256=base.digest(__file__),
                  filter_sha256=base.digest(margin.__file__),parent_filter_sha256=base.digest(margin.previous.__file__),
                  base_fingerprint=base.code_fingerprint(),
                  protocol_sha256=base.digest(base.ROOT/'report/v4-14-r8c-giao-thuc-2026-10-07.md'))
    protocol['fingerprint']=hashlib.sha256(json.dumps(protocol,sort_keys=True).encode()).hexdigest()
    base.write(out/'protocol.json',protocol)
    for key,d in data.items():
        d=base.read(source/'datasets'/(key+'.json'))
        rows,body=margin.prepare_rows(d['rows'])
        assert margin.prepare_rows(rows)[0]==rows
        lookup={id(r):i for r,i in zip(d['rows'],d['raw_indexes'],strict=True)}
        indexes=[lookup[id(r)] for r in rows]
        by_index={i:r for r,i in zip(d['rows'],d['raw_indexes'],strict=True)}
        removed=[dict(raw_index=i,row=by_index[i],r1=d['raw_y'][i],r3=d['raw_r3'][i])
                 for i in sorted(set(d['raw_indexes'])-set(indexes))]
        d.update(rows=rows,body=body,raw_indexes=indexes,y=[d['raw_y'][i] for i in indexes],
                 fingerprint=protocol['fingerprint'],removed_from_b=removed,
                 recovered=[r for r in d['recovered'] if r['raw_index'] in set(indexes)],
                 newly_dropped=[r for r in removed if r['raw_index'] in set(d['old_indexes'])])
        base.write(out/'datasets'/(key+'.json'),d)
        print(key,'removed from b',len(removed),'recoveries retained',len(d['recovered']),flush=True)


def load(out):
    protocol=base.read(out/'protocol.json')
    assert protocol['script_sha256']==base.digest(__file__)
    assert protocol['filter_sha256']==base.digest(margin.__file__)
    assert protocol['parent_filter_sha256']==base.digest(margin.previous.__file__)
    assert protocol['base_fingerprint']==base.code_fingerprint()
    data={}
    for book in base.manifest(base.ROOT/'tmp/doc-nhe-v414')['books']:
        d=base.read(out/'datasets'/(book['id']+'.json'))
        assert d['fingerprint']==protocol['fingerprint']
        d['X'],d['y']=base.feature_matrix(d['rows'],d['body']),np.asarray(d['y'])
        data[book['id']]=d
    return data,protocol


def train(out):
    data,protocol=load(out)
    training=sorted(k for k,d in data.items() if d['book']['split']=='train')
    results=[]
    for name,heldout in r4.splits(training,data):
        path=out/'models'/(name+'.json')
        if path.exists():
            record=base.read(path)
            assert record['fingerprint']==protocol['fingerprint'] and base.digest(path.with_suffix('.joblib'))==record['model_sha256']
            results.append(record)
            continue
        x,y,names=base.training_arrays({k:data[k] for k in training},heldout)
        start=time.perf_counter()
        model=base.fit_model(x,y,'lightgbm')
        seconds=time.perf_counter()-start
        path.parent.mkdir(parents=True,exist_ok=True)
        joblib.dump(model,path.with_suffix('.joblib'))
        predictions={}
        for key in heldout or tuple(k for k in data if k not in training):
            d=data[key]
            probs=base.probability(model,d['X'],'lightgbm')
            np.testing.assert_array_equal(probs,base.probability(joblib.load(path.with_suffix('.joblib')),d['X'],'lightgbm'))
            raw_pred=np.zeros(len(d['raw_y']),dtype=bool)
            raw_pred[d['raw_indexes']]=probs>=.5
            old_name=name if name.startswith('publisher') else key if d['book']['split']=='train' else 'full'
            old_record=base.read(base.ROOT/'tmp/doc-nhe-v414/models'/(old_name+'-lightgbm.json'))
            assert set(names)==set(old_record['train_books'])
            old_pred=np.zeros(len(d['raw_y']),dtype=bool)
            old_pred[d['old_indexes']]=np.asarray(old_record['predictions'][key]['probability'])>=.5
            predictions[key]=dict(probability=probs.tolist(),retained=base.metrics(d['y'],probs>=.5),
                                  full_raw={label:{'old':base.metrics(np.asarray(d[field]),old_pred),
                                                   'new':base.metrics(np.asarray(d[field]),raw_pred)}
                                            for label,field in [('r1','raw_y'),('r3','raw_r3')]})
        record=dict(name=name,fingerprint=protocol['fingerprint'],train_books=names,heldout=list(predictions),
                    seconds=seconds,model_sha256=base.digest(path.with_suffix('.joblib')),predictions=predictions)
        base.write(path,record)
        results.append(record)
        print(name,{k:round(p['full_raw']['r1']['new']['f1'],4) for k,p in predictions.items()},flush=True)
    base.write(out/'training.json',dict(api_usd=0,models=len(results),fit_seconds=sum(r['seconds'] for r in results)))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('stage',choices=('prepare','train'))
    cli.add_argument('--out',type=Path,required=True)
    args=cli.parse_args()
    {'prepare':prepare,'train':train}[args.stage](args.out)
