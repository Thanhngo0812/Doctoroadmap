"""Publish hierarchy experiments with their full unfavorable controls."""
import statistics
import hoc_tieu_de as base


def publish(name,data,lines):
    root=base.ROOT/'report'
    target=root/f'v4-14-{name}-so-do-2026-10-07.json'
    assert not target.exists()
    base.write(target,data)
    target.with_name(f'v4-14-{name}-ket-qua-2026-10-07.md').write_text('\n'.join(lines)+ '\n',encoding='utf-8')


def run():
    a=base.read(base.ROOT/'tmp/a1-v414-r14/results.json')
    b=base.read(base.ROOT/'tmp/a1-v414-r14b/results.json')
    c=base.read(base.ROOT/'tmp/a1-v414-r14c/transport.json')
    before=base.read(base.ROOT/'tmp/a1-v414-r14c/before.json')
    after=base.read(base.ROOT/'tmp/a1-v414-r14c/after.json')
    assert before['books']==after['books']
    lines=['# A1 R14–R14c — bộ cha học và hợp đồng truyền cây','',
        '0 USD API. 19 sách phát triển đã xem, không mở sách test. Không thay Docling.',
        '', '## Đối chứng cùng tiêu đề căn được từ outline','',
        '| Sách/nhánh bỏ ra | N | H0 | H1 số mục/style | Chunker cũ | H2 LightGBM | H2 qua chunker cũ |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for f in b['folds']:
        label=f["book"]+('/'+str(f['group']) if f['group'] is not None else '')
        lines.append(f"| {label} | {f['H2']['headings']} | "+' | '.join(f"{f[v]['parent_accuracy']:.5f}" for v in ('H0','H1','Hchunk','H2','H2_through_chunker'))+' |')
    lines+=['','- H2: LightGBM 100 cây/7 lá, 24 đặc trưng cặp cha–con, decoder chỉ chọn cha trên nhánh đang mở. Không phải thay classifier dòng 300 cây.',
        '- 13 fold bỏ nhánh trong cùng d01-08 + một model full; không phải 13 sách độc lập. doc-4 không train, nhưng là sách phát triển đã xem. Outline là nhãn yếu.',
        '- doc-4: H2 131/171 (76,61%), H1 139/171 (81,29%). Không chọn model học chỉ vì thắng H0 yếu. Đối chứng H1 bổ sung sau R14: đây là phát triển thăm dò.',
        '- Chunker mặc định ghi đè cây H2, chỉ còn 26/171 đúng cha ở phép thử chỉ-heading doc-4. Không diễn giải số này là accuracy toàn PDF.',
        '', '## Thay đổi production có giới hạn','',
        '- Thêm hợp đồng API `heading_scheme="declared-v1"`: đầu vào đã quyết định tập tiêu đề và cây, độ sâu bắt đầu 1, không bỏ cấp, không boolean/float/missing/heading rỗng. Chunker không tự bác tiêu đề hoặc đổi cha.',
        '- Không bật ở CLI, không đổi mặc định Docling/vn-textbook, không dùng mode này cho level Docling phẳng chưa kiểm. Khoá chunk chứa scheme, parse được dùng lại, chunk tách cache.',
        f"- {len(c['records'])} cây H1/H2 với {sum(r['headings'] for r in c['records'])} payload tổng hợp: parent ID và chủ sở hữu chunk đúng cây truyền vào, không đổi cha. Đây là transport, không phải chất lượng PDF.",
        '- 19 cây tham chiếu tái chia chunk mặc định: hash toàn ChunkingResult trước/sau giống nhau (chunk, section, warning, ID, span, refs). Không ingest lại artifact.',
        '- 13 test hợp đồng đạt; đã thấy đỏ trước thêm mode, mutation bỏ validation và bỏ scheme khỏi hash bị bắt. Regression 1019 đạt/4 skip/8 deselected; integration 9 đạt. Các lượt có test trùng, không cộng.',
        '', '## Nghiên cứu và hạn chế','',
        'Thiết kế tách nhận heading/thứ tự/dựng cây, dùng nhánh đang mở tham khảo [Detect-Order-Construct](https://arxiv.org/html/2401.11874v2) (đọc §4.4, Algorithm 1, §5); không sao chép mô hình Transformer của bài. HRDoc chỉ đọc abstract, không nhận đã tái lập kết quả.',
        'Skill paper-lookup dùng xác minh tác giả/phiên bản; scientific-critical-thinking dẫn tới thêm baseline mạnh, không coi nhãn bạc hoặc metric transport là chất lượng ngoài mẫu. Ponytail dùng lại helper/chunker/dependency sẵn có; không giới hạn phạm vi nghiên cứu chủ dự án giao.',
        '[Giao thức R14](v4-14-r14-giao-thuc-phan-tang-2026-10-07.md) · [Đối chứng R14b](v4-14-r14b-giao-thuc-2026-10-07.md) · [Snapshot](v4-14-r14-so-do-2026-10-07.json).',
        'Ghi nhận skill: Kassis, Agarwal, He, Patel & Brueckner (2026), [Scientific Agent Skills](https://doi.org/10.48550/arXiv.2609.00065), record đã xác minh v2.']
    publish('r14',dict(training=a,controls=b,transport=c,default_before=before,default_after=after),lines)
    for name in ('r15','r16'):
        data=base.read(base.ROOT/f'tmp/a1-v414-{name}/e2e.json')
        variants=('existing','H1','H2')
        lines=[f'# A1 {name.upper()} — toàn luồng, không dùng tiêu đề oracle','',
            '0 USD API; 19 sách phát triển đã xem. d01-08 đã train bộ cha nên kết quả H2 của cuốn này là in-sample.',
            '', '| Sách | Cũ strict leaf | H1 strict leaf | H2 strict leaf |', '|---|---:|---:|---:|']
        for row in data['books']:
            lines.append('| '+row['id']+' | '+' | '.join(f"{row['models'][v]['leaf_strict']['share']:.5f}" for v in variants)+' |')
        # Report both full development description and parent-model out-of-training set.
        for label,subset in [('16 D01 (mô tả, gồm d01-08)',[b for b in data['books'] if b['split']=='train']),
                             ('18 sách loại d01-08 (không gọi test mù)',[b for b in data['books'] if not b['parent_model_in_sample']])]:
            lines+=['',label+': '+', '.join(v+' median '+f"{statistics.median(b['models'][v]['leaf_strict']['share'] for b in subset):.5f}" for v in variants)+'.']
        lines+=['','## Outline: đúng cha trên phần căn được','',
            '| Sách | Nhánh | Căn/nguồn | Đúng cha/căn | Đúng cha/nguồn | Cha không căn được |',
            '|---|---|---:|---:|---:|---:|']
        for row in data['books']:
            for v in variants:
                s=row['models'][v].get('outline')
                if s: lines.append(f"| {row['id']} | {v} | {s['matched']}/{s['reference_headings']} | {s['parent_hits']}/{s['matched']} | {s['joint_hits_per_reference']:.5f} | {s['unmatched_parent_errors']} |")
        lines+=['','Heading không căn được không tự động là heading sai: outline không đầy đủ. Mẫu số nguồn ở đây chỉ các bookmark đã căn chắc với dòng trong R14, không phải mọi mục thật trong sách.',
            'Strict leaf không đo tổ tiên, nên H1/H2 có thể giống điểm lá dù cây rất khác. Không lấy bằng nhau ở metric này làm bằng chứng hai cây tương đương.',
            'Cây prototype vẫn thiếu dựng bảng semantic, hình vector/caption đầy đủ và thứ tự đọc xác minh; không phải ứng viên đủ điều kiện thay Docling.']
        if name=='r15':
            lines+=['','R15 tắt các guard nhận tiêu đề bằng mode declared; vì thế giảm strict leaf không tách riêng được lỗi hierarchy. Tiếp tục R16 giữ lại đúng tập tiêu đề qua guard cũ, không fit thêm.']
        else:
            lines+=['','## Kiểm tương đương và đường mục đầy đủ','',
                '| Sách | Nhận/bác heading | Chunk đổi số độ sâu | Cũ path | H1 path | H2 path |',
                '|---|---:|---:|---:|---:|---:|']
            for row in data['books']:
                lines.append(f"| {row['id']} | {row['accepted']}/{row['rejected']} | {row['normalized_depths']} | "+' | '.join(f"{row['models'][v]['path_strict']['share']:.5f}" for v in variants)+' |')
            lines+=['','Tái lập baseline R13 đúng từng strict leaf; giữ guard rồi truyền cây cũ thì mọi trường chunk giống nhau trừ heading_level được chuẩn hóa về độ sâu đường mục. Lượt diagnostic đầu dừng vì khác level 2→1; giao thức đã ghi rõ, không báo byte-identical sai sự thật.',
                'H1/H2 dùng phép chiếu cha qua heading bị bác, không chạy decoder lại. Toàn bộ text chunk và thứ tự giống baseline. Đường mục so Docling chỉ là độ đồng thuận với nguồn bạc; Docling có hierarchy phẳng, không coi thấp hơn là bằng chứng hierarchy thực kém hơn.',
                'Chưa promotion H1/H2. Nhận heading và dựng cây là hai quyết định riêng; cần review cha–con đa sách có ảnh nguồn, không chỉ cấp thêm cây/đặc trưng.']
        lines+=['',f'[Giao thức](v4-14-{name}-giao-thuc-2026-10-07.md) · [Snapshot](v4-14-{name}-so-do-2026-10-07.json).']
        publish(name,data,lines)


if __name__=='__main__': run()
