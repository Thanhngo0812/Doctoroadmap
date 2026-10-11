"""Stronger hierarchy baselines and measurement of chunker contract overrides."""
import argparse
from collections import Counter, defaultdict, deque
from pathlib import Path
import sys
import hoc_tieu_de as base
import cay_tieu_de_r14 as tree
from doc2roadmap.domain.models import DocumentNode, DocumentTree
from doc2roadmap.domain.chunking import chunk_document
from doc2roadmap.infrastructure.text import SentencePieceTokenCounter
from doc2roadmap.domain.sentence_splitter import UnicodeSentenceSplitter
from doc2roadmap.domain.normalization import normalize_text


def style(row):
    return row.get('font'),round(row['size']*2)/2,bool(row['bold']),bool(row.get('italic'))


def rule(rows):
    levels=[]
    anchors=defaultdict(Counter)
    for row in rows:
        kind,number=tree.signature(row['text'])
        level={1:1,2:2,5:3,3:4,4:5+max(len(number)-1,0),6:9}.get(kind)
        levels.append(level)
        if level is not None: anchors[style(row)][level]+=1
    for i,row in enumerate(rows):
        if levels[i] is None:
            counts=anchors[style(row)]
            levels[i]=counts.most_common(1)[0][0] if counts else 2
    parents=[]; stack=[]
    for i,level in enumerate(levels):
        while stack and levels[stack[-1]]>=level: stack.pop()
        parents.append(stack[-1] if stack else -1)
        stack.append(i)
    return parents


def through_chunker(rows,counter,parents=None):
    levels=[]
    for i,row in enumerate(rows):
        levels.append(tree.r2.baseline.heading_level(row['text']) if parents is None else
                      1 if parents[i]<0 else levels[parents[i]]+1)
    nodes=[DocumentNode('section_header',r['text'],i,level=levels[i],page=r['page']) for i,r in enumerate(rows)]
    output=chunk_document(DocumentTree(nodes=nodes),'r14-headings-only',counter,UnicodeSentenceSplitter())
    by_title=defaultdict(deque)
    for i,r in enumerate(rows): by_title[normalize_text(r['text'])].append(i)
    mapped={output.sections[0].section_id:-1}
    predicted=[None]*len(rows)
    for s in output.sections[1:]:
        if not by_title[s.title]: raise ValueError('Section cannot be mapped to source heading')
        i=by_title[s.title].popleft()
        mapped[s.section_id]=i
        predicted[i]=mapped[s.parent_section_id]
    return predicted,output.structure_warnings


def partial_metrics(target,predicted):
    score=tree.metrics(target,[-1 if p is None else p for p in predicted])
    hits=sum(a==b for a,b in zip(target,predicted))
    score.update(parent_hits=hits,parent_accuracy=hits/max(len(target),1),
                 heading_coverage=sum(p is not None for p in predicted)/max(len(target),1),
                 rejected_headings=sum(p is None for p in predicted))
    return score


def run(out):
    assert not out.exists()
    source=base.ROOT/'tmp/a1-v414-r14/results.json'
    original=base.read(source)
    assert original['code_sha256'][str(Path(tree.__file__).resolve().relative_to(base.ROOT))]==base.digest(tree.__file__)
    counter=SentencePieceTokenCounter(base.ROOT/'vendor/gemma/tokenizer.model','google-gemma-sentencepiece-v1')
    result=dict(api_usd=0,source_sha256=base.digest(source),folds=[],
                code_sha256={str(Path(p).resolve().relative_to(base.ROOT)):base.digest(p) for p in (
                    __file__,base.ROOT/'src/doc2roadmap/domain/chunking.py',base.ROOT/'report/v4-14-r14b-giao-thuc-2026-10-07.md')})
    for book,fold in [('d01-08',f) for f in original['folds']]+[('doc-4',original['external'])]:
        entries=original['inputs'][book]['entries']
        if book=='d01-08': entries=tree.subset(entries,{fold['group']})
        rows=[e['row'] for e in entries]; target=[e['parent'] for e in entries]
        assert target==fold['target']
        chunk,warnings=through_chunker(rows,counter)
        transport,transport_warnings=through_chunker(rows,counter,fold['predicted'])
        record=dict(book=book,group=fold.get('group'),H0=fold['H0'],H2=fold['H2'],
                    H1=tree.metrics(target,rule(rows)),Hchunk=partial_metrics(target,chunk),
                    H2_through_chunker=partial_metrics(target,transport),
                    transport_parent_changes=sum(a!=b for a,b in zip(fold['predicted'],transport)),
                    chunker_warnings=warnings,transport_warnings=transport_warnings)
        result['folds'].append(record)
        print(book,record['group'],{v:round(record[v]['parent_accuracy'],3) for v in ('H0','H1','Hchunk','H2','H2_through_chunker')},flush=True)
    base.write(out/'results.json',result)


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--out',type=Path,required=True)
    run(cli.parse_args().out)
