"""Research runner S0/S1/S2, fresh PDF -> real chunk; no production integration."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT/'.venv/Lib/site-packages'))
sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'scripts/doc-nhe'))
from xuat_phieu import light,page_rows,write
from dinh_tuyen import route
from can_dong import chunk_and_align
from kiem_nhan_d02 import read_jsonl

SETTINGS=dict(max_tokens=512,max_table_tokens=2048,hard_cap_tokens=6000,target_tokens=256,sentence_overlap=1)
FREEZE=ROOT/'report/v4-15-s1-dong-bang-2026-10-08.json'


def verify_freeze():
    record=json.loads(FREEZE.read_text(encoding='utf-8'))
    for path,digest in record['files'].items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=digest:
            raise ValueError('Frozen S1 input changed: '+path)
    return record['fingerprint']


def s1(path,key,folder):
    import joblib
    import hoc_tieu_de as features
    import noi_tieu_de_r5 as pairs
    import cau_truc_r2 as grouping
    import loc_bien_r13 as margins
    import caption_hinh_r18 as captions
    import noi_chuong_r20 as chapters
    import chu_trong_hinh_r21 as diagram
    import ma_bai_r22 as lesson
    import ten_chuong_math_r24 as inline
    import vi_tri_hinh_r25 as placement
    import hinh_r6 as images
    verify_freeze()
    fold=key if f'tmp/doc-nhe-v414/models/{key}-lightgbm.joblib' in json.loads(FREEZE.read_text())['files'] else 'full'
    row_model=joblib.load(ROOT/f'tmp/doc-nhe-v414/models/{fold}-lightgbm.joblib')
    pair_model=joblib.load(ROOT/f'tmp/a1-v414-r5/models/{fold}.joblib')
    rows,figures,count=light.extract_rows(path)
    ordinal={}
    for row in rows:
        page=row['page'];ordinal[page]=ordinal.get(page,0)+1;row['d02_id']=f'p{page:04}-l{ordinal[page]:03}'
    retained,body=margins.prepare_rows(rows)
    flags=row_model.predict_proba(features.feature_matrix(retained,body))[:,1]>=.5
    flags[captions.candidates(retained,figures)]=False
    joins=pair_model.predict_proba(pairs.matrix(retained))[:,1]>=.5
    nodes,_=grouping.group_rows(rows,figures,count,flags,prepare_rows=margins.prepare_rows)
    nodes=pairs.regroup(retained,nodes,joins)
    nodes,_=chapters.combine(retained,nodes);nodes,_=diagram.correct(retained,nodes,body)
    nodes,_=lesson.separate(retained,nodes);nodes,_=inline.combine(retained,nodes,body)
    assets=images.extract_assets(path,folder/'images');nodes,warnings=placement.place(retained,nodes,assets)
    tree=images.document_tree(nodes,warnings)
    source_ids={i:[retained[j]['d02_id'] for j in n['source_rows']] for i,n in enumerate(nodes)}
    raw_roles={i:n['node_type'] for i,n in enumerate(nodes)}
    excluded=[r['d02_id'] for r in rows if r['d02_id'] not in {n['d02_id'] for n in retained}]
    return tree,source_ids,raw_roles,excluded,fold


def run(path,key,system,folder,lines=None):
    path=Path(path).resolve();folder=Path(folder)
    if (ROOT/'document-data/test').resolve() in path.parents:raise ValueError('Không mở document-data/test')
    # Canonical rows are an evaluation input, prepared outside the measured pipeline.
    if lines is None:
        from contextlib import closing
        lines=[]
        with light.pdfium.PdfDocument(path) as pdf:
            for i in range(min(len(pdf),300)):
                with closing(pdf[i]) as page:lines.extend(page_rows(page,i+1))
    source_ids=roles=None;excluded=[];routing=None;fold=None
    started=time.perf_counter()
    selected=system
    if system=='S2':routing=route(path);selected=routing['system']
    if selected=='S1':tree,source_ids,roles,excluded,fold=s1(path,key,folder)
    else:
        from doc2roadmap.infrastructure.parsing.docling_parser import DoclingParser,PipelineConfig
        tree=DoclingParser('pypdfium2',pipeline=PipelineConfig(pdf_text_policy='preserve')).parse(path.read_bytes(),path.name).tree
    from doc2roadmap.infrastructure.text import SentencePieceTokenCounter
    from danh_gia import peak_rss_mb
    counter=SentencePieceTokenCounter(ROOT/'vendor/gemma/tokenizer.model','google-gemma-sentencepiece-v1')
    output,prediction=chunk_and_align(tree,lines,key,counter,SETTINGS,source_ids=source_ids,raw_roles=roles,
                                     evaluation_excluded=excluded,on_chunked=peak_rss_mb)
    seconds=time.perf_counter()-started-prediction['alignment']['seconds']
    prediction.update(sach=key,system=system,selected=selected,settings=SETTINGS,
        pdf_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),s1_fingerprint=verify_freeze(),model_fold=fold,
        runtime=dict(seconds=seconds,pages=tree.parse_stats.get('pages') or (len(routing['pages']) if routing else None),
                     peak_rss_mb=prediction.pop('pipeline_peak_rss_mb'),source='fresh PDF to real chunks; includes imports/model load and routing; RAM sampled before alignment, canonical evaluation rows already loaded'),
        routing=routing)
    # Page count from the PDF rather than relying on optional adapter telemetry.
    with light.pdfium.PdfDocument(path) as pdf:prediction['runtime']['pages']=len(pdf)
    prediction['runtime']['seconds_per_page']=seconds/prediction['runtime']['pages']
    write(folder/'prediction.json',prediction);write(folder/'tree.json',tree.to_dict())
    write(folder/'chunks.json',dict(sections=[s.to_dict() for s in output.sections],chunks=[c.to_dict() for c in output.chunks]))
    print(key,system,'DONE',round(seconds,3),len(output.chunks),flush=True)
    return prediction


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf',type=Path,required=True);parser.add_argument('--sach',required=True)
    parser.add_argument('--system',choices=['S0','S1','S2'],required=True);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--dong',type=Path)
    args=parser.parse_args()
    if args.out.exists():parser.error('Dùng thư mục đầu ra mới cho mỗi lần đo')
    run(args.pdf,args.sach,args.system,args.out,read_jsonl(args.dong) if args.dong else None)
