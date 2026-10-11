"""Audit all frozen native figures: real PNG bytes, provenance, placement, chunk refs."""
import argparse
from collections import Counter
import hashlib
from pathlib import Path
import time

import hoc_tieu_de as base
import hinh_r6 as images
import cau_truc_r2 as structure
from do_r2 import validate_prediction
from PIL import Image
from doc2roadmap.domain.chunking import chunk_document
from doc2roadmap.infrastructure.text import SentencePieceTokenCounter, UnicodeSentenceSplitter


def run(out):
    out=out.resolve()
    if not out.is_relative_to(base.ROOT/'tmp') or out.exists():
        raise ValueError('Use a new output under tmp/')
    source=base.ROOT/'tmp/doc-nhe-v414'
    pinned=base.manifest(source)
    counter=SentencePieceTokenCounter(base.ROOT/'vendor/gemma/tokenizer.model','google-gemma-sentencepiece-v1')
    results=[]
    for book in pinned['books']:
        key=book['id']
        d=base.read(source/'datasets'/(key+'.json'))
        name=key if book['split']=='train' else 'full'
        record=base.read(source/'models'/(name+'-lightgbm.json'))
        flags=validate_prediction(record,key,base.code_fingerprint(),len(d['rows']))
        original,_=structure.group_rows(d['rows'],d['figures'],d['pages'],flags)
        start=time.perf_counter()
        assets=images.extract_assets(base.allowed_path(base.ROOT/book['pdf'],external=book['split']=='external'),out/'images')
        seconds=time.perf_counter()-start
        nodes,warnings=images.place_figures(original,assets)
        assert [n for n in original if n['node_type']!='figure']==[n for n in nodes if n['node_type']!='figure']
        assert sorted(n['source_figure'] for n in nodes if n['node_type']=='figure')==list(range(len(d['figures'])))
        for a in assets:
            if a['image_id'] is None:
                assert a['error']
                continue
            path=out/'images'/(a['image_id']+'.png')
            assert hashlib.sha256(path.read_bytes()).hexdigest()==a['image_id']
            with Image.open(path) as im:
                assert list(im.size)==a['pixels']
                im.verify()
        tree=images.document_tree(nodes,warnings)
        settings={k:v for k,v in book['chunk_config'].items() if k in ('max_tokens','max_table_tokens','hard_cap_tokens',
                  'target_tokens','sentence_overlap','result_min_count','result_max_body_chars','heading_scheme')}
        chunked=chunk_document(tree,key,counter,UnicodeSentenceSplitter(),**settings)
        refs=[r.image_id for c in chunked.chunks for r in c.image_refs]
        expected=[a['image_id'] for a in assets if a['image_id']]
        assert Counter(refs)==Counter(expected), 'Missing/duplicated/wrong image refs downstream'
        old_tree=base.read(base.ROOT/book['tree'])
        entry=dict(book=key,source_sha256=book['pdf_sha256'],native_figures=len(assets),
                   docling_figures=sum(n['node_type']=='figure' for n in old_tree['nodes']),
                   docling_tables=sum(n['node_type']=='table' for n in old_tree['nodes']),
                   image_refs=len(refs),asset_extract_seconds=seconds,assets=assets,warnings=warnings,
                   placement_counts=dict(Counter(n['placement'] for n in nodes if n['node_type']=='figure')))
        base.write(out/'books'/(key+'.json'),entry)
        base.write(out/'trees'/(key+'.json'),tree.to_dict())
        results.append(entry)
        print(key,{k:entry[k] for k in ('native_figures','docling_figures','docling_tables','image_refs','placement_counts','asset_extract_seconds')},flush=True)
    base.write(out/'summary.json',dict(api_usd=0,script_sha256=base.digest(__file__),
                                      image_code_sha256=base.digest(images.__file__),books=results))


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--out',type=Path,required=True)
    run(cli.parse_args().out)
