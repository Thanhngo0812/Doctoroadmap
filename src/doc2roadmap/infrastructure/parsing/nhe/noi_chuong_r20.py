"""Join separate chapter labels and titles with auditable source-row geometry."""
from copy import deepcopy
import re
from . import cau_truc_r2 as structure

LABEL=re.compile(r'^(?:chương|chapter|phần|part)\s+(?:\d+|[IVXLCDM]+)[.:]?$',re.I)


def combine(rows,nodes):
    result=[]; audit=[]; i=0
    while i<len(nodes):
        a=nodes[i]; b=nodes[i+1] if i+1<len(nodes) else None
        if a['node_type']!='section_header' or not LABEL.fullmatch(a['text'].strip()) or b is None:
            result.append(deepcopy(a)); i+=1; continue
        reason=None
        if b['node_type']!='section_header': reason='not_heading'
        elif a['page']!=b['page']: reason='different_page'
        elif not a['source_rows'] or not b['source_rows'] or a['source_rows'][-1]+1!=b['source_rows'][0]: reason='not_adjacent_rows'
        elif (not 1<=len(b['text'].split())<=20 or LABEL.fullmatch(b['text'].strip())
              or structure.baseline.CAPTION.match(b['text'])
              or re.match(r'^\s*(?:\d|[IVXLCDM]+[.\-–]?\s|[A-Za-zĐđ][.)]\s|[•●▪◦–−-])',b['text'])): reason='not_title'
        else:
            first=rows[a['source_rows'][-1]]; following=[rows[j] for j in b['source_rows']]
            scale=max(first['size'],1)
            if any(r.get('font')!=first.get('font') or r['bold']!=first['bold']
                   or r.get('italic')!=first.get('italic') or abs(r['size']-first['size'])>.1*scale for r in following): reason='different_style'
            elif not -.25*scale<=a['bbox'][3]-b['bbox'][1]<=4*scale: reason='gap'
            elif min(abs(a['bbox'][0]-b['bbox'][0]),abs(sum(a['bbox'][::2])-sum(b['bbox'][::2]))/2)>1.5*scale: reason='alignment'
            elif any(n['node_type']=='figure' and n['page']==a['page']
                     and n['bbox'][1]>b['bbox'][1] and n['bbox'][3]<a['bbox'][3]
                     and min(n['bbox'][2],b['bbox'][2])>max(n['bbox'][0],b['bbox'][0]) for n in nodes): reason='figure_between'
        audit.append(dict(page=a['page'],label=a['text'],title=b['text'],source_rows=a['source_rows']+b['source_rows'],
                          joined=reason is None,reason=reason))
        if reason:
            result.append(deepcopy(a)); i+=1; continue
        merged=deepcopy(a)
        merged['text']=a['text']+' '+b['text']; merged['source_rows']=a['source_rows']+b['source_rows']
        merged['bbox']=[min(a['bbox'][0],b['bbox'][0]),max(a['bbox'][1],b['bbox'][1]),
                        max(a['bbox'][2],b['bbox'][2]),min(a['bbox'][3],b['bbox'][3])]
        result.append(merged); i+=2
    return result,audit
