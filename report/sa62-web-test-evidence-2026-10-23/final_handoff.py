import json
from pathlib import Path
import xml.etree.ElementTree as ET

root = Path('C:/Users/ngoco/Desktop/Doctoroadmap')
run = Path(__file__).parent
assert json.loads((run / 'full-postmerge-exit.json').read_bytes())['native_exit_code'] == 0
tree = ET.parse(run / 'full-postmerge.xml')
cases = tree.findall('.//testcase')
skips = len(tree.findall('.//testcase/skipped'))
assert not tree.findall('.//testcase/failure') and not tree.findall('.//testcase/error')
passed = len(cases) - skips
path = root / 'report/handoff-dieu-phoi-2026-10-18.md'
body = path.read_bytes().decode('utf-8')
old = '`DailySpendGuard` vẫn tính chúng vào trần ngày.'
if old in body:
    assert body.count(old) == 1
    body = body.replace(old, '`DailySpendGuard` chỉ tính lecture/quiz/assistant/document; trace module_title/embedding của dựng không vào trần này (đính chính SA-62).')
note = f'''**2026-10-23, Codex hoàn tất yêu cầu test SA-62:** đã commit test dương vào chính nhánh `work/sa62-port-kho-pha-b` tại `ce5f581`.
Hai ca âm nhận từ main vẫn giữ PipelineWithoutStorePort. Ca dương default factory ghi cache qua store pipeline và đọc lại bằng PG độc lập;
provider/ADC/JsonPhaseBStore/SQLite bị chặn, recorder 1 lần, 0 calls/0 USD/0 attempt/ledger. Bỏ tiêm store làm 1 assertion fail, nguồn phục hồi SHA.
Cổng trước SA-64 trên ce5f581: 2305 Python/143 React/build xanh. Codex dùng quyền tự ghép được cho phép, ghép/đẩy `9ac2a85`.
Main vừa nhận SA-64 `1d91b0b` trước lệnh ghép, Codex ghi thiếu sót chặn hash và đã kiểm chứng sau ghép tại `14110c0`:
**{passed} Python đạt/{skips} Cloudinary live không bật, 0 fail/error, 143 React/build**, native 0. Không sửa composition hoặc giảm assertion.
Junit lưu Git: `report/sa62-web-test-evidence-2026-10-23/full-postmerge.xml`; báo cáo `report/sa62-tiep-nhan-test-web-2026-10-23.md`.
**SA-62 đã ở main**, không cần Claude ghép lại. W-15 tiếp kiểm toàn pipeline/identity/cache/dry-run 0 USD, chưa có quyền chi mới.
SA-64 đã ghép, W-08 nhận lecture-3; answer-3 chờ SA-66, ảnh trang SA-65 do làn Claude. Artifact Pha A vẫn ở kho tệp.
Codex mở lại cửa ghép sau khi hồ sơ này được đẩy; không còn cổng PostgreSQL đang chạy của Codex.

'''
assert note not in body
assert body.count('## 9. Khi Claude quay lại') == 1
body = body.replace('## 9. Khi Claude quay lại', note + '## 9. Khi Claude quay lại')
status = f'''**Cập nhật SA-62, 2026-10-23:** đã ghép/đẩy **9ac2a85**, test web trên nhánh SA-62 tại ce5f581; kiểm chứng sau ghép cùng SA-64 tại14110c0:
**{passed} Python đạt/{skips} Cloudinary live không bật,0fail,143React/build**. Không còn chờ port cho W-15; toàn W-15 vẫn mở cho kiểm pipeline thật/cache/dry-run,
chưa có quyền chi. SA-64 đã ở main1d91b0b nên W-08 gỡ điểm chờ hợp đồng lecture-3; answer-3 chờ SA-66.
[Báo cáo và JUnit SA-62](sa62-tiep-nhan-test-web-2026-10-23.md). Cửa ghép SA mở lại sau khi hồ sơ này được đẩy; cổng Codex đã kết thúc.

'''
body = body.replace('## 2. Tình hình lúc bàn giao\n', '## 2. Tình hình lúc bàn giao\n\n' + status, 1)
row = f'| 2026-10-23 | hoàn tất test và ghép SA-62 theo lời bàn giao | Codex | **đạt, đã ghép/đẩy 9ac2a85** | Core 266dbdc đã nghiệm thu; nhận main ecd98c2 trên nhánh SA-62, thêm 40 dòng test tại ce5f581. Giữ 2 ca âm factory cũ, thêm default factory→adapter→PG độc lập; RED bỏ injection 1 assertion fail/0 setup/SHA phục hồi, GREEN 3 ca. Cổng 2305 Python/1 skip/143 React/build. Main nhận SA-64 trước lệnh ghép, Codex ghi thiếu sót chặn hash và kiểm chứng tại 14110c0: {passed} Python/{skips} skip Cloudinary/0 fail/143 React/build/native 0. JUnit report/sa62-web-test-evidence-2026-10-23/full-postmerge.xml; báo cáo report/sa62-tiep-nhan-test-web-2026-10-23.md. Không giảm guard, 0 USD, không dọn worktree/dữ liệu, giữ 6 tệp dở root. **SA-62 gỡ chờ W-15; chưa nghiệm thu toàn W-15, chưa paid build/dry-run thật. Mở lại cửa ghép cho Claude sau đẩy hồ sơ** |\n'
path.write_bytes((body.rstrip() + '\n' + row).encode('utf-8'))
print(json.dumps({'passed': passed, 'skipped': skips, 'handoff_and_journal_updated': True}))
