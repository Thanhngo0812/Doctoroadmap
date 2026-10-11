"""Frozen-model counterfactuals on R8c inputs, with/without R5 continuation."""
import argparse
from pathlib import Path
import sys
import joblib
import numpy as np
import hoc_loc_le_r8c as r8
import hoc_r4 as r4
import noi_tieu_de_r5 as pairs
import cau_truc_r2 as structure
from do_r2 import verify_nodes
from danh_gia import heading_score, leaf_score
import so_chunk_doc_nhe as chunks
from doc2roadmap.domain.models import DocumentTree
from doc2roadmap.infrastructure.text import SentencePieceTokenCounter

base=r8.base


def frozen(root,name,key,train_books):
    record=base.read(root/'models'/(name+'.json'))
    path=root/'models'/(name+'.joblib')
    assert base.digest(path)==record['model_sha256']
    assert key not in record['train_books'] and key in record['heldout']
    assert set(record['train_books'])==set(train_books)
    return joblib.load(path),record


def run(out):
    assert not out.exists(), 'Use new output directory'
    data,protocol=r8.load(base.ROOT/'tmp/a1-v414-r8c-model')
    stamp={str(Path(p).relative_to(base.ROOT)):base.digest(p) for p in (
        Path(__file__).resolve(),Path(structure.__file__),Path(pairs.__file__),Path(r4.__file__),Path(r8.__file__),
        Path(r8.margin.__file__),base.ROOT/'report/v4-14-r9-giao-thuc-2026-10-07.md')}
    assert base.read(base.ROOT/'tmp/a1-v414-r4/protocol.json')['script_sha256']==base.digest(r4.__file__)
    assert base.read(base.ROOT/'tmp/a1-v414-r5/protocol.json')['pair_code_sha256']==base.digest(pairs.__file__)
    counter=SentencePieceTokenCounter(base.ROOT/'vendor/gemma/tokenizer.model','google-gemma-sentencepiece-v1')
    books=[]
    for key,d in data.items():
        book=d['book']
        name=key if book['split']=='train' else 'full'
        current=base.read(base.ROOT/'tmp/a1-v414-r8c-model/models'/(name+'.json'))
        assert current['fingerprint']==protocol['fingerprint']
        model,m2=frozen(base.ROOT/'tmp/doc-nhe-v414',name+'-lightgbm',key,current['train_books'])
        assert m2['fingerprint']==base.code_fingerprint()
        probs={'M2c':np.asarray(current['predictions'][key]['probability']),
               'M2f':model.predict_proba(d['X'])[:,1]}
        model,e2=frozen(base.ROOT/'tmp/a1-v414-r4',name+'-E2',key,current['train_books'])
        probs['E2f']=model.predict_proba(r4.feature_matrix(d['rows'],d['body']))[:,1]
        probs['Mean']=(probs['M2f']+probs['E2f'])/2
        model,pair_record=frozen(base.ROOT/'tmp/a1-v414-r5',name,key,current['train_books'])
        joins=model.predict_proba(pairs.matrix(d['rows']))[:,1]>=.5
        tree=base.read(base.ROOT/book['tree'])
        settings={k:v for k,v in book['chunk_config'].items() if k in (
            'max_tokens','max_table_tokens','hard_cap_tokens','target_tokens','sentence_overlap',
            'result_min_count','result_max_body_chars','heading_scheme')}
        reference=chunks.chunks_of(DocumentTree.from_dict(tree),key,counter,settings)
        result=dict(id=key,split=book['split'],models={},probability={k:p.tolist() for k,p in probs.items()},
                    model_sha256={k:r['model_sha256'] for k,r in [('M2c',current),('M2f',m2),('E2f',e2),('B2',pair_record)]})
        for variant,p in probs.items():
            raw_pred=np.zeros(len(d['raw_y']),dtype=bool)
            raw_pred[d['raw_indexes']]=p>=.5
            row_score={label:base.metrics(np.asarray(d[field]),raw_pred) for label,field in [('r1','raw_y'),('r3','raw_r3')]}
            original,_=structure.group_rows(d['rows'],d['figures'],d['pages'],p>=.5,prepare_rows=r8.margin.prepare_rows)
            for relation in ('B0','B2'):
                nodes=original if relation=='B0' else pairs.regroup(d['rows'],original,joins)
                verify_nodes(d['rows'],d['figures'],nodes)
                actual=chunks.chunks_of(chunks.light_tree(nodes),key,counter,settings)
                result['models'][variant+'_'+relation]=dict(full_raw=row_score,
                    heading_strict=heading_score(tree['nodes'],nodes),leaf_strict=leaf_score(reference,actual),
                    chunk_legacy=chunks.compare(reference,actual))
        previous=base.read(base.ROOT/'tmp/a1-v414-r8c-model/e2e'/(key+'.json'))['new']
        for metric in previous:
            assert result['models']['M2c_B0'][metric]==previous[metric]
        base.write(out/'books'/(key+'.json'),result)
        books.append(result)
        print(key,{v:round(r['leaf_strict']['share'],4) for v,r in result['models'].items()},flush=True)
    base.write(out/'e2e.json',dict(api_usd=0,code_sha256=stamp,r8_protocol=protocol['fingerprint'],books=books))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--out',type=Path,required=True)
    run(cli.parse_args().out)
