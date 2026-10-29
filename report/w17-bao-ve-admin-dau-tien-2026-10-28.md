# W-17.1 — POL-R10-01: bảo vệ định danh admin đầu tiên

## 1. Quyết định hiện hành và phạm vi

Chủ dự án nói nguyên văn: **“admin đầu tiên ko đc khóa hay gì”**. ADR 0030 và phân công lần 10 đã chốt: bảo vệ tài khoản bootstrap đầu tiên khỏi disable, demote và delete, kể cả tự thao tác hoặc admin khác thao tác. Đây là điều kiện bắt buộc thay hợp đồng cũ, không còn là Optional.

Nhánh `work/w17-admin-users-backend`, worktree `tmp/w17-admin-users-backend`. Mốc cũ `9cf405ac` chưa nhận/chưa ghép. Đã kiểm sửa dở và merge main local `26d43b83` (có W-04 React) bằng commit `851cf97c`; export test W06/W14/W15/W25 cũ được giữ nguyên. Thư mục chung vẫn main. Không sửa task/spec/handoff điều phối, React hoặc lõi `src/doc2roadmap`.

Mốc này chỉ sửa backend W-17.1, schema bootstrap và CLI đối chiếu DB hiện hữu. Không làm W-17.2/W-17.3, không gửi thư thật hoặc chạy nhà cung cấp. Chi mới 0 USD; bảo toàn dữ liệu W-15 và unknown cũ.

## 2. Định danh bền vững và giao dịch bootstrap

Migration duy nhất `w17_0009` nối **`w12_0008`**; không sửa migration đã ghép. Bảng `bootstrap_admin` có đúng tối đa một hàng: `singleton boolean PRIMARY KEY CHECK(singleton)`, `account_id uuid UNIQUE NOT NULL REFERENCES account ON DELETE RESTRICT`, `established_at timestamptz NOT NULL`. Đây là registry định danh, không thêm role hoặc IAM mới.

`AccountService.create_admin` giữ lock `admin:users` và account/email hiện hành. Nếu chưa có registry và chưa có admin, tạo tài khoản admin + registry + audit cùng transaction. Hai runtime bootstrap cạnh tranh chỉ ghi đúng một UUID; những admin thêm sau không đổi hàng này. Nếu đã có admin mà chưa có registry, không tự chọn admin mới làm người đầu tiên: trả `bootstrap_required`, rollback.

Registry immutable: trigger DB chặn update/delete hàng đã lập; trigger insert chỉ nhận UUID của account admin active và giữ row lock khi xác lập. Trigger trên account chặn disable/demote/đổi ID/xoá tài khoản được bảo vệ. Các thao tác hồ sơ/mật khẩu, last_seen, logout/session, Origin/CSRF và đăng nhập W-02/W-03 vẫn theo hành vi bình thường.

Service PATCH kiểm định danh sau khi lấy lock, trước bất kỳ update/session-delete/audit nào. PATCH nhiều field có status disabled hoặc role user cho người đầu tiên bị từ chối toàn bộ; quota kèm theo cũng không đổi. Không ghi audit thành công giả. Admin thêm sau và người thường vẫn được quản trị theo spec. Guard admin cuối riêng đếm role admin **và status active**, không lấy admin disabled thay cho admin hoạt động.

## 3. DB hiện hữu: chưa tự áp dụng

Không chạy migration/gán UUID trên DB web dùng chung. Toàn bộ thao tác thực thi trong lượt này chỉ trên database kiểm thử tách riêng qua runner PostgreSQL.

Migration tạo bảng rỗng cho DB hiện hữu, không đoán UUID từ role/status hiện hành, thứ tự list, created_at hoặc một user thường tạo sớm. Khi chưa lập registry, DTO `is_first_admin=null`; service từ chối PATCH disable/demote và DB từ chối xóa hoặc hạ/khóa admin với `bootstrap_required`. Profile/password/login và các truy vấn không phá quyền vẫn hoạt động. Tạo thêm admin cũng bị từ chối cho đến khi đối chiếu xong.

Kế hoạch operator trước khi dùng bản sửa với DB hiện hữu:

1. Sao lưu DB và đối chiếu hồ sơ bootstrap/admin_account_created, log vận hành hoặc backup đáng tin cậy để xác định đúng UUID người đầu tiên. Không dùng “hàng đầu bảng” hay email client gửi. Nếu hồ sơ không đủ, dừng và xin chủ dự án xác nhận UUID; không tự chọn theo cách thuận lợi.
2. Sau khi bản sửa/schema được nghiệm thu và trong cửa vận hành được chủ dự án giao, áp dụng migration `w17_0009` vào đúng DB. Lượt này chưa thực hiện bước đó.
3. Operator máy chủ dùng CLI `protect-first-admin --account-id <UUID đã đối chiếu>` với cấu hình DB máy chủ hiện hành. Không có API nhận tham số này từ trình duyệt. Phương thức tin cậy `assign_first_admin` yêu cầu account admin active, chỉ gán một lần, audit `bootstrap_admin_assigned` actor null cùng transaction; lặp đúng UUID không ghi trùng, đổi UUID bị từ chối.
4. Kiểm SQL độc lập đúng một hàng registry và UUID; login/PATCH lỗi/DTO của chính tài khoản đó. Nếu tài khoản bootstrap cũ đã mất quyền/bị xóa trước migration, CLI không tự phục hồi hoặc gán tài khoản thay thế; phải có quyết định phục hồi riêng. Không đụng DB/artifact W-15.

Quyền SQL owner/superuser có thể thay trigger/schema hoặc TRUNCATE; CLI/DB vận hành là ranh giới tin cậy, không phải IAM mới. Không cung cấp đường HTTP bypass hay quyền SQL cho người dùng.

## 4. Lỗi và DTO cho React

Không thêm endpoint quản trị mới ngoài ba route W-17.1. PATCH vẫn chỉ nhận status/role/build_monthly_max; mọi field định danh bảo vệ do client thêm bị validation/fields 422. Mọi response admin no-store.

| HTTP/code | Ý nghĩa | fields |
|---|---|---|
| 409 `protected_admin` | Không cho khóa/hạ quyền người đầu tiên | loc status và/hoặc role thực sự bị cấm |
| 409 `bootstrap_required` | DB hiện hữu chưa xác lập UUID; từ chối thao tác nguy hiểm | loc status/role của PATCH |
| 409 `conflict` | Guard admin active cuối (phòng thủ riêng) | Hợp đồng hiện hành |
| 422 `validation` | Field không đúng/ngoài DTO | Hợp đồng hiện hành |
| 401/403 | Phiên, Actor live, disabled, role, Origin/CSRF | Giữ W-02/W-03 |

`AdminUserResponse` thêm `is_first_admin: bool|null`: true/false khi registry đã lập, null nếu chưa được đối chiếu. React dựa trường này để phản ánh trạng thái, server vẫn quyết định cuối. Email, ngày tạo/login, course count, build month counts/null override giữ hợp đồng trước. Không trả registry raw, hash/password/token, audit.meta hoặc dữ liệu học riêng. OpenAPI sinh từ app hợp nhất; giữ 63 operation và khai báo schema lỗi 409 của PATCH.

`DELETE /me` và `DELETE /admin/users/{uid}` **chưa tồn tại** (W-20 chưa triển khai); request hiện nhận 405 và không thay dữ liệu. Không dựng endpoint xóa tạm. Xóa protected account qua SQL/repository bị trigger/FK từ chối, đảm bảo đường xóa triển khai sau không thể commit vi phạm. W-20 cần nối lỗi public phù hợp và giữ thủ tục bảo toàn học/ledger theo vé, không coi W-20 đã xong.

## 5. RED→GREEN và mutation

Lịch sử báo cáo cũ `w17-admin-users-backend-2026-10-27.md` và toàn evidence giữ nguyên ý nghĩa hợp đồng trước. Ca “cho phép disable admin cuối” đã được thay bằng expected từ chối theo quyết định mới; không skip/xóa guard. Review cũ 23 probe/6 mutant xanh không chứng minh chính sách mới; addendum POL-R10-01 là nguồn nghiệm thu hiện hành.

- `policy-red-01`: setup error vì Docker/db-test đang tắt; giữ log, không tính assertion RED.
- Khởi động Docker Desktop và **db-test đã có**, không migration DB dùng chung.
- `policy-red-02`: assertion fail/0 setup error trên source `851cf97c` chưa sửa policy. PATCH 200, status disabled và quota 7 chứng minh hành vi sai mới; SQL không phải cờ tự gán.
- `policy-green-01`: 21 pass gồm owner policy + account regression.
- `policy-expanded-01`: 79 pass, một fail ở danh mục bảng AuthStore chưa tính bảng mới. Sửa assertion để giữ đủ các bảng cũ và thêm bootstrap_admin; không bỏ kiểm schema.
- `policy-expanded-02`: **147 pass**, native 0; gồm chính sách mới, W-17 cũ đã cập nhật expected, AuthStore/metadata/migration, W-03 PG, W-04 và architecture.
- Mutation mới: **14/14 bị bắt bằng assertion, 0 setup error**, từng source được khôi phục đúng byte/SHA. Kiểm phá guard định danh service, bootstrap write/transaction/shared lock, legacy no-guess/transaction, trigger account/registry, active-admin count, revoke session, update transaction, stale Actor, DTO và account/email lock khi login cạnh tranh.
- Full PG: **3.600 pass, 3 skip, 1 xfail**, native 0. Hai skip đánh giá cần DANHGIA_KHO_CHUNG, một skip Cloudinary thật; xfail SA-66 bản ghi answer-2 cũ cần ghi lại trả phí. Không bật các điều kiện đó trong lượt 0 USD này. JUnit giữ tên/lý do cụ thể; không có ca W-17 bị skip.
- Cổng cuối trên `847cfe94be63f62e9a680cb409e414c19297d1ff`: **3600 Python pass**, 4 skip/xfail (tên/lý do giữ ở summary/JUnit), native 0, 938.52s wrapper; **239 React pass/19 file**, native 0, 144.70s; build native 0, 3.69s. Toàn bộ **71 ca W-17** đã chạy và đạt. Evidence mới không ghi đè hồ sơ W-17 cũ.

Kiểm bắt buộc: self/other-admin, hai admin, PATCH nhiều field, thêm admin/người thường cũ được nâng, reload runtime độc lập, registry immutable, delete SQL, bootstrap race, rollback create/assignment/audit/session, stale/disabled Actor, quota null/biên tháng Việt Nam, DTO/private marker. SQL assertions dùng connection độc lập; cookie HTTP và Argon2 thật; Mailer/model/embedding/media giả, chặn ADC/network.

| Bất biến mới/được giữ | Assertion chạy được |
|---|---|
| RED trước sửa; PATCH nhiều field không thay quota/phiên/audit | `test_new_owner_policy_first_admin_cannot_be_disabled`, `test_first_identity_protected_even_with_two_admins_and_atomic_patch` |
| UUID qua restart, user thường có ngày tạo sớm được nâng không đổi UUID | `test_registry_survives_restart_and_older_learner_promotion_and_filtered_lists`, `test_legacy_upgrade_requires_explicit_uuid_without_guessing_and_atomic_assignment` |
| Client không ghi định danh; chỉ CLI nhận UUID máy chủ | `test_client_cannot_write_bootstrap_identity`, `test_local_cli_assigns_only_explicit_server_uuid` |
| SQL delete/disable/demote/đổi registry bị chặn; API xóa chưa có | `test_database_rejects_delete_and_bypass_of_protected_identity`, `test_no_delete_api_bypass_and_normal_accounts_still_deletable_by_repository_sql` |
| Cạnh tranh bootstrap/admin, đúng một định danh | `test_bootstrap_creation_race_persists_exactly_one_identity_and_audit`, `test_two_postgres_runtimes_keep_first_admin_while_demoting_later_admin` |
| Rollback bootstrap/audit/legacy assignment | `test_bootstrap_insert_and_audit_failure_roll_back_together`, `test_legacy_upgrade_requires_explicit_uuid_without_guessing_and_atomic_assignment` |
| Profile/password, CSRF, disabled/stale Actor | `test_profile_password_and_security_guards_remain_available_for_first_admin`, `test_disabled_actor_and_disabled_admin_not_counted_as_active`, `test_stale_admin_actor_and_unauthorized_patch_cannot_write` |
| Hai cookie, login race, rollback ordinary-account update/session | `test_disable_revokes_two_cookies_enable_never_resurrects`, `test_inflight_login_cannot_leave_a_session_after_disable`, `test_update_and_audit_rollback_on_audit_failure`, `test_update_rolls_back_if_session_delete_fails` |
| Không dữ liệu riêng, DTO, quota/tháng | `test_private_learning_records_are_inaccessible_to_admin_and_absent_from_every_admin_response`, `test_real_response_dtos_strip_repository_extras_at_every_level`, `test_user_monthly_counts_match_existing_quota_at_vietnam_boundary`, `test_patch_quota_override_null_fallback_role_and_idempotent_audit` |

## 6. Cổng, nguồn và bàn giao

Nguồn sửa `847cfe94be63f62e9a680cb409e414c19297d1ff` (18 tệp source/test/OpenAPI, bao gồm một migration mới). Nhận main mới `26d43b83` có W-04 trước cổng; merge main lần kiểm cuối báo Already up to date. Đã tự soát trong `w17-first-admin-evidence/review.md`.

Cả ba cổng cuối đã đạt trên đúng HEAD `847cfe94be63f62e9a680cb409e414c19297d1ff`; nguồn không đổi giữa cổng. Cổng PG qua `scripts/w05_run_tests.py`, mỗi lần basetemp mới; một full PG toàn repo mỗi lúc, sau đó React single worker rồi build. Chưa ghép/push main, dọn worktree/export/artifact hoặc áp dụng DB dùng chung.

Lệnh native từ gốc worktree; metadata lưu command/cwd/HEAD/source SHA/native/giây, không lấy test editable của thư mục chung:

```text
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py -o addopts= -q --basetemp=tmp/w17-policy-full-01 --junitxml=report/w17-first-admin-evidence/runs/policy-full-01.xml
npm.cmd --prefix src/web/frontend test -- --pool=threads --maxWorkers=1
npm.cmd --prefix src/web/frontend run build
```

Đã ordinary-copy/đối chiếu SHA lại fixture sáu cuốn và PDF candidate riêng cho bộ hồi quy hiện hành, không nhập learner store hay artifact run W-15. `npm ci` native 0, audit 0 vulnerability, không đổi lockfile. File PDF/artifact/.env không commit. Chỉ điều phối ghép sau nghiệm thu; nếu main tiến trước ghép phải nhận và chạy cổng theo quy trình.

## 7. Giới hạn và các mốc còn mở

Toàn W-17 chưa đóng. React Người dùng/Nhật ký do web làm sau khi backend sửa được nhận; W-17.2 metadata bản dựng/khoá mẫu và W-17.3 chi/validation/Cloudinary chưa triển khai. W-12 callback sau commit xác minh vẫn chỉ là ghi chú vận hành tùy chọn, không sửa ở đây. Không nghiên cứu/chạy lại W-15, không đổi transport, cache, giá hoặc trần.

Chi ở mốc sau phải cộng receipt build đúng một lần, bỏ trace counted_in=build khỏi phép cộng, giữ unknown/billing_verified và nhãn **“ước theo token, không thay hoá đơn”**. Unknown W-15 0,4139008 USD giữ riêng; đề xuất build 5 USD/ngày và 3 lượt/người/tháng chưa bật/chưa là quyền chi.

## 8. Đề xuất hợp đồng mốc sau — chưa nối retry/cancel

W-17.2 sau khi bản sửa được nhận chỉ GET /admin/builds metadata phân trang/lọc giới hạn và PATCH /admin/courses/{cid} đánh dấu mẫu dev thuộc allowlist sáu cuốn; giữ policy/audit và không chạy provider.

Retry/cancel thay chủ khoá cần điều phối/Claude chốt riêng. Đề xuất một application command/port riêng kiểm Actor admin live, nhận build_id và ý định thao tác, tải target/ownership nội bộ, áp dụng lifecycle/grant/budget theo kết quả hợp đồng. Không giả Actor requested_by hoặc bỏ require_upload/requested_by trong BuildService chung. Bảng HTTP đang có POST /admin/builds/{id}/retry; admin cancel chưa được liệt kê, nên route POST /admin/builds/{id}/cancel chỉ là đề nghị cần bổ sung hợp đồng trước triển khai. Cần chốt trạng thái được retry/cancel, audit, idempotency/race, quyền spend và ai nhận receipt/mail. Lượt này không mở route/port thực thi hoặc xin quyền chi qua đề xuất này.

Lệnh/native/JUnit/SHA nằm trong `w17-first-admin-evidence/runs/`; JSON và schema cho React ở `public/`; bản raw trước chuẩn hoá text giữ tại ignored `tmp/w17-first-admin-raw-evidence`. Manifest ghi cả raw SHA và SHA bản bàn giao. Export W06/W14 và SQL fake W15/W25 ngoài phạm vi được giữ nguyên, liệt kê riêng; không commit vào bản sửa.

Đóng gói: `git add` ban đầu native 128 vì Filename too long ở một tên SQL proof. Khắc phục bằng `git -c core.longpaths=true add/commit` riêng cho lệnh, không sửa global config, không đổi tên/xóa evidence hoặc thay source/test. Chi tiết native và lệnh giữ trong packaging-note.json; manifest được kiểm lại trước commit.
