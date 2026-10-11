"""Export R5 pair and downstream results without concealing disagreements."""
import json
from pathlib import Path
import statistics
import hoc_tieu_de as base


def run():
    root=base.ROOT/'tmp/a1-v414-r5'
    summary=base.read(root/'summary.json')
    results={k:base.read(root/f'{name}.json') for k,name in [('E2','e2e'),('M2','e2e-m2')]}
    output=base.ROOT/'report/v4-14-r5-so-do-2026-10-07.json'
    if output.exists():
        raise ValueError('Do not overwrite measurement')
    models={p.stem:base.read(p) for p in (root/'models').glob('*.json')}
    # Keep per-book denominators/scores, not bulky predicted probabilities in report.
    for m in models.values():
        for p in m['predictions'].values():
            del p['probability']
    base.write(output,dict(pair_summary=summary,pair_models=models,e2e=results,bookmarks=base.read(root/'bookmarks.json')))
    lines=['# A1 R5 — quan hệ nối dòng và chẩn đoán hierarchy','',
           'Đã đo 27 model LightGBM quan hệ, 787 cặp bạc (147 nối/640 tách) từ 16 sách; 135 cặp của 3 sách cũ chỉ kiểm ngoài.',
           '0 USD API, không mở test mới. Model row M2/E2 giữ nguyên, không chọn model theo tên cuốn.','',
           '## Quan hệ cặp','',
           '| Cách chia | Quy tắc cũ TP/FP/FN | Typography TP/FP/FN | LightGBM TP/FP/FN | Micro-F1 cũ → ML |',
           '|---|---:|---:|---:|---:|']
    for k,s in summary['summary'].items():
        counts=['/'.join(str(s[v][n]) for n in ('tp','fp','fn')) for v in ('B0','B1','B2')]
        lines.append('| '+k+' | '+' | '.join(counts)+f" | {s['B0']['micro_f1']:.4f} → {s['B2']['micro_f1']:.4f} |")
    lines+=['','Đây là đối chiếu nhãn bạc trên cặp cả hai đầu đã được căn heading; không đo mọi cặp mô hình sẽ gặp.',
            'd01-04/d01-15 không có positive nối trong mẫu: F1=0 là quy ước zero-division, không diễn giải là accuracy=0; xem FP/TN và mẫu số.',
            'B2 còn false join ở d01-07, không coi typography hay số cây là bảo đảm cấu trúc.','',
            '## Chunk và tiêu đề trên 19 sách','',
            '| Dòng | Nối | Median strict heading | Median strict leaf | Median legacy leaf | Median Jaccard≥0,8 |',
            '|---|---|---:|---:|---:|---:|']
    for row,data in results.items():
        books=[b for b in data['books'] if b['split']=='train']
        for v in ('B0','B1','B2'):
            measures=[statistics.median(b['models'][v][a][c] for b in books) for a,c in
                      [('heading_strict','f1'),('leaf_strict','share'),('chunk_legacy','cung_muc_la'),('chunk_legacy','docling_co_ban_tu_0_8')]]
            lines.append('| '+row+' | '+v+' | '+' | '.join(f'{x:.6f}' for x in measures)+' |')
    lines+=['','| Sách | M2 B0/B2 strict leaf | E2 B0/B2 strict leaf |','|---|---:|---:|']
    for a,b in zip(results['M2']['books'],results['E2']['books'],strict=True):
        assert a['id']==b['id']
        vals=[f"{d['models']['B0']['leaf_strict']['share']:.4f}/{d['models']['B2']['leaf_strict']['share']:.4f}" for d in (a,b)]
        lines.append('| '+a['id']+' | '+' | '.join(vals)+' |')
    lines+=['','## Quyết định','',
            'Giữ M2+B2 làm ứng viên nghiên cứu nối dòng, **chưa thay Docling/production**. Strict leaf M2 cải thiện nhưng legacy leaf giảm; không chọn chỉ số thuận lợi.',
            'Chưa có test vàng independent, bảng/figure assets/reading order chưa đầy đủ. E2+B2 không giải quyết cú giảm d01-01 do row classification.',
            'B0 của cả hai lượt được assert bằng đúng số đầu-cuối R4. Mọi nhánh giữ đủ thứ tự/text/source_rows/bbox; không xóa ký tự để tăng điểm.',
            'R5b là phân tích exploratory bổ sung sau thấy R5a, không gọi là kiểm xác nhận độc lập. Thời gian quan hệ từ cached rows không phải PDF→cây.',
            '', '## Nguồn hierarchy và bước tiếp','',
            'Cây Docling ghim gần như toàn heading level=1; không có nhãn cha–con đáng tin để học trực tiếp.',
            'Bookmark: d01-08 có 305/271 căn duy nhất, doc-4 288/171, d01-13 2/0; 16 sách còn lại không có. Bookmark là tín hiệu native, không phải vàng.',
            'Tiếp tục R6 assets/placement, giữ cổng nguyên vẹn văn bản và cảnh báo trường hợp không biết; không dừng xin duyệt mỗi vòng.',
            '5 test quan hệ đạt, gồm phản ví dụ quy tắc cũ, unknown/đa-node/cross-page và mutation mất dòng; regression cập nhật ở vé.',
            '', '[R5a protocol](v4-14-r5-giao-thuc-2026-10-07.md) · [R5b bổ sung](v4-14-r5b-giao-thuc-2026-10-07.md) · [Toàn bộ số/denominators/hashes](v4-14-r5-so-do-2026-10-07.json)','']
    output.with_name('v4-14-r5-ket-qua-2026-10-07.md').write_text('\n'.join(lines),encoding='utf-8')


if __name__=='__main__':
    run()
