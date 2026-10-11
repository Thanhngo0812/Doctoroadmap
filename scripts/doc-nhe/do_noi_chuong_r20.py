"""All-book chapter-title ablation; all old metrics and inputs stay frozen."""
import argparse
from pathlib import Path
import sys
import ung_vien_r20 as candidate
import noi_chuong_r20 as chapter

base=candidate.base


def run(out):
    assert not out.exists()
    data,_=candidate.r9.r8.load(base.ROOT/'tmp/a1-v414-r8c-model')
    prior={b['id']:b for b in base.read(base.ROOT/'tmp/a1-v414-r19/results.json')['books']}
    counter=candidate.r9.SentencePieceTokenCounter(base.ROOT/'vendor/gemma/tokenizer.model','google-gemma-sentencepiece-v1')
    books=[]
    for key,d in data.items():
        rows,nodes,assets,settings,models=candidate.prepare(key,d)
        revised,audit=chapter.combine(rows,nodes)
        candidate.r9.verify_nodes(rows,d['figures'],revised)
        reference=base.read(base.ROOT/d['book']['tree'])
        result=dict(id=key,split=d['book']['split'],audit=audit,model_sha256=models,models={})
        for variant,current in [('existing',nodes),('chapter',revised)]:
            tree,output,score=candidate.evaluate(key,current,assets,settings,reference,counter)
            result['models'][variant]=score
            base.write(out/'trees'/key/(variant+'.json'),tree.to_dict())
            if variant=='chapter': base.write(out/'nodes'/(key+'.json'),current)
        expected=prior[key]['models']['default']
        assert all(result['models']['existing'][k]==v for k,v in expected.items() if k!='outline')
        base.write(out/'books'/(key+'.json'),result); books.append(result)
        print(key,sum(a['joined'] for a in audit),{v:round(s['leaf_strict']['share'],4) for v,s in result['models'].items()},flush=True)
    paths=[Path(__file__),Path(chapter.__file__),Path(candidate.__file__),base.ROOT/'report/v4-14-r20-giao-thuc-2026-10-08.md']
    base.write(out/'results.json',dict(api_usd=0,books=books,
        code_sha256={str(p.resolve().relative_to(base.ROOT)):base.digest(p) for p in paths}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    run(parser.parse_args().out)
