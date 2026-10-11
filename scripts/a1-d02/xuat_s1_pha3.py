"""Frozen R2 native-only inference for phase-4 custodian; never reads labels."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import time

from pha3 import native_route,extract_rows,tree_for,ROOT,write,SETTINGS,verify_freeze
from can_dong import chunk_and_align


def verify_candidate():
    record=json.loads((ROOT/'report/v4-15-pha-3-dong-bang-2026-10-09.json').read_text(encoding='utf-8'))
    if record['candidate']!='R2-grammar-native-only':raise ValueError('Unexpected frozen candidate')
    for name,digest in record['source_files'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:raise ValueError('Candidate source changed: '+name)
    return record['fingerprint']


def infer(pdf,key,out):
    pdf=Path(pdf).resolve();out=Path(out).resolve()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*',key):raise ValueError('Invalid document ID')
    if out.exists():raise ValueError('Use a new output directory; never overwrite artifacts')
    started=time.perf_counter();routing=native_route(pdf)
    if routing['system']=='reject':raise ValueError('PDF không phải PDF gốc; bản quét/không xác định nằm ngoài phạm vi')
    fingerprint=verify_freeze()
    candidate=verify_candidate()
    rows,figures,pages=extract_rows(pdf)
    tree,ids,roles,excluded,bold=tree_for(pdf,key,out,rows,figures,pages,'grammar')
    from doc2roadmap.infrastructure.text import SentencePieceTokenCounter
    from danh_gia import peak_rss_mb
    counter=SentencePieceTokenCounter(ROOT/'vendor/gemma/tokenizer.model','google-gemma-sentencepiece-v1')
    lines=[dict(id=r['d02_id'],trang=r['page'],text=r['text'],bbox=[r['x0'],r['top'],r['x1'],r['bottom']]) for r in rows]
    output,pred=chunk_and_align(tree,lines,key,counter,SETTINGS,source_ids=ids,raw_roles=roles,
        evaluation_excluded=excluded,on_chunked=peak_rss_mb)
    seconds=time.perf_counter()-started-pred['alignment']['seconds']
    pred.update(sach=key,system='S2-R2-native-only',selected='S1-R2',routing=routing,bold=bold,
        pdf_sha256=hashlib.sha256(pdf.read_bytes()).hexdigest(),s1_baseline_fingerprint=fingerprint,candidate_fingerprint=candidate,
        runtime=dict(seconds=seconds,pages=pages,seconds_per_page=seconds/pages,
            peak_rss_mb=pred.pop('pipeline_peak_rss_mb'),source='fresh PDF -> R2 -> actual chunks, excluding evaluation alignment'),
        api_usd=0)
    write(out/'prediction.json',pred);write(out/'tree.json',tree.to_dict())
    write(out/'chunks.json',dict(sections=[s.to_dict() for s in output.sections],chunks=[c.to_dict() for c in output.chunks]))
    return pred


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf',type=Path,required=True);parser.add_argument('--sach',required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();result=infer(args.pdf,args.sach,args.out)
    print(args.sach,result['system'],round(result['runtime']['seconds'],3),flush=True)
