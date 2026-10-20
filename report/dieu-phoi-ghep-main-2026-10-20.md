# Điều phối ghép bù vào main — 2026-10-20

**Trạng thái:** đã ghép `a3f2f13` tới mốc được phép `8558df4`, cổng đầy đủ đạt và **đã đẩy GitHub** cùng hồ sơ điều phối tới `83f3ffd`.
Thư mục chung ở main; W-03/W-24 đã có worktree riêng. Không kéo mã W-03 hoặc các commit chưa soát vào main.
**Căn cứ:** chủ dự án chuyển thông báo của Claude trong chat; [quy trình nhánh và ghép main](../doc/quy-trinh-nhanh-va-ghep-main.md), commit `a4800a8`, mục 4.

## Mốc được phép ghép

- W-02/W-05 đã soát đạt ở [báo cáo ngày 20](dieu-phoi-nghiem-thu-w02-w05-w24-2026-10-20.md).
- Mốc ghép `8558df4`: hash ba tệp React khớp từng byte manifest UI đã soát, có xét LF/CRLF.
- Hai commit `781415b` (W-24) và `79cb9c9` (UI W-02) không nằm trong bản ghép này; tiếp tục ở W-03, chờ soát.
- W-03 còn có `6cd6be7` thêm helper Figma; commit này cũng chưa được soát và không được kéo vào bản ghép W-02/W-05.
- W-13 không cần merge nhánh biên bản: bốn báo cáo đã có cùng nội dung trên main; tệp vé main mới hơn.

## Các bước đã thực hiện

1. Gửi yêu cầu trực tiếp tới phiên web, chủ dự án đã hỗ trợ mở phiên khi nó đang chờ phê duyệt.
   Web xác nhận đã dừng cả ba Luna và lưu W-03 tại `fdd0620b98e4b8a4599c64804119fb44e5cec4fd`, không commit tệp điều phối.
   Schema checkpoint trước đó `33c70ac`. W-03 chưa được nghiệm thu toàn vé.
2. Sao lưu riêng 15 tệp điều phối vào `tmp/coord-merge-20261020/coordinator-before/`; không dùng stash, không đưa mã W-03 vào main.
3. Tạo worktree `tmp/ghep-main` tại main; merge `--no-ff 8558df4`, không xung đột.
   Commit ghép local: `a3f2f13f184e874f1ef4ac0e3e6cbc7aebb7e980`, nhận main mới `a4800a8`.
4. Kiểm đường import Python bằng tiến trình con: cả `doc2roadmap` và `wayfinder` đều nằm trong `tmp/ghep-main/src/`.
5. Cài React bằng `npm ci`: 113 package, audit không có advisory ở lượt cài; không thay lockfile.
6. Chạy toàn bộ pytest qua runner có PostgreSQL bắt buộc, không lọc đường dẫn test, không giảm ngưỡng.

## Cổng kiểm

Lượt A dùng `--basetemp=tmp/cong-w02-w05-20261020a`, XML `tmp/cong-w02-w05-20261020a.xml` trong worktree.
Log và metadata lệnh: `tmp/coord-merge-20261020/gate-a.log`, `gate-a.json` ở thư mục chung.
**Lượt A đỏ:** 1.476 đạt, 2 fail, 522 error, 333,42 giây. Toàn bộ 522 error là `WinError 3` vì điều phối chưa tạo thư mục cha `tmp/`
trong worktree mới trước khi pytest tạo basetemp. Hai test quiz còn thiếu graph phát triển `doc-1` v45, không phải sai assertion nghiệp vụ.
Đã báo chủ dự án trước khi tiếp tục; chưa đẩy main. Đây không phải `WinError 5` và không được ghi nhầm thành trường hợp đó.

Đã tạo thư mục cha và sao chép đúng hai tệp `artifacts/graph/doc-1/v45/{graph,manifest}.json` từ kho phát triển,
ghi SHA-256 vào `tmp/coord-merge-20261020/environment-repair.json`; không sao chép kho global Pha B, không đổi mã hay test.
Chạy lại **toàn bộ** cổng bằng basetemp mới `tmp/cong-w02-w05-20261020b`; kết quả cuối sẽ cập nhật khi hoàn tất.
**Lượt B đỏ:** 1.991 đạt, 8 fail, 1 Cloudinary live không bật, 0 error, 512,205 giây. Cả tám fail là thiếu fixture phát triển:
bốn ca W-13 cần PDF/cache doc-6; hai ca quiz cần chunks doc-1 v5 đi kèm graph v45; fake builder cần graph/retrieval/formula-images doc-6;
preview PDF cần `doc-1.pdf`. Không có lỗi assertion còn lại ngoài các đầu vào thiếu này.

Đã chuẩn bị snapshot độc lập của đúng hai cuốn doc-1/doc-6, sáu loại artifact phát triển và ảnh công thức của hai cuốn;
927 tệp, 516.129.184 byte, có danh sách đường dẫn/SHA-256 tại `tmp/coord-merge-20261020/development-fixtures.json`.
Không nối toàn bộ kho artifact dùng chung vào worktree. Tám ca đỏ cùng settings kiểm tập trung lại **16/16 đạt**;
không cộng lượt này vào tổng của cổng đầy đủ. Lượt C chạy toàn bộ bằng basetemp mới `tmp/cong-w02-w05-20261020c`.

**React:** 41/41 đạt, TypeScript/Vite build đạt trên cùng commit ghép; XML/lệnh ở `tmp/coord-merge-20261020/react.xml`, `react-gate.json`.
**Lượt C đạt:** **1.999 passed, 1 skipped, 0 fail/error**, 551,74 giây; chỉ Cloudinary live không bật.
Đã chạy cả hai testpaths của repo, không truyền đường dẫn lọc test và PostgreSQL bắt buộc. Không dùng số 2.062 của báo cáo cũ thay kết quả lượt này.
Các lượt A/B đỏ và lượt kiểm tập trung được giữ riêng, không cộng vào số passed cuối.

Bằng chứng lưu cùng repo: [tổng hợp lệnh và số đo](ghep-main-evidence-2026-10-20/gate-summary.json),
[Python XML](ghep-main-evidence-2026-10-20/python-gate.xml), [React XML](ghep-main-evidence-2026-10-20/react-gate.xml),
[build](ghep-main-evidence-2026-10-20/react-build.log), [manifest fixture](ghep-main-evidence-2026-10-20/development-fixtures.json).
Raw XML/log của A/B vẫn ở `tmp/coord-merge-20261020/`, không commit hàng trăm trace setup lặp lại.
`git diff 8558df4 main -- src tests scripts design` rỗng: bản ghép giữ đúng mã đã soát.
Không gọi mô hình hay gửi thư thật; không đưa dữ liệu giữ lại vào worktree kiểm.

## Hồ sơ và phiên tiếp theo

Đã thêm liên kết quy trình vào luật chung web và handoff, gồm lệnh test đúng worktree và trách nhiệm merge của điều phối.
Đã gỡ worktree kiểm sau khi lưu bằng chứng và `git switch main` thành công; giữ nguyên toàn bộ thay đổi điều phối, không stash/force.
Hồ sơ được commit thẳng main theo quy trình.
Đã chuyển W-03 sang `tmp/w03-email-recovery`, nhận main `83f3ffd` bằng `7e8530b`, cài React bằng `npm ci`,
tạo `tmp/` và chép riêng `src/web/.env` đã được gitignore. Đã gửi đường dẫn trực tiếp tới phiên web; phiên cũ được yêu cầu chờ chủ dự án mở lại
trong worktree này, không tiếp tục sửa ở workspace chung. Snapshot W-03 và các phần chưa nghiệm thu được giữ nguyên.
Thiết kế dùng nhánh/worktree riêng `work/w24-figma-evidence` / `tmp/w24-figma-evidence`; chủ dự án đã nhận lời nhắn để chuyển cho nhóm.
Đã tạo nhánh từ `781415b` và cherry-pick riêng helper `6cd6be7` thành `f9540f5`, không mang mã W-03/commit UI `79cb9c9` vào nhánh thiết kế.
Nhánh thiết kế đã nhận main `83f3ffd` bằng `cd8e83d`, không xung đột; chưa được nghiệm thu hay ghép main.
Chủ dự án mở phiên thiết kế tại `C:\Users\ngoco\Desktop\Doctoroadmap\tmp\w24-figma-evidence` để tiếp tục phần còn lại.
`781415b` phải được soát W-24 trước khi W-03 được ghép; không coi bàn giao của nhân viên là phán xét đạt.

Trạng thái tại thời điểm bàn giao sau lần đẩy đầu: [nhánh, worktree và dọn dẹp](ghep-main-evidence-2026-10-20/handoff-state.json).
Nhật ký cuối đợt được commit/đẩy tiếp bằng thay đổi tài liệu; không thay mã đã qua cổng.

## Lưu ý dọn dẹp

- `tmp/w05-core` còn thay đổi chưa commit và thư mục web chưa theo dõi: giữ nguyên, không xoá hay ép dọn.
- Đã gỡ `tmp/w05-postgres` sạch và xoá nhánh `work/w05-postgres` bằng `-d` sau khi main được đẩy.
- Đã xoá nhánh `work/w02-accounts` sau khi xác nhận toàn bộ lịch sử, gồm phần chưa soát, vẫn nằm trong nhánh W-03.
- Sau bản ghép, bốn báo cáo W-13 vẫn giống nhánh biên bản, nhưng `tasks/todo.md` trên main có thêm checklist W-05.
  Điều kiện so sánh chính xác ở mục 4.6 của quy trình chưa thoả; chưa xoá cưỡng bức nhánh biên bản này.
- Không đụng worktree Pha A và hai worktree `ve-04-bo-vang`, `ve-05-bo-cham`.
