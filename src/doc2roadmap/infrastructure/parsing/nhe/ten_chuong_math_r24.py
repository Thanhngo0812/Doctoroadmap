"""Join a narrowly evidenced chapter continuation and inline superscript."""
from copy import deepcopy
import hashlib
import re


def combine(rows,nodes,body):
    result=[]; audit=[]; i=0
    while i<len(nodes):
        a=nodes[i]; rest=nodes[i+1:i+3]
        eligible=(a['node_type']=='section_header' and len(a['source_rows'])>=2
                  and re.match(r'^(?:chương|chapter|phần|part)\s+(?:\d+|[IVXLCDM]+)\b',a['text'],re.I)
                  and len(rest)==2)
        if eligible:
            b,c=rest
            eligible=(b['node_type']=='text' and c['node_type']=='formula'
                      and len(b['source_rows'])==len(c['source_rows'])==1
                      and a['page']==b['page']==c['page']
                      and a['source_rows'][-1]+1==b['source_rows'][0]
                      and b['source_rows'][0]+1==c['source_rows'][0])
        if eligible:
            previous=rows[a['source_rows'][-1]]; line=rows[b['source_rows'][0]]; script=rows[c['source_rows'][0]]
            scale=max(line['size'],1)
            eligible=(2<=len(b['text'].split())<=20 and b['text'][0].islower()
                      and all(previous.get(k)==line.get(k) for k in ('font','bold','italic'))
                      and abs(previous['size']-scale)<=.1*scale and scale>=1.3*body
                      and abs(previous['x0']-line['x0'])<=.5*scale
                      and -.2*scale<=previous['bottom']-line['top']<=.6*scale
                      and 1<=len(c['text'])<=3 and c['text'].isalnum() and script.get('math',0)>=.5
                      and .5*scale<=script['size']<=.95*scale
                      and -.2*scale<=script['x0']-line['x1']<=.4*scale
                      and line['top']<script['top']<=line['top']+.6*scale
                      and line['bottom']<script['bottom']<line['top'])
            if eligible and any(n['node_type']=='figure' and n['page']==a['page']
                and n['bbox'][1]>b['bbox'][1] and n['bbox'][3]<a['bbox'][3]
                and min(n['bbox'][2],b['bbox'][2])>max(n['bbox'][0],b['bbox'][0]) for n in nodes):
                eligible=False
        if not eligible:
            result.append(deepcopy(a));i+=1;continue
        merged=deepcopy(a);sources=[a,b,c]
        merged.update(text=' '.join(n['text'] for n in sources),source_rows=sum((n['source_rows'] for n in sources),[]),
                      bbox=[min(n['bbox'][0] for n in sources),max(n['bbox'][1] for n in sources),
                            max(n['bbox'][2] for n in sources),min(n['bbox'][3] for n in sources)])
        result.append(merged);i+=3
        audit.append(dict(page=a['page'],title=merged['text'],script=c['text'],source_rows=c['source_rows'],
                          script_bbox=c['bbox'],former_formula_id=hashlib.sha256(c['text'].encode()).hexdigest(),
                          role='inline_script'))
    return result,audit
