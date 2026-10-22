# Điều phối — nghiệm thu W-07, soát backend W-14 và W-24; kế hoạch tiếp — 2026-10-21

## 1. Phán xét

Chỉ **W-07 đạt nghiệm thu** trong đợt này. Backend W-14 chưa đạt do hai race huỷ đã tái hiện; React W-14 chưa bàn giao. W-24 chưa đạt do lỗi runtime mới và bằng chứng Figma/guard chưa đủ. Không ghép W-14 hoặc bản thiết kế `c1df32a` vào main.

| Phần | Mốc bàn giao | Phán xét |
|---|---|---|
| W-07 web | `cd1ecb83f5f261af6e8911cf415f366c7b786752`; mã cuối `8f7fd4e` | **Đạt** tại mốc nhận main mới `2a14723611a6de9a4fd1bd18d1e2504231462861`; đã ghép `f20d198` và đẩy GitHub |
| Backend/worker W-14 | `5b24ece9b76edb8d5686fd33114ebdb442bbe336`; mã/test cuối `21a5835` | **Chưa đạt → W-25**; 35 test cũ xanh nhưng hai ca mới đỏ; React còn chờ |
| W-24 thiết kế | `c1df32a80f37a3e3788562f44ad6ddcf5daa48c9` | **Chưa đạt**, tiếp cùng W-24; không dùng phần mới làm chuẩn đã nghiệm thu cho React |

**Ghép W-07:** `f20d19802ed1afbd56ff478c3038e9b9dd80ce5a`, đã đẩy GitHub; chi tiết ở mục 6. **Chi mới: 0 USD**, không lời gọi mô hình, SMTP hoặc Cloudinary thật.

## 2. Cách kiểm và phạm vi bằng chứng

- Thư mục chung ở main `2f4998c`, không đổi nhánh của nhân viên. Soát mã độc lập theo correctness/architecture/security/readability/performance; reviewer W-07 approve phần mã, reviewer W-14/W-24 chỉ rõ Required. Các lượt chạy độc lập của điều phối được lưu riêng, không lấy số báo cáo nhân viên làm kết quả chạy lại.
- Tạo `tmp/coord-w07-w14-acceptance` từ main; nhận W-07 và W-14 để kiểm khả năng tích hợp. Chỉ OpenAPI xung đột, đã sinh lại từ app gồm cả hai API. Commit tích hợp thử **`85ecce04bcacf92852b78d3fb533e1d6b98dfdb6`**; không sửa implementation W-14. Hai ca tái hiện mới là tệp riêng, không đưa vào cổng main.
- Do W-14 chưa đạt, tách `tmp/coord-w07-final` từ main, chỉ nhận W-07. Mốc **`2a14723611a6de9a4fd1bd18d1e2504231462861`** chứa main mới và đúng mã W-07 đã soát; mọi cổng chốt chạy tại mốc này. Bản thiết kế mới không nhập vào worktree này.
- Mỗi worktree kiểm được chép **3.144 tệp** theo hai manifest W-06; nguồn/đích khớp SHA-256. Bỏ một learner store CLI khỏi gói 3.145 tệp; không junction/symlink/hardlink, không mở live/tập giữ lại, không dọn snapshot/worktree/t01a. [Đối chiếu W-07](coord-w07-w14-w24-evidence-2026-10-21/w07-fixture-copy.json), [W-14](coord-w07-w14-w24-evidence-2026-10-21/w14-fixture-copy.json).
- PostgreSQL dùng DB tạm riêng; providers/ADC/Mailer/MediaStore được thay/chặn theo harness. Trình duyệt W-07 chạy HTTP thật + Argon2 + PostgreSQL thật; không có Chrome DevTools MCP/Figma callable trong phiên nên dùng Chromium qua Playwright. Kiểm thiết kế là local Chromium, không coi là đọc/bấm Figma Cloud.
- Bộ [bằng chứng độc lập](coord-w07-w14-w24-evidence-2026-10-21/manifest.json) có SHA-256 và [tóm tắt máy đọc](coord-w07-w14-w24-evidence-2026-10-21/summary.json), native exit/commit/lệnh của từng lượt. Bằng chứng nhân viên vẫn ở nhánh cũ; các worktree được giữ nguyên.
- Gói có **107 tệp bằng chứng** ngoài manifest, khoảng 13,3 MB; `.gitattributes` trong gói giữ nguyên byte khi checkout để SHA-256 không đổi theo LF/CRLF. Chuẩn hóa UTF-8/LF và khoảng trắng cuối dòng của 29 log/XML, chỉ đổi CRLF sang LF ở 22 JSON/script/văn bản khác. Hash bản trước chuẩn hóa của 51 tệp giữ trong [normalization.json](coord-w07-w14-w24-evidence-2026-10-21/normalization.json); các đầu ra chạy thô vẫn ở scratch của điều phối. Đếm testcase/failure/error/skip của XML và giá trị JSON trước/sau bằng nhau; native exit riêng không đổi. Không có chuỗi token cần che trong lượt điều phối này.

## 3. W-07 — đạt

### Cổng chốt độc lập

| Kiểm | Kết quả | Bằng chứng |
|---|---|---|
| Python toàn repo, PostgreSQL bắt buộc | **2.114 đạt, 0 fail/error, 1 skip**, native exit 0; pytest 494,21 giây, wrapper 506,69 giây | [JUnit](coord-w07-w14-w24-evidence-2026-10-21/runs/w07-full-gate.xml), [log](coord-w07-w14-w24-evidence-2026-10-21/runs/w07-full-gate.log), [mốc/lệnh/exit](coord-w07-w14-w24-evidence-2026-10-21/runs/w07-full-gate-exit.json) |
| React | **85 đạt**, không skip/fail/error, exit 0 | [JUnit](coord-w07-w14-w24-evidence-2026-10-21/runs/w07-react.xml), [exit](coord-w07-w14-w24-evidence-2026-10-21/runs/w07-react-exit.json) |
| TypeScript/Vite build | Exit 0 | [log](coord-w07-w14-w24-evidence-2026-10-21/runs/w07-build.log), [exit](coord-w07-w14-w24-evidence-2026-10-21/runs/w07-build-exit.json) |
| Phá guard backend | **8/8 bị assertion bắt**, native 1 từng bản sai, không setup error; phục hồi đúng byte | [ledger](coord-w07-w14-w24-evidence-2026-10-21/runs/w07-mutations/mutations.json) |
| Phá guard UI | **2/2 bị assertion bắt**, nguồn phục hồi | [ledger](coord-w07-w14-w24-evidence-2026-10-21/runs/w07-ui-mutations/ui-mutations.json) |
| Chromium + HTTP + PG | **11 kiểm tra luồng**, 6 cấu hình thật, exit 0 | [audit](coord-w07-w14-w24-evidence-2026-10-21/w07-browser/browser-audit.json), [runtime/SQL](coord-w07-w14-w24-evidence-2026-10-21/w07-browser/runtime.json), [exit](coord-w07-w14-w24-evidence-2026-10-21/runs/w07-browser-exit.json) |

Skip duy nhất là Cloudinary live không bật; không bỏ PostgreSQL. Alembic vẫn **một head `w06_0005`**, không thêm migration rỗng.

### Điều đã chứng minh

- Gateway kiểm membership mỗi lần; actor từ phiên, doc/version từ course đã phát hành. Chỉ node learnable của đúng graph được ghi; strict boolean và cấm trường owner/doc/version do client giả. Inventory tự liệt kê route vẫn bắt route mới thiếu guard.
- `test_progress_is_isolated_between_members_using_independent_postgres_runtimes` dùng hai engine/store/runtime, đọc SQL độc lập. `test_unmark_then_correct_quiz_keeps_learner_choice_through_gateway` giữ learner override; hai test race ép cả hai thứ tự quiz/learner bằng Event và quan sát PostgreSQL lock. Mutation bỏ atomic đỏ ở assertion trạng thái cuối, không chỉ vì thiếu khóa.
- UI optimistic theo node, rollback riêng node lỗi; snapshot cũ không ghi đè node khác. Test có hai response đảo thứ tự, 200 thiếu node, 401 và đổi course/abort. Mutation bỏ rollback và merge cả snapshot đều đỏ.
- Browser đăng ký hai người và tham gia mẫu doc-1 **v8**: mở/gập, click/Space đánh dấu, bỏ dấu, reload và mở module. SQL độc lập thấy A có đúng hai bản ghi (một learned, một not_learned), B có **0**; lần PUT bị chèn lỗi không để lại bản ghi. Doc-1 dùng 35 module/223 bài học từ snapshot, không dựng lại graph.
- Lỗi rollback là **một PUT 500 được Playwright chèn**; các PUT thành công/GET/SQL là thật. Có 12 ảnh mock empty/loading/error ghi `acceptance:false`, tách khỏi sáu ảnh HTTP thật. Không biến lỗi giả thành bằng chứng server từng tự lỗi.
- Sáu cấu hình 390/768/1280 sáng/tối: axe **0 violation/0 incomplete**, không tràn ngang, vùng bấm/keyboard/focus/font và reduced-motion đạt. Giữ **19 console error thô**: 2 bootstrap 401, 1 PUT500 chèn, 4 GET500 chụp trạng thái mock, 12 CSP probe của axe; đối chiếu hẹp đủ 19, không lỗi ngoài dự kiến, không nới CSP.
- Đã xem ảnh thật: chữ/nhịp hàng/phân cấp rõ, token và logo nhất quán, giao diện điện thoại đọc/thao tác được. Taste inspector có **0 FAIL/1 WARN `unused-canvas`** ở desktop; chấp nhận vì cột dự trữ chat/thư viện theo spec còn ngắn, không thêm dữ liệu/action giả để lấp. Inspector dùng snapshot DOM/CSS cho thiết kế; kiểm chức năng/axe chạy trên app HTTP thật.

Ảnh trực tiếp: [1280 sáng](coord-w07-w14-w24-evidence-2026-10-21/w07-browser/roadmap-1280-light.png), [1280 tối](coord-w07-w14-w24-evidence-2026-10-21/w07-browser/roadmap-1280-dark.png), [390 sáng](coord-w07-w14-w24-evidence-2026-10-21/w07-browser/roadmap-390-light.png), [390 tối](coord-w07-w14-w24-evidence-2026-10-21/w07-browser/roadmap-390-dark.png), [768 sáng](coord-w07-w14-w24-evidence-2026-10-21/w07-browser/roadmap-768-light.png), [768 tối](coord-w07-w14-w24-evidence-2026-10-21/w07-browser/roadmap-768-dark.png), [video](coord-w07-w14-w24-evidence-2026-10-21/w07-browser/w07-roadmap-progress.webm). JSON [roadmap](coord-w07-w14-w24-evidence-2026-10-21/w07-browser/roadmap-doc-1.json), [progress sau lưu/rollback](coord-w07-w14-w24-evidence-2026-10-21/w07-browser/progress-after-rollback.json) và [người B](coord-w07-w14-w24-evidence-2026-10-21/w07-browser/progress-learner-b.json).

Phạm vi đạt là W-07, không phải toàn SA-34/Pha B2, chất lượng lại toàn tên module Pha A hoặc các trang bài giảng/chat/quiz chưa làm.

## 4. W-14 — chưa đạt mốc backend, mở W-25

Bộ test W-14 nguyên bản chạy lại trên tích hợp thử: **35 đạt, 0 skip/fail/error**, exit 0; [JUnit](coord-w07-w14-w24-evidence-2026-10-21/runs/w14-baseline.xml). Điều đó chưa đủ vì có hai cửa sổ race chưa được kiểm.

| Required | Cách tái hiện | Quan sát DB/hệ quả |
|---|---|---|
| Confirm ghi đè cancel | Dừng confirm sau khi đọc awaiting_confirmation; cancel ở engine độc lập commit; tiếp tục confirm | `queued`, `cancel_requested=true`, `counts_quota=true`, course `failed`; việc bị treo |
| Cancel khi publication vẫn báo success | Giữ graph_loader trong callback thành công; cancel ở engine độc lập commit; tiếp tục publication | Build `succeeded` dù cờ huỷ true, course `ready`, có thư “Bản dựng xong” |

Vị trí gốc: `application/builds.py` trong `confirm_build` đọc job không khóa hàng rồi UPDATE queued vô điều kiện; `application/build_worker.py` kiểm huỷ trước publication, còn `infrastructure/build_store.py::record_usage` không xét lại cờ sau khi khóa terminal transaction.

[Hai ca mới](coord-w07-w14-w24-evidence-2026-10-21/w14-cancellation-repros.py.txt) đều **đỏ đúng assertion**, 0 setup error, native 1: [JUnit](coord-w07-w14-w24-evidence-2026-10-21/runs/w14-repro2.xml), [log](coord-w07-w14-w24-evidence-2026-10-21/runs/w14-repro2.log), [mốc/lệnh](coord-w07-w14-w24-evidence-2026-10-21/runs/w14-repro2-exit.json). Lượt đầu thiếu thư mục cha basetemp nên có 2 setup error; giữ [log lượt đầu](coord-w07-w14-w24-evidence-2026-10-21/runs/w14-repro.log), **không tính là RED nghiệp vụ**. Tạo cha tmp rồi chạy lại với basetemp mới như trên.

Đã tạo [W-25](../task/web/W-25-dong-bo-xac-nhan-huy-va-ket-thuc-ban-dung.md) gom đúng vùng trạng thái/worker. Cần tuần tự hóa confirm/cancel và xét huỷ dưới khóa khi kết thúc; giữ usage giả khác 0, receipt/fence lease, kiểm cả graph/media publication và không gửi thư thành công sau huỷ đã được nhận trước terminal commit. Không sửa mã sản phẩm của nhân viên trong đợt soát.

Các điểm phối hợp đã đọc: API upload/confirm/poll/cancel/retry/usage, queue SKIP LOCKED, source riêng theo upload, FK build_id, callback usage/lease và MediaStore giả dùng chung giữa runtime. React phải giữ **build_id + course_id**, poll/cancel/retry có query course_id và dùng can_cancel/can_retry. Hợp đồng đã có title trước queued, báo cáo lõi ghi chủ dự án đã chốt trong phiên của họ; không ghi phán xét này là một lần duyệt UI mới.

Vé cũ ghi PDF400 trang nhưng spec chức năng/WebSettings mặc định không giới hạn, chỉ kiểm `build_max_pages` khi bật. Chuẩn hóa lại câu vé theo nguồn chân lý, không đổi mặc định sản phẩm. Sổ chi từng bước thật còn phụ thuộc callback usage checkpoint của W-13 khi nối W-15; tổng chưa phân bổ ghi step=null/attribution_complete=false, không tự chia tiền đều. Các số .003/.12 trong test là usage giả, **không phải tiền nhà cung cấp đã chi**.

## 5. W-24 — chưa đạt, tiếp cùng vé

Reviewer kiểm local Chromium **12 cấu hình** (W-07/W-14 × 390/768/1280 × sáng/tối), đọc plugin/token/guard/bảng bàn giao và chạy phản ví dụ trong bản chép scratch; không sửa nhánh nhân viên. [Review đầy đủ](coord-w07-w14-w24-evidence-2026-10-21/w24/review.md).

1. **Sai tên token runtime:** hai preview mới dùng `--color-text-main`/`--color-brand-blue` không có trong CSS. Cả **6 cấu hình tối có chữ đen** trên nền tối; progress W-07 trong suốt. Đã xem [ảnh 390 tối](coord-w07-w14-w24-evidence-2026-10-21/w24/w07-preview-dark-390.png), [W-14 1280 tối](coord-w07-w14-w24-evidence-2026-10-21/w24/w14-preview-dark-1280.png); ảnh chờ ổn định 500 ms, không phải màu đang transition.
2. **Raw Variables chưa có provenance Cloud và chưa khớp CSS:** đối chiếu 35 biến/light có **7 điểm lệch/thiếu** (tên brand/text/motion, radius-md8 so CSS10, lg12 so14, radius-full/surface-2); plugin thực chỉ tạo 16 màu +10 spacing. Guard mới vẫn xanh khi đổi raw primary sang `#FF0000`. [Đối chiếu và phản ví dụ](coord-w07-w14-w24-evidence-2026-10-21/w24/token-css-observations.json). Đây là phạm vi light đã đo, chưa gọi là đối chiếu đủ mọi token/mode.
3. **Guard clipboard/scroll chưa đo hành vi:** script đọc `data-copied-text` do handler gán; `isVisible` không yêu cầu nằm trong viewport. Bỏ lời gọi thật `navigator.clipboard.writeText` hoặc `scrollIntoView`, verifier vẫn **4/4, native exit 0**; citation đặt top5000 vẫn isVisible=true. [Ledger/phản ví dụ](coord-w07-w14-w24-evidence-2026-10-21/w24/mutation-results.json), [quan sát browser](coord-w07-w14-w24-evidence-2026-10-21/w24/browser-observations.json).
4. **So khung ảnh hỏng:** prototype trỏ hai ảnh GIF/static không tồn tại, naturalWidth **0** trước/sau reduce nhưng audit vẫn xanh. [Ảnh](coord-w07-w14-w24-evidence-2026-10-21/w24/prototype-flow3-broken-image.png), [số đo](coord-w07-w14-w24-evidence-2026-10-21/w24/screenshot-observations.json). Vòng chờ thật trong preview W-14 có ảnh tải được nhưng CSS chỉ32px, khác spec/báo cáo96px.
5. **Thiếu checklist/trạng thái và bằng chứng Cloud:** bảng14 nhóm không thay checklist từng trang/trạng thái của spec11; components không thay màn quản trị/thành viên/404. Bộ ảnh không chứng minh ma trận sáng/tối/cỡ đúng từng trang (auth mobile capture500, mobile board viewport900), không có video bấm bốn prototype Figma hoặc Variables receipt thật. Không có callable Figma trong phiên này nên chưa xác minh node/Variables/bấm Cloud; không kết luận những node tự khai báo là bằng chứng đã kiểm.
6. **Tiến độ mẫu không cộng khớp:** đầu W-07 ghi12/18=67%, tổng module hiển thị5/5+3/8+0/5=8/18; mark/rollback không cập nhật tổng/bar. Sửa bằng một nguồn dữ liệu mẫu, không đổi báo cáo để bỏ qua mâu thuẫn.

Vẫn giữ phần local W-24 đã nghiệm thu và ghép ở các đợt W-03/W-06; không mở lại lỗi đã đóng trên main. Các lỗi trên thuộc bản bàn giao mới hoặc những tiêu chí Cloud/guard vốn còn thiếu. Không cần thiết kế lại thương hiệu; React dùng token chuẩn đang có trên main và spec, không chép các tên biến/số liệu sai của preview mới.

## 6. Ghép, kế hoạch và điều kiện chuyển bước

**Trạng thái ghép:** W-07 đã ghép bằng **`f20d19802ed1afbd56ff478c3038e9b9dd80ce5a`**, `--no-ff`, cha main `2f4998c` và đúng mốc soát `2a14723`; push thành công `2f4998c..f20d198 main -> main`. Đối chiếu `src/`, `tests/`, `scripts/`, `design/` ở commit ghép với mốc qua cổng không có diff. W-14/W-24 mới giữ ngoài main; head vẫn `w06_0005`. Bộ bằng chứng, vé và nhật ký cập nhật sau ghép chỉ là tài liệu, không đổi mã đã qua cổng.

| Nhóm | Việc tiếp theo | Điểm kiểm trước khi chuyển bước |
|---|---|---|
| Lõi | **W-25** sửa hai race trên nền W-14 | RED/GREEN cả hai thứ tự transaction, graph/media publication, SQL độc lập, usage/lease/quota/mail; cổng toàn repo có main mới. Đạt mới ghép mốc backend/schema W-14 |
| Web | **React/tích hợp W-14** theo hợp đồng; giữ phần W-11 đã làm ở nhánh riêng | Có thể chuẩn bị UI trên nhánh phụ thuộc được ghi rõ; nhận backend đã sửa/soát đạt trước cổng cuối. Upload→tên/xác nhận→poll→huỷ/thử lại/kết thúc, browser PG + bộ dựng giả, ảnh/video. Chưa đóng toàn W-14 khi chỉ backend/UI riêng lẻ |
| Thiết kế | **Tiếp W-24**, sửa sáu nhóm trên, ưu tiên hợp đồng W-14 | Token đúng/đẹp sáng tối, guard bắt hành vi bị phá, ảnh thật decode, số tiến độ khớp; đủ từng trạng thái/node/export/video; Cloud thiếu thì báo thiếu |

**Tuyến giữ nguyên:** `w06_0005 → w14_0006 → w11_0007`. W-25 chỉ sửa hành vi, không tạo migration. W-14 đã sửa/soát đạt và ghép trước, W-11 mới nhận main đó để chốt migration/cổng. W-07 không thêm schema. Nhánh W-11 có công việc đang làm, giữ nguyên; đợt này **chưa nghiệm thu W-11**.

**Sau đó:** W-14 đầu-cuối đạt mới mở W-15 nối thật/đo tiền, cần dry-run và tin nhắn duyệt mới; không lấy duyệt phục hồi cũ. W-08 còn cần xác nhận đúng SA-39/40/41 và soát sửa B2 liên quan; W-09/W-10 theo phụ thuộc gốc. W-23 chờ W-22/W-24 và các màn học, W-21 sau cùng. Vertex giữ nguyên; toàn bộ đợt sửa/tích hợp trước W-15 dùng đồ giả0USD.

Đã soạn [lệnh giao việc cho ba nhóm](lenh-giao-viec-sau-w07-2026-10-21.md), chưa gửi phiên nhân viên. Không có câu hỏi cần chủ dự án quyết để lõi sửa race hoặc web chuẩn bị React; chưa phát sinh đề nghị chi tiền.

## 7. Lệnh và tái lập

Các lượt chạy có danh sách argv/cwd/commit/native exit trong `runs/*-exit.json`; wrapper chỉ thu log, không in `.env` hoặc credentials. Ví dụ chạy từ `tmp/coord-w07-final`:

```powershell
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe -X utf8 src/web/backend/tests/copy_w06_fixtures.py
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py -o addopts= -q --basetemp=tmp/coord-w07-full-20261021 --junitxml=C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-review-20261021/evidence/w07-full-gate.xml
npm.cmd --prefix src/web/frontend test -- --pool=threads --maxWorkers=1 --reporter=default --reporter=junit --outputFile=C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-review-20261021/evidence/w07-react.xml
npm.cmd --prefix src/web/frontend run build
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe -X utf8 scripts/w07_web_runtime.py
```

Nếu chạy lại, dùng basetemp mới và tạo thư mục cha tmp trước; cổng trên không cần chạy lại chỉ để đổi định dạng báo cáo. Mutation backend/UI chạy sequential trên mã cùng mốc, đầu ra được chuyển sang thư mục bằng chứng điều phối bằng override OUTPUT; ledger có lệnh từng test, nguồn được phục hồi trước full gate. Không chạy mutation cùng cổng/server trên cùng mã.

W-14 chạy bộ cũ và hai ca mới riêng trên worktree tích hợp thử, qua runner; không trộn hai fail đó vào con số **0 fail của W-07**. W-24 dùng `node scripts/verify_prototype_flows.cjs` ở bản chép scratch và hai script Chromium đã giao trong gói; raw logs giữ những lượt verifier xanh sai để chứng minh guard còn lọt. Collector/hash và wrapper được lưu dạng `.py.txt`; [manifest](coord-w07-w14-w24-evidence-2026-10-21/manifest.json) kiểm tính toàn vẹn của gói.
