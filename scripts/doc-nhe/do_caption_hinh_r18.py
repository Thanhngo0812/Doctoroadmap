"""Frozen M2f+B2 with geometry-qualified caption veto, all development books."""
import argparse
from pathlib import Path
import sys
import joblib
import doi_chung_r9 as r9
import loc_bien_r13 as margin
import caption_hinh_r18 as captions

base=r9.base


def run(out):
    assert not out.exists()
    data,_=r9.r8.load(base.ROOT/'tmp/a1-v414-r8c-model')
    previous={b['id']:b for b in base.read(base.ROOT/'tmp/a1-v414-r13/e2e.json')['books']}
    counter=r9.SentencePieceTokenCounter(base.ROOT/'vendor/gemma/tokenizer.model','google-gemma-sentencepiece-v1')
    books=[]
    for key,d in data.items():
        rows,body=margin.prepare_rows(d['rows'])
        name=key if d['book']['split']=='train' else 'full'
        current=base.read(base.ROOT/'tmp/a1-v414-r8c-model/models'/(name+'.json'))
        model,mrecord=r9.frozen(base.ROOT/'tmp/doc-nhe-v414',name+'-lightgbm',key,current['train_books'])
        flags=model.predict_proba(base.feature_matrix(rows,body))[:,1]>=.5
        proposed=captions.candidates(rows,d['figures'])
        changed=[i for i in proposed if flags[i]]
        original=flags.copy(); flags[changed]=False
        model,precord=r9.frozen(base.ROOT/'tmp/a1-v414-r5',name,key,current['train_books'])
        joins=model.predict_proba(r9.pairs.matrix(rows))[:,1]>=.5
        tree=base.read(base.ROOT/d['book']['tree'])
        settings={k:v for k,v in d['book']['chunk_config'].items() if k in (
            'max_tokens','max_table_tokens','hard_cap_tokens','target_tokens','sentence_overlap',
            'result_min_count','result_max_body_chars','heading_scheme')}
        reference=r9.chunks.chunks_of(r9.DocumentTree.from_dict(tree),key,counter,settings)
        by_identity={id(r):i for i,r in enumerate(d['rows'])}
        audit=[]
        for i in changed:
            old=by_identity[id(rows[i])]; raw=d['raw_indexes'][old]
            audit.append(dict(row_index=i,text=rows[i]['text'],page=rows[i]['page'],
                              r1=int(d['raw_y'][raw]),r3=int(d['raw_r3'][raw])))
        record=dict(id=key,split=d['book']['split'],qualified=len(proposed),changed=audit,
                    model_sha256=dict(M2f=mrecord['model_sha256'],B2=precord['model_sha256']),models={})
        for variant,p in [('existing',original),('caption',flags)]:
            raw=r9.np.zeros(len(d['raw_y']),dtype=bool)
            indexes=[d['raw_indexes'][by_identity[id(row)]] for row in rows]
            raw[indexes]=p
            nodes,_=r9.structure.group_rows(rows,d['figures'],d['pages'],p,prepare_rows=margin.prepare_rows)
            nodes=r9.pairs.regroup(rows,nodes,joins); r9.verify_nodes(rows,d['figures'],nodes)
            actual=r9.chunks.chunks_of(r9.chunks.light_tree(nodes),key,counter,settings)
            record['models'][variant]=dict(full_raw={label:base.metrics(r9.np.asarray(d[field]),raw)
                for label,field in [('r1','raw_y'),('r3','raw_r3')]},heading_strict=r9.heading_score(tree['nodes'],nodes),
                leaf_strict=r9.leaf_score(reference,actual),chunk_legacy=r9.chunks.compare(reference,actual))
        assert record['models']['existing']==previous[key]['models']['M2f_fresh']
        base.write(out/'books'/(key+'.json'),record); books.append(record)
        print(key,len(proposed),len(changed),{v:round(s['leaf_strict']['share'],4) for v,s in record['models'].items()},flush=True)
    paths=[Path(__file__),Path(captions.__file__),base.ROOT/'report/v4-14-r18-giao-thuc-2026-10-07.md']
    base.write(out/'results.json',dict(api_usd=0,books=books,
        code_sha256={str(p.resolve().relative_to(base.ROOT)):base.digest(p) for p in paths}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--out',type=Path,required=True)
    run(cli.parse_args().out)
