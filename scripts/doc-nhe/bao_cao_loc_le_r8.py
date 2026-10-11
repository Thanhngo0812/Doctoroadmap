"""Publish complete R8 margin ablation, including regressions and raw denominators."""
from collections import Counter
import statistics
import hoc_tieu_de as base


def run():
    output=base.ROOT/'report/v4-14-r8-so-do-2026-10-07.json'
    assert not output.exists(), 'Do not overwrite a published measurement'
    variants={}
    for variant,folder in [('b','a1-v414-r8-model'),('c','a1-v414-r8c-model')]:
        root=base.ROOT/'tmp'/folder
        data=[base.read(p) for p in sorted((root/'datasets').glob('*.json'))]
        models={p.stem:base.read(p) for p in sorted((root/'models').glob('*.json'))}
        for record in models.values():
            for prediction in record['predictions'].values():
                del prediction['probability']
        variants[variant]=dict(protocol=base.read(root/'protocol.json'),training=base.read(root/'training.json'),
                               e2e=base.read(root/'e2e.json'),models=models,
                               dataset_sha256={p.name:base.digest(p) for p in sorted((root/'datasets').glob('*.json'))},
                               recovered=sum(len(d['recovered']) for d in data),
                               newly_dropped=sum(len(d['newly_dropped']) for d in data),
                               recovered_labels={str(k):v for k,v in Counter((r['r1'],r['r3']) for d in data for r in d['recovered']).items()},
                               removed_from_b=[dict(book=d['book']['id'],**r) for d in data for r in d.get('removed_from_b',[])])
    base.write(output,dict(api_usd=0,status='development_not_production',
                           audit=base.read(base.ROOT/'tmp/a1-v414-r8/summary.json'),variants=variants))
    lines=['# A1 R8 — không để bộ lọc xóa nội dung trước LightGBM','',
           'Audit 128.320 raw rows của 19 PDF ghim: lọc cũ giữ 124.208, bỏ 4.112.',
           'Đã xem ảnh xác nhận tiêu đề chương d01-03 p6, câu hỏi chương d01-05 p30 và hàng ma trận doc-1 p27 bị mất.',
           'Không dùng nhãn nguồn để giữ/xóa tự động: nhiều header/footer cũng bị Docling gán text/heading sai.','',
           '## Thay đổi và phạm vi','',
           '- R8b: exact text/style/vị trí và mật độ trang; số trang integer đơn có offset nhất quán. Giữ lại 667 dòng, không xóa thêm dòng cũ.',
           '- R8c: nhận thêm số trang dính đầu/cuối running text qua cùng offset/style trên ≥5 trang. Loại lại 341 dòng (đều unknown theo hai căn nhãn), giữ thêm 326 dòng so cũ; vẫn không xóa thêm dòng nào cũ đang giữ.',
           '- 326 dòng gồm 31 heading và 7 nonheading được cả R1/R3 căn, 16 chỉ R1 nonheading, 272 unknown. Không gọi unknown là nội dung đúng hay rác; doc-1 có nhiều mảnh dấu ngoặc ma trận/glyph cần tái dựng công thức.',
           '- Giữ nguyên M2: 73 features, 300 cây, 15 lá, min-child30, seed42, threshold0,5. Mỗi nhánh 27 fit; training corpus/context thay đổi, đây không phải chỉ đổi filter với trọng số model cố định.',
           '- 16 LOBO + 10 nhóm nguồn + full16/3 kiểm ngoài cũ. Không mở test mới, không gọi API, không thay parser production.','',
           '## F1 tiêu đề trên cùng toàn raw-row universe','',
           'Heading bị lọc tính là dự đoán âm; unknown vẫn loại khỏi F1. Không so mẫu số đã lọc khác nhau.','',
           '| Nhãn | Mốc cũ median/min | R8b median/min | R8c median/min |','|---|---:|---:|---:|']
    for label in ('r1','r3'):
        cells=[]
        for v,side in [('b','old'),('b','new'),('c','new')]:
            books=[r for r in variants[v]['e2e']['books'] if r['split']=='train']
            scores=[r['full_raw'][label][side]['f1'] for r in books]
            cells.append(f'{statistics.median(scores):.6f}/{min(scores):.6f}')
        lines.append('| '+label+' | '+' | '.join(cells)+' |')
    lines+=['','## Chunk/heading — median 16 sách','',
            '| Phép đo | Cũ | R8b | R8c |','|---|---:|---:|---:|']
    for metric,field in [('heading_strict','f1'),('leaf_strict','share'),('chunk_legacy','cung_muc_la'),('chunk_legacy','docling_co_ban_tu_0_8')]:
        cells=[statistics.median(r[side][metric][field] for r in variants[v]['e2e']['books'] if r['split']=='train')
               for v,side in [('b','old'),('b','new'),('c','new')]]
        lines.append('| '+metric+'/'+field+' | '+' | '.join(f'{x:.6f}' for x in cells)+' |')
    lines+=['','| Sách | Strict leaf cũ | R8b | R8c |','|---|---:|---:|---:|']
    for b,c in zip(variants['b']['e2e']['books'],variants['c']['e2e']['books'],strict=True):
        assert b['id']==c['id']
        lines.append(f"| {b['id']} | {b['old']['leaf_strict']['share']:.6f} | {b['new']['leaf_strict']['share']:.6f} | {c['new']['leaf_strict']['share']:.6f} |")
    lines+=['','## Quyết định và kiểm chứng','',
            '**Không promotion toàn bộ R8/M2.** Bảo toàn nội dung đã sửa đúng các phản ví dụ, nhưng chunk doc-1 giảm 0,61809→0,41206 và d01-01 giảm 0,65054→0,54839; không giấu bằng median.',
            'R8c là nhánh bảo toàn để phát triển tiếp; việc gom công thức/heading sau khôi phục dòng chưa đủ tốt. Không quay lại xóa nội dung hợp lệ chỉ để tăng tương đồng Docling.',
            '10 test bộ lọc đạt, đã thấy 2 test mới đỏ trên R8b rồi xanh ở R8c. Regression 990 đạt/3 skip ML/8 integration deselected; không đổi src trong R8.',
            'R2 verify_nodes xác nhận toàn bộ dòng giữ lại có text/bbox/thứ tự đúng ở đầu ra 19 sách. Chứng minh này không xác nhận reading order semantic hay glyph chính xác.',
            'Phép đo chunk dùng cached rows, không tuyên bố tốc độ PDF→cây từ thời gian này. Cả R8b/c fit và đo đã kết thúc.',
            'R8c exploratory sau thấy nhược điểm R8b; không coi là kiểm xác nhận độc lập. Chưa có nhãn vàng chuyên gia/toàn bộ A1.',
            '', '[Giao thức R8a/b](v4-14-r8-giao-thuc-2026-10-07.md) · [Giao thức R8c](v4-14-r8c-giao-thuc-2026-10-07.md) · [Số/hashes đầy đủ, cả publisher và external](v4-14-r8-so-do-2026-10-07.json)','']
    output.with_name('v4-14-r8-ket-qua-2026-10-07.md').write_text('\n'.join(lines),encoding='utf-8')


if __name__=='__main__':
    run()
