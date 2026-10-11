"""Verify actual Section parent IDs reproduce frozen hierarchy predictions."""
from pathlib import Path
import sys
import hoc_tieu_de as base
from doi_chung_cay_r14b import tree,rule,partial_metrics
from doc2roadmap.domain.models import DocumentNode,DocumentTree
from doc2roadmap.domain.chunking import chunk_document
from doc2roadmap.infrastructure.text import SentencePieceTokenCounter
from doc2roadmap.domain.sentence_splitter import UnicodeSentenceSplitter


def run(out):
    assert not out.exists()
    source=base.read(base.ROOT/'tmp/a1-v414-r14/results.json')
    counter=SentencePieceTokenCounter(base.ROOT/'vendor/gemma/tokenizer.model','google-gemma-sentencepiece-v1')
    records=[]
    for book,fold in [('d01-08',f) for f in source['folds']]+[('doc-4',source['external'])]:
        entries=source['inputs'][book]['entries']
        if book=='d01-08': entries=tree.subset(entries,{fold['group']})
        rows=[e['row'] for e in entries]
        for variant,parents in [('H1',rule(rows)),('H2',fold['predicted'])]:
            depth=[]; nodes=[]
            for i,row in enumerate(rows):
                depth.append(1 if parents[i]<0 else depth[parents[i]]+1)
                nodes.append(DocumentNode('section_header',row['text'],len(nodes),level=depth[i],page=row['page']))
                # Synthetic payload tests ownership, not PDF parsing accuracy.
                nodes.append(DocumentNode('paragraph',f'Payload heading {i}.',len(nodes),page=row['page']))
            result=chunk_document(DocumentTree(nodes=nodes),'r14c',counter,UnicodeSentenceSplitter(),
                                  heading_scheme='declared-v1',target_tokens=1,sentence_overlap=0)
            mapping={s.section_id:i-1 for i,s in enumerate(result.sections)}
            observed=[mapping[s.parent_section_id] for s in result.sections[1:]]
            assert observed==parents
            assert len(result.chunks)==len(rows)
            for i,c in enumerate(result.chunks):
                assert c.parent_section_id==result.sections[i+1].section_id
                assert c.text==f'Payload heading {i}.'
            record=dict(book=book,group=fold.get('group'),variant=variant,headings=len(rows),
                        parent_changes=sum(a!=b for a,b in zip(observed,parents)),score=partial_metrics(fold['target'],observed))
            records.append(record)
    base.write(out,dict(api_usd=0,scope='synthetic_payload_transport_not_pdf_accuracy',records=records,
                       chunker_sha256=base.digest(base.ROOT/'src/doc2roadmap/domain/chunking.py')))
    print('Verified',len(records),'tree transports',sum(r['headings'] for r in records),'heading/chunk ownerships')


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    run(base.ROOT/'tmp/a1-v414-r14c/transport.json')
