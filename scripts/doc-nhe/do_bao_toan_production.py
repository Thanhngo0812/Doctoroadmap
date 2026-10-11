"""Replay cached development documents through both production text policies.

No PDF conversion, model calls, production writes, or blind-test access.
Run from repository root with the production Python environment.
"""
import hashlib
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT))

from doc2roadmap.domain.chunking import chunk_document
from doc2roadmap.domain.normalization import normalize_text
from doc2roadmap.infrastructure.parsing.docling_parser import DoclingParser, PipelineConfig
from doc2roadmap.infrastructure.text import SentencePieceTokenCounter, UnicodeSentenceSplitter
from tests.conftest import load_docling_fixture

SOURCES = {'nhap-mon-ml': '.pdf', 'xstk-ch3-1': '.pdf', 'baocao-canhan': '.docx', 'naive-bayes': '.pdf'}


def audit():
    counter = SentencePieceTokenCounter(ROOT / 'vendor/gemma/tokenizer.model', 'google-gemma-sentencepiece-v1')
    records = {}
    for name, extension in SOURCES.items():
        source = load_docling_fixture(name)
        parsers = [DoclingParser(pipeline=PipelineConfig(pdf_text_policy=p)) for p in ('legacy', 'preserve')]
        parsed = [p.adapt(source, name + extension) for p in parsers]
        old, new = parsed
        assert old.images == new.images
        assert len(old.tree.nodes) == len(new.tree.nodes)
        changes = Counter()
        samples = []
        # The text policy must not alter layout, hierarchy, geometry or image provenance.
        for before, after in zip(old.tree.nodes, new.tree.nodes, strict=True):
            for field in ('node_type', 'reading_order', 'level', 'page', 'bbox', 'image_id', 'tree_depth'):
                assert getattr(before, field) == getattr(after, field), (name, field)
            for field in ('text', 'raw_text', 'context_prefix', 'table_rows'):
                if getattr(before, field) != getattr(after, field):
                    changes[field] += 1
                    if len(samples) < 8:
                        samples.append({'page': after.page, 'field': field,
                                        'before': getattr(before, field), 'after': getattr(after, field)})
            if after.formula_id:
                assert after.formula_id == hashlib.sha256(normalize_text(after.raw_text).encode()).hexdigest()
            if after.table_id:
                assert after.table_id == DoclingParser._table_id(after.table_rows)
        metrics = {}
        for policy, tree in zip(('legacy', 'preserve'), parsed, strict=True):
            result = chunk_document(tree.tree, name, counter, UnicodeSentenceSplitter())
            assert all(result.normalized_full_text[c.char_start:c.char_end] == c.text for c in result.chunks)
            assert len({c.chunk_id for c in result.chunks}) == len(result.chunks)
            for kind in ('image', 'table', 'formula'):
                available = {getattr(n, kind + '_id') for n in tree.tree.nodes}
                assert all(getattr(ref, kind + '_id') in available for c in result.chunks for ref in getattr(c, kind + '_refs'))
            metrics[policy] = {
                'nodes': len(tree.tree.nodes), 'sections': len(result.sections), 'chunks': len(result.chunks),
                'letters': sum(c.isalpha() for c in result.normalized_full_text),
                'refs': {k: sum(len(getattr(c, k + '_refs')) for c in result.chunks) for k in ('image', 'table', 'formula')},
                'chunk_ids_sha256': hashlib.sha256('\n'.join(c.chunk_id for c in result.chunks).encode()).hexdigest(),
                'warnings': dict(Counter(w.partition(':')[0] for w in result.structure_warnings)),
            }
        for field in ('sections', 'chunks', 'refs', 'warnings'):
            assert metrics['legacy'][field] == metrics['preserve'][field], (name, field)
        records[name] = {'metrics': metrics, 'changed_node_fields': dict(changes), 'examples': samples}
    return {'scope': 'four cached development fixtures, not a blinded quality benchmark',
            'source_hashes': {str(p): hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in
                              ['src/doc2roadmap/infrastructure/parsing/docling_parser.py',
                               'scripts/doc-nhe/do_bao_toan_production.py']}, 'books': records}


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--out', type=Path)
    args = cli.parse_args()
    payload = json.dumps(audit(), ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload + '\n', encoding='utf-8')
        print(args.out)
    else:
        print(payload)
