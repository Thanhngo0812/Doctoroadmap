"""Audit excluded native rows separately from retained-row preservation claims."""
import argparse
from collections import Counter
from pathlib import Path
import time
import hoc_tieu_de as base
from nhan_khoi_r3 import align_rows


def run(out):
    if out.exists(): raise ValueError('Use a new output directory')
    results=[]
    source=base.ROOT/'tmp/doc-nhe-v414'
    for book in base.manifest(source)['books']:
        key=book['id']
        start=time.perf_counter()
        raw,figures,pages=base.light.extract_rows(base.allowed_path(base.ROOT/book['pdf'],external=book['split']=='external'))
        kept,body=base.light.prepare_rows(raw)
        frozen=base.read(source/'datasets'/(key+'.json'))
        assert kept==frozen['rows'] and figures==[{**f,'bbox':tuple(f['bbox'])} for f in frozen['figures']] and pages==frozen['pages']
        retained_ids={id(r) for r in kept}
        dropped=[(i,r) for i,r in enumerate(raw) if id(r) not in retained_ids]
        tree=base.read(base.ROOT/book['tree'])
        matches=align_rows([r for _,r in dropped],tree['nodes'])
        entries=[dict(raw_index=i,row=r,alignment=a) for (i,r),a in zip(dropped,matches,strict=True)]
        counts=dict(Counter(a['label'] for a in matches))
        detail=dict(book=key,source_sha256=book['pdf_sha256'],tree_sha256=book['tree_sha256'],
                    raw_rows=len(raw),retained_rows=len(kept),dropped_rows=len(dropped),aligned_counts=counts,
                    seconds=time.perf_counter()-start,entries=entries)
        base.write(out/'books'/(key+'.json'),detail)
        results.append({k:v for k,v in detail.items() if k!='entries'})
        print(key,len(dropped),counts,flush=True)
    base.write(out/'summary.json',dict(api_usd=0,script_sha256=base.digest(__file__),
                                      baseline_fingerprint=base.code_fingerprint(),books=results))


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--out',type=Path,required=True)
    run(cli.parse_args().out)
