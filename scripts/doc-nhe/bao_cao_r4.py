"""Export every R4 book/source metric and concise Markdown, including regressions."""
import argparse
from pathlib import Path
import statistics
import hoc_tieu_de as base


def run(out):
    summary, e2e = base.read(out/'summary.json'), base.read(out/'e2e.json')
    target = base.ROOT/'report/v4-14-r4-so-do-2026-10-07.json'
    if target.exists():
        raise ValueError('Do not overwrite a published measurement')
    base.write(target,dict(classification=summary,end_to_end=e2e))
    results = summary['results']
    lines = ['# A1 R4 — LightGBM morphology/style và nhãn bạc', '',
             'Đã hoàn tất 81 fit mới + tái dùng 27 M2 đối chứng; 19 sách phát triển đã xem, không có test mù mới. 0 USD API.', '',
             '## Kết luận', '',
             '**Không thay M2/Docling bằng E2 trong sản phẩm.** E2 cải thiện min F1 dòng nhưng trung vị chunk giảm; tăng số cây/đặc trưng không đủ.',
             'E3 căn nhãn chặt hơn không cải thiện đồng đều. Không chọn mặt nạ R3 để che giảm trên R1, không gọi score là xác suất đúng.', '',
             '## Phân loại dòng', '',
             '| Model | R1 LOBO median/min | R3 LOBO median/min | R1 nguồn median/min | Fit giây |',
             '|---|---:|---:|---:|---:|']
    for v,r in results.items():
        s=r['summary']
        values=[s['lobo']['r1'],s['lobo']['r3'],s['publisher']['r1']]
        lines.append('| '+v+' | '+' | '.join(f"{a['median_f1']:.4f}/{a['minimum_f1']:.4f}" for a in values)+f" | {r['fit_seconds']:.1f} |")
    lines += ['', 'R1/R3 là hai phép đối chiếu nhãn bạc trên cùng dòng, không phải hai thử nghiệm độc lập. Cả hai đều có lỗi nguồn.',
              'M2 thời gian fit là số lịch sử, không đo cùng tải máy R4. E1/E2/E3 tổng thời gian fit không bao gồm feature extraction/chấm.', '',
              '| Sách | M2 R1 | E1 R1 | E2 R1 | E3 R1 |', '|---|---:|---:|---:|---:|']
    for b in e2e['books']:
        key=b['id']
        vals=[next(x for x in r['rows'] if x['book']==key and not x['split'].startswith('publisher'))['r1']['f1'] for r in results.values()]
        lines.append('| '+key+' | '+' | '.join(f'{x:.4f}' for x in vals)+' |')
    lines += ['', 'Giữ riêng nguồn: E2 yếu nhất d01-15 F1 0,4365. Đây là tín hiệu phụ thuộc mẫu trình bày nguồn, không được giấu sau LOBO median.', '',
              '## Đầu-cuối cùng grouping R2 và chunker', '',
              '| Sách | Strict heading M2/E2 | Strict leaf M2/E2 | Jaccard≥0,8 M2/E2 | Giây/trang M2/E2 |',
              '|---|---:|---:|---:|---:|']
    for b in e2e['books']:
        a,c=[b['models'][v] for v in ('M2','E2')]
        lines.append(f"| {b['id']} | {a['heading_strict']['f1']:.4f}/{c['heading_strict']['f1']:.4f} | {a['leaf_strict']['share']:.4f}/{c['leaf_strict']['share']:.4f} | {a['chunk_legacy']['docling_co_ban_tu_0_8']:.3f}/{c['chunk_legacy']['docling_co_ban_tu_0_8']:.3f} | {a['seconds_per_page']:.4f}/{c['seconds_per_page']:.4f} |")
    train=[b for b in e2e['books'] if b['split']=='train']
    lines += ['', 'Trung vị 16 sách:', '']
    for v in ('M2','E2'):
        m=[b['models'][v] for b in train]
        lines.append(f"- {v}: strict heading {statistics.median(x['heading_strict']['f1'] for x in m):.6f}; strict leaf {statistics.median(x['leaf_strict']['share'] for x in m):.6f}; legacy leaf {statistics.median(x['chunk_legacy']['cung_muc_la'] for x in m):.4f}; Jaccard≥0,8 {statistics.median(x['chunk_legacy']['docling_co_ban_tu_0_8'] for x in m):.4f}.")
    lines += ['', 'Mỗi model/sách đọc mới PDF ba lần, gồm trích dòng, features, suy luận và grouping; kiểm cây bằng replay OOF đã lưu.',
              'Không gồm cold import/model load, chunking/chấm hoặc table/image asset extraction. Thời gian từng lần, hash, RAM đỉnh tiến trình và size model có trong JSON.',
              'Bộ đọc vẫn thiếu bảng/asset bytes và thứ tự hình ở cuối. Kiểm bảo toàn chỉ trên dòng/hình detector cũ đã giữ, không chứng minh đủ mọi phần của PDF.', '',
              '## Quyết định tiếp', '',
              'Giữ M2 làm mốc, E2 là đối chứng phát triển để nghiên cứu lỗi; không promotion. R5a tách quyết định nối tiêu đề khỏi nhận diện dòng, chốt giao thức trước fit.',
              'Không tiếp tục quét tham số R4 vô hạn; ablation morphology/style chỉ cần nếu muốn quy công riêng, chưa tuyên bố nhóm nào gây cải thiện.',
              'Regression 969 đạt/3 ML skip; 52/52 nhóm A1 trong ML; 9/9 integration. Các số chồng nhau không cộng. Skill scientific-critical-thinking được dùng để không đồng nhất F1 dòng với chất lượng đầu-cuối.', '',
              '[Giao thức](v4-14-r4-giao-thuc-2026-10-07.md) · [Toàn bộ số từng cuốn/nguồn, hai mặt nạ, hash và timing](v4-14-r4-so-do-2026-10-07.json)', '']
    report=target.with_name('v4-14-r4-ket-qua-2026-10-07.md')
    if report.exists():
        raise ValueError('Do not overwrite report')
    report.write_text('\n'.join(lines),encoding='utf-8')


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--out',type=Path,required=True)
    run(cli.parse_args().out)
