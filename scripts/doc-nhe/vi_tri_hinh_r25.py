"""Resolve external figure anchors without claiming embedded text order."""
import hinh_r6 as previous


def overlap(a,b):
    return max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[1],b[1])-max(a[3],b[3]))


def place(rows,nodes,assets):
    placed,warnings=previous.place_figures(nodes,assets)
    text=[n for n in placed if n['node_type']!='figure']
    figures=[n for n in placed if n['node_type']=='figure']
    anchors={};position=0
    for n in placed:
        if n['node_type']=='figure':anchors[n['source_figure']]=position
        else:position+=1
    for figure in figures:
        if figure['placement']!='page_end_unverified':continue
        page_nodes=[(i,n) for i,n in enumerate(text) if n['page']==figure['page']]
        source=next((rows[n['source_rows'][0]] for _,n in page_nodes if n['source_rows']),None)
        if source is None:continue
        bbox=figure['bbox'];area=(bbox[2]-bbox[0])*(bbox[1]-bbox[3])
        if not 0<area<=.6*source['width']*source['height']:continue
        siblings=[f for f in figures if f['page']==figure['page'] and f is not figure]
        if any(overlap(f['bbox'],bbox)>0 for f in siblings):continue
        inside=[];outside=[]
        for i,n in page_nodes:
            nb=n['bbox'];na=(nb[2]-nb[0])*(nb[1]-nb[3])
            if n['node_type'] in {'text','caption','formula','list_item'} and na>0 and overlap(nb,bbox)>=.9*na:
                inside.append(i)
            else:outside.append((i,n))
        if not inside or not outside:continue
        gaps=[p for p in range(len(outside)+1)
              if all(n['bbox'][3]>=bbox[1] for _,n in outside[:p])
              and all(n['bbox'][1]<=bbox[3] for _,n in outside[p:])]
        if len(gaps)!=1:continue
        p=gaps[0]
        anchors[figure['source_figure']]=outside[p][0] if p<len(outside) else page_nodes[-1][0]+1
        figure['placement']='external_vertical_gap'
        warnings=[w for w in warnings if not (w['source_figure']==figure['source_figure'] and w['reason']=='ambiguous_reading_order')]
        warnings.append(dict(source_figure=figure['source_figure'],page=figure['page'],
                             reason='embedded_text_order_unverified',source_rows=[j for i in inside for j in text[i]['source_rows']]))
    inserts={}
    for f in figures:inserts.setdefault(anchors[f['source_figure']],[]).append(f)
    result=[]
    for i in range(len(text)+1):
        result.extend(sorted(inserts.get(i,[]),key=lambda n:(n['page'],-n['bbox'][1],n['bbox'][0],n['source_figure'])))
        if i<len(text):result.append(text[i])
    return result,warnings
