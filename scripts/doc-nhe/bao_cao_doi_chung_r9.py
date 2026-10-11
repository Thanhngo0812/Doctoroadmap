"""Export every frozen-model counterfactual, never a per-book winning oracle."""
import statistics
import hoc_tieu_de as base


def run():
    output=base.ROOT/'report/v4-14-r9-so-do-2026-10-07.json'
    assert not output.exists()
    data=base.read(base.ROOT/'tmp/a1-v414-r9/e2e.json')
    for book in data['books']:
        del book['probability']
    base.write(output,data)
    variants=list(data['books'][0]['models'])
    train=[b for b in data['books'] if b['split']=='train']
    lines=['# A1 R9 — bộ lọc, trọng số mô hình và nối dòng','',
           '19 sách, 8 tổ hợp định trước, không fit thêm/không API. Mọi model loại cuốn đang đo khỏi train; hash/split đã kiểm.',
           'M2c: refit R8c; M2f/E2f: trọng số gốc; Mean: trung bình hai score frozen. Tất cả dùng dòng R8c; B2 là model nối dòng R5.','',
           '## Median 16 sách phát triển','',
           '| Nhánh | Strict heading | Strict leaf | Legacy leaf | Jaccard≥0,8 |','|---|---:|---:|---:|---:|']
    for v in variants:
        scores=[statistics.median(b['models'][v][a][c] for b in train) for a,c in [
            ('heading_strict','f1'),('leaf_strict','share'),('chunk_legacy','cung_muc_la'),('chunk_legacy','docling_co_ban_tu_0_8')]]
        lines.append('| '+v+' | '+' | '.join(f'{s:.6f}' for s in scores)+' |')
    lines+=['','## Strict leaf từng cuốn (không chọn nhánh thắng theo ID)','',
            '| Sách | '+' | '.join(variants)+' |','|---|'+'---:|'*len(variants)]
    for b in data['books']:
        lines.append('| '+b['id']+' | '+' | '.join(f"{b['models'][v]['leaf_strict']['share']:.4f}" for v in variants)+' |')
    lines+=['','## Kết luận có giới hạn','',
            '- d01-01: M2 frozen + filter mới giữ strict leaf 0,65054; refit làm giảm còn 0,54839. Hai dòng khôi phục không tự giải thích mức giảm: đổi trọng số đóng vai trò chính ở trường hợp này.',
            '- doc-1: M2 frozen + filter mới vẫn giảm từ 0,61809 xuống 0,46231; refit còn 0,41206. Vì thế đây không chỉ là vấn đề refit: dòng khôi phục/context/grouping công thức cũng cần xử lý.',
            '- E2f+B2 đạt doc-1 0,62312 nhưng d01-01 chỉ 0,41667. Không dùng nhánh riêng mỗi sách hoặc gọi điểm tốt của một cuốn là mô hình chung tốt.',
            '- Mean không vượt rõ M2f+B2 trên median strict leaf, còn các chỉ số khác bất đồng. Không đủ bằng chứng thêm ensemble vào production.',
            '- Giữ các đối chứng để nghiên cứu, **không promotion**. Cây nhẹ còn thiếu bảng semantic, công thức 2D, hierarchy và nhãn độc lập.',
            '- 152 tổ hợp sách–nhánh đều giữ text/source rows/bbox/thứ tự của dòng retained; B0/M2c tái hiện đúng mọi score R8c. Đây không chứng minh reading order semantic hoặc glyph đúng.',
            '- Đo trên cached rows, không có số tốc độ parse mới. Không test thống kê significance trên 152 quan sát phụ thuộc; đơn vị là sách/nguồn, không phải tổ hợp.',
            '', 'R10 tiếp tục review ảnh không hiển thị dự đoán/nhãn bạc; không quét tham số để chạy theo điểm Docling.',
            '', '[Giao thức](v4-14-r9-giao-thuc-2026-10-07.md) · [Tất cả metric/raw denominators/hash](v4-14-r9-so-do-2026-10-07.json)','']
    output.with_name('v4-14-r9-ket-qua-2026-10-07.md').write_text('\n'.join(lines),encoding='utf-8')


if __name__=='__main__':
    run()
