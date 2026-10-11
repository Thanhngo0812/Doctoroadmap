import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path('scripts/doc-nhe').resolve()))
import ma_bai_r22 as metadata
from do_r2 import verify_nodes


def fixture(code='Mã bài MH 8- 03'):
    texts=['Chương 3','Công nghệ sinh học thực vật',code]
    rows=[dict(text=t,page=1,x0=50,x1=250,top=700-i*20,bottom=690-i*20) for i,t in enumerate(texts)]
    nodes=[dict(text=' '.join(texts),page=1,x0=50,level=1,node_type='section_header',
                source_rows=[0,1,2],bbox=[50,700,250,650])]
    return rows,nodes


def test_metadata_is_retained_in_body_not_in_chapter_title():
    rows,nodes=fixture(); original=metadata.deepcopy(nodes)
    result,audit=metadata.separate(rows,nodes)
    assert [n['node_type'] for n in result]==['section_header','text']
    assert result[0]['text']=='Chương 3 Công nghệ sinh học thực vật'
    assert result[1]['text']=='Mã bài MH 8- 03' and result[1]['level'] is None
    verify_nodes(rows,[],result)
    assert nodes==original and audit[0]['source_rows']==[2]


@pytest.mark.parametrize('text',['Mã bài và ứng dụng','Mã bài học trong giáo dục','Mã hóa MH 8-03','Mã bài ABC'])
def test_normal_title_words_are_not_removed(text):
    rows,nodes=fixture(text)
    result,audit=metadata.separate(rows,nodes)
    assert result==nodes and not audit


def test_code_line_inside_nonchapter_heading_is_not_reinterpreted():
    rows,nodes=fixture(); nodes[0]['text']='1. '+nodes[0]['text']
    assert metadata.separate(rows,nodes)[0]==nodes
