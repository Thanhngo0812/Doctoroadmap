# W-06 — Hợp đồng và triển khai backend/gateway

Ngày 2026-10-20. Nhánh `work/w06-courses-gateway`, worktree `tmp/w06-courses-gateway`. Đã kiểm sạch và nhận main `06c98ea` (W-03 ghép `63f09ad`), sau đó nhận main dữ liệu `29e4350` bằng commit ghép vào nhánh riêng `003f408`. **JSON inline dưới đây là mẫu shape; JSON API thật được ghi riêng trong thư mục bằng chứng.** Chưa nghiệm thu W-06 với React đầu-cuối.

## Hợp đồng HTTP v1 — bản 1

Tiền tố `/api/v1`. Dùng cookie W-02 và `Origin` + `X-CSRF-Token` cho PATCH/POST. Chủ thể luôn lấy từ phiên đăng nhập. Các trường `owner`, `owner_id`, `doc_id`, `graph_version` trong body không quyết định quyền hay phạm vi dữ liệu.

### GET /courses — 200, mẫu

```json
{"owned":[],"joined":[],"samples":[{"course_id":"00000000-0000-4000-8000-000000000006","doc_id":"doc-1","title":"Đại số tuyến tính","description":"Khoá mẫu phát triển","status":"ready","is_sample":true,"published_graph_version":8,"role":null,"owner":{"user_id":"00000000-0000-4000-8000-000000000001","display_name":"Quản trị"},"module_count":35,"member_count":null,"progress":null,"resume":null}]}
```

Ba nhóm luôn tồn tại. `samples` chỉ có ở dev, chỉ chứa mẫu chưa tham gia; prod trả `samples: []`. Mẫu chưa tham gia chỉ hiển thị metadata, không đọc graph/Pha B để tính tiến độ. `module_count` lưu từ graph khi tạo mẫu. `member_count` chỉ có giá trị số khi actor là chủ khóa; người khác nhận null. `role` là `owner`/`learner`/null. `progress` của thành viên: `{"learned":0,"total":223}`. `resume` của thành viên: `{"module_id":"module_001"}` hoặc null nếu chưa ready/không có module. Resume lấy phiên module mới nhất còn giải được trong graph, rồi tiến độ gần nhất, rồi module đầu.

### GET /courses/{cid} — 200, mẫu sau tham gia

```json
{"course_id":"00000000-0000-4000-8000-000000000006","doc_id":"doc-1","title":"Đại số tuyến tính","description":"Khoá mẫu phát triển","status":"ready","is_sample":true,"published_graph_version":8,"role":"learner","owner":{"user_id":"00000000-0000-4000-8000-000000000001","display_name":"Quản trị"},"module_count":35,"member_count":null,"progress":{"learned":0,"total":223},"resume":{"module_id":"module_001"}}
```

Chưa tham gia kể cả mẫu: GET detail/roadmap trả 404; metadata mẫu lấy từ danh sách. Admin không có ngoại lệ học ngoài membership.

### PATCH /courses/{cid} — 200

Body `{"title":"Tên mới","description":"Mô tả mới"}`; một hoặc cả hai trường. Title 1–120 ký tự sau trim, description tối đa 1.000 ký tự. Chỉ chủ khóa được sửa; trả cùng shape detail. Thành viên thường 403; người ngoài 404. Body có trường khác bị bỏ qua, không được thay chủ/doc/version.

### POST /courses/{cid}/join-sample — 200

Body `{}`; không nhận user_id từ client. Tài khoản active đã đăng nhập (không bắt xác minh email) tham gia mẫu ready ở dev được ngay, chưa cần membership. Trả cùng shape detail với `role: "learner"`; chủ mẫu gọi lại giữ `role: "owner"`. Gọi lặp không tạo membership mới. Khóa riêng tư hoặc prod: 404. Khách không được tham gia (bị auth/CSRF từ chối, không thay đổi DB). Đầy khóa: 409 `course_full`.

### GET /courses/{cid}/roadmap — 200, mẫu nhỏ minh họa shape

```json
{"course_id":"00000000-0000-4000-8000-000000000006","doc_id":"doc-1","graph_version":8,"modules":[{"module_id":"module_001","index":0,"title":"Module đầu","description":"Mô tả từ graph","concepts":[{"node_id":"node-example","name":"Khái niệm mẫu"}]}]}
```

Thứ tự module theo `index`, khái niệm theo thứ tự `node_ids` đã công bố của module. Nội dung lấy từ graph, không tự gọi mô hình để đặt tên. Khóa chưa ready: 409 `conflict`.

**Bổ sung khi kiểm doc-1 thật — bản 2:** `modules[].description` giữ nguyên dạng trong graph: chuỗi ở fixture cũ, hoặc mảng các object `{"text":"...","node_ids":["..."],"module_ids":["..."]}` ở graph hiện hành. Hai danh sách ID có thể vắng. UI duyệt các phần `text`, không render thẳng mảng như chuỗi. Kiểm thực tế đã làm schema chuỗi ban đầu đỏ, nên mở union đúng dữ liệu, không sửa graph hay làm phẳng mất cấu trúc.

### Lỗi — dùng nguyên envelope W-01/W-02

```json
{"error":{"code":"not_found","message":"Không tìm thấy nội dung yêu cầu","retry_after":null,"ref":null}}
```

401 `unauthenticated`; 403 `account_disabled`/`forbidden`/`csrf_failed`; 404 `not_found`; 409 `conflict`/`course_full`; 422 `validation`. Không trả chi phí/usage cho người học. Test tự duyệt tất cả route `{cid}`, không whitelist bỏ qua join-sample; nhắm khóa riêng tư, actor ngoài phải nhận đúng 404 envelope.

## Schema, ownership, visibility và phân vùng

- Migration duy nhất `w06_0005 → w03_0004`: bảng `course`, `membership`. Khóa/membership chủ tạo cùng transaction. PK membership `(course_id, account_id)` chống tham gia trùng; partial unique owner theo course. Chủ khóa là admin chạy seed, cũng có membership owner. Tài khoản admin khác không tự được học.
- Mẫu là khóa bình thường có `is_sample=true`; không phải bản sao dữ liệu học. Dữ liệu cá nhân vẫn theo `(actor.user_id, doc_id)` trong PostgreSQL Pha B. Danh mục mẫu dev không cấp quyền nội dung trước join.
- Backend sở hữu `src/web/backend/wayfinder/{application,domain,infrastructure,api}/` liên quan course/gateway, composition, CLI seed, migration và test backend. Web sở hữu `src/web/frontend/`. Không cùng sửa composition/migration; tích hợp qua commit/backend contract. Không sửa `src/doc2roadmap/`, vé, kế hoạch hoặc handoff.
- Fixture: chép từng tệp theo manifest cố định và kiểm SHA-256 nguồn/đích, từ chối mọi reparse point/symlink/hardlink. Không đọc/copy `artifacts/phase_b/live.json`. Không chạm t01a hay dọn snapshot/worktree.

## Các lát thực hiện

1. Khóa/membership + một mẫu tham gia được qua HTTP/PostgreSQL → kiểm rollback, unique owner, join lặp, mọi route private và auth.
2. Gateway kiểm membership trước graph; composition Pha B/spend guard dùng một store PostgreSQL → đọc/ghi từ connection độc lập, cache graph theo doc/version, owner giả bị bỏ qua, Vertex giả ghi nhận đúng transport.
3. Seed sáu cuốn dev qua MediaStore giả, JSON thật doc-1, RED/GREEN guard/owner/store/transport, full gate và bàn giao cho web/điều phối; không tự đóng vé đầu-cuối.

## Điểm cần ghi nhận về schema

Bảng `build`/`upload` chưa có ở head W-03. W-06 sẽ giữ `build_id` nullable dạng UUID, chưa gắn FK vào bảng chưa tồn tại; FK cần thêm khi W-14 đưa bảng build vào. PDF mẫu cần lưu public_id MediaStore; lưu `source_public_id` nullable ở course cùng `module_count` metadata để danh mục chưa tham gia không tải graph. Không tạo trước toàn bộ bảng upload/build ngoài vé.

## Kết quả thực hiện

### Mốc mã và cách tích hợp

- Hợp đồng ban đầu: `c25c78c03d12fc76f56d0f79b4086b8880b48bed`.
- Schema/store/domain: `2e3c87acfb19ae389a97836ce37f4701736dfd51`.
- API, gateway, CLI và kiểm thử: `c694149aa93ad3e45831ed3fa5507a5027ecad16`.
- Kiểm đủ sáu cuốn qua HTTP TCP: `c5fb2012603fd545262d1e075d8c8762e1fb7498`; siết kiểm prod với đầu vào hợp lệ: `4f676d92218d0e770bb90a98452b4d7d21d0b35c`.
- Mã sản phẩm `src/web/backend/wayfinder/` và OpenAPI không đổi từ `c694149`; các mốc sau chỉ nhận main tài liệu và bổ sung kiểm thử/chép dữ liệu.
- `WebServices.courses` là CourseService; `WebServices.learning` là LearningGateway. Nhóm web chỉ cần prefix `/api/v1` và hợp đồng HTTP ở trên, không sửa composition/migration backend.
- `src/web/openapi.json` đã xuất lại từ ứng dụng thật. Không có production endpoint session/progress mới ngoài phạm vi W-06. `LearningGateway.learner(actor, cid, **untrusted)` là ngữ cảnh phía server, cố định owner/doc/version để các vé học dùng tiếp; probe HTTP chỉ tồn tại trong test.
- Người làm vé không ghép main, không sửa vé/kế hoạch/handoff. Từ khi chủ dự án yêu cầu dừng nhắn phiên khác, mọi kết quả chỉ ghi ở đây và báo lại trực tiếp chủ dự án.

### Lượt đã kiểm

| Kiểm | Kết quả |
|---|---|
| Backend (toàn `src/web/backend/tests`) | 252 đạt, 1 skip Cloudinary live opt-in có sẵn; không skip W-06 |
| Cổng cuối tại `4f676d9`, main nền `29e4350` | **2.105 đạt, 1 skip Cloudinary live opt-in; 0 lỗi; 346,45 giây** |
| Backend trong cổng cuối | **253 đạt, 1 skip**, gồm **20 test W-06 đạt**, không skip W-06 |
| React nền W-03, không phải React W-06 | 62 đạt; build Vite thành công |
| Cổng toàn repo ban đầu ở `c694149` (main nền `06c98ea`) | 2.104 đạt, 1 skip Cloudinary live opt-in; 406,47 giây |
| Khóa/membership | Owner và course cùng transaction; lỗi chèn owner rollback course; DB chặn owner thứ hai, xóa/move owner làm mất chủ |
| Join mẫu | Tài khoản chưa xác minh email tham gia mẫu dev được; join lặp một hàng; hai yêu cầu tranh chỗ cuối không vượt capacity; prod/khách không được join |
| Quyền | Mọi route `{cid}` tự vào phép kiểm người ngoài khóa riêng tư, kể cả join-sample; admin không là thành viên cũng 404; thu hồi membership vẫn chặn dù graph đã cache |
| Gateway | Trước khi đọc graph phải qua kiểm actor/membership; cache theo doc/version, khóa khác cùng doc/version dùng chung graph; publication không đổi bản khóa khác |
| PostgreSQL thật | Kết nối độc lập quan sát session/progress/reservation/usage có actor thật, không theo owner giả trong body; spend guard và use case không ghi vào JSON/memory |
| Vertex | Hai provider factory nhận `transport=vertex`; runtime giữ chính provider đó; không tạo PhaseBRuntime/JsonPhaseBStore CLI |
| Tiến độ/resume | Theo từng actor; session module giải được ưu tiên, rồi tiến độ gần nhất, rồi module đầu |
| Seed tổng hợp | Đủ allowlist 6 cuốn, từ chối doc giả ngoài danh sách/prod trước khi đọc graph/upload; MediaStore memory, lặp không upload/tạo lại |
| Seed sáu cuốn thật | CLI thật với MediaStore memory, graph loader thật, PostgreSQL; Uvicorn + HTTP TCP local thật để đăng ký/tham gia/đọc đủ sáu roadmap và tham gia lặp |

JSON **thật từ HTTP TCP + PostgreSQL**: [doc-1](w06-evidence/http-doc1.json), [đủ sáu cuốn](w06-evidence/http-six-books.json). Bao gồm GET courses trước/sau join, POST join, GET detail, GET roadmap đủ 35 module doc-1 và lỗi khóa riêng tư. Provider không được gọi, Mailer giả giữ thư trong bộ nhớ, MediaStore memory; không phải JSON từ mock API hay dữ liệu của người dùng thật.

| doc_id | Graph | Module | Node học |
|---|---:|---:|---:|
| doc-1 | 8 | 35 | 223 |
| nhap-mon-ml | 50 | 15 | 75 |
| naive-bayes | 49 | 5 | 33 |
| doc-6 | 29 | 2 | 11 |
| xstk-ch3-1 | 68 | 14 | 82 |
| doc-4 | 27 | 91 | 495 |

Trong DB kiểm thử có đúng **6 khóa mẫu, 6 membership owner, 6 membership learner** của lượt HTTP. Mỗi cuốn join hai lần vẫn chỉ một membership/người. Seed CLI hai lần vẫn chỉ 6 khóa và 6 lần upload vào MediaStore memory. Khóa riêng tư của fixture dùng riêng để thử chặn người ngoài, không cộng vào sáu khóa mẫu này. Các kết nối HTTP chỉ tới loopback, không phải lời gọi nhà cung cấp bên ngoài.

### RED/GREEN và những lỗi đã bắt

- Lượt đầu chưa có service/runtime/seed/composition hook: test đỏ. Khi có đủ lát triển khai, lượt tập trung xanh.
- Lượt backend đầu bắt UUID psycopg chưa chuyển chuỗi, shape `SessionUseCase.list_sessions` là list, và mô tả module thật là mảng. Đã sửa adapter/schema, không sửa graph hay lõi.
- `test_deferred_owner_check_protects_source_when_owner_membership_is_moved`: đỏ trước vì chuyển hàng owner sang khóa mới có thể bỏ trống khóa cũ; sửa trigger kiểm cả OLD/NEW, xanh sau đó.
- Hai test migration W-03 trước đây giả định head luôn là W-03. Giữ kiểm W-02→W-03 và bảo toàn account bằng nâng rõ `w03_0004`; phép kiểm head dùng một descendant của W-03. Test W-06 kiểm riêng một head chính xác `w06_0005`, nối `w03_0004`. Không sửa migration đã ghép main hoặc bỏ assertion nền.
- **8/8 mutation đã thất bại bởi assertion, không có setup error:** route mới không guard; gateway bỏ kiểm thành viên; lấy owner giả; spend guard trỏ memory; session use case trỏ memory; model/embedding đổi sang developer_api; bỏ kiểm đường dẫn liên kết không còn đích; cố chạy seed prod như dev với PDF/graph hợp lệ. Mã nguồn khôi phục trong finally sau từng phép thử. [Kết quả](w06-evidence/mutations.json), log/XML đỏ cùng thư mục. Phép kiểm hardlink/reparse dùng metadata giả, tuyệt đối không tạo liên kết để thử.
- Lượt `tmp/w06-final-gate` tại `c5fb201` được chủ động dừng ở khoảng 3% để siết test từ chối prod: tránh xanh vì thiếu PDF/graph, kiểm đúng `not_found`, không upload/ghi DB/đọc graph. Giữ log lượt dừng, **không tính là xanh**. Cổng sau dùng basetemp mới `tmp/w06-final-gate2`, trên mốc `4f676d9`.

### Tái lập và dữ liệu

Chạy từ đúng worktree, dùng Python `.venv` ở thư mục chung. Runner đặt PYTHONPATH vào mã của worktree, bắt buộc PostgreSQL và DB UUID riêng; không dùng DB phát triển. PostgreSQL test container đã chạy local, URL/mật khẩu không in ra báo cáo.

```powershell
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe -X utf8 src/web/backend/tests/copy_w06_fixtures.py
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py src/web/backend/tests -o addopts= -q --tb=short --basetemp=tmp/w06-backend-green --junitxml=tmp/w06-backend-green.xml
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe -X utf8 src/web/backend/tests/w06_mutations.py
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py -o addopts= -q --tb=short --basetemp=tmp/w06-final-gate2 --junitxml=tmp/w06-final-gate2.xml
npm.cmd --prefix src/web/frontend ci --no-audit --no-fund
npm.cmd --prefix src/web/frontend test -- --pool=threads --maxWorkers=1
npm.cmd --prefix src/web/frontend run build
```

Không chạy mutation đồng thời với lượt test khác vì harness tạm đổi mã rồi khôi phục. CLI sản phẩm: `web seed-samples --admin-email <admin> --source-root <bản-sao-dev> [--doc-id doc-1]`; bỏ `--doc-id` nhận đủ sáu. Lệnh sản phẩm có upload qua MediaStore cấu hình, **không chạy lệnh này với Cloudinary thật trong nghiệm thu**; kiểm CLI đã thay MediaStore bằng memory và graph loader giả. Chưa seed vào DB phát triển của chủ dự án.

Đã chép **3.144 tệp** theo hai manifest cố định:

- `report/doc1-rebuild-evidence-2026-10-20/development-fixtures.json`: SHA-256 `5fc819f723f7263fe3d443ec780009a75aae66f2c35db8fe0bc3e3c50464eb84`.
- `report/w06-fixtures-evidence-2026-10-20/development-fixtures.json`: SHA-256 `4f81f6d0f04e64bd02257aa873f9d68145bc121ec6e1ecf10d819458ed4d4a5a`.

Kiểm từng hash nguồn/đích, từ chối symlink/reparse point/hardlink và đường dẫn thoát root; bỏ một kho CLI rebuild riêng trong tổng 3.145 tệp vì gateway phải dùng PostgreSQL. [Danh sách hash](w06-evidence/fixture-copy.json). Không chép hay đọc `artifacts/phase_b/live.json`, không dọn/liên kết worktree hoặc sửa snapshot/ZIP/tập giữ lại. Gói dữ liệu do điều phối bàn giao và được chủ dự án chuyển tới; không tự thu gom thêm từ artifacts chung.

### Chưa hoàn tất / chờ phối hợp

- React W-06, trình duyệt, ảnh/video, một khóa mẫu tham gia đầu-cuối qua UI và cổng trên nhánh tích hợp cả web/backend chưa có ở nhánh backend này. Không đóng vé W-06 vì backend riêng xong.
- Chưa có bảng build/upload; `build_id` chưa có FK, `source_public_id` là metadata PDF mẫu tạm theo mục schema. W-14 cần thêm FK/mối nối upload khi bảng xuất hiện.
- Các chức năng học W-07…W-10 chưa mở endpoint; W-06 mới có roadmap và ngữ cảnh dùng tiếp. Không gọi mô hình/media/email thật, chi phí nghiệm thu **0 USD**.
- Cổng trước đã đạt tại `c694149`; cổng cuối dùng `4f676d9`, đã nhận main `29e4350`. Tự review không thay nghiệm thu độc lập của điều phối.

### Chốt hồ sơ backend

[Tóm tắt máy đọc được](w06-evidence/summary.json), [JUnit cổng cuối](w06-evidence/w06-final-gate2.xml), [log cổng cuối](w06-evidence/w06-final-gate2.log). Các lượt có phần giao nhau, không cộng số test các lượt thành tổng test độc lập. Log PowerShell UTF-16 đã chuyển sang UTF-8 để đọc được; không thay kết quả JUnit. Lượt kiểm cuối có exit 0; lượt bị chủ động dừng không được nhận là xanh.

Đã tự review: quyền trước graph, actor thay owner/body, bind SQL, visibility mẫu/dev/prod, transaction khóa/owner/capacity, cache vẫn kiểm membership, provider/store thực của phụ thuộc con, một tuyến migration. Không phát hiện lỗi lõi cần mở quyền `src/doc2roadmap/`. Phạm vi diff chỉ mã `src/web/`, báo cáo/bằng chứng W-06; không có PDF/artifact/cache/secret trong commit. Main vẫn ở `29e4350` khi chốt cổng. Backend đủ để chuyển cho nhóm web bằng commit của nhánh riêng; **chưa đóng W-06 đầu-cuối**.
