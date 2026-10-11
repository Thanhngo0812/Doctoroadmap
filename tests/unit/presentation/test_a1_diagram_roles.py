import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path('scripts/doc-nhe').resolve()))
import chu_trong_hinh_r21 as roles


def fixture(text='GIÁN ĐOAN'):
    row=dict(text=text,page=1,x0=60,x1=140,top=360,bottom=350,size=7,width=600,height=800)
    nodes=[dict(text=text,node_type='section_header',page=1,level=2,
                bbox=[60,360,140,350],source_rows=[0]),
           dict(text='',node_type='figure',page=1,bbox=[50,400,300,200],source_rows=[],source_figure=0)]
    return [row],nodes


@pytest.mark.parametrize('text,kind',[('GIÁN ĐOAN','text'),('Hình 0-6-Lưu đồ hàng đợi','caption')])
def test_diagram_and_enclosed_caption_are_not_section_boundaries(text,kind):
    rows,nodes=fixture(text); original=roles.deepcopy(nodes)
    result,audit=roles.correct(rows,nodes,12)
    assert result[0]['node_type']==kind and result[0]['level'] is None
    assert result[0]['text']==text and result[0]['source_rows']==[0]
    assert result[0]['bbox']==nodes[0]['bbox'] and result[1]==nodes[1]
    assert nodes==original and audit[0]['source_figure']==0


@pytest.mark.parametrize('case',['large_image','page','large_type','numbered','chapter','bullet','overlap','partial','long'])
def test_real_headings_and_ambiguous_raster_ownership_are_kept(case):
    rows,nodes=fixture()
    if case=='large_image': nodes[1]['bbox']=[0,800,600,0]
    elif case=='page': nodes[1]['page']=2
    elif case=='large_type': rows[0]['size']=12
    elif case in ('numbered','chapter','bullet','long'):
        nodes[0]['text']=rows[0]['text']={'numbered':'IV.3 Chuyển ngữ cảnh','chapter':'Chương 5',
            'bullet':'• Hoạt động của công tắc','long':'một hai ba bốn năm sáu bảy tám chín'}[case]
    elif case=='overlap': nodes.append(dict(nodes[1],source_figure=1))
    elif case=='partial': nodes[1]['bbox'][2]=70
    result,audit=roles.correct(rows,nodes,12)
    assert result==nodes and not audit
