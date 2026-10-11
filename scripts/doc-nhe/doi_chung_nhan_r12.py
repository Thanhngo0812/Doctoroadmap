"""Diagnostic silver intervention and self-comparison; never deployable models."""
import argparse
from pathlib import Path
import sys
import numpy as np
import doi_chung_r9 as r9

base=r9.base


def intervene(labels,predicted):
    labels,predicted=np.asarray(labels),np.asarray(predicted,dtype=bool)
    if labels.shape!=predicted.shape or not np.isin(labels,[-1,0,1]).all():
        raise ValueError('One binary/unknown label required per row')
    return np.where(labels>=0,labels==1,predicted)


def run(out):
    assert not out.exists()
    data,protocol=r9.r8.load(base.ROOT/'tmp/a1-v414-r8c-model')
    old={b['id']:b for b in base.read(base.ROOT/'tmp/a1-v414-r9/e2e.json')['books']}
    counter=r9.SentencePieceTokenCounter(base.ROOT/'vendor/gemma/tokenizer.model','google-gemma-sentencepiece-v1')
    books=[]
    for key,d in data.items():
        book=d['book']
        name=key if book['split']=='train' else 'full'
        current=base.read(base.ROOT/'tmp/a1-v414-r8c-model/models'/(name+'.json'))
        model,m2=r9.frozen(base.ROOT/'tmp/doc-nhe-v414',name+'-lightgbm',key,current['train_books'])
        predicted=model.predict_proba(d['X'])[:,1]>=.5
        model,b2=r9.frozen(base.ROOT/'tmp/a1-v414-r5',name,key,current['train_books'])
        joins=model.predict_proba(r9.pairs.matrix(d['rows']))[:,1]>=.5
        tree=base.read(base.ROOT/book['tree'])
        settings={k:v for k,v in book['chunk_config'].items() if k in (
            'max_tokens','max_table_tokens','hard_cap_tokens','target_tokens','sentence_overlap',
            'result_min_count','result_max_body_chars','heading_scheme')}
        reference=r9.chunks.chunks_of(r9.DocumentTree.from_dict(tree),key,counter,settings)
        result=dict(id=key,split=book['split'],models={},model_sha256={'M2':m2['model_sha256'],'B2':b2['model_sha256']},
                    self_control=dict(leaf_strict=r9.leaf_score(reference,reference),
                        chunk_legacy=r9.chunks.compare(reference,reference),
                        missing_leaf=sum(not c.section_path or not r9.structure.baseline.words(c.section_path[-1]) for c in reference)))
        flags={'M2f':predicted}
        for label,field in [('R1','raw_y'),('R3','raw_r3')]:
            flags[label]=intervene(np.asarray(d[field])[d['raw_indexes']],predicted)
        for variant,heading in flags.items():
            original,_=r9.structure.group_rows(d['rows'],d['figures'],d['pages'],heading,prepare_rows=r9.r8.margin.prepare_rows)
            for relation in ('B0','B2'):
                nodes=original if relation=='B0' else r9.pairs.regroup(d['rows'],original,joins)
                r9.verify_nodes(d['rows'],d['figures'],nodes)
                actual=r9.chunks.chunks_of(r9.chunks.light_tree(nodes),key,counter,settings)
                scores=dict(heading_strict=r9.heading_score(tree['nodes'],nodes),
                            leaf_strict=r9.leaf_score(reference,actual),chunk_legacy=r9.chunks.compare(reference,actual))
                if variant=='M2f':
                    for metric,value in scores.items():
                        assert value==old[key]['models'][variant+'_'+relation][metric]
                result['models'][variant+'_'+relation]=scores
        base.write(out/'books'/(key+'.json'),result)
        books.append(result)
        print(key,'self',round(result['self_control']['leaf_strict']['share'],4),
              {v:round(s['leaf_strict']['share'],4) for v,s in result['models'].items()},flush=True)
    paths=[Path(__file__),Path(r9.__file__),Path(r9.structure.__file__),Path(r9.pairs.__file__),
           base.ROOT/'scripts/doc-nhe/danh_gia.py',base.ROOT/'report/v4-14-r12-giao-thuc-2026-10-07.md']
    base.write(out/'e2e.json',dict(api_usd=0,status='diagnostic_uses_target_silver_not_deployable',
        r8_protocol=protocol['fingerprint'],code_sha256={str(p.resolve().relative_to(base.ROOT)):base.digest(p) for p in paths},books=books))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--out',type=Path,required=True)
    run(cli.parse_args().out)
