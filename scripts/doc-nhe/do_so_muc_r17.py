"""Evaluate the frozen H3 baseline on outline and actual predicted headings."""
import argparse
from pathlib import Path
import sys
import joblib
import doi_chung_r9 as r9
import loc_bien_r13 as margin
import cay_tieu_de_r14 as hierarchy
import so_muc_r17 as h3
import tach_nhan_cay_r16 as replay
from do_cay_day_du_r15 import outline_score

base=r9.base


def run(out):
    assert not out.exists()
    original=base.read(base.ROOT/'tmp/a1-v414-r14/results.json')
    folds=[]
    for key,fold in [('d01-08',f) for f in original['folds']]+[('doc-4',original['external'])]:
        entries=original['inputs'][key]['entries']
        if key=='d01-08': entries=hierarchy.subset(entries,{fold['group']})
        rows=[e['row'] for e in entries]; target=[e['parent'] for e in entries]
        folds.append(dict(book=key,group=fold.get('group'),H3=hierarchy.metrics(target,h3.rule(rows))))
    data,_=r9.r8.load(base.ROOT/'tmp/a1-v414-r8c-model')
    previous={b['id']:b for b in base.read(base.ROOT/'tmp/a1-v414-r16/e2e.json')['books']}
    counter=r9.SentencePieceTokenCounter(base.ROOT/'vendor/gemma/tokenizer.model','google-gemma-sentencepiece-v1')
    books=[]
    for key,d in data.items():
        rows,body=margin.prepare_rows(d['rows'])
        name=key if d['book']['split']=='train' else 'full'
        current=base.read(base.ROOT/'tmp/a1-v414-r8c-model/models'/(name+'.json'))
        model,_=r9.frozen(base.ROOT/'tmp/doc-nhe-v414',name+'-lightgbm',key,current['train_books'])
        flags=model.predict_proba(base.feature_matrix(rows,body))[:,1]>=.5
        model,_=r9.frozen(base.ROOT/'tmp/a1-v414-r5',name,key,current['train_books'])
        joins=model.predict_proba(r9.pairs.matrix(rows))[:,1]>=.5
        nodes,_=r9.structure.group_rows(rows,d['figures'],d['pages'],flags,prepare_rows=margin.prepare_rows)
        nodes=r9.pairs.regroup(rows,nodes,joins); r9.verify_nodes(rows,d['figures'],nodes)
        heads=[dict(rows[n['source_rows'][0]],text=n['text']) for n in nodes if n['node_type']=='section_header']
        tree=r9.chunks.light_tree(nodes)
        settings={k:v for k,v in d['book']['chunk_config'].items() if k in (
            'max_tokens','max_table_tokens','hard_cap_tokens','target_tokens','sentence_overlap',
            'result_min_count','result_max_body_chars','heading_scheme')}
        baseline,keep,_=replay.capture(tree,key,counter,settings)
        accepted=[h for h,k in zip(heads,keep) if k]
        parents=h3.rule(accepted)
        actual=replay.chunking.chunk_document(replay.declared(tree,keep,parents),key,counter,
            replay.UnicodeSentenceSplitter(),**{**settings,'heading_scheme':'declared-v1'})
        assert [c.text for c in actual.chunks]==[c.text for c in baseline.chunks]
        reference=r9.chunks.chunks_of(r9.DocumentTree.from_dict(base.read(base.ROOT/d['book']['tree'])),key,counter,settings)
        score=dict(leaf_strict=r9.leaf_score(reference,actual.chunks),path_strict=replay.path_score(reference,actual.chunks))
        assert score['leaf_strict']==previous[key]['models']['existing']['leaf_strict']
        if key in original['inputs']: score['outline']=outline_score(accepted,parents,original['inputs'][key]['entries'])
        record=dict(id=key,split=d['book']['split'],accepted=len(accepted),H3=score)
        base.write(out/'books'/(key+'.json'),record); books.append(record)
        print(key,score.get('outline',{}).get('parent_hits'),flush=True)
    paths=[Path(__file__),Path(h3.__file__),Path(replay.__file__),base.ROOT/'report/v4-14-r17-giao-thuc-2026-10-07.md']
    base.write(out/'results.json',dict(api_usd=0,folds=folds,books=books,
        code_sha256={str(p.resolve().relative_to(base.ROOT)):base.digest(p) for p in paths}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--out',type=Path,required=True)
    run(cli.parse_args().out)
