"""Verify hierarchy transport after chapter and role corrections."""
import argparse
from collections import Counter
from pathlib import Path
import sys
import ung_vien_r20 as candidate
import so_muc_r17 as h3
from do_cay_day_du_r15 import outline_score

base=candidate.base
replay=candidate.replay


def run(out):
    assert not out.exists()
    source=base.ROOT/'tmp/a1-v414-r22/results.json'; prior=base.read(source)
    for path,sha in prior['code_sha256'].items(): assert base.digest(base.ROOT/path)==sha
    learned=base.read(base.ROOT/'tmp/a1-v414-r14/results.json')
    records={b['id']:b for b in prior['books']}
    data,_=candidate.r9.r8.load(base.ROOT/'tmp/a1-v414-r8c-model')
    counter=candidate.r9.SentencePieceTokenCounter(base.ROOT/'vendor/gemma/tokenizer.model','google-gemma-sentencepiece-v1')
    books=[]
    for key,d in data.items():
        rows,_=candidate.margin.prepare_rows(d['rows'])
        path=base.ROOT/'tmp/a1-v414-r22/nodes'/(key+'.json'); nodes=base.read(path)
        candidate.r9.verify_nodes(rows,d['figures'],nodes)
        tree_path=base.ROOT/'tmp/a1-v414-r22/trees'/(key+'.json')
        tree=candidate.r9.DocumentTree.from_dict(base.read(tree_path))
        settings={k:v for k,v in d['book']['chunk_config'].items() if k in (
            'max_tokens','max_table_tokens','hard_cap_tokens','target_tokens','sentence_overlap',
            'result_min_count','result_max_body_chars','heading_scheme')}
        baseline,keep,parents=replay.capture(tree,key,counter,settings)
        heads=[dict(rows[n['source_rows'][0]],text=n['text']) for n in nodes if n['node_type']=='section_header']
        accepted=[h for h,k in zip(heads,keep) if k]
        predicted=h3.rule(accepted)
        revised=replay.declared(tree,keep,predicted)
        output=replay.chunking.chunk_document(revised,key,counter,replay.UnicodeSentenceSplitter(),
                                              **{**settings,'heading_scheme':'declared-v1'})
        indexes={s.section_id:i-1 for i,s in enumerate(output.sections)}
        assert [indexes[s.parent_section_id] for s in output.sections[1:]]==predicted
        assert [c.text for c in baseline.chunks]==[c.text for c in output.chunks]
        for attr,field in [('image_refs','image_id'),('formula_refs','formula_id')]:
            assert Counter(getattr(r,field) for c in baseline.chunks for r in getattr(c,attr))==Counter(
                getattr(r,field) for c in output.chunks for r in getattr(c,attr))
        reference=candidate.r9.chunks.chunks_of(candidate.r9.DocumentTree.from_dict(base.read(base.ROOT/d['book']['tree'])),key,counter,settings)
        leaf=candidate.r9.leaf_score(reference,output.chunks)
        assert leaf==records[key]['models']['metadata']['leaf_strict']
        score=dict(leaf_strict=leaf,chunks=len(output.chunks),sections=len(output.sections),
                   image_refs=sum(len(c.image_refs) for c in output.chunks),formula_refs=sum(len(c.formula_refs) for c in output.chunks))
        entry=dict(id=key,source_nodes_sha256=base.digest(path),source_tree_sha256=base.digest(tree_path),
            changed_parents=sum(a!=b for a,b in zip(parents,predicted)),models=dict(default=dict(score),H3=dict(score)),
            structure_warnings=tree.structure_warnings)
        if key in learned['inputs']:
            for name,p in [('default',parents),('H3',predicted)]:
                entry['models'][name]['outline']=outline_score(accepted,p,learned['inputs'][key]['entries'])
        books.append(entry); base.write(out/'books'/(key+'.json'),entry)
        base.write(out/'trees'/(key+'.json'),revised.to_dict())
        print(key,'changed parents',entry['changed_parents'],entry['models']['H3'].get('outline',''),flush=True)
    paths=[Path(__file__),Path(h3.__file__),Path(replay.__file__),base.ROOT/'src/doc2roadmap/domain/chunking.py',
           base.ROOT/'report/v4-14-r23-giao-thuc-2026-10-08.md']
    base.write(out/'results.json',dict(api_usd=0,source_sha256=base.digest(source),books=books,
        code_sha256={str(p.resolve().relative_to(base.ROOT)):base.digest(p) for p in paths}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--out',type=Path,required=True)
    run(parser.parse_args().out)
