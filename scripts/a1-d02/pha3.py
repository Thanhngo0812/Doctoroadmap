"""Controlled A1 development; keeps the R25 reader and baseline artifacts unchanged."""
from collections import Counter
from pathlib import Path
import argparse
import hashlib
import json
import re
import statistics
import sys
import time
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts/a1-d02'))
from xuat_phieu import light,ROOT,DEVELOPMENT,write
from dinh_tuyen import route
from chay_he import verify_freeze,SETTINGS
from kiem_nhan_d02 import read_jsonl,load_labels
from cham_d02 import score

ARTICLE=re.compile(r'^Điều\s+\d+[.]\s+\S',re.I)
CLAUSE=re.compile(r'^(?:\d+[.]\s+|[a-zđ][)]\s+)',re.I)
MAJOR=re.compile(r'^(?:phần|chương|bài|mục)\s+[\dIVXLC]+\b',re.I)
DECIMAL=re.compile(r'^(\d+(?:\.\d+)+)[.]?\s+\S')


def normalize_bold(rows):
    counts=Counter()
    # Body-like rows estimate the dominant weight, not headings or named bold fonts.
    body=[r for r in rows if r['font_bold']<.6 and len(r['text'].split())>=5]
    for r in body or rows:counts[r['weight']]+=r['chars']
    base=counts.most_common(1)[0][0] if counts else 0
    inflated=base>=600 and sum(r['chars']*r['bold'] for r in rows)>=.8*sum(r['chars'] for r in rows)
    result=[dict(r,bold=(r['font_bold']>=.6 or r['weight']>=base+100) if inflated else r['bold']) for r in rows]
    return result,dict(base_weight=base,inflated=inflated,changed=sum(a['bold']!=b['bold'] for a,b in zip(rows,result)))


def extract_rows(path):
    original=light.describe
    def describe(chars,*args):
        row=original(chars,*args)
        if row:
            visible=[c for c in chars if c.ch.strip()]
            weights=sorted(c.weight for c in visible)
            row.update(weight=weights[len(weights)//2],font_bold=sum(bool(light.BOLD_FONT.search(c.font)) for c in visible)/len(visible))
        return row
    with patch.object(light,'describe',describe):
        rows,figures,pages=light.extract_rows(path)
    ordinals=Counter()
    for r in rows:
        ordinals[r['page']]+=1;r['d02_id']=f"p{r['page']:04}-l{ordinals[r['page']]:03}"
    return rows,figures,pages


def grammar_flags(rows,flags):
    result=[];article=False
    for r,flag in zip(rows,flags):
        text=r['text'].strip()
        if MAJOR.match(text):article=False
        if ARTICLE.match(text) and len(text.split())<=40:
            flag=True;article=True
        elif article and CLAUSE.match(text) and not DECIMAL.match(text):flag=False
        result.append(bool(flag))
    return result


def mask_captions(flags,indexes):
    import numpy as np
    flags=np.array(flags,dtype=bool,copy=True)
    flags[indexes]=False
    return flags


def native_route(path):
    result=route(path)
    return dict(result,system='S1' if result['pdf_type']=='native' else 'reject')


def numbering_features(rows):
    import numpy as np
    return np.asarray([[bool(ARTICLE.match(r['text'])),bool(MAJOR.match(r['text'])),
        bool(DECIMAL.match(r['text'])),bool(CLAUSE.match(r['text'])),r['text'].endswith(':')]
        for r in rows],dtype=np.float32).reshape((-1,5))


def hierarchy(nodes):
    """Use explicit numbering depth; unnumbered headings retain inherited levels."""
    part=False;chapter=0;major=0
    for n in nodes:
        if n['node_type']!='section_header':continue
        text=n['text'];match=re.match(r'^(phần|chương|bài|mục)\s+[\dIVXLC]+\b',text,re.I)
        if match:
            word=match[1].casefold()
            if word=='phần':part=True;chapter=0;level=1
            elif word in {'chương','bài'}:chapter=2 if part else 1;level=chapter
            else:level=max(chapter+1,1)
            n['level']=level;major=level
        elif ARTICLE.match(text):
            n['level']=min(major+1,6)
        elif DECIMAL.match(text):
            n['level']=min(max(chapter+1,len(DECIMAL.match(text)[1].split('.'))+int(part)),6)
    return nodes


def tree_for(path,key,folder,rows,figures,pages,variant,model=None):
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
    import numpy as np
    fold=key if (ROOT/f'tmp/doc-nhe-v414/models/{key}-lightgbm.joblib').exists() else 'full'
    row_model=model or joblib.load(ROOT/f'tmp/doc-nhe-v414/models/{fold}-lightgbm.joblib')
    pair_model=joblib.load(ROOT/f'tmp/a1-v414-r5/models/{fold}.joblib')
    rows=[dict(r) for r in rows]
    bold_info=None
    if variant!='baseline':rows,bold_info=normalize_bold(rows)
    retained,body=margins.prepare_rows(rows)
    matrix=features.feature_matrix(retained,body)
    if model is not None:matrix=np.concatenate((matrix,numbering_features(retained)),axis=1)
    flags=row_model.predict_proba(matrix)[:,1]>=.5
    if variant in {'grammar','hierarchy'}:flags=grammar_flags(retained,flags)
    flags=mask_captions(flags,captions.candidates(retained,figures))
    joins=pair_model.predict_proba(pairs.matrix(retained))[:,1]>=.5
    nodes,_=grouping.group_rows(rows,figures,pages,flags,prepare_rows=margins.prepare_rows)
    nodes=pairs.regroup(retained,nodes,joins)
    nodes,_=chapters.combine(retained,nodes);nodes,_=diagram.correct(retained,nodes,body)
    nodes,_=lesson.separate(retained,nodes);nodes,_=inline.combine(retained,nodes,body)
    if variant=='hierarchy':nodes=hierarchy(nodes)
    assets_file=folder/'assets.json'
    if assets_file.exists():assets=json.loads(assets_file.read_text(encoding='utf-8'))
    else:assets=images.extract_assets(path,folder/'images');write(assets_file,assets)
    nodes,warnings=placement.place(retained,nodes,assets)
    tree=images.document_tree(nodes,warnings)
    source_ids={i:[retained[j]['d02_id'] for j in n['source_rows']] for i,n in enumerate(nodes)}
    roles={i:n['node_type'] for i,n in enumerate(nodes)}
    kept={r['d02_id'] for r in retained};excluded=[r['d02_id'] for r in rows if r['d02_id'] not in kept]
    return tree,source_ids,roles,excluded,bold_info


def train_independent(data,heldout,folder):
    import joblib
    import numpy as np
    from lightgbm import LGBMClassifier
    names=sorted(set(data)-{heldout});path=folder/f'{heldout}.joblib'
    if path.exists():return joblib.load(path)
    model=LGBMClassifier(n_estimators=300,num_leaves=15,learning_rate=.05,min_child_samples=30,
        class_weight='balanced',random_state=42,n_jobs=2,verbosity=-1,deterministic=True,force_col_wise=True)
    model.fit(np.concatenate([data[k][0] for k in names]),np.concatenate([data[k][1] for k in names]))
    path.parent.mkdir(parents=True,exist_ok=True);joblib.dump(model,path)
    write(path.with_suffix('.json'),dict(train_books=names,heldout=heldout,rows=sum(len(data[k][1]) for k in names),
        model_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),features=78,threshold=.5,seed=42))
    return model


def run(out,variant):
    import numpy as np
    import hoc_tieu_de as features
    import loc_bien_r13 as margins
    from can_dong import chunk_and_align
    from danh_gia import heading_score,leaf_score
    from doc2roadmap.domain.models import DocumentTree
    from doc2roadmap.domain.chunking import chunk_document
    from doc2roadmap.domain.sentence_splitter import UnicodeSentenceSplitter
    from doc2roadmap.infrastructure.text import SentencePieceTokenCounter
    fingerprint=verify_freeze()
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((ROOT/'tmp/doc-nhe-v414/manifest.json').read_text(encoding='utf-8'))
    # Exact allowlist from the already pinned old-development manifest; never enumerate held-out PDFs.
    books=manifest['books'];prepared={};training={}
    signatures={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in Path(__file__).parent.glob('*.py')}
    for b in books:
        key=b['id'];path=features.allowed_path(ROOT/b['pdf'],external=b['split']=='external')
        if hashlib.sha256(path.read_bytes()).hexdigest()!=b['pdf_sha256']:raise ValueError('Changed PDF '+key)
        cache=out/'rows'/f'{key}.json'
        if cache.exists():record=json.loads(cache.read_text(encoding='utf-8'))
        else:
            rows,figures,pages=extract_rows(path);record=dict(rows=rows,figures=figures,pages=pages);write(cache,record)
        signatures[str(cache.resolve())]=hashlib.sha256(cache.read_bytes()).hexdigest()
        signatures[str(path.resolve())]=b['pdf_sha256']
        rows=record['rows'];prepared[key]=(path,rows,record['figures'],record['pages'])
        if key in DEVELOPMENT:
            folder=ROOT/'artifacts/a1-d02/development';heads,_=load_labels(key,folder,review=True)
            ids={x for h in heads for x in h['dong']};normalized,_=normalize_bold(rows);retained,body=margins.prepare_rows(normalized)
            training[key]=(np.concatenate((features.feature_matrix(retained,body),numbering_features(retained)),axis=1),
                np.asarray([r['d02_id'] in ids for r in retained],dtype=np.int8))
            for part in ('dong','cay-muc','trang-mau','duyet'):
                p=folder/part/f'{key}.jsonl'
                if p.exists():signatures[str(p.resolve())]=hashlib.sha256(p.read_bytes()).hexdigest()
    pin=out/'inputs.json';record=dict(s1=fingerprint,files=signatures)
    if pin.exists() and json.loads(pin.read_text(encoding='utf-8'))!=record:raise ValueError('Phase3 input changed; use new output')
    write(pin,record)
    counter=SentencePieceTokenCounter(ROOT/'vendor/gemma/tokenizer.model','google-gemma-sentencepiece-v1')
    results=[]
    for b in books:
        key=b['id'];target=out/variant/key;result_path=target/'result.json'
        if result_path.exists():results.append(json.loads(result_path.read_text(encoding='utf-8')));continue
        path,rows,figures,pages=prepared[key];model=train_independent(training,key,out/'models') if variant=='learn' else None
        started=time.perf_counter()
        tree,ids,roles,excluded,info=tree_for(path,key,out/key,rows,figures,pages,variant,model)
        lines=read_jsonl(ROOT/'artifacts/a1-d02/development/dong'/f'{key}.jsonl') if key in DEVELOPMENT else [
            dict(id=r['d02_id'],trang=r['page'],text=r['text'],bbox=[r['x0'],r['top'],r['x1'],r['bottom']]) for r in rows]
        output,pred=chunk_and_align(tree,lines,key,counter,SETTINGS,source_ids=ids,raw_roles=roles,evaluation_excluded=excluded)
        reference_path=ROOT/b['tree']
        if hashlib.sha256(reference_path.read_bytes()).hexdigest()!=b['tree_sha256']:raise ValueError('Changed silver tree '+key)
        reference=DocumentTree.from_dict(json.loads(reference_path.read_text(encoding='utf-8')))
        reference_chunks=chunk_document(reference,key,counter,UnicodeSentenceSplitter(),**SETTINGS).chunks
        result=dict(sach=key,variant=variant,bold=info,seconds_evaluation=time.perf_counter()-started,
            silver=dict(M1=heading_score([n.to_dict() for n in reference.nodes],[n.to_dict() for n in tree.nodes]),
                        M6=leaf_score(reference_chunks,output.chunks)))
        if key in DEVELOPMENT:
            heads,l2=load_labels(key,ROOT/'artifacts/a1-d02/development',review=True);result['D02']=score(lines,heads,l2,pred)
            if variant=='baseline':
                baseline=json.loads((ROOT/f'tmp/a1-v415/phase2b-20261008/{key}/S1/run-1/prediction.json').read_text(encoding='utf-8'))
                assert pred['headings']==baseline['headings'] and pred['chunks']==baseline['chunks'], 'Baseline replay changed '+key
        write(target/'tree.json',tree.to_dict());write(target/'prediction.json',pred);write(result_path,result)
        results.append(result);print('DONE',variant,key,round(result.get('D02',{}).get('M3',{}).get('accuracy',0),4),flush=True)
    summary={}
    for m in ('M1','M2','M3','M6'):
        field={'M1':'f1','M2':'accuracy','M3':'accuracy','M6':'share'}[m]
        summary[m]=statistics.median(r['D02'][m][field] for r in results if 'D02' in r)
    summary['silver_M6']=statistics.median(r['silver']['M6']['share'] for r in results)
    write(out/f'{variant}.json',dict(books=results,summary=summary,api_usd=0,seconds_are_evaluation_not_M5=True))
    print('SUMMARY',variant,summary,flush=True)


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--variant',choices=['baseline','bold','grammar','hierarchy','learn'],required=True)
    args=parser.parse_args();run(args.out,args.variant)
