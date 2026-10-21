# W-06 — React và tích hợp, 2026-10-21

**Đạt kiểm local trong worktree tích hợp; sẵn sàng điều phối soát và ghép. Chưa ghép main.** Nhánh `work/w06-web`, worktree `tmp/w06-web`; giữ nguyên worktree W-03 để đối chiếu.

## Phạm vi và hợp đồng

- Tạo từ main `29e4350`, đã nhận backend bàn giao `8380a1a` bằng merge `8c3bd97`. Backend/gateway API thật có từ `c694149`; mốc test backend cuối `4f676d9`. Không sửa mã backend, composition, migration hoặc OpenAPI của nhóm lõi.
- Hợp đồng: `/api/v1/courses` trả `owned/joined/samples`; các nhóm luôn có mặt. Card chứa status, owner, module_count, member_count chỉ cho owner, progress và resume cá nhân. Mẫu chưa tham gia chỉ có metadata; không giả tiến độ hoặc quyền học.
- Join POST `/{cid}/join-sample` gửi `{}` với cookie/CSRF; chỉ chuyển thẻ sang nhóm đã tham gia sau phản hồi thành công. Mỗi khoá chỉ có một yêu cầu UI đang chạy. Khi thất bại giữ thẻ mẫu và báo lỗi tại thẻ; sau thành công chuyển focus tới Học tiếp.
- Học tiếp dùng đúng route spec `/khoa-hoc/:cid/module/:mid`, với `mid` từ resume API; không tự suy phiên bản graph hoặc module đầu ở client. Entry gọi detail và roadmap sau khi backend kiểm membership, chỉ hiển thị metadata và mô tả module được chọn. Mô tả hỗ trợ chuỗi và mảng object `text` theo hợp đồng bản 2.
- **Không xây lộ trình đầy đủ/lesson/chat/quiz W-07…W-10.** Liên kết `/tai-len` là bàn giao route cho W-14; chưa có upload thật ở W-06. Link mời thuộc W-11: trạng thái rỗng hướng dẫn mở link đã nhận, không tạo luồng tham gia link giả.
- Trang chủ `/` và đăng nhập/đăng ký thành công về `/khoa-hoc`; đường quay lại nội bộ từ guard được giữ, URL ngoài/`//`/backslash/khoảng trắng bị loại. `/tai-khoan` và luồng xác minh/reset cũ còn nguyên.

## Thiết kế và skills

- Đọc vé W-06, chức năng mục khoá học/quyền/API, CSDL course/membership, thiết kế mục thương hiệu/token/khung/trạng thái/truy cập và bàn giao local W-24. W-24/Figma chưa đóng toàn bộ không chặn React.
- Áp dụng `design-taste-frontend` theo **app screen**, hướng `editorial-greeting`, seed **307593073**, giữ palette/type thương hiệu. Spec ưu tiên: h1 là tên trang thay lời chào, header64/56, grid1/2/3 tại390/768/1280; không thêm KPI hoặc hình giả. [Quyết định CSS](w06-web-evidence/design-notes.md).
- Artboard24 sáng/28 tối, Be Vietnam Pro, token thực. Bề mặt phẳng, màu dùng cho trạng thái và thao tác. Focus/keyboard44px, motion120/200 có giảm chuyển động.
- Dùng `frontend-ui-engineering`, `api-and-interface-design`, `test-driven-development`, `incremental-implementation`, `ponytail`, `git-workflow-and-versioning`, `code-review-and-quality`; đọc bộ quy tắc từ `.agents/skills` của workspace chung. Tái dùng AuthProvider, apiJson/CSRF, token và component styling hiện có; không thêm thư viện.
- Chromium/Playwright thật qua công cụ đã có trong repo; không có Chrome DevTools MCP khả dụng được dùng, không ghi là đã kiểm MCP. Inspector taste chạy trên snapshot DOM thật đã bỏ script, chỉ dùng để đo thiết kế; kiểm hành vi/auth/accessibility chạy trên ứng dụng thật.

## Kiểm và bằng chứng

Mã frontend cuối: **`627578e`**; các mốc trước là `2459b84` (tích hợp), `8e5ec1e` (SVG), `f1ec3bb` (gutter). Chủ dự án yêu cầu dùng **“tài liệu”** và **“bài học”**: đã đổi nhãn giao diện, gồm tiến độ, không đổi schema/API hoặc số liệu do backend tính. Toàn bộ đầu vào Python/backend/test/design không đổi từ mốc ghép `8c3bd97`; cổng Python kiểm mã backend đã ghép, còn React/build/browser chạy lại trên frontend cuối sau thay chữ.

| Cổng | Kết quả | Bằng chứng |
|---|---|---|
| Python toàn repo, gồm PostgreSQL thật | **2.105 đạt, 1 bỏ qua**, 0 lỗi/fail; 715,56 giây | [JUnit](w06-web-evidence/full-gate.xml), [log](w06-web-evidence/full-gate.log) |
| React | **77 đạt**, không bỏ qua | [JUnit](w06-web-evidence/react-final.xml), [log](w06-web-evidence/react-final.log) |
| TypeScript + Vite build | Exit 0 | [log](w06-web-evidence/build.log) |
| HTTP/PostgreSQL/trình duyệt | 9 assertion đạt; 6 ảnh thật, 12 ảnh trạng thái mock ghi riêng | [audit](w06-web-evidence/browser-audit.json), [runtime/SQL](w06-web-evidence/runtime.json) |
| Accessibility | 6 màn: **0 violation, 0 incomplete**; overflow, 44×44, focus, icon contrast đạt | [audit](w06-web-evidence/browser-audit.json) |
| Console/network | 0 lỗi ngoài dự kiến; 0 page error/request failure/request ngoài allowlist | [audit gồm raw log](w06-web-evidence/browser-audit.json) |

Một test bỏ qua là Cloudinary live opt-in, đúng yêu cầu không gọi Cloudinary; PostgreSQL bắt buộc không bị bỏ qua. [Tóm tắt máy đọc](w06-web-evidence/acceptance-summary.json).

- RED React trước triển khai: 8 ca mới fail vì trang W-06 chưa có; RED trang chủ: 6 fail/8 đạt vì đích cũ là tài khoản; RED focus sau join: 1 fail/13 đạt khi focus bị mất. Các log sẽ lưu trong thư mục bằng chứng.
- Bổ sung regression cho card building/failed, progress0/null, mẫu/prod rỗng, lỗi tải/thử lại, join đầy, request cookie/CSRF/body, guest, entry union mô tả và outsider404. Ba assertion auth cũ về tài khoản được đổi sang trang khoá học đúng yêu cầu W-06; vẫn kiểm generic/rate limit/logout/CSRF/toast. Assertion status toast được định vị đúng thông báo khi đồng thời có trạng thái tải danh sách.
- Fixture **3.144 tệp** được chép bằng helper backend theo hai manifest cố định/SHA-256, không sao chép kho CLI. Không có junction/symlink/hardlink; không mở live.json hoặc tập giữ lại. Đối chiếu nguồn/đích chạy thành công trong worktree này; [manifest và bằng chứng theo tệp](w06-evidence/fixture-copy.json).
- Browser harness: DB PostgreSQL UUID riêng, Argon2 thật, sáu graph thật gồm doc-1v8; FakeMailer, MemoryMediaStore, provider/ADC/SMTP/Cloudinary bị chặn. Giao dịch và membership được đọc lại từ kết nối SQL độc lập; không seed DB phát triển của chủ dự án.
- Những ảnh trạng thái được dựng bằng chặn phản hồi API chỉ là **bằng chứng thị giác mock**, không thay kiểm tham gia thật; audit đánh dấu `acceptance:false`. JSON danh sách/detail/roadmap lưu từ HTTP thật, không từ mock.
- Lượt đầu không kết nối được PostgreSQL vì Docker Desktop chưa bật; đã khởi động Docker và `db-test`, chạy basetemp mới. Lượt audit sau ghi lỗi401 lúc bootstrap,500 cố ý và CSP do probe axe; phân loại theo đúng stage/request, giữ rawlog, không nới CSP hay bỏ quy tắc accessibility.

## Kết quả tích hợp và giới hạn

- Đăng ký từ UI tạo tài khoản PostgreSQL thật, cookie/CSRF thật. GET trả sáu mẫu. Tham gia doc-1 bằng click, doc-6 bằng keyboard; reload vẫn có hai khoá. Doc-1 **v8**, không khóa v45/v57. Học tiếp đến đúng course/module của API, đối chiếu tiêu đề UI với JSON thật: [trước tham gia](w06-web-evidence/courses-before-join.json), [sau](w06-web-evidence/courses-after-join.json), [detail](w06-web-evidence/doc-1-detail.json), [roadmap](w06-web-evidence/doc-1-roadmap.json).
- Gửi lại join kèm owner/owner_id, doc/version giả: 200 idempotent, vẫn là learner của tài khoản phiên và graph đúng. Outsider gọi detail/roadmap/join khoá riêng đều 404. SQL độc lập xác nhận 6 owner mẫu, 2 learner/via=sample đúng actor, khoá riêng chỉ có seed admin làm owner. [Bằng chứng](w06-web-evidence/runtime.json).
- Runtime dùng PostgresPhaseBStore; UI W-06 chỉ list/join/detail nên **0 phase_b_record là bình thường**, không tuyên bố UI đã ghi tiến độ. Test backend từ lõi kiểm ghi Pha B/quyền/spend trên PostgreSQL; giữ [8 phép phá guard bàn giao từ lõi](w06-evidence/mutations.json), không ghi là web đã chạy lại chúng.
- FakeMailer/MemoryMediaStore, chặn entry point model/ADC/SMTP/Cloudinary: **0 lần gọi mô hình, 0 USD**, không thư thật hoặc upload cloud. DB test UUID được xoá sau kiểm. Không seed DB phát triển của chủ dự án.
- Phá riêng guard ẩn nhóm mẫu rỗng: test thất bại vì heading mẫu xuất hiện sai, không lỗi setup; phục hồi nguồn thì đạt. [Mutation](w06-web-evidence/ui-guard-mutation.json), [RED](w06-web-evidence/empty-samples-guard-red.xml), [GREEN](w06-web-evidence/empty-samples-guard-green.xml).
- Giữ **17 console error thô**, tất cả đối chiếu với trường hợp cố ý: 1 bootstrap401, 4 phản hồi500 mock, 12 thông báo CSP probe axe. Phân loại hẹp theo stage/URL/thông báo, không nới CSP hoặc tắt rule axe. Ký tự icon cũ làm axe incomplete đã thay SVG; lỗi UUID/chuỗi trong harness đã chuẩn hoá. Các log `browser-diagnostic-*.log` lưu chẩn đoán cũ, không thay kết quả cuối.
- Taste inspector **0 FAIL, 1 WARN `below-fold`** ở 1280: 2/6 block bắt đầu ở màn hình đầu. Giữ thứ tự nhóm theo spec và thẻ đầy đủ, khoá đang học ở trên và mẫu ở dưới. [Kết quả](w06-web-evidence/taste-inspect/report.json). Gutter CSS16/24/32; ở1280 nội dung cách mép40 do max-width1200 căn giữa, header cách32. Không báo sai rằng toàn trang đều cách mép32.
- Snapshot kiểm lại cuối: **3.144 tệp** khớp SHA-256; không links/learner cache CLI. [Lượt đối chiếu cuối](w06-web-evidence/fixture-copy-run.log).

## Ảnh/video và soát độc lập

- 390: [sáng](w06-web-evidence/courses-390-light.png), [tối](w06-web-evidence/courses-390-dark.png).
- 768: [sáng](w06-web-evidence/courses-768-light.png), [tối](w06-web-evidence/courses-768-dark.png).
- 1280: [sáng](w06-web-evidence/courses-1280-light.png), [tối](w06-web-evidence/courses-1280-dark.png).
- [Video luồng thật](w06-web-evidence/w06-join-resume.webm). 12 ảnh `mock-only-{empty,loading,error}-{390,1280}-{light,dark}.png` chỉ chứng minh thị giác, có `acceptance:false`; không thay kiểm tham gia thật và không nằm trong video luồng chính.
- [Soát UI/code](w06-web-evidence/ui-review.md), [soát harness/bằng chứng](w06-web-evidence/browser-review.md). Ba agent Luna hỗ trợ CSS/soát UI, runtime PostgreSQL và audit trình duyệt; root tích hợp/chạy kiểm/chốt bàn giao. Không nhắn sang phiên điều phối khác.

## Lệnh tái hiện

Chạy trong `tmp/w06-web`, cần Docker `db-test`, snapshot theo manifest và Playwright có sẵn ở workspace chung. Runner đọc `WAYFINDER_TEST_DATABASE_URL` từ môi trường hoặc `.env` local/chung; không in credentials. Khi chạy lại cổng toàn repo dùng basetemp mới nếu thư mục cũ còn tồn tại.

```powershell
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe -X utf8 src/web/backend/tests/copy_w06_fixtures.py
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py -o addopts= -q --basetemp=tmp/w06-web-full-gate2 --junitxml=report/w06-web-evidence/full-gate.xml
npm.cmd --prefix src/web/frontend test -- --pool=threads --maxWorkers=1 --reporter=default --reporter=junit --outputFile=C:/Users/ngoco/Desktop/Doctoroadmap/tmp/w06-web/report/w06-web-evidence/react-final.xml
npm.cmd --prefix src/web/frontend run build
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe -X utf8 scripts/w06_web_runtime.py
```

Runtime tự gọi `scripts/w06_web_check.cjs`; không chạy Node checker vào server/DB phát triển của chủ dự án.

## Ghi nhận cho W-14, chưa triển khai trong vé này

Chủ dự án hỏi đặt tên khoá học trước khi index. Hướng đề xuất: chọn tài liệu → kiểm tệp → nhập/sửa tên khoá ở bước xác nhận → bấm “Dựng lộ trình” → mới xếp hàng xử lý; nếu bỏ trống lấy tên tài liệu. Spec có bước xác nhận và title mặc định từ tiêu đề/tên tệp, nhưng chưa ghi rõ ô nhập tên tại đây. Cần đưa yêu cầu này vào hợp đồng W-14 khi mở vé; chưa tự sửa vé/kế hoạch/handoff.

## Bàn giao

Backend W-06 đã nhận và kiểm chung, không còn phụ thuộc mở chặn nghiệm thu local. Người điều phối là đầu mối ghép và đóng vé; người làm vé không tự ghép main. W-14 nối upload/worker, W-07 dựng lộ trình đầy đủ. Không sửa vé/kế hoạch/handoff, không làm W-04, không dọn worktree/snapshot và không đụng `tmp/t01a-clean-ff797eb`.
