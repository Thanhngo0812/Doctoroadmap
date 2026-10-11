"""Export all R11 splits and end-to-end results without probability arrays."""
from copy import deepcopy
import statistics
import hoc_tieu_de as base


def run():
    root=base.ROOT/'tmp/a1-v414-r11'
    data=base.read(base.ROOT/'tmp/a1-v414-r11-e2e/e2e.json')
    data['training']=base.read(root/'training.json')
    data['training_protocol']=base.read(root/'protocol.json')
    data['splits']=[]
    for path in sorted((root/'models').glob('*.json')):
        record=base.read(path)
        assert record['fingerprint']==data['protocol']
        for prediction in record['predictions'].values():
            del prediction['probability']
        data['splits'].append(record)
    assert len(data['splits'])==81
    baseline={b['id']:b for b in base.read(base.ROOT/'tmp/a1-v414-r9/e2e.json')['books']}
    for book in data['books']:
        book['models']={**{v:deepcopy(baseline[book['id']]['models'][v]) for v in ('M2c_B0','M2c_B2','M2f_B0','M2f_B2')},**book['models']}
    output=base.ROOT/'report/v4-14-r11-so-do-2026-10-07.json'
    assert not output.exists()
    base.write(output,data)
    lines=['# A1 R11 — cân bằng sách không đủ để nhận toàn A1','',
           '81 fit, 27 split mỗi cấu hình; đầu vào R8c cố định. Đây là weighted ERM, không phải group DRO.',
           f"Tổng thời gian fit: {data['training']['fit_seconds']:.3f} giây; không phải tốc độ PDF→cây. API: 0 USD.",'',
           '## Phân loại dòng, full raw denominator','',
           '| Cấu hình | Phép chia | Nhãn | Median F1 | Min F1 | Cuốn min |','|---|---|---|---:|---:|---|']
    for variant in ('WB73','ERM133','WB133'):
        for group,prefix in [('LOBO','d01'),('Giữ nguồn','publisher'),('External cũ','full')]:
            for label in ('r1','r3'):
                values=[(k,p['full_raw'][label]['f1']) for r in data['splits'] if r['variant']==variant and r['name'].startswith(prefix)
                        for k,p in r['predictions'].items()]
                key,minimum=min(values,key=lambda t:t[1])
                lines.append(f'| {variant} | {group} | {label} | {statistics.median(v for _,v in values):.6f} | {minimum:.6f} | {key} |')
    lines+=['','## Đầu-cuối: median 16 sách phát triển','',
            '| Nhánh | Strict heading | Strict leaf | Legacy leaf | Jaccard≥0,8 |','|---|---:|---:|---:|---:|']
    train=[b for b in data['books'] if b['split']=='train']
    variants=list(train[0]['models'])
    for v in variants:
        values=[statistics.median(b['models'][v][a][c] for b in train) for a,c in [
            ('heading_strict','f1'),('leaf_strict','share'),('chunk_legacy','cung_muc_la'),('chunk_legacy','docling_co_ban_tu_0_8')]]
        lines.append('| '+v+' | '+' | '.join(f'{s:.6f}' for s in values)+' |')
    lines+=['','## Strict leaf đủ 19 cuốn','', '| Sách | '+' | '.join(variants)+' |','|---|'+'---:|'*len(variants)]
    for b in data['books']:
        lines.append('| '+b['id']+' | '+' | '.join(f"{b['models'][v]['leaf_strict']['share']:.4f}" for v in variants)+' |')
    lines+=['','## Quyết định và giới hạn','',
            '- Không promotion: vẫn chưa giải quyết worst-book, giữ riêng nguồn và chất lượng toàn cấu trúc. Cân sách không tự sửa nhãn bạc/unknown.',
            '- WB133 vs ERM133 là so sánh trọng số với cùng features/config/input. M2f là trọng số lịch sử, không dùng nó thay ERM133 để quy tác động cho loss.',
            '- Không chọn model riêng theo ID sách; không tăng/quét cây, lá, threshold sau nhìn kết quả. Tất cả 81 split có hash/model/denominator trong snapshot.',
            '- 114 tổ hợp mới (19×3×2) qua kiểm source rows, chữ, bbox và thứ tự retained. Không suy ra đọc đúng bảng/công thức/hierarchy.',
            '- 19 cuốn đều đã được kiểm trước đây; các hàng R1/R3 và các nhánh cùng sách không phải mẫu độc lập. Chưa chứng minh tổng quát hóa ngoài kho phát triển.',
            '- Test weight đã đỏ với class-balanced toàn tập, rồi xanh khi cân đúng sách/lớp. 996 regression đạt/3 skip ML/8 integration deselected, nhóm A1/heading ML 81 đạt.',
            '- R12 đang tách phần còn lại bằng self-control/can thiệp nhãn, không dừng để xin duyệt mỗi vòng.',
            '', '[Giao thức và nguồn](v4-14-r11-giao-thuc-2026-10-07.md) · [Snapshot mọi số đo](v4-14-r11-so-do-2026-10-07.json)','']
    output.with_name('v4-14-r11-ket-qua-2026-10-07.md').write_text('\n'.join(lines),encoding='utf-8')


if __name__=='__main__':
    run()
