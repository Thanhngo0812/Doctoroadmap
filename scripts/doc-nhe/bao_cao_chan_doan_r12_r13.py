"""Publish fixed diagnostic outputs, keeping historical metrics unchanged."""
import statistics
import hoc_tieu_de as base


def run(round_id,title,conclusions):
    data=base.read(base.ROOT/f'tmp/a1-v414-{round_id}/e2e.json')
    output=base.ROOT/f'report/v4-14-{round_id}-so-do-2026-10-07.json'
    assert not output.exists()
    base.write(output,data)
    train=[b for b in data['books'] if b['split']=='train']
    variants=list(train[0]['models'])
    lines=['# '+title,'','0 USD API; 19 sách đã xem, không phải test mù. Không fit thêm.',
           '', '## Median 16 sách phát triển','',
           '| Nhánh | Strict heading | Strict leaf | Legacy leaf | Jaccard≥0,8 |','|---|---:|---:|---:|---:|']
    for v in variants:
        values=[statistics.median(b['models'][v][a][c] for b in train) for a,c in [
            ('heading_strict','f1'),('leaf_strict','share'),('chunk_legacy','cung_muc_la'),('chunk_legacy','docling_co_ban_tu_0_8')]]
        lines.append('| '+v+' | '+' | '.join(f'{s:.6f}' for s in values)+' |')
    lines+=['','## Strict leaf từng sách','', '| Sách | '+' | '.join(variants)+' |','|---|'+'---:|'*len(variants)]
    for b in data['books']:
        lines.append('| '+b['id']+' | '+' | '.join(f"{b['models'][v]['leaf_strict']['share']:.4f}" for v in variants)+' |')
    if round_id=='r12':
        lines+=['','## Tự so nguồn với chính nó','',
                '| Sách | Strict hits/total | Không có tên lá | Jaccard≥0,8 |','|---|---:|---:|---:|']
        for b in data['books']:
            s=b['self_control']; leaf=s['leaf_strict']
            lines.append(f"| {b['id']} | {leaf['hits']}/{leaf['total']} | {s['missing_leaf']} | {s['chunk_legacy']['docling_co_ban_tu_0_8']:.3f} |")
    else:
        lines+=['','## Audit bỏ dòng','', '| Sách | Dòng bỏ | Cách đo |','|---|---:|---|']
        for b in data['books']:
            lines.append(f"| {b['id']} | {len(b['removed'])} | {b['measurement']} |")
    lines+=['','## Kết luận và giới hạn','',*conclusions,'',
            f'[Giao thức](v4-14-{round_id}-giao-thuc-2026-10-07.md) · [Snapshot](v4-14-{round_id}-so-do-2026-10-07.json)','']
    output.with_name(f'v4-14-{round_id}-ket-qua-2026-10-07.md').write_text('\n'.join(lines),encoding='utf-8')


if __name__=='__main__':
    run('r12','A1 R12 — classifier không phải nút thắt duy nhất',[
        '- Cấp nhãn R1 tại dòng có nhãn: strict leaf median 0,63933→0,75878 khi cùng B2; R3 đạt 0,73139. Unknown vẫn dùng M2. Không phải trần tối ưu hoặc accuracy model.',
        '- Legacy R1 B0 đạt 0,877 còn strict 0,74783: không dùng số thuận lợi để nhận toàn A1. Hai metric khác định nghĩa/mẫu căn.',
        '- Self-control thấp nhất strict leaf 0,94098 (d01-13), median 0,99782. Metric có chunk không tên lá, tie nội dung và chunk không có word-token; điểm thiếu không thể quy hết cho parser. Không đổi metric lịch sử.',
        '- d01-07 nhiều unknown gồm running title bị nhận heading. d01-01/doc-1 còn lỗi grouping/nguồn chữ. Cần tách từng nguyên nhân, không chỉ tăng cây.',
        '- 114 tổ hợp bảo toàn retained text/bbox/order, M2f B0/B2 tái hiện đúng R9. Hai test intervention đạt trong ML; môi trường production không có joblib nên module test được skip.',
        '- Tiếp tục R13 xử lý ca đầu trang xác nhận trên ảnh, rồi xây phép đo phân tầng độc lập với level Docling phẳng.'
    ])
    run('r13','A1 R13 — nhận running title từ dòng biên thực tế',[
        '- Bỏ 112 dòng ở d01-07, tất cả nhãn R1/R3 unknown, cùng mẫu running title đã xem trang 3–4. Không gọi unknown là nhãn âm hoặc coi 112 dòng là 112 ca vàng.',
        '- 18 sách khác không đổi rows/body/score/joins, đã kiểm bằng equality và tái dùng số cũ. Không báo là 19 lượt parse mới.',
        '- M2f+B2 strict leaf d01-07 0,19408→0,22368 khi chỉ bỏ dòng, →0,23026 khi tính lại context. WB133+B2 0,33882→0,34211. Sửa đúng một nguyên nhân nhưng chưa giải quyết cả cuốn.',
        '- 14 test filter đạt; test dữ liệu hình học hợp lệ đỏ trên R8c trước sửa rồi xanh. Fixture đầu tiên sai chiều cao trang đã được sửa trước khi lấy kết quả đỏ làm bằng chứng.',
        '- Giữ prototype, chưa áp vào production. Cần kiểm template bài tập đánh số và nhiều dòng biên; không bảo đảm không xóa nhầm chỉ vì có chuỗi số trang.',
        '- Kế tiếp: tách nhận heading, thứ tự và cây cha–con. Bản nhẹ chưa được nghiệm thu toàn A1.'
    ])
