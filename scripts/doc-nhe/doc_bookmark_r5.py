"""Audit native PDF outlines as an independent structural signal, not gold."""
import argparse
from pathlib import Path
import time
import hoc_tieu_de as base
import pypdfium2 as pdfium
from nhan_khoi_r3 import tokens


def run(out):
    if out.exists():
        raise ValueError('Do not overwrite audit')
    result=[]
    for book in base.manifest(base.ROOT/'tmp/doc-nhe-v414')['books']:
        start=time.perf_counter()
        path=base.allowed_path(base.ROOT/book['pdf'],external=book['split']=='external')
        d=base.read(base.ROOT/'tmp/doc-nhe-v414/datasets'/(book['id']+'.json'))
        items=[]
        with pdfium.PdfDocument(path) as pdf:
            for mark in pdf.get_toc():
                dest=mark.get_dest()
                index=dest.get_index() if dest else None
                page=index+1 if index is not None else None
                title=mark.get_title()
                # Exact ordered lossless-token match only. Do not force a title/page match.
                matches=[i for i,r in enumerate(d['rows']) if r['page']==page and tokens(r['text'])==tokens(title)]
                items.append(dict(title=title,level=mark.level,page=page,view=dest.get_view() if dest else None,matching_rows=matches))
        result.append(dict(book=book['id'],source_sha256=book['pdf_sha256'],bookmarks=items,
                           seconds=time.perf_counter()-start,exact_unique=sum(len(i['matching_rows'])==1 for i in items)))
        print(book['id'],len(items),result[-1]['exact_unique'],flush=True)
    base.write(out,dict(api_usd=0,script_sha256=base.digest(__file__),books=result))


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--out',type=Path,required=True)
    run(cli.parse_args().out)
