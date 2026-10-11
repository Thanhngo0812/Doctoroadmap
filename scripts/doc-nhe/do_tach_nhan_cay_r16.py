"""Frozen R15 trees: isolate acceptance and hierarchy without retraining."""
import argparse
from pathlib import Path
import sys
import tach_nhan_cay_r16 as replay
from do_cay_day_du_r15 import outline_score
from danh_gia import leaf_score
from doc2roadmap.infrastructure.text import SentencePieceTokenCounter

base=replay.base


def parents_of(tree):
    parents=[]; stack=[]; depths=[]
    for n in tree.nodes:
        if n.node_type not in replay.chunking.HEADING_TYPES: continue
        while stack and depths[stack[-1]]>=n.level: stack.pop()
        parents.append(stack[-1] if stack else -1)
        stack.append(len(parents)-1); depths.append(n.level)
    return parents


def run(out):
    assert not out.exists()
    old=base.read(base.ROOT/'tmp/a1-v414-r15/e2e.json')
    sources={b['id']:b for b in base.read(base.ROOT/'tmp/doc-nhe-v414/manifest.json')['books']}
    outlines=base.read(base.ROOT/'tmp/a1-v414-r14/results.json')['inputs']
    counter=SentencePieceTokenCounter(base.ROOT/'vendor/gemma/tokenizer.model','google-gemma-sentencepiece-v1')
    books=[]; hashes={}
    for before in old['books']:
        key=before['id']; book=sources[key]
        paths={v:base.ROOT/'tmp/a1-v414-r15/trees'/key/(v+'.json') for v in ('H1','H2')}
        for path in paths.values(): hashes[str(path.relative_to(base.ROOT))]=base.digest(path)
        trees={v:replay.DocumentTree.from_dict(base.read(p)) for v,p in paths.items()}
        original=replay.DocumentTree.from_dict(trees['H1'].to_dict())
        for n in original.nodes:
            if n.node_type in replay.chunking.HEADING_TYPES: n.level=replay.light.heading_level(n.text)
        settings={k:v for k,v in book['chunk_config'].items() if k in (
            'max_tokens','max_table_tokens','hard_cap_tokens','target_tokens','sentence_overlap',
            'result_min_count','result_max_body_chars','heading_scheme')}
        baseline,keep,parents=replay.capture(original,key,counter,settings)
        reference=replay.chunks.chunks_of(replay.DocumentTree.from_dict(base.read(base.ROOT/book['tree'])),key,counter,settings)
        assert leaf_score(reference,baseline.chunks)==before['models']['existing']['leaf_strict']
        transmitted=replay.chunking.chunk_document(replay.declared(original,keep,parents),key,counter,
            replay.UnicodeSentenceSplitter(),**{**settings,'heading_scheme':'declared-v1'})
        # Legacy numeric levels can skip depths (e.g. a root at level 2).
        # Declared mode uses actual tree depth; every other chunk field must match.
        normalized=[{**replay.asdict(c),'heading_level':len(c.section_path)} for c in baseline.chunks]
        assert normalized==[replay.asdict(c) for c in transmitted.chunks],key
        heads=[dict(page=n.page,text=n.text) for n,k in zip(
            [n for n in original.nodes if n.node_type in replay.chunking.HEADING_TYPES],keep) if k]
        result=dict(id=key,split=book['split'],parent_model_in_sample=key=='d01-08',
            proposed=len(keep),accepted=sum(keep),rejected=len(keep)-sum(keep),
            chunk_transport_exact_except_depth=True,
            normalized_depths=sum(a.heading_level!=b.heading_level for a,b in zip(baseline.chunks,transmitted.chunks)),models={})
        variants={'existing':(baseline,parents)}
        for v,tree in trees.items():
            projected=replay.project(parents_of(tree),keep)
            output=replay.chunking.chunk_document(replay.declared(original,keep,projected),key,counter,
                replay.UnicodeSentenceSplitter(),**{**settings,'heading_scheme':'declared-v1'})
            assert [c.text for c in output.chunks]==[c.text for c in baseline.chunks]
            variants[v]=(output,projected)
        for v,(output,predicted) in variants.items():
            score=dict(leaf_strict=leaf_score(reference,output.chunks),path_strict=replay.path_score(reference,output.chunks))
            if key in outlines: score['outline']=outline_score(heads,predicted,outlines[key]['entries'])
            result['models'][v]=score
        base.write(out/'books'/(key+'.json'),result); books.append(result)
        print(key,result['accepted'],result['rejected'],{v:round(s['path_strict']['share'],4) for v,s in result['models'].items()},flush=True)
    paths=[Path(__file__),Path(replay.__file__),base.ROOT/'report/v4-14-r16-giao-thuc-2026-10-07.md',
           base.ROOT/'src/doc2roadmap/domain/chunking.py']
    base.write(out/'e2e.json',dict(api_usd=0,source_sha256=hashes,books=books,
        code_sha256={str(p.resolve().relative_to(base.ROOT)):base.digest(p) for p in paths}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--out',type=Path,required=True)
    run(cli.parse_args().out)
