"""D-02 packets: raw PDFium lines, page images, bookmarks and seeded strata."""
import argparse
from collections import Counter
from contextlib import closing
import hashlib
import json
from pathlib import Path
import random
import re
import shutil
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT/'.venv/Lib/site-packages'))
sys.path.insert(0,str(ROOT/'scripts/thu-a1'))
import doc_nhe as light

DEVELOPMENT=('d01-02','d01-06','d01-07','d01-10','d01-11','d01-15')


def write(path,value,jsonl=False):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    payload=''.join(json.dumps(v,ensure_ascii=False)+'\n' for v in value) if jsonl else json.dumps(value,ensure_ascii=False,indent=2)+'\n'
    temporary=path.with_suffix(path.suffix+'.tmp');temporary.write_text(payload,encoding='utf-8');temporary.replace(path)


def page_rows(page,number):
    width,height=page.get_size(); result=[]
    for chars in light.page_lines(page):
        row=light.describe(chars,number,height,width)
        if row:
            result.append(dict(id=f'p{number:04}-l{len(result)+1:03}',trang=number,text=row['text'],
                bbox=[row['x0'],row['top'],row['x1'],row['bottom']],co_chu=row['size'],dam=row['bold']))
    # PDFium-generated CR/LF and spaces are omitted; every Unicode letter must survive once.
    with closing(page.get_textpage()) as textpage:
        letters=Counter(chr(light.raw.FPDFText_GetUnicode(textpage.raw,i)) for i in range(textpage.count_chars())
                        if chr(light.raw.FPDFText_GetUnicode(textpage.raw,i)).isalpha())
    assert letters==Counter(c for row in result for c in row['text'] if c.isalpha()), 'Lost/duplicated page letters'
    return result


def select_pages(rows,features,count,seed=42):
    """Raw signals only, no model/docling predictions supplied to annotators."""
    rng=random.Random(seed); chosen=[];strata=[]
    by_page={i:[r for r in rows if r['trang']==i] for i in range(1,count+1)}
    pools={
        'mo_chuong':[p for p,rs in by_page.items() if any(re.match(r'^(?:CHƯƠNG|Chương|PHẦN|Phần|BÀI|Bài)\s+[\dIVXLC]',r['text']) for r in rs)],
        'bang':[p for p,f in features.items() if f['table_hint']],
        'hinh':[p for p,f in features.items() if f['image']],
        'cong_thuc':[p for p,f in features.items() if f['math_hint']],
    }
    used=set(sum(pools.values(),[]))
    normal=[p for p in by_page if p not in used and by_page[p]]
    for name in ('mo_chuong','bang','hinh','cong_thuc','thuong_1','thuong_2','cuoi_sach','ngau_nhien'):
        pool=normal if name.startswith('thuong') else [count] if name=='cuoi_sach' else pools.get(name,list(by_page))
        eligible=[p for p in sorted(pool) if p not in chosen]
        fallback=not eligible
        if fallback:eligible=[p for p in by_page if p not in chosen]
        if not eligible:break
        p=rng.choice(eligible);chosen.append(p);strata.append(dict(loai=name,trang=p,du_phong=fallback))
    return dict(trang=sorted(chosen),phan_tang=strata,seed=seed,pham_vi=[1,count])


def export(pdf_path,sach,folder,*,dpi=110,seed=42):
    pdf_path=Path(pdf_path).resolve();folder=Path(folder)
    if (ROOT/'document-data/test').resolve() in pdf_path.parents:raise ValueError('Không mở document-data/test')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*',sach):raise ValueError('Mã sách sai')
    signature=dict(pdf_sha256=hashlib.sha256(pdf_path.read_bytes()).hexdigest(),dpi=dpi,seed=seed,
                   line_algorithm_sha256=hashlib.sha256((ROOT/'scripts/thu-a1/doc_nhe.py').read_bytes()).hexdigest())
    meta=folder/'metadata'/f'{sach}.json'
    if meta.exists():
        prior=json.loads(meta.read_text(encoding='utf-8'))
        if any(prior.get(k)!=v for k,v in signature.items()):raise ValueError('Phiếu thuộc nguồn/cấu hình khác; dùng thư mục mới')
    else:write(meta,signature)
    started=time.perf_counter();rows=[];features={};images={}
    with light.pdfium.PdfDocument(pdf_path) as pdf:
        count=min(len(pdf),300)
        for i in range(count):
            with closing(pdf[i]) as page:
                current=page_rows(page,i+1);rows.extend(current)
                width,height=page.get_size();objects=list(page.get_objects(max_depth=15))
                features[i+1]=dict(image=any(o.type==light.raw.FPDF_PAGEOBJ_IMAGE for o in objects),
                    table_hint=sum(o.type==light.raw.FPDF_PAGEOBJ_PATH for o in objects)>=8
                        or sum(bool(re.search(r'\d\s+\d',r['text'])) for r in current)>=3,
                    math_hint=sum(any(c in light.STRONG_MATH for c in r['text']) for r in current)>=3)
                image_path=folder/'trang'/sach/f'p{i+1:04}.png';image_path.parent.mkdir(parents=True,exist_ok=True)
                if not image_path.exists():
                    with closing(page.render(scale=dpi/72)) as bitmap:
                        image=bitmap.to_pil();image.save(image_path,format='PNG');image.close()
                images[image_path.relative_to(folder).as_posix()]=hashlib.sha256(image_path.read_bytes()).hexdigest()
            if (i+1)%30==0:print(sach,i+1,'/',count,flush=True)
        bookmarks=[]
        for item in pdf.get_toc():
            dest=item.get_dest();index=dest.get_index() if dest else None
            bookmarks.append(dict(text=item.get_title(),cap=item.level+1,trang=None if index is None else index+1))
        total=len(pdf)
    line_path=folder/'dong'/f'{sach}.jsonl'
    if line_path.exists():
        old=[json.loads(line) for line in line_path.read_text(encoding='utf-8').splitlines() if line.strip()]
        assert old==rows, 'Canonical line IDs/text/geometry changed across repeated extraction'
    write(line_path,rows,True)
    write(folder/'chon-trang-mau'/f'{sach}.json',select_pages(rows,features,count,seed))
    write(folder/'muc_luc_dien_tu'/f'{sach}.json',bookmarks)
    shutil.copyfile(Path(__file__).with_name('kiem_nhan_d02.py'),folder/'kiem_nhan_d02.py')
    shutil.copyfile(ROOT/'report/huong-dan-agentic-gan-nhan-d02.md',folder/'huong-dan-agentic-gan-nhan-d02.md')
    result=dict(signature,sach=sach,trang_pdf=total,trang_xuat=count,dong=len(rows),complete=True,
                coordinate_system='PDF bottom-left: [left, top, right, bottom]',images=images,
                exporter_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                seconds=time.perf_counter()-started)
    write(meta,result);print(sach,'DONE',len(rows),'lines',flush=True)
    return result


def development_paths():
    data=json.loads((ROOT/'document-data/manifest.json').read_text(encoding='utf-8'))
    return {b['id']:ROOT/'document-data'/b['file'] for b in data['books'] if b['id'] in DEVELOPMENT and b['split']=='train'}


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True);parser.add_argument('--sach',choices=DEVELOPMENT)
    parser.add_argument('--pdf',type=Path,help='Custodian only: explicit locked PDF path')
    parser.add_argument('--ma-sach',help='Custodian book ID with --pdf')
    args=parser.parse_args()
    if args.pdf:
        if not args.ma_sach:parser.error('--pdf cần --ma-sach')
        export(args.pdf,args.ma_sach,args.out)
    else:
        for key,path in development_paths().items():
            if not args.sach or args.sach==key:export(path,key,args.out)
