# W-14 — backend/worker giả, 2026-10-21

## Hợp đồng bàn giao trước triển khai

Nền main `eb6af08`; nhánh `work/w14-build-worker`, worktree `tmp/w14-build-worker`.
W-06 đã nghiệm thu/ghép `dc41ee8`. Đã đọc bàn giao W-07 `cd1ecb8`: không thêm
migration, không sửa composition; chưa tự nhập nhánh W-07. Giữ các worktree cũ.

### HTTP `/api/v1`, phiên cookie và CSRF hiện có

| Route | Yêu cầu | Phản hồi |
|---|---|---|
| POST /uploads | multipart `file`, `rights_confirmed=true` | upload-1 + build-1; chưa chạy |
| GET /uploads/{id} | người tải | upload-1, build hiện tại |
| POST /uploads/{id}/build | `{"title":"Tên khoá do người dùng đặt"}` xác nhận rõ ràng | build-1; idempotent theo upload |
| GET /builds/{id} | chủ một upload liên kết bản dựng | build-1 theo course của actor |
| POST /builds/{id}/cancel | `{}` | build-1; chỉ người yêu cầu chạy được huỷ việc dùng chung |
| POST /builds/{id}/retry | `{}` | build-1; chỉ lỗi retryable, không trừ lượt lại |
| GET /me/usage | actor | quota lượt/tháng; không trả tiền/token |

Khách 401, disabled 403, upload/build của người khác 404. Admin không được đọc
upload/build người khác qua các route người dùng này. Không nhận owner/doc/version
từ body. Người chưa xác minh email vẫn được tải/xác nhận. `rights_confirmed` bắt buộc.

Ví dụ JSON **mẫu thiết kế**, chưa phải log HTTP:

```json
{"contract_version":"upload-1","upload_id":"<uuid>","original_name":"Dai so.pdf","kind":"pdf","size_bytes":1234,"page_count":2,"build":{"contract_version":"build-1","build_id":"<uuid>","course_id":"<uuid>","status":"awaiting_confirmation","step":null,"step_index":0,"step_count":4,"started_at":null,"finished_at":null,"confirmation_expires_at":"2026-10-24T00:00:00Z","cancel_requested":false,"can_cancel":true,"can_retry":false,"error":null}}
```

Sau POST xác nhận, cùng build_id/course_id có status queued; worker báo reading /
doc_reading, running / concepts → graph → learning_prep, rồi succeeded. Lỗi đọc
ban_quet/ngon_ngu_khong_ho_tro/chu_loi: rejected. Lỗi mạng: failed/retryable.
Không xác nhận đủ 72 giờ: cancelled, error confirmation_expired, không trừ lượt.
Lỗi HTTP dùng envelope hiện có `{"error":{"code":"file_invalid","message":"…","retry_after":null,"ref":null}}`.
Không public_id, đường dẫn nội bộ, chi phí, token hay dự toán trong các DTO người dùng.

React giữ `course_id` trong phản hồi upload/xác nhận và dùng
`GET /builds/{id}?course_id=<course_id>` khi hỏi mỗi 3 giây; cancel/retry cũng nhận
query này. Query luôn được kiểm lại theo actor và upload gắn build, sai thì 404.
Nhờ đó cùng một người tạo hai khoá khác tên từ cùng tài liệu vẫn nhận đúng khoá
của trang đang mở. Nếu bỏ query, API chọn một khoá của actor để tương thích lời gọi
chỉ có build_id; React mới phải gửi query để giữ đúng ngữ cảnh.

### Ownership, dùng chung và idempotency

Mỗi lần tải hợp lệ tạo upload và course riêng, đúng một owner membership cùng
transaction. SHA-256 → doc_id u- + 20 hex, pipeline_version do server cấu hình.
Cùng tài liệu/pipeline dùng chung build đang dở hoặc thành công. Khoá DB theo
doc/pipeline và unique partial index bảo vệ đồng thời. POST xác nhận lặp không
tạo course/build thứ hai. Upload mới là một lần tải mới; không hứa dedup upload.

Build đang chờ: actor xác nhận đầu tiên thành requested_by, chịu quota/usage.
Actor khác xác nhận cùng việc chỉ gắn course riêng, không trừ lượt. Build thành
công dùng lại: course ready theo đúng graph/module metadata đã lưu, không chạy
runner và không nhập chi lịch sử. Một actor không có quyền huỷ/retry việc đang
chạy do actor khác yêu cầu; UI dùng can_cancel/can_retry.

### Schema và tuyến migration

**Tuyến đã được chốt tại main `2f4998c`: w06_0005 → w14_0006 → w11_0007.**
W-14 giữ migration đang có, W-11 nhận migration này rồi nối phía sau; không tạo
hai head. Đã nhận cập nhật tài liệu, không tự sửa nhánh W-11 hay nhắn phiên khác.

Tạo upload/build/media_asset; course.build_id có FK build, upload.course_id
liên kết nguồn PDF/DOCX riêng của course; khoá mẫu vẫn source_public_id và null
build. Bổ sung bản ghi attempt/checkpoint để fence worker cũ và chống cộng usage
hai lần. Không sửa migration W-06.

### Điểm cần chốt / giới hạn port

- **Chủ dự án đã chốt trong phiên:** được đặt tên khoá trước khi index. Tên điền
  sẵn từ tên tài liệu; POST xác nhận nhận title (1–120 ký tự sau trim), ghi tên
  trước khi queued trong cùng transaction. Không truyền title vẫn giữ tên mặc định.
  Xác nhận lặp không đổi tên lần đầu; muốn sửa tiếp dùng PATCH course sẵn có.
- Vé ghi PDF 400 trang, spec chức năng và WebSettings ghi build_max_pages mặc
  định không giới hạn. Theo nguồn chân lý spec: giữ mặc định None, kiểm trần khi bật.
- BuildResult W-13 có tổng usage của lần chạy; progress không bắt buộc usage từng
  bước. Ghi từng bước khi có số thực; phần tổng chưa phân bổ ghi step=null, không
  bịa chia tiền đều. Báo rõ khả năng phân bổ khi nối W-15; không sửa lõi.
- Bộ dựng thật, React W-14 và nghiệm thu toàn vé chưa nằm trong bàn giao backend này.

## Kế hoạch và phép kiểm

1. Migration + upload/xác nhận → kiểm tệp/quyền, atomic owner/FK, chưa chạy trước xác nhận.
2. Queue/worker → hai worker, dedup, timeout/reclaim một lần, quota/cap, huỷ theo bước.
3. Callback W-13 → SQL độc lập đối chiếu số khác 0 ở success/error/cancel, thiếu số giữ false.
4. Copy giả → allowlist/manifest/hash, không liên kết; đúng graph/media, dọn tệp do worker sở hữu.
5. RED/GREEN/mutation + cổng qua runner trên commit, báo cáo log/JUnit và React còn chờ.

## Triển khai đã có

### Phân vùng và composition

- `application/builds.py`: nhận tệp, kiểm quyền/định dạng/quota, SHA-256,
  xác nhận kèm tên, dùng chung build, DTO an toàn, huỷ/thử lại và quota tháng.
- `infrastructure/build_store.py`: transaction, advisory lock theo tài liệu,
  `FOR UPDATE SKIP LOCKED`, lease UUID, heartbeat/reclaim và receipt usage.
- `application/build_worker.py`: thực thi một việc bằng BuildRunner nhận recorder,
  heartbeat nền 30 giây, huỷ/trần ở ranh giới bước, ghi trạng thái/usage,
  publish graph metadata và media, thông báo qua Mailer được tiêm.
- `infrastructure/fake_build.py`: bọc FakeBuildRunner W-13; kiểm manifest/SHA-256
  và từng đường dẫn trước chép, chỉ sáu doc phát triển; dùng vùng staging riêng
  cho mỗi execution và chỉ phát hành artifact khi thành công.
- `fakes/local_media.py`: media giả lưu ở đĩa riêng để API và worker khác runtime
  đọc được cùng tệp. Composition W-14 mặc định dùng bản giả này; worker mặc định
  dùng FakeMailer, không tự gửi SMTP hoặc upload Cloudinary.
- `api/builds.py`, `WebServices.builds`, `compose_build_service`: hợp đồng HTTP;
  `CourseService.build_service` thêm trường `build` vào card đã kiểm thành viên.
  OpenAPI đã xuất lại; không thay learning runtime/transport Vertex của W-06.

Không sửa mã frontend, nhánh W-07 hay lõi `src/doc2roadmap/`. Cấu hình worker giả
chỉ nhận dev; chưa có lựa chọn runner thật. Media Cloudinary hiện có vẫn nhận
port download với destination do worker sở hữu, nhưng không được gọi trong kiểm.

### Di trú / ownership / nguồn

`w01_0001 → w05_0002 → w02_0003 → w03_0004 → w06_0005 → w14_0006`.
Migration mới tạo upload/build/media_asset/build_attempt và FK course.build_id.
upload.course_id là FK deferred để tạo upload/build/course/owner membership cùng
transaction. Course tạo từ upload có source_public_id bằng upload.public_id riêng
của actor; mẫu cũ giữ source_public_id và build_id null. Khi dùng chung build,
mỗi course vẫn giữ nguồn/tên/chủ riêng, doc_id và phiên bản graph dùng chung.

Unique partial index giữ một build dở theo doc/pipeline. Xác nhận đầu tiên đặt
requested_by/người chịu quota; các xác nhận tiếp theo không tính thêm lượt.
Quota tháng lấy múi giờ Việt Nam, có override account; retry/reclaim giữ queued_at
gốc để không dịch lượt cũ sang tháng mới. Retry tạo lease mới, giữ receipt cũ.

Claim_count tối đa 2 cho một chu kỳ tự reclaim. Huỷ queued/awaiting kết thúc ngay;
huỷ running dừng trước bước kế tiếp, không hoàn lượt. Bản dùng chung chỉ người
yêu cầu chạy được huỷ/retry; mỗi actor vẫn đọc được build qua course của mình.

### Callback và số liệu

BuildResult được ghi vào build_attempt cùng build_id/lease. Cumulative usage của
progress (nếu có) được ghi theo delta từng checkpoint. Callback cuối chỉ cộng phần
chưa ghi, không cộng lại cache/artifact hoặc receipt đã kết thúc. usage_ledger có
purpose=build, learner_id/user_id thực, doc_id, build_id, lease, token, model_calls,
cost và usage_complete. Các bản ghi dùng chung PostgreSQL với web/Pha B.

Callback muộn của lease cũ vẫn ghi số thực đúng receipt một lần, nhưng không đổi
status/graph/course của worker mới và không gửi thư kết quả giả. Nếu worker chết
mà thiếu số thì build giữ usage_complete=false. Lỗi khi phát hành graph/media sau
khi runner đã trả số không làm mất usage đó. Tổng chưa phân bổ được theo bước
ghi step=null, attribution_complete=false; không suy số phân bổ từ artifact.

### Dữ liệu và môi trường kiểm

Đã chép độc lập 3.144 tệp theo hai manifest bàn giao W-06, kiểm SHA-256 từng tệp;
không liên kết hay nhập kho CLI/live. Core fake thật được kiểm với doc-6 v29,
2 module; không dựng lại sáu cuốn, không ghim v45/v57. Test media riêng dùng
ảnh giả và media có cờ confirmed, không giả danh kết quả upload Cloudinary thật.

Các kiểm dùng PostgreSQL UUID riêng, MemoryMediaStore/LocalFakeMediaStore,
FakeMailer và runner giả. Chặn entry point model/ADC/SMTP/Cloudinary. Số .001,
.003, .007, .009, .12… trong SQL là **usage giả cố ý khác 0** để kiểm đối soát;
chi phí nhà cung cấp thực là **0 USD**, không phải tổng các số giả đó.

### Các lỗi đã thấy đỏ rồi sửa

- Chưa có service: collection đỏ khi bắt đầu; không dùng lỗi import làm bằng chứng guard.
- Ca PDF 11 MB ban đầu có test ID quá dài; đã đặt ID ngắn, không bỏ ca kiểm.
- Allowlist của wrapper ban đầu tính thừa loại artifact ngoài danh sách core fake
  chép; đã giới hạn đúng các subtree được phép, vẫn từ chối tệp thừa/sai hash.
- Callback mất lease ban đầu bị bỏ cả usage: SQL độc lập thấy tổng null thay
  .009; đã ghi usage receipt cũ và giữ status worker mới. Giữ RED riêng.
- Một actor có hai course chung build: response xác nhận ban đầu trả course đầu
  tiên. Test RED so hai UUID khác nhau; đã giữ đúng context, thêm query course_id
  được kiểm quyền cho polling/cancel/retry. Giữ RED riêng.
- Lượt cổng `w14-final-gate1` tại `5b20c5e` được chủ động dừng khoảng 3% để sửa
  context trên. Không tính là xanh. Phép phá context mới ban đầu còn có thể xanh
  khi timestamp của hai upload bằng nhau và UUID ngẫu nhiên tình cờ chọn đúng
  course. Đã tăng đồng hồ giả một giây giữa hai upload; phép phá sau đó đỏ chắc
  chắn. Không khởi động gate2 sau lượt mutation bị từ chối; cổng chốt dùng
  basetemp mới `w14-final-gate3`.

## React còn chờ / việc vé sau

React W-14 chưa triển khai trong nhánh này. Web nối màn kéo thả/chọn tài liệu,
checkbox quyền dùng, ô tên điền sẵn và sửa trước xác nhận; chỉ bấm “Dựng lộ trình”
mới POST xác nhận. Poll theo build_id + course_id, đọc can_cancel/can_retry;
ẩn quota khi build_monthly_max null và không hiển thị tiền/dự toán. Cần kiểm UI,
ảnh/video các trạng thái và nghiệm thu đầu-cuối trước đóng W-14.

W-15 mới nối build_document_runner thật, pipeline_version commit/cấu hình và
MediaStore/Mailer thật qua composition. Mặc định hiện tại `web-fake-v1` cố ý là
pipeline của bộ dựng giả, không tuyên bố là phiên bản chuỗi sản phẩm thật.
Fake dùng nội dung cuốn phát triển để kiểm đường ống; không chứng minh chất lượng
bài học của tài liệu mới. W-08 nối đọc nguồn/media theo khoá tài sản của từng bản parse.

**Yêu cầu port cho W-15, không tự sửa lõi:** progress W-13 chưa bắt buộc số usage
tích luỹ từng bước. Muốn có sổ chi từng bước và cổng trần phản ứng ngay giữa một
lượt thật, cần callback usage checkpoint từ pipeline. Tái hiện: BuildResult chỉ
có tổng, callback progress chỉ có status/metadata; web chỉ biết tổng khi recorder
được gọi. Backend hiện nhận được phần mở rộng usage và đã kiểm bằng đồ giả,
ghi phần chưa phân bổ rõ ràng thay vì suy số. Tuyến W-14 trước W-11 đã chốt tại
`2f4998c`; chưa tự mở head W-11 hay gửi tin sang phiên khác.

## Kết quả chốt và bằng chứng

Mốc kiểm cuối **`21a58354ff11a039382066d06f4594e76ba0df2f`**; đã `git merge main`
trước kiểm, main nền **`eb6af0855b8a7f7c42cca8399fe74e189f9aadfe`**. Sau cổng,
main có thêm `2f4998c6d2cafa52d881f514e879fcbf06417c96`, chỉ đổi sáu tệp tài liệu/vé;
đã nhận bằng merge `9e3cfb9`. Đối chiếu `src/`, `tests/`, `scripts/`, `pyproject.toml`
với mốc kiểm không có diff. Không ghi là đã chạy lại cổng sau cập nhật tài liệu.
Các commit sau mốc kiểm chỉ đóng gói hồ sơ hoặc nhận tài liệu main, không đổi mã/test.

| Cổng | Kết quả | Hồ sơ |
|---|---|---|
| Python toàn repo, PostgreSQL bắt buộc | **2.143 đạt, 1 skip, 0 lỗi/fail; exit 0; 483,49 giây** | [JUnit](w14-evidence/w14-final-gate3.xml), [log](w14-evidence/w14-final-gate3.log), [native exit/commit](w14-evidence/w14-final-gate3-exit.json) |
| Backend trong cổng cuối | **289 đạt, 1 skip** | Cùng JUnit trên |
| W-14 trong cổng cuối | **35 đạt**, không skip | Cùng JUnit trên |
| Phá guard rồi phục hồi | **14/14 bị assertion bắt**, không setup error | [Ledger](w14-evidence/mutations.json), log/XML RED theo tên |
| React nền main W-06 | **77 đạt**, exit 0 | [Log](w14-evidence/w14-final-react.log) |
| TypeScript/Vite build | Exit 0 | [Log](w14-evidence/w14-final-build.log), [mốc chạy](w14-evidence/w14-final-frontend-exits.json) |

Một skip là `test_cloudinary_satisfies_shared_media_contract_when_explicitly_enabled`;
không có PostgreSQL hoặc W-14 bị skip. Cảnh báo Docling/PDFium/SWIG/Starlette là
deprecation, không phải lỗi ứng dụng; native exit được ghi riêng, không suy từ
dòng PowerShell NativeCommandError khi stderr có cảnh báo. W-07 đã bàn giao ở
nhánh riêng, chưa ghép main; số 77 trên là regression gate của nền W-14 hiện tại,
không thay kết quả 85 React của nhánh W-07.

Log PowerShell UTF-16 được chuyển sang UTF-8; bỏ khoảng trắng cuối dòng của log/XML
để hồ sơ qua diff check. Số testcase/failure/error/skip không thay đổi.

14 phép phá: chạy trước xác nhận; bỏ tên người dùng đặt; bỏ kiểm người tải; ghi
chi 0 thay số trả về; che cờ thiếu usage; bỏ cờ huỷ; bỏ trần chi; để callback cũ
đổi trạng thái; mất usage khi publication lỗi; upload media chưa confirmed; bỏ
usage callback muộn; mất trạng thái huỷ ở race ranh giới bước; bỏ SKIP LOCKED;
trả nhầm course trong bản dựng dùng chung. Mọi nguồn đã phục hồi trước cổng cuối.

### JSON và SQL độc lập

- [JSON HTTP thật qua TestClient](w14-evidence/http-contract.json): upload,
  xác nhận kèm tên, card đang dựng, bốn bước, kết thúc và quota. PostgreSQL thật;
  không phải TCP/browser và không phải mock phản hồi HTTP.
- [Queue/dedup/hai worker](w14-evidence/sql-queue-claims.json).
- [Capacity](w14-evidence/sql-capacity.json).
- [Success](w14-evidence/sql-succeeded.json), [error thiếu usage](w14-evidence/sql-failed.json),
  [cancel](w14-evidence/sql-cancelled.json): kết nối độc lập đọc build/ledger.
- [RED mất usage muộn](w14-evidence/w14-late-usage-red2.xml),
  [RED trả nhầm course](w14-evidence/w14-course-context-red.xml),
  [GREEN tập trung](w14-evidence/w14-context-green.xml).
- [Đối chiếu fixture](w14-evidence/w14-fixture-copy.log),
  [tóm tắt máy đọc](w14-evidence/summary.json).

### Mốc triển khai

| Commit | Phần |
|---|---|
| `1e0cbf4` | Hợp đồng đầu tiên, trước mã |
| `7f36a17` | Migration/store/queue/receipt |
| `a40a09e` | API và xác nhận kèm tên trước index |
| `5f29568` | Worker/core fake/manifest và kiểm đầu tiên |
| `226d20f` | Usage muộn, race huỷ, checkpoint/cổng độc lập |
| `5b20c5e` | Media giả bền qua runtime API/worker, Mailer giả mặc định |
| `81442d7` | Giữ course context trong response/polling |
| `21a5835` | Làm phép kiểm context xác định; mốc cổng cuối |

### Lệnh tái lập 0 USD

Chạy từ worktree W-14; runner đọc URL PostgreSQL test từ môi trường/.env mà
không in credentials. Dùng basetemp mới cho mỗi lượt, không chạy mutation cùng
lúc cổng khác. Fixture là bản sao cố định theo manifest, không tạo liên kết.

```powershell
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe -X utf8 src/web/backend/tests/copy_w06_fixtures.py
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py src/web/backend/tests/test_builds_w14.py -o addopts= -q --basetemp=tmp/w14-kiem-moi --junitxml=tmp/w14-kiem-moi.xml
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe -X utf8 src/web/backend/tests/w14_mutations.py
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py -o addopts= -q --basetemp=tmp/w14-cong-moi --junitxml=tmp/w14-cong-moi.xml
npm.cmd --prefix src/web/frontend test -- --pool=threads --maxWorkers=1
npm.cmd --prefix src/web/frontend run build
```

CLI `web worker` yêu cầu `--fake-source`, `--fixture-root`, `--manifest`,
`--manifest-sha256`; dùng `--once` để nhận tối đa một việc. Chỉ dùng DB dev riêng,
không chạy phá/seed vào DB của chủ dự án. Để kiểm hoàn toàn tự động với DB UUID,
chạy các test `test_worker_cli_dispatches_real_once_loop_with_injected_fake_services`
và `test_default_fake_media_survives_independent_api_and_worker_composition`.
Chưa khởi động worker chạy nền trên DB dev của chủ dự án.

Đã tự soát quyền/CSRF, SQL bind, atomic owner, FK, queue lock, lease/receipt,
idempotency, quota Việt Nam, trần ngày, huỷ/race, nguồn/tệp tạm và transport.
Đây là **bàn giao backend/worker giả**, chưa phải nghiệm thu độc lập hay đóng
W-14 đầu-cuối. Theo cập nhật `2f4998c`, người soát chờ chủ dự án báo mới bắt đầu
nghiệm thu; chốt tuyến không phải cho phép ghép ngay. Không tự ghép/push main;
không tự sửa vé/kế hoạch/handoff (chỉ nhận thay đổi tài liệu của main).
