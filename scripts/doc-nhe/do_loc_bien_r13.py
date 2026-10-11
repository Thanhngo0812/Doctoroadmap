"""Frozen-weight filter intervention; exact reuse for unchanged books."""
import argparse
from pathlib import Path
import sys
import numpy as np
import doi_chung_r9 as r9
import loc_bien_r13 as margin

base=r9.base


def run(out):
    assert not out.exists()
    data,parent=r9.r8.load(base.ROOT/'tmp/a1-v414-r8c-model')
    baselines={v:{b['id']:b['models'][name] for b in base.read(base.ROOT/path)['books']}
               for v,name,path in [('M2f','M2f_B2','tmp/a1-v414-r9/e2e.json'),
                                   ('WB133','WB133_B2','tmp/a1-v414-r11-e2e/e2e.json')]}
    counter=r9.SentencePieceTokenCounter(base.ROOT/'vendor/gemma/tokenizer.model','google-gemma-sentencepiece-v1')
    books=[]
    for key,d in data.items():
        rows,body=margin.prepare_rows(d['rows'])
        assert margin.prepare_rows(rows)[0]==rows
        source={id(r):i for i,r in enumerate(d['rows'])}
        indexes=[source[id(r)] for r in rows]
        kept=set(indexes)
        raw_indexes=np.asarray(d['raw_indexes'])[indexes]
        removed=[dict(retained_index=i,raw_index=d['raw_indexes'][i],row=r,
                      r1=d['raw_y'][d['raw_indexes'][i]],r3=d['raw_r3'][d['raw_indexes'][i]])
                 for i,r in enumerate(d['rows']) if i not in kept]
        book=d['book']
        result=dict(id=key,split=book['split'],removed=removed,models={},model_sha256={})
        name=key if book['split']=='train' else 'full'
        current=base.read(base.ROOT/'tmp/a1-v414-r8c-model/models'/(name+'.json'))
        pair_model,pr=r9.frozen(base.ROOT/'tmp/a1-v414-r5',name,key,current['train_books'])
        result['model_sha256']['B2']=pr['model_sha256']
        old_joins=pair_model.predict_proba(r9.pairs.matrix(d['rows']))[:,1]>=.5
        static_joins=old_joins[indexes].copy()
        for i in range(len(indexes)):
            if i==0 or indexes[i]!=indexes[i-1]+1:
                static_joins[i]=False
        fresh_joins=pair_model.predict_proba(r9.pairs.matrix(rows))[:,1]>=.5
        if removed:
            tree=base.read(base.ROOT/book['tree'])
            settings={k:v for k,v in book['chunk_config'].items() if k in (
                'max_tokens','max_table_tokens','hard_cap_tokens','target_tokens','sentence_overlap',
                'result_min_count','result_max_body_chars','heading_scheme')}
            reference=r9.chunks.chunks_of(r9.DocumentTree.from_dict(tree),key,counter,settings)
        for variant,root,suffix,features in [('M2f','tmp/doc-nhe-v414','-lightgbm',base.feature_matrix),
                                           ('WB133','tmp/a1-v414-r11','-WB133',r9.r4.feature_matrix)]:
            model,record=r9.frozen(base.ROOT/root,name+suffix,key,current['train_books'])
            result['model_sha256'][variant]=record['model_sha256']
            old_x=features(d['rows'],d['body'])
            old_p=model.predict_proba(old_x)[:,1]
            p=model.predict_proba(features(rows,body))[:,1]
            result['models'][variant+'_baseline']=baselines[variant][key]
            if not removed:
                assert rows==d['rows'] and body==d['body']
                np.testing.assert_array_equal(p,old_p)
                np.testing.assert_array_equal(fresh_joins,static_joins)
                for mode in ('static','fresh'):
                    result['models'][variant+'_'+mode]=baselines[variant][key]
                continue
            for mode,prob,joins in [('static',old_p[indexes],static_joins),('fresh',p,fresh_joins)]:
                nodes,_=r9.structure.group_rows(rows,d['figures'],d['pages'],prob>=.5,prepare_rows=margin.prepare_rows)
                nodes=r9.pairs.regroup(rows,nodes,joins)
                r9.verify_nodes(rows,d['figures'],nodes)
                actual=r9.chunks.chunks_of(r9.chunks.light_tree(nodes),key,counter,settings)
                raw=np.zeros(len(d['raw_y']),dtype=bool)
                raw[raw_indexes]=prob>=.5
                result['models'][variant+'_'+mode]=dict(
                    full_raw={label:base.metrics(np.asarray(d[field]),raw) for label,field in [('r1','raw_y'),('r3','raw_r3')]},
                    heading_strict=r9.heading_score(tree['nodes'],nodes),leaf_strict=r9.leaf_score(reference,actual),
                    chunk_legacy=r9.chunks.compare(reference,actual))
        result['measurement']='recomputed' if removed else 'unchanged_inputs_and_predictions_verified_reuse'
        base.write(out/'books'/(key+'.json'),result)
        books.append(result)
        print(key,'removed',len(removed),{v:round(s['leaf_strict']['share'],4) for v,s in result['models'].items()},flush=True)
    paths=[Path(__file__),Path(margin.__file__),Path(r9.__file__),Path(r9.structure.__file__),Path(r9.pairs.__file__),
           base.ROOT/'report/v4-14-r13-giao-thuc-2026-10-07.md']
    base.write(out/'e2e.json',dict(api_usd=0,parent=parent['fingerprint'],
        code_sha256={str(p.resolve().relative_to(base.ROOT)):base.digest(p) for p in paths},books=books))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--out',type=Path,required=True)
    run(cli.parse_args().out)
