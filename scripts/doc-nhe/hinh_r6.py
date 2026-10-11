"""Research-only native image assets and conservative placement; no text sorting."""
from copy import deepcopy
from contextlib import closing
import hashlib
import io
from pathlib import Path

import pypdfium2 as pdfium
import pypdfium2.raw as raw
from doc2roadmap.domain.models import DocumentNode, DocumentTree


def extract_assets(path, folder):
    assets=[]
    folder=Path(folder)
    with pdfium.PdfDocument(path) as pdf:
        for index in range(len(pdf)):
            with closing(pdf[index]) as page:
                width,height=page.get_size()
                for obj in page.get_objects(max_depth=2):
                    if obj.type!=raw.FPDF_PAGEOBJ_IMAGE:
                        continue
                    left,bottom,right,top=obj.get_bounds()
                    if (right-left)*(top-bottom)<.03*width*height:
                        continue
                    entry=dict(page=index+1,bbox=[left,top,right,bottom],source_figure=len(assets),image_id=None,error=None)
                    px,py=obj.get_px_size()
                    w,h=right-left,top-bottom
                    if (px<py)!=(w<h):
                        px,py=py,px
                    projected_pixels=w*h*max(px/w,py/h)**2 if w>0 and h>0 else float('inf')
                    if max(px*py,projected_pixels)>25_000_000:
                        entry['error']='image_over_25M_pixels_needs_fallback'
                    else:
                        try:
                            # Preserve native resolution after matrix/mask; the guard
                            # bounds projected allocation, including rotated/stretched images.
                            with closing(obj.get_bitmap(render=True,scale_to_original=True)) as bitmap:
                                pixels=[bitmap.width,bitmap.height]
                                image=bitmap.to_pil()
                                buffer=io.BytesIO()
                                image.save(buffer,format='PNG')
                                image.close()
                            payload=buffer.getvalue()
                            key=hashlib.sha256(payload).hexdigest()
                            folder.mkdir(parents=True,exist_ok=True)
                            target=folder/(key+'.png')
                            if target.exists():
                                assert hashlib.sha256(target.read_bytes()).hexdigest()==key
                            else:
                                target.write_bytes(payload)
                            entry.update(image_id=key,bytes=len(payload),pixels=pixels)
                        except pdfium.PdfiumError as error:
                            entry['error']=str(error)
                    assets.append(entry)
    return assets


def place_figures(nodes,assets):
    text=[deepcopy(n) for n in nodes if n['node_type']!='figure']
    figures=[deepcopy(n) for n in nodes if n['node_type']=='figure']
    if len(figures)!=len(assets):
        raise ValueError('Detector and asset extraction disagree')
    inserts={}
    warnings=[]
    for figure,asset in zip(figures,assets):
        for field in ('source_figure','page','bbox'):
            if figure[field]!=asset[field]:
                raise ValueError('Wrong figure asset geometry/provenance')
        figure['image_id']=asset['image_id']
        page_nodes=[(i,n) for i,n in enumerate(text) if n['page']==figure['page']]
        top,bottom=figure['bbox'][1],figure['bbox'][3]
        candidates=[]
        for position in range(len(page_nodes)+1):
            before,after=page_nodes[:position],page_nodes[position:]
            if all(n['bbox'][3]>=top for _,n in before) and all(n['bbox'][1]<=bottom for _,n in after):
                candidates.append(position)
        if len(candidates)==1:
            place=candidates[0]
            figure['placement']='vertical_gap'
        else:
            place=len(page_nodes)
            figure['placement']='page_end_unverified'
            warnings.append(dict(source_figure=figure['source_figure'],page=figure['page'],reason='ambiguous_reading_order'))
        if page_nodes:
            anchor=page_nodes[place][0] if place<len(page_nodes) else page_nodes[-1][0]+1
        else:
            anchor=next((i for i,n in enumerate(text) if n['page']>figure['page']),len(text))
        inserts.setdefault(anchor,[]).append(figure)
        if asset['error']:
            warnings.append(dict(source_figure=figure['source_figure'],page=figure['page'],reason=asset['error']))
    result=[]
    for i in range(len(text)+1):
        result.extend(sorted(inserts.get(i,[]),key=lambda n:(n['page'],-n['bbox'][1],n['bbox'][0],n['source_figure'])))
        if i<len(text):
            result.append(text[i])
    return result,warnings


def document_tree(nodes,warnings):
    result=[]
    for n in nodes:
        kind=n['node_type']
        text=n['text']
        raw_text=None
        formula_id=None
        if kind=='formula':
            raw_text=text
            formula_id=hashlib.sha256(text.encode()).hexdigest()
            text='[formula]'
        elif kind=='figure':
            text=text or '[figure]'
        elif kind=='caption':
            kind='text'
        result.append(DocumentNode(node_type=kind,text=text,reading_order=len(result),page=n['page'],
                                   bbox=tuple(n['bbox']),level=n.get('level'),tree_depth=1,
                                   image_id=n.get('image_id'),raw_text=raw_text,formula_id=formula_id))
    return DocumentTree(nodes=result,structure_warnings=[str(w) for w in warnings])
