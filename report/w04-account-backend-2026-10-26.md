# W-04 — Mốc backend tài khoản, 2026-10-26

## Phạm vi và nền

Nhánh `work/w04-account-backend`, worktree `tmp/w04-account-backend`, tạo từ main local
`8c7aab42b216ecbdc63bcc91ccbc4861df111024`, đã chứa mốc W-16 nhận tại `c5b4f5f`.
Nguồn: vé W-04, spec chức năng mục 2/10/11, nền W-02/W-03 và lời giao lần 7.
Thông tin phân công 2026-10-26 thay phân công web cũ: lõi làm backend; web giữ React/tích hợp.
Mốc này **không đóng toàn W-04**, không có trang hồ sơ hoặc bằng chứng giao diện React mới.

Chỉ sửa AccountService, port/repository tài khoản, fake repository, route/DTO auth, test W-04,
OpenAPI sinh từ app và báo cáo/bằng chứng W-04. Schema hiện hành đủ account/auth_session/audit_event;
không migration, không sửa app/gateway/content/learning_runtime/React hoặc `src/doc2roadmap/`.
Giữ nguyên W-16, callback cache/retry core, cấu hình transport/giá/trần và mọi dữ liệu W-15.

## Hợp đồng cho web

Mọi đường dẫn dưới `/api/v1`. Các route mới đều qua Origin/CSRF middleware hiện hành,
cookie phiên phía máy chủ; không có đường miễn CSRF mới. Phản hồi thành công `Cache-Control: no-store`.

| Route | Body | HTTP 200 |
|---|---|---|
| PATCH `/me` | `{"display_name":"  An  "}` | IdentityResponse như GET `/me`, tên thành `An` |
| POST `/me/password` | `current_password`, `new_password` | `{"message":"Đã đổi mật khẩu. Các phiên đăng nhập khác đã được đăng xuất."}` |
| POST `/auth/logout-all` | không body, `null` hoặc `{}` | `{"message":"Đã đăng xuất khỏi mọi thiết bị."}` và xóa cookie |

PATCH cắt khoảng trắng hai đầu **trước** kiểm 1–60 ký tự; 60 ký tự kèm khoảng trắng ngoài hợp lệ.
DTO cấm mọi khóa ngoài hợp đồng, gồm role/email/owner/account_id/session_id. Dịch vụ cũng kiểm tên
và luật mật khẩu W-02: 8–128 ký tự, từ chối danh sách phổ biến, dùng Argon2id hiện hành.
Không yêu cầu email đã xác minh cho các thao tác này.

| Lỗi | Status | fields/ý nghĩa |
|---|---|---|
| `validation` | 422 | tên rỗng/61: `body.display_name`; payload thừa: `body.<khóa>` |
| `validation` | 422 | độ dài mật khẩu mới: `body.new_password`; danh sách phổ biến: `new_password` |
| `invalid_credentials` | 401 | mật khẩu hiện tại sai, cùng thông báo chung W-02; không đổi hash/phiên/audit |
| `csrf_failed` | 403 | Origin thiếu/null/ngoài allowlist hoặc CSRF thiếu/khác phiên; kiểm trước body |
| `unauthenticated` | 401 | cookie hết hạn/bị hủy; GET `/me` và mutation gửi lại cookie đã hủy |
| `account_disabled` | 403 | tài khoản bị khóa; giữ quy tắc hủy phiên W-02 |

Khách thiếu cookie/CSRF ở mutation nhận 403 `csrf_failed` theo W-02, GET `/me` nhận 401.
JSON mẫu xuất từ HTTP/PG trong thư mục từng lượt GREEN; token CSRF fixture được che có ghi chú,
không đưa mật khẩu/hash/token phiên/token reset vào public fixture. Không thay error handler chung
để đồng nhất hai loại `fields.loc` đã có (Pydantic và service).

Bản giao web cuối: [PATCH me](w04-evidence/public/profile.json),
[đổi mật khẩu](w04-evidence/public/password-changed.json),
[logout-all](w04-evidence/public/logout-all.json),
[validation tên](w04-evidence/public/profile-validation.json),
[sai mật khẩu hiện tại](w04-evidence/public/wrong-current-password.json),
[mật khẩu phổ biến](w04-evidence/public/new-password-validation.json),
[audit đổi mật khẩu](w04-evidence/public/password_changed-audit.json),
[audit logout-all](w04-evidence/public/logout_all-audit.json).

Đổi mật khẩu giữ **đúng cookie A** đã xác thực; không nhận ID phiên/tài khoản từ body.
Hủy B và mọi phiên khác của chính tài khoản A, giữ nguyên phiên người khác.
Logout-all hủy cả A+B; xóa cookie với Path=/, HttpOnly, SameSite=Lax và Secure khi HTTPS/prod,
không Domain. Đặt lại mật khẩu W-03 tiếp tục hủy **tất cả**, khác đổi mật khẩu.

Audit `password_changed` và `logout_all`: actor_id=target_id=tài khoản từ phiên,
target_kind=`account`, thời gian từ clock, IP theo helper hiện hành, meta rỗng.
Đổi hash/hủy phiên/audit cùng transaction; lỗi audit rollback cả hash và thu hồi phiên trên PG.

## Vì sao cách triển khai này

Dùng lại `me` để xác thực cookie; sau khi lấy khóa account ID/email normalized/session,
đọc lại phiên và tài khoản trong transaction. Cách này ngăn identity vừa được xác thực nhưng
đã bị reset/logout/khóa/hết hạn trước lúc ghi. Các khóa account dùng cùng cơ chế advisory hiện hành
với login/reset; không đưa đối tượng HTTP hoặc thư viện PG vào tầng application.

Repository thêm update tên và tùy chọn loại trừ một session ID khi hủy phiên. Mặc định vẫn hủy hết,
nên reset/disabled giữ nghĩa cũ. Query luôn giới hạn account_id; không có danh sách thiết bị hoặc
thay đổi email/quyền. Không sao chép password hashing/session/CSRF thành cơ chế khác.

OpenAPI được tái sinh bằng `write_openapi(create_app(...))`, không sửa JSON tay;
giữ đủ **44 operation cũ**, thêm đúng **3 operation**, tổng 47. Có kiểm snapshot bằng app thật.
Nếu main nhận route W-10 sau mốc này, phải merge main rồi sinh lại từ app kết hợp.

## Kiểm chứng có thể chạy lại

Test: `src/web/backend/tests/test_w04_accounts.py`, fake clock + Argon2id thật,
chạy cùng assertion trên FakeAuthStore và PostgresAuthStore; hai client A/B có cookie độc lập
cùng tài khoản và client tài khoản khác. Mailer/model/media giả, chặn SMTP/Cloudinary/ADC/provider.

| Bất biến | Assertion runnable |
|---|---|
| trim, 1/60 hợp lệ, lưu qua PG, B đọc được, người khác giữ nguyên | `test_profile_trim_boundaries_persist_and_preserve_identity` |
| rỗng/61 có fields, không ghi | `test_profile_validation_fields_without_mutation` |
| không nâng quyền/email/owner | `test_profile_rejects_mass_assignment` |
| sai mật khẩu cũ không đổi hash/phiên/audit | `test_wrong_current_password_leaves_hash_sessions_and_audit_unchanged` |
| W-02 password policy | `test_new_password_uses_w02_policy_without_mutation` |
| A giữ, B không replay được, hash/đăng nhập/audit đúng | `test_change_keeps_a_revokes_b_checks_hash_login_and_audit` |
| không tin ID phiên/owner body | `test_session_owner_body_forgery_rejected` |
| logout-all hủy A+B, không hủy người khác, cookie đúng | `test_logout_all_revokes_a_b_preserves_other_and_cookie_security` |
| Origin/CSRF/guest/disabled | `test_csrf_origin_guest_disabled_and_cross_session_guards` |
| kiểm service và phiên bị hủy giữa đọc/ghi | `test_service_methods_validate_without_http_and_reject_stale_session` |
| DTO lọc private fields thật | `test_profile_uses_public_response_dto` |
| rollback hash/thu hồi/audit cùng nhau | `test_pg_password_hash_revocation_and_audit_commit_atomically` |
| reset W-03 vẫn hủy A+B, mật khẩu mới đăng nhập được | `test_w03_reset_still_revokes_all_including_a` |

Lượt `red-01` giữ nguyên: Docker engine/db-test chưa chạy, **21 PG setup errors**, không tính là RED PG.
Đã khởi động Docker Desktop và đúng service db-test từ compose hiện hành, không tạo lại volume hay xóa DB.
`red-02`: **34 fail / 8 pass / 0 setup error** trên source cũ (32 assertion HTTP + 2 phương thức chưa có).
`profile-green-01` có 6 assertion dùng sai `fields.loc`; sửa test theo định dạng W-02 hiện hành,
giữ log gốc. `profile-green-02`: **16 pass**. `password-green-01`: **14 pass**.
`regression-green-01`: **112 pass** gồm W-02/W-03/password/architecture.
Thêm kiểm stale cho cả ba thao tác, DTO và rollback: `adversarial-green-01`: **49 pass** W-04.

Mutation trên chính source sản phẩm, lưu patch/harness/lệnh/native/XML và phục hồi nguyên byte.
Hai lần đầu parser harness chưa nhận đủ dạng assertion của JUnit; lần 3 bắt 8 mutant rồi dừng
trước mutant tên do pattern trùng validation đăng ký. Giữ đủ log; lần 4 chỉ kiểm hai ca còn lại,
không tính lỗi harness thành lỗi sản phẩm hoặc giảm assertion nghiệp vụ.
Kết quả cuối, commit source và các cổng được ghi tiếp sau khi hoàn tất bên dưới.

## Chi phí và dữ liệu

Toàn mốc **0 USD**. Fixture ledger/bản dựng trong cổng toàn repo là dữ liệu test, không phải chi thật.
Fixture sáu sách chép bằng helper allowlist/SHA, không link hoặc chép learner store.
PDF candidate train chép riêng theo SHA chỉ để test fake/dry-run sẵn có trong cổng toàn repo;
không chạy lại operator W-15, không replay trả phí, không nhận DB/cache/run riêng vào kho chung.
Không commit PDF/artifact/.env. Giá demo vẫn `billing_verified=false`; unknown W-15
`0.4139008 USD` giữ riêng, không ghi 0 hoặc hóa đơn thật. Đề xuất build 5 USD/ngày và
3 lượt có chi/người/tháng chưa bật và không là quyền chi mới.

Giữ output test ngoài W-04 tại worktree, chỉ sao chép bằng chứng cần giao vào thư mục W-04;
không restore/stash/reset/xóa dữ liệu hoặc commit output ngoài phạm vi.
Chỉ chủ dự án/điều phối nghiệm thu và ghép; không gửi message phiên khác, không tự merge/push main.


## Kết quả cổng cuối và bàn giao

Commit mã **`b8cb7de1edef899a38fb2df4215bbc2dd177cce4`** trên main đã nhận `8c7aab42b216ecbdc63bcc91ccbc4861df111024`. PG toàn repo: **2808 pass**, 2 skip/xfail có sẵn; React **203 pass**; build native **0**. Ba cổng chạy tuần tự trên cùng source/HEAD; native, lệnh, cwd, số giây và source SHA trong `w04-evidence/runs/`.

Sau phục hồi mutation, **119 test hồi quy đạt**, gồm **49 ca W-04**. **10/10 mutant bị bắt bằng assertion**, không setup error trong các lượt được tính. Tự review correctness/readability/architecture/security/performance không còn phát hiện chặn; đây là tự kiểm, vẫn chờ điều phối soát độc lập.

[JSON public/audit cho web](w04-evidence/public/metadata.json), [summary](w04-evidence/summary.json), [manifest SHA](w04-evidence/manifest.json). CSRF fixture được che; tên/email/UUID còn lại là dữ liệu tổng hợp, không phải dữ liệu người dùng thật. Không đổi cấu hình demo, không gọi nhà cung cấp/SMTP/Cloudinary/ADC thật; **0 USD**.

Worktree còn output phát sinh của cổng cũ ngoài W-04, được liệt kê trong `retained-test-exports.json`; giữ nguyên và không nằm trong commit bàn giao. **Backend W-04 sẵn sàng soát; toàn W-04 còn React/tích hợp của web. Chưa ghép/push main.**

Bản commit log/XML dùng UTF-8/LF và bỏ khoảng trắng/tab cuối dòng vật lý để đạt `git diff --check`; raw gốc giữ nguyên trong ignored `tmp/w04-raw-evidence/`, `manifest.json` ghi cả raw_sha256 và sha256 bản commit. Không đổi JSON values, JUnit attributes, số test hoặc native; có helper normalize kèm provenance.
