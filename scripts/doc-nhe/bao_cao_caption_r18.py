"""Publish all caption-veto interventions, including silver-positive changes."""
from collections import Counter
import hoc_tieu_de as base


def run():
    source=base.ROOT/'tmp/a1-v414-r18/results.json'; data=base.read(source)
    output=base.ROOT/'report/v4-14-r18-so-do-2026-10-07.json'
    assert not output.exists()
    changes=[r for b in data['books'] for r in b['changed']]
    labels=Counter((r['r1'],r['r3']) for r in changes)
    lines=['# A1 R18 — caption có hình phía trên','',
        '0 USD API, 19 sách phát triển, không train và không mở test. Model M2f+B2/threshold cố định, baseline R13 tái hiện đúng toàn bộ bốn nhóm metric.',
        '', '| Sách | Đủ hình học / đổi cờ | Heading F1 cũ → mới | Strict leaf cũ → mới |',
        '|---|---:|---:|---:|']
    better=worse=0
    for b in data['books']:
        a,c=b['models']['existing'],b['models']['caption']
        before,after=a['leaf_strict']['share'],c['leaf_strict']['share']
        better+=after>before; worse+=after<before
        lines.append(f"| {b['id']} | {b['qualified']}/{len(b['changed'])} | {a['heading_strict']['f1']:.5f} → {c['heading_strict']['f1']:.5f} | {before:.5f} → {after:.5f} |")
    lines+=['',f'Đổi {len(changes)} cờ heading; {better} cuốn tăng strict leaf, {worse} cuốn giảm, {len(data["books"])-better-worse} không đổi.',
        'Hai test hình học đỏ khi chưa có luật rồi xanh. Có kiểm không hình, khác trang, xa, không phủ ngang, chữ chen và tên Hình học/Bảng không đủ điều kiện. Hàm không sửa rows; verifier source rows/text/bbox/order chạy cả baseline lẫn can thiệp.',
        '', '## Audit nhãn bạc ở dòng đổi cờ','', '| R1 | R3 | Số dòng |', '|---:|---:|---:|']
    for (a,b),n in sorted(labels.items()): lines.append(f'| {a} | {b} | {n} |')
    lines+=['','1 = heading bạc; 0 = âm bạc; -1 = unknown. Không đổi unknown thành âm để tuyên bố precision. Danh sách đầy đủ text/page/index nằm trong snapshot.',
        'Đã xem ảnh nguồn d01-08 trang PDF 177 và 179: Hình 0-6 (FIFO) và Hình 0-9 (LRU) nằm dưới sơ đồ; trang 179 còn có heading thật V.3 ở trên. Hai dòng caption này có nhãn heading dương ở cả R1/R3. Đây là hai phản ví dụ cụ thể của nhãn bạc, đề xuất agent không tự ghi đè dataset. Poppler cảnh báo font Symbol/ArialUnicode, chữ caption đang kiểm vẫn rõ.',
        '', '## Giới hạn và quyết định','',
        '- Luật thăm dò sau xem d01-08 p6; đây không phải kiểm mù. Không tự gọi mọi cờ sửa là caption thật. Raster bbox có thể là phần hình/ảnh trang hoặc trang trí; cần audit hình với caption.',
        '- Chỉ ảnh raster phía trên có khoảng cách/phủ ngang phù hợp. Chưa xử lý caption trên hình, bảng/vector, nhiều dòng caption, hoặc nhãn inside-diagram.',
        '- Cờ false giữ chữ trong bố cục (caption/text tùy classifier cũ), không phải đã gắn caption semantic vào ImageRef. Không chặn formula hoặc monospace.',
        '- Giữ prototype; chưa thay Docling hoặc tự bật ở production. Cần nối với phân tầng và kiểm ảnh/bảng/reading order trước quyết định toàn A1.',
        '- Lượt evaluator đầu dừng vì so dictionary thiếu full_raw, chưa xuất số; đã bổ sung đúng metric raw vào cả hai nhánh, giữ assertion bằng nguyên dictionary, không bỏ kiểm bất lợi.',
        '', '[Giao thức](v4-14-r18-giao-thuc-2026-10-07.md) · [Snapshot](v4-14-r18-so-do-2026-10-07.json).']
    images=list((base.ROOT/'tmp/pdfs/a1-r18').glob('*.png'))
    assert len(images)==2
    data['visual_review']=dict(status='agent_proposals_not_gold_not_training',book='d01-08',pages=[177,179],
        png_sha256={str(p.relative_to(base.ROOT)):base.digest(p) for p in images})
    base.write(output,data)
    output.with_name('v4-14-r18-ket-qua-2026-10-07.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


if __name__=='__main__': run()
