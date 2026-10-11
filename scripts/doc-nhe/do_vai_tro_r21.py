"""Replay R20 candidate and measure conservative diagram-text correction."""
import argparse
from pathlib import Path
import sys
import ung_vien_r20 as candidate
import chu_trong_hinh_r21 as roles

base=candidate.base


def run(out):
    assert not out.exists()
    prior_path=base.ROOT/'tmp/a1-v414-r20/results.json'
    prior=base.read(prior_path)
    for path,sha in prior['code_sha256'].items(): assert base.digest(base.ROOT/path)==sha
    records={b['id']:b for b in prior['books']}
    data,_=candidate.r9.r8.load(base.ROOT/'tmp/a1-v414-r8c-model')
    counter=candidate.r9.SentencePieceTokenCounter(base.ROOT/'vendor/gemma/tokenizer.model','google-gemma-sentencepiece-v1')
    books=[]
    for key,d in data.items():
        rows,_,assets,settings,models=candidate.prepare(key,d)
        path=base.ROOT/'tmp/a1-v414-r20/nodes'/(key+'.json'); nodes=base.read(path)
        body=candidate.margin.prepare_rows(d['rows'])[1]
        revised,audit=roles.correct(rows,nodes,body)
        candidate.r9.verify_nodes(rows,d['figures'],revised)
        tree,output,score=candidate.evaluate(key,revised,assets,settings,base.read(base.ROOT/d['book']['tree']),counter)
        old=records[key]['models']['chapter']
        assert score['image_refs']==old['image_refs'] and score['formula_refs']==old['formula_refs']
        if not audit: assert score==old
        entry=dict(id=key,audit=audit,body=body,source_sha256=base.digest(path),model_sha256=models,
                   models=dict(existing=old,roles=score))
        books.append(entry); base.write(out/'books'/(key+'.json'),entry)
        base.write(out/'nodes'/(key+'.json'),revised); base.write(out/'trees'/(key+'.json'),tree.to_dict())
        print(key,len(audit),old['leaf_strict']['share'],score['leaf_strict']['share'],flush=True)
    paths=[Path(__file__),Path(roles.__file__),base.ROOT/'report/v4-14-r21-giao-thuc-2026-10-08.md']
    base.write(out/'results.json',dict(api_usd=0,books=books,source_sha256=base.digest(prior_path),
        code_sha256={str(p.resolve().relative_to(base.ROOT)):base.digest(p) for p in paths}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--out',type=Path,required=True)
    run(parser.parse_args().out)
