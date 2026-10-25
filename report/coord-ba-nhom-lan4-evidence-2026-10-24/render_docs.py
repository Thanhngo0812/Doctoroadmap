"""Publish the scoped review outcome after the exact candidate has passed and merged."""
import json, subprocess
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path('C:/Users/ngoco/Desktop/Doctoroadmap')
HERE = Path(__file__).parent
QA = ROOT/'report/coord-ba-nhom-lan4-evidence-2026-10-24'
decision = json.loads((HERE/'merge-result.json').read_text())
merge, candidate = decision['merge_sha'][:7], decision['candidate_sha']
cases = list(ET.parse(HERE/'runs/full-current.xml').getroot().iter('testcase'))
assert not any(c.find('failure') is not None or c.find('error') is not None for c in cases)
passed = sum(c.find('skipped') is None for c in cases)
audit = json.loads((HERE/'browser-independent.json').read_text(encoding='utf-8'))
http_count = audit['http']
values = {'MERGE_SHA':merge,'CANDIDATE_SHA':candidate,'FULL_PASSED':f'{passed:,}'.replace(',','.'),'HTTP_COUNT':str(http_count)}
for name in ['full-current','react-current','build-current','browser-current-retry']:
    receipt = json.loads((HERE/f'runs/{name}-exit.json').read_text())
    assert receipt['native_exit_code'] == 0 and receipt['commit'] == candidate, name
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip() == decision['merge_sha']
paths = []
owner_quote = decision['owner_message']
owner_note = ('**Quyết định mới của chủ dự án — 2026-10-24, chỉ đồng bộ bằng commit local:**\n\n'
              f'> {owner_quote}\n\n'
              'Ghi cho Claude và mọi phiên điều phối: tạm thời chưa cần push main; dừng các lượt thử truyền tiếp theo, '
              'không tự đẩy lại đến khi chủ dự án yêu cầu. Đây là quyết định của chủ dự án, ưu tiên hơn quy định cũ '
              'tự đẩy sau mỗi lần ghép. Nhận `main` local mới nhất; vẫn soát đúng commit/chạy cổng trước ghép. '
              'Mã đã ghép local `bad8e45`; GitHub main chưa được đồng bộ mốc này. '
              'Đã ghi ngoại lệ vào `doc/quy-trinh-nhanh-va-ghep-main.md`.\n\n')

def write(relative, text):
    assert '{{' not in text, relative
    path = ROOT/relative
    path.write_text(text,encoding='utf-8',newline='\n')
    paths.append(relative)

for template, target in [('report-template.md','report/dieu-phoi-nghiem-thu-ba-nhom-lan4-2026-10-24.md'),
                         ('tasks-template.md','report/lenh-giao-viec-ba-nhom-lan4-2026-10-24.md')]:
    text = (HERE/template).read_text(encoding='utf-8')
    for key,value in values.items():
        text = text.replace('{{'+key+'}}',value)
    assert not (ROOT/target).exists(), target
    write(target,text)

reference = '[biên bản lần4](../../report/dieu-phoi-nghiem-thu-ba-nhom-lan4-2026-10-24.md)'
ticket_notes = {
 'task/web/W-08-trang-hoc-bai-giang-doc-trang.md':
    f'**Nghiệm thu lần4, 2026-10-24: W-08 đạt · đã ghép local `{merge}`.** Mốc web `c8c687b`, cổng cuối `{candidate[:7]}` '
    f'đã nhận main có SA-68: {values["FULL_PASSED"]} Python đạt/0 fail/1 Cloudinary skip/1 replay xfail có sẵn, '
    f'181 React/build; browser PG12cấu hình/109ảnh/{http_count}HTTP/17Axe. Đóng R-W08-1 (nhãn theo tiến độ hiện tại, save/rollback không fetch bài) '
    'và R-W08-2 (tiêu đề tự kiểm tra, final authoritative); hai mutation lỗi cũ bị bắt, 5 rawSSE không lộ đáp án. '
    f'Chuyển web sang W-09, giữ bằng chứng/không dọn worktree; {reference}. Các trạng thái chưa nhận bên dưới là lịch sử.',
 'task/web/W-15-noi-bo-dung-that-do-usd-cuon.md':
    f'**Nghiệm thu lần4, 2026-10-24: nhận mốc 0USD `bf761fe`, ghép local `{merge}`; toàn W-15 vẫn mở.** '
    'Đã kiểm toàn pipeline thật với provider giả/PG, hai dry-run nội bộ, doc-6 cache-only dừng label-roles/SpendNotAllowed, '
    'không nhận ready/course/mail thật. Gói operator `9b3bd82` chưa ghép: sửa run_dir Windows ghi dấu ngược bị safe_path từ chối '
    'bằng test prepare→JSON→execute thực; xác minh đơn vị SKU online Vertex embedding trước duyệt profile/có tiền. '
    'Đề nghị bootstrap1USD và cuốn52trang3USD chưa được duyệt, chưa chạy. Worktree kiểm cần chép thêm candidate PDF theo SHA riêng, '
    f'ngoài fixture sáu cuốn. Giữ Vertex/meter duy nhất/không chi; {reference}.',
 'task/web/W-24-bo-sung-va-sua-ban-giao-w22.md':
    '**Nghiệm thu lần4, 2026-10-24: giữ đạt có ghi chú mốc thiết kế web đã nhận; không yêu cầu Cloud Figma.** '
    'Nguồn mới `eb29f29`: 52test qua runner, 24lượt preview browser; nhận các sửa96px/retry/lỗi đuôi/anchor/VM. '
    'Chưa ghép cả nhánh; trả riêng3lỗi công thức HTML mới: W09 thiếu CSS chỉ số dưới, W08/W09 mất biểu thức ở cây truy cập, '
    'W08 thiếu thẻ đóng làm lồng công thức/văn xuôi. Sửa giới hạn trước dùng lại mẫu; không giao làm lại token/layout/plugin/Cloud '
    f'và không thu hồi mốc web đã nhận. Hỗ trợ W-09/soát React W-08 theo W-23; {reference}.',
 'task/web/W-09-tro-ly-va-phien.md':
    f'**Mở sau nghiệm thu lần4, 2026-10-24:** W-08 đã đạt/ghép `{merge}`; SA-66/69/70 đã ở main, '
    'không còn điểm chờ lõi. Nhận main cài HTTP/gateway/React answer-3 bằng PG/fake0USD, focus từng lượt/cache-only, '
    'session ownership/client_turn_id, nguồn và sự kiện artifact an toàn; tham khảo HTML/CSS/token và cùng thiết kế soát React, '
    f'không chờ Cloud. {reference} và [lời giao lần4](../../report/lenh-giao-viec-ba-nhom-lan4-2026-10-24.md).',
 'task/web/W-10-quiz-tai-lieu-thu-vien.md':
    '**Cập nhật nghiệm thu lần4, 2026-10-24:** SA-67 document-3 đã ghép `6cfc535`, SA-68 quiz-3 đã ghép `21cfab3`. '
    'W-10 đã có cả hai mốc lõi mới, xếp sau W-09; đọc spec document-3/quiz-3 và kiểm HTTP/React/ẩn đáp án/xáo phương án/'
    f'nộp bài/quyền/thư viện bằng PG/fake0USD. Không dùng hợp đồng cũ thay bản mới; {reference}. Các điểm chờ SA-67/68 phía dưới là lịch sử.'
}
for path,note in ticket_notes.items():
    text = (ROOT/path).read_text(encoding='utf-8')
    split = text.index('\n\n')
    text = text[:split+2]+note+'\n\n'+text[split+2:]
    if 'W-08-' in path:
        old = 'sửa hai Required sau kiểm độc lập `89122f6`, chưa ghép; SA-62/64/65 đều đã ở main, không còn chờ lõi.'
        assert old in text
        text = text.replace(old,f'đạt · đã ghép local `{merge}`; hai Required đã đóng, chuyển W-09. Phần chưa ghép dưới đây là lịch sử.',1)
    write(path,text)

plan_path = 'task/web/00-ke-hoach.md'
plan = (ROOT/plan_path).read_text(encoding='utf-8')
rows = {
 '08': f'| [W-08](W-08-trang-hoc-bai-giang-doc-trang.md) | trang học: bài giảng stream, "Đọc trang p" | W-07; SA-62/64/65/70 đã ghép | đạt · ghép local `{merge}`, cổng `{candidate[:7]}`: {values["FULL_PASSED"]}Python/0fail/1skip/1xfail,181React/build; browser12cấu hình/109ảnh/17Axe; đóng2Required, [lần4](../../report/dieu-phoi-nghiem-thu-ba-nhom-lan4-2026-10-24.md) |',
 '09': '| [W-09](W-09-tro-ly-va-phien.md) | trợ lý và phiên chat | W-08 và SA-66/69/70 đã ghép | ưu tiên tiếp ngay; answer-3 HTTP/gateway/React, focus/cache-only/session/artifact, fake0USD; không chờ lõi hoặc Cloud |',
 '10': '| [W-10](W-10-quiz-tai-lieu-thu-vien.md) | quiz, tài liệu, thư viện | W-07; SA-67 document-3 6cfc535, SA-68 quiz-3 21cfab3 đã ghép | đủ hai mốc lõi mới; sau W-09 kiểm HTTP/React/privacy/submit/library bằng PG/fake0USD theo spec mới |',
 '15': f'| [W-15](W-15-noi-bo-dung-that-do-usd-cuon.md) | nối bộ dựng thật, đo USD/cuốn và phút/cuốn | W-13/14/SA-62 đã đạt | nhận mốc pipeline/dry-run0USD bf761fe, ghép `{merge}`; toàn vé còn mở, sửa operator Windows và xác minh đơn vị giá online trước xin duyệt paid; chưa cấp quyền chi |',
 '24': '| [W-24](W-24-bo-sung-va-sua-ban-giao-w22.md) | sửa/bổ sung bàn giao thiết kế web | — | giữ đạt có ghi chú mốc web, không Cloud; eb29f29 chưa ghép, trả riêng3lỗi công thức HTML mới rồi hỗ trợ W-09/W-23, không giao lại token/layout đã nhận |'
}
lines = plan.splitlines()
for ticket,row in rows.items():
    matches = [index for index,line in enumerate(lines) if line.startswith(f'| [W-{ticket}](')]
    assert len(matches) == 1, ticket
    lines[matches[0]] = row
plan = '\n'.join(lines)+'\n'
split = plan.index('\n\n')
intro = (f'**Mới nhất — nghiệm thu lần4 2026-10-24:** W-08 và mốc kiểm/dry-run0USD W-15 đã ghép local `{merge}`; '
         'toàn W-15 còn mở. Thiết kế giữ đạt có ghi chú mốc web, chỉ vá3lỗi công thức preview mới, không Cloud. '
         'Web sang W-09; lõi sửa operator/điều kiện profile trước xin chi; thiết kế hỗ trợ React/W-23. '
         'SA-67/68 đã ghép, W-10 có đủ document-3/quiz-3. '
         '[Biên bản](../../report/dieu-phoi-nghiem-thu-ba-nhom-lan4-2026-10-24.md), '
         '[lời giao ba nhóm](../../report/lenh-giao-viec-ba-nhom-lan4-2026-10-24.md). Giữ Vertex, chi mới0USD.\n\n')
local_note = ('**Đồng bộ local theo quyết định chủ dự án 2026-10-24:** tạm thời chưa cần push main; '
              'ghi commit mới nhất trên máy và chờ chủ dự án yêu cầu tiếp. Điều kiện soát/test trước ghép vẫn giữ nguyên.\n\n')
write(plan_path,plan[:split+2]+local_note+intro+plan[split+2:])

handoff_path = 'report/handoff-dieu-phoi-2026-10-18.md'
handoff = (ROOT/handoff_path).read_text(encoding='utf-8')
marker = '## 2. Tình hình lúc bàn giao\n\n'
assert handoff.count(marker) == 1
intro = (f'**Mới nhất — Codex nghiệm thu lần4, 2026-10-24:** W-08 `c8c687b` đạt; mốc W-15 pipeline/dry-run0USD `bf761fe` đạt, '
         f'đã ghép local **`{merge}`**, đỉnh kiểm `{candidate[:7]}` đã nhận main có SA-68. '
         f'**{values["FULL_PASSED"]}Python đạt/0fail/1Cloudinary skip/1replay xfail có sẵn,181React/build**; '
         f'browser PG12cấu hình/109ảnh/{http_count}HTTP/17Axe,5rawSSE,2mutation lỗi cũ bị bắt. Giữ lượt đỏ thiếu candidate PDF và các cổng main cũ, '
         'đã chép SHA đúng/chạy lại toàn cổng, không bỏ test. Toàn W-15 chưa đóng: gói operator9b3bd82 chưa ghép do run_dir Windows, '
         'cần xác minh đơn vị SKU online Vertex embedding trước duyệt profile; đề nghị1+3USD chưa duyệt/chưa chạy. '
         'W-22/W-24 giữ đạt có ghi chú mốc web theo chủ dự án, không Cloud; eb29f29 trả riêng3lỗi công thức HTML mới. '
         'Web tiếp W-09, lõi sửa operator/profile0USD, thiết kế hỗ trợ React/W-23; W-10 đã có SA-67document-3 và SA-68quiz-3. '
         'Giữ Vertex, không dọn/link dữ liệu,6tệp dở root giữ SHA. '
         '[Biên bản](dieu-phoi-nghiem-thu-ba-nhom-lan4-2026-10-24.md), '
         '[lời giao](lenh-giao-viec-ba-nhom-lan4-2026-10-24.md). **Mở lại cửa ghép SA/cổng toàn repo cho Claude sau commit hồ sơ local này.**\n\n')
handoff = handoff.replace(marker,marker+owner_note+intro,1)
communication_marker = '## 8. Câu hỏi treo\n\n'
assert handoff.count(communication_marker) == 1
handoff = handoff.replace(communication_marker,communication_marker+owner_note,1)
start = handoff.index('**Cửa nghiệm thu ba nhóm lần 4, 2026-10-24')
end = handoff.index('\n**2026-10-24, Codex nhận cập nhật Claude/chủ dự án:**', start)
replacement = (f'**Cửa nghiệm thu ba nhóm lần4 — đã xong, mở lại sau commit hồ sơ local 2026-10-24:** '
               f'ghép local `{merge}`, cổng `{candidate[:7]}` xanh; Codex không còn cổng PG toàn repo đang chạy. '
               'Claude có thể tiếp SA/SA-61 theo quy trình nhận main mới. Trong cửa này main nhận thêm SA-68 nên Codex giữ cả lượt kiểm '
               'và đã nhận main5e19b9b/chạy lại toàn cổng/browser trước ghép; không dùng gate main cũ. '
               'Chi Codex0USD, paid W-15 chưa duyệt, không Cloud Figma và không dọn/link dữ liệu. '
               '**Theo quyết định mới của chủ dự án: chỉ commit local, tạm thời chưa cần push main.**\n')
handoff = handoff[:start]+replacement+handoff[end:]
handoff += (f'\n| 2026-10-24 | nghiệm thu ba nhóm lần4 | Codex | W-08 và mốc W-15bf761fe đạt, ghép local **{merge}** | '
            f'Cổng cuối{candidate[:7]} nhận main có SA-68: {values["FULL_PASSED"]}Python/0fail/1skip/1xfail có sẵn,181React/build; '
            f'browser PG12cấu hình/109ảnh/{http_count}HTTP/17Axe/5rawSSE,2mutation bắt lỗi cũ,DB/port đã dừng. '
            'Lượt đầu đỏ thiếu candidate PDF giữ nguyên, chép thường/SHA/chạy lại. ToànW-15 mở, operatorWindows cần sửa, '
            'unitonlineembedding cần xác minh trướcpaid,1+3USD chỉ đề nghị/chưa duyệt. Chi mới0USD; sáu tệp dở giữ SHA, không dọn/link dữ liệu |\n'
            '| 2026-10-24 | thiết kế và kế hoạch lần4 | Codex | giữ nhận mốc thiết kế web, trả riêng3lỗi previewmới; chưa ghép nhánh thiết kế/operator | '
            'W24eb29f29:52test,24lượt browser; vá CSS chỉsố/toán truycập/span lồng; không Cloud/không giao lại token/layout đã nhận. '
            'Web W09answer3 tiếp ngay; W10đãcóSA67/68; lõi sửaoperator/profile0USD, thiết kếReact/W23. '
            'Prompt report/lenh-giao-viec-ba-nhom-lan4-2026-10-24.md chưa gửi ngoài. Mở lại cửa SA/cổng toàn repo cho Claude sau commit hồ sơ local, giữVertex |\n')
handoff += ('| 2026-10-24 | quyết định chủ dự án về đồng bộ Git | Chủ dự án, Codex ghi nguyên lời | '
            '**Tạm thời chỉ commit local, chưa cần push main** | '+owner_quote+
            '; mọi phiên điều phối nhận main local mới nhất, giữ soát/test trước ghép, không tự thử push tiếp đến khi chủ dự án yêu cầu. '
            'Các lượt truyền trước đã dừng, main GitHub chưa chứa bad8e45; không thu hồi commit ghép local |\n')
write(handoff_path,handoff)
protocol_path = 'doc/quy-trinh-nhanh-va-ghep-main.md'
protocol = (ROOT/protocol_path).read_text(encoding='utf-8')
split = protocol.index('\n\n')
exception = ('**Ngoại lệ tạm thời do chủ dự án quyết định 2026-10-24 — đồng bộ bằng commit local:**\n\n'
             f'> {owner_quote}\n\n'
             'Tạm thời dừng bước push main lên GitHub; commit phần đã nghiệm thu và hồ sơ mới nhất trên máy. '
             'Chỉ tiếp tục push khi chủ dự án yêu cầu. Ngoại lệ này ưu tiên hơn mục1.2, mục3.6 và mọi lời nhắc '
             'tự đẩy sau mỗi lần ghép bên dưới. Các điều kiện soát mã, nhận main local mới nhất, đúng commit, '
             'cổng test xanh, không force/rebase và bảo vệ dữ liệu vẫn giữ nguyên. '
             'Người điều phối ghi trạng thái local/remote thật trong bàn giao, không ghi đã đẩy khi chưa đẩy.\n\n')
write(protocol_path,protocol[:split+2]+exception+protocol[split+2:])
(HERE/'docs-paths.json').write_text(json.dumps(paths,indent=2)+'\n')
print(json.dumps({'docs':len(paths),'merge':merge,'passed':passed}))
