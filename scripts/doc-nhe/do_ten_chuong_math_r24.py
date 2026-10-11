"""Measure a narrow inline-script role correction and verify exact ref deltas."""
import argparse
from collections import Counter
from pathlib import Path
import sys
import ung_vien_r20 as candidate
import ten_chuong_math_r24 as titles

base=candidate.base


def run(out):
    assert not out.exists()
    source=base.ROOT/'tmp/a1-v414-r22/results.json'; prior=base.read(source)
    for path,sha in prior['code_sha256'].items(): assert base.digest(base.ROOT/path)==sha
    records={b['id']:b for b in prior['books']}
    data,_=candidate.r9.r8.load(base.ROOT/'tmp/a1-v414-r8c-model')
    counter=candidate.r9.SentencePieceTokenCounter(base.ROOT/'vendor/gemma/tokenizer.model','google-gemma-sentencepiece-v1')
    books=[]
    for key,d in data.items():
        rows,_,assets,settings,models=candidate.prepare(key,d)
        path=base.ROOT/'tmp/a1-v414-r22/nodes'/(key+'.json');nodes=base.read(path)
        body=candidate.margin.prepare_rows(d['rows'])[1]
        revised,audit=titles.combine(rows,nodes,body)
        candidate.r9.verify_nodes(rows,d['figures'],revised)
        reference=base.read(base.ROOT/d['book']['tree'])
        tree,output,score=candidate.evaluate(key,revised,assets,settings,reference,counter)
        old=records[key]['models']['metadata']
        assert score['image_refs']==old['image_refs']
        if not audit: assert score==old
        else:
            _,before,before_score=candidate.evaluate(key,nodes,assets,settings,reference,counter)
            assert before_score==old
            expected=Counter(r.formula_id for c in before.chunks for r in c.formula_refs)
            for event in audit:
                formula=event['former_formula_id']; assert expected[formula]>0; expected[formula]-=1
            actual=Counter(r.formula_id for c in output.chunks for r in c.formula_refs)
            assert actual==+expected, 'Unexpected lost/duplicated formulas beyond corrected inline scripts'
            assert score['formula_refs']==old['formula_refs']-len(audit)
        entry=dict(id=key,audit=audit,source_sha256=base.digest(path),model_sha256=models,
                   models=dict(existing=old,inline_script=score))
        books.append(entry);base.write(out/'books'/(key+'.json'),entry)
        base.write(out/'nodes'/(key+'.json'),revised);base.write(out/'trees'/(key+'.json'),tree.to_dict())
        print(key,len(audit),old['leaf_strict']['share'],score['leaf_strict']['share'],flush=True)
    paths=[Path(__file__),Path(titles.__file__),base.ROOT/'report/v4-14-r24-giao-thuc-2026-10-08.md']
    base.write(out/'results.json',dict(api_usd=0,source_sha256=base.digest(source),books=books,
        code_sha256={str(p.resolve().relative_to(base.ROOT)):base.digest(p) for p in paths}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    run(parser.parse_args().out)
