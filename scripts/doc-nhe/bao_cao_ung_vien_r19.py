"""Publish combined candidate results; preservation is not semantic quality."""
import hoc_tieu_de as base


def run():
    source=base.ROOT/'tmp/a1-v414-r19/results.json'; data=base.read(source)
    output=base.ROOT/'report/v4-14-r19-so-do-2026-10-07.json'
    assert not output.exists()
    lines=['# A1 R19 — ứng viên ghép caption, ảnh và phân tầng','',
        '0 USD API, không refit, 19 sách phát triển. H2 d01-08 in-sample. Chưa promotion bộ nhẹ.',
        '', '| Sách | Trước ghép ảnh strict leaf | Sau ghép | Chunk | Ảnh refs | Formula refs | Vị trí chưa rõ |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for b in data['books']:
        s=b['models']['default']
        lines.append(f"| {b['id']} | {b['baseline_without_assets']['leaf_strict']['share']:.5f} | {s['leaf_strict']['share']:.5f} | {s['chunks']} | {s['image_refs']} | {s['formula_refs']} | {b['placement_counts'].get('page_end_unverified',0)} |")
    lines+=['','Mọi byte image_id khớp SHA-256 của asset PNG canonical R6. Hình học/source_figure khớp; toàn bộ node không phải figure giữ nguyên text/thứ tự/bbox. Ở mỗi nhánh, multiset ImageRef downstream bằng multiset ảnh có byte — kiểm số lần xuất hiện, không chỉ tập ID.',
        'Đổi vị trí hình làm thay ranh giới chunk: báo cả ca giảm (không chọn output theo điểm từng cuốn). Không diễn giải độ đồng thuận với chunk Docling là độ đúng semantic.',
        '', '## Cây sau lọc heading/caption','',
        '| Sách | Nhánh | Đúng cha/căn | Căn/nguồn | Đúng cha/nguồn | Cha chưa căn được |',
        '|---|---|---:|---:|---:|---:|']
    for b in data['books']:
        for v,s in b['models'].items():
            o=s.get('outline')
            if o: lines.append(f"| {b['id']} | {v} | {o['parent_hits']}/{o['matched']} | {o['matched']}/{o['reference_headings']} | {o['joint_hits_per_reference']:.5f} | {o['unmatched_parent_errors']} |")
    lines+=['','H2/H3 giải mã lại trên cùng tập heading qua guard, không chiếu cây cũ như R16. Model/luật cố định. Mọi strict leaf của ba nhánh giống nhau từng sách, nhưng bảng cha khác: metric lá không đủ chọn cây.',
        '', '## Ranh giới đã kiểm và chưa đạt','',
        '- Đã ghép bảo toàn dòng, lọc caption hình học, ảnh native có byte/ref, cây tường minh và chunk. Có test kết hợp cho caption không trở thành mục cha và ảnh vẫn có ref, ngoài assert 19 cuốn.',
        '- R6 chỉ phát hiện raster kích thước đủ lớn. Chưa dựng bảng semantic, không bảo đảm sơ đồ vector/layer chữ đã thành ảnh hoàn chỉnh. Vị trí không rõ vẫn có cảnh báo, không gán confidence giả.',
        '- Hierarchy vẫn phụ thuộc nhận heading/nhóm đa dòng và nhãn outline yếu; đã có bằng chứng outline sai ở R17. Không dùng d01-08 in-sample để chọn mô hình tổng quát.',
        '- Không phải benchmark tốc độ parse mới: đây là inference/grouping từ dòng và ảnh đã cache. Không dùng thời gian này hứa số phút/cuốn.',
        '- Cây nằm ở `tmp/a1-v414-r19/trees/<book>/{default,H2,H3}.json`, ảnh trỏ ID tới `tmp/a1-v414-r6-native-resolution/images/`. Đây là bundle nghiên cứu nội bộ, không artifact production tự chứa.',
        '- Production vẫn Docling adapter 13. Phần đã tích hợp trong lượt này chỉ là hợp đồng API declared-v1 với cache/test hồi quy; không tự bật light parser khi các cổng chất lượng còn thiếu.',
        '', '[Giao thức](v4-14-r19-giao-thuc-2026-10-07.md) · [Snapshot](v4-14-r19-so-do-2026-10-07.json).']
    base.write(output,data)
    output.with_name('v4-14-r19-ket-qua-2026-10-07.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


if __name__=='__main__': run()
