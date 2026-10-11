import sys
from pathlib import Path
sys.path.insert(0,str(Path('scripts/doc-nhe').resolve()))
from caption_hinh_r18 import candidates


def row(text='Hình 1-2 Nội dung',page=1,top=480,left=10,right=190):
    return dict(text=text,page=page,top=top,bottom=top-10,size=10,x0=left,x1=right)


def figure(page=1): return dict(page=page,bbox=[0,500,200,700])


def test_numbered_caption_needs_nearby_image_on_same_page():
    r=row(); saved=dict(r)
    assert candidates([r],[figure()])==[0]
    assert r==saved
    assert candidates([r],[])==[]
    assert candidates([r],[figure(2)])==[]
    assert candidates([row(top=400)],[figure()])==[]
    assert candidates([row(left=220,right=390)],[figure()])==[]


def test_intervening_text_or_unqualified_title_not_vetoed():
    assert candidates([row('Body',top=490),row()],[figure()])==[]
    assert candidates([row('Hình học không gian')],[figure()])==[]
    assert candidates([row('Bảng 1 Tổng kết')],[figure()])==[]
    assert candidates([row('Figure 1: Image')],[figure()])==[0]


def test_caption_and_image_keep_actual_chunk_owner_and_image_reference():
    import hinh_r6 as images
    from doc2roadmap.domain.chunking import chunk_document
    from tests.conftest import WordCounter,splitter
    rows=[row('1. Real section',top=750),row()]
    veto=candidates(rows,[figure()])
    nodes=[dict(node_type='caption' if i in veto else 'section_header',text=r['text'],
        page=1,bbox=[r['x0'],r['top'],r['x1'],r['bottom']],level=1,source_rows=[i]) for i,r in enumerate(rows)]
    nodes.append(dict(node_type='figure',text='',page=1,bbox=[0,700,200,500],source_figure=0,source_rows=[]))
    assets=[dict(source_figure=0,page=1,bbox=[0,700,200,500],image_id='fixture-image',error=None)]
    placed,warnings=images.place_figures(nodes,assets)
    output=chunk_document(images.document_tree(placed,warnings),'test',WordCounter(),splitter())
    assert [s.title for s in output.sections[1:]]==['1. Real section']
    assert any(rows[1]['text'] in c.text and c.section_path==['1. Real section'] for c in output.chunks)
    assert [r.image_id for c in output.chunks for r in c.image_refs]==['fixture-image']
