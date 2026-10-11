import importlib.util
from contextlib import closing
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('d02_packets',ROOT/'scripts/a1-d02/xuat_phieu.py')
packets=importlib.util.module_from_spec(spec);spec.loader.exec_module(packets)


def make_pdf(path,content=None,font='Helvetica',image=False,bookmark=False):
    content=content or 'BT /F1 12 Tf 30 150 Td (Chapter 1) Tj 0 -20 Td (A body line.) Tj ET'
    objects=[b'<< /Type /Catalog /Pages 2 0 R >>',b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
        ('<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] /Resources << /Font << /F1 4 0 R >> '+
         ('/XObject << /I 6 0 R >> ' if image else '')+'>> /Contents 5 0 R >>').encode(),
        f'<< /Type /Font /Subtype /Type1 /BaseFont /{font} >>'.encode(),
        f'<< /Length {len(content)} >>\nstream\n{content}\nendstream'.encode()]
    if image:objects.append(b'<< /Type /XObject /Subtype /Image /Width 1 /Height 1 /ColorSpace /DeviceRGB /BitsPerComponent 8 /Length 3 >>\nstream\n\xff\xff\xff\nendstream')
    if bookmark:
        assert not image
        objects[0]=b'<< /Type /Catalog /Pages 2 0 R /Outlines 6 0 R >>'
        objects += [b'<< /Type /Outlines /First 7 0 R /Last 7 0 R /Count 1 >>',
                    b'<< /Title (Chapter 1) /Parent 6 0 R /Dest [3 0 R /Fit] >>']
    payload=b'%PDF-1.4\n';offsets=[0]
    for i,obj in enumerate(objects,1):
        offsets.append(len(payload));payload+=f'{i} 0 obj\n'.encode()+obj+b'\nendobj\n'
    xref=len(payload);payload+=f'xref\n0 {len(objects)+1}\n0000000000 65535 f \n'.encode()
    payload+=b''.join(f'{p:010} 00000 n \n'.encode() for p in offsets[1:])
    payload+=f'trailer\n<< /Root 1 0 R /Size {len(objects)+1} >>\nstartxref\n{xref}\n%%EOF'.encode()
    path.write_bytes(payload)


def test_packet_line_ids_and_each_letter_survive_two_extractions(tmp_path):
    path=tmp_path/'book.pdf';make_pdf(path)
    with packets.light.pdfium.PdfDocument(path) as pdf:
        with closing(pdf[0]) as page:
            first=packets.page_rows(page,1);second=packets.page_rows(page,1)
    assert first==second
    assert [r['id'] for r in first]==['p0001-l001','p0001-l002']
    assert ''.join(c for r in first for c in r['text'] if c.isalpha())=='ChapterAbodyline'


def test_l2_strata_are_seeded_unique_and_have_fallbacks():
    rows=[dict(trang=p,text='Chương 1' if p==2 else 'body') for p in range(1,11)]
    features={p:dict(table_hint=p==3,image=p==4,math_hint=p==5) for p in range(1,11)}
    first=packets.select_pages(rows,features,10)
    assert first==packets.select_pages(rows,features,10)
    assert len(first['trang'])==8 and len(set(first['trang']))==8
    strata={s['loai']:s['trang'] for s in first['phan_tang']}
    assert [strata[k] for k in ('mo_chuong','bang','hinh','cong_thuc','cuoi_sach')]==[2,3,4,5,10]
    assert packets.select_pages(rows[:2],{p:features[p] for p in (1,2)},2)['trang']==[1,2]


def test_real_packet_layout_and_bookmark_empty_are_exported(tmp_path):
    path=tmp_path/'book.pdf';make_pdf(path)
    result=packets.export(path,'book',tmp_path/'out')
    assert result['dong']==2 and result['complete']
    out=tmp_path/'out'
    assert (out/'trang/book/p0001.png').read_bytes().startswith(b'\x89PNG')
    assert (out/'muc_luc_dien_tu/book.json').read_text().strip()=='[]'
    assert (out/'kiem_nhan_d02.py').exists() and (out/'chon-trang-mau/book.json').exists()


def test_pdf_bookmark_destination_is_exported(tmp_path):
    import json
    path=tmp_path/'book.pdf';make_pdf(path,bookmark=True)
    packets.export(path,'book',tmp_path/'out')
    data=json.loads((tmp_path/'out/muc_luc_dien_tu/book.json').read_text())
    assert data==[dict(text='Chapter 1',cap=1,trang=1)]
