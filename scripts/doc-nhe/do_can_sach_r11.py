"""End-to-end evaluation of all fixed R11 variants, not a per-book winner."""
import argparse
from pathlib import Path
import sys
import numpy as np
import doi_chung_r9 as r9
import hoc_can_sach_r11 as training

base=r9.base


def run(source,out):
    assert not out.exists(), 'Use a new output directory'
    protocol=base.read(source/'protocol.json')
    assert base.read(source/'training.json')['models']==81
    assert protocol['script_sha256']==base.digest(training.__file__)
    assert protocol['weight_sha256']==base.digest(training.balance.__file__)
    assert protocol['features_sha256']==base.digest(r9.r4.__file__)
    data,parent=r9.r8.load(base.ROOT/'tmp/a1-v414-r8c-model')
    assert protocol['parent']==parent['fingerprint']
    assert base.read(base.ROOT/'tmp/a1-v414-r5/protocol.json')['pair_code_sha256']==base.digest(r9.pairs.__file__)
    counter=r9.SentencePieceTokenCounter(base.ROOT/'vendor/gemma/tokenizer.model','google-gemma-sentencepiece-v1')
    books=[]
    for key,d in data.items():
        assert protocol['inputs'][key]==base.digest(base.ROOT/'tmp/a1-v414-r8c-model/datasets'/(key+'.json'))
        book=d['book']
        name=key if book['split']=='train' else 'full'
        old=base.read(base.ROOT/'tmp/a1-v414-r8c-model/models'/(name+'.json'))
        pair_model,pair_record=r9.frozen(base.ROOT/'tmp/a1-v414-r5',name,key,old['train_books'])
        joins=pair_model.predict_proba(r9.pairs.matrix(d['rows']))[:,1]>=.5
        tree=base.read(base.ROOT/book['tree'])
        settings={k:v for k,v in book['chunk_config'].items() if k in (
            'max_tokens','max_table_tokens','hard_cap_tokens','target_tokens','sentence_overlap',
            'result_min_count','result_max_body_chars','heading_scheme')}
        reference=r9.chunks.chunks_of(r9.DocumentTree.from_dict(tree),key,counter,settings)
        result=dict(id=key,split=book['split'],models={},model_sha256={'B2':pair_record['model_sha256']})
        wide=r9.r4.feature_matrix(d['rows'],d['body'])
        for variant,config in training.CONFIGS.items():
            model,record=r9.frozen(source,name+'-'+variant,key,old['train_books'])
            assert record['fingerprint']==protocol['fingerprint']
            p=np.asarray(record['predictions'][key]['probability'])
            np.testing.assert_array_equal(p,model.predict_proba(wide[:,:config['features']])[:,1])
            result['model_sha256'][variant]=record['model_sha256']
            raw=np.zeros(len(d['raw_y']),dtype=bool)
            raw[d['raw_indexes']]=p>=.5
            row_score={label:base.metrics(np.asarray(d[field]),raw) for label,field in [('r1','raw_y'),('r3','raw_r3')]}
            assert row_score==record['predictions'][key]['full_raw']
            original,_=r9.structure.group_rows(d['rows'],d['figures'],d['pages'],p>=.5,prepare_rows=r9.r8.margin.prepare_rows)
            for relation in ('B0','B2'):
                nodes=original if relation=='B0' else r9.pairs.regroup(d['rows'],original,joins)
                r9.verify_nodes(d['rows'],d['figures'],nodes)
                actual=r9.chunks.chunks_of(r9.chunks.light_tree(nodes),key,counter,settings)
                result['models'][variant+'_'+relation]=dict(full_raw=row_score,
                    heading_strict=r9.heading_score(tree['nodes'],nodes),leaf_strict=r9.leaf_score(reference,actual),
                    chunk_legacy=r9.chunks.compare(reference,actual))
        base.write(out/'books'/(key+'.json'),result)
        books.append(result)
        print(key,{v:round(r['leaf_strict']['share'],4) for v,r in result['models'].items()},flush=True)
    code=[Path(__file__),Path(r9.__file__),Path(r9.structure.__file__),Path(r9.pairs.__file__),Path(r9.chunks.__file__)]
    base.write(out/'e2e.json',dict(api_usd=0,protocol=protocol['fingerprint'],
        code_sha256={str(p.resolve().relative_to(base.ROOT)):base.digest(p) for p in code},books=books))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--source',type=Path,default=base.ROOT/'tmp/a1-v414-r11')
    cli.add_argument('--out',type=Path,required=True)
    args=cli.parse_args()
    run(args.source,args.out)
