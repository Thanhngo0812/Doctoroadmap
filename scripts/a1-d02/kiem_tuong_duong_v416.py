"""Compare product R2 with frozen research R2 using the same full models, no labels."""
from collections import Counter
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/a1-d02'))
sys.path.insert(0, str(ROOT / 'scripts/doc-nhe'))
from pha3 import tree_for, verify_freeze
from doc2roadmap.domain.chunking import chunk_document
from doc2roadmap.domain.models import DocumentTree
from doc2roadmap.domain.sentence_splitter import UnicodeSentenceSplitter
from doc2roadmap.infrastructure.text import SentencePieceTokenCounter
from do_san_pham_v416 import DEVELOPMENT, write


def main(out):
    verify_freeze()
    counter = SentencePieceTokenCounter(ROOT / 'vendor/gemma/tokenizer.model', 'google-gemma-sentencepiece-v1')
    settings = dict(max_tokens=512, max_table_tokens=2048, hard_cap_tokens=6000, target_tokens=256, sentence_overlap=1)
    manifest = json.loads((ROOT / 'tmp/doc-nhe-v414/manifest.json').read_text(encoding='utf-8'))
    records = []
    for key in DEVELOPMENT:
        book = next(b for b in manifest['books'] if b['id'] == key)
        raw = json.loads((ROOT / f'tmp/a1-v415/phase3g-20261009/rows/{key}.json').read_text(encoding='utf-8'))
        # A synthetic key without an existing LOBO model forces research R2 to use full.
        folder = ROOT / f'tmp/a1-v415/phase3g-20261009/{key}'
        if not (folder / 'assets.json').is_file():
            raise ValueError('Missing frozen assets; do not overwrite research outputs')
        reference, _, _, _, _ = tree_for(ROOT / book['pdf'], 'v416-full-reference', folder,
                                         raw['rows'], raw['figures'], raw['pages'], 'grammar')
        product = DocumentTree.from_dict(json.loads((out / f'nhe/{key}/tree.json').read_text(encoding='utf-8')))
        actual = chunk_document(product, key, counter, UnicodeSentenceSplitter(), **settings)
        expected = chunk_document(reference, key, counter, UnicodeSentenceSplitter(), **settings)
        record = dict(book=key, model='full', tree_equal=[n.to_dict() for n in product.nodes] == [n.to_dict() for n in reference.nodes],
                      sections_equal=[s.to_dict() for s in actual.sections] == [s.to_dict() for s in expected.sections],
                      chunks_equal=[c.to_dict() for c in actual.chunks] == [c.to_dict() for c in expected.chunks],
                      reference_nodes=dict(Counter(n.node_type for n in reference.nodes)))
        records.append(record)
        write(out / 'full-equivalence.json', dict(books=records, complete=len(records)==6,
              all_equal=all(r['tree_equal'] and r['sections_equal'] and r['chunks_equal'] for r in records)))
        print(record, flush=True)
    if not all(r['tree_equal'] and r['sections_equal'] and r['chunks_equal'] for r in records):
        raise AssertionError('R2 full equivalence failed; inspect full-equivalence.json')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    main(parser.parse_args().out)
