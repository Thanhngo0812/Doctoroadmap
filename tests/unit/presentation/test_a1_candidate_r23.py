"""Independent downstream consequences of the combined research candidate."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path('scripts/doc-nhe').resolve()))
import noi_chuong_r20 as chapter
import chu_trong_hinh_r21 as diagram
import ma_bai_r22 as metadata
import hinh_r6 as images
import so_muc_r17 as hierarchy
import tach_nhan_cay_r16 as replay
from do_r2 import verify_nodes


class Counter:
    identifier='test-words'

    def count(self,text):
        return len(text.split())


def test_chapter_and_part_parentage_survives_roles_metadata_images_and_chunking():
    specs=[('Phần I',760,20),('Cơ sở lý thuyết',730,20),('Chương 1',690,20),
           ('Khái niệm và ứng dụng',660,20),('Mã bài MH 01',630,20),('GIÁN ĐOAN',450,7),
           ('Nội dung chương này giải thích nguyên lý hoạt động của thiết bị.',280,12)]
    rows=[dict(text=t,page=1,x0=50,x1=250,top=y,bottom=y-size,size=size,font='Bold',bold=True,
               italic=False,width=600,height=800) for t,y,size in specs]
    nodes=[]
    # Simulate B2's pre-existing title + lesson-code grouping.
    for indexes in ([0],[1],[2],[3,4],[5],[6]):
        source=[rows[i] for i in indexes]
        nodes.append(dict(node_type='text' if indexes==[6] else 'section_header',
            text=' '.join(r['text'] for r in source),source_rows=list(indexes),page=1,x0=50,level=1,
            bbox=[50,max(r['top'] for r in source),250,min(r['bottom'] for r in source)]))
    figures=[dict(page=1,bbox=[40,400,300,480])]
    nodes.append(dict(node_type='figure',text='',page=1,bbox=[40,480,300,400],source_rows=[],source_figure=0))
    nodes,_=chapter.combine(rows,nodes)
    nodes,_=diagram.correct(rows,nodes,12)
    nodes,_=metadata.separate(rows,nodes)
    verify_nodes(rows,figures,nodes)
    assets=[dict(page=1,bbox=[40,480,300,400],source_figure=0,image_id='fixture-image',error=None)]
    placed,warnings=images.place_figures(nodes,assets)
    tree=images.document_tree(placed,warnings)
    counter=Counter(); _,keep,_=replay.capture(tree,'fixture',counter,{})
    heads=[dict(rows[n['source_rows'][0]],text=n['text']) for n in nodes if n['node_type']=='section_header']
    accepted=[h for h,k in zip(heads,keep) if k]
    declared=replay.declared(tree,keep,hierarchy.rule(accepted))
    output=replay.chunking.chunk_document(declared,'fixture',counter,replay.UnicodeSentenceSplitter(),heading_scheme='declared-v1')
    sections={s.title:s for s in output.sections}
    part=sections['Phần I Cơ sở lý thuyết']; child=sections['Chương 1 Khái niệm và ứng dụng']
    assert child.parent_section_id==part.section_id
    assert 'GIÁN ĐOAN' not in sections and all('Mã bài' not in s.title for s in output.sections)
    body=' '.join(c.text for c in output.chunks)
    assert 'Mã bài MH 01' in body and 'GIÁN ĐOAN' in body
    image_chunks=[c for c in output.chunks if c.image_refs]
    assert [r.image_id for c in image_chunks for r in c.image_refs]==['fixture-image']
    assert all(c.parent_section_id==child.section_id for c in image_chunks)
