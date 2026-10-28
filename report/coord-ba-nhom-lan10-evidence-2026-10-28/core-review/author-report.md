# W-17.1 — backend người dùng và nhật ký quản trị

## Mốc và phạm vi

- Worktree `tmp/w17-admin-users-backend`, nhánh `work/w17-admin-users-backend`.
- Main local nhận khi tạo nhánh: `530a8c9f5109bac549b224f17ffee727d2767c07`.
- Mã triển khai: `7722a78bf80f1305ae19645b799d4bb23862f7b1`; commit kiểm mở rộng và HEAD chạy cổng: `8a8a46cb1e7eef2c95daddbe6cc36192b5aeff20`.
- Chỉ backend W-17.1: `AdminService.list_users/update_user/list_audit`, ba HTTP route, policy, repository, composition, DTO/OpenAPI và kiểm thử. Toàn W-17 chưa hoàn tất; React do web làm sau.
- 0 USD mới, Mailer/model/embedding/media giả. Không chạy W-15 operator, gửi thư thật, gọi Gemini/ADC/Cloudinary thật hay sửa core/transport/cache/giá/trần.

## Hợp đồng cho React

Tất cả dưới `/api/v1`, cookie phiên phía máy chủ; PATCH cần Origin và X-CSRF-Token hiện hành. Mọi phản hồi admin, kể cả lỗi, có `Cache-Control: no-store`.

| Route | Input | Phản hồi |
|---|---|---|
| `GET /admin/users` | `email` chứa chuỗi literal, trim/lower, tối đa 254; `role=user|admin`, `status=active|disabled`; `limit=1..100` mặc định 50; `offset=0..100000` mặc định 0 | `{items,total,limit,offset}` |
| `PATCH /admin/users/{uid}` | UUID; object không rỗng chỉ chứa `status`, `role`, `build_monthly_max` | Một item người dùng |
| `GET /admin/audit` | `actor_id` UUID, `action` tên snake_case tối đa 80, `since`/`until` timestamp có timezone; cùng phân trang | `{items,total,limit,offset}` |

Item người dùng: `id,email,display_name,role,status,email_verified_at,created_at,last_login_at,owned_courses,build_monthly_max,builds_this_month`. `last_login_at` có thể null, ví dụ admin được tạo bằng CLI nhưng chưa login. Đăng ký cấp phiên theo W-02 và ghi last_login_at ngay khi tạo tài khoản; login thành công cập nhật mốc này. `owned_courses` đếm course hiện còn thuộc chủ; không trả tên hay nội dung các khoá đó.

`builds_this_month = {used,max,resets_at}`: used là số lượt có `counts_quota=true` với queued_at trong tháng nửa mở theo Asia/Ho_Chi_Minh, cùng predicate và helper tháng của quota hiện hành. Không đếm lượt reuse hoặc cộng USD. `build_monthly_max` là override đã lưu; null kế thừa `WebSettings.build_monthly_max`. max là trần hiệu lực, null khi cấu hình demo tắt và không có override. PATCH chỉ nhận null hoặc integer 1..2147483647; không nhận bool, chuỗi, 0 hay số âm. Không đổi cấu hình toàn hệ thống.

Danh sách user xếp created_at giảm dần, id làm tie-breaker. Audit xếp at giảm dần, id giảm dần; since bao gồm, until loại trừ. Item audit chỉ có `id,at,actor_id,action,target_kind,target_id,ip`. Không đọc/trả `meta`, raw extra, hash, token hay bản ghi học.

Schema chuẩn được tái sinh từ app tại `src/web/openapi.json`: 60 operation nền được giữ, thêm 3 operation quản trị = 63. JSON HTTP thật/SQL PostgreSQL tổng hợp trong `w17-evidence/full-01/`, dùng tài khoản và dữ liệu giả; không phải log người học thật.

## Quyền, giao dịch và hành vi chưa có chính sách

Policy domain chỉ cho admin active. Service đọc lại tài khoản hiện hành, kể cả sau khi lấy lock, nên Actor cũ không giữ quyền sau demote/disable. Admin không có bypass học: test tự liệt kê mọi route có cid, trả not_found khi chưa là thành viên. Chat/tài liệu/đáp án có chuỗi đánh dấu trong PG được quét qua toàn phản hồi route admin và kết quả service.

Mỗi thay đổi dùng AuthStore.atomic, advisory lock chung `admin:users` và account locks cùng định danh với login/reset. Sau lock mới đếm role admin và ghi. Hai engine/runtime hạ quyền hai admin cùng lúc chỉ một giao dịch được đổi, giao dịch còn lại conflict. Việc tạo thêm admin bằng CLI không làm giảm số admin. Phép kiểm đếm tài khoản có role admin, bao gồm disabled; không tự thêm luật “phải có một admin active”.

Disable update account, xoá mọi auth_session và ghi audit trong cùng giao dịch. Login đang chạy chia sẻ account/email lock: nếu login hoàn tất trước, disable xoá cả phiên vừa tạo. Enable chỉ đổi trạng thái, không tái tạo phiên; cookie cũ tiếp tục 401 và phải login mới. Audit hoặc xoá session lỗi thì rollback account/quota/role/session. Payload sai, Origin/CSRF sai hoặc actor không đủ quyền không ghi thay đổi.

Mỗi field thực sự đổi ghi một event cùng transaction, meta rỗng: `admin_user_disabled`, `admin_user_enabled`, `admin_user_role_changed`, `admin_user_quota_changed`; actor lấy từ phiên, target_kind account, target_id uid. PATCH lặp cùng giá trị không tạo thay đổi/audit trùng.

**Điểm cần chủ dự án quyết định ở mốc sau:** spec chỉ cấm hạ quyền admin cuối, chưa cấm disable admin cuối. Trước W-17.1 chưa có route disable admin; hạ tầng account/session đã hiểu disabled. Triển khai này cho phép disable admin cuối theo trường status, giữ role admin và huỷ phiên như mọi tài khoản. Có test riêng và JSON `last-admin-disabled.json`; không coi đó là chính sách an toàn vận hành đã được duyệt. Đề xuất bổ sung luật bảo toàn ít nhất một admin active và quy trình phục hồi CLI; chưa tự áp dụng/chỉnh spec.

Không có migration mới: account/auth_session/audit_event/course/build và chỉ mục hiện hành đủ dùng; head vẫn `w12_0008`, không sửa migration đã ghép. Truy vấn có phân trang, chỉ chọn cột metadata, không tải ledger hoặc nội dung Phase B; không tạo IAM hay hệ nhật ký khác.

## Bằng chứng kiểm thử

| Invariant | Runnable assertion chính |
|---|---|
| Tìm email literal, phân trang/lọc giới hạn, DTO public | `test_users_public_projection_search_and_demo_null`, `test_pagination_literal_email_filters_and_last_login`, `test_users_filters_are_bounded` |
| Disable hai cookie, enable không hồi sinh, login cạnh tranh | `test_disable_revokes_two_cookies_enable_never_resurrects`, `test_inflight_login_cannot_leave_a_session_after_disable` |
| Admin cuối và hai runtime cạnh tranh | `test_last_admin_demote_rejected`, `test_two_postgres_runtimes_cannot_demote_both_last_admins` |
| Actor cũ, khách/người thường, route mới bỏ guard | `test_stale_admin_actor_and_unauthorized_patch_cannot_write`, `test_all_admin_routes_require_admin_and_no_store`, `test_admin_inventory_detects_an_unguarded_new_route` |
| Fields/CSRF và rollback audit/session | `test_invalid_patch_fields_never_change_account_or_sessions`, `test_csrf_and_origin_required_and_missing_user_is_stable`, `test_update_and_audit_rollback_on_audit_failure`, `test_update_rolls_back_if_session_delete_fails` |
| Trần override/null, tháng Việt Nam/năm nhuận | `test_patch_quota_override_null_fallback_role_and_idempotent_audit`, `test_user_monthly_counts_match_existing_quota_at_vietnam_boundary` |
| Audit metadata, lọc biên ngày, không nội dung riêng | `test_audit_filters_half_open_dates_and_never_exposes_arbitrary_meta`, `test_audit_invalid_filters_fail_with_fields`, `test_private_learning_records_are_inaccessible_to_admin_and_absent_from_every_admin_response`, `test_real_response_dtos_strip_repository_extras_at_every_level` |
| Hành vi disable admin cuối được nêu minh bạch | `test_disabling_only_admin_is_allowed_by_existing_status_rule_and_does_not_revive` |

Tất cả ở `src/web/backend/tests/test_w17_admin.py`: 48 case parametrized, PostgreSQL thực/cookie HTTP thực, Argon2 thật, fake clock và chặn network. SQL assertions dùng connection độc lập; snapshot SQL chỉ chứa cột public và số phiên, không chứa hash/token. Hai runtime race dùng hai engine PostgreSQL độc lập. Các bước đều qua runner `scripts/w05_run_tests.py`, không chạy pytest trần.

Lịch sử giữ cả lỗi:

- red-01: 5 fail, thiếu route/service trên nền cũ; không setup error.
- green-01: 4 pass, 1 fail do bộ liệt kê chưa duyệt router lồng nhau của FastAPI; sửa bộ kiểm đệ quy, thêm route cố ý bỏ guard.
- green-02: 6 pass.
- expanded-01: 48 pass (W-17 ở thời điểm đó + architecture).
- expanded-02: native 4, chỉ sai đường dẫn test `test_w03_recovery.py` không tồn tại; không chạy ca nào, không ghi là GREEN.
- expanded-03: 120 pass (W-17 + architecture + W-04 + W-03 PG/HTTP).
- 11 mutation: đều bị bắt bằng assertion, 0 setup error. Bao gồm bỏ revoke, bỏ guard cuối, bỏ admin lock, bỏ atomic, bỏ authorize, bỏ kiểm Actor live, lộ meta, bỏ DTO, sai biên tháng, sai biên since, bỏ account/email lock với login. Mỗi file được phục hồi byte/SHA sau mutation; kết quả ở `mutations.json` và log/JUnit riêng.
- focused-final: 53 pass = 48 W-17 + 5 architecture.
- Cổng full PG: **3481 pass, 3 skip, 1 xfail**, native 0, 703.48 giây wrapper. Hai skip đánh giá graph cần DANHGIA_KHO_CHUNG, một skip Cloudinary thật; xfail SA-66 bản ghi answer-2 cũ cần ghi lại bằng lượt trả phí. Không bật các điều kiện chạy ngoài phạm vi. Tên/lý do giữ nguyên ở summary.json/JUnit. React **229 pass/18 file**, native 0, 119.16 giây; build native 0, 3.21 giây. Cả ba cùng HEAD `8a8a46cb1e7eef2c95daddbe6cc36192b5aeff20` và chạy tuần tự, không đổi mã giữa cổng.

Fixtures: helper copy_w06_fixtures sao chép thường danh sách sáu cuốn phát triển, không link hoặc import learner store. PDF train candidate cần cho hồi quy toàn repo được copy riêng vào tmp, SHA đối chiếu độc lập theo candidate hiện hành; không commit PDF/artifact/.env. Chỉ dùng fixture cho test có sẵn, không chạy W-15 paid/operator.

Lệnh cổng từ gốc worktree (native command/cwd/SHA/giây trong từng `runs/*-exit.json`):

```text
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py -o addopts= -q --basetemp=tmp/w17-full-01 --junitxml=report/w17-evidence/runs/full-01.xml
npm.cmd --prefix src/web/frontend test -- --pool=threads --maxWorkers=1
npm.cmd --prefix src/web/frontend run build
```

`npm ci` lần đầu đã cài 229 package, audit 0 vulnerability; không đổi lockfile. Trước mỗi cổng kiểm runner toàn repo không có cổng khác; PG, React, build chạy tuần tự. Đã tự soát correctness/security/architecture/privacy/performance trong `w17-evidence/review.md`; đây chưa phải nghiệm thu điều phối.

Hỗ trợ tái hiện ở `w17-evidence/reproduce/`: capture qua runner, mutant có phục hồi byte, copy fixture và OpenAPI sinh từ app. Nếu chạy lại phải dùng nhãn/basetemp mới; để chạy script mutation mẫu, chép hai helper capture/mutations về `tmp` của worktree riêng trước, không chạy chồng cổng. Bản nguồn trước/sau theo từng lần có SHA trong native metadata; không tái chạy mutant trên nhánh đã ghép. Manifest ghi SHA bản text bàn giao và raw SHA; native bytes gốc được giữ ở local ignored `tmp/w17-raw-evidence`. Chỉ chuẩn hoá LF/ANSI/khoảng trắng cuối dòng khi đóng gói, không thay kết quả hay làm xanh lỗi cũ.

Công cụ đóng gói ghi đủ tệp/manifest rồi gặp UnicodeEncodeError của console cp1252 ở lệnh print cuối (native 1, không phải cổng test/build). Lệnh kiểm độc lập với Python `-X utf8` sau đó native 0, xác nhận toàn bộ 231 hash đầu tiên khớp. Chi tiết giữ ở `packaging-note.json`; không chạy lại hoặc ghi đè kết quả cổng. Các export W06/W14 và SQL fake W15/W25 ngoài phạm vi được giữ nguyên tại worktree, liệt kê trong `retained-test-exports.json`, không đưa vào commit.

## Ghi chú còn mở và bàn giao

- W-12 tùy chọn: token/email có thể đã commit khi callback sau verify lỗi, khiến HTTP báo thất bại dù dữ liệu xác minh đã bền vững. `list_my_invitations` hiện tự sửa liên kết. Đây là cải thiện vận hành chưa giao bắt buộc, không phải lỗi cấp quyền chặn W-12; mốc này không sửa hook.
- Sau mốc này chỉ đề xuất W-17.2 bản dựng/khoá mẫu, rồi W-17.3 chi/log lecture_validation/Cloudinary cache 1 giờ. Chưa triển khai, chưa đánh dấu toàn W-17 hoàn tất.
- Khi làm chi sau này: receipt build chỉ cộng một lần, loại trace counted_in=build; giữ unknown/billing_verified và nhãn “ước theo token, không thay hoá đơn”. Unknown W-15 0,4139008 USD giữ riêng, không quy thành 0/hóa đơn. Đề xuất build 5 USD/ngày và 3 lượt có chi/người/tháng chưa bật, không là quyền chi mới.
- Chưa ghép/push main hoặc dọn worktree/dữ liệu. Điều phối nghiệm thu mốc backend và giao React; yêu cầu cổng/main trước ghép theo quy trình hiện hành.
