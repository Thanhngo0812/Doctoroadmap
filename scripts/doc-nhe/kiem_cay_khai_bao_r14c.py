"""Snapshot/check complete existing chunk results before opt-in hierarchy support."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
import hoc_tieu_de as base
from doc2roadmap.domain.models import DocumentTree
from doc2roadmap.domain.chunking import chunk_document
from doc2roadmap.infrastructure.text import SentencePieceTokenCounter
from doc2roadmap.domain.sentence_splitter import UnicodeSentenceSplitter


def run(out,check):
    assert not out.exists()
    counter=SentencePieceTokenCounter(base.ROOT/'vendor/gemma/tokenizer.model','google-gemma-sentencepiece-v1')
    results=[]
    for book in base.manifest(base.ROOT/'tmp/doc-nhe-v414')['books']:
        tree=DocumentTree.from_dict(base.read(base.ROOT/book['tree']))
        settings={k:v for k,v in book['chunk_config'].items() if k in (
            'max_tokens','max_table_tokens','hard_cap_tokens','target_tokens','sentence_overlap',
            'result_min_count','result_max_body_chars','heading_scheme')}
        chunked=chunk_document(tree,book['id'],counter,UnicodeSentenceSplitter(),**settings)
        serialized=json.dumps(asdict(chunked),ensure_ascii=False,sort_keys=True).encode('utf-8')
        results.append(dict(id=book['id'],config=settings,sha256=hashlib.sha256(serialized).hexdigest(),
                            chunks=len(chunked.chunks),sections=len(chunked.sections)))
        print(book['id'],len(chunked.chunks),flush=True)
    if check: assert results==base.read(check)['books'], 'Existing chunk result changed'
    base.write(out,dict(api_usd=0,books=results,checked_against=str(check) if check else None,
                       chunker_sha256=base.digest(base.ROOT/'src/doc2roadmap/domain/chunking.py')))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--out',type=Path,required=True)
    cli.add_argument('--check',type=Path)
    a=cli.parse_args(); run(a.out,a.check)
