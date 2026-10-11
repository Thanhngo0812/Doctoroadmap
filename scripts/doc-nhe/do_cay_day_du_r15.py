"""Actual predicted headings + H1/H2 hierarchy; research artifacts only."""
import argparse
from pathlib import Path
import sys
import joblib
import numpy as np
import doi_chung_r9 as r9
import loc_bien_r13 as margin
import cay_tieu_de_r14 as hierarchy
from doi_chung_cay_r14b import rule
from nhan_khoi_r3 import tokens
from doc2roadmap.domain.chunking import chunk_document
from doc2roadmap.domain.sentence_splitter import UnicodeSentenceSplitter

base=r9.base


def outline_score(headings,parents,entries):
    matches={}
    used=set()
    for i,h in enumerate(headings):
        found=[j for j,e in enumerate(entries) if e['row']['page']==h['page'] and tokens(e['row']['text'])==tokens(h['text'])]
        if len(found)==1 and found[0] not in used:
            # Reject duplicate predictions of the same source title too.
            if sum(h['page']==other['page'] and tokens(h['text'])==tokens(other['text']) for other in headings)!=1:
                continue
            matches[i]=found[0]; used.add(found[0])
    hits=0; wrong_unmatched_parent=0
    for i,j in matches.items():
        target=entries[j]['parent']
        while target!=-1 and target not in used: target=entries[target]['parent']
        predicted=-1 if parents[i]<0 else matches.get(parents[i],-2)
        hits+=predicted==target
        wrong_unmatched_parent+=predicted==-2
    return dict(reference_headings=len(entries),predicted_headings=len(headings),matched=len(matches),
                coverage=len(matches)/max(len(entries),1),unmatched_predicted=len(headings)-len(matches),
                parent_hits=hits,parent_accuracy_on_matched=hits/max(len(matches),1),
                joint_hits_per_reference=hits/max(len(entries),1),unmatched_parent_errors=wrong_unmatched_parent)


def run(out):
    assert not out.exists()
    data,parent=r9.r8.load(base.ROOT/'tmp/a1-v414-r8c-model')
    model_record=base.read(base.ROOT/'tmp/a1-v414-r14/results.json')
    path=base.ROOT/'tmp/a1-v414-r14/parent-model.joblib'
    assert base.digest(path)==model_record['model_sha256']
    assert model_record['code_sha256'][str(Path(hierarchy.__file__).resolve().relative_to(base.ROOT))]==base.digest(hierarchy.__file__)
    parent_model=joblib.load(path)
    counter=r9.SentencePieceTokenCounter(base.ROOT/'vendor/gemma/tokenizer.model','google-gemma-sentencepiece-v1')
    books=[]
    previous={b['id']:b for b in base.read(base.ROOT/'tmp/a1-v414-r13/e2e.json')['books']}
    for key,d in data.items():
        rows,body=margin.prepare_rows(d['rows'])
        name=key if d['book']['split']=='train' else 'full'
        current=base.read(base.ROOT/'tmp/a1-v414-r8c-model/models'/(name+'.json'))
        model,_=r9.frozen(base.ROOT/'tmp/doc-nhe-v414',name+'-lightgbm',key,current['train_books'])
        flags=model.predict_proba(base.feature_matrix(rows,body))[:,1]>=.5
        model,_=r9.frozen(base.ROOT/'tmp/a1-v414-r5',name,key,current['train_books'])
        joins=model.predict_proba(r9.pairs.matrix(rows))[:,1]>=.5
        nodes,_=r9.structure.group_rows(rows,d['figures'],d['pages'],flags,prepare_rows=margin.prepare_rows)
        nodes=r9.pairs.regroup(rows,nodes,joins)
        r9.verify_nodes(rows,d['figures'],nodes)
        headings=[dict(rows[n['source_rows'][0]],text=n['text']) for n in nodes if n['node_type']=='section_header']
        def score(rows,i,candidates,parents):
            x=np.asarray([hierarchy.pair_features(rows,i,p,parents) for p in candidates],dtype=np.float32)
            return parent_model.predict_proba(x)[:,1]
        parents_by={'H1':rule(headings),'H2':hierarchy.decode(headings,score)}
        tree=r9.DocumentTree.from_dict(base.read(base.ROOT/d['book']['tree']))
        settings={k:v for k,v in d['book']['chunk_config'].items() if k in (
            'max_tokens','max_table_tokens','hard_cap_tokens','target_tokens','sentence_overlap',
            'result_min_count','result_max_body_chars','heading_scheme')}
        reference=r9.chunks.chunks_of(tree,key,counter,settings)
        result=dict(id=key,split=d['book']['split'],parent_model_in_sample=key=='d01-08',models={})
        baseline=previous[key]['models']['M2f_fresh']
        result['models']['existing']=baseline
        for variant,parents in parents_by.items():
            candidate=r9.chunks.light_tree(nodes)
            hnodes=[n for n in candidate.nodes if n.node_type=='section_header']
            assert len(hnodes)==len(parents)
            depth=[]
            for i,n in enumerate(hnodes):
                depth.append(1 if parents[i]<0 else depth[parents[i]]+1)
                n.level=depth[i]
            actual=chunk_document(candidate,key,counter,UnicodeSentenceSplitter(),**{**settings,'heading_scheme':'declared-v1'})
            # Independently verify actual section parent IDs, not only assigned node levels.
            section_index={s.section_id:i-1 for i,s in enumerate(actual.sections)}
            observed=[section_index[s.parent_section_id] for s in actual.sections[1:]]
            assert observed==parents
            base.write(out/'trees'/key/(variant+'.json'),candidate.to_dict())
            result['models'][variant]=dict(leaf_strict=r9.leaf_score(reference,actual.chunks),
                chunk_legacy=r9.chunks.compare(reference,actual.chunks),heading_strict=baseline['heading_strict'])
            if key in model_record['inputs']:
                result['models'][variant]['outline']=outline_score(headings,parents,model_record['inputs'][key]['entries'])
        base.write(out/'books'/(key+'.json'),result)
        books.append(result)
        print(key,{v:round(s['leaf_strict']['share'],4) for v,s in result['models'].items()},flush=True)
    paths=[Path(__file__),Path(margin.__file__),Path(hierarchy.__file__),base.ROOT/'scripts/doc-nhe/doi_chung_cay_r14b.py',
           base.ROOT/'src/doc2roadmap/domain/chunking.py',base.ROOT/'report/v4-14-r15-giao-thuc-2026-10-07.md']
    base.write(out/'e2e.json',dict(api_usd=0,parent_model_sha256=model_record['model_sha256'],
        code_sha256={str(p.resolve().relative_to(base.ROOT)):base.digest(p) for p in paths},books=books))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--out',type=Path,required=True)
    run(cli.parse_args().out)
