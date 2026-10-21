# Điều phối — nghiệm thu W-06 và kế hoạch tiếp theo

**Ngày:** 2026-10-21 · **Người soát:** Codex · **Trạng thái:** **đạt nghiệm thu W-06**, đã ghép **`dc41ee8`** và đẩy GitHub; mốc soát/cổng cuối `8b6e500`.

## 1. Mốc bàn giao và phạm vi

Chủ dự án yêu cầu kiểm cả ba nhóm sau khi báo hoàn thành W-06. Main nền `29e4350dc04a818b9695987b0bd2d9e9ba33626b`; thư mục chung giữ main, các worktree nhân viên không bị sửa.

| Nhóm | Mốc nhận để soát | Phạm vi |
|---|---|---|
| Lõi | `bde3e0b`, gồm mã backend `c694149`, kiểm cuối `4f676d9`, hồ sơ `8380a1a` | Course/membership, migration, API, gateway, PostgreSQL, seed sáu cuốn |
| Web | `d9b5e1a20c99d63eb076750b707435bf1d03169c`, đã nhận backend `8380a1a` | React, auth redirect, route mở khoá/module, kiểm đầu-cuối và README |
| Thiết kế | `63dd8bd`, sau khi nhận main và giữ phần W-24 cũ | Preview W-06/W-04, plugin, báo cáo, bổ sung assertion local |

Điều phối tạo worktree mới `tmp/coord-w06-acceptance`, nhánh `work/coord-w06-acceptance` từ mốc web, nhận hồ sơ lõi và thiết kế thành `15adf1e`. Sau khi sửa các phát hiện bắt buộc về câu chữ/bằng chứng thiết kế, mốc chốt là **`8b6e500adfb12845a9186ff120912e1a5a34f0d2`**. Phần backend/React không bị điều phối sửa.

Nguồn: [vé W-06](../task/web/W-06-khoa-mau-khoa-hoc-cua-toi-gateway.md), [bàn giao lõi](w06-backend-gateway-2026-10-20.md), [xác nhận tiếp nhận của lõi](w06-loi-xac-nhan-web-tich-hop-2026-10-21.md), [bàn giao React](w06-react-tich-hop-2026-10-21.md), [thiết kế có đính chính](w24-bo-sung-w22-2026-10-20.md).

## 2. Soát độc lập và phát hiện

**Backend:** approve trong phạm vi W-06; chưa thấy lỗi Critical/Required. Quyền thành viên kiểm trước graph/cache; owner lấy từ actor; runtime tự compose các use case và spend guard với cùng `PostgresPhaseBStore`, không dựng runtime CLI JSON. Cả hai provider giữ Vertex. Join khoá hàng course trước đếm capacity; migration kiểm đúng một chủ, gồm cả OLD/NEW khi di chuyển membership owner.

**React:** approve sau khi đọc auth/route/API/state/CSS. Join gửi cookie/CSRF, không tạo membership giả khi lỗi, chặn yêu cầu trùng theo khoá, abort khi unmount; thành công chuyển focus sang “Học tiếp”. ID được encode trong route; module lấy từ resume API. Mô tả graph dạng chuỗi hoặc mảng object `text` được hiển thị đúng. Giữ cách gọi “tài liệu” và “bài học” theo chỉ thị chủ dự án đã ghi trong bàn giao web.

**Required thiết kế đã sửa tại `8b6e500`:**

1. Plugin ghi “Đã xác minh (24h)”, báo cáo cũng gán hạn 24 giờ cho trạng thái đã xác minh. Đã bỏ hạn trạng thái; 24 giờ chỉ áp dụng link xác minh, reset vẫn 60 phút.
2. Báo cáo ghi resend theo 60 giây; đã sửa về **3 lần mỗi giờ**.
3. Một đoạn chữ canvas vẫn báo “Đã gắn kết nối” vô điều kiện dù helper đã đếm thất bại; đổi thành hướng dẫn kiểm báo cáo reactions và nối tay các mục chưa thành công.
4. Báo cáo khẳng định đồng bộ Cloud hai chiều, clipboard/citation, `<details open>` và mutation vượt quá bằng chứng. Đã phân biệt thông tin Cloud do nhóm khai báo với kết quả kiểm độc lập, mô tả đúng assertion HTML và giữ W-24 mở.

Người soát độc lập xác nhận lại approve phần local và frontend tại `8b6e500`. **Không đóng toàn bộ W-22/W-24:** chưa có raw Variables export có nguồn gốc và bộ node/ảnh/video/bấm trực tiếp Figma đầy đủ. Audit 4/4 chỉ là HTML local, không thay kiểm prototype trong Figma. Phiên này không có Figma/Chrome DevTools MCP khả dụng; kiểm UI bằng Chromium thật qua Playwright đã có, không ghi đã dùng MCP.

**Optional, không chặn W-06:** CLI seed hai tiến trình đồng thời trên DB trống có thể tạo hai mẫu cùng doc_id; idempotency hiện được chứng minh cho chạy tuần tự. Chạy một phiên seed tại một thời điểm. `next=/dang-nhap` hoặc `/dang-ky` vẫn là đích nội bộ được chấp nhận; chưa thấy open redirect ra ngoài, có thể siết khi sửa auth sau này. Không mở rộng thay đổi trong lượt nghiệm thu này.

## 3. Kiểm thử do điều phối thực hiện

| Kiểm | Kết quả | Bằng chứng độc lập |
|---|---|---|
| Dữ liệu trong worktree mới | **3.144 tệp khớp SHA-256**, bỏ kho CLI doc-1; không liên kết | `coord-w06-evidence-2026-10-21/fixture-copy.json` |
| Cổng Python tại `8b6e500`, PostgreSQL bắt buộc | **2.107 đạt, 0 fail, 1 Cloudinary live không bật, exit 0; 470,22 giây** | `coord-w06-evidence-2026-10-21/final-python.*` |
| React tại `8b6e500` | **77 đạt**, exit 0 | `coord-w06-evidence-2026-10-21/final-react.log` |
| TypeScript/Vite build tại `8b6e500` | **đạt**, exit 0 | `coord-w06-evidence-2026-10-21/final-build.log` |
| Browser, HTTP/PostgreSQL/Argon2 thật | **9 assertion**, 6 màn sáng/tối ở 390/768/1280; 0 page error/tràn ngang/vi phạm axe, 0 axe incomplete | [audit](coord-w06-evidence-2026-10-21/browser-audit.json), [SQL/runtime](coord-w06-evidence-2026-10-21/runtime.json) |
| Phá guard backend rồi phục hồi mã | **8/8 bị assertion bắt**, không setup error | [mutations.json](coord-w06-evidence-2026-10-21/mutations.json), log/XML RED cùng thư mục |
| Prototype HTML local | **4/4 đạt** trong phạm vi assertion hiện có | `coord-w06-evidence-2026-10-21/prototype.log` |
| Preview thiết kế W-06/W-04 | **12 cấu hình**; 0 tràn ngang, 0 control dưới 44×44, 0 JS; sau chờ 350 ms không còn animation chạy với reduce | `coord-w06-evidence-2026-10-21/design-audit.json`, ảnh design cùng thư mục |
| Taste inspector app | exit 0, **0 FAIL/1 WARN below-fold** | `coord-w06-evidence-2026-10-21/taste-inspector.log` |

Tám phép phá gồm route mới không guard, gateway bỏ kiểm thành viên, owner giả, spend guard trỏ memory, session trỏ memory, transport đổi Developer API, bỏ kiểm dangling reparse, và seed prod với đầu vào hợp lệ. Chạy tuần tự trước cổng; `finally` phục hồi nguồn và Git đối chiếu backend không có diff sau lượt phá. Cổng cuối chạy trên đúng mã đã phục hồi.

JUnit cuối có **20 test W-06, 23 test token và 8 test SA-47**, đều đạt. Assertion tiêu biểu trong `src/web/backend/tests/test_courses_w06.py`:

| Điều cần bảo vệ | Test chạy được |
|---|---|
| Mọi route riêng tư, kể cả thêm route mới | `test_every_cid_route_hides_private_course_from_outsiders_including_admin`, `test_route_inventory_catches_a_new_unguarded_route` |
| Actor/store/Vertex đúng và quan sát PostgreSQL độc lập | `test_gateway_ignores_claimed_owner_and_records_actor_in_independent_postgres_connection`, `test_composition_binds_vertex_models_and_all_child_stores_to_postgres` |
| Join lặp, capacity tranh chỗ, owner/rollback | `test_logged_in_unverified_user_can_join_dev_sample_and_repeat_without_duplicates`, `test_join_concurrency_respects_course_capacity`, `test_owner_constraint_and_course_creation_rollback` |
| Seed allowlist/dev/prod, đủ sáu graph thật | `test_seed_only_allows_six_development_documents_in_dev_and_uploads_once`, `test_real_six_book_seed_join_and_roadmap_over_tcp_http` |
| Cache vẫn kiểm quyền, graph ghim, resume riêng | `test_cached_graph_never_bypasses_revoked_membership`, `test_graph_is_pinned_to_course_version_and_cached_by_doc_version`, `test_course_progress_and_resume_are_per_actor_and_resume_resolves_module_scope` |

Browser tạo DB UUID riêng, migrate lên **một head `w06_0005`**, seed sáu graph/PDF thật qua MemoryMediaStore, đăng ký UI và xác nhận bằng SQL độc lập:

- Sáu membership owner mẫu, hai membership learner/via=sample cho đúng actor (doc-1/doc-6); gọi join lặp vẫn một membership/người/khoá.
- Tải lại trang giữ quyền; “Học tiếp” mở đúng course/module theo JSON thật, doc-1 v8.
- Người ngoài khoá riêng tư bị 404 cho detail, roadmap và join, kể cả request gửi owner/doc/version giả.
- UI W-06 chưa ghi tiến độ: 0 `phase_b_record` trong runtime browser là đúng phạm vi list/join/detail. Test backend kiểm ghi session/progress/reservation/usage qua kết nối PostgreSQL độc lập; không lấy property kiểu store làm đủ bằng chứng.
- Test DB đã tự xoá đúng UUID sau khi đóng kết nối. Không seed vào DB phát triển của chủ dự án.

Giữ **17 console error thô**, đối chiếu hẹp: 1 bootstrap 401, 4 phản hồi 500 cố ý để chụp mock error, 12 thông báo CSP do probe axe. 0 lỗi ngoài dự kiến, 0 page error/request failure ngoài probe, không nới CSP. Sáu ảnh UI chính là dữ liệu thật; 12 ảnh empty/loading/error dùng phản hồi chặn được gắn `acceptance:false`, chỉ chứng minh thị giác.

Đã xem ảnh desktop sáng/mobile tối: bố cục thẻ 3/2/1 cột rõ, logo/font đúng, nhãn thao tác và trạng thái phù hợp. Cảnh báo below-fold chấp nhận vì danh sách có nhiều nhóm và thẻ; thứ tự ưu tiên nhóm đang học được giữ. Preview thiết kế là bảng trạng thái tĩnh, không phải ứng dụng nghiệp vụ hoặc nghiệm thu Figma.

**Chi mới: 0 USD; lời gọi mô hình: 0.** Provider/ADC/SMTP/Cloudinary được chặn trong harness, Mailer và MediaStore giả. Browser có tải font ở các origin Google Fonts đã cho phép; không gọi nhà cung cấp AI. Không chạm tập giữ lại, kho Pha B live chung, snapshot/ZIP hoặc t01a; không dọn worktree.

### Lệnh tái lập

Từ `tmp/coord-w06-acceptance`:

```text
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe -X utf8 src/web/backend/tests/copy_w06_fixtures.py
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe -X utf8 src/web/backend/tests/w06_mutations.py
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py -o addopts= -q --basetemp=tmp/coord-w06-final --junitxml=tmp/coord-w06-final.xml
npm.cmd --prefix src/web/frontend test -- --pool=threads --maxWorkers=1
npm.cmd --prefix src/web/frontend run build
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe -X utf8 scripts/w06_web_runtime.py
node scripts/verify_prototype_flows.cjs
node tmp/coord_design_check.cjs
```

Không chạy mutation cùng cổng hoặc server dùng mã đó. Dùng basetemp mới cho lần chạy lại. Các lệnh được bọc `subprocess.run`, giữ native exit code; không lấy warning PowerShell thành kết quả pytest. Lượt React/build ban đầu `15adf1e` được giữ riêng; đã chạy lại ở đúng `8b6e500`. Preview đo ngay sau đổi theme có transition ngắn đang chạy; chờ ổn định 350 ms rồi kiểm lại cho kết quả nêu trên, không báo nhầm là shimmer không tắt.

## 4. Schema và phần bàn giao cho vé sau

Head hiện kiểm là `w01_0001 → w05_0002 → w02_0003 → w03_0004 → w06_0005`. W-06 chỉ thêm một migration course/membership; giữ kiểm upgrade từ schema trước, owner rollback/unique và capacity tranh chỗ.

- `course.module_count`: metadata lấy từ graph khi tạo, phải giữ khớp `published_graph_version` khi phát hành phiên bản mới; không tin giá trị người dùng gửi.
- `source_public_id`: metadata PDF mẫu phía server, không lộ URL/Cloudinary ID lâu dài qua card API. W-08 dùng đường media có kiểm thành viên; W-14 nối nguồn tài liệu tải lên khi có upload/build.
- `build_id`: UUID nullable ở W-06, bảng build chưa tồn tại nên chưa có FK. W-14 phải thêm FK khi tạo bảng build và kiểm nguồn upload/PDF; không sửa migration W-06 đã ghép hoặc âm thầm bỏ ràng buộc của spec.
- Graph trong bản sao: doc-1 v8, nhap-mon-ml v50, naive-bayes v49, doc-6 v29, xstk-ch3-1 v68, doc-4 v27. Không dựng lại để lấy v45/v57; không đưa cache CLI vào PostgreSQL của web.

## 5. Kế hoạch tiếp theo

Mục tiêu gần nhất: **học được một tài liệu mẫu qua lộ trình và tiến độ thật**, sau đó mở chia sẻ/tải tài liệu. W-06 mới là danh sách/quyền/gateway; trang module hiện là bản tóm tắt để kiểm resume, chưa phải bài giảng/chat/quiz hoàn chỉnh.

| Nhóm | Ưu tiên sau W-06 | Bàn giao và điều kiện đạt |
|---|---|---|
| Web | **W-07**: lộ trình và tiến độ đầu-cuối; sau đó W-11 chia sẻ bằng link | Gateway progress/PUT theo actor, node thuộc graph đã ghim; UI module mở/gập, đánh dấu/bỏ dấu, rollback khi API lỗi; JSON thật, ảnh/video và browser PG |
| Lõi | Xác nhận phần tiến độ SA-47 phục vụ W-07; tiếp **backend/worker W-14 với bộ dựng giả** | Hợp đồng upload/xác nhận/queue trước; worker/callback W-13 ghi usage thực kể cả lỗi/huỷ, kiểm tranh việc/huỷ/dùng lại; DB/source/FK nối đúng W-06; phối hợp React khi web chuyển sang W-14 |
| Thiết kế | **W-24 phần Figma còn thiếu**, ưu tiên màn W-07 và upload/xác nhận W-14 | Raw Variables export + provenance, bảng đủ node/trạng thái/sáng tối/390/768/1280, bốn prototype/video và assertion clipboard/citation/GIF đúng hành vi; cập nhật bản Figma theo lỗi đã sửa local |

W-07 và W-14 có thể chuẩn bị song song trong worktree riêng; W-14 backend xong riêng chưa đóng vé. Nếu thiếu người React, ưu tiên hoàn tất W-07 trước rồi tích hợp W-11/W-14 theo thứ tự điều phối. W-04 đủ điều kiện nhưng không tranh người với đường học chính. Không làm W-08/W-09/W-10 ngay như đã đủ mọi phụ thuộc B2.

**Điểm kiểm trước W-07:** đã soát độc lập và approve phạm vi SA-47 memory/JSON: learner-write và quiz read–check–write cùng `store.atomic()`, hai instance dùng chung một store object, hai thứ tự và race đều kiểm trạng thái cuối; JSON mở lại và dữ liệu owner/doc/node khác được kiểm. Không suy rộng bảo đảm JSON sang nhiều process/store object. Đủ mở W-07 theo hợp đồng hiện có; W-07 vẫn phải kiểm PostgreSQL qua các connection/runtime độc lập: A đánh dấu không đổi B, learner bỏ dấu không bị quiz đúng ghi đè, node ngoài graph trả 404. Đây chưa phải nghiệm thu chức năng W-07 hoặc toàn SA-34; cổng W-06 xanh không tự đóng SA-46/49/50/51.

**Migration tiếp theo:** W-07 không thêm bảng thì không tạo migration rỗng. W-11 và W-14 mỗi vé một migration, nhận head main mới trước khi ghép; điều phối chốt tuyến theo thứ tự tích hợp, không cho hai nhánh cùng giả định làm successor của `w06_0005`. W-14 có thể làm service/worker/test trước phần ghép schema nếu W-11 đang chiếm tuyến.

**Các mốc sau:** W-07 → W-08/W-09/W-10 theo từng phụ thuộc B2; W-11 → W-12; W-14 đạt mới mở W-15 chạy dựng thật, dry-run và duyệt tiền mới. W-23 chờ W-22 và các màn học; W-21 vẫn là đợt triển khai/sao lưu/end-to-end cuối. Giới hạn quiz cloze offline từng ghi 1/5 ở mẫu phục hồi vẫn cần xử lý trước nghiệm thu quiz, không che bằng cổng W-06.

Ghi nhận từ báo cáo web: chủ dự án hỏi đặt tên khoá trước index; đề xuất ô tên ở bước xác nhận của W-14, trước queue/dựng, mặc định tên tài liệu. Cần đối chiếu chỉ thị khi chốt hợp đồng W-14, chưa tự thêm giao diện hay biến câu hỏi thành thay đổi trong W-06.

Đợt này chỉ lập kế hoạch và cập nhật hồ sơ; chưa gửi giao việc sang ba phiên nhân viên. Cả ba nhận main mới trước lượt sau, chỉ chép dữ liệu theo manifest/hash, giữ mọi worktree/snapshot. Vertex tiếp tục được dùng; các lượt kiểm W-07/W-11/W-14 dùng đồ giả, 0 USD.

## 6. Ghép và trạng thái cuối

- Commit merge **`dc41ee83513bf609065f74ffe151e782125a171e`**, hai cha `29e4350` và đúng mốc được soát `8b6e500`, dùng `--no-ff`, không xung đột.
- Đã push thành công: `29e4350..dc41ee8 main -> main`. Đối chiếu `src/`, `tests/`, `scripts/`, `design/` ở commit ghép giống hệt mốc qua cổng.
- Hồ sơ điều phối cập nhật sau ghép: vé W-06/W-07/W-11/W-14/W-24, bảng kế hoạch, nhật ký, mô tả schema W-06→W-14 và bằng chứng độc lập có manifest SHA-256. Chỉ thay tài liệu sau cổng, không thay mã sản phẩm.
- `git diff --check` của phần mới có một dòng khoảng trắng trong preview W-04; không sửa định dạng ngoài phạm vi để đổi mốc đã kiểm. Log kiểm nguyên byte được giữ để đối chiếu, không gộp bằng chứng của nhân viên thành lượt điều phối.
- Giữ nguyên worktree nhân viên, worktree nghiệm thu, snapshot/ZIP và t01a. Chưa gửi giao việc sang các phiên; chủ dự án có thể dùng kế hoạch ở mục 5 để mở đợt tiếp.
