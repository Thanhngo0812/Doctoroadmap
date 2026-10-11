"""Read-only conservative complex-page audit, no gold or Docling labels in gate."""
import argparse
from collections import Counter, defaultdict
from contextlib import closing
from pathlib import Path
import re
import time
import hoc_tieu_de as base
import pypdfium2 as pdfium
import pypdfium2.raw as raw


def reasons(rows,objects):
    result=[]
    if objects.get('image',0): result.append('raster')
    if objects.get('path',0): result.append('vector')
    if not rows: result.append('no_native_text')
    if any(r['math']>=.2 for r in rows): result.append('math_font')
    if any(len(re.findall(r'\d+',r['text']))>=3 or sum(c.isdigit() for c in r['text'])/max(len(r['text']),1)>=.3 for r in rows):
        result.append('numeric_dense')
    return result


def run(out, depth=2):
    if out.exists(): raise ValueError('Do not overwrite measurement')
    results=[]
    for book in base.manifest(base.ROOT/'tmp/doc-nhe-v414')['books']:
        key=book['id']
        d=base.read(base.ROOT/'tmp/doc-nhe-v414/datasets'/(key+'.json'))
        by_page=defaultdict(list)
        for r in d['rows']: by_page[r['page']].append(r)
        pages=[]
        start=time.perf_counter()
        with pdfium.PdfDocument(base.allowed_path(base.ROOT/book['pdf'],external=book['split']=='external')) as pdf:
            assert len(pdf)==d['pages']
            for index in range(len(pdf)):
                with closing(pdf[index]) as page:
                    types=Counter(obj.type for obj in page.get_objects(max_depth=depth))
                    counts=dict(image=types[raw.FPDF_PAGEOBJ_IMAGE],path=types[raw.FPDF_PAGEOBJ_PATH],text=types[raw.FPDF_PAGEOBJ_TEXT])
                    pages.append(dict(page=index+1,objects=counts,reasons=reasons(by_page[index+1],counts)))
        # Labels only after gate decisions; never fed to reasons().
        tree=base.read(base.ROOT/book['tree'])
        known={n['page'] for n in tree['nodes'] if n['node_type'] in ('figure','table') and n.get('page') is not None}
        sent={p['page'] for p in pages if p['reasons']}
        entry=dict(book=key,pages=len(pages),fallback=len(sent),fallback_share=len(sent)/len(pages),
                   known_complex_pages=len(known),covered_complex_pages=len(known&sent),missed_known_pages=sorted(known-sent),
                   page_details=pages,object_scan_seconds_only=time.perf_counter()-start,
                   source_sha256=book['pdf_sha256'],tree_sha256=book['tree_sha256'])
        results.append(entry)
        print({k:v for k,v in entry.items() if k not in ('page_details','source_sha256','tree_sha256')},flush=True)
    base.write(out,dict(api_usd=0,object_depth=depth,script_sha256=base.digest(__file__),books=results))


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--out',type=Path,required=True)
    cli.add_argument('--depth',type=int,choices=(2,15),default=2)
    args=cli.parse_args()
    run(args.out,args.depth)
