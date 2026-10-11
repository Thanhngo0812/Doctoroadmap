"""Offline before/after audit of caption metadata, independent of chunk semantics."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
from doc2roadmap.infrastructure.parsing.docling_parser import DoclingParser
from doc2roadmap.domain.chunking import chunk_document
from doc2roadmap.infrastructure.text import SentencePieceTokenCounter, UnicodeSentenceSplitter
from tests.conftest import load_docling_fixture


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def collect():
    counter = SentencePieceTokenCounter(ROOT / 'vendor/gemma/tokenizer.model', 'google-gemma-sentencepiece-v1')
    result = {'adapter_version': DoclingParser().adapter_version,
              'parser_sha256': hashlib.sha256((ROOT / 'src/doc2roadmap/infrastructure/parsing/docling_parser.py').read_bytes()).hexdigest(), 'books': {}}
    for name in ('nhap-mon-ml', 'xstk-ch3-1', 'baocao-canhan', 'naive-bayes'):
        parsed = DoclingParser().adapt(load_docling_fixture(name), name + ('.docx' if name == 'baocao-canhan' else '.pdf'))
        tree = parsed.tree.to_dict()
        metadata = tree['parse_stats'].pop('caption_provenance', None)
        chunks = chunk_document(parsed.tree, name, counter, UnicodeSentenceSplitter())
        result['books'][name] = {
            'tree_without_caption_metadata_sha256': digest(tree), 'chunks_sha256': digest(asdict(chunks)),
            'image_hashes': {k: hashlib.sha256(v).hexdigest() for k, v in parsed.images.items()},
            'caption_metadata': metadata,
            'caption_metadata_bytes': len(json.dumps(metadata, ensure_ascii=False).encode()) if metadata is not None else 0,
        }
    return result


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--out', type=Path, required=True)
    cli.add_argument('--baseline', type=Path)
    args = cli.parse_args()
    if args.out.exists():
        raise ValueError('Do not overwrite a previous measurement')
    result = collect()
    if args.baseline:
        old = json.loads(args.baseline.read_text(encoding='utf-8'))
        for book, current in result['books'].items():
            for field in ('tree_without_caption_metadata_sha256', 'chunks_sha256', 'image_hashes'):
                assert current[field] == old['books'][book][field], (book, field)
        result['baseline_sha256'] = hashlib.sha256(args.baseline.read_bytes()).hexdigest()
        result['unchanged_payload_verified'] = True
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f"adapter {result['adapter_version']}: {len(result['books'])} fixtures; {args.out}")
