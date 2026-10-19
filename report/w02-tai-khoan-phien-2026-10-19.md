# W-02 — Tài khoản và phiên cookie

**Trạng thái:** done-local, sẵn sàng chủ dự án/người điều phối nghiệm thu. **Nhánh:** work/w02-accounts. **Chi phí mô hình:** 0 USD.

## Phạm vi bàn giao

- Account/Actor và luật W-02; AccountService đăng ký, đăng nhập, đăng xuất, lấy phiên; AuthStore giả và PostgreSQL.
- Bốn endpoint /api/v1/auth/register, /auth/login, /auth/logout, /me; cookie HttpOnly/SameSite=Lax, Secure khi HTTPS và luôn Secure ở prod; chỉ lưu SHA-256 token 32 byte; CSRF riêng từng phiên.
- Phiên hết sau 7 ngày không dùng hoặc 30 ngày tuyệt đối; chỉ ghi last_seen khi cũ hơn 5 phút. Tài khoản khoá bị từ chối và thu hồi mọi phiên.
- Argon2id 19 MiB / 2 vòng / parallelism 1, salt ngẫu nhiên; mật khẩu 8–128 ký tự, giữ khoảng trắng, danh sách 10.001 mục phổ biến đóng kèm. Danh sách và giấy phép đọc được từ wheel, không cần mạng lúc chạy.
- Giới hạn 5 lần sai/email và 20 lần sai/IP trong 15 phút. Kiểm, băm và ghi sự kiện nằm trong một giao dịch có advisory lock SHA-256 ổn định; nhiều kết nối dùng chung giới hạn. Lỗi đăng nhập không làm rollback bộ đếm.
- Origin kiểm trước body; mặc định chỉ cùng nguồn localhost/IP loopback. Tên miền thật cần allowed_origins chính xác. Ngoài POST đăng ký/đăng nhập, mọi phương thức thay đổi dữ liệu cần CSRF khớp phiên. Không tin header forwarding do ứng dụng tự đọc.
- CLI create-admin hỏi mật khẩu ẩn qua stdin, không có tham số password và không cần Vertex. Nhật ký không lưu email/mật khẩu/token thô.
- React có đăng ký/đăng nhập, trường lỗi và focus, giới hạn thử bằng giây/phút, phiên qua tải lại, menu tên/đăng xuất và trang tài khoản thực. Đăng xuất đi một luồng về đăng nhập, đã bỏ hai lệnh điều hướng cạnh tranh. /demo giữ dữ liệu mẫu.

## Tích hợp W-05 và di trú

Đã ghép đúng commit bàn giao W-05 **8b920d626872986befd47b66710661dc5a332352** qua merge b918209; giữ cả kho Pha B và dịch vụ tài khoản trong composition. Những thay đổi src/doc2roadmap là của nhánh W-05, không phải mở rộng phạm vi W-02.

Chuỗi duy nhất: **w01_0001 → w05_0002 → w02_0003**. W-02 tạo account, auth_session, rate_limit_event, audit_event; migration đóng băng schema, không import metadata có thể đổi ở tương lai. Test W-01 vẫn kiểm revision nền; test head kiểm đủ bảng, chỉ mục/ràng buộc và khớp metadata runtime. Đã upgrade PostgreSQL local, khởi động lại API tại http://127.0.0.1:8000, health/db tốt và trang đăng nhập trả 200.

## Quyết định đã chốt

- Chủ dự án chọn giữ tự đăng nhập sau đăng ký mới. Email trùng sau chuẩn hoá trả cùng HTTP 200 và cùng JSON, không cấp phiên mới hay sửa tài khoản cũ. Khác biệt cookie và /me vẫn cho phép suy ra email đã tồn tại: giới hạn riêng tư được chủ dự án chấp nhận; không tuyên bố chống dò email hoàn toàn. Quyết định đã bổ sung vào spec chức năng và vé.
- Tài khoản disabled: yêu cầu hợp lệ đầu tiên phát hiện khoá trả account_disabled và xoá mọi phiên; cookie đã thu hồi sau đó trả unauthenticated. Mở khoá không phục hồi phiên cũ.
- Quản trị viên CLI là đường bootstrap tin cậy, email được coi đã xác minh; không tự cấp phiên. HTTP đăng ký không nhận role/status/email_verified.
- Không gửi thư trong W-02. W-03 làm xác minh/reset; W-04 làm hồ sơ. Chưa mở W-06, W-15 hay W-23.

## Kết quả kiểm cuối

| Phép kiểm | Kết quả | Bằng chứng |
|---|---|---|
| Toàn bộ lõi và web, PostgreSQL bắt buộc | **2.062 đạt, 1 bỏ qua, 0 lỗi**, exit 0; 345,45 giây | [XML](w02-evidence/full-regression.xml), [tóm tắt](w02-evidence/regression-summary.json) |
| Backend trong vòng trên | **150 đạt**, 1 Cloudinary live bỏ qua theo cờ bật riêng | XML và tóm tắt ở trên |
| React | **29/29 đạt**, build production đạt | [XML React](w02-evidence/frontend-final.xml) |
| Trình duyệt, composition thật và Alembic đầy đủ, database thử tự xoá | **12 màn**, 9 assertion luồng; không tràn ngang, ảnh vỡ, lỗi axe hoặc lỗi console ứng dụng | [JSON browser](w02-evidence/browser-audit.json) |
| Wheel | Đủ blocklist/giấy phép/migration; đọc đủ 10.001 mục từ wheel | [JSON package](w02-evidence/package-check.json) |
| Hợp đồng API | Snapshot OpenAPI khớp; ví dụ thật bốn endpoint | [JSON ví dụ](w02-evidence/api-examples.json), src/web/openapi.json |

Cloudinary live được bật riêng và không chạy lại trong vòng W-02; W-01 đã kiểm thật. Không gửi thư, không sinh nội dung trả phí. Có 8 cảnh báo thư viện/Starlette hiện hữu; không hạ hay bỏ test để xử lý cảnh báo.

Một vòng hồi quy trước có 2.060 đạt, 1 lỗi: Windows WinError 5 tại os.replace của kho JSON lõi trong test_assistant_sessions_share_learner_reservation_before_streaming[json]. File liên quan chạy riêng lại 18/18; vòng toàn bộ với thư mục tạm mới đạt như trên. Không sửa nguồn kho JSON, thêm retry hay nới assertion để che lỗi; hiện tượng chưa tái hiện và vẫn được lưu trong tóm tắt.

## Invariant → assertion chạy được

| Invariant | Tên test |
|---|---|
| Chuẩn hoá email; trùng không chiếm tài khoản; JSON/status giống nhau | test_registration_duplicate_same_body_no_account_takeover |
| Argon2id, salt, không lưu token/mật khẩu thô trên PostgreSQL | test_password_hash_is_argon2id_with_owasp_minimum_and_random_salt; test_real_postgres_http_stores_no_raw_credentials_and_revokes_disabled_account |
| Lỗi known/unknown như nhau, lần thứ sáu bị chặn | test_known_unknown_login_errors_match_and_sixth_failure_is_throttled |
| Nhiều kết nối cùng chịu email/IP limit | test_shared_email_limit_holds_across_store_instances_and_connections; test_shared_ip_limit_holds_across_many_connections |
| Hết hạn và khoá không phục hồi phiên | test_disabled_session_is_revoked_on_first_request_and_cannot_return_if_reenabled; test_real_postgres_http_stores_no_raw_credentials_and_revokes_disabled_account |
| Liệt kê mọi route unsafe, kể cả route mới; Origin/CSRF fail closed | test_all_unsafe_routes_fail_closed_including_new_future_route; test_empty_origin_config_only_trusts_local_development_hosts |
| Cookie và proxy HTTPS | test_cookie_security_and_logout_revokes_old_cookie; test_production_cookie_is_secure_even_behind_http_upstream |
| Admin thật, không Vertex hay mật khẩu trên argv | test_create_admin_bootstraps_real_postgres_without_vertex; các test CLI trong test_web_cli.py |
| Một head nối W-05 và schema từ rỗng | test_w02_head_migrates_from_empty_and_follows_w05; test_w02_migration_schema_matches_runtime_metadata |

Đã thấy đỏ trước khi module/route/migration tồn tại; test bổ sung Origin/cookie thấy đỏ trên mã cũ trước khi sửa. Bộ mutation chạy cô lập bắt được bỏ dummy verify, bỏ idle expiry, không xoá phiên disabled, bỏ email throttle và tháo global CSRF. Schema guard từng bắt token hash ngắn/thiếu ràng buộc. Không sửa nguồn chính để chạy mutation.

## Giao diện và taste

Áp dụng design-taste-frontend theo app-screen, frontend-ui-engineering và tài liệu thiết kế WayFinder; giữ palette thương hiệu và Be Vietnam Pro. Hướng tham chiếu editorial-greeting được thu gọn cho biểu mẫu tài khoản; seed picker ban đầu không được lưu, không dựng lại giả lịch sử.

- App lint Auth.tsx: 0 FAIL, 2 WARN. App inspector trang đăng nhập: 0 FAIL, 3 WARN; cả desktop/tablet/mobile được xem lại.
- Chấp nhận kicker vì mỗi màn chỉ có một dòng nhận diện theo bản vẽ thương hiệu; khoảng trống desktop giữ trọng tâm vào form; khoảng cách header 14 px dùng khung chung hiện có và các vùng bấm đã đạt 44 px. Các cảnh báo này không che lỗi contrast/overflow/tương tác.
- Root đã xem ảnh và sửa hai lỗi thật thấy đỏ: link vùng bấm 15–18 px và ảnh brand mark không tồn tại. Guard trình duyệt hiện kiểm ảnh complete/naturalWidth và target 44 px.
- Ảnh hai trang đủ 390/768/1280 ở sáng/tối trong w02-evidence; thêm ảnh validation, invalid credentials, rate limit, đăng ký trùng và tài khoản.
- Thêm probe dữ liệu biên với tên 60 ký tự liền và email 254 ký tự: đã thấy đỏ do tràn ở 390 px, sửa minmax/overflow-wrap trong trang tài khoản; 390/1280 px đều đạt. Phản hồi /me của probe được mô phỏng rõ ràng, không tạo tài khoản local. [Kết quả](w02-evidence/long-account-audit.json), script scripts/w02_long_account_check.cjs.
- Không có Chrome DevTools MCP trong phiên; dùng Chromium/Playwright với profile riêng. 24 chẩn đoán CSP do axe chèn style được tách toolDiagnostics; HTTP 401/429 chủ ý khi thử lỗi nằm trong expectedHttpDiagnostics. Giữ CSP, không tắt chính sách để chạy kiểm.

## Tái chạy

Từ gốc repo, dùng src/web/.env phía server và db-test đang chạy:

~~~powershell
.venv/Scripts/web.exe --env-file src/web/.env check
npm.cmd --prefix src/web/frontend test -- --pool=threads --maxWorkers=1
npm.cmd --prefix src/web/frontend run build
~~~

Nếu Windows Temp/cache cũ lỗi quyền, dùng basetemp mới và -p no:cacheprovider theo README. Browser script scripts/w02_browser_check.cjs dùng W02_BASE_URL trỏ server test; tạo tài khoản example.vn và thử throttle, nên chạy trên database thử. Vòng nghiệm thu trên đã dùng composition/ADC thật và migration đầy đủ trong database UUID riêng, rồi dừng server 8002/xoá database. Giữ API local 8000 đang chạy cho chủ dự án.

Nguồn: [OWASP Password Storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html), [Argon2-cffi API](https://argon2-cffi.readthedocs.io/en/stable/api.html), [SecLists](https://github.com/danielmiessler/SecLists); commit/SHA-256 và MIT license đóng kèm wayfinder/data.
