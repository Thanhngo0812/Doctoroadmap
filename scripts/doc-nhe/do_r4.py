"""R4 selected candidates: identical grouping/chunker, full PDF-to-tree timings."""
import argparse
from pathlib import Path
import statistics
import sys
import time

import hoc_r4 as r4
import cau_truc_r2 as structure
from do_r2 import verify_nodes, validate_prediction
from danh_gia import heading_score, leaf_score, peak_rss_mb
import so_chunk_doc_nhe as chunks
from doc2roadmap.domain.models import DocumentTree
from doc2roadmap.infrastructure.text import SentencePieceTokenCounter
import joblib
import numpy as np

base = r4.base


def run(out):
    source = base.ROOT / 'tmp/doc-nhe-v414'
    pinned = base.manifest(source)
    protocol = base.read(out / 'protocol.json')
    if protocol['script_sha256'] != base.digest(r4.__file__):
        raise ValueError('Training code changed')
    summary = base.read(out / 'summary.json')
    assert summary['protocol_fingerprint'] == protocol['fingerprint']
    variants = ['M2', *summary['e2e_candidates']]
    stamp = {str(Path(p).resolve().relative_to(base.ROOT)): base.digest(p) for p in
             (__file__, structure.__file__, chunks.__file__, base.ROOT/'scripts/doc-nhe/danh_gia.py',
              base.ROOT/'src/doc2roadmap/domain/chunking.py')}
    counter = SentencePieceTokenCounter(base.ROOT / 'vendor/gemma/tokenizer.model', 'google-gemma-sentencepiece-v1')
    results = []
    for book in pinned['books']:
        key = book['id']
        path = out / 'e2e' / (key + '.json')
        if path.exists():
            result = base.read(path)
            if result['code_sha256'] != stamp or result['protocol_fingerprint'] != protocol['fingerprint'] or list(result['models']) != variants:
                raise ValueError('Evaluator/candidate changed: use fresh output')
            results.append(result)
            continue
        data = base.read(source / 'datasets' / (key + '.json'))
        tree = base.read(base.ROOT / book['tree'])
        settings = {k: v for k, v in book['chunk_config'].items() if k in ('max_tokens', 'max_table_tokens',
                    'hard_cap_tokens', 'target_tokens', 'sentence_overlap', 'result_min_count', 'result_max_body_chars', 'heading_scheme')}
        reference = chunks.chunks_of(DocumentTree.from_dict(tree), key, counter, settings)
        result = dict(id=key, split=book['split'], pages=data['pages'], code_sha256=stamp,
                      protocol_fingerprint=protocol['fingerprint'], models={})
        for variant in variants:
            name = key if book['split'] == 'train' else 'full'
            record_path = (source if variant == 'M2' else out) / 'models' / f"{name}-{'lightgbm' if variant == 'M2' else variant}.json"
            record = base.read(record_path)
            assert key not in record['train_books'] and key in record['heldout']
            assert base.digest(record_path.with_suffix('.joblib')) == record['model_sha256']
            if variant == 'M2':
                flags = validate_prediction(record, key, base.code_fingerprint(), len(data['rows']))
            else:
                assert record['fingerprint'] == protocol['fingerprint']
                flags = np.asarray(record['predictions'][key]['probability']) >= .5
            model = joblib.load(record_path.with_suffix('.joblib'))
            nodes, _ = structure.group_rows(data['rows'], data['figures'], data['pages'], flags)
            verify_nodes(data['rows'], data['figures'], nodes)
            actual_chunks = chunks.chunks_of(chunks.light_tree(nodes), key, counter, settings)
            values = {'heading_strict': heading_score(tree['nodes'], nodes),
                      'leaf_strict': leaf_score(reference, actual_chunks),
                      'chunk_legacy': chunks.compare(reference, actual_chunks),
                      'model_sha256': record['model_sha256'], 'model_bytes': record['model_bytes']}
            pdf = base.allowed_path(base.ROOT / book['pdf'], external=book['split'] == 'external')
            timings = []
            def predictor(rows, body):
                x = base.feature_matrix(rows, body) if variant == 'M2' else r4.feature_matrix(rows, body)
                p = model.predict_proba(x)[:, 1]
                np.testing.assert_allclose(p, record['predictions'][key]['probability'], rtol=0, atol=0)
                return p >= .5
            for _ in range(3):
                started = time.perf_counter()
                fresh, _ = structure.parse(pdf, predictor)
                timings.append(time.perf_counter()-started)
                assert fresh == nodes, 'Fresh PDF-to-tree output differs from cached OOF grouping'
            values.update(timing_seconds=timings, seconds_per_page=statistics.median(timings)/data['pages'])
            result['models'][variant] = values
            print(key, variant, 'strict leaf', values['leaf_strict']['share'], 'seconds/page', values['seconds_per_page'], flush=True)
        result['peak_process_rss_mb'] = peak_rss_mb()
        base.write(path, result)
        results.append(result)
    base.write(out / 'e2e.json', dict(api_usd=0, scope='development; no table recognition/assets integration', books=results))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--out', type=Path, required=True)
    run(cli.parse_args().out)
