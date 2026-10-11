"""V4-16 phase 1: six development books only, fresh isolated A1+chunk measurements."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
DEVELOPMENT = ('d01-02', 'd01-06', 'd01-07', 'd01-10', 'd01-11', 'd01-15')


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def worker(key, a1, out):
    from doc2roadmap.infrastructure.parsing.nhe_parser import NheParser
    from doc2roadmap.infrastructure.parsing.docling_parser import DoclingParser, PipelineConfig
    from doc2roadmap.infrastructure.parsing.pdf_scope import require_native_pdf
    from doc2roadmap.infrastructure.text import SentencePieceTokenCounter
    from doc2roadmap.domain.chunking import chunk_document
    from doc2roadmap.domain.models import DocumentTree
    from doc2roadmap.domain.sentence_splitter import UnicodeSentenceSplitter
    from doc2roadmap.application.use_cases.ingest_document import tree_text_quality
    sys.path.insert(0, str(ROOT / 'scripts/doc-nhe'))
    from danh_gia import peak_rss_mb
    manifest = json.loads((ROOT / 'tmp/doc-nhe-v414/manifest.json').read_text(encoding='utf-8'))
    book = next(b for b in manifest['books'] if b['id'] == key)
    pdf = ROOT / book['pdf']
    if not pdf.resolve().is_relative_to((ROOT / 'document-data/train').resolve()):
        raise ValueError('Only development training PDFs')
    source = pdf.read_bytes()
    if hashlib.sha256(source).hexdigest() != book['pdf_sha256']:
        raise ValueError('Changed development PDF')
    counter = SentencePieceTokenCounter(ROOT / 'vendor/gemma/tokenizer.model', 'google-gemma-sentencepiece-v1')
    settings = dict(max_tokens=512, max_table_tokens=2048, hard_cap_tokens=6000, target_tokens=256, sentence_overlap=1)
    started = time.perf_counter()
    require_native_pdf(source)
    parser = NheParser() if a1 == 'nhe' else DoclingParser('pypdfium2', pipeline=PipelineConfig(pdf_text_policy='preserve'))
    parsed = parser.parse(source, pdf.name)
    result = chunk_document(parsed.tree, key, counter, UnicodeSentenceSplitter(), **settings)
    seconds = time.perf_counter() - started
    peak = peak_rss_mb()
    # Evaluation and serialization are outside the measured PDF -> real chunk interval.
    old = DocumentTree.from_dict(json.loads((ROOT / f'tmp/a1-v415/phase3g-20261009/grammar/{key}/tree.json').read_text(encoding='utf-8')))
    old_chunks = chunk_document(old, key, counter, UnicodeSentenceSplitter(), **settings)
    nodes = [n.to_dict() for n in parsed.tree.nodes]
    chunks = dict(sections=[s.to_dict() for s in result.sections], chunks=[c.to_dict() for c in result.chunks])
    record = dict(book=key, a1=a1, seconds=seconds, minutes=seconds/60, peak_rss_mb=peak,
                  pdf_sha256=book['pdf_sha256'], node_counts=dict(Counter(n.node_type for n in parsed.tree.nodes)),
                  image_assets=len(parsed.images), text_quality=tree_text_quality(parsed.tree),
                  historical_R2_tree_equal=nodes == [n.to_dict() for n in old.nodes],
                  historical_R2_chunks_equal=chunks == dict(sections=[s.to_dict() for s in old_chunks.sections],
                                                           chunks=[c.to_dict() for c in old_chunks.chunks]), api_usd=0)
    write(out / 'tree.json', parsed.tree.to_dict())
    write(out / 'chunks.json', chunks)
    write(out / 'measurement.json', record)
    print(key, a1, round(seconds, 3), 'seconds', round(peak, 1), 'MB', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--book', choices=DEVELOPMENT)
    parser.add_argument('--a1', choices=('nhe', 'docling'))
    args = parser.parse_args()
    if args.book:
        if not args.a1:
            parser.error('--a1 required with --book')
        worker(args.book, args.a1, args.out)
        return
    records = []
    for a1 in ('nhe', 'docling'):
        for key in DEVELOPMENT:
            folder = args.out / a1 / key
            target = folder / 'measurement.json'
            if not target.exists():
                from chay_pha_2 import machine_cpu
                cpu_before = machine_cpu()
                while cpu_before is not None and cpu_before >= .2:
                    print('WAIT CPU', round(cpu_before * 100, 1), key, a1, flush=True)
                    time.sleep(10)
                    cpu_before = machine_cpu()
                if cpu_before is None:
                    raise RuntimeError('CPU chưa đo được; không nhận lượt này là máy rảnh')
                folder.mkdir(parents=True, exist_ok=True)
                with (folder / 'process.log').open('w', encoding='utf-8') as log:
                    done = subprocess.run([sys.executable, str(Path(__file__).resolve()), '--out', str(folder),
                                           '--book', key, '--a1', a1], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
                if done.returncode:
                    raise RuntimeError(f'{key}/{a1}: exit {done.returncode}; see {folder}/process.log')
                measured = json.loads(target.read_text(encoding='utf-8'))
                measured.update(machine_cpu_before=cpu_before, idle_before=True)
                write(target, measured)
            records.append(json.loads(target.read_text(encoding='utf-8')))
            write(args.out / 'summary.json', dict(measurements=records, complete=len(records)==12, api_usd=0))
            print('DONE', key, a1, flush=True)


if __name__ == '__main__':
    main()
