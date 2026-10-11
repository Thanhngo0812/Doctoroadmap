import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path('scripts/doc-nhe').resolve()))
import noi_chuong_r20 as chapter
from do_r2 import verify_nodes


def fixture():
    rows=[dict(text=t,page=1,x0=50.,x1=250.,top=top,bottom=top-20,size=20.,font='Bold',bold=True,italic=False)
          for t,top in [('Chương V',700.),('Vật chất và ý thức',660.)]]
    nodes=[dict(node_type='section_header',text=r['text'],page=r['page'],x0=r['x0'],level=1,
                source_rows=[i],bbox=[r['x0'],r['top'],r['x1'],r['bottom']]) for i,r in enumerate(rows)]
    return rows,nodes


def test_chapter_label_and_title_are_one_heading_preserving_each_source_row():
    rows,nodes=fixture(); saved=chapter.deepcopy(nodes)
    result,audit=chapter.combine(rows,nodes)
    assert len(result)==1 and result[0]['text']=='Chương V Vật chất và ý thức'
    assert result[0]['source_rows']==[0,1] and result[0]['bbox']==[50.,700.,250.,640.]
    verify_nodes(rows,[],result)
    assert nodes==saved and audit[0]['joined'] is True


@pytest.mark.parametrize('change',['subheading','caption','paragraph','page','font','gap','next_chapter'])
def test_chapter_join_rejects_unsafe_neighbors(change):
    rows,nodes=fixture()
    if change in ('subheading','caption','next_chapter'):
        rows[1]['text']=nodes[1]['text']={'subheading':'I- Vật chất','caption':'Hình 1 Nội dung','next_chapter':'Chương VI'}[change]
    elif change=='paragraph': nodes[1]['node_type']='text'
    elif change=='page': rows[1]['page']=nodes[1]['page']=2
    elif change=='font': rows[1]['font']='Body'
    elif change=='gap': rows[1]['top']=nodes[1]['bbox'][1]=400
    result,_=chapter.combine(rows,nodes)
    assert result==nodes


def test_source_row_loss_is_caught_by_independent_verifier():
    rows,nodes=fixture(); result,_=chapter.combine(rows,nodes)
    result[0]['source_rows']=[0]
    with pytest.raises(AssertionError): verify_nodes(rows,[],result)


def test_figure_between_label_and_title_blocks_even_when_figures_stored_last():
    rows,nodes=fixture()
    nodes.append(dict(node_type='figure',page=1,bbox=[50.,679.,200.,661.],source_rows=[]))
    result,audit=chapter.combine(rows,nodes)
    assert result==nodes and audit[0]['reason']=='figure_between'
