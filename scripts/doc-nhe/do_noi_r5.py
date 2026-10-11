"""Heading continuation E2 ablation: legacy rule, typography rule, pair LightGBM."""
import argparse
from pathlib import Path
import time
import numpy as np
import joblib
import hoc_tieu_de as base
import noi_tieu_de_r5 as pairs
import cau_truc_r2 as structure
from do_r2 import verify_nodes
from danh_gia import heading_score, leaf_score
import so_chunk_doc_nhe as chunks
from doc2roadmap.domain.models import DocumentTree
from doc2roadmap.infrastructure.text import SentencePieceTokenCounter


def run(out, row_variant='E2'):
    source=base.ROOT/'tmp/doc-nhe-v414'
    row_source=source if row_variant=='M2' else base.ROOT/'tmp/a1-v414-r4'
    pinned=base.manifest(source)
    protocol=base.read(out/'protocol.json')
    assert protocol['pair_code_sha256']==base.digest(pairs.__file__)
    counter=SentencePieceTokenCounter(base.ROOT/'vendor/gemma/tokenizer.model','google-gemma-sentencepiece-v1')
    results=[]
    for book in pinned['books']:
        key=book['id']
        target=out/('e2e-m2' if row_variant=='M2' else 'e2e')/(key+'.json')
        if target.exists():
            raise ValueError('Do not overwrite evaluation')
        d=base.read(source/'datasets'/(key+'.json'))
        assert base.digest(source/'datasets'/(key+'.json'))==protocol['inputs'][key]['dataset_sha256']
        name=key if book['split']=='train' else 'full'
        row_record_path=row_source/'models'/(name+('-lightgbm.json' if row_variant=='M2' else '-E2.json'))
        row_record=base.read(row_record_path)
        assert key not in row_record['train_books'] and key in row_record['heldout']
        flags=np.asarray(row_record['predictions'][key]['probability'])>=.5
        record=base.read(out/'models'/(name+'.json'))
        assert record['fingerprint']==protocol['fingerprint'] and key not in record['train_books'] and key in record['heldout']
        model_path=out/'models'/(name+'.joblib')
        assert base.digest(model_path)==record['model_sha256']
        model=joblib.load(model_path)
        started=time.perf_counter()
        probability=model.predict_proba(pairs.matrix(d['rows']))[:,1]
        relation_seconds=time.perf_counter()-started
        np.testing.assert_array_equal(probability,record['predictions'][key]['probability'])
        settings={k:v for k,v in book['chunk_config'].items() if k in ('max_tokens','max_table_tokens','hard_cap_tokens',
                  'target_tokens','sentence_overlap','result_min_count','result_max_body_chars','heading_scheme')}
        tree=base.read(base.ROOT/book['tree'])
        reference=chunks.chunks_of(DocumentTree.from_dict(tree),key,counter,settings)
        original,_=structure.group_rows(d['rows'],d['figures'],d['pages'],flags)
        rules=[False]+[pairs.rule(a,b,typography=True) for a,b in zip(d['rows'],d['rows'][1:])]
        value=dict(id=key,split=book['split'],pages=d['pages'],models={},relation_seconds_only=relation_seconds,
                   evaluator_sha256=base.digest(__file__),row_variant=row_variant,row_record_sha256=base.digest(row_record_path),
                   pair_record_sha256=base.digest(out/'models'/(name+'.json')))
        for variant,joins in [('B0',None),('B1',rules),('B2',probability>=.5)]:
            nodes=original if joins is None else pairs.regroup(d['rows'],original,joins)
            verify_nodes(d['rows'],d['figures'],nodes)
            actual=chunks.chunks_of(chunks.light_tree(nodes),key,counter,settings)
            value['models'][variant]=dict(heading_strict=heading_score(tree['nodes'],nodes),
                                          leaf_strict=leaf_score(reference,actual),chunk_legacy=chunks.compare(reference,actual))
        # Independent replay of the previous evaluator's B0 metrics.
        previous=base.read(base.ROOT/'tmp/a1-v414-r4/e2e'/(key+'.json'))['models'][row_variant]
        for metric in ('heading_strict','leaf_strict','chunk_legacy'):
            assert value['models']['B0'][metric]==previous[metric]
        results.append(value)
        base.write(target,value)
        print(key,{k:round(v['leaf_strict']['share'],4) for k,v in value['models'].items()},flush=True)
    base.write(out/('e2e-m2.json' if row_variant=='M2' else 'e2e.json'),dict(api_usd=0,books=results))


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--out',type=Path,required=True)
    cli.add_argument('--row-variant',choices=('E2','M2'),default='E2')
    args=cli.parse_args()
    run(args.out,args.row_variant)
