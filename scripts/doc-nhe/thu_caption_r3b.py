"""Offline four-page provenance pilot; never writes production artifacts."""
import argparse
from collections import Counter
from pathlib import Path
import os
import time

# Cached models only: this pilot must not download or call a provider.
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
import hoc_tieu_de as learn
from nhan_khoi_r3b import project_captions
from doc2roadmap.infrastructure.parsing.docling_parser import DoclingParser

PAGES = {'d01-04': 138, 'd01-06': 90, 'd01-07': 47, 'd01-14': 199}


def run(out):
    out = out.resolve()
    if not out.is_relative_to(learn.ROOT / 'tmp') or out.exists():
        raise ValueError('Use a new output directory under tmp/')
    books = learn.manifest(learn.ROOT / 'tmp/doc-nhe-v414')['books']
    parser = DoclingParser('pypdfium2')
    results = []
    for book in books:
        if book['id'] not in PAGES:
            continue
        page = PAGES[book['id']]
        start = time.perf_counter()
        doc = parser._get_converter().convert(learn.ROOT / book['pdf'], page_range=(page, page)).document
        if set(doc.pages) != {page}:
            raise ValueError(f'Page numbering changed: {list(doc.pages)} versus {page}')
        parsed = parser.adapt(doc, Path(book['pdf']).name)
        metadata = parsed.tree.parse_stats['caption_provenance']
        data = learn.read(learn.ROOT / 'tmp/doc-nhe-v414/datasets' / (book['id'] + '.json'))
        indexed = [(i, r) for i, r in enumerate(data['rows']) if r['page'] == page]
        projection = project_captions([r for _, r in indexed], metadata)
        for label in projection['labels']:
            label['dataset_row'] = indexed[label['row']][0]
        record = dict(book=book['id'], page=page, source_sha256=book['pdf_sha256'],
                      adapter_version=parser.adapter_version, seconds=time.perf_counter()-start,
                      caption_provenance=metadata, projection=projection,
                      node_counts=dict(Counter(n.node_type for n in parsed.tree.nodes)))
        learn.write(out / (book['id'] + '.json'), record)
        learn.write(out / (book['id'] + '-raw.json'), doc.export_to_dict())
        results.append({k: record[k] for k in ('book', 'page', 'seconds', 'node_counts') } | {
            'caption_records': len(metadata['items']), 'caption_rows': len(projection['labels']),
            'rejected': projection['rejected'], 'unresolved_links': metadata['unresolved_links']})
        print(results[-1], flush=True)
    learn.write(out / 'summary.json', dict(books=results, script_sha256=learn.digest(__file__),
                parser_sha256=learn.digest(learn.ROOT / 'src/doc2roadmap/infrastructure/parsing/docling_parser.py'), api_usd=0))


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--out', type=Path, required=True)
    run(cli.parse_args().out)
