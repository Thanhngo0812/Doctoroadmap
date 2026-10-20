# W-03 — Hợp đồng triển khai

Phạm vi chỉ W-03. Nhánh work/w03-email-recovery. Tài liệu chuẩn: task/web/W-03-xac-minh-email-quen-mat-khau.md và spec tương ứng. Không sửa W-06/lõi.

## HTTP (tiền tố /api/v1)

| POST | JSON body | Success 200 message |
|---|---|---|
| /auth/verify-email | {token} | Email đã được xác minh. |
| /auth/resend-verification | {} | Nếu email chưa được xác minh, bạn sẽ nhận được thư xác minh mới. |
| /auth/password-reset/request | {email} | Nếu email có tài khoản, bạn sẽ nhận được thư đặt lại mật khẩu. |
| /auth/password-reset/confirm | {token, password} | Đã đặt lại mật khẩu. Hãy đăng nhập bằng mật khẩu mới. |

Verify/request/confirm là POST công khai nhưng luôn kiểm Origin, không đòi phiên/CSRF cũ. Resend bắt buộc phiên+CSRF+Origin. Không tháo middleware toàn cục.
Token sai/hết hạn/đã dùng: link_invalid 410; error.fields có loc=token, type=token_invalid/token_expired/token_used, message tiếng Việt phù hợp. Frontend dùng type để dựng trạng thái, không suy từ nội dung chữ. Sai password: validation 422 cùng fields hiện có. Throttle: rate_limited 429 có retry_after, cùng hành vi known/unknown email.
Các POST public không xác thực bằng cookie cũ; token hành động là bằng chứng cho verify/confirm. Confirm thành công xoá cookie phiên hiện tại, client clearSession rồi về đăng nhập kèm success. GET trang link không tiêu thụ token; người dùng xác nhận bằng nút.

## Schema/service

w03_0004 nối w02_0003, bảng email_token theo spec; purpose verify_email/reset_password, chỉ băm SHA256 token ngẫu nhiên 32 byte. Tiêu thụ nguyên tử trong giao dịch cùng cập nhật account/phiên. Khi reset thành công vô hiệu các token reset còn lại của account để link cũ không lấy lại tài khoản. Các bảng rate_limit_event/audit_event được dùng lại.
AuthPolicy bổ sung email_verify_ttl_hours=24, resend_verification_per_hour=3, password_reset_ttl_minutes=60, public_base_url='http://127.0.0.1:8000'; reset request tối đa 3/email/giờ. AccountService nhận keyword mailer (có thể None cho caller W-02 cũ; composition thực luôn phải cấp Mailer). Clock hiện có. Không giữ transaction DB trong lúc gửi SMTP; lỗi gửi không làm lộ email tồn tại/rollback tài khoản đã tạo, được log thông báo chung không nội dung thư/token.
verify_email(token), resend_verification(account_id), request_password_reset(email), reset_password(token,password); keyword ip optional cho audit. Trả None hoặc Account nếu hữu ích nội bộ, HTTP trả message như bảng trên. register() giữ kết quả W-02, gửi một verify cho tài khoản mới; duplicate gửi existing_account, không tạo token/phiên chiếm tài khoản.

## Mailer (đầu mối mailer sở hữu các tệp này)

application/ports.py: Mailer.send(to:str, subject:str, body:str, *, html_body:str|None=None)->None.
application/email_templates.py: render_account_email(kind, *, display_name:str, action_url:str, base_url:str)->MailContent với subject/text/html; kind verify_email/reset_password/existing_account. HTML logo dùng base_url+/assets/Artboard%2024.png. Các link đăng nhập/quên mật khẩu cũng từ base_url tin cậy, escape input.
fakes/mail.py: FakeMailer.messages, mỗi message có to/subject/body/html_body. infrastructure/mail.py: ConsoleMailer và SmtpMailer; SmtpMailer keyword host,port,username,password,from_address,starttls=True; không kết nối SMTP trong constructor, có timeout hữu hạn. Test adapter dùng kết nối giả. Console chỉ dev (nội dung thư theo yêu cầu vé); SMTP không log nội dung/token.

## Ownership

Backend agent: application/accounts.py, application/auth_ports.py, domain/auth.py nếu cần, infrastructure/auth_schema.py/auth_store.py, fakes/auth.py, migrations/versions/w03_0004_email_tokens.py, api/auth.py, test W-03 backend mới và cập nhật guard HTTP cũ đúng ngoại lệ public mới. Không sửa settings/composition/testing.py.
Frontend agent: toàn bộ frontend W-03, test React mới/cũ cần thiết; không sửa backend/design. Giữ menu, vị trí thông báo bên phải, khung vừa chữ và text căn giữa. Giữ lỗi trường đỏ và không outline xanh trên alert lỗi.
Mailer agent: đúng ba nhóm file Mailer/templates/fake bên trên và test_mailer.py; không sửa settings/composition/accounts.
Root: settings/composition/testing.py, test composition/settings/migration cũ cần cập nhật, browser/runtime/acceptance, docs/commit. Các agent không tự git add/commit và không sửa cùng tệp người khác.
