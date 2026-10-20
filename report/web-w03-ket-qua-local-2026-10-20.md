# W-03 — Kết quả triển khai và kiểm local, 2026-10-20

**Cập nhật sau khi doc-1 được dựng lại: W-03 đạt kiểm và soát nội bộ trên local; cổng toàn repo đã xanh (2.075 đạt, 1 Cloudinary live bỏ qua).** Xem [báo cáo nghiệm thu mới](web-w03-nghiem-thu-2026-10-20.md). Chưa ghép main; báo cáo trực tiếp chủ dự án theo yêu cầu. Các lượt thiếu fixture dưới đây được giữ làm lịch sử.

**Cập nhật logo/Gmail:** chủ dự án đã kiểm thư thật thành công. Đã thêm URL logo Cloudinary vào env, nối vào cả ba mẫu thư và khởi động lại local; cổng toàn repo sau sửa đạt 2.085/1 skip, xem [phụ lục](web-w03-logo-email-2026-10-20.md).

## Mốc mã và phạm vi

- Nhánh work/w03-email-recovery, worktree tmp/w03-email-recovery; mã nghiệp vụ: **89eefdb**; bản sửa header cuối được lưu cùng bản cập nhật báo cáo này. Các mốc trước: schema **33c70ac**, snapshot **fdd0620**, điểm nghỉ **3955af8**.
- Chỉ W-03 của web; không làm W-06. Không sửa vé, kế hoạch/handoff, mã lõi hay migration đã ở main. Migration của vé w03_0004 có down_revision=w02_0003.
- Main mới 88a6905 chỉ cập nhật quy trình và hồ sơ sự cố cache, không đổi mã sản phẩm.
- Nhánh còn mang các commit chưa soát từ trước: 781415b/79cb9c9/6cd6be7. Phần W-24 phải được phán xét riêng trước khi ghép; không tự coi các commit này đã đạt.

## Đã triển khai

- Xác minh email, gửi lại xác minh, yêu cầu/hoàn tất đặt lại mật khẩu; ba mẫu thư tiếng Việt có logo, Mailer console/fake/SMTP.
- Token ngẫu nhiên 32 byte, chỉ lưu SHA-256, dùng một lần và gắn email hiện tại; xác minh 24 giờ, reset 60 phút; giới hạn 3 yêu cầu mỗi giờ theo vé. Reset thu hồi mọi phiên và token reset còn lại.
- Ba POST verify/request/confirm công khai vẫn kiểm Origin trước body; resend cần phiên + CSRF + Origin. Không tháo guard toàn cục.
- SMTP gửi ngoài giao dịch DB qua queue giới hạn 32 tác vụ/2 thread, STARTTLS kiểm chứng chỉ và timeout adapter hữu hạn. Lỗi gửi/queue đầy giữ phản hồi chung, không log nội dung/token/credential.
- Khoá PostgreSQL chung cho login/reset và request/reset tránh phiên dùng mật khẩu cũ hoặc token chen vào trước commit reset. Kiểm token reset trước khi băm mật khẩu, rồi kiểm lại trong giao dịch.
- Logout dùng cùng chính sách cookie Secure của production như login/reset, kể cả khi ASGI thấy HTTP phía sau proxy TLS.
- UI banner, verify/forgot/reset: pending, thành công, hết hạn, đã dùng, thiếu mã. GET không tự tiêu thụ token; link thư mới dùng fragment rồi được xoá khỏi URL. Link mới trong cùng tab xoá trạng thái/toast cũ; response cũ không ghi đè link mới.
- Toast bên phải, khung vừa chữ, text giữa; lỗi trường đỏ + dòng nhỏ bên dưới, alert không viền focus xanh. Có giảm chuyển động và vùng bấm 44 px. Luật chưa xác minh không mời qua email được kiểm trong bảng quyền; hành động thật thuộc W-12.

## Bản sửa giao diện cuối theo yêu cầu chủ dự án

- Bỏ liên kết Đăng nhập/Tài khoản ở header của trang xác minh và đặt lại mật khẩu; giữ logo, nút sáng/tối và hành động tiếp tục trong nội dung trang.
- Bốn regression cho hai trang ở trạng thái có/không có phiên đều đỏ trên giao diện cũ, xanh sau sửa. Lượt lọc sai khiến test bị bỏ qua được giữ riêng và không tính là RED. [RED](w03-evidence/header-navigation-red.xml), [GREEN đầy đủ 62 test](w03-evidence/header-navigation-green.xml).
- Build đạt. Kiểm trình duyệt bổ sung hai trang ở 390/1280 px: 4/4 đạt, không tràn ngang, không page error, nút đổi giao diện hoạt động. [Audit và ảnh](w03-evidence/header-navigation/audit.json). Bộ 18 cấu hình phía dưới đã được chạy lại sau bản sửa header và sau khi nhận main chứa fixture doc-1 mới.

## Kết quả kiểm

| Cổng | Kết quả và bằng chứng |
|---|---|
| Toàn bộ backend web, PostgreSQL bắt buộc | **223 đạt, 1 bỏ qua** Cloudinary live chưa bật; [XML](w03-evidence/backend-final.xml) |
| React | **62 đạt**, không bỏ qua; [XML](w03-evidence/frontend-tests.xml) |
| Build | TypeScript + Vite đạt; JS gzip khoảng 96,5 kB |
| Browser HTTP/AuthStore/Argon2/PostgreSQL thật | **18 cấu hình màn, 8 nhóm assertion luồng**, 0 page error; [audit](w03-evidence/browser-audit.json), [runtime](w03-evidence/isolated-runtime.json), [video](w03-evidence/w03-auth-flow.webm) |
| Trạng thái link lỗi | 4 trạng thái expired/used kiểm axe sau animation; không toast cũ, không outline xanh |
| Taste và thiết kế | **0 FAIL, 1 WARN**, giảm từ 3 WARN; [critique](w03-evidence/ui-critique.md), [inspector](w03-evidence/taste-inspect/report.json). Đã bỏ eyebrow dư và sửa inset header 390 px thành 16 px; giữ khoảng trống desktop cân hai bên cho form một nhiệm vụ. Điểm critique chủ quan 7,7, không thay phán xét Figma |
| Thư mẫu | 3 mẫu × 2 kích thước, không tràn; kiểm logo và path/hash/query của nút; [review và ảnh](w03-email-templates/visual-review.md). Render Chromium với logo local; chưa khẳng định kết quả Gmail/Outlook |
| Các nhóm lõi đã đủ fixture sau khôi phục | **33 đạt**, gồm W-13, fake builder, preview và migration; [XML](w03-evidence/recovered-core-fixtures.xml) |
| Local đang chạy | http://127.0.0.1:8000 — health/db tốt, head w03_0004; [metadata](w03-evidence/local-runtime.json). SMTP dùng cấu hình đã cấp; không tự gửi thử thư |

Không cộng các lượt tập trung vào tổng cổng đầy đủ. Kiểm tự động dùng Mailer giả; không gọi mô hình, chi phí mô hình **0 USD**.

## Đỏ trước sửa và các phép phá guard

- Race request/reset PostgreSQL: bỏ alias email làm request hoàn tất trước commit reset; assertion chờ Lock thất bại. Thêm lại alias thì request tuần tự hoá sau reset và token mới vẫn hợp lệ. [RED](w03-evidence/request-race-red.xml), [GREEN](w03-evidence/request-race-green.xml).
- Race login/reset dùng hai engine, backend PID và pg_stat_activity; bỏ alias thì phiên dùng mật khẩu cũ còn sống. Không chỉ so danh sách khoá hoặc dựa vào sleep.
- Logout production/HTTP: test đỏ vì cookie xoá thiếu Secure, xanh sau sửa; đồng thời kiểm token phiên cũ bị từ chối. [RED](w03-email-templates/test_logout_red.xml), [GREEN](w03-email-templates/test_w03_auth_http.xml).
- Query/hash không có token từng xoá mất alert: hai regression đỏ trước sửa, xanh sau sửa. [RED](w03-evidence/tokenless-urls-red.xml), [GREEN](w03-evidence/tokenless-urls-green.xml).
- Guard TTL, dùng một lần, thu hồi phiên bị phá trong bộ nhớ và bị bắt qua trạng thái account/audit/phiên độc lập. [XML](w03-evidence/guard-mutations.xml).
- Guard SMTP có fake kết nối/giao thư hoàn chỉnh; mutant đi tới giao thư giả, bản đúng từ chối trước kết nối. Trường hợp header dùng MIME giả cho phép header để kiểm riêng guard adapter, không tuyên bố stdlib bỏ kiểm header.

## Đối chiếu tiêu chí vé

Các assertion dưới đây trong test_w03_accounts.py, trừ dòng PostgreSQL:

| Tiêu chí | Assertion |
|---|---|
| Một thư xác minh, xác minh được, lần hai từ chối | test_register_sends_one_hashed_token_and_verification_is_one_use |
| Quá 24 giờ và đổi email bị từ chối | test_verification_expiration_and_changed_email_are_rejected |
| Gửi lại lần thứ 4 bị giới hạn | test_resend_is_limited_by_shared_store_and_sends_three_per_hour |
| Email không tồn tại: cùng phản hồi, không thư | test_password_reset_request_is_generic_and_throttles_known_and_unknown_emails |
| Reset một lần, thu hồi phiên/token khác | test_password_reset_is_single_use_revokes_all_sessions_and_other_reset_tokens |
| Reset quá 60 phút | test_password_reset_token_expires_after_sixty_minutes |
| DB chỉ giữ hash | test_postgres_persists_only_token_hash_and_reset_revokes_every_session trong test_w03_postgres.py |
| Ảnh banner/ba trang, thư HTML | w03-evidence/, w03-email-templates/ và script browser/preview có assertion |

## Cổng toàn repo trước khi dựng lại doc-1 (lịch sử)

Lượt cong-w03-final-1 ngắt theo yêu cầu nghỉ trưa khoảng 13%, chưa có JUnit; log dở được giữ. Chẩn đoán sau đó chỉ ra fixture W-13 thiếu; không coi lỗi setup/fixture là RED của nghiệp vụ.

Lượt toàn bộ cong-w03-final-2: **2.071 đạt, 4 fail, 1 Cloudinary live bỏ qua**, 402,70 giây. [XML đầy đủ](w03-evidence/full-gate-fixtures-missing.xml). Bốn fail là hai test quiz đọc graph doc-1/v45 bị FileNotFound; fake builder thiếu graph/ảnh công thức doc-6; preview thiếu PDF doc-1 nên không trả PNG.

Sau thông tin khôi phục, đã chép **787/927 tệp** trong manifest từ snapshot độc lập tmp/development-fixtures-20261020: 736 tệp mới + 51 tệp sẵn có, tất cả khớp SHA-256; **0 junction**, không đổi assertion hoặc mã lõi. [Danh sách đối chiếu](w03-evidence/fixture-recovery-copy.json). Các nhóm đủ fixture đã đạt 33/33; đây không thay cho việc chạy lại toàn bộ cổng.

Còn thiếu 140 tệp doc-1, gồm canonical v5 và graph v45. **Chưa chạy lại cổng đầy đủ và chưa tuyên bố đạt.** Chờ nguồn khôi phục đúng hash, chép theo manifest rồi chạy lại toàn bộ bằng basetemp mới; sau đó bàn giao nghiệm thu độc lập/ghép. Không dùng số 2.062 của báo cáo cũ thay số thực.

Không sửa/gỡ/dọn tmp/t01a-clean-ff797eb, không dùng làm nguồn cache; không dọn snapshot/cache khôi phục. Đã báo quy tắc cho cả ba Luna. Thao tác junction thuộc điều phối.

## Lệnh tái kiểm và giới hạn

Từ gốc worktree, dùng Python chung qua runner để import đúng mã:

    ../../.venv/Scripts/python.exe scripts/w05_run_tests.py -o addopts= -q --basetemp=tmp/cong-w03-next --junitxml=tmp/cong-w03-next.xml
    npm.cmd --prefix src/web/frontend test -- --pool=threads --maxWorkers=1
    npm.cmd --prefix src/web/frontend run build
    ../../.venv/Scripts/python.exe scripts/w03_browser_runtime.py
    ../../.venv/Scripts/python.exe report/w03-email-templates/render_samples.py
    node report/w03-email-templates/email_visual_check.cjs

Script browser tạo DB UUID riêng và dọn đúng DB đó; ứng dụng thật không có route lấy thư giả. Queue SMTP là bộ nhớ: restart có thể mất thư đang đợi, người học dùng gửi lại. Chưa kiểm giao thư Gmail thật. Runtime local khởi động bằng tmp/w03_serve_local.py được Git bỏ qua, nạp cấu hình phía máy chủ và ép import từ worktree; không có bí mật trong commit hay VITE_*.

Nguồn: [OWASP Forgot Password](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html), [Python smtplib](https://docs.python.org/3/library/smtplib.html), [Python secrets](https://docs.python.org/3/library/secrets.html). Báo cáo này thay trạng thái điểm nghỉ trưa; vẫn giữ báo cáo cũ làm lịch sử.
