from copy import deepcopy
import sys
from pathlib import Path

import pytest

sys.path.insert(0,str(Path('scripts/doc-nhe').resolve()))
import hinh_r6 as images
from doc2roadmap.domain.chunking import chunk_document
from tests.conftest import WordCounter, splitter


def text(value,box,page=1):
    return dict(node_type='text',text=value,bbox=box,page=page,source_rows=[0],level=None)


def figure(box,page=1,index=0):
    return dict(node_type='figure',text='',bbox=box,page=page,source_rows=[],level=None,source_figure=index)


def asset(node):
    return {k:node[k] for k in ('page','bbox','source_figure')} | dict(image_id='a'*64,error=None)


def test_figure_moves_to_gap_without_sorting_or_mutating_text():
    first=text('Before image.',[10,700,300,680])
    second=text('After image.',[10,300,300,280])
    fig=figure([20,600,280,400])
    nodes=[first,second,fig]
    frozen=deepcopy(nodes)
    result,warnings=images.place_figures(nodes,[asset(fig)])
    assert [n['node_type'] for n in result]==['text','figure','text']
    assert result[0]==first and result[2]==second and nodes==frozen
    assert not warnings
    tree=images.document_tree(result,warnings)
    output=chunk_document(tree,'book',WordCounter(),splitter())
    refs=[r for chunk in output.chunks for r in chunk.image_refs]
    assert len(refs)==1 and refs[0].image_id=='a'*64
    assert tree.nodes[1].bbox==(20,600,280,400)


def test_two_column_or_overlapping_text_is_not_claimed_as_solved():
    fig=figure([20,600,280,400])
    a=text('Right column',[310,680,590,500])
    b=text('Left column',[10,700,300,680])
    c=text('Next page',[10,700,300,680],2)
    result,warnings=images.place_figures([a,b,c,fig],[asset(fig)])
    assert [n['text'] for n in result]==['Right column','Left column','','Next page']
    assert result[2]['placement']=='page_end_unverified'
    assert warnings[0]['reason']=='ambiguous_reading_order'


def test_wrong_asset_is_rejected_and_missing_bytes_are_visible():
    fig=figure([20,600,280,400])
    wrong=asset(fig)|{'page':2}
    with pytest.raises(ValueError):
        images.place_figures([fig],[wrong])
    result,warnings=images.place_figures([fig],[asset(fig)|{'image_id':None,'error':'decode failed'}])
    assert len(result)==1 and result[0]['image_id'] is None
    assert any(w['reason']=='decode failed' for w in warnings)


def test_missing_image_reference_mutation_is_caught(monkeypatch):
    original=images.document_tree
    def broken(nodes,warnings):
        tree=original(nodes,warnings)
        for n in tree.nodes:
            n.image_id=None
        return tree
    monkeypatch.setattr(images,'document_tree',broken)
    with pytest.raises(AssertionError):
        test_figure_moves_to_gap_without_sorting_or_mutating_text()


def test_real_pdf_image_can_be_rendered_and_decoded(tmp_path):
    # Generated PDF fixture, independent of the detector/asset code under test.
    from PIL import Image
    import hashlib
    pdf=tmp_path/'image.pdf'
    with Image.new('RGB',(300,200),(10,80,150)) as source:
        source.save(pdf,'PDF',resolution=144)
    assets=images.extract_assets(pdf,tmp_path/'assets')
    assert len(assets)==1 and assets[0]['image_id'] and not assets[0]['error']
    path=tmp_path/'assets'/(assets[0]['image_id']+'.png')
    assert hashlib.sha256(path.read_bytes()).hexdigest()==assets[0]['image_id']
    with Image.open(path) as restored:
        assert restored.size==(300,200)
        assert max(abs(a-b) for a,b in zip(restored.convert('RGB').getpixel((150,100)),(10,80,150)))<=3
