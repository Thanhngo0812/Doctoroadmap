# W-17.2 — Metadata bản dựng và khoá mẫu (backend)

**Trạng thái:** đang hoàn tất (code + test xanh, bảng phá xong; còn chạy lại sau commit cuối).
Nhánh `work/w17-builds-samples-backend` (worktree `tmp/w17-builds-samples-backend`), tạo từ main local 96515f08. Không ghép, không push.

## Phạm vi

Hai điểm cuối, không migration (dùng bảng `build`, `upload`, `account`, `course`, `audit_event` sẵn có):

1. `GET /api/v1/admin/builds`
2. `PATCH /api/v1/admin/courses/{cid}` với `{"is_sample": bool}`

Mã: `application/admin.py` (`list_builds`, `set_sample_course`), `application/admin_ports.py`, `infrastructure/admin_store.py` (SQL), `api/admin.py` (DTO/route), `src/web/openapi.json` (snapshot cập nhật, chỉ thêm). Test: `tests/test_w17_builds_samples.py` (34 ca), bộ phá `tests/w17_2_mutations.py`. Sửa nhỏ ở test cũ: `test_w17_admin.py` (helper liệt kê route thay `{cid}` và gửi thân `is_sample`; vòng "mọi route admin trả 200" bỏ qua route khoá mẫu, đã có test riêng) và `test_courses_w06.py::routes_with_cid` (kho kiểm kê "mọi route `{cid}` trả 404 cho người ngoài" bỏ tiền tố `/api/v1/admin/`, vì route admin cố ý tác động lên khoá theo id; không bỏ qua nó thì 3 ca W-06 và 1 ca W-17.1 đỏ).

## Hợp đồng cho React

Mọi phản hồi `cache-control: no-store`. Lỗi theo dạng `{"error":{"code","message","retry_after","ref","fields":[{"loc","message"}]}}`.

### GET /admin/builds

Tham số (tất cả tuỳ chọn): `q` (≤254, tìm con chuỗi không phân biệt hoa thường trên `doc_id`, email người yêu cầu; hoặc bằng đúng `build_id`; ký tự `%`/`_` là chữ thường), `status` (`awaiting_confirmation|queued|reading|running|rejected|succeeded|failed|cancelled`), `usage_complete` (bool, `false` = thiếu usage), `since`/`until` (ISO có múi giờ, nửa mở `[since, until)` trên `created_at`, `since < until`), `limit` 1–100 (mặc định 50), `offset` 0–100000. Sắp xếp `created_at` giảm dần, rồi `id`. `total` là tổng sau lọc.

Ví dụ một phần tử (`items[]`, số thật từ test):

```json
{
  "build_id": "71b6ae08-5d1c-4501-b606-17adb79b48d1",
  "doc_id": "u-2c5dee23da2afe8e9890",
  "status": "succeeded",
  "step": "learning_prep",
  "pipeline_version": "web-fake-v1",
  "requested_by": {"user_id": "12b16541-0cef-427c-9034-ae50f83b1628", "email": "ae98...@example.vn"},
  "upload": {"kind": "pdf", "page_count": 1, "size_bytes": 581},
  "course_count": 1,
  "counts_quota": true,
  "cancel_requested": false,
  "claim_count": 0,
  "created_at": "2026-03-10T05:00:00Z",
  "queued_at": "2026-03-10T05:00:00Z",
  "started_at": "2026-03-10T05:00:02Z",
  "finished_at": "2026-03-10T05:01:03Z",
  "error": null,
  "usage": {"spent_usd": 0.123456, "model_calls": 9, "input_tokens": 1200, "output_tokens": 340,
            "usage_complete": true, "elapsed_seconds": 61.5},
  "graph_version": 3,
  "module_count": 7
}
```

Bao ngoài: `{"items":[...],"total":5,"limit":50,"offset":0}`. Một bản dựng lỗi: `"error": {"code":"loi_mang","message":"Kết nối bị gián đoạn; bạn có thể thử lại","retryable":true}`.

Điều React cần biết:
- `requested_by` và `upload` có thể `null` (tài khoản bị xoá thì cột `requested_by` thành NULL).
- `error.code` thuộc `ban_quet|chu_loi|ngon_ngu_khong_ho_tro|loi_mang|het_tran_he_thong|loi_noi_bo|confirmation_expired|khong_ro`. `message` là văn bản cố định theo mã; cột `build.error_message` **không bao giờ được đọc**. Mã lạ trong DB hiện thành `khong_ro`.
- `spent_usd` là số (float, 6 chữ số thập phân), ước theo token, không thay hoá đơn.
- Không có: tên tệp gốc, tiêu đề khoá, `public_id`, sha, worker/lease, kết quả `build_attempt`, nội dung chat/tài liệu/quiz.
- `course_count` là số khoá trỏ vào bản dựng (không có id/tiêu đề khoá).

Lỗi: 401 `unauthenticated`; 403 `forbidden`/`account_disabled`; 422 `validation` (có `fields[].loc` = tên tham số) cho `limit`, `offset`, `status`, `usage_complete`, `q` quá dài, `since`/`until` thiếu múi giờ hoặc `since >= until`.

### PATCH /admin/courses/{cid}

Thân: đúng một trường `{"is_sample": true|false}` (bool chặt; thừa trường hay `"true"`/`1` thì 422). `cid` phải là UUID (sai thì 422).

Thành công 200 (tắt/bật lại cùng giá trị cũng 200, không ghi audit):

```json
{"course_id": "ffc922ed-1eb2-4202-8cf1-0903d59f9103", "doc_id": "doc-1", "title": "Khoá mẫu",
 "status": "ready", "is_sample": true, "published_graph_version": 1, "module_count": 2,
 "updated_at": "2026-01-01T00:00:00Z"}
```

Audit: mỗi lần **đổi thật** ghi một dòng `admin_course_sample_set` hoặc `admin_course_sample_unset` (`target_kind=course`, `target_id=cid`, cùng giao dịch với việc đổi cờ).

Lỗi:

| HTTP | code | khi nào |
|---|---|---|
| 401/403 | `unauthenticated`/`forbidden`/`account_disabled`/`csrf_failed` | chưa đăng nhập, không phải admin còn hiệu lực, thiếu CSRF/Origin |
| 404 | `not_found` | không có khoá `cid`, **hoặc** khoá không thuộc sáu `doc_id` phát triển (doc-1, nhap-mon-ml, naive-bayes, doc-6, xstk-ch3-1, doc-4): hai trường hợp cho cùng một phản hồi, không xác nhận sự tồn tại của khoá riêng, kể cả với admin |
| 409 | `conflict`, `fields[0].loc="env"` | `env` không phải `dev` (cả bật lẫn tắt) |
| 409 | `conflict`, `loc="is_sample"` | đã có khoá mẫu khác cùng `doc_id` (giữ bất biến một mẫu/tài liệu như `SampleSeeder`) |
| 422 | `validation` | thân hay `cid` sai |

Thứ tự kiểm: admin → bool → `env` → khoá tồn tại và thuộc allowlist (404) → trùng mẫu. Người không phải admin luôn nhận `forbidden`, không lộ chính sách `env`.

## Lệnh và số test

Tất cả qua `scripts/w05_run_tests.py`, PostgreSQL `db-test` (5433), DB UUID riêng, không chạm cổng 8000 hay `wayfinder-db-1`.

- Gốc: 79 ca W-17.1 xanh trước khi sửa (`test_w17_admin/first_admin/r11`).
- Đỏ trước: 33/34 ca mới fail (404 hoặc `AttributeError`, assertion, không phải lỗi setup) khi chưa có mã; ca còn lại (`csrf_and_origin_required_for_flag`) xanh sẵn vì middleware chặn trước route. Sau khi cài: 34 xanh.
- `src/web/backend/tests/test_w17_builds_samples.py`: 34 passed. Với `test_w17_admin/first_admin/r11` và `test_web_architecture` (snapshot OpenAPI): xem dòng tổng kết cuối báo cáo.

## Bảng phá (`tests/w17_2_mutations.py`, từng phép một, khôi phục bytes + đối chiếu SHA)

Mỗi phép chạy cả tệp test mới; "bắt" = có assertion fail, 0 lỗi setup. Bằng chứng: `report/w17-2-evidence/mutations/first/mutations.json` (và `second/` cho phép chạy lại sau khi thêm assertion).

| Phép phá | Bị bắt bởi |
|---|---|
| bỏ kiểm admin ở `list_builds` (service) | `service_layer_refuses_non_admin_and_stale_actors` |
| bỏ kiểm admin ở service **và** ở route builds | 8 ca (route inventory, user/demoted, service...) |
| bỏ kiểm admin ở `set_sample_course` (cả hai lần) | `admin_demoted_after_entering_the_lock`, `service_layer_refuses...` |
| bỏ kiểm admin lần đầu (trước `env`) | `service_layer_refuses...` (phần `env=prod`) |
| bỏ kiểm admin lại trong khoá | `admin_demoted_after_entering_the_lock_cannot_flag` |
| bỏ kiểm allowlist | 5 ca `flag_outside_the_six_allowlisted_documents` (chạy lại ở `third/`) |
| bỏ kiểm `env` | `flag_refused_when_the_environment_is_not_dev` |
| bỏ chống trùng mẫu | `second_course_of_the_same_document...`, `concurrent_flags_on_two_courses...` |
| bỏ khoá advisory | `concurrent_flags_on_two_courses_of_one_document_leave_exactly_one_sample` |
| ghi audit mỗi lần dù không đổi | `flag_on_off...audits_once_per_change`, `concurrent_identical_flags_audit_one_change` |
| tách audit khỏi giao dịch (đổi cờ commit riêng) | `flag_and_audit_commit_or_roll_back_together` |
| `StrictBool` -> `bool` | `flag_missing_course_and_invalid_bodies...` |
| DTO lỗi dùng `error_message` thô | `builds_item_contract...`, `builds_response_never_carries_private_or_raw_fields` |
| mã lỗi lạ đi thẳng ra DTO | `builds_item_contract_example_and_error_message_is_fixed_text` |
| bỏ `response_model` (không lọc trường thừa) | `builds_dto_strips_repository_extras` |
| `until` đóng / `since` mở | `builds_date_range_is_half_open_on_created_at` |
| tìm bằng `LIKE` (ký tự đại diện) / phân biệt hoa thường | `builds_page_filters_totals_and_order_match_independent_sql` |
| `total` bỏ qua bộ lọc | 5 ca (date range, page filters, item contract...) |
| sắp xếp tăng dần / bỏ `offset` / bỏ lọc status / bỏ lọc usage | `builds_page_filters_totals_and_order_match_independent_sql` |
| cho `since` không múi giờ và `since >= until` | các ca `builds_invalid_filters...` |

**Phép sống sót (1/26), ghi rõ vì sao tương đương:** `no-row-lock` — bỏ `FOR UPDATE` trên dòng `course` trong `lock_course`. Mọi lần gọi `set_sample_course` đã tuần tự hoá bằng khoá advisory `admin:samples` (và kiểm đó được bắt riêng), nên khoá dòng không đổi kết quả quan sát được. Giữ lại như lớp phòng thủ thứ hai chống thao tác xoá/đổi khoá ngoài đường admin (W-20 sau này). Nếu điều phối muốn tối giản, có thể bỏ.

## Quyết định đáng chú ý và giới hạn

- **Không tạo migration.** Không thêm chỉ mục duy nhất cho "một mẫu mỗi tài liệu"; bất biến giữ bằng khoá advisory trong `AdminService`. `SampleSeeder` (CLI) không lấy khoá này nên về lý thuyết có thể chạy đồng thời với PATCH; hiếm và chỉ do operator.
- **Không dùng `BuildService`**: nó gắn với người tải (`require_upload`, `requested_by`). Danh sách admin đọc thẳng bảng qua `AdminStore` với danh sách cột cố định, không nới guard chung. Chưa có retry/cancel/chi/Cloudinary/`lecture_validation`.
- **Không hiện tên tệp gốc và tiêu đề khoá** trong danh sách (do người dùng đặt, có thể là dữ liệu riêng); admin nhận diện bản dựng bằng `doc_id`, email người yêu cầu, `build_id`. Nếu cần tên tệp để gỡ lỗi, phải hỏi chủ dự án.
- `updated_at` của khoá đổi khi bật/tắt (dùng chung cột).
- Bản dựng của tài liệu `u-…` tái dùng (nhiều khoá cùng `build_id`) hiện một dòng với `course_count`, `requested_by` là người xác nhận gần nhất.
- Văn bản lỗi cố định lặp lại từ `build_worker.py` (từ điển cục bộ trong hàm nên không import được).
- Không đụng frontend, không có ảnh chụp (vé không có giao diện).

## Câu hỏi cho điều phối

1. Khoá ngoài allowlist trả 404 (như `SampleSeeder`/`join_sample` và để giữ bất biến "admin không xác nhận được khoá riêng"); `env!=dev` và trùng mẫu trả 409 `conflict`. Nếu muốn `env!=dev` cũng là 404 (giống seeder) thì đổi một dòng; hiện tôi giữ 409 để React hiện được "chỉ có ở dev".
2. Spec cơ sở dữ liệu (`doc/web-co-so-du-lieu-spec.md`, cột `action`) nên thêm `admin_course_sample_set/unset`; spec mục 9/11 và vé W-17 nên ghi hợp đồng này. Tôi không sửa spec theo sổ tay.
3. Có cần giữ quy tắc "một mẫu mỗi tài liệu" ở PATCH (tôi thêm) hay chỉ allowlist là đủ?
