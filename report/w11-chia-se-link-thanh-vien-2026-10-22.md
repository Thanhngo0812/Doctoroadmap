# W-11 — chia sẻ link và thành viên — 2026-10-22

## Mốc bàn giao và phạm vi

- Nhánh `work/w11-share-links`, worktree `tmp/w11-share-links`; giữ checkpoint `a53f0d3`. Đã merge main theo quy trình, không rebase hoặc đổi nhánh thư mục chung.
- Main nền cuối: **`dee87ccde928100c7e6168a348040d77d197ebfb`**. Các mốc tích hợp: `fb47885` nhận W-14; `a559737` nhận SA-55; `1af3229` nhận main mới có SA-58/59. Giữ nguyên transport Vertex theo quyết định chủ dự án; không gọi nhà cung cấp.
- **Commit mã được kiểm: `b9b5e6817390f8189813707095a04eeac16df95a`.** Commit bằng chứng sau mốc này chỉ bổ sung báo cáo và tệp kiểm, không đổi mã chạy/test/harness. [Manifest nguồn](w11-evidence/final-2026-10-22/source-manifest.json) lưu SHA-256 của 625 tệp nguồn/test đã theo dõi.
- Đợt trước giữ ở [báo cáo ngày 21](w11-chia-se-link-thanh-vien-2026-10-21.md). Đợt này hoàn tất W-11; không tự đánh dấu vé đạt, ghép/push main hoặc mở W-08 trước nghiệm thu của điều phối.

## Chức năng đã triển khai

- Chủ khoá tạo link: mặc định 7 ngày, chọn hạn hoặc không hết hạn, số lượt tuỳ chọn. URL đầy đủ chỉ hiện một lần; sao chép bằng clipboard; đóng/mở lại, Escape, đổi khoá hoặc phản hồi muộn không làm hiện lại URL cũ. Danh sách chỉ có 6 ký tự cuối và trạng thái/lượt/hạn; có xác nhận thu hồi.
- Trang `/join/<token>` riêng cho khách, người đã đăng nhập và link hỏng. Khách thấy tên khoá/chủ khoá/số module/bài học; đăng nhập hoặc đăng ký giữ `next` quay lại đúng link. Người đăng nhập xem thông báo dữ liệu trước nút Tham gia. Link hỏng không dùng giao diện reset mật khẩu/email.
- Chủ khoá xem tên, ngày tham gia, lần học gần nhất và xoá thành viên. Thành viên thường chỉ thấy chủ khoá/số thành viên và có thể rời khoá. Chủ khoá không tự xoá/rời khoá.
- Thu hồi link không xoá người đã tham gia. Xoá/rời chặn quyền ở request kế tiếp; dữ liệu học riêng được giữ. Tham gia lại bằng link mới đọc đúng tiến độ và phiên cũ.
- Không thêm W-12 lời mời email, W-18 tiến độ lớp, W-08…W-10 hoặc runner thật W-15. Không sửa use case trợ lý nhận từ main.

## Schema, quyền và giao dịch

- Một migration **`w11_0007 → w14_0006`**, không sửa migration đã ghép hoặc tạo merge revision. Fixture phải qua Alembic, không `metadata.create_all` để lách migration.
- `share_link` có UUID/FK/index, SHA-256 bytea 32 byte unique, tail 6 ký tự, hạn/thu hồi và ràng buộc lượt. Không có cột token thô/URL. Token ngẫu nhiên 32 byte, base64url canonical.
- Tham gia khoá hàng link rồi course; kiểm lại hạn/thu hồi, membership, trần 200 người; thêm membership, tăng lượt và audit trong một transaction. Đã là thành viên không trừ lượt. Hai người tranh link một lượt và hai link tranh chỗ cuối đều chỉ một người vào.
- Quản lý dùng actor của phiên; không nhận owner/doc/version tuỳ ý từ body. Route riêng tư giữ guard kể cả người ngoài có vai trò admin. Link sai/thu hồi/hết hạn/hết lượt cùng `link_invalid` và envelope.
- Khi nhận main giữ cả SharingService/BuildService, router/UI của hai vé, **`BuildView.upload_id` đúng actor/course** và **`UploadView.confirmed_at` riêng mỗi upload**. OpenAPI xuất lại từ app không dựng provider.

## Kiểm phản ví dụ — RED/GREEN

| Kiểm | Bằng chứng và kết luận |
|---|---|
| Schema | [Migration RED](w11-evidence/final-2026-10-22/migration-red.xml) trước migration; đây là lỗi setup/schema có chủ đích, không tính là mutation nghiệp vụ. GREEN qua Alembic/PostgreSQL thật. |
| Quyền/token/lượt/transaction/dữ liệu riêng | **8/8 mutation bị assertion bắt**, từng bản sai native 1, không setup error; nguồn phục hồi đúng byte/SHA trước full gate/browser. [Ledger/lệnh/hash](w11-evidence/final-2026-10-22/mutations/results.json). |
| Giữ dữ liệu | [Hai ca remove/leave](w11-evidence/final-2026-10-22/session-green.xml) ghi/đọc PostgresPhaseBStore, kiểm chính xác cả session và progress sau tham gia lại. Mutation xoá Pha B bị ca remove bắt. |
| Link hỏng | Browser/Axe bắt `aria-labelledby` thiếu target; [React RED](w11-evidence/final-2026-10-22/join-label-red.xml), [GREEN](w11-evidence/final-2026-10-22/join-label-green.xml) sau thêm ID cho heading. Không nới Axe. |
| Cột thành viên | [Browser RED](w11-evidence/final-2026-10-22/browser-alignment-red2.log), native 1: cột chủ khoá tại x=305/524 nhưng learner tại 243/415 ở 768 px. Sửa lưới dành cột thao tác thống nhất; [GREEN](w11-evidence/final-2026-10-22/browser-alignment-green/audit.json), native 0, kiểm vị trí hai cột tại 768/1280 sáng/tối. |

Tám mutation: lộ full token; bỏ revoke; bỏ expiry; bỏ giới hạn preview; bỏ tăng use_count; mất transaction; bỏ xoá membership; xoá dữ liệu Pha B khi gỡ thành viên. Tên assertion và lệnh đầy đủ nằm trong ledger.

Các lượt browser phát triển có lỗi CSP khi chèn style inline, locator combobox, redaction cản phân tích tương phản, aria thật và đóng dialog quá sớm làm abort list. Đã sửa nguyên nhân, giữ kiểm zero unexpected network/console errors. `browser-dev6` chạy luồng thật đạt nhưng inspector lỗi thư mục profile; đã tạo thư mục và bắt buộc có report đủ ba viewport, thay vì chỉ dựa exit code. `browser-alignment-red` là lượt chưa nạp assertion mới do lỗi encoding ở bước chuẩn bị: native 0, **không tính là RED**; chỉ `browser-alignment-red2` là RED hợp lệ. Lịch sử được giữ để đối chiếu.

## Cổng cuối sau nhận main và sửa giao diện

Các cổng dưới đây chạy trên **`b9b5e6817390f8189813707095a04eeac16df95a`**, main nền `dee87cc`; 625 hash nguồn được kiểm lại sau tất cả các lượt. [Lệnh/kết quả máy đọc được](w11-evidence/final-2026-10-22/gate-results.json).

| Cổng | Kết quả | Native exit và bằng chứng |
|---|---|---|
| Toàn repo/Python/PostgreSQL | **2.270 đạt, 1 bỏ qua**, 0 lỗi | **0**; [JUnit](w11-evidence/final-2026-10-22/acceptance-python.xml), [log](w11-evidence/final-2026-10-22/acceptance-python.log) |
| React | **121 đạt**, 0 bỏ qua | **0**; [JUnit](w11-evidence/final-2026-10-22/acceptance-react.xml), [log](w11-evidence/final-2026-10-22/acceptance-react.log) |
| Build | Thành công | **0**; [log](w11-evidence/final-2026-10-22/acceptance-build.log) |
| Browser thật | 36 ảnh, 12 Axe không violation/incomplete, 47 bản ghi HTTP | **0**; [audit](w11-evidence/final-2026-10-22/browser-final/audit.json), [log](w11-evidence/final-2026-10-22/browser-final.log) |

Test duy nhất bỏ qua là Cloudinary live, không bật theo yêu cầu dùng dịch vụ giả và chi phí 0 USD. Browser không có lỗi console/network ngoài dự kiến; 31 bản ghi dự kiến là 401 khi chưa có phiên, 410 của link hỏng và probe CSP từ Axe, được giữ riêng trong audit. Không bỏ assertion, skip thêm hoặc hạ ngưỡng để xanh.

Lệnh từ gốc worktree, mỗi lần dùng basetemp mới; không chạy pytest trần:

```powershell
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py -o addopts= -q --basetemp=tmp/w11-final-full-20261022-5 --junitxml=report/w11-evidence/final-2026-10-22/acceptance-python.xml
npm.cmd --prefix src/web/frontend test -- --pool=threads --maxWorkers=1 --reporter=junit --outputFile=../../../report/w11-evidence/final-2026-10-22/acceptance-react.xml
npm.cmd --prefix src/web/frontend run build
$env:W11_EVIDENCE_RUN='browser-final'
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe -X utf8 scripts/w11_web_runtime.py
```

Sau kiểm bố cục, ba regression bổ sung bắt nhãn vùng thiếu target ở loading/denied: [RED](w11-evidence/final-2026-10-22/regions-red.xml), [GREEN](w11-evidence/final-2026-10-22/regions-green.xml). Commit `b9b5e68` chỉ sửa ID/điều kiện nhãn và thêm ba test; không đổi backend. Lượt `handoff-*` khởi chạy tại `bf3cb87`; frontend được sửa trong khi cổng Python đang chạy nên chỉ giữ lịch sử, không coi đó là cổng đóng băng cuối. Cổng cuối dùng `acceptance-*` trên `b9b5e68`.

Các lượt `full-*` (2.237 Python), `final-*` (2.249 Python), `main-*` (2.270 Python) là lịch sử ở các commit trước, không thay cổng cuối. Mỗi lượt có log/JUnit/native exit riêng. Test hồi quy sinh lại JSON của W-06/W-14/W-25: đã chép/hash vào các thư mục `regression-run*` của vé rồi phục hồi bản đã theo dõi; không bàn giao sửa báo cáo của nhóm khác. Basetemp ở `tmp/`, không lẫn fixture/synthetic image vào ảnh UI.

## Browser HTTP/PostgreSQL thật

- PostgreSQL UUID riêng, FastAPI/Auth/CSRF/Argon2/CourseService/SharingService/LearningGateway/PostgresPhaseBStore thật. FakeMailer; media không dùng trong luồng này. Harness chặn model/ADC/SMTP/Cloudinary. Không intercept API để giả kết quả UI.
- Dữ liệu sáu cuốn chép theo hai manifest, kiểm SHA-256: **3.144 tệp**. [Nhật ký fixture](w11-evidence/final-2026-10-22/fixture-copy.log); doc-1 v8, không junction/symlink/hardlink, CLI learner/live/heldout. Không seed hoặc phá DB phát triển của chủ dự án.
- Chủ khoá tạo/sao chép URL, đóng/mở lại không thấy URL; khách vào rồi đăng nhập quay lại đúng link; kiểm `next` đăng ký; disclosure/tham gia; tham gia lặp qua API và UI không tăng lượt; đánh dấu bài học qua HTTP.
- Thu hồi vẫn GET course 200; xoá thành viên qua UI rồi GET progress 404; link mới tham gia lại thấy learned; rời qua UI rồi GET course 404; chủ khoá rời trả 403. Broken/revoked/exhausted/expired cùng HTTP 410/envelope và trang JoinPage riêng.
- SQL qua engine độc lập kiểm còn một owner, link chính dùng đúng một lượt, hàng Pha B còn nguyên, không có cột token thô và đủ năm loại audit. UUID DB bị xoá sau kiểm, không còn service harness ở 8011.
- **36 ảnh**: 6 màn × 390/768/1280 × sáng/tối; **12 lượt Axe** tại 1280 trên từng màn/sáng/tối. Không gọi toàn bộ 36 ảnh đã Axe. Video riêng chủ khoá và learner. Kiểm vùng bấm 44 px, không tràn ngang, Tab trong dialog, Escape/focus trở lại, focus thấy rõ và OS reduced-motion.
- URL một lần trong ảnh/video được che bằng CSS text-security chỉ ở harness; clipboard/HTTP vẫn dùng giá trị thật. JSON/log che token, không ghi auth/cookie/CSRF. Lượt đổi theme của modal dùng dispatch vào nút React thật để giữ đồng bộ logo/token khi shell đang inert; chỉ là ma trận diện mạo, không giả là người dùng bấm nền modal.

Bằng chứng cuối: [HTTP/console/network/Axe](w11-evidence/final-2026-10-22/browser-final/audit.json), [runtime/SQL](w11-evidence/final-2026-10-22/browser-final/runtime.json), [video chủ khoá](w11-evidence/final-2026-10-22/browser-final/owner.webm), [video learner](w11-evidence/final-2026-10-22/browser-final/learner.webm), [inspector](w11-evidence/final-2026-10-22/browser-final/taste-inspect/report.json), [ảnh 390 sáng](w11-evidence/final-2026-10-22/browser-final/owner-members-390-light.png), [ảnh 1280 tối](w11-evidence/final-2026-10-22/browser-final/owner-members-1280-dark.png), [kiểm DB/cổng đã dừng](w11-evidence/final-2026-10-22/cleanup-check.json). Toàn bộ ảnh và lịch sử có [chỉ mục riêng](w11-evidence/final-2026-10-22/README.md).

## Thiết kế và rà soát

Áp dụng **`design-taste-frontend` app screen**, direction/ghi chú đã lưu của W-11, token/font/logo Artboard 9–28 trên main và tài liệu W-24. Giữ nhãn “tài liệu”/“bài học”, không nhập raw JSON thiết kế chưa đạt. Danh sách có hàng/kẻ phân cách theo dữ liệu thật; thao tác quản lý rõ theo quyền, màu danger chỉ dùng hành động phá, không thêm KPI hay số trang trí.

Đã xem ảnh thật của hộp chia sẻ mobile, link khách desktop và thành viên tablet sáng/tối; phát hiện/sửa cột ngày lệch và kiểm lại bằng vị trí DOM. Inspector đo snapshot DOM/CSS của trang thành viên thật ở ba chiều rộng; đây là kiểm thiết kế, không thay acceptance HTTP. Không có FAIL; một WARN `hero-void` tại 1280 do danh sách chỉ có hai người. Giữ khoảng trống theo số thành viên thực, không bịa thêm hàng. Xem [rà soát mã/giới hạn](w11-evidence/final-2026-10-22/review.md).

## Bàn giao và việc sau

[README](../src/web/README.md) có các bước mở PostgreSQL/backend/frontend, URL, public base và cách dừng. Commit bằng chứng không đổi mã đã kiểm; manifest nguồn và bằng chứng cho phép đối chiếu SHA-256. Token test bị mutation cố ý làm lộ được che trong log/JUnit, không thay trạng thái assertion/native exit. Nhật ký chuẩn hoá ghi rõ lần xử lý đầu chưa lưu được đầy đủ hash trước chuyển đổi; không suy diễn hash gốc từ bản cuối. Các bản sao hồi quy giữ nguyên byte và hash nguồn; [manifest bằng chứng cuối](w11-evidence/final-2026-10-22/sha256-manifest.json) bao phủ toàn bộ tệp bàn giao trong thư mục này.

Chi phí dịch vụ ngoài **0 USD**; không gọi mô hình/gửi thư thật/upload Cloudinary. Không sửa vé/kế hoạch/handoff, không dọn worktree/snapshot/ZIP hoặc đụng `tmp/t01a-clean-ff797eb`.

**Chờ điều phối nghiệm thu W-11.** Sau khi đạt và ghép, mới tạo worktree W-08 từ main mới. Giữ lecture-2, SSE sau cổng, media/source kiểm quyền và không hiện bản lùi theo việc được giao. W-09/W-10 sau đó theo lịch điều phối; không mở đồng thời ba vé sửa LearningGateway. Không còn câu hỏi chức năng cần chủ dự án chốt trong phạm vi W-11 hiện hành.
