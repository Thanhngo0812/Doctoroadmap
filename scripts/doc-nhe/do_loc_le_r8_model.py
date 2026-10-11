"""R8: compare changed margins with identical grouping/chunker and raw denominators."""
import argparse
from pathlib import Path
import sys

import hoc_loc_le_r8 as experiment
import cau_truc_r2 as structure
from do_r2 import verify_nodes
from danh_gia import heading_score, leaf_score
import so_chunk_doc_nhe as chunks
from doc2roadmap.domain.models import DocumentTree
from doc2roadmap.infrastructure.text import SentencePieceTokenCounter
import numpy as np

base = experiment.base


def run(out, experiment=experiment):
    data, protocol = experiment.load(out)
    counter = SentencePieceTokenCounter(base.ROOT/'vendor/gemma/tokenizer.model', 'google-gemma-sentencepiece-v1')
    stamp = {Path(p).name: base.digest(p) for p in (
        __file__, structure.__file__, experiment.margin.__file__, chunks.__file__,
        base.ROOT/'scripts/doc-nhe/danh_gia.py', base.ROOT/'src/doc2roadmap/domain/chunking.py')}
    results = []
    for key, d in data.items():
        path = out/'e2e'/(key+'.json')
        if path.exists():
            result = base.read(path)
            assert result['code_sha256'] == stamp and result['fingerprint'] == protocol['fingerprint']
            results.append(result)
            continue
        book = d['book']
        record = base.read(out/'models'/((key if book['split']=='train' else 'full')+'.json'))
        assert key not in record['train_books'] and key in record['heldout']
        assert record['fingerprint'] == protocol['fingerprint']
        flags = np.asarray(record['predictions'][key]['probability']) >= .5
        nodes, _ = structure.group_rows(d['rows'], d['figures'], d['pages'], flags,
                                       prepare_rows=experiment.margin.prepare_rows)
        verify_nodes(d['rows'], d['figures'], nodes)
        tree = base.read(base.ROOT/book['tree'])
        settings = {k:v for k,v in book['chunk_config'].items() if k in (
            'max_tokens','max_table_tokens','hard_cap_tokens','target_tokens','sentence_overlap',
            'result_min_count','result_max_body_chars','heading_scheme')}
        reference = chunks.chunks_of(DocumentTree.from_dict(tree), key, counter, settings)
        actual = chunks.chunks_of(chunks.light_tree(nodes), key, counter, settings)
        values = dict(heading_strict=heading_score(tree['nodes'], nodes),
                      leaf_strict=leaf_score(reference, actual), chunk_legacy=chunks.compare(reference, actual))
        old = base.read(base.ROOT/'tmp/a1-v414-r4/e2e'/(key+'.json'))['models']['M2']
        old = {k:old[k] for k in values}
        result = dict(id=key, split=book['split'], code_sha256=stamp, fingerprint=protocol['fingerprint'],
                      recovered=len(d['recovered']), newly_dropped=len(d['newly_dropped']),
                      raw_rows=len(d['raw_y']), old_retained=len(d['old_indexes']), retained=len(d['rows']),
                      full_raw=record['predictions'][key]['full_raw'], old=old, new=values)
        base.write(path, result)
        results.append(result)
        print(key, 'strict leaf', old['leaf_strict']['share'], '->', values['leaf_strict']['share'], flush=True)
    base.write(out/'e2e.json', dict(api_usd=0, cached_evaluation=True, books=results))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--variant', choices=('b','c'), default='b')
    args=parser.parse_args()
    if args.variant=='c':
        import hoc_loc_le_r8c as experiment
    run(args.out, experiment)
