# W-03 — Soát độc lập lại trước nghiệm thu, 2026-10-20

Mã sản phẩm được soát: `7cc60fa`. Nhánh nghiệm thu nhận main thành `e940633ae6a6bfa34088c484fcf9ea2fceeddce4`; `git diff --exit-code 7cc60fa HEAD -- src/web design` không có thay đổi. Main bổ sung fixture quiz và tài liệu khôi phục. Ba người soát chỉ đọc mã/bằng chứng, không sửa tệp, chạy DB/test hoặc gửi thư; cổng chạy lại do root thực hiện và báo riêng.

## luna_backend — approve, không có finding bắt buộc sửa

Đã soát vòng đời token, hash SHA-256, purpose/account/email/expiry/use trong giao dịch; kiểm token trước Argon2; thu hồi mọi phiên và token reset còn lại. Khoá email dùng chung cho login/reset và request/reset có test PostgreSQL chờ Lock cùng phép phá alias. Origin được kiểm trước body; resend vẫn có phiên và CSRF. Migration và schema khớp vé.

Giới hạn: cùng body/status và gửi SMTP bất đồng bộ chưa chứng minh thời gian phản hồi không thể phân biệt email có/không có tài khoản. Nhánh có tài khoản vẫn ghi token và đưa thư vào queue. Đây là ghi chú không chặn theo hợp đồng W-03, không tuyên bố đã đo hoặc loại bỏ kênh thời gian.

## luna_frontend — approve, không có finding bắt buộc sửa

Đã soát Auth.tsx, W03.test.tsx, route/provider và CSS motion; xem bốn ảnh header mới cùng bằng chứng trạng thái/18 cấu hình trước đó. Bắt token rồi xoá URL giữ đúng lỗi thiếu token; generation guard chặn response cũ khi mở link mới. Reset xoá phiên và chuyển đăng nhập kèm thông báo; verify cập nhật /me theo trạng thái phiên. Validation, ARIA/focus, trạng thái terminal và giảm chuyển động phù hợp. Taste có 0 FAIL, 1 WARN khoảng trống desktop đã giải thích.

## luna_media — approve, không có finding bắt buộc sửa

Đã soát SMTP, mẫu thư, cấu hình, Origin/CSRF và xoá cookie. STARTTLS kiểm chứng chỉ, xác thực sau TLS, timeout hữu hạn; lỗi gửi được làm sạch; production từ chối console mailer. Mẫu thư escape nội dung và dùng link cùng origin. Middleware chỉ miễn kiểm phiên/CSRF cho các POST công khai đã liệt kê; các mutation khác giữ guard. Cookie xoá theo chính sách Secure production. Đã đối chiếu JUnit Mailer/guard và RED/GREEN logout lưu trước đó; không giao thư SMTP thật trong lượt soát này.

## Phạm vi kết luận

Ba lượt approve chỉ dành cho mã W-03 và bằng chứng đã nêu. Không thay quyền ghép main của điều phối, không đóng W-24, không nghiệm thu W-06, không chứng minh giao thư Gmail thật. Kết quả cổng toàn repo mới nằm trong báo cáo nghiệm thu của root.
