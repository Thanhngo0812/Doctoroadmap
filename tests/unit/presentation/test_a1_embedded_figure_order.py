import sys
from copy import deepcopy
from pathlib import Path
import pytest
sys.path.insert(0,str(Path('scripts/doc-nhe').resolve()))
import vi_tri_hinh_r25 as placement


def fixture():
    rows=[dict(width=600,height=800,page=1)]*3
    nodes=[dict(node_type=kind,text=text,page=1,bbox=bbox,source_rows=[i]) for i,(kind,text,bbox) in enumerate([
        ('text','Trước hình',[50,600,300,580]),('caption','Hình 1',[80,450,220,430]),
        ('text','Sau hình',[50,300,300,280])])]
    figure=dict(node_type='figure',text='',page=1,bbox=[40,500,320,400],source_rows=[],source_figure=0)
    nodes.append(figure)
    assets=[dict(page=1,bbox=figure['bbox'],source_figure=0,image_id='asset',error=None)]
    return rows,nodes,assets


def test_figure_is_before_following_body_but_embedded_order_stays_flagged():
    rows,nodes,assets=fixture();original=deepcopy(nodes)
    placed,warnings=placement.place(rows,nodes,assets)
    kinds=[n['node_type'] for n in placed]
    image=next(n for n in placed if n['node_type']=='figure')
    assert kinds==['text','caption','figure','text']
    assert image['placement']=='external_vertical_gap' and image['image_id']=='asset'
    assert [n for n in placed if n['node_type']!='figure']==nodes[:-1]
    assert any(w['reason']=='embedded_text_order_unverified' for w in warnings)
    assert nodes==original


@pytest.mark.parametrize('case',['large','heading','overlap','all_inside','out_of_order'])
def test_unresolved_geometry_keeps_fallback(case):
    rows,nodes,assets=fixture()
    if case=='large':nodes[-1]['bbox']=assets[0]['bbox']=[0,800,600,0]
    elif case=='heading':nodes[1]['node_type']='section_header'
    elif case=='overlap':
        nodes.append(dict(nodes[-1],source_figure=1));assets.append(dict(assets[0],source_figure=1))
    elif case=='all_inside':
        nodes[0]['bbox']=nodes[1]['bbox'];nodes[2]['bbox']=nodes[1]['bbox']
    elif case=='out_of_order':nodes[0],nodes[2]=nodes[2],nodes[0]
    placed,warnings=placement.place(rows,nodes,assets)
    assert all(n['placement']=='page_end_unverified' for n in placed if n['node_type']=='figure')
    assert any(w['reason']=='ambiguous_reading_order' for w in warnings)
