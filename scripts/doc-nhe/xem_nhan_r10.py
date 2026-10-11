"""Render frozen, prediction-free R3 review selections with row boxes."""
import argparse
from collections import Counter
from pathlib import Path
import subprocess
import sys
import hoc_tieu_de as base
from PIL import Image, ImageDraw


def run(out,start,count):
    packet=base.ROOT/'tmp/a1-v414-r3/review-packet.json'
    previous=base.ROOT/'report/v4-14-r3-review-2026-10-07.json'
    known={e['id'] for e in base.read(previous)['entries']}
    counts=Counter()
    selected=[]
    for entry in base.read(packet):
        key=entry['book'],entry['role']
        if entry['id'] in known or counts[key]>=(2 if entry['role']=='development' else 1):
            continue
        counts[key]+=1
        selected.append(entry)
    manifest=dict(packet_sha256=base.digest(packet),previous_review_sha256=base.digest(previous),
                  protocol_sha256=base.digest(base.ROOT/'report/v4-14-r10-giao-thuc-2026-10-07.md'),
                  script_sha256=base.digest(__file__),entries=selected)
    target=out/'selection.json'
    if target.exists():
        assert base.read(target)==manifest
    else:
        base.write(target,manifest)
    pinned={b['id']:b for b in base.manifest(base.ROOT/'tmp/doc-nhe-v414')['books']}
    for number,entry in list(enumerate(selected))[start:start+count]:
        image_path=out/f'{number:02d}-{entry["book"]}-{entry["page"]}.png'
        if image_path.exists():
            continue
        book=pinned[entry['book']]
        pdf=base.allowed_path(base.ROOT/book['pdf'],external=book['split']=='external')
        prefix=image_path.with_suffix('')
        result=subprocess.run(['pdftoppm','-f',str(entry['page']),'-l',str(entry['page']),'-r','100',
                               '-singlefile','-png',str(pdf),str(prefix)],capture_output=True,text=True)
        if result.returncode:
            raise RuntimeError(result.stderr)
        d=base.read(base.ROOT/'tmp/doc-nhe-v414/datasets'/(entry['book']+'.json'))
        row=d['rows'][entry['row']]
        with Image.open(image_path) as source:
            image=source.convert('RGB')
        sx,sy=image.width/row['width'],image.height/row['height']
        left,top,right,bottom=entry['bbox']
        draw=ImageDraw.Draw(image)
        draw.rectangle([left*sx,(row['height']-top)*sy,right*sx,(row['height']-bottom)*sy],outline='#d00000',width=2)
        image.save(image_path)
        image.close()
        base.write(image_path.with_suffix('.json'),dict(id=entry['id'],page=entry['page'],
                   render_warning=result.stderr,source_sha256=book['pdf_sha256'],render_sha256=base.digest(image_path)))
        print(number,entry['id'],entry['page'],entry['text'],flush=True)


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--out',type=Path,default=Path('tmp/pdfs/a1-r10'))
    cli.add_argument('--start',type=int,default=0)
    cli.add_argument('--count',type=int,default=6)
    a=cli.parse_args()
    run(a.out,a.start,a.count)
