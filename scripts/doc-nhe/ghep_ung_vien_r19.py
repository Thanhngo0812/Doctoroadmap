"""Integrate existing research components without promoting the light parser."""
import argparse
from collections import Counter
from pathlib import Path
import sys
import joblib
import doi_chung_r9 as r9
import loc_bien_r13 as margin
import caption_hinh_r18 as captions
import hinh_r6 as images
import cay_tieu_de_r14 as hierarchy
import so_muc_r17 as h3
import tach_nhan_cay_r16 as replay
from do_cay_day_du_r15 import outline_score

base=r9.base


def run(out):
    assert not out.exists()
    data,_=r9.r8.load(base.ROOT/'tmp/a1-v414-r8c-model')
    before={b['id']:b for b in base.read(base.ROOT/'tmp/a1-v414-r18/results.json')['books']}
    learned=base.read(base.ROOT/'tmp/a1-v414-r14/results.json')
    model_path=base.ROOT/'tmp/a1-v414-r14/parent-model.joblib'
    assert base.digest(model_path)==learned['model_sha256']
    parent_model=joblib.load(model_path)
    counter=r9.SentencePieceTokenCounter(base.ROOT/'vendor/gemma/tokenizer.model','google-gemma-sentencepiece-v1')
    books=[]
    for key,d in data.items():
        rows,body=margin.prepare_rows(d['rows'])
        name=key if d['book']['split']=='train' else 'full'
        current=base.read(base.ROOT/'tmp/a1-v414-r8c-model/models'/(name+'.json'))
        model,_=r9.frozen(base.ROOT/'tmp/doc-nhe-v414',name+'-lightgbm',key,current['train_books'])
        flags=model.predict_proba(base.feature_matrix(rows,body))[:,1]>=.5
        flags[captions.candidates(rows,d['figures'])]=False
        model,_=r9.frozen(base.ROOT/'tmp/a1-v414-r5',name,key,current['train_books'])
        joins=model.predict_proba(r9.pairs.matrix(rows))[:,1]>=.5
        nodes,_=r9.structure.group_rows(rows,d['figures'],d['pages'],flags,prepare_rows=margin.prepare_rows)
        nodes=r9.pairs.regroup(rows,nodes,joins); r9.verify_nodes(rows,d['figures'],nodes)
        assets=base.read(base.ROOT/'tmp/a1-v414-r6-native-resolution/books'/(key+'.json'))['assets']
        for asset in assets:
            if asset['image_id']:
                assert base.digest(base.ROOT/'tmp/a1-v414-r6-native-resolution/images'/(asset['image_id']+'.png'))==asset['image_id']
        placed,warnings=images.place_figures(nodes,assets)
        assert [n for n in nodes if n['node_type']!='figure']==[n for n in placed if n['node_type']!='figure']
        tree=images.document_tree(placed,warnings)
        settings={k:v for k,v in d['book']['chunk_config'].items() if k in (
            'max_tokens','max_table_tokens','hard_cap_tokens','target_tokens','sentence_overlap',
            'result_min_count','result_max_body_chars','heading_scheme')}
        reference=r9.chunks.chunks_of(r9.DocumentTree.from_dict(base.read(base.ROOT/d['book']['tree'])),key,counter,settings)
        baseline,keep,parents=replay.capture(tree,key,counter,settings)
        heads=[dict(rows[n['source_rows'][0]],text=n['text']) for n in nodes if n['node_type']=='section_header']
        accepted=[h for h,k in zip(heads,keep) if k]
        def score(rows,i,candidates,parents):
            x=r9.np.asarray([hierarchy.pair_features(rows,i,p,parents) for p in candidates],dtype=r9.np.float32)
            return parent_model.predict_proba(x)[:,1]
        variants={'default':parents,'H2':hierarchy.decode(accepted,score),'H3':h3.rule(accepted)}
        record=dict(id=key,split=d['book']['split'],parent_model_in_sample=key=='d01-08',
            placement_counts=dict(Counter(n['placement'] for n in placed if n['node_type']=='figure')),
            baseline_without_assets=before[key]['models']['caption'],models={})
        expected=Counter(a['image_id'] for a in assets if a['image_id'])
        for v,predicted in variants.items():
            candidate=tree if v=='default' else replay.declared(tree,keep,predicted)
            output=baseline if v=='default' else replay.chunking.chunk_document(candidate,key,counter,
                replay.UnicodeSentenceSplitter(),**{**settings,'heading_scheme':'declared-v1'})
            refs=[r.image_id for c in output.chunks for r in c.image_refs]
            assert Counter(refs)==expected
            scores=dict(leaf_strict=r9.leaf_score(reference,output.chunks),chunks=len(output.chunks),
                sections=len(output.sections),image_refs=len(refs),formula_refs=sum(len(c.formula_refs) for c in output.chunks))
            if key in learned['inputs']: scores['outline']=outline_score(accepted,predicted,learned['inputs'][key]['entries'])
            record['models'][v]=scores
            base.write(out/'trees'/key/(v+'.json'),candidate.to_dict())
        base.write(out/'books'/(key+'.json'),record); books.append(record)
        print(key,{v:round(s['leaf_strict']['share'],4) for v,s in record['models'].items()},flush=True)
    paths=[Path(__file__),Path(images.__file__),Path(h3.__file__),Path(captions.__file__),Path(hierarchy.__file__),
           base.ROOT/'report/v4-14-r19-giao-thuc-2026-10-07.md']
    base.write(out/'results.json',dict(api_usd=0,books=books,
        code_sha256={str(p.resolve().relative_to(base.ROOT)):base.digest(p) for p in paths}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--out',type=Path,required=True)
    run(cli.parse_args().out)
