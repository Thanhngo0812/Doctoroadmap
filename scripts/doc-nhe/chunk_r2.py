"""A1 R2 downstream ablation; same chunker/settings for reference and all arms."""
import argparse
from pathlib import Path
import time
import hoc_tieu_de as learn
import cau_truc_r2 as r2
import do_r2 as replay
import so_chunk_doc_nhe as chunk_eval
from danh_gia import leaf_score
from doc2roadmap.domain.models import DocumentNode, DocumentTree
from doc2roadmap.infrastructure.text import SentencePieceTokenCounter


def run(source, out):
    if out.resolve() == source.resolve() or out.resolve().is_relative_to(source.resolve()):
        raise ValueError('Do not overwrite v1')
    manifest = learn.manifest(source)
    result = {'api_usd': 0, 'scope': 'development; chunk conversion unchanged from v1, not asset integration',
              'manifest_sha256': learn.digest(source/'manifest.json'),
              'code_sha256': {str(path.relative_to(learn.ROOT)): learn.digest(path) for path in [
                  Path(__file__).resolve(), Path(r2.__file__).resolve(), Path(replay.__file__).resolve(),
                  Path(chunk_eval.__file__).resolve(), learn.ROOT/'scripts/doc-nhe/danh_gia.py',
                  learn.ROOT/'src/doc2roadmap/domain/chunking.py']}, 'books': []}
    counter = SentencePieceTokenCounter(learn.ROOT/'vendor/gemma/tokenizer.model', 'google-gemma-sentencepiece-v1')
    began = time.perf_counter()
    for book in manifest['books']:
        key = book['id']
        start = time.perf_counter()
        data = learn.read(source/'datasets'/f'{key}.json')
        if data['fingerprint'] != learn.code_fingerprint():
            raise ValueError('Frozen dataset changed')
        name = key if book['split'] == 'train' else 'full'
        path = source/'models'/f'{name}-lightgbm.json'
        record = learn.read(path)
        if learn.digest(path.with_suffix('.joblib')) != record['model_sha256']:
            raise ValueError('Model changed')
        flags = replay.validate_prediction(record, key, data['fingerprint'], len(data['rows']))
        tree = DocumentTree.from_dict(learn.read(learn.ROOT/book['tree']))
        settings = {k: v for k, v in book['chunk_config'].items() if k in ('max_tokens', 'max_table_tokens',
                    'hard_cap_tokens', 'target_tokens', 'sentence_overlap', 'result_min_count', 'result_max_body_chars', 'heading_scheme')}
        reference = chunk_eval.chunks_of(tree, key, counter, settings)
        entry = {'id': key, 'split': book['split'], 'settings': settings, 'models': {}}
        for kind in ('v1_m2', 'text', 'protected'):
            if kind == 'v1_m2':
                nodes, _ = r2.baseline.group_rows(data['rows'], data['figures'], data['pages'], flags)
            else:
                nodes, _ = r2.group_rows(data['rows'], data['figures'], data['pages'], flags, protect_types=kind == 'protected')
                replay.verify_nodes(data['rows'], data['figures'], nodes)
            # Exactly the legacy conversion for all arms: do not silently add bbox/asset behavior to one arm.
            chunks = chunk_eval.chunks_of(chunk_eval.light_tree(nodes), key, counter, settings)
            entry['models'][kind] = {'strict_leaf': leaf_score(reference, chunks),
                                      'legacy': chunk_eval.compare(reference, chunks)}
        entry['seconds'] = time.perf_counter()-start
        result['books'].append(entry)
        learn.write(out/'chunk-books'/f'{key}.json', entry)
        print(f"{key} chunk {len(result['books'])}/19: {entry['seconds']:.1f}s", flush=True)
    result['seconds'] = time.perf_counter()-began
    learn.write(out/'chunks.json', result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--source', type=Path, default=Path('tmp/doc-nhe-v414'))
    parser.add_argument('--out', type=Path, default=Path('tmp/a1-v414-r2/canonical'))
    args = parser.parse_args()
    run(args.source, args.out)
