"""Publish frozen measurements without changing scoring or source artifacts."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def run():
    combined={}
    for round_id in (20,21,22,23):
        source=ROOT/f'tmp/a1-v414-r{round_id}/results.json'
        data=json.loads(source.read_text(encoding='utf-8')); combined[round_id]=data
        target=ROOT/f'report/v4-14-r{round_id}-so-do-2026-10-08.json'
        assert not target.exists()
        target.write_text(json.dumps(data,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
    lines=['# A1 R20–R23 — chương, chữ trong hình và cây sau ghép','',
        '19 sách phát triển đã xem; không phải kiểm mù. 0 USD API, không fit lại model, không mở sách test.',
        'Các phép đo dùng cùng nhãn bạc/metric cũ; không chọn nhánh riêng theo ID sách.',
        '', '## Đối chiếu strict leaf','',
        '| Sách | R19 | R20 nối chương | R21 vai trò trong hình | R22 mã bài | R23 H3 |',
        '|---|---:|---:|---:|---:|---:|']
    for i,b in enumerate(combined[20]['books']):
        values=[b['models']['existing'],b['models']['chapter'],combined[21]['books'][i]['models']['roles'],
                combined[22]['books'][i]['models']['metadata'],combined[23]['books'][i]['models']['H3']]
        assert all(combined[r]['books'][i]['id']==b['id'] for r in combined)
        lines.append('| '+b['id']+' | '+' | '.join(f"{v['leaf_strict']['share']:.5f}" for v in values)+' |')
    lines+=['','## Can thiệp và giới hạn','',
        '- R20 nối 27 cặp trên 4 sách. Strict leaf giảm ở d01-01, doc-1, doc-4; 16 sách giữ nguyên. Không gọi mọi cặp là tên hoàn chỉnh: p176 d01-01 còn thiếu dòng cuối có superscript; p36 d01-06 lẫn mã bài đã chuyển sang R22.',
        '- R21 đổi 4 heading: ba caption nằm trong raster d01-08 p42/59/64; một nhãn sơ đồ d01-14 p227. D01-08 tăng 514→516/676; 18 sách không đổi. Nhãn p232 d01-14 vẫn chưa sửa vì không qua ngưỡng cỡ chữ đã đóng trước đo; không nới ngưỡng sau khi nhìn kết quả.',
        '- R22 tách hai dòng Mã bài ở d01-06 p18/36 khỏi tên chương, giữ nội dung body. 19/19 strict leaf không đổi; metric lá không đo đầy đủ chất lượng tên chương.',
        '- Đã xem PDF gốc ở chín trang: d01-08 p42/59/64, d01-14 p227/232, d01-06 p18/36, d01-01 p176, doc-1 p16. Ba caption d01-08 không hiện trên ảnh kết xuất; chưa kết luận cơ chế che chữ. Poppler báo thiếu font Symbol/ArialUnicode: các ảnh không chứng minh toàn bộ glyph toán đúng.',
        '- Mỗi nhánh giữ 855 ImageRef và 13178 FormulaRef (số lần xuất hiện downstream, không phải số công thức độc lập). Kiểm partition nguồn, text và bbox trên đủ 19 sách. R23 còn kiểm multiset ID ảnh/công thức và toàn bộ parent_section_id đầu ra; không chỉ assert cờ của thuật toán.',
        '', '## Cha–con sau ghép','',
        '| Sách | Nhánh | Đúng cha/căn được | Căn được/outline gốc |',
        '|---|---|---:|---:|']
    for b in combined[23]['books']:
        for name,score in b['models'].items():
            if 'outline' in score:
                o=score['outline'];lines.append(f"| {b['id']} | {name} | {o['parent_hits']}/{o['matched']} | {o['matched']}/{o['reference_headings']} |")
    lines+=['','Outline là nhãn yếu, đã có ca phẳng không phản ánh PDF. R20 đổi tên chương nên phép căn exact-match cũ có thể giảm coverage. Không đổi phép căn và không coi điểm ở phần căn được là accuracy toàn A1.',
        '', '## Trạng thái và bước kế tiếp','',
        'Chưa bật bộ nhẹ thay Docling. Production adapter 13 và cấu hình không đổi trong đợt R20–R23. LightGBM M2f/B2 vẫn giữ nguyên; H3 là bộ giải cây dựa trên số mục/style, không phải một model mới thắng mọi sách.',
        'Điểm mở có bằng chứng: tên chương kèm công thức inline, chữ sơ đồ ngoài raster/không đủ ngưỡng, reading order, bảng semantic và vector graphics; 221 vị trí ảnh chưa xác minh không được xoá cảnh báo. Nhãn/sách độc lập làm sau theo chủ dự án.',
        'Các output dưới tmp là nghiên cứu nội bộ, không phải artifact production tự chứa. Không dùng thời gian replay từ cache để hứa thời gian parse một cuốn mới.',
        '', 'Giao thức và số đo từng vòng được giữ riêng trong report/v4-14-r20…r23-*. Không commit lẫn các thay đổi khác trong worktree.']
    target=ROOT/'report/v4-14-r20-r23-ket-qua-2026-10-08.md'
    assert not target.exists();target.write_text('\n'.join(lines)+'\n',encoding='utf-8')


def publish24():
    source=ROOT/'tmp/a1-v414-r24/results.json'
    data=json.loads(source.read_text(encoding='utf-8'))
    target=ROOT/'report/v4-14-r24-so-do-2026-10-08.json'
    assert not target.exists()
    target.write_text(json.dumps(data,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')


def publish25():
    from collections import Counter
    data=json.loads((ROOT/'tmp/a1-v414-r25/results.json').read_text(encoding='utf-8'))
    target=ROOT/'report/v4-14-r25-so-do-2026-10-08.json';assert not target.exists()
    target.write_text(json.dumps(data,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
    counts=Counter();lines=['# R25 — đặt raster theo body ngoài, không giấu cảnh báo chữ nội hình','',
        '19 sách phát triển, 0 USD API. Không refit, không đổi production, không mở test books.',
        '', '| Sách | Anchor mới | Còn fallback cuối trang | Strict leaf trước | Sau |',
        '|---|---:|---:|---:|---:|']
    for b in data['books']:
        counts.update(b['placements']);old=b['models']['existing'];new=b['models']['placement']
        lines.append(f"| {b['id']} | {len(b['moved'])} | {b['placements'].get('page_end_unverified',0)} | {old['leaf_strict']['share']:.5f} | {new['leaf_strict']['share']:.5f} |")
    lines+=['',f"Tổng: {counts['vertical_gap']} khe dọc cũ; {counts['external_vertical_gap']} anchor theo body ngoài; {counts['page_end_unverified']} fallback chưa định vị.",
        'Mỗi anchor mới vẫn có `embedded_text_order_unverified`. Không nói tổng số hình có vấn đề đã từ 221 xuống 166: 55 ca chuyển loại cảnh báo, chưa được chấm thứ tự chữ trong hình.',
        '', 'Đã xem PDF d01-03 p19 (hình orbital trước caption), d01-05 p12 (cellulose trước footer), d01-06 p45 (callus trước caption/body tiếp); d01-08 p42 đã xem từ R21. Đây là kiểm chẩn đoán có chủ đích, không phải mẫu ngẫu nhiên chứng minh 55/55 đúng. Poppler có cảnh báo font Symbol/ArialUnicode.',
        '', 'Kiểm độc lập: toàn bộ node không phải hình giữ nguyên text/thứ tự/bbox; multiset ImageRef và FormulaRef downstream bằng R24 từng ID. Tổng 855 ảnh refs, 13177 formula refs. Không biến ảnh có vector/chữ lớp ngoài thành bitmap hoàn chỉnh ở vòng này.',
        '', 'Test đỏ trước sửa: ảnh vẫn nằm sau body tiếp theo. Sau sửa 6 test đạt, gồm ảnh lớn, heading nằm trong ảnh, ảnh chồng, không có body ngoài, thứ tự ngoài không tạo khe. Toàn nhóm A1/heading ML sau R25: 147 passed, 21 deselected.',
        '', '[Giao thức](v4-14-r25-giao-thuc-2026-10-08.md) · [Số đo](v4-14-r25-so-do-2026-10-08.json) · [R24](v4-14-r24-ket-qua-2026-10-08.md).',
        '', 'R25 dùng nhánh default của R24. Không tự suy ra H3 R23 đã được đo lại trên R25. Chưa thay Docling; toàn A1 chưa nghiệm thu vì bảng semantic, vector graphics, reading order và hierarchy độc lập còn mở.']
    (ROOT/'report/v4-14-r25-ket-qua-2026-10-08.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


if __name__=='__main__':
    import sys
    if sys.argv[1:]==['--r24']:publish24()
    elif sys.argv[1:]==['--r25']:publish25()
    else:run()
