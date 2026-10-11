"""Publish R6/R7 measurements and their non-promotion decision."""
from pathlib import Path
from collections import Counter
import hoc_tieu_de as base


def run():
    r6=base.read(base.ROOT/'tmp/a1-v414-r6-native-resolution/summary.json')
    gates=[base.read(base.ROOT/'tmp/a1-v414-r7'/name) for name in ('gate.json','gate-depth15.json')]
    target=base.ROOT/'report/v4-14-r6-r7-so-do-2026-10-07.json'
    if target.exists(): raise ValueError('Do not overwrite report')
    base.write(target,dict(native_assets=r6,page_gates=gates))
    lines=['# A1 R6–R7 — tài sản hình và giới hạn luồng lai','',
           'Đã kiểm đủ 19 sách, 0 USD API, không mở test/không thay artifact production.','',
           '## R6: trích bytes và đưa ImageRef vào chunk','',
           '855/855 đối tượng raster của detector cũ trích được PNG và có đúng 855 ImageRef downstream; 852 PNG khác nhau (66.877.058 byte).',
           '638 placement có khoảng dọc rõ, 217 chỉ giữ cuối đúng trang kèm cảnh báo chưa xác minh. Văn bản/source rows/bbox không bị sắp lại hoặc mất.',
           'Trích asset tổng 30,89 giây, **không phải thời gian parse A1**, không gồm nhận vector diagram hay bảng.','',
           '| Sách | Raster giữ/refs | Figure Docling | Table Docling | Khoảng dọc / chưa rõ |',
           '|---|---:|---:|---:|---:|']
    for b in r6['books']:
        c=b['placement_counts']
        lines.append(f"| {b['book']} | {b['native_figures']}/{b['image_refs']} | {b['docling_figures']} | {b['docling_tables']} | {c.get('vertical_gap',0)}/{c.get('page_end_unverified',0)} |")
    lines+=['', 'Không gọi 855/1.214 là recall: đối tượng raster và hình semantic khác đơn vị. Bản nhẹ còn không dựng 294 table mà Docling ghi trong nguồn.',
            'Kiểm ảnh d01-06 trang 22 cho thấy native raster chỉ là một phần đường nối, chữ/nhãn hóa học nằm ngoài raster. **ImageRef hợp lệ không chứng minh hình hoàn chỉnh.**',
            'PNG RGBA giữ alpha; nền tối của trình xem không phải nền ảnh trong PDF. Không flatten/đổi màu để giấu khác biệt.', '',
            '### Sửa lỗi chất lượng trong quá trình thử', '',
            '- Lượt `tmp/a1-v414-r6` trích theo kích thước trang ~72dpi, làm ảnh 144dpi 300×200 thành 150×100. Không chọn lượt này.',
            '- Test PDF thật tạo bằng PIL được chạy đỏ trước sửa; chuyển render ở native resolution có mask/ma trận, giới hạn dự toán allocation 25M pixels, test xanh.',
            '- Canonical `tmp/a1-v414-r6-native-resolution`: 0 lỗi decode/fallback pixel trên 19 sách. Toàn bộ PNG hash/đọc lại/kích thước và refs được assert.',
            '- 5 test ảnh gồm placement không đổi text, hai cột giữ cảnh báo, sai asset bị bác, mutation bỏ image_id và real-PDF độ phân giải.',
            '- Lượt đầu dùng context-manager không được PdfPage hỗ trợ đã thất bại trước đo; sửa bằng closing(), không giấu lần lỗi.', '',
            '## R7: cổng native cho trang cần bộ đọc chuyên dụng','',
            '| Sách | Trang | Fallback depth2/depth15 | Trang figure/table nguồn | Lọt depth2/depth15 |','|---|---:|---:|---:|---:|']
    for a,b in zip(gates[0]['books'],gates[1]['books'],strict=True):
        assert a['book']==b['book']
        lines.append(f"| {a['book']} | {a['pages']} | {a['fallback']}/{b['fallback']} | {a['known_complex_pages']} | {len(a['missed_known_pages'])}/{len(b['missed_known_pages'])} |")
    total=sum(b['pages'] for b in gates[1]['books'])
    fallback=sum(b['fallback'] for b in gates[1]['books'])
    lines+=['', f'Depth15: {fallback}/{total} trang phải dùng Docling ({100*fallback/total:.2f}%); phủ 1.047/1.047 trang có figure/table trong nhãn nguồn.',
            'Depth2 bỏ sót d01-04 trang 44: cấu trúc hóa học nằm trong Form lồng; depth2 không thấy path, depth5/15 có 17 path. Đã xem ảnh trang, không coi source figure là false positive chỉ để làm đẹp cổng.',
            'R7b thay depth sau khi xem lỗi là phân tích exploratory có ghi giao thức bổ sung, không phải test độc lập. Không tăng threshold hoặc whitelist ID cuốn.', '',
            '## Quyết định và việc chưa đạt','',
            '**Chưa tích hợp native/hybrid làm A1 mặc định.** Cổng có coverage tốt đối với bạc nhưng fallback hơn 80%, chưa giải quyết heading/chữ/cấp mục của phần còn lại. Không suy coverage này thành safety chứng nhận.',
            'Metadata caption v13 của R3b vẫn là phần production đã chứng minh tương thích; R6/R7 chỉ prototype/nghiên cứu.',
            'Bảng cần TableFormer/Docling hoặc thành phần chuyên dụng, sơ đồ cần layout/crop tổng hợp thay vì bitmap đơn; không dựng parser bảng ad hoc để chạy theo count.',
            'Tiếp tục R8 audit các dòng bị filter loại, vì kiểm R2/R4/R5/R6 trước đây chỉ bảo toàn dòng đã giữ. Không mở sách mới trước khi khép các lỗ hổng nội bộ.',
            'Theo scientific-critical-thinking: tách integrity, semantic quality và coverage; theo skill PDF: kiểm ảnh thực, giữ cảnh báo Poppler thiếu font Symbol/ArialUnicode khi render trang nguồn.', '',
            '[Giao thức R6](v4-14-r6-giao-thuc-2026-10-07.md) · [R7 và bổ sung](v4-14-r7-giao-thuc-2026-10-07.md) · [Snapshot](v4-14-r6-r7-so-do-2026-10-07.json)','']
    target.with_name('v4-14-r6-r7-ket-qua-2026-10-07.md').write_text('\n'.join(lines),encoding='utf-8')


if __name__=='__main__':
    run()
