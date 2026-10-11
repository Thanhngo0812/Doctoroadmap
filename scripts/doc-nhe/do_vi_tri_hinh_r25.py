"""Measure image-anchor resolution, preserving separate internal-order warnings."""
import argparse
from collections import Counter
from pathlib import Path
import sys
import ung_vien_r20 as candidate
import vi_tri_hinh_r25 as placement

base=candidate.base


def refs(output,kind,field):
    return Counter(getattr(r,field) for c in output.chunks for r in getattr(c,kind))


def run(out):
    assert not out.exists()
    source=base.ROOT/'tmp/a1-v414-r24/results.json';prior=base.read(source)
    for path,sha in prior['code_sha256'].items():assert base.digest(base.ROOT/path)==sha
    records={b['id']:b for b in prior['books']}
    data,_=candidate.r9.r8.load(base.ROOT/'tmp/a1-v414-r8c-model')
    counter=candidate.r9.SentencePieceTokenCounter(base.ROOT/'vendor/gemma/tokenizer.model','google-gemma-sentencepiece-v1')
    books=[]
    for key,d in data.items():
        rows,_,assets,settings,models=candidate.prepare(key,d)
        path=base.ROOT/'tmp/a1-v414-r24/nodes'/(key+'.json');nodes=base.read(path)
        candidate.r9.verify_nodes(rows,d['figures'],nodes)
        reference=base.read(base.ROOT/d['book']['tree'])
        _,before,before_score=candidate.evaluate(key,nodes,assets,settings,reference,counter)
        assert before_score==records[key]['models']['inline_script']
        placed,warnings=placement.place(rows,nodes,assets)
        assert [n for n in nodes if n['node_type']!='figure']==[n for n in placed if n['node_type']!='figure']
        tree=candidate.images.document_tree(placed,warnings)
        output=candidate.replay.chunking.chunk_document(tree,key,counter,candidate.replay.UnicodeSentenceSplitter(),**settings)
        for kind,field in [('image_refs','image_id'),('formula_refs','formula_id')]:assert refs(output,kind,field)==refs(before,kind,field)
        target=candidate.r9.chunks.chunks_of(candidate.r9.DocumentTree.from_dict(reference),key,counter,settings)
        score=dict(leaf_strict=candidate.r9.leaf_score(target,output.chunks),chunks=len(output.chunks),sections=len(output.sections),
                   image_refs=sum(len(c.image_refs) for c in output.chunks),formula_refs=sum(len(c.formula_refs) for c in output.chunks))
        moved=[dict(page=n['page'],source_figure=n['source_figure'],bbox=n['bbox']) for n in placed
               if n['node_type']=='figure' and n['placement']=='external_vertical_gap']
        entry=dict(id=key,source_sha256=base.digest(path),model_sha256=models,models=dict(existing=before_score,placement=score),
                   moved=moved,warnings=warnings,placements=dict(Counter(n['placement'] for n in placed if n['node_type']=='figure')))
        if not moved:assert score['leaf_strict']==before_score['leaf_strict']
        books.append(entry);base.write(out/'books'/(key+'.json'),entry);base.write(out/'trees'/(key+'.json'),tree.to_dict())
        print(key,len(moved),before_score['leaf_strict']['share'],score['leaf_strict']['share'],flush=True)
    paths=[Path(__file__),Path(placement.__file__),base.ROOT/'report/v4-14-r25-giao-thuc-2026-10-08.md']
    base.write(out/'results.json',dict(api_usd=0,source_sha256=base.digest(source),books=books,
        code_sha256={str(p.resolve().relative_to(base.ROOT)):base.digest(p) for p in paths}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    run(parser.parse_args().out)
