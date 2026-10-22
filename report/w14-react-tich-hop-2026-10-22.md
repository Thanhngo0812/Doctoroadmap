# W-14 — React và tích hợp bộ dựng giả — 2026-10-22

## Đợt cuối sau nhận backend đã duyệt — đã chạy cổng, chờ điều phối nghiệm thu

- Backend/schema được điều phối duyệt tại `4dbfe8e`, ghép main `a572459`. Đã merge main `66cd439` thành `756502f`; main nhận tiếp SA-53 khi lượt kiểm đang chạy nên merge lại main mới nhất lúc đó `5e524d3` thành `5197e10`. Không rebase, không đổi nhánh thư mục chung; W-11 giữ riêng `a53f0d3`.
- Main có thêm commit tài liệu `8b85d19` trong lúc kiểm; merge lần ba thành `4dd74ce`. `git diff 6b4a8cd 4dd74ce -- src scripts tests design` rỗng. Vẫn chạy lại cổng để bàn giao đúng đỉnh sau nhận main mới nhất.
- **Chủ dự án đã chốt main nền `8b85d19` cho đợt này**, sau khi được hỏi rõ mục3.5 của quy trình. Commit tài liệu đến sau `207c6c0` nằm ngoài mốc đã chốt; không tiếp tục lặp cổng vì tài liệu đổi. Backend đã duyệt vẫn là `a572459`.
- Đỉnh mã cho lượt cuối: **`da61cdc200ba02f3e445d63684998a368cf01fb9`**, có cả câu hướng dẫn sau `953240b`. Hai DTO đã soát vẫn nguyên; không thêm migration hoặc đổi khoá/trạng thái W-25. So với `6b4a8cd`, harness chỉ đổi thư mục đích bằng chứng sang `run3`. README/báo cáo cập nhật sau kiểm không đổi mã chạy.
- Tại `b050ac7`, bỏ đúng32 tệp synthetic image khỏi index bằng `git rm --cached`; còn đủ32 tệp local. Ignore `/basetemp*/`, đồng thời ignore các input fixture tái sinh ở thư mục con. Đỉnh mới không có basetemp trong `git ls-tree`; [preflight và hash guard](w14-react-evidence/final-main-2026-10-22-run2/preflight.json).
- Đã phá lại3 guard UI và2 guard DTO, tuần tự trước full gate/server: **5/5 native exit1 qua assertion, 0 setup error**, nguồn phục hồi đúng SHA-256. DTO mutation dùng nhầm `job.upload_id` cho course dùng lại và trả `confirmed_at=None` sau xác nhận; không chỉ phá tên trường. [UI ledger](w14-react-evidence/final-main-2026-10-22/ui-mutations/results.json), [DTO ledger](w14-react-evidence/final-main-2026-10-22/dto-mutations/results.json). Hash còn khớp ở đỉnh cuối.
- Lượt đầu trên `fe50c5c`/main `66cd439`: Python **2.172 đạt, 1 Cloudinary live bỏ qua**, React104/build đạt. Browser **native exit1** tại chờ worker thử lại hoàn tất240giây, `lastException=null`; DB đã dọn. Chưa chạy SQL cuối hoặc toàn bộ trạng thái nên **không dùng lượt này làm bằng chứng đạt**. Nghi tranh chấp I/O do chạy cùng full Python; chưa coi đó là nguyên nhân đã chứng minh. Giữ [log browser đỏ](w14-react-evidence/final-main-2026-10-22/browser.log), [audit từng trạng thái đã kiểm](w14-react-evidence/final-main-2026-10-22/browser-audit.json), [cleanup](w14-react-evidence/final-main-2026-10-22/runtime.json), [JUnit Python lượt đầu](w14-react-evidence/final-main-2026-10-22/python.xml).
- Lượt2 tại `6b4a8cd`/main `5e524d3`, basetemp `tmp/w14-final-main-py-20261022-2`: Python **2.176 đạt, 1 bỏ qua**, React **104 đạt**, build native exit0. Browser chạy riêng sau Python và **đạt native exit0**:47 ảnh,225 phản hồi/206 payload JSON,14 audit Axe,0 violation/incomplete/console error/page error/failed request. SQL độc lập xác nhận5 course/4 build, upload/tên riêng, reuse chỉ1 worker attempt và5 dòng usage giả tổng0,002USD; DB được dọn. Giữ [bằng chứng lượt2](w14-react-evidence/final-main-2026-10-22-run2/); chỉ kết luận không tái hiện timeout khi chạy riêng, chưa khẳng định nguyên nhân I/O.
- Lượt3 dùng basetemp mới `tmp/w14-final-main-py-20261022-3`; browser chạy sau full Python, giữ timeout240giây/assertion. **Tất cả native exit0** trên `da61cdc`, không sửa mã chạy sau đó. [Tóm tắt nguồn/cwd/argv/kết quả](w14-react-evidence/final-main-2026-10-22-run3/final-gate-summary.json).

| Cổng cuối tại `da61cdc` | Kết quả | Bằng chứng |
|---|---|---|
| Python toàn repo + PostgreSQL bắt buộc | **2.176 đạt, 1 Cloudinary live bỏ qua**, 0 fail/error, native0; pytest528,51giây | [log](w14-react-evidence/final-main-2026-10-22-run3/python.log), [JUnit](w14-react-evidence/final-main-2026-10-22-run3/python.xml), [exit](w14-react-evidence/final-main-2026-10-22-run3/python-exit.txt) |
| React | **104 đạt**, 0 skip/fail/error, native0 | [log](w14-react-evidence/final-main-2026-10-22-run3/react.log), [JUnit](w14-react-evidence/final-main-2026-10-22-run3/react.xml), [exit](w14-react-evidence/final-main-2026-10-22-run3/react-exit.txt) |
| TypeScript/Vite | Đạt, native0 | [log](w14-react-evidence/final-main-2026-10-22-run3/build.log), [exit](w14-react-evidence/final-main-2026-10-22-run3/build-exit.txt) |
| Browser HTTP/worker/PG thật, provider giả | **13 nhóm assertion,47 ảnh,235 phản hồi API/216 payload JSON**, native0 | [log](w14-react-evidence/final-main-2026-10-22-run3/browser.log), [audit](w14-react-evidence/final-main-2026-10-22-run3/browser-audit.json), [JSON thật](w14-react-evidence/final-main-2026-10-22-run3/http-responses.json), [video](w14-react-evidence/final-main-2026-10-22-run3/w14-upload-build.webm), [exit](w14-react-evidence/final-main-2026-10-22-run3/browser-exit.txt) |
| Axe/console/network | **14 audit,0 violation/0 incomplete; 0 lỗi console ngoài dự kiến,0 page error,0 failed request/font failure** | [audit có route/state/theme/width](w14-react-evidence/final-main-2026-10-22-run3/browser-audit.json) |
| SQL độc lập + cleanup | 5 course đúng chủ,4 build có trạng thái cuối đúng; hai upload đã xác nhận riêng, hai tên riêng; reuse chỉ1 worker attempt;5 dòng usage giả tổng0,002USD; DB/worker/browser/server8014 đã dừng | [kết quả SQL](w14-react-evidence/final-main-2026-10-22-run3/runtime.json), [kiểm đọc lại DB/cổng](w14-react-evidence/final-main-2026-10-22-run3/cleanup-check.json) |

29 thông báo console dự kiến được đối chiếu riêng:1 GET `/me`401 lúc chưa đăng nhập và28 probe CSP từ14 lần Axe. Mỗi cảnh báo font CSP phải khớp đúng request bị chặn; không tắt CSP hoặc lọc lỗi sản phẩm. Phạm vi thật/giả: FastAPI, session/CSRF, PostgreSQL, BuildService/BuildWorker/PostgresPhaseBStore thật; ManifestFakeBuildRunner/ScriptedBuildRunner, MemoryMediaStore và FakeMailer giả. Không intercept/mock API để thay trạng thái UI. **Chi dịch vụ ngoài0USD**;0,002USD trong ledger là dữ liệu giả kiểm ghi sổ.

Đã kiểm lại nhãn/tên trước POST, poll/reload giữ build+course ID, upload/tên riêng khi dùng lại, huỷ/thử lại/rejected/succeeded, quota không giới hạn được ẩn, không hiện tiền/token/dự toán. Ảnh cancelled mới và browser assertion đã kiểm câu hướng dẫn sau `953240b`; bộ cũ trước vá câu chữ chỉ là lịch sử. Giảm chuyển động được bật bằng browser media setting mô phỏng OS, kiểm `matchMedia`, ảnh tĩnh thay GIF và không còn animation đang chạy; có kiểm native file input qua Tab/focus và vùng bấm44px.

Taste app-screen giữ hướng `framed-sheet`, Be Vietnam Pro, token/logo/ảnh chờ của main. Inspector chạy lại từ snapshot DOM/CSS thật:0 FAIL,1 WARN `hero-void` tại1280, không thay bằng dữ liệu/trang trí giả. Đã xem trực tiếp ảnh cuối upload390light, confirmation1280dark, running390dark, cancelled390dark, rejected1280light, success768dark; mọi ảnh ma trận còn lại có kiểm tràn ngang/vùng bấm tự động. Không nhận đã đánh giá thị giác thủ công từng47 ảnh.

Lệnh cuối từ gốc worktree (stdout/stderr và `$LASTEXITCODE` được lưu theo bảng trên):

```powershell
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py -o addopts= -q --basetemp=tmp/w14-final-main-py-20261022-3 --junitxml=report/w14-react-evidence/final-main-2026-10-22-run3/python.xml
npm.cmd --prefix src/web/frontend test -- --pool=threads --maxWorkers=1 --reporter=junit --outputFile=../../../report/w14-react-evidence/final-main-2026-10-22-run3/react.xml
npm.cmd --prefix src/web/frontend run build
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe -X utf8 scripts/w14_web_runtime.py
```

[Hygiene32 tệp và SHA-256](w14-react-evidence/final-main-2026-10-22-run3/handoff-hygiene.json), [hash input không track](w14-react-evidence/final-main-2026-10-22-run3/browser-inputs.json), [chuẩn hoá UTF-8/LF/khoảng trắng kèm hash trước/sau](w14-react-evidence/final-main-2026-10-22-run3/normalization.json), [manifest bằng chứng lượt3](w14-react-evidence/final-main-2026-10-22-run3/manifest.json). Giữ đầy đủ log lượt đỏ và hai lượt trước; không sửa assertion, skip hoặc timeout để xanh. Snapshot/worktree/ZIP giữ nguyên, không đụng `tmp/t01a-clean-ff797eb`. README đã có lệnh mở service.

**Bàn giao để điều phối nghiệm thu lại; người làm không tự đóng W-14, không ghép/push main.** W-11 giữ nguyên `a53f0d3`, chỉ tiếp tục sau W-14 được điều phối chấp nhận, migration `w11_0007` nối `w14_0006`. SA-34/SA khác và runner thật W-15 không được nhận là đã đạt từ lượt kiểm này.

**Phạm vi Axe:** bộ cũ chỉ có trang rejected. Harness mới kiểm7 trạng thái × sáng/tối tại1280px: upload, confirmation, running, succeeded, cancelled, retryable, rejected; chỉ nhận kết quả khi đủ14 audit. Ảnh ma trận390/768/1280 kiểm tràn ngang/vùng bấm, không được gọi toàn bộ47 ảnh là đã chạy Axe. Các mục bên dưới là **lịch sử local trước khi nhận backend đã duyệt**, không thay đợt cuối này.

## Gốc nhánh và phạm vi

- Nhánh `work/w14-react`, worktree một cấp `tmp/w14-react`, tách đúng commit W-25 `0a2afa8` (gốc W-14 `5b24ece`, có main `46703b4`). Đây là **phụ thuộc đang chờ soát**, không coi backend/schema đã đạt hoặc đã ghép main. Trước cổng tích hợp cuối phải nhận main có backend W-14/W-25 được điều phối chấp nhận.
- W-11 được giữ nguyên ở `work/w11-share-links`, worktree `tmp/w11-share-links`, commit `a53f0d3`; không nhập mã W-11 vào W-14. Tuyến migration giữ `w06_0005 → w14_0006 → w11_0007`; React không tạo migration.
- Đọc vé W-14, báo cáo backend/worker, soát W-07/W-14/W-24, spec chức năng/CSDL/thiết kế, quy trình nhánh và fixture. Chỉ làm upload/xác nhận/tên trước index, tiến trình/cancel/retry, quota và thẻ đang dựng. Không làm runner thật W-15 hoặc W-08…W-11.

## Hợp đồng và điểm bổ sung khi nối

Nguồn hợp đồng: `report/w14-backend-worker-2026-10-21.md` và DTO/API của mốc phụ thuộc. UI giữ `build_id` + `course_id`; GET poll mỗi 3 giây, cancel/retry luôn gửi `course_id`. URL `/ban-dung/:buildId?course_id=<cid>&upload_id=<uid>` giữ ngữ cảnh; không lấy chủ khoá/tài liệu từ client. Tên hiển thị lấy course thật, tên trước xác nhận điền từ tên tệp và cho sửa. Chỉ POST xác nhận sau bấm “Dựng lộ trình”.

Phát hiện thiếu hợp đồng khi quay lại từ card: BuildView cũ không có `upload_id`, trong khi confirm chỉ nhận route theo upload. Bổ sung tối thiểu `upload_id` nullable, chỉ lấy upload thuộc actor và đúng course. Thành viên thường không nhận ID upload của chủ khoá, hai course dùng chung build không dùng nhầm `job.upload_id`. Test PostgreSQL/HTTP riêng bảo vệ điểm này; không thay trạng thái/khóa W-25.

Hợp đồng thứ hai: `UploadView.confirmed_at` nullable phản ánh xác nhận của **chính lần tải**, độc lập trạng thái build dùng chung. Vì vậy course thứ hai vẫn sửa tên/xác nhận khi build chung đang chạy hoặc đã thành công; không tự POST thay người dùng, không gọi runner thêm. Hai thay đổi DTO không thêm bảng hoặc migration, được tách commit `4c13841` và `261523e`; OpenAPI đã xuất lại. Đây là phần bổ sung cần điều phối/nhóm lõi soát khi tích hợp, không sửa lén mốc W-25 gốc.

## Thiết kế

Áp dụng `design-taste-frontend` cho app screen và `frontend-ui-engineering`, giữ màu/font/token main, Artboard 24/28 cùng hình chờ chính thức. Không dùng preview W-24 có biến không tồn tại. Nhãn người học dùng “tài liệu” và “bài học”; tiến trình là bốn bước thật, không tạo phần trăm giả. Không hiển thị tiền, token hoặc dự toán. Motion theo token 120/200 ms, reduced-motion giữ ảnh tĩnh; focus và vùng bấm mobile theo spec.

## Kiểm và bằng chứng

Các kiểm Python dùng runner của worktree, PostgreSQL UUID riêng, model/runner/media/mailer giả. Không gửi thư thật, Cloudinary hoặc gọi mô hình. Chỉ copy fixture theo manifest/SHA-256, không link/live/learner CLI.

Đã chép và kiểm 3.144 tệp phát triển qua `copy_w06_fixtures.py`, hai manifest gốc W-06/doc-1-rebuild; không dùng bản v45/v57. Bằng chứng HTTP/ảnh/video sẽ ghi rõ real HTTP so với trạng thái mock nếu có.

### Các lượt kiểm local đã hoàn tất

| Phép kiểm | Kết quả | Bằng chứng |
|---|---|---|
| Python toàn repo trên nhánh phụ thuộc | 2.165 đạt, 1 Cloudinary live bỏ qua; native exit 0 | [log](w14-react-evidence/local-full-py1.log), [JUnit](w14-react-evidence/local-full-py1.xml) |
| React toàn bộ sau picker/heading fix | 103 đạt; native exit 0; lượt bàn giao sau sửa câu chữ lưu riêng bên dưới | [log](w14-react-evidence/final-local-react.log), [JUnit](w14-react-evidence/final-local-react.xml) |
| React bàn giao sau sửa câu hướng dẫn | 104 đạt, 0 lỗi; native exit 0 | [log](w14-react-evidence/handoff-react.log), [JUnit](w14-react-evidence/handoff-react.xml), [exit code](w14-react-evidence/handoff-react-exit.txt) |
| TypeScript + Vite | native exit 0; build sau sửa câu chữ cũng native exit0 | [log](w14-react-evidence/final-local-build.log), [build bàn giao](w14-react-evidence/handoff-build.log) |
| Phá guard UI tuần tự | 3/3 bị assertion bắt, mỗi bản sai native exit 1, 0 setup error; harness exit 0 | [ledger và hash phục hồi](w14-react-evidence/ui-mutations/results.json) |
| Hợp đồng PostgreSQL/HTTP bổ sung | RED thiếu `upload_id`/`confirmed_at`, GREEN 18 test gồm hồi quy W-25 | [rà hợp đồng](w14-react-evidence/backend-contract-review.md), [JUnit](w14-react-evidence/build-contract2.xml) |

Python chạy khi backend đã có hai trường bổ sung (`261523e`), sau đó chỉ sửa UI/harness/tài liệu. Bộ browser hoàn chỉnh kiểm mã sản phẩm `7078660` với harness `d162dbe`. Sau khi xem ảnh cancelled, sửa duy nhất câu hướng dẫn chung không còn gợi một nút retry không có (`953240b`), thêm regression thấy RED trước sửa và chạy lại toàn React/build; không đổi API, trạng thái, quyền hoặc layout. [RED câu chữ](w14-react-evidence/cancel-copy-red.xml), [React bàn giao](w14-react-evidence/handoff-react.xml). **Ảnh/video browser trước sửa câu chữ này; chưa chạy lại browser/full Python sau thay đổi đó.** Cổng cuối trên main đã soát vẫn phải chạy lại toàn bộ, không lấy các số local thay thế. Test xuất lại JSON W-06/W-14 được chép vào [archive đợt này](w14-react-evidence/regression-exports/) rồi phục hồi bản gốc; không sửa bằng chứng vé khác.

Các phép phá UI: tự POST xác nhận khi upload chưa được người dùng bấm, bỏ query `course_id` khi poll, và bỏ cập nhật card sau 3 giây. Nguồn được khôi phục đúng byte/SHA-256 trước khi build/browser. Giữ mọi assertion/skip/ngưỡng hiện có. Không chạy mutation cùng server hoặc cổng.

### Lệnh đã dùng

Từ gốc `tmp/w14-react`; lệnh Python luôn qua runner, mỗi lượt có basetemp mới. Redirect log bằng `cmd.exe`, lấy native exit code.

```bat
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py -o addopts= -q --basetemp=tmp/w14-react-local-py1 --junitxml=report/w14-react-evidence/local-full-py1.xml
npm.cmd --prefix src/web/frontend test -- --pool=threads --maxWorkers=1 --reporter=junit --outputFile=../../../report/w14-react-evidence/final-local-react.xml
npm.cmd --prefix src/web/frontend run build
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w14_react_mutations.py
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe -X utf8 scripts/w14_web_runtime.py
```

### Rà soát và giới hạn thị giác

[Rà soát tích hợp](w14-react-evidence/integration-review.md) phát hiện và đã xử lý upload đến muộn khi rời trang, action bị giữ bận khi đổi route, huỷ đang chờ bị bấm lặp, và learner bị dẫn vào build API chỉ dành cho chủ upload. Không mở rộng quyền API để né lỗi route. Thẻ learner vẫn dùng trang course đã kiểm membership, có cập nhật trạng thái.

[Nhận xét hai vòng](w14-react-evidence/visual-critique.md) ghi ảnh đã xem và giới hạn thiết kế. Taste snapshot sau sửa heading: **0 FAIL, 1 WARN** `hero-void` ở1280; đây là snapshot DOM thật phục vụ kiểm thiết kế, không thay HTTP/browser interaction. Giữ một cột tác vụ hữu hạn, không thêm số liệu/trang trí giả để lấp khoảng trống. Điểm tự đánh giá7,1/10, không nhận chất lượng gallery7,5+.

### Browser thật và JSON

Harness tạo DB UUID riêng trên `db-test`, upgrade tới `w14_0006`, dựng FastAPI thật và dùng cookie/CSRF thật. `BuildService`/`BuildWorker`/`PostgresPhaseBStore` thật được nối với MemoryMediaStore, FakeMailer và ManifestFakeBuildRunner cùng kết quả lỗi scripted. Không mock/intercept API để thay trạng thái giao diện. Các control chỉ tồn tại trong script harness, bind loopback và được chặn bằng token ngẫu nhiên trong bộ nhớ; không nằm trong app sản phẩm.

- Chọn PDF/DOCX, tick quyền; trước bấm xác nhận không có worker call. Sửa tên trước POST, reload đọc lại tên/course đúng từ PostgreSQL.
- Poll giữ `build_id` và `course_id`; cancel/retry gửi `course_id`. Kiểm reading/running qua reload và chuyển ảnh chờ sang tĩnh khi reduced-motion.
- Thành công → course ready; tải lại đúng byte tạo course khác, tên khác, dùng chung build; không gọi worker lần nữa khi xác nhận course thứ hai.
- Huỷ khi reading, lỗi có thể thử lại → queued → succeeded, bản quét → rejected và không có nút retry. Không hứa hoàn lượt khi huỷ/từ chối.
- Màn upload, confirmation, running, success, cancelled, retryable và rejected có ảnh390/768/1280 sáng/tối. Lượt cuối chờ CSS transitions kết thúc trước khi chụp; không sửa màu bằng cách hậu kỳ ảnh.
- Lượt cuối trên `d162dbe`: native exit **0**, **13 nhóm assertion, 47 ảnh, 173 phản hồi API/154 payload JSON**, 5 course qua4 build. **0 lỗi console không dự kiến, 0 page error, 0 failed request/font failure, Axe0 violation/0 incomplete**. Có3 console dự kiến được đối chiếu: bootstrap `/me`401 và2 probe CSP của Axe; không gọi chúng là lỗi sản phẩm. [Log cuối](w14-react-evidence/browser-final.log).
- Kết quả SQL độc lập xác nhận5 course đúng chủ, hai tên riêng cùng build, trạng thái cuối có succeeded/cancelled/rejected và5 dòng usage giả tổng0,002USD. Đây là số tổng hợp kiểm sổ; chi dịch vụ ngoài vẫn0USD.
- Runtime ghi `temporaryDatabaseRemoved=true`; kiểm đọc lại PostgreSQL không còn DB prefix của harness tại [cleanup-check.json](w14-react-evidence/cleanup-check.json). Server8014 và browser/worker của harness đã dừng. Giữ nguyên worktree, snapshot, ZIP; không tắt dịch vụ DB chung của nhóm khác.
- [JSON phản hồi HTTP](w14-react-evidence/http-responses.json), [audit browser](w14-react-evidence/browser-audit.json), [kết quả đối chiếu SQL độc lập và cleanup](w14-react-evidence/runtime.json), [video](w14-react-evidence/w14-upload-build.webm). Các JSON này là dữ liệu từ FastAPI/PostgreSQL thật trong môi trường giả provider, không phải ví dụ thiết kế. Truy vấn SQL/assertion cụ thể ở `scripts/w14_web_runtime.py::_database_evidence`; runtime.json lưu kết quả kiểm, không tự nhận là dump đủ mọi hàng DB.

[Lịch sử lượt kiểm](w14-react-evidence/browser-run-history.md) phân biệt lỗi môi trường/harness với lỗi sản phẩm. Giữ log cũ, không đổi assertion để làm xanh; thí dụ lỗi đầu do tràn native file input, lỗi typography trên mobile, lỗi locator trùng, timeout chép manifest và tên mã chặn CSP khác giữa Chromium. Các lần RED/stub/collection không thay bằng chứng phá guard nghiệp vụ.

## Điểm lưu mã

| Phần | Commit |
|---|---|
| Gốc backend chưa nghiệm thu | `0a2afa8` (W-25, nhận W-14 `5b24ece`) |
| Upload ID đúng actor/course | `4c13841` |
| Xác nhận độc lập mỗi lần tải | `261523e` |
| React/card/route/error/quota | `316bccf` |
| Picker tiếng Việt/kéo thả | `7d8462e` |
| Heading ngắn, giữ tên đầy đủ | `7078660` — mã sản phẩm đã chạy browser đầy đủ |
| Browser/harness/phép phá guard và ảnh màu ổn định | `d162dbe` — mốc chạy browser cuối |
| Câu hướng dẫn trạng thái dừng, regression RED/GREEN | `953240b` — chỉ đổi câu chữ sau browser, kiểm React/build riêng |

README cập nhật cách mở PostgreSQL/backend/frontend/worker giả, URL, môi trường và cách dừng. **Chi phí dịch vụ ngoài mới:0 USD**. Số usage khác0 trong SQL là số giả nhằm kiểm ghi sổ, không phải chi nhà cung cấp.

## Phụ thuộc còn chờ

- Điều phối soát và ghép backend W-14/W-25, bàn giao main; sau đó nhận main và chạy cổng cuối đúng commit.
- Không tự đóng vé hoặc ghép/push main. Đây là bàn giao local, chưa có kết luận nghiệm thu cuối trên main đã nhận backend được duyệt.

## Điểm dừng theo yêu cầu chủ dự án

**Đã hoàn tất phần React và kiểm tích hợp local bằng bộ dựng giả, lưu mã/bằng chứng rồi dừng.** Chủ dự án sẽ gửi main có backend W-14/W-25 đã được điều phối soát. Khi được nhắn tiếp: nhận main bằng merge trong worktree W-14, soát lại hai trường DTO/composition nếu có xung đột, chạy cổng toàn repo/PostgreSQL/React/build/browser trên đúng đỉnh tích hợp; lúc đó mới bàn giao để điều phối quyết định nghiệm thu W-14. W-11 vẫn giữ nguyên `a53f0d3`, nối migration sau W-14 theo tuyến đã chốt, chưa nghiệm thu trong đợt này.
