import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path('scripts/doc-nhe').resolve()))
import ten_chuong_math_r24 as titles
from do_r2 import verify_nodes


def fixture():
    specs=[('Chương 5',700,680,50,220,20,0),('Phép biến đổi tuyến tính và',660,640,50,330,20,0),
           ('dạng toàn phương trên R',632,612,50,300,20,0),('n',638,621,302,312,16,.9)]
    rows=[dict(text=t,page=1,top=top,bottom=bottom,x0=l,x1=r,size=size,math=math,
               font='Math' if math else 'Bold',bold=not math,italic=False) for t,top,bottom,l,r,size,math in specs]
    nodes=[]
    for indexes,kind in [([0,1],'section_header'),([2],'text'),([3],'formula')]:
        rs=[rows[i] for i in indexes]
        nodes.append(dict(text=' '.join(r['text'] for r in rs),node_type=kind,page=1,x0=rs[0]['x0'],
            level=1 if kind=='section_header' else None,source_rows=indexes,
            bbox=[min(r['x0'] for r in rs),max(r['top'] for r in rs),max(r['x1'] for r in rs),min(r['bottom'] for r in rs)]))
    return rows,nodes


def test_inline_superscript_is_part_of_title_without_losing_source_glyph():
    rows,nodes=fixture();original=titles.deepcopy(nodes)
    result,audit=titles.combine(rows,nodes,12)
    assert len(result)==1 and result[0]['node_type']=='section_header'
    assert result[0]['text']=='Chương 5 Phép biến đổi tuyến tính và dạng toàn phương trên R n'
    verify_nodes(rows,[],result)
    assert nodes==original and audit[0]['script']=='n' and audit[0]['source_rows']==[3]


@pytest.mark.parametrize('case',['below','far','size','page','nonmath','body_size','different_font','numbered'])
def test_display_formula_and_unsafe_continuation_are_not_swallowed(case):
    rows,nodes=fixture()
    if case=='below': rows[3]['top']=nodes[2]['bbox'][1]=600
    elif case=='far': rows[3]['x0']=nodes[2]['bbox'][0]=350
    elif case=='size': rows[3]['size']=20
    elif case=='page': rows[3]['page']=nodes[2]['page']=2
    elif case=='nonmath': rows[3]['math']=0
    elif case=='different_font': rows[2]['font']='Body'
    elif case=='numbered': rows[2]['text']=nodes[1]['text']='5.1 Phép biến đổi'
    result,audit=titles.combine(rows,nodes,20 if case=='body_size' else 12)
    assert result==nodes and not audit


def test_intervening_figure_prevents_join_and_source_loss_is_detectable():
    rows,nodes=fixture()
    nodes.append(dict(node_type='figure',text='',page=1,bbox=[50,639,330,633],source_rows=[],source_figure=0))
    assert titles.combine(rows,nodes,12)[0]==nodes
    rows,nodes=fixture();result,_=titles.combine(rows,nodes,12)
    result[0]['source_rows']=[0,1,2]
    with pytest.raises(AssertionError): verify_nodes(rows,[],result)
