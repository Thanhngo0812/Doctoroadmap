"""Conservative role correction for short text enclosed by a raster."""
from copy import deepcopy
import re


def correct(rows,nodes,body):
    result=deepcopy(nodes); audit=[]
    figures=[n for n in nodes if n['node_type']=='figure']
    for node in result:
        if node['node_type']!='section_header' or not node['source_rows']: continue
        text=node['text'].strip()
        caption=bool(re.match(r'^(?:hình|figure|fig\.)\s+\d',text,re.I))
        source=[rows[i] for i in node['source_rows']]
        if caption:
            if len(text.split())>40: continue
        elif (len(text.split())>8 or any(r['size']>.8*body for r in source)
              or re.match(r'^(?:\d|[IVXLCDM]+[.\-\s]|[A-Za-zĐđ][.)]\s|chương\b|chapter\b|phần\b|part\b|[•●▪◦–−-])',text,re.I)):
            continue
        left,top,right,bottom=node['bbox']; area=(right-left)*(top-bottom)
        if area<=0: continue
        owners=[]
        for figure in figures:
            if figure['page']!=node['page']: continue
            fl,ft,fr,fb=figure['bbox']
            if not 0<(fr-fl)*(ft-fb)<=.6*source[0]['width']*source[0]['height']: continue
            overlap=max(0,min(fr,right)-max(fl,left))*max(0,min(ft,top)-max(fb,bottom))
            if overlap>=.9*area: owners.append(figure)
        if len(owners)!=1: continue
        node.update(node_type='caption' if caption else 'text',level=None)
        audit.append(dict(page=node['page'],text=text,source_rows=node['source_rows'],
                          source_figure=owners[0]['source_figure'],role=node['node_type'],
                          reason='caption_inside_raster_visibility_unverified' if caption else 'small_diagram_text'))
    return result,audit
