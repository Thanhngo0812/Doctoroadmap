"""Publish R17 results and explicitly separated visual review proposals."""
import hoc_tieu_de as base


def run():
    source=base.ROOT/'tmp/a1-v414-r17/results.json'
    data=base.read(source)
    earlier=base.read(base.ROOT/'tmp/a1-v414-r14b/results.json')
    lookup={(f['book'],f['group']):f for f in earlier['folds']}
    lines=['# A1 R17 — sửa số mục hỗn hợp, không nhận toàn A1','',
        '0 USD API; không train thêm; không mở sách test. Hai test phản ví dụ đỏ trên H1, xanh với H3.',
        '', '## Cùng tập tiêu đề outline','',
        '| Sách/nhánh | N | H1 đúng cha | H2 đúng cha | H3 đúng cha | H3 ancestor F1 |',
        '|---|---:|---:|---:|---:|---:|']
    for f in data['folds']:
        prior=lookup[f['book'],f['group']]; s=f['H3']
        lines.append(f"| {f['book']}/{f['group']} | {s['headings']} | {prior['H1']['parent_hits']} | {prior['H2']['parent_hits']} | {s['parent_hits']} | {s['ancestor_f1']:.5f} |")
    lines+=['','H3 đọc III.1/VI.2.1 thành số mục nhiều cấp và nhận chữ C. theo dãy A/B cùng style. doc-4 tăng H1 139→H3 142/171 trên tập chỉ-heading. Đây là sửa sau xem lỗi development, không phải kết quả blind test.',
        '', '## Đầu-cuối với tiêu đề dự đoán','',
        '| Sách | Heading qua guard | Strict leaf | Path với Docling | Outline đúng cha/căn |',
        '|---|---:|---:|---:|---:|']
    for b in data['books']:
        s=b['H3']; o=s.get('outline')
        lines.append(f"| {b['id']} | {b['accepted']} | {s['leaf_strict']['share']:.5f} | {s['path_strict']['share']:.5f} | "+(f"{o['parent_hits']}/{o['matched']}" if o else '—')+' |')
    lines+=['','Toàn bộ text chunk/thứ tự và strict leaf giống baseline R16, kiểm bằng assertion. H3 chạy sau guard. H1/H2 R16 là chiếu cây đã giải mã trước guard, nên không quy chênh toàn luồng chỉ cho sửa prefix; phép so H1/H3 trên cùng outline phía trên mới cô lập rule.',
        'Doc-4 toàn luồng đúng 123/158 heading căn được (nguồn 171); d01-08 113/271. Còn sai nhiều, không promotion. Không chọn H2 cho riêng d01-08 và H3 riêng doc-4 để làm đẹp bảng.',
        '', '## Kiểm ảnh nguồn — đề xuất của agent, không phải nhãn vàng','',
        '- Đã xem đủ trang PDF doc-4 39, 77 và d01-08 5, 6, 48. Năm PNG, hash nằm trong snapshot. Poppler cảnh báo thiếu display font Symbol/ArialUnicode ở d01-08; chữ heading được kiểm vẫn nhìn rõ. Không đánh giá độ đúng mọi glyph/formula từ render này.',
        '- doc-4 p39: C. là mục lớn phía trên I-; củng cố phản ví dụ chữ cái/La Mã. Chỉ trang này không xác nhận toàn bộ chuỗi A/B/C, chuỗi đó có trong dữ liệu dòng đối chứng.',
        '- doc-4 p77: Phần II có tiêu đề lớn, phía dưới là Chương V / Vật chất và ý thức rồi I- và 1. Outline đã căn lại ghi Phần II, Chương V, Vật chất và ý thức đều là root. Ảnh cho bằng chứng không thể coi nhãn outline phẳng là vàng; tên chương cũng bị tách khỏi số chương. Không sửa nhãn để tự tăng điểm model.',
        '- d01-08 p5–6: III Hệ điều hành là gì? rồi III.1 Tầm nhìn người dùng ở trang sau. Có hình và caption Hình 0-1 ở giữa, không phải mục cha của III.1.',
        '- d01-08 p48: VI.2 Đặt tên chứa VI.2.1 Giao tiếp trực tiếp; số hỗn hợp phản ánh phân cấp thật, không phải chỉ dấu khác style.',
        '', '## Quyết định','',
        'Giữ H3 là đối chứng prototype. Production chỉ nhận hợp đồng truyền cây R14c đã kiểm, mặc định vẫn Docling adapter 13. Đã có sửa hữu ích nhưng **chưa có bằng chứng bản nhẹ đạt toàn A1**.',
        'Bước tiếp theo có giá trị hơn tăng cây: kiểm/sửa ontology và nhãn cha–con đa sách bằng ảnh; tách caption/nội dung sơ đồ khỏi heading; nối nhãn chương với tên chương; kiểm bảng/reading order và ảnh semantic. Nhãn agent phải lưu tách và không vừa dùng fit vừa tuyên bố kiểm độc lập. Sách mới/kiểm độc lập vẫn làm cuối theo yêu cầu chủ dự án.',
        'Không nâng ngân sách, không gửi PDF ra dịch vụ, không ghi đè output cũ, chưa commit lẫn worktree.',
        '', '[Giao thức](v4-14-r17-giao-thuc-2026-10-07.md) · [Snapshot](v4-14-r17-so-do-2026-10-07.json).',
        'Skill PDF hỗ trợ kiểm bố cục thật; scientific-critical-thinking giữ nhãn yếu/đề xuất agent tách khỏi vàng và không chọn nhánh theo sách.']
    images=list((base.ROOT/'tmp/pdfs/a1-r17').glob('*.png'))
    assert len(images)==5
    data['visual_review']=dict(status='agent_proposals_not_gold_not_training',pages={'doc-4':[39,77],'d01-08':[5,6,48]},
        png_sha256={str(p.relative_to(base.ROOT)):base.digest(p) for p in images})
    data['source_sha256']=base.digest(source)
    output=base.ROOT/'report/v4-14-r17-so-do-2026-10-07.json'
    assert not output.exists()
    base.write(output,data)
    output.with_name('v4-14-r17-ket-qua-2026-10-07.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


if __name__=='__main__': run()
