"""Route by PDF rendering signals; independent of book names or learned headings."""
import argparse
from collections import Counter
from contextlib import closing
import ctypes
import json
from pathlib import Path
import sys

from xuat_phieu import ROOT,light


def page_signals(page,number):
    width,height=page.get_size(); area=width*height
    coverage=0.
    for obj in page.get_objects(max_depth=15):
        if obj.type==light.raw.FPDF_PAGEOBJ_IMAGE:
            l,b,r,t=obj.get_bounds()
            coverage=max(coverage,max(0,min(width,r)-max(0,l))*max(0,min(height,t)-max(0,b))/max(area,1))
    letters=hidden=glyphless=0;buffer=ctypes.create_string_buffer(256);flags=ctypes.c_int()
    with closing(page.get_textpage()) as tp:
        for i in range(tp.count_chars()):
            if not chr(light.raw.FPDFText_GetUnicode(tp.raw,i)).isalpha():continue
            letters+=1
            text_object=light.raw.FPDFText_GetTextObject(tp.raw,i)
            hidden+=bool(text_object) and light.raw.FPDFTextObj_GetTextRenderMode(text_object)==3
            light.raw.FPDFText_GetFontInfo(tp.raw,i,buffer,256,ctypes.byref(flags))
            glyphless+=b'GlyphLessFont' in buffer.value
    if not letters:kind='scan_no_text' if coverage>=.8 else 'no_text'
    elif coverage>=.8 and (hidden/letters>=.5 or glyphless/letters>=.5):kind='scan_ocr'
    elif hidden/letters>=.5 or glyphless/letters>=.5:kind='hidden_text_without_full_image'
    else:kind='native'
    return dict(page=number,type=kind,letters=letters,hidden_render_3=hidden,glyphless=glyphless,
                max_image_coverage=coverage)


def route(path):
    path=Path(path).resolve()
    if (ROOT/'document-data/test').resolve() in path.parents:raise ValueError('Không mở document-data/test')
    with light.pdfium.PdfDocument(path) as pdf:
        rows=[]
        for i in range(len(pdf)):
            with closing(pdf[i]) as page:rows.append(page_signals(page,i+1))
    counts=Counter(r['type'] for r in rows)
    content=len(rows)-counts['no_text'];scan=counts['scan_ocr']+counts['scan_no_text']
    if not content:kind='no_text'
    elif scan>=content*.5:kind='scan_ocr' if counts['scan_ocr'] else 'scan_no_text'
    elif counts['native']==content:kind='native'
    else:kind='mixed'
    return dict(pdf_type=kind,system='S1' if kind=='native' else 'S0',pages=rows,page_counts=dict(counts),
                rules=dict(full_image=.8,hidden_or_glyphless=.5,scan_book_fraction=.5))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();records=[]
    for book in json.loads(args.manifest.read_text(encoding='utf-8'))['books']:
        path=ROOT/book['pdf'];record=dict(sach=book['id'],expected=book['type'],**route(path))
        record['correct']=record['pdf_type']==book['type'];records.append(record)
        print(book['id'],record['pdf_type'],record['correct'],flush=True)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(dict(books=records,correct=sum(r['correct'] for r in records),total=len(records)),
                                  ensure_ascii=False,indent=2),encoding='utf-8')
