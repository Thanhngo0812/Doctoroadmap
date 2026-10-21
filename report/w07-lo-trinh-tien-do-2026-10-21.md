# W-07 — Lộ trình và tiến độ, 2026-10-21

**Đã triển khai; bàn giao mã và kết quả kiểm để điều phối soát. Người làm không tự đóng vé.** Nhánh `work/w07-roadmap-progress`, worktree một cấp `tmp/w07-roadmap-progress`, tách từ main `eb6af08`. Giữ nguyên W-06/W-03 và các snapshot, không ghép/push main.

## Phạm vi

- Gateway `get_progress`, `set_progress`, roadmap thêm tổng tiến độ khoá/module; HTTP GET progress và PUT node `{learned: boolean}`; React lộ trình/module mở/gập, danh sách bài học theo thứ tự và đánh dấu/bỏ dấu.
- Tái dùng LearningGateway/WebLearningRuntime/PostgresPhaseBStore. Actor từ phiên; doc/version từ course đã phát hành. Không thêm bảng hoặc migration. Không sửa composition; W-14 tiếp nhận độc lập qua điều phối, không lấy đè tệp nhánh khác.
- Hợp đồng `progress-1` giữ nguyên, chỉ thêm `course_id`; PUT trả full snapshot. Body boolean strict, không nhận trường owner/doc/version. Roadmap giữ metadata/concept fields, thêm summary. [Hợp đồng API](w07-evidence/api-contract.md).
- Không triển khai bài giảng, chat, quiz, thư viện W-08…W-10. Việc gọi `mark_quiz_correct` trong test chỉ kiểm quy tắc tiến độ qua use case hiện có, không phải giao diện/HTTP quiz mới.
- Nhãn giao diện dùng “tài liệu” và “bài học”; node/concept trong hợp đồng giữ tên kỹ thuật hiện có. Hai khoá cùng tài liệu dùng chung tiến độ của cùng một người theo spec; hai người luôn cách ly.

## Nguồn và thiết kế

- Đọc AGENTS.md, vé W-07, báo cáo nghiệm thu W-06, mục 4 lệnh giao việc sau W-06, quy trình nhánh/ghép main, runbook fixture; spec Pha B2 `progress-1`, web mục 7/API, CSDL Pha B, thiết kế lộ trình/token/khung/trạng thái/truy cập.
- `8b6e500` đã có trên main nền. Tham khảo thêm report/preview W-07 của nhánh thiết kế `work/w24-figma-evidence` tại `c1df32a`, chỉ đọc; không tự nhập mã hoặc tuyên bố đã nghiệm thu Variables/Cloud/Figma W-24.
- Áp dụng `design-taste-frontend` app screen, `frontend-ui-engineering`, `api-and-interface-design`, `test-driven-development`, `incremental-implementation`, `security-and-hardening`, `ponytail`, `git-workflow-and-versioning`, `documentation-and-adrs`, và soát chất lượng. Hướng draw `achromatic-ledger`, seed70321, giữ palette/type WayFinder. [Quyết định thiết kế](w07-evidence/design-notes.md).
- Logo Artboard24/28, Be Vietnam Pro, token màu/khoảng cách/motion đã chốt. Native checkbox, focus/keyboard và vùng bấm44px, giảm chuyển động. Không nút hoặc số liệu nghiệp vụ giả cho các tính năng ngoài vé.

## Dữ liệu và cách ly

Chép **3.144 tệp** từ hai manifest trong `report/w06-fixtures-evidence-2026-10-20/bundles.json`; SHA-256 nguồn/đích khớp, không links, không nhập learner store CLI. Bỏ một tệp learner store khỏi tổng3.145 của manifest. Doc-1 **v8**, doc-6v29, bốn graph còn lại đúng gói. [Log đối chiếu](w07-evidence/fixture-copy.log). Không mở kho live chung/tập giữ lại.

Test dùng PostgreSQL thật ở DB UUID riêng, mô hình/Mailer/MediaStore giả; không gửi thư, không upload Cloudinary, không gọi Gemini. Giữ Vertex là transport backend. Không seed hoặc mutation trên DB phát triển của chủ dự án.

## Kiểm thử và bằng chứng

### Mốc mã và lệnh

Mốc kiểm cuối: **`8f7fd4e21e87a20102ecdf576e1c6e35a4912ed7`**. Đã chạy `git merge main` trước cổng: main `eb6af08` đã có đầy đủ, không xung đột. Các commit sau cổng chỉ lưu báo cáo/bằng chứng, không sửa mã/test/harness. Các mốc triển khai:

- `86cbb02`: gateway/API/OpenAPI và test PostgreSQL.
- `e1b5af1`: React lộ trình/tiến độ.
- `b00b13e`: harness cách ly và README.
- `3e9975b`, `e01b8f4`: sửa selector và chờ navigation trong harness.
- `8c54b14`: đặt accessible label lên native progress.
- `8f7fd4e`: menu tài khoản mobile gọn, tên đầy đủ giữ trong accessible name.

| Cổng | Kết quả cuối | Bằng chứng |
|---|---|---|
| Toàn repo, PostgreSQL bắt buộc | **2.114 đạt, 1 bỏ qua**, native exit0; 368,79 giây | [JUnit](w07-evidence/full-python-final.xml), [log](w07-evidence/full-python-final.log) |
| React | **85 đạt**, không bỏ qua, native exit0 | [JUnit](w07-evidence/react-final.xml), [log](w07-evidence/react-final.log) |
| TypeScript/Vite build | Native exit0 | [log](w07-evidence/build-final.log) |
| Phá guard backend | **8/8** bị assertion bắt, không setup error; phục hồi mã | [ledger/lệnh](w07-evidence/mutations.json) |
| Phá guard UI | **2/2** bị assertion bắt; phục hồi đúng byte | [ledger/lệnh](w07-evidence/ui-mutations.json) |

Một test bỏ qua là Cloudinary live không bật, đúng yêu cầu; PostgreSQL không bị bỏ qua. Lượt Python đầu trên backend tương tự cũng đạt2.114/1skip nhưng chưa có các bản vá UI/harness cuối; giữ [JUnit/log preflight](w07-evidence/python-preflight.xml), không thay lượt chốt.

Lệnh chạy từ gốc worktree; log giữ native exit code của tiến trình, không lấy warning PowerShell làm kết quả:

```powershell
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py -o addopts= -q --basetemp=tmp/cong-w07-2 --junitxml=tmp/cong-w07-2.xml
npm.cmd --prefix src/web/frontend test -- --pool=threads --maxWorkers=1 --reporter=default --reporter=junit --outputFile=C:/Users/ngoco/Desktop/Doctoroadmap/tmp/w07-roadmap-progress/report/w07-evidence/react-final.xml
npm.cmd --prefix src/web/frontend run build
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe -X utf8 scripts/w07_web_runtime.py
```

### Các bất biến đã kiểm

- `test_progress_is_isolated_between_members_using_independent_postgres_runtimes`: A đánh dấu, B không đổi; B bỏ dấu, A vẫn learned. Hai engine/store/gateway riêng; truy vấn SQL độc lập xác nhận owner và trạng thái từng người.
- `test_unmark_then_correct_quiz_keeps_learner_choice_through_gateway`: gọi quiz progress use case qua context gateway sau bỏ dấu vẫn `not_learned/source=learner`.
- Hai test race `test_quiz_read_then_concurrent_learner_unmark_is_serialized_by_postgres` và `test_learner_unmark_transaction_then_concurrent_quiz_respects_learner_source` ép hai thứ tự bằng Event và quan sát `pg_stat_activity`, rồi đọc lại SQL. Phá atomic của quiz làm sai chính trạng thái cuối, không chỉ lỗi vì thiếu lock.
- HTTP kiểm node ngoài/non-learnable404, boolean strict422, trường owner giả422, guest401, CSRF403, outsiderGET/PUT404. Inventory tự liệt kê route vẫn kiểm mọi route mới; body hợp lệ riêng cho PUT progress để test chạm guard thay vì dừng ở validation.
- Roadmap giữ thứ tự graph đã phát hành, lọc node không learnable, số học tổng khoá/module khớp. Không lấy kết quả memory/JSON SA-47 thay PostgreSQL; không tuyên bố toàn SA-34 hoặc SA khác đạt theo W-07.
- UI cập nhật tức thời từng node, khoá submit trùng cùng node; full response cũ chỉ merge node vừa xác nhận. Lỗi server hoặc200 thiếu node cần lưu đều rollback;401 thu hồi trạng thái phiên. Huỷ request khi rời course, controller cũ không xoá request mới cùng node ID.

### RED/GREEN và chẩn đoán

- `w07-red.xml`, `w07-red2.xml` là hai lỗi setup ban đầu (email fixture, membership via), không tính là RED nghiệp vụ. `w07-red3.xml` là RED vì gateway chưa có phương thức tiến độ; `w07-green*.xml` lưu các lượt sau triển khai.
- Frontend có log lỗi trung gian nhưng không giữ được JUnit RED đầu tiên của nhóm test mới; không gán XML Python thành React. Hai mutation rollback/stale-snapshot và [RED accessible progress](w07-evidence/react-progressbar-red.xml) / [GREEN](w07-evidence/react-progressbar-green.xml) là bằng chứng falsifiable React được lưu.
- Runner mutation đầu chạy được5case rồi dừng vì needle newlineCRLF, trước khi sửa source cho case đó. Sửa riêng runner và chạy phần còn lại;8case cuối trong ledger đều assertion fail/native1, nguồn phục hồi. Không coi lỗi runner là phép phá đạt.
- Test Python focused đầu gặp thiếu basetemp parent, lưu `final-python.xml`; lượt sau `final-python2.xml` đạt27, `architecture.xml` đạt5. Hai thư mục basetemp giữ local và được loại khỏi Git.
- Browser lượt đầu lỗi selector thiếu dấu trong “Tiến độ cả khoá”; lượt sau axe phát hiện aria-label gắn `div` generic, đã sửa nativeprogress và thêm RED/GREEN. Lượt tiếp các assertion đã đạt nhưng Promise navigation chưa chờ gây exit1 lúc đóng context; đã sửa await. Giữ `browser-*-diagnostic.*`, không ghi những lượt exit1 là đạt.
- Một số traceback pytest in token phiên của tài khoản test DB tạm. Bản bàn giao chỉ che chuỗi token, giữ assertion/trạng thái; bản thô giữ local và SHA-256 tại [log-redactions](w07-evidence/log-redactions.json). Không có credentials `.env` trong bàn giao.
- Log/XML được chuẩn hoá UTF-8 và bỏ khoảng trắng cuối dòng để Git kiểm sạch; các bản trước định dạng giữ dưới `tmp/` bị Git bỏ qua. Không thay kết quả hoặc assertion.

## Phối hợp và phạm vi tích hợp

API shape công bố trong [hợp đồng](w07-evidence/api-contract.md). **Composition thay đổi: không có**; không sửa migration đã ghép và không tạo migration rỗng, head vẫn `w06_0005`. Lõi W-14 có thể tiếp tục service/worker độc lập; điều phối quyết định tuyến schema và ghép, không lấy đè tệp giữa hai nhánh.

Đánh dấu thành viên/quyền, graphcache và store dựa W-06; phần mới không tự nâng quyền admin. Bài giảng/chat/quiz/thư viện chỉ có vùng dự trữ tĩnh phù hợp bố cục, không action giả. Các tiêu đề nội dung do graph trả được giữ nguyên, chỉ đổi nhãn sản phẩm theo yêu cầu chủ dự án.

## Browser, JSON và thiết kế cuối

- Browser trên mốc `8f7fd4e`: **11 assertion luồng**, **6 ảnh HTTP thật** sáng/tối ở390/768/1280, **12 ảnh mock** empty/loading/error ghi `acceptance:false`; native exit0. [Audit](w07-evidence/browser-audit.json), [log](w07-evidence/browser-final.log), [runtime/SQL](w07-evidence/runtime.json), [tóm tắt](w07-evidence/acceptance-summary.json).
- Đăng ký UI hai tài khoản, cùng tham gia mẫu doc-1v8; mở/gập module, đánh dấu bằng click/Space và bỏ dấu qua PUT thật, route module đọc cùng tiến độ. GET/SQL độc lập xác nhận A có đúng2bản ghi:1learned/1not_learned, B không có bản ghi. Reload và tổng hiển thị khớp GET.
- Lỗi rollback500 được **chèn qua Playwright đúng1PUT**, không phải lỗi server thật. Quan sát checkbox checked khi response bị giữ, sau500 trở về unchecked và báo lỗi. GET thật và SQL độc lập xác nhận không có bản ghi của lần lỗi. Không mô phỏng các PUT thành công.
- Axe cả6màn: **0violation, 0incomplete**. Kiểm tràn ngang,44px, nativecheckbox/keyboard/focus, font tải thật và reducedmotion đạt. SVG contrast tính từ foreground/background thật ≥3:1.
- Giữ **19console error thô**, cả19đối chiếu hẹp:2bootstrap401,1rollbackPUT500chèn,4GET500choảnhmock,12thôngbáoCSPprobeaxe. Không có console/page/request/external failure ngoài dự kiến; không nới CSP hoặc tắt rule. Font ngoài chỉ các originGoogle đã chốt.
- Taste source lint **0FAIL/0WARN**; inspector **0FAIL/1WARN `unused-canvas`** ở1280. Cột chính và khung dự trữ bên phải giữ bố cục spec, nội dung dự trữ ngắn làm vùng phải ít chữ; không tạo chat/thư viện giả để lấp. Giữ nguyên cảnh báo trong [JSON](w07-evidence/taste-inspect/report.json), không nói đã hết WARN. Inspector dùng snapshot DOM thật bỏscript và CSSbuildinline, chỉ kiểm thiết kế (`acceptance:false`); hành vi/axe kiểm trên app thật.
- Menu tài khoản ở390dùng chữ “Tài khoản” để tránh cắt tên dài; accessible name vẫn chứa tên đầy đủ. Giữ logo/font/token theo W-24. [Soát UI](w07-evidence/ui-review.md), [soát frontend](w07-evidence/frontend-review.md), [soát harness](w07-evidence/browser-review.md). Các review độc lập chỉ đọc, không ghi là agent đã chạy lại test của root.

### Tệp bàn giao trực tiếp

- JSON thật: [roadmap doc-1](w07-evidence/roadmap-doc-1.json), [progress trước](w07-evidence/progress-before.json), [sau lưu/rollback](w07-evidence/progress-after-rollback.json), [người B](w07-evidence/progress-learner-b.json).
- 390: [sáng](w07-evidence/roadmap-390-light.png), [tối](w07-evidence/roadmap-390-dark.png).
- 768: [sáng](w07-evidence/roadmap-768-light.png), [tối](w07-evidence/roadmap-768-dark.png).
- 1280: [sáng](w07-evidence/roadmap-1280-light.png), [tối](w07-evidence/roadmap-1280-dark.png).
- [Video mở/gập/đánh dấu/bỏ dấu/rollback](w07-evidence/w07-roadmap-progress.webm). Các ảnh mock có tên `mock-only-*`, không thay luồng thật. Video dùng tài khoản test giả, không credentials chủ dự án.

Đã phục hồi riêng2JSON W-06 do test hồi quy sinh lại ID ngẫu nhiên, giữ bằng chứng W-06 nguyên bản; JSON W-07 lưu ởthưmục riêng. Không sửa vé/kếhoạch/handoff. Không dọn worktree/snapshot/ZIP, không đụng `tmp/t01a-clean-ff797eb`. **Chi phí0USD, không gọi mô hình/mail/cloudthật.** Điều phối quyết định nghiệm thu và ghép.

## Chạy dịch vụ

[README](../src/web/README.md) đã đổi lệnh khởi động sang worktree W-07: PostgreSQL, backend, React/Vite hoặc build một nguồn, origin/CSRF, cách dừng. Lệnh nghiệm thu luôn dùng runner `scripts/w05_run_tests.py`, không pytest trần.
